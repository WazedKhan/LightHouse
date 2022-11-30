"""
Url mapping for Post API
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from post import views

router = DefaultRouter()
router.register('post', views.PostViewSet)
router.register('tags', views.TagViewSet)

app_name = 'post'
urlpatterns = [
    path('', include(router.urls))
]
