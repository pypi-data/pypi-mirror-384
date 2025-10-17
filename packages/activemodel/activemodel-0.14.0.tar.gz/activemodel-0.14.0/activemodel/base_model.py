import json
import typing as t
import textcase
from uuid import UUID
from contextlib import nullcontext

import sqlalchemy as sa
import sqlmodel as sm
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.orm.attributes import flag_modified as sa_flag_modified
from sqlmodel import Column, Field, Session, SQLModel, inspect, select
from typeid import TypeID
from sqlalchemy.orm import declared_attr

from activemodel.mixins.pydantic_json import PydanticJSONMixin

# NOTE: this patches a core method in sqlmodel to support db comments
from . import get_column_from_field_patch  # noqa: F401
from .query_wrapper import QueryWrapper
from .session_manager import get_session

POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}
"""
By default, the foreign key naming convention in sqlalchemy do not create unique identifiers when there are multiple
foreign keys in a table. This naming convention is a workaround to fix this issue:

- https://github.com/zhanymkanov/fastapi-best-practices?tab=readme-ov-file#set-db-keys-naming-conventions
- https://github.com/fastapi/sqlmodel/discussions/1213
- Implementation lifted from: https://github.com/AlexanderZharyuk/billing-service/blob/3c8aaf19ab7546b97cc4db76f60335edec9fc79d/src/models.py#L24
"""

SQLModel.metadata.naming_convention = POSTGRES_INDEXES_NAMING_CONVENTION


