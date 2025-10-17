from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    asynccontextmanager,
    contextmanager,
)
from datetime import datetime, timezone
from pydantic import ValidationError
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from typing import (
    AsyncGenerator,
    Generator,
    Generic,
    Literal,
    Tuple,
    overload,
)
from uuid import uuid4
from maleo.logging.enums import Level
from maleo.logging.logger import EnvironmentT, ServiceKeyT, Database
from maleo.schemas.application import ApplicationContext, OptApplicationContext
from maleo.schemas.connection import OptConnectionContext
from maleo.schemas.error.enums import ErrorCode
from maleo.schemas.exception.exc import MaleoException
from maleo.schemas.exception.factory import Factory as MaleoExceptionFactory
from maleo.schemas.operation.action.system import SystemOperationAction
from maleo.schemas.operation.context import generate
from maleo.schemas.operation.enums import (
    OperationType,
    SystemOperationType,
    Origin,
    Layer,
    Target,
)
from maleo.schemas.operation.mixins import Timestamp
from maleo.schemas.operation.system import SuccessfulSystemOperation
from maleo.schemas.response import NoDataResponse
from maleo.schemas.security.authentication import OptAnyAuthentication
from maleo.schemas.security.authorization import OptAnyAuthorization
from maleo.schemas.security.impersonation import OptImpersonation
from maleo.types.uuid import OptUUID
from maleo.utils.exception import extract_details
from ..enums import Connection
from ..config import SQLConfigT


