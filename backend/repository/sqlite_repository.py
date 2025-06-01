from contextlib import contextmanager

from sqlalchemy import create_engine, event, func, desc, over
from sqlalchemy.orm import sessionmaker, declarative_base, Session, aliased

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

    def delete_item(self, item_id: int):
        with self.session_scope() as session:
            request = (
                session.query(Request)
                    .filter(Request.item_id == item_id)
                    .first()
            )

            item = self._get_item_request(item_id=request.item_id)

            session.delete(request)

            if item.client_id:
                client = (
                    session.query(Client)
                        .filter(Client.item_id == item.client_id)
                        .first()
                )
                session.delete(client)
            if item.run_options_id:
                run_options = (
                    session.query(RunOptions)
                        .filter(RunOptions.item_id == item.run_options_id)
                        .first()
                )
                session.delete(run_options)

    def delete_old_results(self, maintain_last_results: int = 10000):
        with self.session_scope() as session:
            def delete_by_table(table_handler):
                # Define a window function to partition by `request_id` and order by `timestamp` desc
                window = over(
                    func.row_number(),
                    partition_by=table_handler.request_id,
                    order_by=desc(table_handler.timestamp)
                ).label("row_number")

                # Create a subquery to assign row numbers to each row within its `request_id` partition
                subquery = (
                    session.query(
                        table_handler,
                        window
                    )
                    .subquery()
                )

                # Map the subquery back to the Result model
                table_handler_with_row_number = aliased(table_handler, subquery)

                # Filter the subquery to get only the top 10,000 rows per `request_id`
                query = (
                    session.query(
                        table_handler_with_row_number.item_id
                    )
                    .filter(subquery.c.row_number <= maintain_last_results)
                    .filter(table_handler_with_row_number.parent_id == None)
                    .order_by(table_handler_with_row_number.request_id, desc(table_handler_with_row_number.timestamp))
                )

                # Execute the query and fetch results
                results = query.all()
                keep_ids = list(map(lambda item_id: item_id[0], results))

                # Delete old results:
                if keep_ids:
                    # Delete all rows from the `results` table where `item_id` is not in the `items_to_keep` list
                    delete_query = (
                        session.query(table_handler)
                        .filter(table_handler.item_id <= min(keep_ids))
                    )

                    # Execute the delete query
                    delete_query.delete(synchronize_session=False)

            delete_by_table(CollectionResult)
            delete_by_table(ModbusResponse)

    def update_item_from_handler(self, item_handler: str, item_id: int, **kwargs):
        with self.session_scope() as session:
            item = self._get_item(item_handler=item_handler, item_id=item_id)
            for key, value in kwargs.items():
                setattr(item, key, value)
            session.add(item)
            return item

    def add_item_from_dataclass(self, item: BaseItem):
        """Crea un nuevo ítem y lo guarda en la base de datos."""
        with self.session_scope() as session:
            session.add(item)
            return item

    def create_item_request_from_handler(self, item_name: str, item_handler: str, parent_id: int = None):
        """Crea un nuevo ítem y lo guarda en la base de datos."""
        with self.session_scope() as session:
            base_request_item = DATACLASS_REGISTRY["Request"](name=item_name, request_type_handler=item_handler)
            session.add(base_request_item)
            session.flush()

            item = DATACLASS_REGISTRY.get(item_handler)(item_id=base_request_item.item_id, name=item_name, parent_id=parent_id)
            session.add(item)
            return item

    def create_client_item(self, item_name: str, item_handler: str, parent: BaseItem):
        """Crea un nuevo ítem y lo guarda en la base de datos."""
        with self.session_scope() as session:
            item = DATACLASS_REGISTRY.get(item_handler)(name=item_name)
            base_client_item = DATACLASS_REGISTRY["Client"](name=item_name, client_type_handler=item.item_handler)

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

    def _get_item(self, item_handler: str, item_id: int):
        with self.session_scope() as session:
            item_class_handler = self.get_class_handler(item_handler)

            item = (
                session.query(item_class_handler)
                    .filter(item_class_handler.item_id == item_id)
                    .first()
            )
            return item

    def _get_item_request(self, item_id: int):
        with self.session_scope() as session:
            base_request = (
                session.query(Request)
                    .filter(Request.item_id == item_id)
                    .first()
            )

            item = self._get_item(item_handler=base_request.request_type_handler, item_id=item_id)
            return item

    def _get_item_client(self, item: BaseRequest) -> Client:
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

    def _get_item_run_options(self, item: BaseRequest) -> RunOptions:
        with self.session_scope() as session:
            run_options = (
                session.query(RunOptions)
                    .filter(RunOptions.item_id == item.run_options_id)
                    .first()
                )
            return run_options

    # TODO: old
    # def get_item_last_result_tree(self, item: BaseRequest) -> BaseResult | None:
    #     def get_result_with_children(item_handler, item_id):
    #         result_item = self._get_item_result(item_handler=item_handler, item_id=item_id)
    #         for index, child_data in enumerate(result_item.children):
    #             result_item.children[index] = get_result_with_children(**child_data)
    #         # Sort items at each level based on 'position':
    #         result_item.children.sort(key=lambda x: x.timestamp)
    #         return result_item
    #
    #     last_execution_result = None
    #
    #     with self.session_scope() as session:
    #         item_class_handler = self.get_class_handler(item.item_response_handler)
    #
    #         # Get the maximum execution_id
    #         max_execution_id = session.query(func.max(item_class_handler.execution_session_id)).scalar()
    #
    #         # Get all rows with that execution_id
    #         results = (
    #             session.query(item_class_handler)
    #             .filter(item_class_handler.request_id == item.item_id)
    #             .filter(item_class_handler.execution_session_id == max_execution_id)
    #             .all()
    #         )
    #
    #         if results:
    #             last_execution_result = (
    #                 session.query(ExecutionSession)
    #                 .filter(ExecutionSession.item_id == max_execution_id)
    #                 .first()
    #             )
    #
    #             for result in results:
    #                 get_result_with_children(item_handler=result.item_handler,
    #                                          item_id=result.item_id)
    #
    #             last_execution_result.children = results
    #
    #         return last_execution_result

    def get_item_last_result_tree(self, item: BaseRequest) -> BaseResult:
        def get_result_with_children(item_handler, item_id):
            result_item = self._get_item_result(item_handler=item_handler, item_id=item_id)
            for index, child_data in enumerate(result_item.children):
                result_item.children[index] = get_result_with_children(**child_data)
            # Sort items at each level based on 'position':
            result_item.children.sort(key=lambda x: x.timestamp)
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
                last_result = get_result_with_children(item_handler=last_result.item_handler,
                                                       item_id=last_result.item_id)
            return last_result

    def get_item_results_history(self, item: BaseRequest) -> BaseResult:
        with self.session_scope() as session:
            item_class_handler = self.get_class_handler(item.item_response_handler)
            results_history = (
                session.query(item_class_handler)
                    .filter(item_class_handler.request_id == item.item_id)
                    .order_by(item_class_handler.timestamp.desc())
                    .limit(10)
                    .all()
                )

            if results_history is None:
                results_history = []

            return results_history

    def get_items_request_tree(self, item: BaseItem = None) -> list[Collection]:
        def get_item_with_children(item_id):
            _item = self.get_item_request(item_id=item_id)
            # Replace item dict by dataclass:
            for _index, _child_id in enumerate(_item.children):
                _item.children[_index] = get_item_with_children(_child_id)
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
                    items[index] = get_item_with_children(item.item_id)
                # Sort items at each level based on 'position':
                items.sort(key=lambda x: x.position or 0)

            return items

    def get_item_request(self, item_id: int):
        with self.session_scope() as session:
            request = self._get_item_request(item_id)

            # Solve relationships:
            item_client = self._get_item_client(request)
            request.client = item_client
            item_run_options = self._get_item_run_options(request)
            request.run_options = item_run_options
            item_last_result = self.get_item_last_result_tree(request)
            request.last_result = item_last_result
            item_results_history = self.get_item_results_history(request)
            request.results_history = item_results_history

            # Solve children:
            if request.item_handler == "Collection":
                children = []
                children += (
                    session.query(Collection.item_id)
                        .filter(Collection.parent_id == item_id)
                        .all()
                )
                children += (
                    session.query(ModbusRequest.item_id)
                        .filter(ModbusRequest.parent_id == item_id)
                        .all()
                )

                children = [child.item_id for child in children]
            else:
                children = []

            request.children = children

            return request

    def _get_item_result(self, item_handler: str, item_id: int):
        with self.session_scope() as session:
            result = self._get_item(item_handler=item_handler, item_id=item_id)

            # Solve children:
            if result.item_handler == "CollectionResult":
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

    result = repository_obj.delete_old_results(10)
