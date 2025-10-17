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
class GetTitle(BrynQPanderaDataFrameModel):
    """Schema for Titles/Titels get, https://docs.afas.help/apidoc/nl/Organisaties%20en%20personen#get-/connectors/ProfitTitles"""
    title: Series[str] = pa.Field(coerce=True, nullable=False, description="Titel/aanhef", alias="TtId")
    description: Series[str] = pa.Field(coerce=True, nullable=True, description="Omschrijving", alias="Ds")

    class _Annotation:
        primary_key = "title"
        foreign_keys = {}
