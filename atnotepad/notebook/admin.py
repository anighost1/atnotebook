from django.contrib import admin
from .models import Notebook, NotebookCollaborator


@admin.register(Notebook)
class NotebookAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'created_at')
    search_fields = ('title', 'owner__username')
    list_filter = ('created_at',)


@admin.register(NotebookCollaborator)
class NotebookCollaboratorAdmin(admin.ModelAdmin):
    list_display = ('user', 'notebook', 'role', 'joined_at')
    search_fields = ('user__username', 'notebook__title')
    list_filter = ('role', 'joined_at')
