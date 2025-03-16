from sqlalchemy import create_engine, Column, String, ForeignKey, JSON
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

from backend.models import *
from backend.repository.base_repository import BaseRepository


DATABASE_URL = "sqlite:///commsman.db"
Base = declarative_base()


class SQLiteRepository(BaseRepository):
    def __init__(self, database_url: str = DATABASE_URL):
        super().__init__()

        self.engine = create_engine(database_url, echo=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def load(self):
        pass

    def save(self):
        """Guarda los cambios en la base de datos."""
        self.session.commit()

    def create_item_from_handler(self, item_name: str, item_handler: str, parent: BaseItem = None):
        """Crea un nuevo ítem y lo guarda en la base de datos."""
        item = DATACLASS_REGISTRY.get(item_handler)(name=item_name, parent_id=getattr(parent, "id"))
        self.session.add(item)
        self.save()
        return item

    def create_item_from_dataclass(self, item: BaseItem):
        """Crea un nuevo ítem y lo guarda en la base de datos."""
        self.session.add(item)
        self.save()
        return item

    def create_client_item(self, item_name: str, item_handler: str, parent: BaseItem):
        """Crea un nuevo ítem y lo guarda en la base de datos."""
        item = DATACLASS_REGISTRY.get(item_handler)(name=item_name)
        base_client_item = DATACLASS_REGISTRY["Client"](name=item_name, client_type=item.client_type)

        self.session.add(base_client_item)
        item.client_id = base_client_item.id
        self.session.add(item)
        parent.client_id = base_client_item.id
        self.session.add(item)

        self.save()
        return item

    def create_run_options_item(self, item_name: str, item_handler: str, parent: BaseItem):
        """Crea un nuevo ítem y lo guarda en la base de datos."""
        item = DATACLASS_REGISTRY.get(item_handler)(name=item_name)
        self.session.add(item)
        parent.run_options_id = item.id
        self.session.add(item)

        self.save()
        return item

    def update_item(self, item: BaseItem, **kwargs):
        """Actualiza un ítem en la base de datos."""
        item = self.session.query(item).filter_by(id=item.id).first()

        for key, value in kwargs.items():
            setattr(item, key, value)

        self.session.add(item)
        self.save()
        return item

    def delete_item(self, item: BaseItem):
        """Elimina un ítem y sus referencias de la base de datos."""
        self.session.delete(item)
        self.save()

    def get_item(self):
        pass

    def get_item_client(self, item: BaseRequest) -> BaseItem:
        base_client = (
            self.session.query(Client)
                .filter(Client.id == item.client_id)
                .first()
            )

        client_handler = self.get_class_handler(base_client.client_type_handler)
        client = (
            self.session.query(client_handler)
                .filter(client_handler.id == base_client.id)
                .first()
            )
        return client

    def get_request(self):
        item = self.session.query(ModbusRequest).first()
        item_handler = self.get_class_handler(item.item_handler)

        item_client = self.get_item_client(item)
        item_client_handler = self.get_class_handler(item_client.item_handler)

        request = (
            self.session.query(item_handler, RunOptions, item_client_handler)
                .join(RunOptions, RunOptions.id == item_handler.run_options_id)
                .join(Client, Client.id == item_handler.client_id)
                .join(item_client_handler, Client.id == item_client_handler.client_id)
                .filter(item_handler.id == item.id)
            )
        return request.first()


if __name__ == "__main__":
    repository_obj = SQLiteRepository()
    result = repository_obj.get_request()
    print(result)
    print(len(result))
    print(result.port)
