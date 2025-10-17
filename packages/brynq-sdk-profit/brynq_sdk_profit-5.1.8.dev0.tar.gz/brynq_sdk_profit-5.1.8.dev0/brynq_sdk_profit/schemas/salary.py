import pandas as pd
import pandera as pa
from pandera.typing import Series, DateTime
from pydantic import BaseModel, Field, field_validator
from pydantic.config import ConfigDict
from typing import Optional
from datetime import datetime, date
import math
from .enums import (
    SalaryTypeEnum, SalaryScaleEnum, SalaryScaleTypeEnum, PartenaReasonEnum,
    StockOptionsCodeEnum, RemunerationMethodEnum, HealthcareSalaryIncreaseReasonEnum,
    ReplacementReasonEnum, SocialMaribelTypeEnum, BBTBBKEnum, Choice45YearEnum,
    Choice50YearEnum, Choice52YearEnum, Choice55YearEnum, LocationFunctionAllowanceEnum,
    ProrataTheoreticalHourlyWageEnum, ProrataLocationEnum, ProrataAllowancesEnum,
    HistoricSalaryScaleEnum
)

class BaseSalarySchema(pa.DataFrameModel):
    """Base schema for salary-related operations in Pandera DataFrame format.

    This schema defines the minimum required fields for any salary operation.
    Use this as a base class for other salary-related DataFrame schemas.
    """
    startdate_salary: Series[DateTime] = pa.Field(coerce=True, nullable=False)
    employee_id: Series[str] = pa.Field(coerce=True, nullable=False)
    salary_type: Series[str] = pa.Field(coerce=True, nullable=False)

class SalaryGetSchema(pa.DataFrameModel):
    """Schema for retrieving salary information in DataFrame format.

    This schema defines the structure for salary data retrieval operations,
    including both employee and employer information along with salary details.
    """
    salary_id: Series[str] = pa.Field(coerce=True)
    type_of_salary: Series[str] = pa.Field(coerce=True)
    employer_id: Series[str] = pa.Field(coerce=True)
    employee_id: Series[str] = pa.Field(coerce=True)
    name: Series[str] = pa.Field(coerce=True)
    start_date: Series[DateTime] = pa.Field(coerce=True)
    salary: Series[int] = pa.Field(coerce=True)
    employer_name: Series[str] = pa.Field(coerce=True)

    class Config:
        coerce = True
        strict = True

