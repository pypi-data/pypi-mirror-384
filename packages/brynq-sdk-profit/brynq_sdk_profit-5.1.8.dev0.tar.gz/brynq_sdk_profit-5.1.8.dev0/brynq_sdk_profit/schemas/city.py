#general imports
from typing import Optional, List, Union
from datetime import date
#pydantic and pandera imports
from pydantic import BaseModel, Field, EmailStr, AnyUrl, model_validator
from pydantic.config import ConfigDict
from pandera.typing import Series
import pandera as pa
#brynq
from brynq_sdk_functions import BrynQPanderaDataFrameModel
#local imports
from .enums import (
    MatchPersonEnum, NameUseEnum, GenderEnum, NationalityEnum,
    MaritalStatusEnum, PreferredMediumEnum, AmountOfEmployeesEnum, TitleEnum
)


#--- GET SCHEMA ---
class GetCity(BrynQPanderaDataFrameModel):
    """Schema for City/Woonplaatsen get, https://docs.afas.help/apidoc/nl/Organisaties%20en%20personen#get-/connectors/Profit_Residence"""
    city: Series[str] = pa.Field(coerce=True, nullable=False, description="Woonplaats", alias="Residence")
    country_id: Series[str] = pa.Field(coerce=True, nullable=True, description="Land (code)", alias="CountryId")
    country_name: Series[str] = pa.Field(coerce=True, nullable=True, description="Land (naam)", alias="CountryName")
    phone_prefix: Series[str] = pa.Field(coerce=True, nullable=True, description="Netnummer", alias="TelephonePrefix")
    postal_code_begin: Series[str] = pa.Field(coerce=True, nullable=True, description="Begin postcode", alias="ZipCodeBegin")
    postal_code_end: Series[str] = pa.Field(coerce=True, nullable=True, description="Eind postcode", alias="ZipCodeEnd")
    creation_date: Series[str] = pa.Field(coerce=True, nullable=True, description="Aangemaakt op", alias="CreateDate")
    modified_date: Series[str] = pa.Field(coerce=True, nullable=True, description="Gewijzigd op", alias="ModifiedDate")


    class _Annotation:
        primary_key = "city"
        foreign_keys = {}