class SessionManager(Generic[SQLConfigT]):
    def __init__(
        self,
        config: SQLConfigT,
        engines: Tuple[AsyncEngine, Engine],
        logger: Database[EnvironmentT, ServiceKeyT],
        application_context: OptApplicationContext = None,
    ):
        self._config = config
        self._async_engine, self._sync_engine = engines
        self._logger = logger
        self._application_context = (
            application_context
            if application_context is not None
            else ApplicationContext.from_env()
        )
        self._operation_context = generate(
            origin=Origin.SERVICE,
            layer=Layer.UTILITY,
            target=Target.DATABASE,
            target_details=self._config.model_dump(
                exclude={"connection": {"password"}}
            ),
        )

        self._async_sessionmaker: async_sessionmaker[AsyncSession] = async_sessionmaker[
            AsyncSession
        ](bind=self._async_engine, expire_on_commit=True)
        self._sync_sessionmaker: sessionmaker[Session] = sessionmaker[Session](
            bind=self._sync_engine, expire_on_commit=True
        )

    async def _async_session_handler(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> AsyncGenerator[AsyncSession, None]:
        """Reusable function for managing async database session."""
        operation_id = operation_id if operation_id is not None else uuid4()
        operation_action = SystemOperationAction(
            type=SystemOperationType.DATABASE_CONNECTION, details=None
        )

        session: AsyncSession = self._async_sessionmaker()
        SuccessfulSystemOperation[NoDataResponse[None]](
            application_context=self._application_context,
            id=operation_id,
            context=self._operation_context,
            action=operation_action,
            timestamp=Timestamp.now(),
            summary="Successfully created new async database session",
            connection_context=connection_context,
            authentication=authentication,
            authorization=authorization,
            impersonation=impersonation,
            response=NoDataResponse[None](metadata=None, other=None),
        ).log(self._logger, level=Level.DEBUG)

        executed_at = datetime.now(tz=timezone.utc)

        try:
            # explicit transaction context — will commit on success, rollback on exception
            async with session.begin():
                yield session
            SuccessfulSystemOperation[NoDataResponse[None]](
                application_context=self._application_context,
                id=operation_id,
                context=self._operation_context,
                action=operation_action,
                timestamp=Timestamp.completed_now(executed_at),
                summary="Successfully committed async database transaction",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
                response=NoDataResponse[None](metadata=None, other=None),
            ).log(self._logger, level=Level.INFO)
        except SQLAlchemyError as se:
            await session.rollback()
            exc = MaleoExceptionFactory.from_code(
                ErrorCode.INTERNAL_SERVER_ERROR,
                details=extract_details(se),
                operation_type=OperationType.SYSTEM,
                application_context=self._application_context,
                operation_id=operation_id,
                operation_context=self._operation_context,
                operation_action=operation_action,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="SQLAlchemy error occured while handling async database session",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
            )
            exc.operation.log(self._logger, level=Level.ERROR)
            raise exc from se
        except ValidationError as ve:
            await session.rollback()
            exc = MaleoExceptionFactory.from_code(
                ErrorCode.UNPROCESSABLE_ENTITY,
                details=ve.errors(),
                operation_type=OperationType.SYSTEM,
                application_context=self._application_context,
                operation_id=operation_id,
                operation_context=self._operation_context,
                operation_action=operation_action,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="Validation error occured while handling async database session",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
            )
            exc.operation.log(self._logger, level=Level.ERROR)
            raise exc from ve
        except MaleoException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            exc = MaleoExceptionFactory.from_code(
                ErrorCode.INTERNAL_SERVER_ERROR,
                details=extract_details(e),
                operation_type=OperationType.SYSTEM,
                application_context=self._application_context,
                operation_id=operation_id,
                operation_context=self._operation_context,
                operation_action=operation_action,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="Unexpected error occured while handling async database session",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
            )
            exc.operation.log(self._logger, level=Level.ERROR)
            raise exc from e
        finally:
            await session.close()
            SuccessfulSystemOperation[NoDataResponse[None]](
                application_context=self._application_context,
                id=operation_id,
                context=self._operation_context,
                action=operation_action,
                timestamp=Timestamp.now(),
                summary="Successfully closed async database session",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
                response=NoDataResponse[None](metadata=None, other=None),
            ).log(self._logger, level=Level.INFO)

    def _sync_session_handler(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> Generator[Session, None, None]:
        """Reusable function for managing sync database session."""
        operation_id = operation_id if operation_id is not None else uuid4()
        operation_action = SystemOperationAction(
            type=SystemOperationType.DATABASE_CONNECTION, details=None
        )

        session: Session = self._sync_sessionmaker()
        SuccessfulSystemOperation[NoDataResponse[None]](
            application_context=self._application_context,
            id=operation_id,
            context=self._operation_context,
            action=operation_action,
            timestamp=Timestamp.now(),
            summary="Successfully created new sync database session",
            connection_context=connection_context,
            authentication=authentication,
            authorization=authorization,
            impersonation=impersonation,
            response=NoDataResponse[None](metadata=None, other=None),
        ).log(self._logger, level=Level.DEBUG)

        executed_at = datetime.now(tz=timezone.utc)

        try:
            # explicit transaction context — will commit on success, rollback on exception
            with session.begin():
                yield session
            SuccessfulSystemOperation[NoDataResponse[None]](
                application_context=self._application_context,
                id=operation_id,
                context=self._operation_context,
                action=operation_action,
                timestamp=Timestamp.completed_now(executed_at),
                summary="Successfully committed sync database transaction",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
                response=NoDataResponse[None](metadata=None, other=None),
            ).log(self._logger, level=Level.INFO)
        except SQLAlchemyError as se:
            session.rollback()  # Rollback on error
            exc = MaleoExceptionFactory.from_code(
                ErrorCode.INTERNAL_SERVER_ERROR,
                details=extract_details(se),
                operation_type=OperationType.SYSTEM,
                application_context=self._application_context,
                operation_id=operation_id,
                operation_context=self._operation_context,
                operation_action=operation_action,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="SQLAlchemy error occured while handling sync database session",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
            )
            exc.operation.log(self._logger, level=Level.ERROR)
            raise exc from se
        except ValidationError as ve:
            session.rollback()  # Rollback on error
            exc = MaleoExceptionFactory.from_code(
                ErrorCode.UNPROCESSABLE_ENTITY,
                details=ve.errors(),
                operation_type=OperationType.SYSTEM,
                application_context=self._application_context,
                operation_id=operation_id,
                operation_context=self._operation_context,
                operation_action=operation_action,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="Validation error occured while handling async database session",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
            )
            exc.operation.log(self._logger, level=Level.ERROR)
            raise exc from ve
        except MaleoException:
            session.rollback()  # Rollback on error
            raise
        except Exception as e:
            session.rollback()  # Rollback on error
            exc = MaleoExceptionFactory.from_code(
                ErrorCode.INTERNAL_SERVER_ERROR,
                details=extract_details(e),
                operation_type=OperationType.SYSTEM,
                application_context=self._application_context,
                operation_id=operation_id,
                operation_context=self._operation_context,
                operation_action=operation_action,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="Unexpected error occured while handling sync database session",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
            )
            exc.operation.log(self._logger, level=Level.ERROR)
            raise exc from e
        finally:
            session.close()  # Ensure session closes
            SuccessfulSystemOperation[NoDataResponse[None]](
                application_context=self._application_context,
                id=operation_id,
                context=self._operation_context,
                action=operation_action,
                timestamp=Timestamp.now(),
                summary="Successfully closed sync database session",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
                response=NoDataResponse[None](metadata=None, other=None),
            ).log(self._logger, level=Level.INFO)

    @asynccontextmanager
    async def _async_context_manager(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> AsyncGenerator[AsyncSession, None]:
        """Async context manager implementation."""
        async for session in self._async_session_handler(
            operation_id,
            connection_context,
            authentication,
            authorization,
            impersonation,
        ):
            yield session

    @contextmanager
    def _sync_context_manager(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> Generator[Session, None, None]:
        """Sync context manager implementation."""
        yield from self._sync_session_handler(
            operation_id,
            connection_context,
            authentication,
            authorization,
            impersonation,
        )

    # Overloaded context manager methods
    @overload
    def get(
        self,
        connection: Literal[Connection.ASYNC],
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> AbstractAsyncContextManager[AsyncSession]: ...

    @overload
    def get(
        self,
        connection: Literal[Connection.SYNC],
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> AbstractContextManager[Session]: ...

    def get(
        self,
        connection: Connection = Connection.ASYNC,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> AbstractAsyncContextManager[AsyncSession] | AbstractContextManager[Session]:
        """Context manager for manual session handling."""
        if operation_id is None:
            operation_id = uuid4()
        if connection is Connection.ASYNC:
            return self._async_context_manager(
                operation_id,
                connection_context,
                authentication,
                authorization,
                impersonation,
            )
        else:
            return self._sync_context_manager(
                operation_id,
                connection_context,
                authentication,
                authorization,
                impersonation,
            )

    # Alternative: More explicit methods
    @asynccontextmanager
    async def get_async(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> AsyncGenerator[AsyncSession, None]:
        """Explicit async context manager."""
        async for session in self._async_session_handler(
            operation_id,
            connection_context,
            authentication,
        ):
            yield session

    @contextmanager
    def get_sync(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> Generator[Session, None, None]:
        """Explicit sync context manager."""
        yield from self._sync_session_handler(
            operation_id,
            connection_context,
            authentication,
        )

    def as_async_dependency(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ):
        """Explicit async dependency injection."""

        def dependency() -> AsyncGenerator[AsyncSession, None]:
            return self._async_session_handler(
                operation_id,
                connection_context,
                authentication,
                authorization,
                impersonation,
            )

        return dependency

    def as_sync_dependency(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ):
        """Explicit sync dependency injection."""

        def dependency() -> Generator[Session, None, None]:
            return self._sync_session_handler(
                operation_id,
                connection_context,
                authentication,
                authorization,
                impersonation,
            )

        return dependency

    def dispose(self):
        self._sync_sessionmaker.close_all()
