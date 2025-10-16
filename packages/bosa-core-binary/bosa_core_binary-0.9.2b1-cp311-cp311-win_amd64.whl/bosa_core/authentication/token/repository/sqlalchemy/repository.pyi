from _typeshed import Incomplete
from bosa_core.authentication.database import SQLAlchemySQLDataStore as SQLAlchemySQLDataStore
from bosa_core.authentication.token.repository.base_repository import BaseRepository as BaseRepository
from bosa_core.authentication.token.repository.models import Token as Token
from bosa_core.authentication.token.repository.sqlalchemy.models import DBToken as DBToken
from uuid import UUID

class SqlAlchemyTokenRepository(BaseRepository):
    """SQLAlchemy token repository."""
    db: Incomplete
    def __init__(self, data_store: SQLAlchemySQLDataStore) -> None:
        """Initialize the repository.

        Args:
            data_store (SQLAlchemySQLDataStore): Data store.
        """
    def get_token(self, client_id: UUID, user_id: UUID, token_id: UUID) -> Token | None:
        """Get token.

        Args:
            client_id (UUID): Client ID.
            user_id (UUID): User ID.
            token_id (UUID): Token ID.

        Returns:
            Token: The token
        """
    def create_token(self, token: Token) -> None:
        """Create token.

        Args:
            token (Token): The token
        """
    def revoke_token(self, client_id: UUID, user_id: UUID, token_id: UUID) -> bool:
        """Revoke a token.

        Args:
            client_id (UUID): Client ID.
            user_id (UUID): User ID.
            token_id (UUID): Token ID.

        Returns:
            bool: True if token was found and revoked, False otherwise
        """
