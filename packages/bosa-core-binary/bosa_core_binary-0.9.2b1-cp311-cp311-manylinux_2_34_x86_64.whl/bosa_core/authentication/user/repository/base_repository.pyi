import abc
from abc import ABC, abstractmethod
from bosa_core.authentication.user.repository.models import UserModel as UserModel
from uuid import UUID

class BaseRepository(ABC, metaclass=abc.ABCMeta):
    """Base repository interface."""
    @abstractmethod
    def get_user(self, client_id: UUID, user_id: UUID) -> UserModel:
        """Get user.

        Args:
            client_id (UUID): Client ID.
            user_id (UUID): User ID.

        Returns:
            UserModel: The user model
        """
    @abstractmethod
    def get_user_by_identifier(self, client_id: UUID, identifier: str) -> UserModel:
        """Get user by identifier.

        Args:
            client_id (UUID): Client ID.
            identifier (str): User identifier.

        Returns:
            UserModel: The user model
        """
    @abstractmethod
    def create_user(self, user: UserModel) -> UserModel:
        """Creates a new user.

        Args:
            user (UserModel): User model.

        Returns:
            UserModel: Created user.
        """
