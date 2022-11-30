"""Serializer for Post API"""

from rest_framework import serializers

from core.models import Post, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class PostSerializer(serializers.ModelSerializer):
    """Serializer for posts"""
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'tags']
        read_only_fields = ['id']

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        post = Post.objects.create(**validated_data)

        for tag in tags:
            tag_object, created = Tag.objects.get_or_create(
                user=self.context['request'].user,
                **tag
            )
            post.tags.add(tag_object)

        return post


class PostDetailSerializer(PostSerializer):
    """Post detail serializer"""

    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + ['created_at', 'updated_at']
