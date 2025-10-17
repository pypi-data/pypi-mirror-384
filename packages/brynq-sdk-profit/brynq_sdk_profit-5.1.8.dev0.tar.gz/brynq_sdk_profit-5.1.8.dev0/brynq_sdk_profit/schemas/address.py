from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from datetime import date
from typing import Optional, List, Union, Literal
from brynq_sdk_functions import BrynQPanderaDataFrameModel

from .person import PersonElementBase
from .organisation import OrganisationElementBase

#NOTE: THIS IS FOR PERSON/organisation: NOT FOR 'post/connectors/KnAddress'
#fields for address
class AddressCreate(BaseModel):
    """Defines the actual data fields for a single address record used for put and post requests.
    documenation: https://docs.afas.help/apidoc/nl/Organisaties%20en%20personen#post-/connectors/KnPerson/KnBasicAddressAdr"""
    # Required fields
    country: Optional[str] = Field(default=None, max_length=3, serialization_alias="CoId", description="Land", example="NL")
    is_mail_address: Optional[bool] = Field(default=None, serialization_alias="PbAd", description="Postbusadres", example="True")
    address_active_effective_date: Optional[date] = Field(default=None, serialization_alias="BeginDate", description="Begin datum adres", example="date(2024, 1, 1), or 2024-01-01")
    find_address_based_on_postal_code: Optional[bool] = Field(default=None, serialization_alias="ResZip", description="Zoek adres op basis van postcode", example="True")

    # Optional fields
    street_addition: Optional[str] = Field(default=None, serialization_alias="StAd", description="Straat toevoeging", example="Main Street")
    street: Optional[str] = Field(default=None, max_length=60, serialization_alias="Ad", description="Straat", example="Molendijk")
    house_number: Optional[int] = Field(default=None, serialization_alias="HmNr", description="47")
    house_number_addition: Optional[str] = Field(default=None, max_length=30, serialization_alias="HmAd", description="Huisnummer toevoeging", example="A")
    postal_code: Optional[str] = Field(default=None, max_length=15, serialization_alias="ZpCd", description="Postcode", example="1234AB")
    city: Optional[str] = Field(default=None, max_length=50, serialization_alias="Rs", description="Plaats", example="Amsterdam")
    address_addition: Optional[str] = Field(default=None, serialization_alias="AdAd", description="Adres toevoeging", example="appartment top floor")

    model_config = ConfigDict(serialize_by_alias=True,
                              str_strip_whitespace = True,
                              str_min_length=0,
                              str_max_length=255,
                              coerce_numbers_to_str=False,
                              extra='allow', #allow to dump extra fields. (maybe needed for custom?)
                              frozen=True, #all values passes shoul dbe the end result.
                              allow_inf_nan = False,
                              ser_json_timedelta = 'iso8601', #is this correct? could also be 'float'
                              ser_json_bytes= 'base64', #is this correct? options: base64, hex, utf8
                              validate_default = True,
                              use_enum_values = True,
                              )

# Template classes for missing schemas
class AddressGetSchema(BrynQPanderaDataFrameModel):
    """Schema for profit address data"""
    pass


# Payload Structure Schemas (CREATE/UPDATE)
# it is easiest to read from the bottom up (the low level classes are used to create the higher level classes and need to be defined first).
# in general we have:
# {schema_name : { Element: {Fields : {}, Objects: [schema_name_objects] } }}
# in which schema_name_objects is a list of schemas which are nested in 'schema_name' and in turn each object (=schema) in the list has this same structure outlined above,
# unless it has no nested objects/schemas, then it is just the fields.
class AliasedModel(BaseModel):
    """Base model to apply serialization by alias to all structural classes."""
    model_config = ConfigDict(
        serialize_by_alias=True,
        validate_by_name=True,
        validate_by_alias=True,
    )

#Object: Element -> Fields
class ElementItem(AliasedModel):
    """Represents a single item in an address list, creating the {"Fields": ...} object."""
    fields: AddressCreate = Field(serialization_alias="Fields")

#Object: Element -> Objects -> KnBasicAddressAdr and KnBasicAddressPad; These two classes create the {"KnBasicAddressAdr": ...} objects in the payload
class KnBasicAddressAdr(AliasedModel):
    """Represents the object containing the address list, creating the {"Element": [...]} structure."""
    element: List[ElementItem] = Field(default_factory=list, serialization_alias="Element")

class KnBasicAddressPad(AliasedModel):
    """Represents the object containing the PO box list, creating the {"Element": [...]} structure."""
    element: List[ElementItem] = Field(default_factory=list, serialization_alias="Element")

class KnBasicAddressAdrObject(AliasedModel):
    """Creates the final address object {"KnBasicAddressAdr": ...} to be placed in the Objects list."""
    kn_basic_address_adr: KnBasicAddressAdr = Field(serialization_alias="KnBasicAddressAdr")

class KnBasicAddressPadObject(AliasedModel):
    """Creates the final PO box object {"KnBasicAddressPad": ...} to be placed in the Objects list."""
    kn_basic_address_pad: KnBasicAddressPad = Field(serialization_alias="KnBasicAddressPad")

#KnPerson.Element (Fields and Objects)
class AddressElement(AliasedModel):
    """Represents the main 'Element' containing top-level person/organisation fields and the nested 'Objects' list."""
    fields: Union[PersonElementBase, OrganisationElementBase] = Field(serialization_alias="Fields")
    objects: Optional[List[Union[
        "KnBasicAddressAdrObject",
        "KnBasicAddressPadObject",
    ]]] = Field(default=None, serialization_alias="Objects")
    action: Optional[Literal["insert", 'update']] = Field(default=None, serialization_alias="@action")

#KnPerson -> Element (Fields and Objects)
class AddressObject(AliasedModel):
    """Wraps the main AddressElement to form the content of the KnPerson object"""
    element: AddressElement = Field(serialization_alias="Element")

#KnPerson
class AddressPayload(AliasedModel):
    """The root model for the entire API request body, can be either KnPerson or KnOrganisation."""
    kn_person: Optional[AddressObject] = Field(default=None, alias="KnPerson", serialization_alias="KnPerson")
    kn_organisation: Optional[AddressObject] = Field(default=None, alias="KnOrganisation", serialization_alias="KnOrganisation")
