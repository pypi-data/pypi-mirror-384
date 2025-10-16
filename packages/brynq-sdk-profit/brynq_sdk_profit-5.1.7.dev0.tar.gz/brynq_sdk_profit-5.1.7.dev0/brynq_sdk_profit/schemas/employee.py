#general imports
from typing import Optional, List, Union, Literal, Any
from datetime import date, datetime
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
    MaritalStatusEnum, PreferredMediumEnum, AmountOfEmployeesEnum, StatusEnum,
    StartPhaseEnum, PaymentFrequencyEnum, PayslipDistributionEnum, AnnualStatementDistributionEnum,
    EmailEnum, TransitionEnum
)
from .person import PersonPayload
from .contract import ContractCreate
from .function import FunctionCreate
from .timetable import TimeTableCreate, WorkTimeCreate
from .salary import SalaryCreate, SalaryAdditionCreate
from .agency_fiscus import AgencyFiscusCreate


class EmployeeBase(BaseModel):
    employee_id: Optional[str] = Field(default=None, max_length=15, alias="EmId", description="Medewerker", examples=["1234567890", "9876543210", "1122334455"])
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
class EmployeeGetSchema(BrynQPanderaDataFrameModel):
    # Required Fields
    employee_id: Series[str] = pa.Field(coerce=True, nullable=False)
    person_id: Series[str] = pa.Field(coerce=True, nullable=False)
    gender: Series[str] = pa.Field(coerce=True, nullable=False)
    first_name: Series[str] = pa.Field(coerce=True, nullable=False)
    last_name: Series[str] = pa.Field(coerce=True, nullable=False)
    employer_number: Series[str] = pa.Field(coerce=True, nullable=True)
    prefix_birth_name: Series[str] = pa.Field(coerce=True, nullable=True)
    birth_date: Series[datetime] = pa.Field(coerce=True, nullable=True)
    nationality: Series[str] = pa.Field(coerce=True, nullable=True)
    ssn: Series[str] = pa.Field(coerce=True, nullable=True)
    title: Series[str] = pa.Field(coerce=True, nullable=True)
    phone_work: Series[str] = pa.Field(coerce=True, nullable=True)
    mail_work: Series[str] = pa.Field(coerce=True, nullable=True)
    street: Series[str] = pa.Field(coerce=True, nullable=True)
    state: Series[str] = pa.Field(coerce=True, nullable=True)
    street_number: Series[str] = pa.Field(coerce=True, nullable=True)
    street_number_add: Series[str] = pa.Field(coerce=True, nullable=True)
    postal_code: Series[str] = pa.Field(coerce=True, nullable=True)
    city: Series[str] = pa.Field(coerce=True, nullable=True)
    country: Series[str] = pa.Field(coerce=True, nullable=True)
    function_start_date: Series[datetime] = pa.Field(coerce=True, nullable=True)
    function: Series[str] = pa.Field(coerce=True, nullable=True)
    organisational_unit: Series[str] = pa.Field(coerce=True, nullable=True)
    supervisor_id: Series[str] = pa.Field(coerce=True, nullable=True)
    cost_center: Series[str] = pa.Field(coerce=True, nullable=True)
    work_schedule_valid_from: Series[datetime] = pa.Field(coerce=True, nullable=True)
    days_per_week: Series[float] = pa.Field(coerce=True, nullable=True)
    weekly_hours: Series[float] = pa.Field(coerce=True, nullable=True)
    contract_start_date: Series[datetime] = pa.Field(coerce=True, nullable=True)
    end_date_contract: Series[datetime] = pa.Field(coerce=True, nullable=True)
    type_of_contract: Series[str] = pa.Field(coerce=True, nullable=True)
    type_of_employee: Series[str] = pa.Field(coerce=True, nullable=True)
    probation_end_date: Series[datetime] = pa.Field(coerce=True, nullable=True)
    termination_date: Series[datetime] = pa.Field(coerce=True, nullable=True)
    termination_reason: Series[str] = pa.Field(coerce=True, nullable=True)
    salary_amount: Series[float] = pa.Field(coerce=True, nullable=True)
    salary_type: Series[str] = pa.Field(coerce=True, nullable=True)

    class Config:
        coerce = True
        strict = True

