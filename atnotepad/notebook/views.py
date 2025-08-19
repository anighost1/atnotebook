from rest_framework import viewsets, permissions
from django.db.models import Q
from .models import Notebook, NotebookCollaborator
from .serializers import NotebookSerializer, NotebookCollaboratorSerializer
from rest_framework.exceptions import PermissionDenied


class NotebookViewSet(viewsets.ModelViewSet):
    serializer_class = NotebookSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        for_self = self.request.query_params.get("forSelf", "true").lower() == "true" # pyright: ignore[reportAttributeAccessIssue]
        for_collab = self.request.query_params.get("forCollab", "false").lower() == "true" # pyright: ignore[reportAttributeAccessIssue]

        if user.is_staff or user.is_superuser:
            return Notebook.objects.all()

        q_filter = Q()
        if for_self:
            q_filter |= Q(owner=user)
        if for_collab:
            q_filter |= Q(collaborators__user=user)

        return Notebook.objects.filter(q_filter).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def update(self, request, *args, **kwargs):
        notebook = self.get_object()
        user = request.user

        is_collaborator = notebook.collaborators.filter(user=user).exists()

        if notebook.owner != user and not is_collaborator:
            return Response(
                {"detail": "Only the owner or collaborators can edit this notebook."},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        notebook = self.get_object()
        user = request.user

        if notebook.owner != user:
            return Response(
                {"detail": "Only the owner can delete this notebook."},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().destroy(request, *args, **kwargs)


class NotebookCollaboratorViewSet(viewsets.ModelViewSet):
    queryset = NotebookCollaborator.objects.all()
    serializer_class = NotebookCollaboratorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return NotebookCollaborator.objects.all()

        return NotebookCollaborator.objects.filter(notebook__owner=user)

    def perform_create(self, serializer):
        notebook = serializer.validated_data["notebook"]
        collaborator_to_add = serializer.validated_data["user"]
        request_user = self.request.user
        request_user = self.request.user

        if notebook.owner != request_user and not request_user.is_staff and not request_user.is_superuser:
            raise PermissionDenied(
                "Only the notebook owner or an admin can add collaborators.")

        if collaborator_to_add == notebook.owner:
            raise serializer.ValidationError(
                "Notebook owner doesn't need to be added as a collaborator.")

        serializer.save()

    def update(self, request, *args, **kwargs):
        collab = self.get_object()
        user = request.user

        if collab.notebook.owner != user and not user.is_staff and not user.is_superuser:
            return Response(
                {"detail": "Only the notebook owner or an admin can update collaborators."},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        collab = self.get_object()
        user = request.user

        if collab.notebook.owner != user and not user.is_staff and not user.is_superuser:
            return Response(
                {"detail": "Only the notebook owner or an admin can remove collaborators."},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().destroy(request, *args, **kwargs)
