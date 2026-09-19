import json
from typing import List, Optional
from sqlalchemy.types import TypeDecorator, Text
try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False


class VectorType(TypeDecorator):
    """
    Custom SQLAlchemy TypeDecorator that uses pgvector.sqlalchemy.Vector when
    connected to PostgreSQL, and serializes as JSON text on SQLite/other dialects.
    """
    impl = Text
    cache_ok = True

    def __init__(self, dimensions: int = 768, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dimensions = dimensions

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and HAS_PGVECTOR:
            return dialect.type_descriptor(Vector(self.dimensions))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Optional[List[float]], dialect):
        if value is None:
            return None
        if dialect.name == "postgresql" and HAS_PGVECTOR:
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect) -> Optional[List[float]]:
        if value is None:
            return None
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return [float(x) for x in value.strip("[]").split(",") if x.strip()]
        return list(value)