class EmployeeCreate(EmployeeBase):
    date_of_death: Optional[Union[date, Literal[""]]] = Field(default=None, alias="DaDe", description="Overlijdensdatum", examples=[date(2020, 1, 1), date(2021, 1, 30), date(2022, 4, 2)])
    date_of_marriage: Optional[Union[date, Literal[""]]] = Field(default=None, alias="DaMa", description="Huwelijksdatum", examples=[date(2010, 1, 1), date(2011, 1, 30), date(2012, 4, 2)])
    date_of_divorce: Optional[Union[date, Literal[""]]] = Field(default=None, alias="DaDi", description="Datum scheiding", examples=[date(2015, 1, 1), date(2016, 1, 30), date(2017, 4, 2)])
    status: Optional[StatusEnum] = Field(default=None, alias="StId", description="Status: I = In dienst; S = Sollicitant; U = Uit dienst", examples=[StatusEnum.IN_DIENST, StatusEnum.SOLLICITANT, StatusEnum.UIT_DIENST])
    work_level: Optional[int] = Field(default=None, alias="WrLv", description="Werkniveau", examples=[1, 2, 3]) # not sure if its actuall an enum.
    blocked: Optional[bool] = Field(default=None, alias="Bl", description="Geblokkeerd", examples=[True, False])
    objection_to_recording: Optional[bool] = Field(default=None, alias="LwOb", description="Bezwaar tegen vastlegging", examples=[True, False])
    belongs_to_targetgroup: Optional[bool] = Field(default=None, alias="LwTg", description="Behorend tot doelgroep", examples=[True, False])
    city_of_birth: Optional[str] = Field(default=None, max_length=50, alias="LwRs", description="Geboorteplaats", examples=["Amsterdam", "Rotterdam", "Utrecht", "Gouda"])
    country_of_birth: Optional[str] = Field(default=None, max_length=3, alias="LwNa", description="Geboorteland", examples=["NL", "B","D"])
    country_of_birth_father: Optional[str] = Field(default=None, max_length=3, alias="LwFa", description="Geboorteland vader", examples=["NL", "B","D"])
    country_of_birth_mother: Optional[str] = Field(default=None, max_length=3, alias="LwMo", description="Geboorteland moeder", examples=["NL", "B","D"])
    export_employee_to_time_registration: Optional[bool] = Field(default=None, alias="ExTm", description="Exporteren naar tijdregistratie", examples=[True, False])
    remarks: Optional[bytes] = Field(default=None, alias="Re", description="Opmerking")
    deviating_language_from_employer: Optional[str] = Field(default=None, alias="LgId", description="Taal verschilt van werkgever", examples=["NL", "B","D"])
    account_manager: Optional[str] = Field(default=None, alias="RlBh", max_length=15, description="Relatiebeheerder", examples=["1234567890", "9876543210", "1122334455"])
    start_phase: Optional[StartPhaseEnum] = Field(default=None, alias="StFs", description="Startfase", examples=[list(StartPhaseEnum)])
    start_phase_from: Optional[date] = Field(default=None, alias="BeSf", description="Begindatum startfase", examples=[date(2020, 1, 1), date(2021, 1, 30), date(2022, 4, 2)])
    date_last_worked: Optional[date] = Field(default=None, alias="DlWk", description="Datum laatst gewerkt", examples=[date(2020, 1, 1), date(2021, 1, 30), date(2022, 4, 2)])
    worked_weeks_employment_history: Optional[int] = Field(default=None, alias="WkWh", description="Gewerkte weken arbeidsverleden", examples=[1, 2, 3])
    calendar_weeks_phase_3_employment_history: Optional[int] = Field(default=None, alias="CF3h", description="Kalenderweken fase 3 arbeidsverleden", examples=[1, 2, 3])
    calendar_weeks_phase_b_employment_history: Optional[int] = Field(default=None, alias="CFBh", description="Kalenderweken fase B arbeidsverleden", examples=[1, 2, 3])
    num_phase_3_contracts_employment_history: Optional[int] = Field(default=None, alias="AF3h", description="Aantal fase 3 contracten arbeidsverleden", examples=[1, 2, 3])
    num_phase_b_contracts_employment_history: Optional[int] = Field(default=None, alias="AFBh", description="Aantal fase B contracten arbeidsverleden", examples=[1, 2, 3])
    payment_frequency: Optional[PaymentFrequencyEnum] = Field(default=None, alias="ViPa", description="Betalingsfrequentie", examples=[list(PaymentFrequencyEnum)])
    blocked_for_payment: Optional[bool] = Field(default=None, alias="BlPa", description="Geblokkeerd voor betaling", examples=[True, False])
    payslip_distribution: Optional[PayslipDistributionEnum] = Field(default=None, alias="PsPv", description="Verstrekking loonstrook", examples=[list(PayslipDistributionEnum)])
    annual_statement_distribution: Optional[AnnualStatementDistributionEnum] = Field(default=None, alias="YsPv", description="Verstrekking jaaropgave", examples=[list(AnnualStatementDistributionEnum)])
    email_for_digital_documents: Optional[EmailEnum] = Field(default=None, alias="EmAd", description="E-mail voor digitale documenten", examples=[EmailEnum.PRIVATE, EmailEnum.BUSINESS])
    secure_email_attachments: Optional[bool] = Field(default=None, alias="SeAt", description="E-mailbijlagen beveiligen", examples=[True, False])
    password: Optional[str] = Field(default=None, alias="PwEm", description="Wachtwoord", examples=["1234567890", "9876543210", "1122334455"], max_length=70)
    allow_sharing_private_email: Optional[bool] = Field(default=None, alias="EmUp", description="Mijn privé e-mailadres mag verstrekt worden", examples=[True, False])
    under_guardianship: Optional[bool] = Field(default=None, alias="BeVo", description="Bewindvoering", examples=[True, False])
    last_purchase_date_bicycle: Optional[date] = Field(default=None, alias="DlFi", description="Laatste aanschafdatum fiets", examples=[date(2020, 1, 1), date(2021, 1, 30), date(2022, 4, 2)])
    transitional_arrangement: Optional[TransitionEnum] = Field(default=None, alias="ViTr", description="Overgangsregeling 2022", examples=[list(TransitionEnum)])
    flex: Optional[bool] = Field(default=None, alias="Flex", description="Flex-medewerker", examples=[True, False])
    preferred_purchase_relation: Optional[str] = Field(default=None, alias="CrId", description="Voorkeur inkooprelatie", examples=["1234567890", "9876543210", "1122334455"], max_length=16)

