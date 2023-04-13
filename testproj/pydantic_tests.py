from images.models import Picture
from django.db.models import QuerySet
from pydantic import BaseModel, Field, field_serializer, model_serializer, field_validator, validator, root_validator
from schema import Schema


class PictureModel(Schema):
    id: int
    title: str
    image: str
    foo: str
    # bar: str
    type: str
    type_display: str = Field(alias='get_type_display')
    alias_test: str = Field(alias='rel.method')

    @staticmethod
    def resolve_foo(obj):
        return f'foo is: <{obj}>'

    # def resolve_bar(self, obj):
    #     return f'bar is: <bar {obj}>, title={self.title}'


class ResponseModel(Schema):
    pictures: list[PictureModel]


def run_test():
    qs = Picture.objects

    class MockResponse:
        pictures = qs

    response = MockResponse()

    obj = ResponseModel.from_orm(response)  # aka from_orm
    print(obj.model_dump())
