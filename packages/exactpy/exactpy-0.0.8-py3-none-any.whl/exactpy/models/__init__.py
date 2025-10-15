from pydantic import AliasGenerator, BaseModel, ConfigDict
from pydantic.alias_generators import to_pascal


class ExactOnlineBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(serialization_alias=to_pascal)
    )
    # resource: str

    @classmethod
    def set_as_property(cls):
        @property
        def getter(client):
            property = "_prop_%s" % (cls.__name__,)
            if not hasattr(client, property):
                setattr(client, property, cls)
            return getattr(client, property)

        return getter

    def show(id: int): ...

    def get(): ...

    def all(): ...

    def filter(): ...
