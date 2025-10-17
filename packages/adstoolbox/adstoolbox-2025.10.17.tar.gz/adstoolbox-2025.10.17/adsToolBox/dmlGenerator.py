import sqlalchemy as sa
from abc import ABC, abstractmethod

class DmlGenerator(ABC):
    """Abstract base class for DML Generator."""
    def __init__(self, engine: sa.engine.Engine):
        self.engine = engine

    def quote(self, name: str) -> str:
        """Quote database object names."""
        return self.engine.dialect.identifier_preparer.quote(name)

    @abstractmethod
    def to_json(self, columns) -> str:
        """Generate SQL for columns to json conversion."""
        pass

    @abstractmethod
    def to_sha2_256(self, string: str) -> str:
        """Generate SQL for SHA2-256 hash."""
        pass

    @abstractmethod
    def to_md5(self, string: str) -> str:
        """Generate SQL for MD5 hash."""
        pass

class MssqlDmlGenerator(DmlGenerator):
    """Concrete class for MSSQL DML Generator."""
    def to_json(self, columns) -> str:
        columns_expression = ", ".join([f"{str(col.expression)} AS {self.quote(col.name)}" for col in columns])
        sql_statement = f"(SELECT {columns_expression} FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)"
        return sql_statement

    def to_sha2_256(self, string: str) -> str:
        sql_statement = f"CONVERT(varchar(64), HASHBYTES('SHA2_256', {string}), 2)"
        return sql_statement

    def to_md5(self, string: str) -> str:
        sql_statement = f"CONVERT(varchar(32), HASHBYTES('MD5', {string}), 2)"
        return sql_statement

class PostgresqlDmlGenerator(DmlGenerator):
    """Concrete class for PostgreSQL DML Generator."""
    def to_json(self, columns) -> str:
        columns_expression = ", ".join([f"{self.quote(col.name)}, {str(col.expression)}" for col in columns])
        sql_statement = f"json_build_object({columns_expression})::text"
        return sql_statement

    def to_sha2_256(self, string: str) -> str:
        sql_statement = f"encode(digest({string}, 'sha256'), 'hex')"
        return sql_statement

    def to_md5(self, string: str) -> str:
        sql_statement = f"md5({string})"
        return sql_statement

def createDmlGenerator(engine):
    """Factory function to create the appropriate DML Generator class."""
    dialect = engine.dialect.name
    if dialect == "mssql":
        return MssqlDmlGenerator(engine)
    elif dialect == "postgresql":
        return PostgresqlDmlGenerator(engine)
    else:
        raise NotImplementedError(f"DML Generator for database type '{dialect}' are not implemented.")