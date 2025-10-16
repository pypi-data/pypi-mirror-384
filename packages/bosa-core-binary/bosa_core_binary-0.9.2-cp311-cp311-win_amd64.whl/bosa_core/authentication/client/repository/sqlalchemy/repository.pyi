from _typeshed import Incomplete
from bosa_core.authentication.client.repository.base_repository import BaseRepository as BaseRepository
from bosa_core.authentication.client.repository.models import ClientBasic as ClientBasic, ClientModel as ClientModel
from bosa_core.authentication.client.repository.sqlalchemy.models import DBClient as DBClient
from bosa_core.authentication.database import SQLAlchemySQLDataStore as SQLAlchemySQLDataStore
from uuid import UUID

class SqlAlchemyClientRepository(BaseRepository):
    """SQLAlchemy client repository."""
    db: Incomplete
    def __init__(self, data_store: SQLAlchemySQLDataStore) -> None:
        """Initialize the repository.

        Args:
            data_store (SQLAlchemySQLDataStore): Data store.
        """
    def create_client(self, client: ClientBasic) -> ClientModel:
        """Create a client.

        Args:
            client (ClientBasic): The client to create.

        Returns:
            ClientModel: The created client.

        Raises:
            ValidationError: If the data model has changed.
        """
    def get_client_by_id(self, client_id: UUID) -> ClientModel | None:
        """Get a client by ID.

        Args:
            client_id (UUID): The client ID

        Returns:
            ClientModel | None: The client

        Raises:
            ValidationError: If the data model has changed.
        """
    def get_client_list(self) -> list[ClientModel]:
        """Get a list of all clients.

        Returns:
            list[ClientModel]: A list of all clients.

        Raises:
            ValidationError: If the data model has changed.
        """
    def update_client(self, client: ClientModel) -> ClientModel | None:
        """Update a client.

        Args:
            client (ClientModel): The client to update.

        Returns:
            ClientModel: The updated client.

        Raises:
            ValidationError: If the data model has changed.
        """
