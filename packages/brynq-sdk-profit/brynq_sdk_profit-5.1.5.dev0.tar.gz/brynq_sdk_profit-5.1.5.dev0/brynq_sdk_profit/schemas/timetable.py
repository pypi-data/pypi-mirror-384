import pandas as pd
import pandera as pa
from pandera.typing import Series, DateTime
from typing import Optional
from datetime import date
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
# from .employee import EmployeeBase
from .enums import (
    RegularityCodeEnum, InvoluntaryPartTimeEnum, WorkScheduleCodeEnum,
    CDocumentsEnum, CAO42Enum, ShiftNightReductionEnum, WorkTimeReorganizationEnum,
    ScheduleTypeEnum, HoursPromisePeriodEnum
)


# class BaseTimetableSchema(EmployeeBase):
#     startdate: Series[DateTime] = pa.Field(coerce=True, nullable=False)
#     weekly_hours: Series[float] = pa.Field(coerce=True, nullable=False)
#     parttime_percentage: Series[float] = pa.Field(coerce=True, nullable=False)

#     class Config:
#         coerce = True
#         strict = False

class TimeTableCreate(BaseModel):
    """Pydantic schema for AfasTimeTable fields"""
    # --- General AFAS timetable fields ---
    guid: Optional[str] = Field(alias="GUID", description="GUID", default=None, max_length=38, examples=["00000000-0000-0000-0000-000000000000"])
    timetable_start_date: Optional[date] = Field(alias="DaBg", description="Begindatum rooster", default=None, examples=[date(2020, 1, 1)])
    service_number: Optional[int] = Field(alias="DvSn", description="Volgnummer dienstverband", default=None, examples=[1])
    standard_schedule: Optional[int] = Field(alias="SeNo", description="Standaardrooster", default=None, examples=[1])
    schedule_type: Optional[ScheduleTypeEnum] = Field(alias="EtTy", description="Type rooster", default=None, examples=[list(ScheduleTypeEnum)])
    suspension_hours_type: Optional[str] = Field(alias="StIn", description="Schorsing urensoort", default=None, max_length=5)
    deviation_hours_per_week_declaration: Optional[float] = Field(alias="DfHo", description="Afw. uren p.w. aangifte", default=None, examples=[1.0])
    variable_work_pattern: Optional[bool] = Field(alias="StPa", description="Wisselend arbeidspatroon", default=None, examples=[True, False])
    variable_work_pattern_with_schedule: Optional[bool] = Field(alias="Spec", description="Wisselend arbeidspatroon met werkrooster", default=None, examples=[True, False])
    flexible_working_hours: Optional[bool] = Field(alias="PtDu", description="Flexibele werktijden", default=None, examples=[True, False])
    days_per_week: Optional[float] = Field(alias="DyWk", description="Aantal dagen per week", default=None, examples=[1.0])
    hours_per_week: Optional[float] = Field(alias="HrWk", description="Aantal uren per week", default=None, examples=[1.0])
    leave_accrual_per_week: Optional[float] = Field(alias="AhWk", description="Verlofopbouw per week", default=None, examples=[1.0])
    part_time_percentage: Optional[float] = Field(alias="PcPt", description="Parttime (%)", default=None, examples=[1.0])
    five_sv_days: Optional[bool] = Field(alias="FtSv", description="5 SV-dagen", default=None, examples=[True, False])
    is_on_call_agreement: Optional[bool] = Field(alias="ClAg", description="Oproepovereenkomst", default=None, examples=[True, False])
    apply_min_max_contract_in_payroll: Optional[bool] = Field(alias="Immc", description="Min/max-contract toepassen in Payroll", default=None, examples=[True, False])
    hours_minimum_per_week: Optional[float] = Field(alias="HrMn", description="Minimum uren per week", default=None, examples=[1.0])
    hours_maximum_per_week: Optional[float] = Field(alias="HrMx", description="Maximum uren per week", default=None, examples=[1.0])
    has_annual_hours_norm: Optional[bool] = Field(alias="YrHr", description="Jaarurennorm", default=None, examples=[True, False])
    hours_minimum_per_period: Optional[float] = Field(alias="HrPm", description="Min. uren per periode", default=None, examples=[1.0])
    hours_promise_period: Optional[HoursPromisePeriodEnum] = Field(alias="HrPr", description="Urenbelofte", default=None, examples=[list(HoursPromisePeriodEnum)])
    fte_amount: Optional[float] = Field(alias="Ft", description="Aantal FTE", default=None, examples=[1.0])

    # --- weekly scheduling fields in hours/day ---
    start_time_sunday: Optional[str] = Field(alias="TbSu", description="Begintijd zondag", default=None)
    end_time_sunday: Optional[str] = Field(alias="TeSu", description="Eindtijd zondag", default=None)
    break_duration_sunday: Optional[str] = Field(alias="PsSu", description="Pauzeduur Zondag", default=None)
    start_time_monday: Optional[str] = Field(alias="TbMo", description="Begintijd maandag", default=None)
    end_time_monday: Optional[str] = Field(alias="TeMo", description="Eindtijd maandag", default=None)
    break_duration_monday: Optional[str] = Field(alias="PsMo", description="Pauzeduur Maandag", default=None)
    start_time_tuesday: Optional[str] = Field(alias="TbTu", description="Begintijd dinsdag", default=None)
    end_time_tuesday: Optional[str] = Field(alias="TeTu", description="Eindtijd dinsdag", default=None)
    break_duration_tuesday: Optional[str] = Field(alias="PsTu", description="Pauzeduur Dinsdag", default=None)
    start_time_wednesday: Optional[str] = Field(alias="TbWe", description="Begintijd woensdag", default=None)
    end_time_wednesday: Optional[str] = Field(alias="TeWe", description="Eindtijd woensdag", default=None)
    break_duration_wednesday: Optional[str] = Field(alias="PsWe", description="Pauzeduur Woensdag", default=None)
    start_time_thursday: Optional[str] = Field(alias="TbTh", description="Begintijd donderdag", default=None)
    end_time_thursday: Optional[str] = Field(alias="TeTh", description="Eindtijd donderdag", default=None)
    break_duration_thursday: Optional[str] = Field(alias="PsTh", description="Pauzeduur Donderdag", default=None)
    start_time_friday: Optional[str] = Field(alias="TbFr", description="Begintijd vrijdag", default=None)
    end_time_friday: Optional[str] = Field(alias="TeFr", description="Eindtijd vrijdag", default=None)
    break_duration_friday: Optional[str] = Field(alias="PsFr", description="Pauzeduur Vrijdag", default=None)
    start_time_saturday: Optional[str] = Field(alias="TbSa", description="Begintijd zaterdag", default=None)
    end_time_saturday: Optional[str] = Field(alias="TeSa", description="Eindtijd zaterdag", default=None)
    break_duration_saturday: Optional[str] = Field(alias="PsSa", description="Pauzeduur Zaterdag", default=None)
    hours_sunday: Optional[float] = Field(alias="HrSu", description="Uren Zondag", default=None, examples=[1.0])
    hours_monday: Optional[float] = Field(alias="HrMo", description="Uren Maandag", default=None, examples=[1.0])
    hours_tuesday: Optional[float] = Field(alias="HrTu", description="Uren Dinsdag", default=None, examples=[1.0])
    hours_wednesday: Optional[float] = Field(alias="HrWe", description="Uren Woensdag", default=None, examples=[1.0])
    hours_thursday: Optional[float] = Field(alias="HrTh", description="Uren Donderdag", default=None, examples=[1.0])
    hours_friday: Optional[float] = Field(alias="HrFr", description="Uren Vrijdag", default=None, examples=[1.0])
    hours_saturday: Optional[float] = Field(alias="HrSa", description="Uren Zaterdag", default=None, examples=[1.0])

    # --- Weekly availability percentages/ftes per day ---
    fte_sunday: Optional[float] = Field(alias="FtSu", description="FTE zondag", default=None, examples=[1.0])
    fte_monday: Optional[float] = Field(alias="FtMo", description="FTE maandag", default=None, examples=[1.0])
    fte_tuesday: Optional[float] = Field(alias="FtTu", description="FTE dinsdag", default=None, examples=[1.0])
    fte_wednesday: Optional[float] = Field(alias="FtWe", description="FTE woensdag", default=None, examples=[1.0])
    fte_thursday: Optional[float] = Field(alias="FtTh", description="FTE donderdag", default=None, examples=[1.0])
    fte_friday: Optional[float] = Field(alias="FtFr", description="FTE vrijdag", default=None, examples=[1.0])
    fte_saturday: Optional[float] = Field(alias="FtSa", description="FTE zaterdag", default=None, examples=[1.0])
    fte_bapo: Optional[float] = Field(alias="FtBp", description="BAPO FTE", default=None, examples=[1.0])
    fte_save_bapo: Optional[float] = Field(alias="FtSb", description="Spaar BAPO FTE", default=None, examples=[1.0])
    remuneration_percentage: Optional[float] = Field(alias="ReRa", description="Bezoldigingspercentage", default=None, examples=[1.0])
    work_time_reorganization: Optional[WorkTimeReorganizationEnum] = Field(alias="ReWt", description="Reorganisatie arbeidstijd", default=None, examples=[list(WorkTimeReorganizationEnum)])

    # --- weekly availability flags ---
    is_workday_sunday: Optional[bool] = Field(alias="WdSu", description="Zondag werkdag", default=None, examples=[True, False])
    is_workday_monday: Optional[bool] = Field(alias="WdMo", description="Maandag werkdag", default=None, examples=[True, False])
    is_workday_tuesday: Optional[bool] = Field(alias="WdTu", description="Dinsdag werkdag", default=None, examples=[True, False])
    is_workday_wednesday: Optional[bool] = Field(alias="WdWe", description="Woensdag werkdag", default=None, examples=[True, False])
    is_workday_thursday: Optional[bool] = Field(alias="WdTh", description="Donderdag werkdag", default=None, examples=[True, False])
    is_workday_friday: Optional[bool] = Field(alias="WdFr", description="Vrijdag werkdag", default=None, examples=[True, False])
    is_workday_saturday: Optional[bool] = Field(alias="WdSa", description="Zaterdag werkdag", default=None, examples=[True, False])
    is_irregular_employment: Optional[bool] = Field(alias="IrEm", description="Onregelmatige tewerkstelling", default=None, examples=[True, False])
    involuntary_part_time: Optional[InvoluntaryPartTimeEnum] = Field(alias="InPt", description="Onvrijwillig deeltijds", default=None, examples=[list(InvoluntaryPartTimeEnum)])
    # --- weekly schedule codes (belgian?) ---
    work_schedule_code: Optional[WorkScheduleCodeEnum] = Field(alias="CoWo", description="Code werkschema", default=None, examples=[list(WorkScheduleCodeEnum)])
    c_documents: Optional[CDocumentsEnum] = Field(alias="CDoc", description="C-Documenten", default=None, examples=[list(CDocumentsEnum)])
    cao_42: Optional[CAO42Enum] = Field(alias="Cl42", description="CAO 42", default=None, examples=[list(CAO42Enum)])
    shift_night_reduction: Optional[ShiftNightReductionEnum] = Field(alias="ShRe", description="Ploeg/nachtvermindering", default=None, examples=[list(ShiftNightReductionEnum)])
    work_redistribution_numerator: Optional[float] = Field(alias="WrNu", description="Teller progr. werkherv.", default=None, examples=[1.0])
    work_redistribution_denominator: Optional[float] = Field(alias="WrDe", description="Noemer progr. werkherv.", default=None, examples=[1.0])
    work_redistribution_system: Optional[float] = Field(alias="WrRe", description="Stelsel bij progr. werkherv.", default=None, examples=[1.0])
    regularity_code: Optional[RegularityCodeEnum] = Field(alias="ReCo", description="Regelmaatcode", default=None, examples=[list(RegularityCodeEnum)])

    # --- parental leave fields ---
    parental_leave_child_sequence: Optional[int] = Field(alias="PlaFaSn", description="Kind", default=None, examples=[1])
    parental_leave_hours_per_week: Optional[float] = Field(alias="PlaPhWk", description="Uren ouderschapsverlof per week", default=None, examples=[1.0])
    parental_leave_form_type: Optional[str] = Field(alias="PlaViTy", description="Ouderschapsverlof vorm (BE)", default=None, max_length=10)
    parental_leave_number_of_blocks: Optional[int] = Field(alias="PlaAmBl", description="Aantal blokken (BE)", default=None, examples=[1])
    parental_leave_distribution_type: Optional[str] = Field(alias="PlaVaDl", description="Type verdeling uren ouderschapsverlof", default=None, max_length=10)
    parental_leave_paid_percentage: Optional[float] = Field(alias="PlaPerc", description="Percentage betaald ouderschapsverlof", default=None, examples=[1.0])
    parental_leave_planned_end_date: Optional[date] = Field(alias="PlaPlDe", description="Geplande einddatum ouderschapsverlof", default=None, examples=[date(2020, 1, 1)])
    parental_hours_monday: Optional[float] = Field(alias="PhMo", description="Uren ouderschapsverlof maandag", default=None, examples=[1.0])
    parental_hours_tuesday: Optional[float] = Field(alias="PhTu", description="Uren ouderschapsverlof dinsdag", default=None, examples=[1.0])
    parental_hours_wednesday: Optional[float] = Field(alias="PhWe", description="Uren ouderschapsverlof woensdag", default=None, examples=[1.0])
    parental_hours_thursday: Optional[float] = Field(alias="PhTh", description="Uren ouderschapsverlof donderdag", default=None, examples=[1.0])
    parental_hours_friday: Optional[float] = Field(alias="PhFr", description="Uren ouderschapsverlof vrijdag", default=None, examples=[1.0])
    parental_hours_saturday: Optional[float] = Field(alias="PhSa", description="Uren ouderschapsverlof zaterdag", default=None, examples=[1.0])
    parental_hours_sunday: Optional[float] = Field(alias="PhSu", description="Uren ouderschapsverlof zondag", default=None, examples=[1.0])
    parental_fte_monday: Optional[float] = Field(alias="PfMo", description="FTE ouderschapsverlof maandag", default=None, examples=[1.0])
    parental_fte_tuesday: Optional[float] = Field(alias="PfTu", description="FTE ouderschapsverlof dinsdag", default=None, examples=[1.0])
    parental_fte_wednesday: Optional[float] = Field(alias="PfWe", description="FTE ouderschapsverlof woensdag", default=None, examples=[1.0])
    parental_fte_thursday: Optional[float] = Field(alias="PfTh", description="FTE ouderschapsverlof donderdag", default=None, examples=[1.0])
    parental_fte_friday: Optional[float] = Field(alias="PfFr", description="FTE ouderschapsverlof vrijdag", default=None, examples=[1.0])
    parental_fte_saturday: Optional[float] = Field(alias="PfSa", description="FTE ouderschapsverlof zaterdag", default=None, examples=[1.0])
    parental_fte_sunday: Optional[float] = Field(alias="PfSu", description="FTE ouderschapsverlof zondag", default=None, examples=[1.0])

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


class WorkTimeCreate(BaseModel):
    """Pydantic schema for AfasWorkTime fields"""
    # --- General AFAS worktime fields ---
    work_schedule_start_date: Optional[date] = Field(alias="DaBe", description="Begindatum werkrooster", default=None, examples=[date(2020, 1, 1)])
    schedule_cycle: Optional[int] = Field(alias="Twcy", description="Roostercyclus", default=None, examples=[1])
    start_with_week_schedule: Optional[int] = Field(alias="Twcp", description="Begin met weekrooster", default=None, examples=[1])
    sequence_number: Optional[int] = Field(alias="Twcc", description="Volgnummer", default=None, examples=[1])

    # --- Belgian-specific worktime fields ---

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
