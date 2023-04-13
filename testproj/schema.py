from typing import Any, Callable, Dict, Type, TypeVar, Union, no_type_check

import pydantic
from django.db.models import Manager, QuerySet
from django.db.models.fields.files import FieldFile
from django.template import Variable, VariableDoesNotExist
from pydantic import BaseModel, Field, validator, root_validator
from pydantic.main import ModelMetaclass

# pydantic_version = list(map(int, pydantic.VERSION.split(".")[:2]))
# assert pydantic_version >= [1, 6], "Pydantic 1.6+ required"

__all__ = ["BaseModel", "Field", "validator", "DjangoGetter", "Schema"]

S = TypeVar("S", bound="Schema")


class DjangoGetter:
    __slots__ = ("_obj", "_schema_cls")

    def __init__(self, obj: Any, schema_cls: "Type[Schema]"):
        self._obj = obj
        self._schema_cls = schema_cls

    def __getattr__(self, key: str) -> Any:
        resolver = self._schema_cls._ninja_resolvers.get(key)
        if resolver:
            item = resolver(getter=self)
        else:
            try:
                item = getattr(self._obj, key)
            except AttributeError:
                try:
                    # item = attrgetter(key)(self._obj)
                    item = Variable(key).resolve(self._obj)
                    # TODO: Variable(key) __init__ is actually slower than
                    #       resolve - so it better be cached
                except VariableDoesNotExist as e:
                    raise KeyError(key) from e
        return self._convert_result(item)

    # def get(self, key: Any, default: Any = None) -> Any:
    #     try:
    #         return self[key]
    #     except KeyError:
    #         return default

    def _convert_result(self, result: Any) -> Any:
        if isinstance(result, Manager):
            return list(result.all())

        elif isinstance(result, getattr(QuerySet, "__origin__", QuerySet)):
            return list(result)

        if callable(result):
            return result()

        elif isinstance(result, FieldFile):
            if not result:
                return None
            return result.url

        return result


class Resolver:
    __slots__ = ("_func", "_static")
    _static: bool
    _func: Any

    def __init__(self, func: Union[Callable, staticmethod]):
        if isinstance(func, staticmethod):
            self._static = True
            self._func = func.__func__
        else:
            self._static = False
            self._func = func

    def __call__(self, getter: DjangoGetter) -> Any:
        if self._static:
            return self._func(getter._obj)
        return self._func(self._fake_instance(getter), getter._obj)

    def _fake_instance(self, getter: DjangoGetter) -> "Schema":
        """
        Generate a partial schema instance that can be used as the ``self``
        attribute of resolver functions.
        """

        class PartialSchema(Schema):
            def __getattr__(self, key: str) -> Any:
                print('!!!1', key)
                value = getattr(getter, key)
                print('!!!2', repr(value))
                field = getter._schema_cls.__fields_set__[key]
                print('!!!3')
                value = field.validate(value, values={}, loc=key, cls=None)[0]
                print('!!!4')
                return value

        return PartialSchema()


class ResolverMetaclass(ModelMetaclass):
    _ninja_resolvers: Dict[str, Resolver]

    @no_type_check
    def __new__(cls, name, bases, namespace, **kwargs):
        resolvers = {}

        for base in reversed(bases):
            base_resolvers = getattr(base, "_ninja_resolvers", None)
            if base_resolvers:
                resolvers.update(base_resolvers)
        for attr, resolve_func in namespace.items():
            if not attr.startswith("resolve_"):
                continue
            if (
                not callable(resolve_func)
                # A staticmethod isn't directly callable in Python <=3.9.
                and not isinstance(resolve_func, staticmethod)
            ):
                continue  # pragma: no cover
            resolvers[attr[8:]] = Resolver(resolve_func)

        result = super().__new__(cls, name, bases, namespace, **kwargs)
        result._ninja_resolvers = resolvers
        return result


class Schema(BaseModel, metaclass=ResolverMetaclass):
    class Config:
        from_attributes = True  # aka orm_mode

    @root_validator(pre=True)
    def run_root_validator(cls, values):
        values = DjangoGetter(values, cls)
        print('!--> run_root_validator', values, type(values))
        # # print(dir(cls))
        # print(cls.__dict__)

        return values

    @classmethod
    def from_orm(cls: Type[S], obj: Any) -> S:
        return cls.model_validate(obj)

    def dict(self, *a, **kw):
        return self.model_dump()


# class Schema(BaseModel, metaclass=ResolverMetaclass):
#     class Config:
#         orm_mode = True
#         getter_dict = DjangoGetter

#     @classmethod
#     def from_orm(cls: Type[S], obj: Any) -> S:
#         getter_dict = cls.__config__.getter_dict
#         obj = (
#             # DjangoGetter also needs the class so it can find resolver methods.
#             getter_dict(obj, cls)
#             if issubclass(getter_dict, DjangoGetter)
#             else getter_dict(obj)
#         )
#         return super().from_orm(obj)

#     @classmethod
#     def _decompose_class(cls, obj: Any) -> GetterDict:
#         # This method has backported logic from Pydantic 1.9 and is no longer
#         # needed once that is the minimum version.
#         if isinstance(obj, GetterDict):
#             return obj
#         return super()._decompose_class(obj)  # pragma: no cover