class EmployeeUpdate(EmployeeBase):
    pass


class UploadConfig(BaseModel):
    """Shared configuration for nested AFAS payload models."""
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


class AfasOrgunitFunctionElement(UploadConfig):
    """Element for AfasOrgunitFunction."""
    start_date_attribute: Optional[date] = Field(alias="@DaBe", default=None)
    fields: FunctionCreate = Field(alias="Fields")
    objects: Optional[List[Any]] = Field(default=None, alias="Objects")


class AfasOrgunitFunctionObject(UploadConfig):
    element: Optional[List[AfasOrgunitFunctionElement]] = Field(default=None, alias="Element")


class AfasOrgunitFunctionSchema(UploadConfig):
    afas_orgunit_function: AfasOrgunitFunctionObject = Field(alias="AfasOrgunitFunction")


class AfasContractElement(UploadConfig):
    """Element for AfasContract."""
    action: Optional[Literal["insert", "update"]] = Field(default=None, alias="@Action", description="Action for this element")
    contract_start_date: Optional[date] = Field(alias="@DaBe", default=None)
    fields: ContractCreate = Field(alias="Fields")
    objects: Optional[List[Any]] = Field(default=None, alias="Objects")


class AfasContractObject(UploadConfig):
    element: Optional[List[AfasContractElement]] = Field(default=None, alias="Element")


