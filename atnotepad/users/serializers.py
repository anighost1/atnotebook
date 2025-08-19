from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, FriendList
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'phone', 'address',
                  'is_verified', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_verified', 'created_at', 'updated_at']


class UserWithProfileSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password',
                  'first_name', 'last_name', 'profile']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        password = validated_data.pop('password')

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        UserProfile.objects.create(user=user, **profile_data)

        return user

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['profile'] = UserProfileSerializer(instance.profile).data
        return rep


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class FriendListSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    friend = SimpleUserSerializer(read_only=True)
    friend_id = serializers.PrimaryKeyRelatedField(
        source='friend',
        queryset=User.objects.all(),
        write_only=True
    )

    class Meta:
        model = FriendList
        fields = ['id', 'user', 'friend', 'friend_id', 'status', 'created_at']

    def validate(self, attrs):
        request_user = self.context['request'].user
        friend = attrs.get('friend')

        if request_user == friend:
            raise serializers.ValidationError(
                "You cannot be friends with yourself.")

        if FriendList.objects.filter(user=request_user, friend=friend).exists() or \
           FriendList.objects.filter(user=friend, friend=request_user).exists():
            raise serializers.ValidationError(
                "This friendship already exists.")

        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        user = request.user

        if instance.friend != user:
            raise PermissionDenied(
                "You are not allowed to perform this action.")

        status = validated_data.get('status', instance.status)
        instance.status = status
        instance.save()
        return instance