class SalaryCreate(BaseModel):
    """Pydantic schema for AfasSalary fields"""
    # --- General AFAS salary fields ---
    guid: Optional[str] = Field(alias="GUID", description="GUID", default=None, max_length=38, examples=["00000000-0000-0000-0000-000000000000"])
    salary_start_date: Optional[date] = Field(alias="DaBe", description="Begindatum salaris", default=None, examples=[date(2020, 1, 1)])
    service_number: Optional[int] = Field(alias="DvSn", description="Volgnummer dienstverband", default=None, examples=[1])
    step: Optional[float] = Field(alias="SaSt", description="Trede", default=None, examples=[1.0])
    salary_end_step: Optional[float] = Field(alias="SaS2", description="Eindtrede", default=None, examples=[1.0])
    type_of_salary: Optional[SalaryTypeEnum] = Field(alias="SaPe", description="Soort salaris", default=None, examples=[list(SalaryTypeEnum)])
    salary_amount: Optional[float] = Field(alias="EmSa", description="Salaris", default=None, examples=[1.0])
    allowance_in_percentage: Optional[bool] = Field(alias="SaPr", description="Toeslag in procenten", default=None, examples=[True, False])
    pension_number: Optional[str] = Field(alias="SaNr", description="Pensioennummer", default=None, max_length=15)
    is_net_salary: Optional[bool] = Field(alias="NtSa", description="Netto salaris", default=None, examples=[True, False])
    period_table: Optional[int] = Field(alias="PtId", description="Periodetabel", default=None, examples=[1])
    annual_salary_bt: Optional[float] = Field(alias="SaYe", description="Jaarloon BT", default=None, examples=[1.0])
    allowance_amount: Optional[float] = Field(alias="EmSc", description="Toeslag", default=None, examples=[1.0])
    salary_scale_type: Optional[int] = Field(alias="TaId", description="Soort loonschaal", default=None, examples=[1])
    wage_scale: Optional[SalaryScaleEnum] = Field(alias="VaSc", description="Loonschaal", default=None, examples=[list(SalaryScaleEnum)])
    apply_timetable: Optional[bool] = Field(alias="TtPy", description="Rooster toepassen in Payroll", default=None, examples=[True, False])
    function_scale_type_id: Optional[int] = Field(alias="FuTa", description="Soort functieschaal", default=None, examples=[1])
    function_scale: Optional[SalaryScaleEnum] = Field(alias="FuSc", description="Functieschaal", default=None, examples=[list(SalaryScaleEnum)])

    # --- Belgian-specific salary extensions ---
    rsp: Optional[float] = Field(alias="Rsp", description="RSP", default=None, examples=[1.0])
    apply_salary_scale: Optional[bool] = Field(alias="ApSc", description="Barema toepassen", default=None, examples=[True, False])
    salary_scale_type_id: Optional[int] = Field(alias="ScTy", description="Loonschaal type", default=None, examples=[1])
    salary_scale_category: Optional[SalaryScaleTypeEnum] = Field(alias="AcLs", description="Type loonschaal", default=None, examples=[list(SalaryScaleTypeEnum)])
    partena_reason: Optional[PartenaReasonEnum] = Field(alias="PaRe", description="Reden Partena", default=None, examples=[list(PartenaReasonEnum)])
    partena_comment: Optional[str] = Field(alias="PaCp", description="Commentaar Partena", default=None, max_length=100)
    flexi_job_amount: Optional[float] = Field(alias="PaBf", description="Bedrag flexjob", default=None, examples=[1.0])
    soft_landing_premium: Optional[bool] = Field(alias="PaZl", description="Premie zachte landingsbaan", default=None, examples=[True, False])
    salary_scale_code: Optional[str] = Field(alias="ScCo", description="Loonschaal code", default=None, max_length=9)
    stock_options_code: Optional[StockOptionsCodeEnum] = Field(alias="Z70", description="Code % van opties", default=None, examples=[list(StockOptionsCodeEnum)])
    stock_options_percentage: Optional[float] = Field(alias="Z71", description="% van opties op aandelen", default=None, examples=[1.0])

    model_config = ConfigDict(
        serialize_by_alias=True,
        str_strip_whitespace=True,
        str_min_length=0,
        str_max_length=255,
        coerce_numbers_to_str=False,
        extra="forbid",
        frozen=True,
        allow_inf_nan=False,
        ser_json_timedelta="iso8601",
        ser_json_bytes="base64",
        validate_default=True,
        use_enum_values=True,
        validate_by_name=True,
        validate_by_alias=True,
    )

class SalaryUpdate(SalaryCreate):
    pass

