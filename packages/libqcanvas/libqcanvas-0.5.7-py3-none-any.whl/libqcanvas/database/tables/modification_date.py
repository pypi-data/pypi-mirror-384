from datetime import datetime

from sqlalchemy.orm import Mapped


class ModificationDate:
    last_modification_date: Mapped[datetime]
