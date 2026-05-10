from django.test import TestCase
from rest_framework.test import APIClient
from collab.models import AuditLog, Comment, Document, DocumentVersion, Tag, WorkspaceMember


class UserApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.client.defaults['HTTP_HOST'] = 'localhost'
		self.valid_payload = {
			'first_name': 'Owner',
			'last_name': 'One',
			'email': 'owner@example.com',
			'phone': '+15555550123',
		}

	def test_create_user_returns_201_and_serialized_body(self):
		response = self.client.post('/api/users/', self.valid_payload, format='json')

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data['first_name'], self.valid_payload['first_name'])
		self.assertEqual(response.data['email'], self.valid_payload['email'])
		self.assertIn('id', response.data)
		self.assertIn('created_at', response.data)

	def test_get_user_by_uuid_returns_200(self):
		create_response = self.client.post('/api/users/', self.valid_payload, format='json')
		user_id = create_response.data['id']

		response = self.client.get(f'/api/users/{user_id}/')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data['id'], user_id)
		self.assertEqual(response.data['email'], self.valid_payload['email'])

	def test_create_user_rejects_invalid_email(self):
		payload = {**self.valid_payload, 'email': 'not-an-email'}

		response = self.client.post('/api/users/', payload, format='json')

		self.assertEqual(response.status_code, 400)
		self.assertIn('email', response.data)

	def test_create_user_rejects_invalid_phone(self):
		payload = {**self.valid_payload, 'phone': '12345'}

		response = self.client.post('/api/users/', payload, format='json')

		self.assertEqual(response.status_code, 400)
		self.assertIn('phone', response.data)


class WorkspaceApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.client.defaults['HTTP_HOST'] = 'localhost'
		self.owner_payload = {
			'first_name': 'Owner',
			'last_name': 'One',
			'email': 'owner.workspace@example.com',
			'phone': '+15555550124',
		}
		self.member_payload = {
			'first_name': 'Editor',
			'last_name': 'Two',
			'email': 'editor.workspace@example.com',
			'phone': '+15555550125',
		}

	def create_user(self, payload):
		response = self.client.post('/api/users/', payload, format='json')
		self.assertEqual(response.status_code, 201)
		return response.data

	def test_workspace_flow_matches_expected_endpoints(self):
		owner = self.create_user(self.owner_payload)
		member = self.create_user(self.member_payload)

		workspace_response = self.client.post(
			'/api/workspaces/',
			{'name': 'Workspace One', 'owner': owner['id'], 'is_active': True},
			format='json',
		)
		self.assertEqual(workspace_response.status_code, 201)
		workspace = workspace_response.data
		self.assertEqual(workspace['member_count'], 1)

		workspace_detail = self.client.get(f"/api/workspaces/{workspace['id']}/")
		self.assertEqual(workspace_detail.status_code, 200)
		self.assertEqual(workspace_detail.data['member_count'], 1)

		add_member_response = self.client.post(
			f"/api/workspaces/{workspace['id']}/members/",
			{'user': member['id'], 'role': 'editor'},
			format='json',
		)
		self.assertEqual(add_member_response.status_code, 201)
		self.assertEqual(add_member_response.data['role'], 'editor')

		duplicate_member_response = self.client.post(
			f"/api/workspaces/{workspace['id']}/members/",
			{'user': member['id'], 'role': 'viewer'},
			format='json',
		)
		self.assertEqual(duplicate_member_response.status_code, 409)
		self.assertIn('detail', duplicate_member_response.data)

		members_response = self.client.get(f"/api/workspaces/{workspace['id']}/members/")
		self.assertEqual(members_response.status_code, 200)
		self.assertEqual(len(members_response.data), 2)

		summary_response = self.client.get(f"/api/workspaces/{workspace['id']}/summary/")
		self.assertEqual(summary_response.status_code, 200)
		self.assertEqual(summary_response.data['member_count'], 2)
		self.assertEqual(summary_response.data['document_count'], 0)
		self.assertEqual(summary_response.data['comment_count'], 0)
		self.assertTrue(WorkspaceMember.objects.filter(workspace_id=workspace['id']).exists())


class DocumentApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.client.defaults['HTTP_HOST'] = 'localhost'
		self.owner_payload = {
			'first_name': 'Owner',
			'last_name': 'One',
			'email': 'owner.document@example.com',
			'phone': '+15555550126',
		}
		self.editor_payload = {
			'first_name': 'Editor',
			'last_name': 'Two',
			'email': 'editor.document@example.com',
			'phone': '+15555550127',
		}

	def create_user(self, payload):
		response = self.client.post('/api/users/', payload, format='json')
		self.assertEqual(response.status_code, 201)
		return response.data

	def create_workspace(self, owner_id):
		response = self.client.post(
			'/api/workspaces/',
			{'name': 'Docs Workspace', 'owner': owner_id, 'is_active': True},
			format='json',
		)
		self.assertEqual(response.status_code, 201)
		return response.data

	def test_document_create_update_versions_stats_and_tags(self):
		owner = self.create_user(self.owner_payload)
		editor = self.create_user(self.editor_payload)
		workspace = self.create_workspace(owner['id'])
		tag = Tag.objects.create(name='backend')

		create_response = self.client.post(
			'/api/documents/',
			{
				'title': 'Doc One',
				'content': 'Initial content',
				'workspace': workspace['id'],
				'created_by': owner['id'],
				'status': 'draft',
			},
			format='json',
		)
		self.assertEqual(create_response.status_code, 201)
		document = create_response.data
		self.assertEqual(Document.objects.count(), 1)
		self.assertEqual(DocumentVersion.objects.count(), 1)
		self.assertEqual(DocumentVersion.objects.first().version_number, 1)

		update_response = self.client.put(
			f"/api/documents/{document['id']}/",
			{
				'title': document['title'],
				'content': 'Updated content',
				'workspace': document['workspace'],
				'created_by': document['created_by'],
				'status': 'published',
				'updated_by': editor['id'],
			},
			format='json',
		)
		self.assertEqual(update_response.status_code, 200)
		self.assertEqual(DocumentVersion.objects.count(), 2)
		self.assertEqual(DocumentVersion.objects.order_by('-version_number').first().version_number, 2)

		list_response = self.client.get(
			f"/api/documents/?workspace={workspace['id']}&status=published&search=Doc"
		)
		self.assertEqual(list_response.status_code, 200)
		self.assertEqual(len(list_response.data), 1)

		versions_response = self.client.get(f"/api/documents/{document['id']}/versions/")
		self.assertEqual(versions_response.status_code, 200)
		self.assertEqual(len(versions_response.data), 2)
		self.assertEqual(versions_response.data[0]['version_number'], 2)
		self.assertEqual(versions_response.data[1]['version_number'], 1)

		stats_response = self.client.get(f"/api/documents/{document['id']}/stats/")
		self.assertEqual(stats_response.status_code, 200)
		self.assertEqual(stats_response.data['version_count'], 2)
		self.assertEqual(stats_response.data['comment_count'], 0)
		self.assertEqual(stats_response.data['contributor_count'], 2)

		tag_response = self.client.post(
			f"/api/documents/{document['id']}/tags/",
			{'tag_ids': [str(tag.id)]},
			format='json',
		)
		self.assertEqual(tag_response.status_code, 200)
		self.assertEqual(tag_response.data[0]['name'], 'backend')

		tags_list_response = self.client.get('/api/tags/')
		self.assertEqual(tags_list_response.status_code, 200)
		self.assertEqual(tags_list_response.data[0]['document_count'], 1)

		self.assertEqual(self.client.get(f"/api/documents/{document['id']}/versions/").status_code, 200)


class CommentTagAuditLogApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.client.defaults['HTTP_HOST'] = 'localhost'
		self.owner_payload = {
			'first_name': 'Owner',
			'last_name': 'One',
			'email': 'owner.comment@example.com',
			'phone': '+15555550128',
		}
		self.editor_payload = {
			'first_name': 'Editor',
			'last_name': 'Two',
			'email': 'editor.comment@example.com',
			'phone': '+15555550129',
		}

	def create_user(self, payload):
		response = self.client.post('/api/users/', payload, format='json')
		self.assertEqual(response.status_code, 201)
		return response.data

	def create_workspace_and_document(self):
		owner = self.create_user(self.owner_payload)
		editor = self.create_user(self.editor_payload)
		workspace_response = self.client.post(
			'/api/workspaces/',
			{'name': 'Comments Workspace', 'owner': owner['id'], 'is_active': True},
			format='json',
		)
		self.assertEqual(workspace_response.status_code, 201)
		workspace = workspace_response.data

		document_response = self.client.post(
			'/api/documents/',
			{
				'title': 'Threaded Doc',
				'content': 'Initial content',
				'workspace': workspace['id'],
				'created_by': owner['id'],
				'status': 'draft',
			},
			format='json',
		)
		self.assertEqual(document_response.status_code, 201)
		return owner, editor, workspace, document_response.data

	def test_comments_are_threaded_and_filtered_by_document(self):
		owner, editor, workspace, document = self.create_workspace_and_document()

		top_level_response = self.client.post(
			'/api/comments/',
			{
				'document': document['id'],
				'author': owner['id'],
				'content': 'Top-level comment',
				'parent': None,
			},
			format='json',
		)
		self.assertEqual(top_level_response.status_code, 201)
		top_level_comment = top_level_response.data

		reply_response = self.client.post(
			'/api/comments/',
			{
				'document': document['id'],
				'author': editor['id'],
				'content': 'Reply comment',
				'parent': top_level_comment['id'],
			},
			format='json',
		)
		self.assertEqual(reply_response.status_code, 201)
		self.assertEqual(str(reply_response.data['parent']), top_level_comment['id'])

		comments_response = self.client.get(f"/api/comments/?document={document['id']}")
		self.assertEqual(comments_response.status_code, 200)
		self.assertEqual(len(comments_response.data), 2)
		self.assertTrue(any(item['parent'] is None for item in comments_response.data))
		self.assertTrue(any(str(item['parent']) == top_level_comment['id'] for item in comments_response.data))
		self.assertTrue(Comment.objects.filter(document_id=document['id']).exists())

	def test_comment_reply_rejects_cross_document_parent(self):
		owner, editor, workspace, document = self.create_workspace_and_document()
		other_document_response = self.client.post(
			'/api/documents/',
			{
				'title': 'Other Doc',
				'content': 'Other content',
				'workspace': workspace['id'],
				'created_by': owner['id'],
				'status': 'draft',
			},
			format='json',
		)
		self.assertEqual(other_document_response.status_code, 201)

		parent_comment = self.client.post(
			'/api/comments/',
			{
				'document': document['id'],
				'author': owner['id'],
				'content': 'Parent comment',
				'parent': None,
			},
			format='json',
		)
		self.assertEqual(parent_comment.status_code, 201)

		invalid_reply = self.client.post(
			'/api/comments/',
			{
				'document': other_document_response.data['id'],
				'author': editor['id'],
				'content': 'Invalid reply',
				'parent': parent_comment.data['id'],
			},
			format='json',
		)
		self.assertEqual(invalid_reply.status_code, 400)
		self.assertIn('parent', invalid_reply.data)

	def test_tags_create_and_audit_logs_filter(self):
		owner, editor, workspace, document = self.create_workspace_and_document()

		tag_response = self.client.post('/api/tags/', {'name': 'frontend'}, format='json')
		self.assertEqual(tag_response.status_code, 201)
		self.assertEqual(tag_response.data['name'], 'frontend')
		self.assertTrue(Tag.objects.filter(name='frontend').exists())

		update_response = self.client.put(
			f"/api/documents/{document['id']}/",
			{
				'title': document['title'],
				'content': 'Updated content',
				'workspace': document['workspace'],
				'created_by': document['created_by'],
				'status': 'published',
				'updated_by': editor['id'],
			},
			format='json',
		)
		self.assertEqual(update_response.status_code, 200)

		audit_logs_response = self.client.get(f"/api/audit-logs/?actor_id={owner['id']}")
		self.assertEqual(audit_logs_response.status_code, 200)
		self.assertTrue(len(audit_logs_response.data) >= 1)
		self.assertTrue(all(str(item['actor']) == owner['id'] for item in audit_logs_response.data))

		audit_log_date = audit_logs_response.data[0]['timestamp']
		filtered_response = self.client.get(
			f"/api/audit-logs/?actor_id={owner['id']}&date_from={audit_log_date}&date_to={audit_log_date}"
		)
		self.assertEqual(filtered_response.status_code, 200)
		self.assertTrue(len(filtered_response.data) >= 1)
		self.assertTrue(all(str(item['actor']) == owner['id'] for item in filtered_response.data))
		self.assertTrue(AuditLog.objects.filter(actor_id=owner['id']).exists())
