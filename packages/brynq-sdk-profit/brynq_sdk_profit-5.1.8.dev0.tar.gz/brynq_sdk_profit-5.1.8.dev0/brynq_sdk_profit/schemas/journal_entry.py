#-- journal entries (or financiele mutaties)
#general imports
from typing import Optional, List, Union, Literal
from datetime import date
#pydantic and pandera imports
from pydantic import BaseModel, Field, EmailStr, AnyUrl, model_validator
from pydantic.config import ConfigDict
from pandera.typing import Series, DateTime, Date
import pandera as pa
#brynq
from brynq_sdk_functions import BrynQPanderaDataFrameModel
#local imports
from .enums import (
    AccountReferenceEnum
)


#--- PUT or POST SCHEMA ---
class JournalFinancialEntryParametersCreate(BaseModel):
    """
    Schema for journal financial entry parameters (dagboek)
    part of AFAS Mutaties API
    fields are inside object
    serialized result (when wrapped in nested schema structure):
    FiEntryPar: {
        Element: {
            Fields: {
                Year*: int
                Peri*: int
                UnId: str
                JoCo*: str
                AdDe: bool
                AdDa: bool
                PrTp: int
                AuNu: bool
            }
        }
    }
    """
    year: Optional[int] = Field(alias = "Year", description = "Boekjaar", default = None)
    period: Optional[int] = Field(alias = "Peri", description = "Periode", default = None)
    administration_id: Optional[str] = Field(alias = "UnId", description = "Nummer Administratie", default = None)
    journal_id: Optional[str] = Field(alias = "JoCo", description = "Dagboek", default = None, max_length = 6)
    add_specialisation_code: Optional[bool] = Field(alias = "AdDe", description = "Maak verbijzonderingscode", default = None)
    add_specilisation_application: Optional[bool] = Field(alias = "AdDa", description = "Maak verbijzonderingstoewijzing", default = None)
    booking_type: Optional[int] = Field(alias = "PrTp", description = "Type  boeking", default = None)
    auto_number_invoice: Optional[bool] = Field(alias = "AuNu", description = " Autonummering factuur", default = None)

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
        validate_by_name=True,  # Allows initializing the model using Python field names (e.g., 'is_mailbox_address').
        validate_by_alias=True, # Also allows initializing using the alias (e.g., 'PadAdr').
    )

class JournalFinancialEntryCreate(BaseModel):
    """
    Schema for journal financial entry create; FiEntries
    fields are inside objects list
    serialized result (when wrapped in nested schema structure):
    FiEntries: {
        Element: [
            {
                Fields: {
                    VaAs: str
                    AcNr: str
                    EnDa: str
                    ...
                    BpDa: str
                    AmDe: float
                    AmCr: float
                }
            }
        ]
    }
    """
    journal_number: Optional[int] = Field(alias = "EnNo", description = "Nummer journaalpost", default = None)
    account_reference: Optional[AccountReferenceEnum] = Field(alias = "VaAs", description = "Kenmerk rekening (1 = Grootboekrekening; 2 = Debiteur; 3 = Crediteur)", default = None)
    general_ledger_id: Optional[str] = Field(alias = "AcNr", description = "Account nummer", default = None, max_length = 16)
    date_booking: Optional[date] = Field(alias = "EnDa", description = "Boekingsdatum", default = None)
    date_document: Optional[date] = Field(alias = "BpDa", description = "Datum document", default = None)
    booking_number: Optional[Union[str, int]] = Field(alias = "BpNr", description = "Boekstuknummer", default = None)
    invoice_number: Optional[str] = Field(alias = "InId", description = "Factuurnummer", default = None, max_length = 12)
    description: Optional[str] = Field(alias = "Ds", description = "Omschrijving", default = None)
    debet: Optional[float] = Field(alias = "AmDe", description = "Bedrag debet", default = None)
    credit: Optional[float] = Field(alias = "AmCr", description = "Bedrag credit", default = None)
    btw_code: Optional[str] = Field(alias = "VaId", description = "Btw-code", default = None, max_length = 3)
    btw_reclaim: Optional[str] = Field(alias = "CoVc", description = "Btw-terugvordering", default = None, max_length = 16)
    currency: Optional[str] = Field(alias = "CuId", description = "Valuta", default = None, max_length = 3)
    rate: Optional[float] = Field(alias = "Rate", description = "Koers", default = None)
    foreign_currency_debet: Optional[float] = Field(alias = "AmDc", description = "Valutabedrag debet", default = None)
    foreign_currency_credit: Optional[float] = Field(alias = "AmCc", description = "Valutabedrag credit", default = None)
    due_date: Optional[date] = Field(alias = "DaEx", description = "Vervaldatum", default = None)
    payment_reference: Optional[str] = Field(alias = "PaRe", description = "Betalingskenmerk", default = None, max_length = 32)
    judge: Optional[str] = Field(alias = "Judg", description = "Beoordelaar", default = None, max_length = 15)
    block_for_payment: Optional[bool] = Field(alias = "BlPa", description = "Blokkeren voor betaling", default = None)

    project_id: Optional[str] = Field(alias = "PrId", description = "Projectnummer", default = None, max_length = 15)
    #TODO add other optional fields


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
        validate_by_name=True,  # Allows initializing the model using Python field names (e.g., 'is_mailbox_address').
        validate_by_alias=True, # Also allows initializing using the alias (e.g., 'PadAdr').
    )


class JournalFinancialDimEntries(BaseModel):
    """
    Schema for journal financial dim entries; FiDimEntries
    fields are inside objects list
    serialized result (when wrapped in nested schema structure):
    FiDimEntries: {
        Element: [
            {
                Fields: {
                    DiC1: str
                    DiC2: str
                    ...
                }
            }
        ]
    }
    """
    specialisation_code_1: Optional[str] = Field(alias = "DiC1", description = "Code verbijzonderingsas 1", default = None, max_length = 16)
    specialisation_code_2: Optional[str] = Field(alias = "DiC2", description = "Code verbijzonderingsas 2", default = None, max_length = 16)
    specialisation_code_3: Optional[str] = Field(alias = "DiC3", description = "Code verbijzonderingsas 3", default = None, max_length = 16)
    specialisation_code_4: Optional[str] = Field(alias = "DiC4", description = "Code verbijzonderingsas 4", default = None, max_length = 16)
    specialisation_code_5: Optional[str] = Field(alias = "DiC5", description = "Code verbijzonderingsas 5", default = None, max_length = 16)
    #TODO add other optional fields

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
        validate_by_name=True,
        validate_by_alias=True,
    )

class JournalentryGetSchema(BrynQPanderaDataFrameModel):
    salary_process: Series[str] = pa.Field(coerce=True, nullable=True)
    employer: Series[str] = pa.Field(coerce=True)
    name: Series[str] = pa.Field(coerce=True)
    wage_component: Series[int] = pa.Field(coerce=True)
    wage_component_sequence_nmbr: Series[int] = pa.Field(coerce=True)
    salary_process_plan: Series[int] = pa.Field(coerce=True)
    sequence_number: Series[int] = pa.Field(coerce=True)

    class Config:
        coerce = True
        strict = True
