import sqlalchemy as sa
from sqlalchemy import exc
from abc import ABC, abstractmethod

class DdlOperations(ABC):
    """Abstract base class for DDL operations."""
    def __init__(self, engine: sa.engine.Engine, logger):
        self.engine = engine
        self.logger = logger

    def quote(self, name: str) -> str:
        """Quote database object names."""
        return self.engine.dialect.identifier_preparer.quote(name)

    def execute(self, query):
        """Execute a raw SQL query."""
        try:
            with self.engine.begin() as conn:
                conn.execute(sa.text(query))
                self.logger.debug(f"Executed query: {query}")
        except exc.SQLAlchemyError as e:
            self.logger.debug(f"Error executing query: {query} : {e}")
            raise

    def create_table(self, table: sa.Table) -> None:
        """Create a table."""
        if self.engine.dialect.has_table(self.engine.connect(), table.name, schema=table.schema):
            table.metadata.reflect(bind=self.engine, extend_existing=True, schema=table.schema, only=[table.name])
            self.logger.info(f"Table {table.schema}.{table.name} already exists.")
            return
        sql_statement = str(sa.schema.CreateTable(table).compile(self.engine))
        try:
            self.execute(sql_statement)
            table.metadata.reflect(bind=self.engine, extend_existing=True, schema=table.schema, only=[table.name])
            self.logger.info(f"Created table {table.schema}.{table.name}.")
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error creating table {table.schema}.{table.name}: {e}.")
            raise

    def drop_table(self, table: sa.Table) -> None:
        """Drop a table."""
        if not self.engine.dialect.has_table(self.engine.connect(), table.name, schema=table.schema):
            self.logger.info(f"Table {table.schema}.{table.name} does not exist.")
            return
        sql_statement = str(sa.schema.DropTable(table).compile(self.engine))
        try:
            self.execute(sql_statement)
            self.logger.info(f"Dropped table {table.schema}.{table.name}.")
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error dropping table {table.schema}.{table.name}: {e}.")
            raise

    def truncate_table(self, table: sa.Table) -> None:
        """Truncate a table."""
        if not self.engine.dialect.has_table(self.engine.connect(), table.name, schema=table.schema):
            self.logger.info(f"Table {table.schema}.{table.name} does not exist.")
            return
        sql_statement = f"TRUNCATE TABLE {self.quote(table.schema)}.{self.quote(table.name)}"
        try:
            self.execute(sql_statement)
            self.logger.info(f"Truncated table {table.schema}.{table.name}.")
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error truncating table {table.schema}.{table.name}: {e}.")
            raise

    @abstractmethod
    def _add_column_sql(self, table: sa.Table, column: sa.Column) -> str:
        """Generate SQL for adding a column."""
        pass

    def add_column(self, table: sa.Table, column: sa.Column) -> None:
        """Add a column to a table."""
        if column.name in table.c:
            self.logger.info(f"Column {column.name} already exists in table {table.schema}.{table.name}.")
            return
        sql_statement = self._add_column_sql(table, column)
        try:
            self.execute(sql_statement)
            table.append_column(column)
            self.logger.info(f"Added column {column.name} to table {table.schema}.{table.name}.")
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error adding column {column.name} to table {table.schema}.{table.name}: {e}.")
            raise

    @abstractmethod
    def _create_view_sql(self, view: sa.Table, definition: sa.Selectable, or_replace=True) -> str:
        """Generate SQL for creating a view."""
        pass

    def create_view(self, view: sa.Table, definition: sa.Selectable, or_replace=True) -> None:
        """Create a view."""
        if self.engine.dialect.has_table(self.engine.connect(), view.name, schema=view.schema) and not or_replace:
            view.metadata.reflect(bind=self.engine, views=True, extend_existing=True, schema=view.schema,
                                  only=[view.name])
            self.logger.info(f"View {view.schema}.{view.name} already exists")
            return
        sql_statement = self._create_view_sql(view, definition, or_replace)
        try:
            self.execute(sql_statement)
            view.metadata.reflect(bind=self.engine, views=True, extend_existing=True, schema=view.schema,
                                  only=[view.name])
            self.logger.info(f"Created view {view.schema}.{view.name}.")
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error creating view {view.schema}.{view.name}: {e}.")
            raise

    def create_index(self, table, columns_name, index_name, unique=False):
        """Create an index on multiple table columns."""
        if index_name in [idx.name for idx in table.indexes]:
            self.logger.info(f"Index {index_name} already exists on table {table.schema}.{table.name}.")
            return
        for column_name in columns_name:
            if column_name not in table.c:
                raise ValueError(f"Column {column_name} does not exist in table {table.schema}.{table.name}.")
        index = sa.Index(index_name, *[table.c[column_name] for column_name in columns_name], unique=unique)
        try:
            index.create(self.engine)
            self.logger.info(
                f"Created index {index_name} on columns {', '.join(columns_name)} of table {table.schema}.{table.name}.")
        except exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error creating index {index_name} on columns {', '.join(columns_name)} of table {table.schema}.{table.name}: {e}.")
            raise

class MssqlDdlOperations(DdlOperations):
    """Concrete class for MSSQL DDL operations."""
    def _add_column_sql(self, table: sa.Table, column: sa.Column) -> str:
        column_definition = f"{self.quote(column.name)} {column.type.compile(self.engine.dialect)}"
        sql_statement = f"ALTER TABLE {self.quote(table.schema)}.{self.quote(table.name)} ADD {column_definition}"
        return sql_statement

    def _create_view_sql(self, view: sa.Table, definition: sa.Selectable, or_replace=True) -> str:
        if or_replace:
            sql_statement = f"CREATE OR ALTER VIEW {self.quote(view.schema)}.{self.quote(view.name)} AS {definition.compile(compile_kwargs={'literal_binds': True})}"
        else:
            sql_statement = f"CREATE VIEW {self.quote(view.schema)}.{self.quote(view.name)} AS {definition.compile(compile_kwargs={'literal_binds': True})}"
        return sql_statement

class PostgresqlDdlOperations(DdlOperations):
    """Concrete class for PostgreSQL DDL operations."""
    def _add_column_sql(self, table: sa.Table, column: sa.Column) -> str:
        column_definition = f"{self.quote(column.name)} {column.type.compile(self.engine.dialect)}"
        sql_statement = f"ALTER TABLE {self.quote(table.schema)}.{self.quote(table.name)} ADD COLUMN {column_definition}"
        return sql_statement

    def _create_view_sql(self, view: sa.Table, definition: sa.Selectable, or_replace=True) -> str:
        if or_replace:
            sql_statement = f"CREATE OR REPLACE VIEW {self.quote(view.schema)}.{self.quote(view.name)} AS {definition.compile(compile_kwargs={'literal_binds': True})}"
        else:
            sql_statement = f"CREATE VIEW {self.quote(view.schema)}.{self.quote(view.name)} AS {definition.compile(compile_kwargs={'literal_binds': True})}"
        return sql_statement

def createDdlOperations(engine, logger):
    """Factory function to create the appropriate DDL operations class."""
    dialect = engine.dialect.name
    if dialect == "mssql":
        return MssqlDdlOperations(engine, logger)
    elif dialect == "postgresql":
        return PostgresqlDdlOperations(engine, logger)
    else:
        raise NotImplementedError(f"DDL operations for database type '{dialect}' are not implemented.")