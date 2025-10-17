from rest_framework.response import Response
from rest_framework import status

from ...authentication.base import BaseAuthenticatedAPIView
from .client import TemplateAPI
from .serializers import (
    TemplateCreateSerializer,
    TemplateEditSerializer,
    TemplateIdSerializer,
    TemplateNameSerializer,
    TemplateDeleteByIdSerializer,
    TemplateListQuerySerializer,
)


class TemplateByIdView(BaseAuthenticatedAPIView):
    def get(self, request, template_id: str):
        api = TemplateAPI()
        resp = api.get_template_by_id(template_id)
        return Response(resp.json(), status=resp.status_code)

    def post(self, request, template_id: str):
        serializer = TemplateEditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        api = TemplateAPI()
        resp = api.edit_template(template_id, serializer.validated_data)
        return Response(resp.json() if resp.content else None, status=resp.status_code)


class TemplateByNameView(BaseAuthenticatedAPIView):
    def get(self, request):
        serializer = TemplateNameSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        api = TemplateAPI()
        resp = api.get_template_by_name(serializer.validated_data["name"])
        return Response(resp.json(), status=resp.status_code)

    def delete(self, request):
        serializer = TemplateNameSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        api = TemplateAPI()
        resp = api.delete_template_by_name(serializer.validated_data["name"])
        return Response(resp.json() if resp.content else None, status=resp.status_code)


class TemplateListCreateView(BaseAuthenticatedAPIView):
    def get(self, request):
        serializer = TemplateListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        api = TemplateAPI()
        resp = api.list_templates(**serializer.validated_data)
        return Response(resp.json(), status=resp.status_code)

    def post(self, request):
        serializer = TemplateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        api = TemplateAPI()
        resp = api.create_template(serializer.validated_data)
        return Response(resp.json(), status=resp.status_code)


class TemplateNamespaceView(BaseAuthenticatedAPIView):
    def get(self, request):
        api = TemplateAPI()
        resp = api.get_namespace()
        return Response(resp.json(), status=resp.status_code)


class TemplateDeleteByIdView(BaseAuthenticatedAPIView):
    def delete(self, request):
        serializer = TemplateDeleteByIdSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        api = TemplateAPI()
        resp = api.delete_template_by_id(
            serializer.validated_data["hsm_id"], serializer.validated_data["name"]
        )
        return Response(resp.json() if resp.content else None, status=resp.status_code)


