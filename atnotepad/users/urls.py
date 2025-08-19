from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserCreateView, FriendListViewSet, UserSearchView

router = DefaultRouter()
router.register(r'friend', FriendListViewSet, basename='friend')

urlpatterns = [
    path('', UserCreateView.as_view(), name='user-create'),
    path('search/', UserSearchView.as_view(), name='user-search'),
    path('', include(router.urls)),
]
