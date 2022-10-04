from django.shortcuts import get_object_or_404
from rest_framework import exceptions, response, views


class BaseAPIView(views.APIView):
    lookup_field = "pk"
    model = None
    queryset = None

    @property
    def serializer(self):
        if not hasattr(self, "serializer"):
            raise exceptions.APIException(
                detail="Serializer not found", code="serializer_not_found"
            )
        return getattr(self, "serializer")

    @property
    def model(self):
        if not hasattr(self, "model"):
            raise exceptions.APIException(
                detail="Model not found", code="model_not_found"
            )
        return getattr(self, "model")

    def _get_queryset(self, lookup_value=None):
        user_id = (
            None if len(self.authentication_classes) == 0 else self.request.user.pk
        )
        if not self.model and not self.queryset:
            raise exceptions.APIException("`Both model` or `queryset` cannot be empty")

        lookup_payload = {self.lookup_field: lookup_value}
        if user_id:
            lookup_payload["user"] = user_id

        if lookup_value and not self.lookup_field:
            raise exceptions.APIException("`lookup_field` required")

        if not lookup_value:
            return self.queryset if self.queryset else self.model.objects.all()

        if not self.queryset:
            return get_object_or_404(self.model, **lookup_payload)

        return self.queryset.get(**lookup_payload)

    def get_queryset(self, lookup_value=None):
        return self._get_queryset(lookup_value)

    def get(self, request, pk=None):
        if pk:
            serializer = self.serializer(instance=self.get_queryset(pk))
        else:
            serializer = self.serializer(instance=self.get_queryset(), many=True)
        return response.Response(serializer.data)

    def post(self, request):
        serializer = self.serializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data, status=201)

    def put(self, request, pk=None):
        serializer = self.serializer(
            instance=self.get_queryset(pk),
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data, status=202)

    def delete(self, request, pk=None):
        instance = self.get_queryset(pk)
        instance.delete()
        return response.Response(status=204)