class AfasContractSchema(UploadConfig):
    afas_contract: AfasContractObject = Field(alias="AfasContract")


class AfasWorkTimeElement(UploadConfig):
    worktime_start_date: Optional[date] = Field(alias="@DaBe", default=None)
    fields: WorkTimeCreate = Field(alias="Fields")


class AfasWorkTimeObject(UploadConfig):
    element: Optional[List[AfasWorkTimeElement]] = Field(default=None, alias="Element")


class AfasWorkTimeSchema(UploadConfig):
    afas_work_time: AfasWorkTimeObject = Field(alias="AfasWorkTime")


class AfasTimeTableElement(UploadConfig):
    timetable_start_date: Optional[date] = Field(alias="@DaBg", default=None)
    fields: TimeTableCreate = Field(alias="Fields")
    objects: Optional[List[AfasWorkTimeSchema]] = Field(default=None, alias="Objects")


class AfasTimeTableObject(UploadConfig):
    element: Optional[List[AfasTimeTableElement]] = Field(default=None, alias="Element")


class AfasTimeTableSchema(UploadConfig):
    afas_time_table: AfasTimeTableObject = Field(alias="AfasTimeTable")


class AfasSalaryAdditionElement(UploadConfig):
    fields: SalaryAdditionCreate = Field(alias="Fields")


class AfasSalaryAdditionObject(UploadConfig):
    element: Optional[List[AfasSalaryAdditionElement]] = Field(default=None, alias="Element")


class AfasSalaryAdditionSchema(UploadConfig):
    afas_salary_addition: AfasSalaryAdditionObject = Field(alias="AfasSalaryAddition")


class AfasSalaryElement(UploadConfig):
    salary_start_date: Optional[date] = Field(alias="@DaBe", default=None)
    fields: SalaryCreate = Field(alias="Fields")
    objects: Optional[List[AfasSalaryAdditionSchema]] = Field(default=None, alias="Objects")


class AfasSalaryObject(UploadConfig):
    element: Optional[List[AfasSalaryElement]] = Field(default=None, alias="Element")


class AfasSalarySchema(UploadConfig):
    afas_salary: AfasSalaryObject = Field(alias="AfasSalary")


class AfasAgencyFiscusElement(UploadConfig):
    start_date_attr: Optional[date] = Field(default=None, alias="@DaBe", description="Start date attribute")
    agency_id_attr: Optional[str] = Field(default=None, alias="@AyId", description="Agency ID attribute")
    action: Optional[Literal["insert", "update"]] = Field(default=None, alias="@Action", description="Action for this element")
    fields: AgencyFiscusCreate = Field(alias="Fields")


class AfasAgencyFiscusObject(UploadConfig):
    element: Optional[List[AfasAgencyFiscusElement]] = Field(default=None, alias="Element")


class AfasAgencyFiscusSchema(UploadConfig):
    afas_agency_fiscus: AfasAgencyFiscusObject = Field(alias="AfasAgencyFiscus")


class AfasEmployeeElement(UploadConfig):
    """Element representing the full AfasEmployee payload."""
    action: Optional[Literal["insert", "update"]] = Field(default=None, alias="@Action", description="Action for this element")
    employee_identifier: Optional[str] = Field(alias="@EmId", default=None)
    fields: EmployeeCreate = Field(alias="Fields")
    objects: Optional[List[Union[
        PersonPayload,
        AfasContractSchema,
        AfasOrgunitFunctionSchema,
        AfasTimeTableSchema,
        AfasSalarySchema,
        AfasAgencyFiscusSchema
    ]]] = Field(default=None, alias="Objects")


class AfasEmployeeObject(UploadConfig):
    element: AfasEmployeeElement = Field(alias="Element")


class AfasEmployeePayload(UploadConfig):
    afas_employee: AfasEmployeeObject = Field(alias="AfasEmployee")
