from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Iterator, Any
import sqlalchemy
from sqlalchemy import text
from sqlalchemy.engine import Engine
from google.cloud.alloydbconnector import Connector, IPTypes


class AbstractDatabase(ABC):
    """
    Abstract database class.
    """

    @abstractmethod
    def query(self, query: str):
        pass


class AlloyDB(AbstractDatabase):
    """
    AlloyDB database class.
    """

    def __init__(
        self,
        project: str,
        region: str,
        cluster: str,
        instance: str,
        database: str,
        user: str,
        password: str = "",
        ip_type: IPTypes = IPTypes.PUBLIC,
        driver: str = "pg8000",
    ):
        self.project = project
        self.region = region
        self.cluster = cluster
        self.instance = instance
        self.database = database
        self.user = user
        self.password = password
        self.ip_type = ip_type
        self.driver = driver

    def _instance_connection_name(self):
        return f"projects/{self.project}/locations/{self.region}/clusters/{self.cluster}/instances/{self.instance}"

    @contextmanager
    def _engine(
        self,
    ) -> Iterator[Engine]:
        """
        Get an engine to the instance.
        """

        if Connector is None:
            raise RuntimeError("google-cloud-alloydbconnector not installed")

        def getconn():
            """
            Get a connection to the instance.
            """
            # Create the connector
            connector = Connector(ip_type=self.ip_type)

            # Connect to the instance
            return connector.connect(
                self._instance_connection_name(),
                self.driver,
                user=self.user,
                password=self.password,
                db=self.database,
                ip_type=self.ip_type,
                enable_iam_auth=True,
            )

        # Create the engine
        engine = sqlalchemy.create_engine(
            f"postgresql+{self.driver}://", creator=getconn
        )

        try:
            # Yield the engine
            yield engine
        finally:
            # Dispose the engine
            engine.dispose()

    def query(
        self,
        query_str: str,
        fetch: bool = True,
        parameters: dict[str, Any] | list[dict[str, Any]] | None = None,
        **kwargs,
    ):
        """
        Query the database.
        """
        with self._engine(**kwargs) as engine:
            with engine.connect() as connection:
                with connection.begin() as transaction:
                    if parameters is not None:
                        result = connection.execute(text(query_str), parameters)
                    else:
                        result = connection.execute(text(query_str))
                    if fetch:
                        return [dict(row) for row in result]
                return None


# ============================================================
# Factory Unified Database
# ============================================================
class DB(AbstractDatabase):
    """
    Factory class that creates the correct backend based on the db_type.
    """

    def __init__(self, database_type: str, **config):
        """
        Initialize the factory.
        """
        if database_type == "alloydb":
            required = ["project", "region", "instance", "database", "user"]
            for r in required:
                if r not in config:
                    raise ValueError(f"Missing required config key: {r}")

            self._impl = AlloyDB(**config)
            self.__class__ = AlloyDB
            self.__dict__ = self._impl.__dict__
        else:
            raise NotImplementedError(f"Database {database_type} is not supported yet")

    def query(self, query: str):
        return self._impl.query(query)
