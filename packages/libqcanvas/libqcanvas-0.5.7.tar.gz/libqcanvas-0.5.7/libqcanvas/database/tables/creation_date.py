from datetime import datetime

from sqlalchemy.orm import Mapped


class CreationDate:
    creation_date: Mapped[datetime]
