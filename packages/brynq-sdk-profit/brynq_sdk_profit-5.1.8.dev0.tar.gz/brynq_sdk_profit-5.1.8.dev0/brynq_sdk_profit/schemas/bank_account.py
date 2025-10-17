from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from typing import Optional, Literal, List
#local imports
from .enums import CodeDoorberekening
from .person import PersonElementBase

# Employee bank account update schema, post /connectors/knPerson/KnBankAccount, put /connectors/KnOrganisation/KnBankAccount
class PostBankAccountPerson(BaseModel):
    """
    can be bosed used for employee or organisation bank account
    https://docs.afas.help/apidoc/nl/Organisaties%20en%20personen#put-/connectors/KnPerson
    """
    #required fields
    bank_country: str = Field(max_length=3, serialization_alias="CoId", description="Land van de bank")

    #optional fields
    employee_id: Optional[str] = Field(default=None, serialization_alias="@EmId", description="Medewerker-id") #used in special case for employee bank account
    iban_check: Optional[bool] = Field(default=None, serialization_alias="IbCk", description="IBAN-controle")
    iban: Optional[str] = Field(default=None, max_length=40, serialization_alias="Iban", description="IBAN-nummer")
    bank_account: Optional[str] = Field(default=None, max_length=40, serialization_alias="BaAc", description="Bankrekening")
    bank_type: Optional[int] = Field(default=None, serialization_alias="BkTp", description="Type bank")
    bank: Optional[str] = Field(default=None, max_length=15, serialization_alias="BkIc", description="Bank")
    accept_blocked_bank_account: Optional[bool] = Field(default=None, serialization_alias="AcGa", description="G-rekening")
    accept_cheque: Optional[bool] = Field(default=None, serialization_alias="AcCk", description="Cheque")
    deviating_name: Optional[str] = Field(default=None, max_length=80, serialization_alias="DiNm", description="Afwijkende naam")
    deviating_location: Optional[str] = Field(default=None, max_length=35, serialization_alias="DiPl", description="Afwijkende woonplaats")
    bic_code: Optional[str] = Field(default=None, max_length=11, serialization_alias="Bic", description="BIC-code")
    bank_name: Optional[str] = Field(default=None, max_length=35, serialization_alias="BaNm", description="Naam bank")
    bank_branch: Optional[str] = Field(default=None, max_length=35, serialization_alias="BaFi", description="Filiaal van de bank")
    bank_address: Optional[str] = Field(default=None, max_length=35, serialization_alias="BaAd", description="Adres van de bank")
    bank_location: Optional[str] = Field(default=None, max_length=35, serialization_alias="BaPl", description="Vestigingsplaats bank")
    charge_code: Optional[CodeDoorberekening] = Field(default=None, serialization_alias="CalM", description="Code doorberekening")

    model_config = ConfigDict(serialize_by_alias=True,
                              str_strip_whitespace = True,
                              str_min_length=0,
                              str_max_length=255,
                              coerce_numbers_to_str=False,
                              extra='allow', #allow to dump extra fields.
                              frozen=True, #all values passes shoul dbe the end result.
                              allow_inf_nan = False,
                              ser_json_timedelta = 'iso8601', #is this correct? could also be 'float'
                              ser_json_bytes= 'base64', #is this correct? options: base64, hex, utf8
                              validate_default = True,
                              use_enum_values = True,
                              )

# Get schema (placeholder for bank account retrieval)
class GetBankAccountSchema(BaseModel):
    """Schema for bank account retrieval operations"""
    pass  # TODO: Implement when needed

# =============================================================================
# PERSON PATH SCHEMAS (Following address schema pattern)
# =============================================================================
# These schemas are for the PERSON API endpoints:
# - API Endpoint: /connectors/KnPerson/KnBankAccount
# - Structure: KnPerson -> Element -> Fields + Objects -> objects.KnBankAccount -> Element -> Fields
# - Use case: Person-level bank account operations (same level as address objects)
# =============================================================================
class AliasedModel(BaseModel):
    """Base model to apply serialization by alias to all structural classes."""
    model_config = ConfigDict(
        serialize_by_alias=True,
        validate_by_name=True,
        validate_by_alias=True,
    )

#Object: Element -> Fields
class BankAccountElementItem(AliasedModel):
    """Represents a single item in a bank account list, creating the {"Fields": ...} object."""
    fields: PostBankAccountPerson = Field(serialization_alias="Fields")

#Object: Element -> Objects -> KnBankAccount; This class creates the {"KnBankAccount": ...} object in the payload
class KnBankAccount(AliasedModel):
    """Represents the object containing the bank account list, creating the {"Element": [...]} structure."""
    element: List[BankAccountElementItem] = Field(default_factory=list, serialization_alias="Element")

class KnBankAccountObject(AliasedModel):
    """Creates the final bank account object {"KnBankAccount": ...} to be placed in the Objects list."""
    kn_bank_account: KnBankAccount = Field(serialization_alias="KnBankAccount")

#KnPerson.Element (Fields and Objects)
class BankAccountElement(AliasedModel):
    """Represents the main 'Element' containing top-level person fields and the nested 'Objects' list."""
    fields: PersonElementBase = Field(serialization_alias="Fields")
    objects: Optional[List[KnBankAccountObject]] = Field(default=None, serialization_alias="Objects")
    action: Literal["insert"] = Field(default="insert", serialization_alias="@action")

#KnPerson -> Element (Fields and Objects)
class BankAccountPerson(AliasedModel):
    """Person schema itself, only contains the nested 'Element' structure. This schema is used to create the {"KnPerson":{"Element":...}} structure in the payload"""
    element: BankAccountElement = Field(serialization_alias="Element")

