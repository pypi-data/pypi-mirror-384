import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Literal, Union, overload
from uuid import UUID
from maleo.client.maleo.config import MaleoMetadataClientConfig
from maleo.client.maleo.service import MaleoClientService
from maleo.database.enums import Connection
from maleo.database.utils import build_cache_key
from maleo.enums.cardinality import Cardinality
from maleo.enums.connection import Header
from maleo.logging.enums import Level
from maleo.metadata.constants.medical_service import MEDICAL_SERVICE_RESOURCE
from maleo.metadata.schemas.medical_service import (
    ReadMultipleParameter,
    ReadSingleParameter,
    StandardMedicalServiceSchema,
    FullMedicalServiceSchema,
)
from maleo.metadata.enums.medical_service import Granularity, IdentifierType
from maleo.metadata.utils.medical_service import get_schema_model
from maleo.schemas.connection import ConnectionContext
from maleo.schemas.exception.factory import Factory as MaleoExceptionFactory
from maleo.schemas.operation.action.resource import ReadResourceOperationAction
from maleo.schemas.operation.enums import OperationType, Target
from maleo.schemas.operation.mixins import Timestamp
from maleo.schemas.operation.resource import (
    ReadMultipleResourceOperation,
    ReadSingleResourceOperation,
)
from maleo.schemas.pagination import StrictPagination
from maleo.schemas.response import (
    MultipleDataResponse,
    ReadMultipleDataResponse,
    SingleDataResponse,
    ReadSingleDataResponse,
)
from maleo.schemas.security.authorization import (
    OptionalAnyAuthorization,
    AnyAuthorization,
    Factory as AuthorizationFactory,
)
from maleo.schemas.security.impersonation import OptionalImpersonation
from maleo.types.dict import OptionalStringToStringDict
from maleo.utils.merger import merge_dicts


