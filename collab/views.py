from django.db import IntegrityError
from django.db import transaction
from django.db.models import Count, Q
from django.utils.dateparse import parse_datetime
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AuditLog, Comment, Document, Tag, User, Workspace, WorkspaceMember
from .serializers import (
	AddMemberSerializer,
	AuditLogSerializer,
	CommentCreateSerializer,
	CommentSerializer,
	DocumentSerializer,
	DocumentVersionSerializer,
	TagSerializer,
	UserSerializer,
	WorkspaceMemberSerializer,
	WorkspaceSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
	queryset = User.objects.all().order_by('-created_at')
	serializer_class = UserSerializer
	lookup_field = 'id'
	http_method_names = ['get', 'post']


class WorkspaceViewSet(viewsets.ModelViewSet):
	serializer_class = WorkspaceSerializer
	http_method_names = ['get', 'post']

	def get_queryset(self):
		return Workspace.objects.select_related('owner').annotate(
			member_count=Count('members', distinct=True),
		).order_by('-created_at')

	@action(detail=True, methods=['post'], url_path='members')
	def add_member(self, request, pk=None):
		try:
			workspace = Workspace.objects.get(id=pk)
		except Workspace.DoesNotExist:
			return Response({'detail': 'Workspace not found.'}, status=status.HTTP_404_NOT_FOUND)

		serializer = AddMemberSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		try:
			with transaction.atomic():
				member = WorkspaceMember.objects.create(
					workspace=workspace,
					user=serializer.validated_data['user'],
					role=serializer.validated_data['role'],
				)
		except IntegrityError:
			return Response(
				{'detail': 'This user is already a member of the workspace.'},
				status=status.HTTP_409_CONFLICT,
			)

		response_serializer = WorkspaceMemberSerializer(member)
		return Response(response_serializer.data, status=status.HTTP_201_CREATED)

	@add_member.mapping.get
	def list_members(self, request, pk=None):
		try:
			workspace = Workspace.objects.get(id=pk)
		except Workspace.DoesNotExist:
			return Response({'detail': 'Workspace not found.'}, status=status.HTTP_404_NOT_FOUND)
		members = workspace.members.select_related('user').all().order_by('-joined_at')
		serializer = WorkspaceMemberSerializer(members, many=True)
		return Response(serializer.data)

	@action(detail=True, methods=['get'], url_path='summary')
	def summary(self, request, pk=None):
		try:
			workspace = Workspace.objects.get(id=pk)
		except Workspace.DoesNotExist:
			return Response({'detail': 'Workspace not found.'}, status=status.HTTP_404_NOT_FOUND)
		summary_data = Workspace.objects.filter(id=workspace.id).annotate(
			document_count=Count('documents', distinct=True),
			member_count=Count('members', distinct=True),
			comment_count=Count('documents__comments', distinct=True),
		).values('id', 'name', 'document_count', 'member_count', 'comment_count').first()
		return Response(summary_data)


class DocumentViewSet(viewsets.ModelViewSet):
	queryset = Document.objects.select_related('workspace', 'created_by').prefetch_related('tags').all().order_by('-updated_at')
	serializer_class = DocumentSerializer
	http_method_names = ['get', 'post', 'put']

	def get_queryset(self):
		queryset = super().get_queryset()
		workspace_id = self.request.query_params.get('workspace')
		status_param = self.request.query_params.get('status')
		tag_name = self.request.query_params.get('tag_name')
		search_text = self.request.query_params.get('search')

		if workspace_id:
			queryset = queryset.filter(workspace_id=workspace_id)
		if status_param:
			queryset = queryset.filter(status=status_param)
		if tag_name:
			queryset = queryset.filter(tags__name__iexact=tag_name)
		if search_text:
			queryset = queryset.filter(Q(title__icontains=search_text) | Q(content__icontains=search_text))

		return queryset.distinct()

	def perform_create(self, serializer):
		serializer.save(actor=serializer.validated_data.get('created_by'))

	def perform_update(self, serializer):
		actor = serializer.validated_data.get('updated_by')
		serializer.save(actor=actor)

	@action(detail=True, methods=['get'], url_path='versions')
	def versions(self, request, pk=None):
		document = self.get_object()
		versions = document.versions.select_related('saved_by').all().order_by('-version_number')
		serializer = DocumentVersionSerializer(versions, many=True)
		return Response(serializer.data)

	@action(detail=True, methods=['get'], url_path='stats')
	def stats(self, request, pk=None):
		document = self.get_object()
		stats_data = Document.objects.filter(id=document.id).annotate(
			version_count=Count('versions', distinct=True),
			comment_count=Count('comments', distinct=True),
			contributor_count=Count('versions__saved_by', distinct=True),
		).values('id', 'title', 'version_count', 'comment_count', 'contributor_count').first()
		return Response(stats_data)

	@action(detail=True, methods=['post'], url_path='tags')
	def add_tags(self, request, pk=None):
		document = self.get_object()
		tag_ids = request.data.get('tag_ids', [])
		tag_names = request.data.get('tag_names', [])

		valid_tag_ids = list(Tag.objects.filter(id__in=tag_ids).values_list('id', flat=True))
		tags_to_add = list(Tag.objects.filter(id__in=valid_tag_ids))
		for tag_name in tag_names:
			if tag_name:
				tag_obj, _ = Tag.objects.get_or_create(name=tag_name)
				tags_to_add.append(tag_obj)

		if not tags_to_add:
			return Response(
				{'detail': 'Provide tag_ids or tag_names to add tags.'},
				status=status.HTTP_400_BAD_REQUEST,
			)

		document.tags.add(*tags_to_add)
		serializer = TagSerializer(document.tags.all(), many=True)
		return Response(serializer.data, status=status.HTTP_200_OK)


class CommentViewSet(viewsets.ModelViewSet):
	queryset = Comment.objects.select_related('author', 'document', 'parent').all().order_by('-created_at')
	http_method_names = ['get', 'post']

	def get_serializer_class(self):
		if self.action == 'create':
			return CommentCreateSerializer
		return CommentSerializer

	def get_queryset(self):
		queryset = super().get_queryset()
		document_id = self.request.query_params.get('document')
		if document_id:
			queryset = queryset.filter(document_id=document_id)
		return queryset


class TagViewSet(viewsets.ModelViewSet):
	serializer_class = TagSerializer
	http_method_names = ['get', 'post']

	def get_queryset(self):
		return Tag.objects.annotate(document_count=Count('documents', distinct=True)).order_by('name')


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = AuditLog.objects.select_related('actor').all().order_by('-timestamp')
	serializer_class = AuditLogSerializer

	def get_queryset(self):
		queryset = super().get_queryset()
		actor_id = self.request.query_params.get('actor_id')
		date_from = self.request.query_params.get('date_from')
		date_to = self.request.query_params.get('date_to')

		if actor_id:
			queryset = queryset.filter(actor_id=actor_id)
		if date_from:
			parsed_from = parse_datetime(date_from)
			if parsed_from:
				queryset = queryset.filter(timestamp__gte=parsed_from)
		if date_to:
			parsed_to = parse_datetime(date_to)
			if parsed_to:
				queryset = queryset.filter(timestamp__lte=parsed_to)

		return queryset
