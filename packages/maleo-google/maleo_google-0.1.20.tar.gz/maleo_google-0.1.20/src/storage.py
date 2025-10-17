import os
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from google.cloud.storage import Bucket, Client
from pydantic import BaseModel, Field
from typing import Annotated
from uuid import uuid4
from maleo.database.enums import Connection
from maleo.database.managers import RedisManager
from maleo.database.enums import CacheOrigin, CacheLayer
from maleo.database.utils import build_cache_namespace, build_cache_key
from maleo.enums.expiration import Expiration
from maleo.logging.config import LogConfig
from maleo.logging.enums import Level
from maleo.schemas.application import OptApplicationContext
from maleo.schemas.connection import OptConnectionContext
from maleo.schemas.data import DataPair
from maleo.schemas.error.enums import ErrorCode
from maleo.schemas.exception.factory import Factory as MaleoExceptionFactory
from maleo.schemas.operation.enums import (
    OperationType,
    ResourceOperationType,
    ResourceOperationCreateType,
    Target as OperationTarget,
)
from maleo.schemas.operation.mixins import Timestamp
from maleo.schemas.operation.resource import (
    CreateResourceOperationAction,
    ReadResourceOperationAction,
    CreateSingleResourceOperation,
    ReadSingleResourceOperation,
)
from maleo.schemas.resource import AggregateField, ResourceIdentifier
from maleo.schemas.response import (
    SingleDataResponse,
    CreateSingleDataResponse,
    ReadSingleDataResponse,
)
from maleo.schemas.security.authentication import OptAnyAuthentication
from maleo.schemas.security.authorization import OptAnyAuthorization
from maleo.schemas.security.impersonation import OptImpersonation
from maleo.types.misc import OptPathOrStr
from maleo.types.string import OptStr
from maleo.types.uuid import OptUUID
from maleo.utils.exception import extract_details
from .base import GOOGLE_RESOURCE, GoogleClientManager
from .types import OptionalCredentials


CLOUD_STORAGE_RESOURCE = deepcopy(GOOGLE_RESOURCE)
CLOUD_STORAGE_RESOURCE.identifiers.append(
    ResourceIdentifier(key="cloud_storage", name="Cloud Storage", slug="cloud-storage")
)


class Asset(BaseModel):
    url: Annotated[str, Field(..., description="Asset's URL")]


