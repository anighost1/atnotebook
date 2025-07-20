from rest_framework import serializers
from .models import Notebook, NotebookCollaborator
from django.contrib.auth import get_user_model

User = get_user_model()


class NotebookSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    collaborators = serializers.SerializerMethodField()

    class Meta:
        model = Notebook
        fields = ['id', 'title', 'content', 'owner',
                  'created_at', 'updated_at', 'collaborators']

    def get_collaborators(self, obj):
        collaborators = obj.collaborators.select_related('user').all()
        return [
            {
                'user_id': str(collab.user.id),
                'username': collab.user.username,
                'role': collab.role,
            }
            for collab in collaborators
        ]


class NotebookCollaboratorSerializer(serializers.ModelSerializer):
    # user = serializers.SlugRelatedField(
    #     slug_field='username', queryset=User.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    notebook = serializers.PrimaryKeyRelatedField(
        queryset=Notebook.objects.all())

    class Meta:
        model = NotebookCollaborator
        fields = ['id', 'notebook', 'user', 'role', 'joined_at']
