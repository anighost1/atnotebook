from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Notebook(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='owned_notebook')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notebook'

    def __str__(self):
        return self.title


class NotebookCollaborator(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    notebook = models.ForeignKey(
        Notebook, on_delete=models.CASCADE, related_name='collaborators')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='collaborations')
    role = models.CharField(max_length=20, choices=[(
        'editor', 'Editor'), ('viewer', 'Viewer')], default='editor')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notebook_collaborator'
        unique_together = ('notebook', 'user')

    def __str__(self):
        return f'{self.user.username} → {self.notebook.title}'
