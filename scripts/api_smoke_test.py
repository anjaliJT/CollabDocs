import json
import os
import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "collab_docs.settings")

import django

django.setup()

from rest_framework.test import APIClient
from collab.models import AuditLog, Comment, Document, DocumentVersion, Tag, User, Workspace, WorkspaceMember


def print_step(name, status_code, payload):
    print(f"[{status_code}] {name}")
    print(json.dumps(payload, indent=2, default=str))


client = APIClient()
client.defaults["HTTP_HOST"] = "localhost"
run_suffix = uuid.uuid4().hex[:8]

# Users
user1_payload = {
    "first_name": "Owner",
    "last_name": "One",
    "email": f"owner_{run_suffix}@example.com",
    "phone": f"90000{run_suffix[:5]}",
}
res = client.post("/api/users/", user1_payload, format="json")
user1 = res.json()
print_step("Create user1", res.status_code, user1)

res = client.get(f"/api/users/{user1['id']}/")
print_step("Get user1 by id", res.status_code, res.json())

user2_payload = {
    "first_name": "Editor",
    "last_name": "Two",
    "email": f"editor_{run_suffix}@example.com",
    "phone": f"91111{run_suffix[:5]}",
}
res = client.post("/api/users/", user2_payload, format="json")
user2 = res.json()
print_step("Create user2", res.status_code, user2)

# Workspaces
workspace_payload = {
    "name": f"Workspace-{run_suffix}",
    "owner": user1["id"],
    "is_active": True,
}
res = client.post("/api/workspaces/", workspace_payload, format="json")
workspace = res.json()
print_step("Create workspace", res.status_code, workspace)

res = client.get(f"/api/workspaces/{workspace['id']}/")
print_step("Get workspace", res.status_code, res.json())

add_member_payload = {"user": user2["id"], "role": "editor"}
res = client.post(f"/api/workspaces/{workspace['id']}/members/", add_member_payload, format="json")
print_step("Add workspace member", res.status_code, res.json())

res = client.get(f"/api/workspaces/{workspace['id']}/members/")
print_step("List workspace members", res.status_code, res.json())

res = client.get(f"/api/workspaces/{workspace['id']}/summary/")
print_step("Workspace summary", res.status_code, res.json())

# Tags
res = client.post("/api/tags/", {"name": f"backend-{run_suffix}"}, format="json")
tag = res.json()
print_step("Create tag", res.status_code, tag)

# Documents
document_payload = {
    "title": f"Doc-{run_suffix}",
    "content": "Initial content",
    "workspace": workspace["id"],
    "created_by": user1["id"],
    "status": "draft",
}
res = client.post("/api/documents/", document_payload, format="json")
document = res.json()
print_step("Create document", res.status_code, document)

update_payload = {
    "title": document["title"],
    "content": "Updated content",
    "workspace": document["workspace"],
    "created_by": document["created_by"],
    "status": "published",
    "updated_by": user2["id"],
}
res = client.put(f"/api/documents/{document['id']}/", update_payload, format="json")
print_step("Update document", res.status_code, res.json())

res = client.get(
    f"/api/documents/?workspace={workspace['id']}&status=published&search=Doc-{run_suffix}"
)
print_step("List documents with filters", res.status_code, res.json())

res = client.get(f"/api/documents/{document['id']}/versions/")
print_step("Document versions", res.status_code, res.json())

res = client.get(f"/api/documents/{document['id']}/stats/")
print_step("Document stats", res.status_code, res.json())

res = client.post(
    f"/api/documents/{document['id']}/tags/",
    {"tag_ids": [tag["id"]]},
    format="json",
)
print_step("Add tags to document", res.status_code, res.json())

# Comments
comment_payload = {
    "document": document["id"],
    "author": user1["id"],
    "content": "Top-level comment",
    "parent": None,
}
res = client.post("/api/comments/", comment_payload, format="json")
comment = res.json()
print_step("Create top-level comment", res.status_code, comment)

reply_payload = {
    "document": document["id"],
    "author": user2["id"],
    "content": "Reply comment",
    "parent": comment["id"],
}
res = client.post("/api/comments/", reply_payload, format="json")
print_step("Create reply comment", res.status_code, res.json())

res = client.get(f"/api/comments/?document={document['id']}")
print_step("List comments for document", res.status_code, res.json())

# Audit logs
res = client.get(f"/api/audit-logs/?actor_id={user1['id']}")
print_step("Audit logs filtered by actor", res.status_code, res.json())

# DB verification via ORM
counts = {
    "users": User.objects.count(),
    "workspaces": Workspace.objects.count(),
    "workspace_members": WorkspaceMember.objects.count(),
    "documents": Document.objects.count(),
    "document_versions": DocumentVersion.objects.count(),
    "comments": Comment.objects.count(),
    "tags": Tag.objects.count(),
    "audit_logs": AuditLog.objects.count(),
}
print("ORM_COUNTS")
print(json.dumps(counts, indent=2))
