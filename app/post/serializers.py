"""Serializer for Post API"""

from rest_framework import serializers

from core.models import Post, Tag


class PostSerializer(serializers.ModelSerializer):
    """Serializer for posts"""

    class Meta:
        model = Post
        fields = ['id', 'title', 'content']
        read_only_fields = ['id']


class PostDetailSerializer(PostSerializer):
    """Post detail serializer"""

    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + ['created_at', 'updated_at']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']