class MedicalServiceClientService(MaleoClientService[MaleoMetadataClientConfig]):
    resource = MEDICAL_SERVICE_RESOURCE

    @overload
    async def read(
        self,
        cardinality: Literal[Cardinality.MULTIPLE],
        granularity: Literal[Granularity.STANDARD],
        *,
        operation_id: UUID,
        resource_operation_action: ReadResourceOperationAction,
        connection_context: ConnectionContext,
        authorization: AnyAuthorization,
        impersonation: OptionalImpersonation = None,
        parameters: ReadMultipleParameter,
        headers: OptionalStringToStringDict = None,
    ) -> ReadMultipleDataResponse[
        StandardMedicalServiceSchema, StrictPagination, None
    ]: ...
    @overload
    async def read(
        self,
        cardinality: Literal[Cardinality.MULTIPLE],
        granularity: Literal[Granularity.FULL],
        *,
        operation_id: UUID,
        resource_operation_action: ReadResourceOperationAction,
        connection_context: ConnectionContext,
        authorization: AnyAuthorization,
        impersonation: OptionalImpersonation = None,
        parameters: ReadMultipleParameter,
        headers: OptionalStringToStringDict = None,
    ) -> ReadMultipleDataResponse[FullMedicalServiceSchema, StrictPagination, None]: ...
    @overload
    async def read(
        self,
        cardinality: Literal[Cardinality.SINGLE],
        granularity: Literal[Granularity.STANDARD],
        *,
        operation_id: UUID,
        resource_operation_action: ReadResourceOperationAction,
        connection_context: ConnectionContext,
        authorization: AnyAuthorization,
        impersonation: OptionalImpersonation = None,
        parameters: ReadSingleParameter,
        headers: OptionalStringToStringDict = None,
    ) -> ReadSingleDataResponse[StandardMedicalServiceSchema, None]: ...
    @overload
    async def read(
        self,
        cardinality: Literal[Cardinality.SINGLE],
        granularity: Literal[Granularity.FULL],
        *,
        operation_id: UUID,
        resource_operation_action: ReadResourceOperationAction,
        connection_context: ConnectionContext,
        authorization: AnyAuthorization,
        impersonation: OptionalImpersonation = None,
        parameters: ReadSingleParameter,
        headers: OptionalStringToStringDict = None,
    ) -> ReadSingleDataResponse[FullMedicalServiceSchema, None]: ...
    async def read(
        self,
        cardinality: Cardinality,
        granularity: Granularity,
        *,
        operation_id: UUID,
        resource_operation_action: ReadResourceOperationAction,
        connection_context: ConnectionContext,
        authorization: OptionalAnyAuthorization = None,
        impersonation: OptionalImpersonation = None,
        parameters: Union[ReadMultipleParameter, ReadSingleParameter],
        headers: OptionalStringToStringDict = None,
    ) -> Union[
        ReadMultipleDataResponse[StandardMedicalServiceSchema, StrictPagination, None],
        ReadMultipleDataResponse[FullMedicalServiceSchema, StrictPagination, None],
        ReadSingleDataResponse[StandardMedicalServiceSchema, None],
        ReadSingleDataResponse[FullMedicalServiceSchema, None],
    ]:
        redis_client = self._redis.manager.client.get(Connection.ASYNC)
        data_model_cls = get_schema_model(granularity)

        executed_at = datetime.now(tz=timezone.utc)

        # Define arguments being used in this function
        positional_arguments = [cardinality, granularity]
        keyword_arguments = {
            "authorization": (
                authorization.model_dump(mode="json")
                if authorization is not None
                else None
            ),
            "parameters": parameters.model_dump(mode="json"),
        }

        # Define full function string
        ext = f"({json.dumps(positional_arguments)}|{json.dumps(keyword_arguments)})"

        # Define full cache_key
        cache_key = build_cache_key(ext, namespace=self._namespace)

        if parameters.use_cache:
            # Initialize cache operation context
            operation_context = deepcopy(self._operation_context)
            operation_context.target.type = Target.CACHE

            redis_response_str = await redis_client.get(cache_key)

            if redis_response_str is not None:
                operation_timestamp = Timestamp.completed_now(executed_at)
                if cardinality is Cardinality.MULTIPLE:
                    response = ReadMultipleDataResponse[
                        data_model_cls, StrictPagination, None
                    ].model_validate_json(redis_response_str)
                    ReadMultipleResourceOperation[
                        data_model_cls, StrictPagination, None
                    ](
                        application_context=self._application_context,
                        id=operation_id,
                        context=operation_context,
                        action=resource_operation_action,
                        resource=self.resource,
                        timestamp=operation_timestamp,
                        summary=f"Successfully retrieved {cardinality} {granularity} medical services from cache",
                        connection_context=connection_context,
                        authentication=None,
                        authorization=authorization,
                        impersonation=impersonation,
                        response=response,
                    ).log(
                        self._logger, Level.INFO
                    )
                elif cardinality is Cardinality.SINGLE:
                    response = ReadSingleDataResponse[
                        data_model_cls, None
                    ].model_validate_json(redis_response_str)
                    ReadSingleResourceOperation[data_model_cls, None](
                        application_context=self._application_context,
                        id=operation_id,
                        context=operation_context,
                        action=resource_operation_action,
                        resource=self.resource,
                        timestamp=operation_timestamp,
                        summary=f"Successfully retrieved {cardinality} {granularity} medical service from cache",
                        connection_context=connection_context,
                        authentication=None,
                        authorization=authorization,
                        impersonation=impersonation,
                        response=response,
                    ).log(self._logger, Level.INFO)

                return response  # type: ignore

        operation_context = deepcopy(self._operation_context)
        operation_context.target.type = Target.MICROSERVICE

        async with self._http_client_manager.get() as http_client:
            base_headers = {
                Header.CONTENT_TYPE.value: "application/json",
                Header.X_OPERATION_ID.value: str(operation_id),
            }
            if impersonation is not None:
                base_headers[Header.X_USER_ID.value] = str(impersonation.user_id)
                if impersonation.organization_id is not None:
                    base_headers[Header.X_ORGANIZATION_ID.value] = str(
                        impersonation.organization_id
                    )

            if headers is not None:
                headers = merge_dicts(base_headers, headers)
            else:
                headers = base_headers

            if authorization is not None:
                auth = AuthorizationFactory.httpx_auth(
                    scheme=authorization.scheme, authorization=authorization.credentials
                )
            else:
                auth = None

            if isinstance(parameters, ReadMultipleParameter):
                url = f"{self._config.url}/v1/{self.resource.identifiers[-1].slug}/"
            elif isinstance(parameters, ReadSingleParameter):
                if parameters.identifier is IdentifierType.ID:
                    url = f"{self._config.url}/v1/{self.resource.identifiers[-1].slug}/{parameters.value}"
                else:
                    url = f"{self._config.url}/v1/{self.resource.identifiers[-1].slug}/{parameters.identifier}/{parameters.value}"

            params = parameters.to_query_params()

            response = await http_client.get(
                url, params=params, headers=headers, auth=auth
            )

            operation_timestamp = Timestamp.completed_now(executed_at)

            if response.is_error:
                raise MaleoExceptionFactory.from_httpx(
                    response,
                    operation_type=OperationType.REQUEST,
                    application_context=self._application_context,
                    operation_id=operation_id,
                    operation_context=operation_context,
                    operation_action=resource_operation_action,
                    operation_timestamp=operation_timestamp,
                    connection_context=connection_context,
                    authentication=None,
                    authorization=authorization,
                    impersonation=impersonation,
                    logger=self._logger,
                )

            if isinstance(parameters, ReadMultipleParameter):
                validated_response = MultipleDataResponse[
                    data_model_cls, StrictPagination, None
                ].model_validate(response.json())
                service_response = ReadMultipleDataResponse[
                    data_model_cls, StrictPagination, None
                ].new(
                    data=validated_response.data,
                    pagination=validated_response.pagination,
                )
                ReadMultipleResourceOperation[data_model_cls, StrictPagination, None](
                    application_context=self._application_context,
                    id=operation_id,
                    context=operation_context,
                    action=resource_operation_action,
                    resource=MEDICAL_SERVICE_RESOURCE,
                    timestamp=operation_timestamp,
                    summary=f"Successfully retrieved multiple {granularity} medical services from microservice",
                    connection_context=connection_context,
                    authentication=None,
                    authorization=authorization,
                    impersonation=impersonation,
                    response=service_response,
                ).log(self._logger, Level.INFO)
            elif isinstance(parameters, ReadSingleParameter):
                validated_response = SingleDataResponse[
                    data_model_cls, None
                ].model_validate(response.json())
                service_response = ReadSingleDataResponse[data_model_cls, None].new(
                    data=validated_response.data,
                )
                ReadSingleResourceOperation[data_model_cls, None](
                    application_context=self._application_context,
                    id=operation_id,
                    context=operation_context,
                    action=resource_operation_action,
                    resource=MEDICAL_SERVICE_RESOURCE,
                    timestamp=operation_timestamp,
                    summary=f"Successfully retrieved single {granularity} medical service from microservice",
                    connection_context=connection_context,
                    authentication=None,
                    authorization=authorization,
                    impersonation=impersonation,
                    response=service_response,
                ).log(self._logger, Level.INFO)

            return service_response  # type: ignore
