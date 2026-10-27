from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView, TokenVerifyView
)
from . import views

router = DefaultRouter()
router.register('posts', views.PostViewSet, basename='posts')
router.register('groups', views.GroupViewSet, basename='groups')
router.register('follow', views.FollowViewSet, basename='follow')
router.register(
    r'posts/(?P<post_id>\d+)/comments',
    views.CommentViewSet,
    basename='comments'
)

urlpatterns = [
    path('v1/', include(router.urls)),
    path('v1/jwt/create/', TokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('v1/jwt/refresh/', TokenRefreshView.as_view(),
         name='token_refresh'),
    path('v1/jwt/verify/', TokenVerifyView.as_view(),
         name='token_verify'),
]