#KnPerson
class BankAccountPayload(AliasedModel):
    """The root model for the entire API request body. This ensures that we serialize with {"KnPerson":...} alias as the root object"""
    kn_person: BankAccountPerson = Field(serialization_alias="KnPerson")

#---------------- EMPLOYEE BANK ACCOUNT FIELDS SCHEMA ----------------
class PostBankAccountEmployee(BaseModel):
    """
    Schema for the fields within a single employee bank account record.
    Corresponds to: ... -> AfasBankInfo -> Element -> Fields
    """
    # Required fields
    account_id: str = Field(max_length=42, serialization_alias="AcId", description="Rekeningnummer")
    is_cash_payment: bool = Field(serialization_alias="NoBk", description="Kasbetaling")
    sequence_number: int = Field(serialization_alias="SeNo", description="Volgnummer")
    is_salary_account: bool = Field(serialization_alias="SaAc", description="Salarisrekening")
    bank_type: int = Field(serialization_alias="BkTp", description="Type bank")

    # Optional fields
    payment_reference: Optional[str] = Field(default=None, max_length=32, serialization_alias="Ds", description="Betalingskenmerk")
    deviating_name: Optional[str] = Field(default=None, max_length=80, serialization_alias="Nm", description="Afwijkende naam")
    deviating_location: Optional[str] = Field(default=None, max_length=50, serialization_alias="Rs", description="Afwijkende woonplaats")
    wage_component: Optional[int] = Field(default=None, serialization_alias="ScId", description="Looncomponent")
    bank_country: Optional[str] = Field(default=None, max_length=3, serialization_alias="CoId", description="Land")
    bank: Optional[str] = Field(default=None, max_length=15, serialization_alias="BkIc", description="Bank")
    is_foreign_sepa: Optional[bool] = Field(default=None, serialization_alias="FoPa", description="Rekening buiten SEPA-gebied")
    iban_check: Optional[bool] = Field(default=None, serialization_alias="IbCk", description="IBAN controle")
    iban: Optional[str] = Field(default=None, max_length=40, serialization_alias="Iban", description="IBAN nummer")
    bic_code: Optional[str] = Field(default=None, max_length=40, serialization_alias="Bic", description="BIC Code")

    model_config = ConfigDict(serialize_by_alias=True,
                              str_strip_whitespace = True,
                              str_min_length=0,
                              str_max_length=255,
                              coerce_numbers_to_str=False,
                              extra='allow', #allow to dump extra fields.
                              frozen=True, #all values passes shoul dbe the end result.
                              allow_inf_nan = False,
                              ser_json_timedelta = 'iso8601', #is this correct? could also be 'float'
                              ser_json_bytes= 'base64', #is this correct? options: base64, hex, utf8
                              validate_default = True,
                              use_enum_values = True,
                              )

# =============================================================================
# EMPLOYEE PATH SCHEMAS (Different from PERSON path above)
# =============================================================================
# These schemas are for the EMPLOYEE API endpoints, which have a different structure:
# - API Endpoint: /connectors/KnEmployee/AfasBankInfo
# - Structure: AfasEmployee -> Element(@EmId) -> Objects -> AfasBankInfo -> Element(@NoBk) -> Fields
# - Use case: Employee-specific bank account operations with additional employee fields
# =============================================================================
#Element -> Fields
class AfasBankInfoElement(AliasedModel):
    """
    this will create Fields: "Element": {
              "@AcId": "NL13TEST0123456789",
              "@NoBk": false,
              "Action": "insert",
              "Fields": {
                 ...
                 }
                }
    """
    fields: PostBankAccountEmployee = Field(serialization_alias="Fields")
    account_id_attr: Optional[str] = Field(default=None, serialization_alias="@AcId", description="Account ID attribute")
    no_bank_attr: Optional[bool] = Field(default=None, serialization_alias="@NoBk", description="No bank attribute")
    action: Optional[Literal["insert", "update"]] = Field(default=None, serialization_alias="Action", description="Action for this bank account")

#AfasBankInfo only contains Element (which contains Fields)
class AfasBankInfo(AliasedModel):
    element: List[AfasBankInfoElement] = Field(serialization_alias="Element")

#Object: Objects -> AfasBankInfo
class AfasBankInfoObject(AliasedModel):
    """Creates the final bank account object {"AfasBankInfo": ...} to be placed in the Objects list."""
    afas_bank_info: AfasBankInfo = Field(serialization_alias="AfasBankInfo")

#AfasEmployee.Element (which contains Objects)
class BankAccountEmployeeElement(AliasedModel):
    """Represents the main 'Element'. Containing top-level employee id and action (via @action and @EmId) fields and the nested 'Objects' list."""
    objects: List[AfasBankInfoObject] = Field(serialization_alias="Objects") #doesnt have to be a list?
    employee_id: str = Field(serialization_alias="@EmId")
    action: Literal["insert", "update"] = Field(default="insert", serialization_alias="@action")

#AfasEmployee -> Element
class BankAccountEmployee(AliasedModel):
    """Employee schema itself, only contains the nested 'Element' structure. This schema is used to create the {"AfasEmployee":{"Element":...}} element in the payload"""
    element: BankAccountEmployeeElement = Field(serialization_alias="Element")

#AfasEmployee
class BankAccountEmployeePayload(AliasedModel):
    """The root model for the entire API request body. This ensures that we serialize with {"AfasEmployee":...} alias as the root object"""
    afas_employee: BankAccountEmployee = Field(serialization_alias="AfasEmployee")