class SalaryAdditionCreate(BaseModel):
    """Pydantic schema for AfasSalaryAddition fields"""
    # --- General salary addition fields ---
    alternative_hourly_wage_1: Optional[float] = Field(alias="AHw1", description="Alternatief uurloon 1", default=None, examples=[1.0])
    alternative_hourly_wage_2: Optional[float] = Field(alias="AHw2", description="Alternatief uurloon 2", default=None, examples=[1.0])
    alternative_hourly_wage_3: Optional[float] = Field(alias="AHw3", description="Alternatief uurloon 3", default=None, examples=[1.0])
    alternative_hourly_wage_4: Optional[float] = Field(alias="AHw4", description="Alternatief uurloon 4", default=None, examples=[1.0])
    salary_scale_gross_wage: Optional[float] = Field(alias="BaPw", description="Barema brutoloon", default=None, examples=[1.0])
    salary_scale_daily_wage: Optional[float] = Field(alias="BaDw", description="Barema dagloon", default=None, examples=[1.0])
    salary_scale_hourly_wage: Optional[float] = Field(alias="BaHw", description="Barema uurloon", default=None, examples=[1.0])
    remuneration_method: Optional[RemunerationMethodEnum] = Field(alias="RmWy", description="Bezoldigingswijze", default=None, examples=[list(RemunerationMethodEnum)])
    daily_wage: Optional[float] = Field(alias="DaWa", description="Dagloon", default=None, examples=[1.0])
    wage_category: Optional[str] = Field(alias="WaCa", description="Looncategorie", default=None, max_length=20)
    salary_increase_reason: Optional[str] = Field(alias="WrRe", description="Reden loonsverhoging", default=None, max_length=20)
    healthcare_salary_increase_reason: Optional[HealthcareSalaryIncreaseReasonEnum] = Field(alias="WrRH", description="Reden loonsverhoging (zorg)", default=None, examples=[list(HealthcareSalaryIncreaseReasonEnum)])
    sub_wage_category: Optional[str] = Field(alias="SwCa", description="Sublooncategorie", default=None, max_length=20)
    allowance_1: Optional[float] = Field(alias="Add1", description="Toeslag 1", default=None, examples=[1.0])
    allowance_2: Optional[float] = Field(alias="Add2", description="Toeslag 2", default=None, examples=[1.0])
    allowance_3: Optional[float] = Field(alias="Add3", description="Toeslag 3", default=None, examples=[1.0])
    advance_percentage: Optional[int] = Field(alias="AdPc", description="Voorschot percentage", default=None, examples=[1])
    advance_hours: Optional[float] = Field(alias="AdHo", description="Voorschot uren", default=None, examples=[1.0])
    advance_fixed_amount: Optional[float] = Field(alias="AdAm", description="Voorschot vast bedrag", default=None, examples=[1.0])
    historic_salary_scale: Optional[HistoricSalaryScaleEnum] = Field(alias="HiBa", description="Hist. barema-aanduiding", default=None, examples=[list(HistoricSalaryScaleEnum)])
    historic_salary_scale_date: Optional[date] = Field(alias="HiBd", description="Hist. barema-datum", default=None, examples=[date(2020, 1, 1)])
    location_function_allowance: Optional[LocationFunctionAllowanceEnum] = Field(alias="LoFu", description="Standplaats functie", default=None, examples=[list(LocationFunctionAllowanceEnum)])
    salary_category: Optional[str] = Field(alias="SaCa", description="Categorie", default=None, max_length=20)
    salary_scale_seniority: Optional[str] = Field(alias="BaAn", description="Barema anciënniteit", default=None, max_length=10)
    actual_seniority: Optional[str] = Field(alias="TrAn", description="Werkelijke anciënniteit", default=None, max_length=6)
    amount_hsf: Optional[float] = Field(alias="AHSF", description="Bedrag H/S/F", default=None, examples=[1.0])
    function_complement_amount: Optional[float] = Field(alias="AmFc", description="Bedrag functiecompl.", default=None, examples=[1.0])
    prorata_theoretical_hourly_wage: Optional[ProrataTheoreticalHourlyWageEnum] = Field(alias="PrHw", description="Prorata theor. uurloon", default=None, examples=[list(ProrataTheoreticalHourlyWageEnum)])
    prorata_location: Optional[ProrataLocationEnum] = Field(alias="PrLc", description="Prorata standplaats", default=None, examples=[list(ProrataLocationEnum)])
    prorata_allowances: Optional[ProrataAllowancesEnum] = Field(alias="PrAd", description="Prorata-toeslagen", default=None, examples=[list(ProrataAllowancesEnum)])

    # --- Replacement scheduling fields ---
    replacement_employee_1: Optional[str] = Field(alias="Rpl1", description="Vervanger 1", default=None, max_length=50)
    replacement_name_1: Optional[str] = Field(alias="RpN1", description="Naam vervanger 1", default=None, max_length=255)
    replacement_insz_1: Optional[str] = Field(alias="RIn1", description="INSZ-nummer 1", default=None, max_length=12)
    replacement_hours_per_week_1: Optional[float] = Field(alias="RHw1", description="Uren per week 1", default=None, examples=[1.0])
    replacement_reason_1: Optional[ReplacementReasonEnum] = Field(alias="RRe1", description="Reden vervanging 1", default=None, examples=[list(ReplacementReasonEnum)])
    replacement_employee_2: Optional[str] = Field(alias="Rpl2", description="Vervanger 2", default=None, max_length=50)
    replacement_name_2: Optional[str] = Field(alias="RpN2", description="Naam vervanger 2", default=None, max_length=255)
    replacement_insz_2: Optional[str] = Field(alias="RIn2", description="INSZ-nummer 2", default=None, max_length=12)
    replacement_hours_per_week_2: Optional[float] = Field(alias="RHw2", description="Uren per week 2", default=None, examples=[1.0])
    replacement_reason_2: Optional[ReplacementReasonEnum] = Field(alias="RRe2", description="Reden vervanging 2", default=None, examples=[list(ReplacementReasonEnum)])
    replacement_employee_3: Optional[str] = Field(alias="Rpl3", description="Vervanger 3", default=None, max_length=50)
    replacement_name_3: Optional[str] = Field(alias="RpN3", description="Naam vervanger 3", default=None, max_length=255)
    replacement_insz_3: Optional[str] = Field(alias="RIn3", description="INSZ-nummer 3", default=None, max_length=12)
    replacement_hours_per_week_3: Optional[float] = Field(alias="RHw3", description="Uren per week 3", default=None, examples=[1.0])
    replacement_reason_3: Optional[ReplacementReasonEnum] = Field(alias="RRe3", description="Reden vervanging 3", default=None, examples=[list(ReplacementReasonEnum)])
    replacement_employee_4: Optional[str] = Field(alias="Rpl4", description="Vervanger 4", default=None, max_length=50)
    replacement_name_4: Optional[str] = Field(alias="RpN4", description="Naam vervanger 4", default=None, max_length=255)
    replacement_insz_4: Optional[str] = Field(alias="RIn4", description="INSZ-nummer 4", default=None, max_length=12)
    replacement_hours_per_week_4: Optional[float] = Field(alias="RHw4", description="Uren per week 4", default=None, examples=[1.0])
    replacement_reason_4: Optional[ReplacementReasonEnum] = Field(alias="RRe4", description="Reden vervanging 4", default=None, examples=[list(ReplacementReasonEnum)])
    replacement_employee_5: Optional[str] = Field(alias="Rpl5", description="Vervanger 5", default=None, max_length=50)
    replacement_name_5: Optional[str] = Field(alias="RpN5", description="Naam vervanger 5", default=None, max_length=255)
    replacement_insz_5: Optional[str] = Field(alias="RIn5", description="INSZ-nummer 5", default=None, max_length=12)
    replacement_hours_per_week_5: Optional[float] = Field(alias="RHw5", description="Uren per week 5", default=None, examples=[1.0])
    replacement_reason_5: Optional[ReplacementReasonEnum] = Field(alias="RRe5", description="Reden vervanging 5", default=None, examples=[list(ReplacementReasonEnum)])

    # --- Belgian-specific salary addition fields ---
    social_maribel_type: Optional[SocialMaribelTypeEnum] = Field(alias="SoMa", description="Soc. Maribel type", default=None, examples=[list(SocialMaribelTypeEnum)])
    social_maribel_percentage: Optional[float] = Field(alias="SmPe", description="Soc. Maribel percentage", default=None, examples=[1.0])
    special_professional_title: Optional[BBTBBKEnum] = Field(alias="BtBk", description="BBT/BBK", default=None, examples=[list(BBTBBKEnum)])
    cao_45_premium_percentage: Optional[float] = Field(alias="AD45", description="% Premie ADV CAO 45+", default=None, examples=[1.0])
    choice_45_year: Optional[Choice45YearEnum] = Field(alias="AC45", description="Keuze 45 jaar", default=None, examples=[list(Choice45YearEnum)])
    choice_50_year: Optional[Choice50YearEnum] = Field(alias="AC50", description="Keuze 50 jaar", default=None, examples=[list(Choice50YearEnum)])
    choice_52_year: Optional[Choice52YearEnum] = Field(alias="AC52", description="Keuze 52 jaar", default=None, examples=[list(Choice52YearEnum)])
    choice_55_year: Optional[Choice55YearEnum] = Field(alias="AC55", description="Keuze 55 jaar", default=None, examples=[list(Choice55YearEnum)])
    eq: Optional[bool] = Field(alias="Eq", description="Gelijkgestelde", default=None, examples=[True, False])
    of: Optional[bool] = Field(alias="Of", description="Ambtshalve", default=None, examples=[True, False])
    no_fu: Optional[bool] = Field(alias="NoFu", description="Geen financiering", default=None, examples=[True, False])
    dc_hw: Optional[int] = Field(alias="DcHw", description="Aantal bij uurloon", default=None, examples=[1])
    dc_pw: Optional[int] = Field(alias="DcPw", description="Aantal bij periodeloon", default=None, examples=[1])
    dc_dw: Optional[int] = Field(alias="DcDw", description="Aantal bij dagloon", default=None, examples=[1])

    model_config = ConfigDict(
        serialize_by_alias=True,
        str_strip_whitespace=True,
        str_min_length=0,
        str_max_length=255,
        coerce_numbers_to_str=False,
        extra="forbid",
        frozen=True,
        allow_inf_nan=False,
        ser_json_timedelta="iso8601",
        ser_json_bytes="base64",
        validate_default=True,
        use_enum_values=True,
        validate_by_name=True,
        validate_by_alias=True,
    )
