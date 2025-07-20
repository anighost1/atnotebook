
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotebookViewSet, NotebookCollaboratorViewSet

router = DefaultRouter()
router.register(r'collaborator', NotebookCollaboratorViewSet, basename='collaborator')
router.register(r'', NotebookViewSet, basename='notebook')

urlpatterns = [
    path('', include(router.urls)),
]
