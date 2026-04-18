from rest_framework import serializers
from .models import Workspace, WorkspaceMember

class workspaceSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = Workspace
        fields = ['id', 'name', 'owner', 'created_at']
        read_only_fields = ['id', 'owner', 'create_at']
   
class workspaceMemberSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = WorkspaceMember
        fields = ['id', 'workspace', 'user', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']