class GoogleCloudStorage(GoogleClientManager):
    def __init__(
        self,
        log_config: LogConfig,
        *,
        application_context: OptApplicationContext = None,
        credentials: OptionalCredentials = None,
        credentials_path: OptPathOrStr = None,
        bucket_name: OptStr = None,
        redis: RedisManager,
    ) -> None:
        super().__init__(
            CLOUD_STORAGE_RESOURCE.aggregate(),
            CLOUD_STORAGE_RESOURCE.aggregate(AggregateField.NAME),
            log_config,
            application_context,
            credentials,
            credentials_path,
        )
        self._client = Client(credentials=self._credentials)

        self._bucket_name = None
        if bucket_name is not None:
            self._bucket_name = bucket_name
        else:
            env_bucket_name = os.getenv("GCS_BUCKET_NAME", None)
            if env_bucket_name is not None:
                self._bucket_name = env_bucket_name

        if self._bucket_name is None:
            self._client.close()
            raise ValueError(
                "Unable to determine 'bucket_name' either from argument or environment variable"
            )

        self._bucket = self._client.lookup_bucket(bucket_name=self._bucket_name)
        if self._bucket is None:
            self._client.close()
            raise ValueError(f"Bucket '{self._bucket_name}' does not exist.")

        self._redis = redis
        self._namespace = build_cache_namespace(
            CLOUD_STORAGE_RESOURCE.aggregate(AggregateField.KEY, sep=":"),
            base=self._application_context.service_key,
            client=self._key,
            origin=CacheOrigin.CLIENT,
            layer=CacheLayer.SERVICE,
        )

        self._root_location = self._application_context.service_key

    @property
    def bucket(self) -> Bucket:
        if self._bucket is None:
            raise ValueError("Bucket has not been initialized.")
        return self._bucket

    async def upload(
        self,
        content: bytes,
        location: str,
        content_type: OptStr = None,
        *,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        root_location_override: OptStr = None,
        make_public: bool = False,
        use_cache: bool = True,
        expiration: Expiration = Expiration.EXP_15MN,
    ) -> SingleDataResponse[Asset, None]:
        operation_id = operation_id if operation_id is not None else uuid4()
        operation_action = CreateResourceOperationAction(
            type=ResourceOperationType.CREATE,
            create_type=ResourceOperationCreateType.NEW,
        )

        executed_at = datetime.now(tz=timezone.utc)

        if root_location_override is None or (
            isinstance(root_location_override, str) and len(root_location_override) <= 0
        ):
            blob_name = f"{self._root_location}/{location}"
        else:
            blob_name = f"{root_location_override}/{location}"

        resource = deepcopy(CLOUD_STORAGE_RESOURCE)
        resource.details = {"location": location, "blob_name": blob_name}

        try:
            blob = self.bucket.blob(blob_name=blob_name)
            blob.upload_from_string(content, content_type=content_type or "text/plain")

            if make_public:
                blob.make_public()
                url = blob.public_url
            else:
                url = blob.generate_signed_url(
                    version="v4",
                    expiration=timedelta(seconds=expiration.value),
                    method="GET",
                )

            if use_cache:
                client = self._redis.client.get(Connection.ASYNC)
                cache_key = build_cache_key(blob_name, namespace=self._namespace)
                await client.set(name=cache_key, value=url, ex=expiration.value)

            asset = Asset(url=url)
            operation_response_data = DataPair[None, Asset](
                old=None,
                new=asset,
            )
            operation_response = CreateSingleDataResponse[Asset, None](
                data=operation_response_data, metadata=None, other=None
            )
            CreateSingleResourceOperation[Asset, None](
                application_context=self._application_context,
                id=operation_id,
                context=self._operation_context,
                action=operation_action,
                timestamp=Timestamp.completed_now(executed_at),
                summary=f"Successfully uploaded object to '{location}'",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
                resource=resource,
                response=operation_response,
            ).log(self._logger, Level.INFO)
            return SingleDataResponse[Asset, None](
                data=asset, metadata=None, other=None
            )
        except Exception as e:
            exc = MaleoExceptionFactory.from_code(
                ErrorCode.INTERNAL_SERVER_ERROR,
                details=extract_details(e),
                operation_type=OperationType.RESOURCE,
                application_context=self._application_context,
                operation_id=operation_id,
                operation_context=self._operation_context,
                operation_action=operation_action,
                resource=resource,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary=f"Unexpected error raised while uploading object to '{location}'",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
            )
            raise exc from e

    async def generate_signed_url(
        self,
        location: str,
        *,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        root_location_override: OptStr = None,
        use_cache: bool = True,
        expiration: Expiration = Expiration.EXP_15MN,
    ) -> SingleDataResponse[Asset, None]:
        operation_id = operation_id if operation_id is not None else uuid4()
        operation_action = ReadResourceOperationAction()

        executed_at = datetime.now(tz=timezone.utc)

        if root_location_override is None or (
            isinstance(root_location_override, str) and len(root_location_override) <= 0
        ):
            blob_name = f"{self._root_location}/{location}"
        else:
            blob_name = f"{root_location_override}/{location}"

        resource = deepcopy(CLOUD_STORAGE_RESOURCE)
        resource.details = {"location": location, "blob_name": blob_name}

        if use_cache:
            client = self._redis.client.get(Connection.ASYNC)
            cache_key = build_cache_key(blob_name, namespace=self._namespace)
            url = await client.get(cache_key)
            if url is not None:
                operation_context = deepcopy(self._operation_context)
                operation_context.target.type = OperationTarget.CACHE
                asset = Asset(url=url)
                operation_response_data = DataPair[Asset, None](old=asset, new=None)
                operation_response = ReadSingleDataResponse[Asset, None](
                    data=operation_response_data, metadata=None, other=None
                )
                ReadSingleResourceOperation[Asset, None](
                    application_context=self._application_context,
                    id=operation_id,
                    context=operation_context,
                    action=operation_action,
                    resource=resource,
                    timestamp=Timestamp.completed_now(executed_at),
                    summary=f"Successfully retrieved signed url for '{location}' from cache",
                    connection_context=connection_context,
                    authentication=authentication,
                    authorization=authorization,
                    impersonation=impersonation,
                    response=operation_response,
                ).log(self._logger, Level.INFO)

                return SingleDataResponse[Asset, None](
                    data=asset, metadata=None, other=None
                )

        blob = self.bucket.blob(blob_name=blob_name)
        if not blob.exists():
            exc = MaleoExceptionFactory.from_code(
                ErrorCode.NOT_FOUND,
                operation_type=OperationType.RESOURCE,
                application_context=self._application_context,
                operation_id=operation_id,
                operation_context=self._operation_context,
                operation_action=operation_action,
                resource=resource,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary=f"Asset '{location}' not found",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
            )
            raise exc

        url = blob.generate_signed_url(
            version="v4", expiration=timedelta(seconds=expiration.value), method="GET"
        )

        if use_cache:
            client = self._redis.client.get(Connection.ASYNC)
            cache_key = build_cache_key(blob_name, namespace=self._namespace)
            await client.set(name=cache_key, value=url, ex=expiration.value)

        asset = Asset(url=url)
        operation_response_data = DataPair[Asset, None](old=asset, new=None)
        operation_response = ReadSingleDataResponse[Asset, None](
            data=operation_response_data, metadata=None, other=None
        )
        ReadSingleResourceOperation[Asset, None](
            application_context=self._application_context,
            id=operation_id,
            context=self._operation_context,
            action=operation_action,
            resource=resource,
            timestamp=Timestamp.completed_now(executed_at),
            summary=f"Successfully generated signed url for asset '{location}'",
            connection_context=connection_context,
            authentication=authentication,
            authorization=authorization,
            impersonation=impersonation,
            response=operation_response,
        ).log(self._logger, Level.INFO)

        return SingleDataResponse[Asset, None](data=asset, metadata=None, other=None)