class BaseModel(SQLModel):
    """
    Base model class to inherit from so we can hate python less.

    Some notes:

    - Inspired by https://github.com/woofz/sqlmodel-basecrud/blob/main/sqlmodel_basecrud/basecrud.py
    - lifecycle hooks are modeled after Rails.
    - class docstrings are converted to table-level comments
    - save(), delete(), select(), where(), and other easy methods you would expect in a real ORM
    - Fixes foreign key naming conventions
    - Sane table names

    Here's how hooks work:

        Create/Update: before_create, after_create, before_update, after_update, before_save, after_save, around_save
        Delete: before_delete, after_delete, around_delete

    around_* hooks must be context managers (method returning a CM or a CM attribute).
    Ordering (create): before_create -> before_save -> (enter around_save) -> persist -> after_create -> after_save -> (exit around_save)
    Ordering (update): before_update -> before_save -> (enter around_save) -> persist -> after_update -> after_save -> (exit around_save)
    Delete: before_delete -> (enter around_delete) -> delete -> after_delete -> (exit around_delete)

        # TODO document this in activemodel, this is an interesting edge case
    # https://claude.ai/share/f09e4f70-2ff7-4cd0-abff-44645134693a

    """

    __table_args__ = None

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        from sqlmodel._compat import set_config_value

        # Enables field-level docstrings on the pydantic `description` field, which we
        # copy into table/column comments by patching SQLModel internals elsewhere.
        set_config_value(model=cls, parameter="use_attribute_docstrings", value=True)

        cls._apply_class_doc()

    @classmethod
    def _apply_class_doc(cls):
        """
        Pull class-level docstring into a table comment.

        This will help AI SQL writers like: https://github.com/iloveitaly/sql-ai-prompt-generator
        """

        doc = cls.__doc__.strip() if cls.__doc__ else None

        if doc:
            table_args = getattr(cls, "__table_args__", None)

            if table_args is None:
                cls.__table_args__ = {"comment": doc}
            elif isinstance(table_args, dict):
                table_args.setdefault("comment", doc)
            elif isinstance(table_args, tuple):
                # If it's a tuple, we need to convert it to a list and add the comment
                table_args = list(table_args)
                table_args.append({"comment": doc})
                cls.__table_args__ = tuple(table_args)
            else:
                raise ValueError(
                    f"Unexpected __table_args__ type {type(table_args)}, expected dictionary."
                )

    # TODO no type check decorator here
    @declared_attr
    def __tablename__(cls) -> str:
        """
        Automatically generates the table name for the model by converting the model's class name from camel case to snake case.
        This is the recommended text case style for table names:

        https://wiki.postgresql.org/wiki/Don%27t_Do_This#Don.27t_use_upper_case_table_or_column_names

        By default, the model's class name is lower cased which makes it harder to read.

        Also, many text case conversion libraries struggle handling words like "LLMCache", this is why we are using
        a more precise library which processes such acronyms: [`textcase`](https://pypi.org/project/textcase/).

        https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
        """
        return textcase.snake(cls.__name__)

    @classmethod
    def foreign_key(cls, **kwargs):
        """
        Returns a `Field` object referencing the foreign key of the model.

        Helps quickly build a many-to-one or one-to-one relationship.

        >>> other_model_id: int = OtherModel.foreign_key()
        >>> other_model = Relationship()
        """

        field_options = {"nullable": False} | kwargs

        return Field(
            # TODO id field is hard coded, should pick the PK field in case it's different
            sa_type=cls.model_fields["id"].sa_column.type,  # type: ignore
            foreign_key=f"{cls.__tablename__}.id",
            **field_options,
        )

    @classmethod
    def select(cls, *args):
        "create a query wrapper to easily run sqlmodel queries on this model"
        return QueryWrapper[cls](cls, *args)

    @classmethod
    def where(cls, *args):
        "convenience method to avoid having to write .select().where() in order to add conditions"
        return cls.select().where(*args)

    # TODO we should add an instance method for this as well
    @classmethod
    def upsert(
        cls,
        data: dict[str, t.Any],
        unique_by: str | list[str],
    ) -> t.Self:
        """
        This method will insert a new record if it doesn't exist, or update the existing record if it does.

        It uses SQLAlchemy's `on_conflict_do_update` and does not yet support MySQL. Some implementation details below.

        ---

        - `index_elements=["name"]`: Specifies the column(s) to check for conflicts (e.g., unique constraint or index). If a row with the same "name" exists, it triggers the update instead of an insert.
        - `values`: Defines the data to insert (e.g., `name="example", value=123`). If no conflict occurs, this data is inserted as a new row.

        The `set_` parameter (e.g., `set_=dict(value=123)`) then dictates what gets updated on conflict, overriding matching fields in `values` if specified.
        """
        index_elements = [unique_by] if isinstance(unique_by, str) else unique_by

        stmt = (
            postgres_insert(cls)
            .values(**data)
            .on_conflict_do_update(index_elements=index_elements, set_=data)
            .returning(cls)
        )

        with get_session() as session:
            result = session.exec(stmt)
            session.commit()

            # TODO this is so ugly:
            result = result.one()[0]

        return result

    def delete(self):
        """Delete instance running delete hooks and optional around_delete context manager."""

        cm = self._get_around_context_manager("around_delete") or nullcontext()

        with get_session() as session:
            if (
                old_session := Session.object_session(self)
            ) and old_session is not session:
                old_session.expunge(self)
            session.delete(self)

            self._call_hook("before_delete")
            with cm:
                session.commit()
            self._call_hook("after_delete")

        return True

    def save(self):
        """Persist instance running create/update hooks and optional around_save context manager."""

        is_new = self.is_new()
        cm = self._get_around_context_manager("around_save") or nullcontext()

        with get_session() as session:
            if (
                old_session := Session.object_session(self)
            ) and old_session is not session:
                old_session.expunge(self)

            session.add(self)

            # the order and placement of these hooks is really important
            # we need the current object to be in a session otherwise it will not be able to
            # load any relationships.
            self._call_hook("before_create" if is_new else "before_update")
            self._call_hook("before_save")

            with cm:
                session.commit()
                session.refresh(self)

            self._call_hook("after_create" if is_new else "after_update")
            self._call_hook("after_save")

            # Only call the transform method if the class is a subclass of PydanticJSONMixin
            if issubclass(self.__class__, PydanticJSONMixin):
                self.__class__.__transform_dict_to_pydantic__(self)
        return self

    def _call_hook(self, hook_name: str) -> None:
        method = getattr(self, hook_name, None)
        if callable(method):
            if method.__code__.co_argcount != 1:
                raise TypeError(
                    f"Hook '{hook_name}' must accept exactly 1 positional argument (self)"
                )
            method()

    def _get_around_context_manager(self, name: str) -> t.ContextManager | None:
        obj = getattr(self, name, None)
        if obj is None:
            return None

        # If it's a callable (method/function), call it to obtain the CM
        if callable(obj):
            obj = obj()

        cm = obj
        if not (hasattr(cm, "__enter__") and hasattr(cm, "__exit__")):
            raise TypeError(
                f"{name} must return or be a context manager implementing __enter__/__exit__"
            )
        return t.cast(t.ContextManager, cm)

    def refresh(self):
        "Refreshes an object from the database"

        with get_session() as session:
            if (
                old_session := Session.object_session(self)
            ) and old_session is not session:
                old_session.expunge(self)

            session.add(self)
            session.refresh(self)

            # Only call the transform method if the class is a subclass of PydanticJSONMixin
            if issubclass(self.__class__, PydanticJSONMixin):
                self.__class__.__transform_dict_to_pydantic__(self)

        return self

    # TODO shouldn't this be handled by pydantic?
    # TODO where is this actually used? shoudl prob remove this
    # TODO should we even do this? Can we specify a better json rendering class?
    def json(self, **kwargs):
        return json.dumps(self.dict(), default=str, **kwargs)

    # TODO should move this to the wrapper
    @classmethod
    def count(cls) -> int:
        """
        Returns the number of records in the database.
        """
        with get_session() as session:
            return session.scalar(sm.select(sm.func.count()).select_from(cls))

    # TODO got to be a better way to fwd these along...
    @classmethod
    def first(cls):
        # TODO should use dynamic pk
        return cls.select().order_by(sa.desc(cls.id)).first()

    # @classmethod
    # def last(cls):
    #     return cls.select().first()

    # TODO throw an error if this field is set on the model
    def is_new(self) -> bool:
        return not self._sa_instance_state.has_identity

    def flag_modified(self, *args: str) -> None:
        """
        Flag one or more fields as modified/mutated/dirty. Useful for marking a field containing sub-objects as modified.

        Will throw an error if an invalid field is passed.
        """

        assert len(args) > 0, "Must pass at least one field name"

        for field_name in args:
            if field_name not in self.__fields__:
                raise ValueError(f"Field '{field_name}' does not exist in the model.")

            # check if the field exists
            sa_flag_modified(self, field_name)

    def modified_fields(self) -> set[str]:
        "set of fields that are modified"

        insp = inspect(self)

        return {attr.key for attr in insp.attrs if attr.history.has_changes()}

    @classmethod
    def find_or_create_by(cls, **kwargs):
        """
        Find record or create it with the passed args if it doesn't exist.
        """

        result = cls.get(**kwargs)

        if result:
            return result

        new_model = cls(**kwargs)
        new_model.save()

        return new_model

    @classmethod
    def find_or_initialize_by(cls, **kwargs):
        """
        Unfortunately, unlike ruby, python does not have a great lambda story. This makes writing convenience methods
        like this a bit more difficult.
        """

        result = cls.get(**kwargs)

        if result:
            return result

        new_model = cls(**kwargs)
        return new_model

    @classmethod
    def primary_key_column(cls) -> Column:
        """
        Returns the primary key column of the model by inspecting SQLAlchemy field information.

        >>> ExampleModel.primary_key_field().name
        """

        # TODO note_schema.__class__.__table__.primary_key
        # TODO no reason why this couldn't be cached

        pk_columns = list(cls.__table__.primary_key.columns)

        if not pk_columns:
            raise ValueError("No primary key defined for the model.")

        if len(pk_columns) > 1:
            raise ValueError(
                "Multiple primary keys defined. This method supports only single primary key models."
            )

        return pk_columns[0]

    # TODO what's super dangerous here is you pass a kwarg which does not map to a specific
    #      field it will result in `True`, which will return all records, and not give you any typing
    #      errors. Dangerous when iterating on structure quickly
    # TODO can we pass the generic of the superclass in?
    # TODO can we type the method signature a bit better?
    # def get(cls, *args: sa.BinaryExpression, **kwargs: t.Any):
    @classmethod
    def get(cls, *args: t.Any, **kwargs: t.Any):
        """
        Gets a single record (or None) from the database. Pass an PK ID or kwargs to filter by.
        """
        # TODO id is hardcoded, not good! Need to dynamically pick the best uid field
        id_field_name = "id"

        # special case for getting by ID
        if len(args) == 1 and isinstance(args[0], (int, TypeID, str, UUID)):
            kwargs[id_field_name] = args[0]
            args = ()

        statement = select(cls).filter(*args).filter_by(**kwargs)

        with get_session() as session:
            return session.exec(statement).first()

    @classmethod
    def one_or_none(cls, *args: t.Any, **kwargs: t.Any):
        """
        Gets a single record from the database. Pass an PK ID or a kwarg to filter by.
        Returns None if no record is found. Throws an error if more than one record is found.
        """

        args, kwargs = cls.__process_filter_args__(*args, **kwargs)
        statement = select(cls).filter(*args).filter_by(**kwargs)

        with get_session() as session:
            return session.exec(statement).one_or_none()

    @classmethod
    def one(cls, *args: t.Any, **kwargs: t.Any):
        """
        Gets a single record from the database. Pass an PK ID or a kwarg to filter by.
        """

        args, kwargs = cls.__process_filter_args__(*args, **kwargs)
        statement = select(cls).filter(*args).filter_by(**kwargs)

        with get_session() as session:
            return session.exec(statement).one()

    @classmethod
    def __process_filter_args__(cls, *args: t.Any, **kwargs: t.Any):
        """
        Helper method to process filter arguments and implement some nice DX for our devs.
        """

        id_field_name = cls.primary_key_column().name

        # special case for getting by ID without having to specify the field name
        # TODO should dynamically add new pk types based on column definition
        if len(args) == 1 and isinstance(args[0], (int, TypeID, str, UUID)):
            kwargs[id_field_name] = args[0]
            args = ()

        return args, kwargs

    @classmethod
    def all(cls):
        "get a generator for all records in the database"
        with get_session() as session:
            results = session.exec(sm.select(cls))

            # TODO do we need this or can we just return results?
            for result in results:
                yield result

    @classmethod
    def sample(cls):
        """
        Pick a random record from the database. Raises if none exist.

        Helpful for testing and console debugging.
        """

        query = sm.select(cls).order_by(sa.sql.func.random()).limit(1)

        with get_session() as session:
            return session.exec(query).one()
