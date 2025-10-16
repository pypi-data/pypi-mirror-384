# schemas/base.py
from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel, Field

# A generic type variable that can be any Pydantic model.
FieldsModel = TypeVar('FieldsModel', bound=BaseModel)
ObjectsModel = TypeVar('ObjectsModel', bound=BaseModel)

class BaseElement(BaseModel, Generic[FieldsModel, ObjectsModel]):
    """
    A generic base for the 'Element' structure that contains
    strongly-typed fields and a list of nested objects.
    """
    fields: FieldsModel = Field(serialization_alias="Fields")
    objects: Optional[List[ObjectsModel]] = Field(default=None, serialization_alias="Objects")

class BaseObject(BaseModel, Generic[FieldsModel, ObjectsModel]):
    """A generic base for the 'Object' structure that contains one element."""
    element: BaseElement[FieldsModel, ObjectsModel] = Field(serialization_alias="Element")

class BasePayload(BaseModel, Generic[FieldsModel, ObjectsModel]):
    """A generic base for the top-level payload structure."""
    kn_object: BaseObject[FieldsModel, ObjectsModel] = Field(serialization_alias="KnPerson")  # Note: Alias will be overridden

# Specialized base classes for common patterns
class BaseElementWithFieldsOnly(BaseModel, Generic[FieldsModel]):
    """A generic base for elements that only contain fields (no objects)."""
    fields: FieldsModel = Field(serialization_alias="Fields")

class BaseObjectWithFieldsOnly(BaseModel, Generic[FieldsModel]):
    """A generic base for objects that contain elements with only fields."""
    element: Optional[List[BaseElementWithFieldsOnly[FieldsModel]]] = Field(default=None, serialization_alias="Element")

class BaseSchemaWithFieldsOnly(BaseModel, Generic[FieldsModel]):
    """A generic base for schemas that contain objects with only fields."""
    kn_object: BaseObjectWithFieldsOnly[FieldsModel] = Field(serialization_alias="KnObject")  # Note: Alias will be overridden
