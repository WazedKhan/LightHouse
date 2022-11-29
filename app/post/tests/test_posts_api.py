"""
Test Post APIs
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Post

from post.serializers import PostSerializer


POST_URL = reverse('post:post-list')


def create_post(user, **params):
    """create and return a sample post"""
    defaults = {
        'title': 'Sample title',
        'content': 'Sample content'
    }

    params.update(defaults)
    post = Post.objects.create(user=user, **params)
    return post


class PublicPostApiTests(TestCase):
    """Test unauthenticated API request"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call post API"""
        res = self.client.get(POST_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivatePostApiTests(TestCase):
    """Test authenticated API request"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create(
            email='user@example.com',
            password='pass123word'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_posts(self):
        """Test retrieving list of posts"""
        create_post(user=self.user)
        create_post(user=self.user)

        res = self.client.get(POST_URL)
        posts = Post.objects.all().order_by('-id')
        serializer = PostSerializer(posts, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)  # type: ignore

    def test_post_list_limited_to_user(self):
        """Test list of post is limited to authenticated user"""
        other_user = get_user_model().objects.create_user(  # type: ignore
            email='other@example.com',
            password='pass123word'
        )
        create_post(user=other_user)
        create_post(user=self.user)

        res = self.client.get(POST_URL)

        posts = Post.objects.filter(user=self.user)
        serializer = PostSerializer(posts, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)  # type: ignore
