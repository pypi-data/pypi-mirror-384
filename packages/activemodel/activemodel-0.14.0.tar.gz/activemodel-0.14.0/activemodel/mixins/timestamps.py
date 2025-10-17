from datetime import datetime

import sqlalchemy as sa
from sqlmodel import Field

# TODO raw sql https://github.com/tiangolo/sqlmodel/discussions/772
# @classmethod
# def select(cls):
#     with get_session() as session:
#         results = session.exec(sql.select(cls))

#         for result in results:
#             yield result


class TimestampsMixin:
    """
    Simple created at and updated at timestamps. Mix them into your model:

    >>> class MyModel(TimestampsMixin, SQLModel):
    >>>    pass

    Notes:
    
    - Originally pulled from: https://github.com/tiangolo/sqlmodel/issues/252
    - Related issue: https://github.com/fastapi/sqlmodel/issues/539
    """

    created_at: datetime | None = Field(
        default=None,
        sa_type=sa.DateTime(timezone=True),
        sa_column_kwargs={"server_default": sa.func.now()},
        nullable=False,
    )

    updated_at: datetime | None = Field(
        default=None,
        sa_type=sa.DateTime(timezone=True),
        sa_column_kwargs={"onupdate": sa.func.now(), "server_default": sa.func.now()},
    )
