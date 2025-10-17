"""Connection subclass for Datastar sandbox connections."""

from typing import Dict, Any, Optional
import time
import pandas as pd
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.exc import DBAPIError

from ..project import Project
from ..connection import Connection
from ..frog_platform import OptilogicClient

MAX_ATTEMPTS = 10

SANDBOX_SCHEMA = "starburst"


class SandboxConnection(Connection):
    """Represents a Datastar sandbox connection."""

    def __init__(self, project: Project):

        self.project = project
        self.engine: Optional[Engine] = None

        # Note: base will persist, which calls back into subclass, so call init here at end
        super().__init__(name="Sandbox", description="Sandbox", sandbox=True)

    # ------------------------------------------------------------------
    # Direct sandbox access

    def read_table(self, table_name: str) -> pd.DataFrame:
        """
        Retrieve a sandbox table into a pandas DataFrame.

        Args:
            table_name: Name of the table to read.

        Returns:
            A pandas DataFrame containing the table data.
        """

        return pd.read_sql_table(
            table_name, con=self._get_engine(), schema=SANDBOX_SCHEMA
        )

    def write_table(self, df: pd.DataFrame, table_name: str) -> None:
        """
        Write a DataFrame to a SQL table.
        """
        df.to_sql(
            table_name,
            con=self._get_engine(),
            if_exists="append",
            index=False,
            schema=SANDBOX_SCHEMA,
        )

    def _get_engine(self) -> Engine:
        """
        Create and verify a SQLAlchemy engine with retry logic.

        Returns:
            A connected SQLAlchemy Engine.
        Raises:
            OperationalError: If the connection cannot be established after retries.
        """

        if self.engine:
            return self.engine

        connection_string = self._get_connection_string()
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                engine = create_engine(connection_string)

                # Test the connection explicitly
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))

                self.engine = engine
                return engine

            except DBAPIError:
                if attempt == MAX_ATTEMPTS:
                    raise
                print(
                    f"Connection failed. Project may not be ready. Retry attempt {attempt}/{MAX_ATTEMPTS})"
                )
                time.sleep(attempt)  # linear backoff

        # unreachable
        assert False

    def _get_connection_string(self) -> str:

        oc = OptilogicClient(appkey=Project.api().app_key)

        [success, connection_string] = oc.get_connection_string(self.project.name)

        assert success

        return connection_string

    # ------------------------------------------------------------------
    # Abstract method implementation

    def get_connection_type(self) -> str:
        return "sandbox"

    def _from_configuration(self, payload: Dict[str, Any]) -> None:
        pass

    def _to_configuration(self) -> Dict[str, Any]:
        return {}
