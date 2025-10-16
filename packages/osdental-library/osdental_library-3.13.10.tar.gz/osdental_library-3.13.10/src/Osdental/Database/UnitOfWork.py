import asyncio
from typing import Dict, Any, Callable
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError, IntegrityError, DBAPIError, InvalidRequestError
from Osdental.Exception.ControlledException import OSDException, DatabaseException, UnexpectedException
from Osdental.Shared.Enums.Code import Code

class UnitOfWork:
    def __init__(self, session_factory: Callable[[], AsyncSession], repositories: Dict[str, Any] = None):
        self._session_factory = session_factory
        self._repositories = repositories or {}
        self._instances = {}
        self.session: AsyncSession | None = None

    def __getattr__(self, item):
        if item in self._instances:
            return self._instances[item]
        
        raise OSDException(error=f'UnitOfWork object has no attribute {item}')


    @asynccontextmanager
    async def __call__(self):
        try:
            async with self._session_factory() as session: 
                self.session = session
                self._instances = {name: repo_cls(self.session) for name, repo_cls in self._repositories.items()}
                async with self.session.begin():
                    yield self
        except asyncio.CancelledError:
            raise 
        except IntegrityError as ierr:
            raise DatabaseException(status_code=Code.INTEGRITY_DB_ERROR_CODE, error=str(ierr))
        except OperationalError as oerr:
            raise DatabaseException(status_code=Code.OPERATIONAL_DB_ERROR_CODE, error=str(oerr))
        except (DBAPIError, InvalidRequestError) as db_err:
            raise DatabaseException(status_code=Code.DB_UNKNOWN_ERROR_CODE, error=str(db_err))
        except OSDException:
            raise 
        except Exception as err:
            raise UnexpectedException(status_code=Code.DB_UNKNOWN_ERROR_CODE, error=str(err))
        finally:
            self._instances.clear()
