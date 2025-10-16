"""
Basic building blocks for generic class based views.

We don't bind behaviour to http method handlers yet,
which allows mixin classes to be composed in interesting ways.
"""
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.settings import api_settings
from rest_framework.exceptions import NotFound

from .response import CustomResponse
from django.utils.translation import gettext as _


class CustomCreateModelMixin:
    """
    Create a model instance.
    """

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return CustomResponse(
            data=serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
            message=f"{self.get_serializer().Meta.model._meta.verbose_name} "
            + _("created successfully"),
        )

    def perform_create(self, serializer):
        serializer.save()

    def get_success_headers(self, data):
        try:
            return {"Location": str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}


class CustomListModelMixin:
    """
    List a queryset.
    """

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return CustomResponse(
            data=serializer.data,
            status=status.HTTP_200_OK,
            message=f"{self.get_serializer().Meta.model._meta.verbose_name_plural} "
            + _("retrieved successfully"),
        )



class ListSingleObjectMixin:
    """
    List a queryset and return a single object in an object-like response
    instead of a list. Raises an error if no object is found or if multiple objects exist.
    """
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        count = queryset.count()
        if count == 0:
            raise NotFound("No object found.")
        elif count > 1:
            raise ValidationError("Multiple objects found; expected a single object.")

        # Now that we have confirmed there is exactly one object, retrieve it.
        instance = queryset.first()

        serializer = self.get_serializer(instance, many=False)
        return CustomResponse(
            data=serializer.data,
            status=status.HTTP_200_OK,
            message=f"{self.get_serializer().Meta.model._meta.verbose_name} retrieved successfully",
        )

class CustomRetrieveModelMixin:
    """
    Retrieve a model instance.
    """

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return CustomResponse(
            serializer.data,
            status=status.HTTP_200_OK,
            message=f"{self.get_serializer().Meta.model._meta.verbose_name} "
            + _("retrieved successfully"),
        )


class CustomUpdateModelMixin:
    """
    Update a model instance.
    """

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return CustomResponse(
            data=serializer.data,
            message=f"{self.get_serializer().Meta.model._meta.verbose_name} "
            + _("updated successfully"),
            status=status.HTTP_200_OK,
        )

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class CustomDestroyModelMixin:
    """
    Destroy a model instance.
    """

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return CustomResponse(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()
