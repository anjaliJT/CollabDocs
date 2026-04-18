from django.db import models
from apps.collab.models import User
import uuid
# Create your models here.

class Workspace(models.Model): 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class WorkspaceMember(models.Model): 
    class RoleChoices(models.TextChoices): 
        """ENUM BASED CHOICES, Provide more readability,
          gives extra methods,features. -> .choices, .labels, .values, .names, 
          Easy to maintaain. 
          IDE autocompletion
          """
        ADMIN = "ADMIN", "Admin"
        EDITOR = "EDITOR","Editor"
        VIWER = "VIWER", "Viwer"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=RoleChoices.choices, default=RoleChoices.ADMIN)
    joined_at = models.DateField(auto_now_add = True)

    class Meta: 
        """
        constriant : 
        ------------
        this enfore uniqueness at database level,
        prevent dublicate member for same workspace, 
        ensures data integrity event under concurrent requests

        indexes : 
        ---------
        creates database indexes
        speeds up lookup  on a table 
        speeds up queries like : filter
        """
        constraints =[ models.UniqueConstraint(
            fields=['workspace', 'user'], 
            name='unique_workspace_member'
            )
            ]
        indexes = [
            models.Index(fields=['workspace', 'user'])
        ]