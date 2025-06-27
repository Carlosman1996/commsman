from contextlib import contextmanager

from sqlalchemy import create_engine, event, func, desc, over
from sqlalchemy.orm import sessionmaker, declarative_base, aliased

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

    def update_item_from_handler(self, item_id: int, item_handler: str, **kwargs):
        with self.session_scope() as session:
            item = self._get_item_from_handler(item_handler=item_handler, item_id=item_id)
            for key, value in kwargs.items():
                setattr(item, key, value)
            session.add(item)
            return item

    def add_item_from_dataclass(self, item: BaseItem):
        """Crea un nuevo ítem y lo guarda en la base de datos."""
        with self.session_scope() as session:
            session.add(item)
            return item

    def create_item_request_from_handler(self, item_name: str, item_handler: str, parent_item_id: int = None):
        """Crea un nuevo ítem y lo guarda en la base de datos."""
        with self.session_scope() as session:
            base_request_item = DATACLASS_REGISTRY["Request"](name=item_name, request_type_handler=item_handler)
            session.add(base_request_item)
            session.flush()

            item = DATACLASS_REGISTRY.get(item_handler)(item_id=base_request_item.item_id, name=item_name, parent_id=parent_item_id)
            session.add(item)
            return item

    def create_client_item(self, item_name: str, item_handler: str, parent_item_id: int):
        """Crea un nuevo ítem y lo guarda en la base de datos."""
        with self.session_scope() as session:
            item = DATACLASS_REGISTRY.get(item_handler)(name=item_name)
            base_client_item = DATACLASS_REGISTRY["Client"](name=item_name, client_type_handler=item.item_handler)

            parent_item = self._get_item(parent_item_id)

            session.add(base_client_item)
            session.flush()
            item.client_id = base_client_item.item_id
            session.add(item)
            parent_item.client_id = base_client_item.item_id
            session.add(parent_item)
            return item

    def create_run_options_item(self, item_name: str, item_handler: str, parent_item_id: int):
        """Crea un nuevo ítem y lo guarda en la base de datos."""
        with self.session_scope() as session:
            item = DATACLASS_REGISTRY.get(item_handler)(name=item_name)
            session.add(item)
            session.flush()

            parent_item = self._get_item(parent_item_id)

            parent_item.run_options_id = item.item_id
            session.add(parent_item)
        return item

    def _get_item(self, item_id: int):
        with self.session_scope() as session:
            base_item = (
                session.query(Request)
                    .filter(Request.item_id == item_id)
                    .first()
            )
            item = self._get_item_from_handler(item_handler=base_item.request_type_handler, item_id=base_item.item_id)
            return item

    def _get_item_from_handler(self, item_handler: str, item_id: int):
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

            item = self._get_item_from_handler(item_handler=base_request.request_type_handler, item_id=item_id)
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

    def get_item_last_result_tree(self, item_id: int) -> BaseResult | None:
        def get_result_with_children(item_handler, item_id):
            result_item = self._get_item_result(item_handler=item_handler, item_id=item_id)
            for index, child_data in enumerate(result_item.children):
                result_item.children[index] = get_result_with_children(**child_data)
            # Sort items at each level based on 'position':
            result_item.children.sort(key=lambda x: x.timestamp)
            return result_item

        execution_session = None
        with self.session_scope() as session:

            item = self._get_item(item_id)
            response_class_handler = self.get_class_handler(item.item_response_handler)

            # Step 1: Get max execution_session_id for this item
            last_execution_session_id = (
                session.query(func.max(response_class_handler.execution_session_id))
                .filter(response_class_handler.request_id == item.item_id)
                .first()
            )
            if not last_execution_session_id:
                return None

            # Step 2: Get all results linked to last execution id
            results = (
                session.query(response_class_handler)
                .filter(response_class_handler.request_id == item.item_id)
                .filter(response_class_handler.execution_session_id == last_execution_session_id[0])
                .order_by(response_class_handler.timestamp.desc())
                .all()
            )

            if results:
                last_result = results[0]

                # Get item last execution session:
                execution_session = (
                    session.query(ExecutionSession)
                    .filter(ExecutionSession.item_id == last_result.execution_session_id)
                    .order_by(ExecutionSession.timestamp.desc())
                    .first()
                )

                if execution_session:

                    # Resolve the number of total results ok and ko:
                    execution_session.iterations = len(results)
                    for result in results:
                        if result.item_handler == "CollectionResult":
                            execution_session.total_ok += result.total_ok
                            execution_session.total_failed += result.total_failed
                        else:
                            if result.result == "OK":
                                execution_session.total_ok += 1
                            elif result.result == "Failed":
                                execution_session.total_failed += 1

                    # Resolve the possible nested results in collections:
                    last_result = get_result_with_children(item_handler=last_result.item_handler,
                                                           item_id=last_result.item_id)
                    execution_session.results = last_result

            return execution_session

    def get_item_results_history(self, item_id: int) -> BaseResult:
        with self.session_scope() as session:

            item = self._get_item(item_id)
            response_class_handler = self.get_class_handler(item.item_response_handler)

            # Step 1: Get all distinct execution_session_ids for this item
            execution_sessions = (
                session.query(response_class_handler.execution_session_id)
                .filter(response_class_handler.request_id == item.item_id)
                .distinct()
                .all()
            )

            # Flatten the list of tuples to a list of IDs
            execution_session_ids = [row[0] for row in execution_sessions]

            # Step 2: Get the last 10 ExecutionSession entries for those session IDs
            results_history = (
                session.query(ExecutionSession)
                .filter(ExecutionSession.item_id.in_(execution_session_ids))
                .order_by(ExecutionSession.timestamp.desc())
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
            if item:
                items = [item]
            else:
                items = (
                    session.query(Collection)
                    .filter(Collection.parent_id == None)
                    .all()
                )

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
            item_last_result = self.get_item_last_result_tree(item_id)
            request.last_result = item_last_result
            item_results_history = self.get_item_results_history(item_id)
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
            result = self._get_item_from_handler(item_handler=item_handler, item_id=item_id)

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

    item = repository_obj.get_item_request(10)
    print(item)
