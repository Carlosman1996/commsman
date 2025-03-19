from sqlalchemy import create_engine, Column, String, ForeignKey, JSON, distinct, union
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, contains_eager

from backend.models import *
from backend.repository.base_repository import BaseRepository


DATABASE_URL = "sqlite:///commsman.db"
Base = declarative_base()


class SQLiteRepository(BaseRepository):
    def __init__(self, database_url: str = DATABASE_URL):
        super().__init__()

        self.engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def load(self):
        pass

    def save(self):
        """Guarda los cambios en la base de datos."""
        self.session.commit()

    def create_item_from_handler(self, item_name: str, item_handler: str, parent_id: int = None):
        """Crea un nuevo ítem y lo guarda en la base de datos."""
        item = DATACLASS_REGISTRY.get(item_handler)(name=item_name, parent_id=parent_id)
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
        item.client_id = base_client_item.item_id
        self.session.add(item)
        parent.client_id = base_client_item.item_id
        self.session.add(item)

        self.save()
        return item

    def create_run_options_item(self, item_name: str, item_handler: str, parent: BaseItem):
        """Crea un nuevo ítem y lo guarda en la base de datos."""
        item = DATACLASS_REGISTRY.get(item_handler)(name=item_name)
        self.session.add(item)
        parent.run_options_id = item.item_id
        self.session.add(item)

        self.save()
        return item

    def delete_item(self, item_handler: str, item_id: int):
        item_class_handler = self.get_class_handler(item_handler)

        item = (
            self.session.query(item_class_handler)
                .filter(item_class_handler.item_id == item_id)
                .first()
        )
        self.session.delete(item)
        self.save()

    def get_item(self):
        pass

    def get_item_client(self, item: BaseRequest) -> Client:
        base_client = (
            self.session.query(Client)
                .filter(Client.item_id == item.client_id)
                .first()
            )

        if base_client:
            client_handler = self.get_class_handler(base_client.client_type_handler)
            client = (
                self.session.query(client_handler)
                    .filter(client_handler.item_id == base_client.item_id)
                    .first()
                )
            return client
        else:
            return None

    def get_item_run_options(self, item: BaseRequest) -> RunOptions:
        run_options = (
            self.session.query(RunOptions)
                .filter(RunOptions.item_id == item.run_options_id)
                .first()
            )
        return run_options

    def get_items_request(self):
        requests = []
        requests += (
            self.session.query(Collection)
                .all()
        )
        requests += (
            self.session.query(ModbusRequest)
                .all()
        )
        return requests

    def get_item_request(self, item_handler: str, item_id: int):
        item_class_handler = self.get_class_handler(item_handler)

        request = (
            self.session.query(item_class_handler)
                .filter(item_class_handler.item_id == item_id)
                .first()
        )

        # Solve relationships:
        item_client = self.get_item_client(request)
        request.client = item_client
        item_run_options = self.get_item_run_options(request)
        request.run_options = item_run_options

        # Solve parent:
        parent = (
            self.session.query(Collection.item_handler, Collection.item_id)
            .filter(Collection.item_id == request.parent_id)
            .first()
        )
        if parent:
            request.parent = parent._asdict()

        # Solve children:
        if item_handler == "Collection":
            children = []
            children += (
                self.session.query(Collection.item_handler, Collection.item_id)
                    .filter(Collection.parent_id == item_id)
                    .all()
            )
            children += (
                self.session.query(ModbusRequest.item_handler, ModbusRequest.item_id)
                    .filter(ModbusRequest.parent_id == item_id)
                    .all()
            )

            children = [child._asdict() for child in children]
        else:
            children = []

        request.children = children

        return request

    def get_item_result(self, item_handler: str, item_id: int):
        item_class_handler = self.get_class_handler(item_handler)

        result = (
            self.session.query(item_class_handler)
                .filter(item_class_handler.item_id == item_id)
                .first()
        )

        # Solve parent:
        parent = (
            self.session.query(CollectionResult.item_handler, CollectionResult.item_id)
            .filter(CollectionResult.item_id == result.parent_id)
            .first()
        )
        if parent:
            result.parent = parent._asdict()

        # Solve children:
        if item_handler == "CollectionResult":
            children = []
            children += (
                self.session.query(CollectionResult.item_handler, CollectionResult.item_id)
                    .filter(CollectionResult.parent_id == item_id)
                    .all()
            )
            children += (
                self.session.query(ModbusResponse.item_handler, ModbusResponse.item_id)
                    .filter(ModbusResponse.parent_id == item_id)
                    .all()
            )

            children = [child._asdict() for child in children]
        else:
            children = []

        result.children = children

        return result


if __name__ == "__main__":
    repository_obj = SQLiteRepository()

    result = repository_obj.get_item_result(item_id=1, item_handler="CollectionResult")

    print(result)
