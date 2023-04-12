from images.models import Picture
from django.db.models import QuerySet
from pydantic import BaseModel, Field, field_serializer, model_serializer, field_validator, validator


class Schema(BaseModel):
    """
    In django-ninja we must have a base class named schema
    so that pydantic models never confused with django models
    """

    class Config:
        from_attributes = True  # aka orm_mode

    # @classmethod
    # def model_validate(cls, obj, **kwargs):
    #     __tracebackhide__ = True
    #     print('model_validate', cls.__name__)
    #     return cls.__pydantic_validator__.validate_python(obj, **kwargs)


class PictureModel(Schema):
    id: int
    title: str


class ResponseModel(Schema):
    pictures: list[PictureModel]


def run_test():
    qs = Picture.objects.all()
    print(qs.first().image.path)

    class MockResponse:
        pictures = qs

    response = MockResponse()

    obj = ResponseModel.model_validate(response)  # aka from_orm
    print(obj.model_dump())
