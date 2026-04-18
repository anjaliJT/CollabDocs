
"""
    concepts : 
    -----------

        transaction.atomic() ,
        override
        create()
        annotate()
        Count
        select_related
        serializer nesting
        @action
        aggregate()
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action 
from rest_framework.response import Response
from .serializers import workspaceSerializer, workspaceMemberSerializer
from .models import WorkspaceMember, Workspace

class workspaceViewset(viewsets.ModelViewSet): 
    """
    these two core requirement : 
    queryset  : what data to operate on 
    serializer_class :  how data is validated and returned. 
    """
    queryset = Workspace.objects.all()
    serializer_class = workspaceSerializer

    # MEMBERS (GET + POST)
    @action(detail=True, methods=['get','post'], url_path='members')
    def members(self, request, pk=None):
        workspace = self.get_object() 

        if request.method == 'GET': 
            members = WorkspaceMember.Objects.filter(workspace = workspace)
            serialzer = workspaceMemberSerializer(members,many=True)
            return Response(serialzer.data)
        
        elif request.method == 'POST':
            data = request.data.copy()
            data[workspace] = workspace.id

            serialzer = workspaceMemberSerializer(data = data)
            serialzer.is_valid(raise_exception=True)
            serialzer.save()

            return Response(serialzer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='summary')
    def summary(self,request,pk=None): 
        workspace = self.get_object()
        member_count = WorkspaceMember.objects.filter(workspace=workspace).count()

        data = {
            "id": workspace.id,
            "name": workspace.name, 
            "member_count": member_count
        }

        return Response(data)
