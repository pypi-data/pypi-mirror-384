import abc
from abc import ABC, abstractmethod
from bosa_core.authentication.client.repository.models import ClientBasic as ClientBasic, ClientModel as ClientModel
from uuid import UUID

class BaseRepository(ABC, metaclass=abc.ABCMeta):
    """Base repository interface."""
    @abstractmethod
    def create_client(self, client: ClientBasic) -> ClientModel:
        """Create client."""
    @abstractmethod
    def get_client_by_id(self, client_id: UUID) -> ClientModel | None:
        """Get client by id."""
    @abstractmethod
    def get_client_list(self) -> list[ClientModel]:
        """Get list of clients."""
    @abstractmethod
    def update_client(self, client: ClientModel) -> ClientModel:
        """Update client."""
