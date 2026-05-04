from rest_framework import serializers

from .models import AuditLog, Comment, Document, DocumentVersion, Tag, User, Workspace, WorkspaceMember


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'created_at']
        read_only_fields = ['id', 'created_at']


class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ['id', 'name', 'owner', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class WorkspaceMemberSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)

    class Meta:
        model = WorkspaceMember
        fields = ['id', 'workspace', 'user', 'user_detail', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class AddMemberSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    role = serializers.ChoiceField(choices=WorkspaceMember.Role.choices)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class DocumentSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, required=False)

    class Meta:
        model = Document
        fields = [
            'id',
            'title',
            'content',
            'workspace',
            'created_by',
            'updated_by',
            'status',
            'updated_at',
            'tags',
        ]
        read_only_fields = ['id', 'updated_at', 'tags']

    def create(self, validated_data):
        actor = validated_data.pop('actor', self.context.get('actor'))
        validated_data.pop('updated_by', None)
        instance = Document(**validated_data)
        instance.save(actor=actor)
        return instance

    def update(self, instance, validated_data):
        actor = validated_data.pop('actor', self.context.get('actor'))
        validated_data.pop('updated_by', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(actor=actor)
        return instance


class DocumentVersionSerializer(serializers.ModelSerializer):
    saved_by_detail = UserSerializer(source='saved_by', read_only=True)

    class Meta:
        model = DocumentVersion
        fields = ['id', 'document', 'content', 'version_number', 'saved_by', 'saved_by_detail', 'saved_at']


class CommentSerializer(serializers.ModelSerializer):
    author_detail = UserSerializer(source='author', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'document', 'author', 'author_detail', 'content', 'parent', 'created_at']
        read_only_fields = ['id', 'created_at']


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'document', 'author', 'content', 'parent', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        parent = attrs.get('parent')
        document = attrs.get('document')
        if parent and parent.document_id != document.id:
            raise serializers.ValidationError({'parent': 'Parent comment must belong to the same document.'})
        return attrs


class AuditLogSerializer(serializers.ModelSerializer):
    actor_detail = UserSerializer(source='actor', read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'actor', 'actor_detail', 'action', 'model_name', 'object_id', 'timestamp']
