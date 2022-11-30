"""
Test Post APIs
"""
import os
import tempfile
from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Post, Tag

from post.serializers import PostSerializer, PostDetailSerializer


POST_URL = reverse('post:post-list')


def image_upload_url(post_id):
    """Create and return a image upload url"""
    return reverse('post:post-upload-image', args=[post_id])


def detail_url(post_id):
    """Create and returns a detail URL"""
    return reverse('post:post-detail', args=[post_id])


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)  # type: ignore


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
            email='test@example.com',
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

    def test_get_post_detail(self):
        """Test get post detail"""
        post = create_post(user=self.user)

        url = detail_url(post.id)  # type: ignore
        res = self.client.get(url)

        serializer = PostDetailSerializer(post)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)  # type: ignore

    def test_create_post(self):
        """Test creating a post"""
        payload = {
            'title': 'Test Title',
            'content': 'Test Content'
        }

        res = self.client.post(POST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(id=res.data['id'])  # type: ignore

        for k, v in payload.items():
            self.assertEqual(getattr(post, k), v)

        self.assertEqual(post.user, self.user)

    def test_full_update(self):
        """Test partial update of post"""
        post = create_post(
            user=self.user,
            title='Post Title',
            content='Post Content'
        )

        payload = {
            'title': 'Post Title Updated'
        }

        url = detail_url(post_id=post.id)  # type: ignore
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.title, payload['title'])
        self.assertEqual(post.user, self.user)

    def test_partial_update(self):
        """Test partial update of post"""
        post = create_post(
            user=self.user,
            title='Post Title',
            content='Post Content'
        )

        payload = {
            'title': 'Post Title Updated',
            'content': 'Post Content Updated'
        }

        url = detail_url(post_id=post.id)  # type: ignore
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.title, payload['title'])
        self.assertEqual(post.content, payload['content'])
        self.assertEqual(post.user, self.user)

    def test_update_user_response_error(self):
        """Test partial update of post"""
        post = create_post(
            user=self.user,
            title='Post Title',
            content='Post Content'
        )
        other_user = create_user(email='user2@exampl.com', password='test123')
        payload = {
            'user': other_user
        }

        url = detail_url(post_id=post.id)  # type: ignore
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        post.refresh_from_db()
        self.assertEqual(post.user, self.user)
        self.assertNotEqual(post.user, other_user)

    def test_delete_post(self):
        """Test deleting a post"""
        post = create_post(user=self.user)

        url = detail_url(post.id)  # type: ignore
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(id=post.id).exists())  # type: ignore # noqa

    def test_post_other_user_post_error(self):
        """Test tring to delete other user post gives error"""
        new_user = create_user(email='new@example.com', password='test123')
        post = create_post(user=new_user)

        url = detail_url(post.id)  # type: ignore
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Post.objects.filter(id=post.id).exists())  # type: ignore # noqa

    def test_create_post_with_new_tag(self):
        """Test creating a post with new tags."""
        payload = {
            'title': 'Post Title',
            'content': 'Post content',
            'tags': [{'name': 'Food'}, {'name': 'Health'}]
        }
        res = self.client.post(POST_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        posts = Post.objects.filter(user=self.user)
        self.assertEqual(posts.count(), 1)
        post = posts[0]
        self.assertEqual(post.tags.count(), 2)
        for tag in payload['tags']:
            exists = post.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_post_with_existing_tags(self):
        """Test creating a post with existing tag."""
        tag_road = Tag.objects.create(user=self.user, name='Roads')
        payload = {
            'title': 'Post Title',
            'content': 'Post content',
            'tags': [{'name': 'Roads'}, {'name': 'Safety'}]
        }

        res = self.client.post(POST_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        posts = Post.objects.filter(user=self.user)
        self.assertEqual(posts.count(), 1)
        post = posts[0]
        self.assertEqual(post.tags.count(), 2)
        self.assertIn(tag_road, post.tags.all())
        for tag in payload['tags']:
            exists = post.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test create tag when updating a post."""
        post = create_post(user=self.user)
        payload = {'tags': [{'name': 'Food'}]}

        url = detail_url(post.id)  # type: ignore
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Food')
        self.assertIn(new_tag, post.tags.all())

    def test_update_post_assign_tag(self):
        """Test assigning an existing tag when updating a post."""
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        post = create_post(user=self.user)
        post.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(post.id)  # type: ignore
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, post.tags.all())
        self.assertNotIn(tag_breakfast, post.tags.all())

    def test_clear_post_tags(self):
        """Test clearing a posts tags."""
        tag = Tag.objects.create(user=self.user, name='Dessert')
        post = create_post(user=self.user)
        post.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(post.id)  # type: ignore
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(post.tags.count(), 0)


class ImageUplaodTests(TestCase):
    """Test for the image upload API"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='test@example.com', password='test123')
        self.client.force_authenticate(self.user)
        self.post = create_post(self.user)

    def tearDown(self):
        self.post.image.delete()

    def test_upload_image(self):
        """Test uploading image to a post"""
        url = image_upload_url(self.post.id)  # type: ignore

        with tempfile.NamedTemporaryFile(suffix='.jpg') as img_file:
            img = Image.new('RGB', (10, 10))
            img.save(img_file, format='JPEG')
            img_file.seek(0)
            payload = {'image': img_file}
            res = self.client.post(url, payload, format='multipart')

        self.post.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)  # type: ignore
        self.assertTrue(os.path.exists(self.post.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading a invalid image"""
        url = image_upload_url(self.post.id)  # type: ignore
        payload = {'image': 'notanimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
