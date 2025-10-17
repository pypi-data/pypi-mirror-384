from datetime import datetime

from sqlalchemy import Text, TypeDecorator


class TZDateTime(TypeDecorator):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value: datetime, dialect):
        if value is not None:
            if not value.tzinfo or value.tzinfo.utcoffset(value) is None:
                raise TypeError("tzinfo is required")
            value = value.isoformat()
        return value

    def process_result_value(self, value: str, dialect):
        if value is not None:
            value = datetime.fromisoformat(value)
        return value
