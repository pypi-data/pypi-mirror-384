from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, RootModel
from pydantic.alias_generators import to_camel


class CitraBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=True,
    )


T = TypeVar("T")


class CitraBaseModelList(RootModel[list[T]], Generic[T]):
    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, index):
        return self.root[index]

    def __len__(self):
        return len(self.root)

    def append(self, value: T):
        self.root.append(value)

    def extend(self, values: list[T]):
        self.root.extend(values)
