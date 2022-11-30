"""
Test cases for models.
"""
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def create_user(email='user@example.com', password='testpass123'):
    """Create a return a new user."""
    return get_user_model().objects.create_user(email, password)  # type: ignore # noqa


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with an email is successful."""
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(  # type: ignore
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'sample123')  # type: ignore # noqa
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test that creating a user without an email raises a ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')  # type: ignore

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = get_user_model().objects.create_superuser(  # type: ignore
            'test@example.com',
            'test123',
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_post(self):
        """Test creating a post is sccessful"""
        user = get_user_model().objects.create(
            email='user@example.com',
            password='pass123word'
        )

        post = models.Post.objects.create(
            user=user,
            title='New Post',
            content='Post Content',
        )
        self.assertEqual(str(post), post.title)

    def test_create_tag(self):
        """Test creating tag"""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='Earth')

        self.assertEqual(str(tag), tag.name)

    @patch('core.models.uuid.uuid4')
    def test_post_file_name_uuid(self, mock_uuid):
        """Test generating image path"""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.post_image_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/post/{uuid}.jpg')
