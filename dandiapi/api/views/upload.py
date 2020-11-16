from __future__ import annotations

from typing import Dict

from django.http.response import HttpResponseBase
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    parser_classes,
    permission_classes,
)
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from s3_file_field._multipart import MultipartManager, TransferredPart, TransferredParts

from dandiapi.api.models import Validation
from dandiapi.api.tasks import validate
from dandiapi.api.views.serializers import ValidationSerializer


class UploadInitializationRequestSerializer(serializers.Serializer):
    file_name = serializers.CharField(trim_whitespace=False)
    file_size = serializers.IntegerField(min_value=1)


class PartInitializationResponseSerializer(serializers.Serializer):
    part_number = serializers.IntegerField(min_value=1)
    size = serializers.IntegerField(min_value=1)
    upload_url = serializers.URLField()


class UploadInitializationResponseSerializer(serializers.Serializer):
    object_key = serializers.CharField(trim_whitespace=False)
    upload_id = serializers.CharField()
    parts = PartInitializationResponseSerializer(many=True, allow_empty=False)


class PartCompletionRequestSerializer(serializers.Serializer):
    part_number = serializers.IntegerField(min_value=1)
    size = serializers.IntegerField(min_value=1)
    etag = serializers.CharField()

    def create(self, validated_data) -> TransferredPart:
        return TransferredPart(**validated_data)


class UploadCompletionRequestSerializer(serializers.Serializer):
    object_key = serializers.CharField(trim_whitespace=False)
    upload_id = serializers.CharField()
    parts = PartCompletionRequestSerializer(many=True, allow_empty=False)

    def create(self, validated_data) -> TransferredParts:
        parts = [
            TransferredPart(**part)
            for part in sorted(validated_data.pop('parts'), key=lambda part: part['part_number'])
        ]
        return TransferredParts(parts=parts, **validated_data)


class UploadCompletionResponseSerializer(serializers.Serializer):
    complete_url = serializers.URLField()
    body = serializers.CharField(trim_whitespace=False)


class UploadValidationRequestSerializer(serializers.Serializer):
    object_key = serializers.CharField(trim_whitespace=False, required=False)
    sha256 = serializers.CharField(trim_whitespace=False)


@swagger_auto_schema(
    method='POST',
    request_body=UploadInitializationRequestSerializer(),
    responses={200: UploadInitializationResponseSerializer()},
)
@api_view(['POST'])
@parser_classes([JSONParser])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def upload_initialize_view(request: Request) -> HttpResponseBase:
    """
    Initialize a multipart upload.

    A list of parts will be returned, each of which has a presigned upload URL and a size.
    This URL communicates directly with the object store so the client can upload bytes directly.

    https://docs.aws.amazon.com/AmazonS3/latest/dev/mpuoverview.html
    """
    request_serializer = UploadInitializationRequestSerializer(data=request.data)
    request_serializer.is_valid(raise_exception=True)
    upload_request: Dict = request_serializer.validated_data

    # TODO The first argument to generate_filename() is an instance of the model.
    # We do not and will never have an instance of the model during field upload.
    # Maybe we need a different generate method/upload_to with a different signature?
    object_key = Validation.blob.field.storage.generate_filename(upload_request['file_name'])

    initialization = MultipartManager.from_storage(Validation.blob.field.storage).initialize_upload(
        object_key, upload_request['file_size']
    )

    response_serializer = UploadInitializationResponseSerializer(initialization)
    return Response(response_serializer.data)


@swagger_auto_schema(
    method='POST',
    request_body=UploadCompletionRequestSerializer(),
    responses={200: UploadCompletionResponseSerializer()},
)
@api_view(['POST'])
@parser_classes([JSONParser])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def upload_complete_view(request: Request) -> HttpResponseBase:
    """
    Complete a multipart upload.

    After all data has been uploaded using the URLs provided by initialize, this endpoint must
    be called to create the object in the object store. A presigned URL that performs the
    completion is returned, as the completion might take several minutes for large files.
    """
    request_serializer = UploadCompletionRequestSerializer(data=request.data)
    request_serializer.is_valid(raise_exception=True)
    completion: TransferredParts = request_serializer.save()

    completed_upload = MultipartManager.from_storage(Validation.blob.field.storage).complete_upload(
        completion
    )

    response_serializer = UploadCompletionResponseSerializer(
        {
            'complete_url': completed_upload.complete_url,
            'body': completed_upload.body,
        }
    )
    return Response(response_serializer.data)


@swagger_auto_schema(
    method='POST', request_body=UploadValidationRequestSerializer(), responses={204: 'No content'}
)
@api_view(['POST'])
@parser_classes([JSONParser])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def upload_validate_view(request: Request) -> HttpResponseBase:
    """
    Start the validation process for an existing object.

    The validation process checks that the given sha256 checksum matches the checksum calculated on
    the uploaded object, and that Dandi CLI validation succeeds. Validation must succeed before an
    asset can be registered.
    If the object_key is not specified, it will be looked up using the sha256 checksum if a valid
    object has been validated before. This allows clients to check if blobs have already been
    uploaded before uploading it themselves.
    """
    request_serializer = UploadValidationRequestSerializer(data=request.data)
    request_serializer.is_valid(raise_exception=True)
    # validation: Validation = request_serializer.save()

    # Use the validation from the DB if it already exists
    try:
        validation = Validation.objects.get(sha256=request_serializer.validated_data['sha256'])
        # Concurrent validation creates a race condition in celery, so avoid it if possible
        if validation.state == Validation.State.IN_PROGRESS:
            raise ValidationError('Validation already in progress.')
        validation.state = Validation.State.IN_PROGRESS
    except Validation.DoesNotExist:
        if 'object_key' not in request_serializer.validated_data:
            raise ValidationError('A validation for an object with that checksum does not exist.')
        validation = Validation(
            blob=request_serializer.validated_data['object_key'],
            sha256=request_serializer.validated_data['sha256'],
            state=Validation.State.IN_PROGRESS,
        )

    if not validation.object_key_exists():
        raise ValidationError('Object does not exist.')

    validation.save()

    validate.delay(validation.id)
    return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(method='GET', responses={200: ValidationSerializer()})
@api_view(['GET'])
@parser_classes([JSONParser])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def upload_get_validation_view(request: Request, sha256: str) -> HttpResponseBase:
    """Get the status of a validation."""
    validation = get_object_or_404(Validation, sha256=sha256)

    response_serializer = ValidationSerializer(validation)
    return Response(response_serializer.data)
