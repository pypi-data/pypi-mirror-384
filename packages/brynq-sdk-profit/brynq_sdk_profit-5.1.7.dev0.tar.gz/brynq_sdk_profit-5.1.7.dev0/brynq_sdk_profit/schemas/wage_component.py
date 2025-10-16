import pandera as pa
from pandera.typing import Series
from datetime import date
from .employee import EmployeeBase
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal

#--- PUT or POST SCHEMA ---
class WageComponentPost(BaseModel):
    """Pydantic schema for creating a new wage component, part of AFAS Loonadministratie API (HrVarValue: https://docs.afas.help/apidoc/nl/Loonadministratie#post-/connectors/HrVarValue)"""

    # Core fields
    parameter: Optional[int] = Field(default=None, serialization_alias="VaId", description="Parameter (VaId)", examples=[2689610, 2689810])
    value: Optional[str] = Field(default=None, serialization_alias="Va", description="Value (Waarde)", max_length=20)
    employee_id: Optional[str] = Field(default=None, serialization_alias="EmId", description="Employee ID (Medewerker)", max_length=15)

    # Additional fields that belong in Fields
    start_date: Optional[date] = Field(default=None, serialization_alias="DaBe", description="Start date (Begindatum)")
    end_date: Optional[date] = Field(default=None, serialization_alias="DaEn", description="End date (Einddatum)")
    employment: Optional[int] = Field(default=None, serialization_alias="EnSe", description="Employment (Dienstverband)")
    application_type: Optional[Literal['T', 'V', 'H']] = Field(default=None, serialization_alias="DiTp", description="Application type (Toepassing, T = Toepassen bij alle dienstverbanden; V = Verdelen over alle dienstverbanden; H = Toepassen op hoofddienstverband;)")
    reason: Optional[bytes] = Field(default=None, serialization_alias="ReAu", description="Reason (Reden)")

    model_config = ConfigDict(
        serialize_by_alias=True,
        str_strip_whitespace=True,
        str_min_length=0,
        str_max_length=255,
        coerce_numbers_to_str=False,
        extra='forbid',
        frozen=True,
        allow_inf_nan=False,
        ser_json_timedelta='iso8601',
        ser_json_bytes='base64',
        validate_default=True,
        use_enum_values=True,
        # Why: These two settings replace the deprecated 'populate_by_name=True'.
        validate_by_name=True,  # Allows initializing the model using Python field names (e.g., 'is_postal_address').
        validate_by_alias=True, # Also allows initializing using the serialization_alias (e.g., 'PadAdr').
    )

class WageComponentPut(WageComponentPost):
    """Pydantic schema for updating a wage component"""

# --- Nested API Payload Structure Classes ---
class WageComponentElement(BaseModel):
    """Element object within HrVarValue"""
    fields: WageComponentPost = Field(serialization_alias="Fields")

class WageComponentObject(BaseModel):
    """Object object within HrVarValue, so HrVarValue is initialised"""
    element: WageComponentElement = Field(serialization_alias="Element")

class WageComponentPayload(BaseModel):
    """Top-level payload structure matching the HrVarValue API endpoint"""
    hr_var_value: WageComponentObject = Field(serialization_alias="HrVarValue")

#--- GET SCHEMA ---
class WageComponentGetSchema(pa.DataFrameModel):
    employee_id: Series[str] = pa.Field(coerce=True, nullable=True)  # Added from EmployeeBase
    wage_component_id: Series[int] = pa.Field(coerce=True, nullable=True)
    parameter: Series[int] = pa.Field(coerce=True, nullable=False)
    start_date: Series[date] = pa.Field(coerce=True, nullable=False)
    value: Series[float] = pa.Field(coerce=True, nullable=True)
    booked_by: Series[str] = pa.Field(coerce=True, nullable=False)
    end_date: Series[date] = pa.Field(coerce=True, nullable=True)

    class Config:
        coerce = True
        strict = True
