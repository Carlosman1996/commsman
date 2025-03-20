from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from backend.models import *
from backend.repository.base_repository import BaseRepository


DATABASE_URL = "sqlite:///commsman.db"
Base = declarative_base()


class SQLiteRepository(BaseRepository):
    def __init__(self, database_url: str = DATABASE_URL):
        super().__init__()

        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def load(self):
        pass

    def save(self):
        pass

    def delete_item(self, item_handler: str, item_id: int):
        with self.session_scope() as session:
            item = self.get_item(item_handler, item_id, session)
            session.delete(item)
            session.add(item)

    def update_item_from_handler(self, item_handler: str, item_id: int, **kwargs):
        with self.session_scope() as session:
            item = self.get_item(item_handler, item_id, session)
            for key, value in kwargs.items():
                setattr(item, key, value)
            session.add(item)

    def update_item_from_dataclass(self, item: BaseItem, **kwargs):
        with self.session_scope() as session:
            for key, value in kwargs.items():
                setattr(item, key, value)
            session.add(item)

    def add_item_from_dataclass(self, item: BaseItem):
        """Crea un nuevo ítem y lo guarda en la base de datos."""
        with self.session_scope() as session:
            session.add(item)

    def create_item_from_handler(self, item_name: str, item_handler: str, parent_id: int = None):
        """Crea un nuevo ítem y lo guarda en la base de datos."""
        with self.session_scope() as session:
            item = DATACLASS_REGISTRY.get(item_handler)(name=item_name, parent_id=parent_id)
            session.add(item)
            return item

    def create_client_item(self, item_name: str, item_handler: str, parent: BaseItem):
        """Crea un nuevo ítem y lo guarda en la base de datos."""
        with self.session_scope() as session:
            item = DATACLASS_REGISTRY.get(item_handler)(name=item_name)
            base_client_item = DATACLASS_REGISTRY["Client"](name=item_name, item_type=item.item_type, client_type_handler=item.item_handler)

            session.add(base_client_item)
            session.flush()
            item.client_id = base_client_item.item_id
            session.add(item)
            parent.client_id = base_client_item.item_id
            session.add(parent)
            return item

    def create_run_options_item(self, item_name: str, item_handler: str, parent: BaseItem):
        """Crea un nuevo ítem y lo guarda en la base de datos."""
        with self.session_scope() as session:
            item = DATACLASS_REGISTRY.get(item_handler)(name=item_name)
            session.add(item)
            session.flush()

            parent.run_options_id = item.item_id
            session.add(parent)
        return item

    def get_item(self, item_handler: str, item_id: int):
        with self.session_scope() as session:
            item_class_handler = self.get_class_handler(item_handler)

            item = (
                session.query(item_class_handler)
                    .filter(item_class_handler.item_id == item_id)
                    .first()
            )
            return item

    def get_item_client(self, item: BaseRequest) -> Client:
        with self.session_scope() as session:
            base_client = (
                session.query(Client)
                    .filter(Client.item_id == item.client_id)
                    .first()
                )

            if base_client:
                client_handler = self.get_class_handler(base_client.client_type_handler)
                client = (
                    session.query(client_handler)
                        .filter(client_handler.client_id == base_client.item_id)
                        .first()
                    )
                return client
            else:
                return None

    def get_item_run_options(self, item: BaseRequest) -> RunOptions:
        with self.session_scope() as session:
            run_options = (
                session.query(RunOptions)
                    .filter(RunOptions.item_id == item.run_options_id)
                    .first()
                )
            return run_options

    def get_item_last_result_tree(self, item: BaseRequest) -> BaseResult:
        def get_result_with_children(item_handler, item_id):
            result_item = self.get_item_result(item_handler=item_handler, item_id=item_id)
            for index, child_data in enumerate(result_item.children):
                result_item.children[index] = get_result_with_children(**child_data)
            return result_item

        with self.session_scope() as session:
            item_class_handler = self.get_class_handler(item.item_response_handler)
            last_result = (
                session.query(item_class_handler)
                    .filter(item_class_handler.request_id == item.item_id)
                    .order_by(item_class_handler.timestamp.desc())
                    .first()
                )

            if last_result:
                last_result = get_result_with_children(last_result.item_handler, last_result.item_id)
            return last_result

    def get_items_request_tree(self, item: BaseItem = None) -> list[Collection]:
        def get_item_with_children(item_handler, item_id):
            _item = self.get_item_request(item_handler=item_handler, item_id=item_id)
            # Replace item dict by dataclass:
            for _index, _child_data in enumerate(_item.children):
                _item.children[_index] = get_item_with_children(**_child_data)
            # Sort items at each level based on 'position':
            _item.children.sort(key=lambda x: x.position or 0)
            return _item

        with self.session_scope() as session:
            if item is None:
                items = (
                    session.query(Collection)
                    .filter(Collection.parent_id == None)
                    .all()
                )
            else:
                items = [item]

            if items:
                for index, item in enumerate(items):
                    items[index] = get_item_with_children(item.item_handler, item.item_id)
                # Sort items at each level based on 'position':
                items.sort(key=lambda x: x.position or 0)

            return items

    def get_item_request(self, item_handler: str, item_id: int):
        with self.session_scope() as session:
            request = self.get_item(item_handler, item_id)

            # Solve relationships:
            item_client = self.get_item_client(request)
            request.client = item_client
            item_run_options = self.get_item_run_options(request)
            request.run_options = item_run_options
            item_last_result = self.get_item_last_result_tree(request)
            request.last_result = item_last_result

            # Solve parent:
            parent = (
                session.query(Collection.item_handler, Collection.item_id)
                .filter(Collection.item_id == request.parent_id)
                .first()
            )
            if parent:
                request.parent = parent._asdict()

            # Solve children:
            if item_handler == "Collection":
                children = []
                children += (
                    session.query(Collection.item_handler, Collection.item_id)
                        .filter(Collection.parent_id == item_id)
                        .all()
                )
                children += (
                    session.query(ModbusRequest.item_handler, ModbusRequest.item_id)
                        .filter(ModbusRequest.parent_id == item_id)
                        .all()
                )

                children = [child._asdict() for child in children]
            else:
                children = []

            request.children = children

            return request

    def get_item_result(self, item_handler: str, item_id: int):
        with self.session_scope() as session:
            result = self.get_item(item_handler, item_id)

            # Solve parent:
            parent = (
                session.query(CollectionResult.item_handler, CollectionResult.item_id)
                .filter(CollectionResult.item_id == result.parent_id)
                .first()
            )
            if parent:
                result.parent = parent._asdict()

            # Solve children:
            if item_handler == "CollectionResult":
                children = []
                children += (
                    session.query(CollectionResult.item_handler, CollectionResult.item_id)
                        .filter(CollectionResult.parent_id == item_id)
                        .all()
                )
                children += (
                    session.query(ModbusResponse.item_handler, ModbusResponse.item_id)
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

    result = repository_obj.get_items_request_tree()
    print(result)
