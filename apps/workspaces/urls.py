from rest_framework.routers import DefaultRouter 
from .views import   workspaceViewset





# API :
# POST : /api/workspaces/
# GET : /api/workspaces/{id}/
# POST: /api/workspaces/{id}/members/
# GET : /api/workspaces/{id}/members/
# GET : /api/workspaces/{id}/summary/

router = DefaultRouter()
router.register('', workspaceViewset, basename='workspace')

urlpatterns = router.urls


