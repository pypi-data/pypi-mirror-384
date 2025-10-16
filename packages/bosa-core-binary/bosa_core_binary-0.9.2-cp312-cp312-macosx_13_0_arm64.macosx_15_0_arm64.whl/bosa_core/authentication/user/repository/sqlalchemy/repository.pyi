from _typeshed import Incomplete
from bosa_core.authentication.database import SQLAlchemySQLDataStore as SQLAlchemySQLDataStore
from bosa_core.authentication.user.repository.base_repository import BaseRepository as BaseRepository
from bosa_core.authentication.user.repository.models import UserModel as UserModel
from bosa_core.authentication.user.repository.sqlalchemy.models import DBUser as DBUser
from uuid import UUID

class SqlAlchemyUserRepository(BaseRepository):
    """User repository."""
    db: Incomplete
    def __init__(self, data_store: SQLAlchemySQLDataStore) -> None:
        """Initialize the repository.

        Args:
            data_store (SQLAlchemySQLDataStore): Data store.
        """
    def get_user(self, client_id: UUID, user_id: UUID) -> UserModel | None:
        """Retrieves a user.

        Args:
            client_id (UUID): Client ID.
            user_id (UUID): User ID.

        Returns:
            UserModel: User object.
        """
    def get_user_by_identifier(self, client_id: UUID, identifier: str) -> UserModel | None:
        """Retrieves a user.

        Args:
            client_id (UUID): Client ID.
            identifier (str): User identifier.

        Returns:
            UserModel | None: User object or None if not found.
        """
    def create_user(self, user: UserModel) -> UserModel:
        """Creates a new user.

        Args:
            user (UserModel): User model.

        Returns:
            UserModel: Created user.
        """
