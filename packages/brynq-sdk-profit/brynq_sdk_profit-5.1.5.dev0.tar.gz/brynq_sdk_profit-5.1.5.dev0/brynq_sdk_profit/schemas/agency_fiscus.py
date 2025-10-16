from typing import Optional
from datetime import date

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from .enums import (
    IncomeRelationTypeEnum, EmploymentRelationTypeEnum, TableColorEnum,
    TableCodeEnum, WageTaxCreditEnum, HealthInsuranceEnum, SectorRiskGroupCAOEnum,
    SeniorDiscountEnum, PremiumDiscountEnum, VacationVouchersEnum,
    NoCarAdditionReasonEnum, DayTableApplicationEnum
)


class AgencyFiscusCreate(BaseModel):
    """Pydantic schema for AfasAgencyFiscus fields"""
    # --- General AFAS agency fiscus fields ---
    start_date: Optional[date] = Field(alias="DaBe", description="Begindatum", default=None, examples=[date(2020, 1, 1)])
    agency_id: Optional[str] = Field(alias="AyId", description="Instantie", default=None, max_length=15)
    end_date: Optional[date] = Field(alias="DaEn", description="Einddatum", default=None, examples=[date(2020, 12, 31)])
    income_relation_type: Optional[IncomeRelationTypeEnum] = Field(alias="ViIn", description="Soort inkomstenverhouding", default=None, examples=[list(IncomeRelationTypeEnum)])
    employment_relation_type: Optional[EmploymentRelationTypeEnum] = Field(alias="ViEm", description="Aard arbeidsverhouding", default=None, examples=[list(EmploymentRelationTypeEnum)])
    tax_table_color: Optional[TableColorEnum] = Field(alias="ViTs", description="Tabelkleur", default=None, examples=[list(TableColorEnum)])
    tax_table_code: Optional[TableCodeEnum] = Field(alias="ViCd", description="Tabelcode", default=None, examples=[list(TableCodeEnum)])
    wage_tax_credit: Optional[WageTaxCreditEnum] = Field(alias="ViLk", description="Loonheffingskorting", default=None, examples=[list(WageTaxCreditEnum)])
    health_insurance: Optional[HealthInsuranceEnum] = Field(alias="ViZv", description="Zvw", default=None, examples=[list(HealthInsuranceEnum)])
    is_zw_insured: Optional[bool] = Field(alias="YnZW", description="ZW", default=None, examples=[True, False])
    is_ww_insured: Optional[bool] = Field(alias="YnWW", description="WW", default=None, examples=[True, False])
    is_wao_wia_insured: Optional[bool] = Field(alias="YWAO", description="WAO/WIA", default=None, examples=[True, False])
    is_ufo: Optional[bool] = Field(alias="DoPs", description="UFO", default=None, examples=[True, False])
    sector_risk_group: Optional[SectorRiskGroupCAOEnum] = Field(alias="ViRi", description="Afwijkende sector risicogroep", default=None, examples=[list(SectorRiskGroupCAOEnum)])
    cbs_cao_code: Optional[SectorRiskGroupCAOEnum] = Field(alias="ViFc", description="Afwijkende CBS cao", default=None, examples=[list(SectorRiskGroupCAOEnum)])
    senior_discount: Optional[SeniorDiscountEnum] = Field(alias="ViOk", description="Alleenstaande ouderenkorting", default=None, examples=[list(SeniorDiscountEnum)])
    premium_discount: Optional[PremiumDiscountEnum] = Field(alias="ViHa", description="Premiekorting", default=None, examples=[list(PremiumDiscountEnum)])
    vacation_vouchers: Optional[VacationVouchersEnum] = Field(alias="ViVb", description="Vakantiebonnen", default=None, examples=[list(VacationVouchersEnum)])
    no_car_addition_reason: Optional[NoCarAdditionReasonEnum] = Field(alias="ViCx", description="Reden geen bijtelling auto", default=None, examples=[list(NoCarAdditionReasonEnum)])

    # --- Dutch payroll taxation specifics ---
    student_regulation: Optional[bool] = Field(alias="TxF4", description="Studenten- en scholierenregeling", default=None, examples=[True, False])
    transport_by_employer: Optional[bool] = Field(alias="TrI", description="Vervoer vanwege inhoudingsplichtige", default=None, examples=[True, False])
    employee_loan: Optional[bool] = Field(alias="Loan", description="Personeelslening (rente/kosten geen loon)", default=None, examples=[True, False])
    self_employed_bargeman: Optional[bool] = Field(alias="TxIs", description="Zelfstandige binnenschipper", default=None, examples=[True, False])
    domestic_staff_children: Optional[bool] = Field(alias="TxHc", description="Huispersoneel en/of meewerkende kinderen", default=None, examples=[True, False])
    no_authority_family: Optional[bool] = Field(alias="TxGf", description="Geen gezagsverhouding met familie van eigenaar", default=None, examples=[True, False])
    no_authority_previous_owner: Optional[bool] = Field(alias="TxGo", description="Geen gezagsverhouding met vorige eigenaar", default=None, examples=[True, False])
    director_shareholder: Optional[bool] = Field(alias="TxCs", description="Directeur/grootaandeelhouder", default=None, examples=[True, False])
    on_call_no_obligation: Optional[bool] = Field(alias="TxGy", description="Oproep-/invalkracht zonder verplichting", default=None, examples=[True, False])
    on_call_with_obligation: Optional[bool] = Field(alias="TxGn", description="Oproep-/invalkracht met verplichting", default=None, examples=[True, False])
    aow_benefit_single: Optional[bool] = Field(alias="TxAo", description="AOW-uitkering voor alleenstaanden", default=None, examples=[True, False])
    wajong_benefit: Optional[bool] = Field(alias="TxF5", description="Wajong-uitkering", default=None, examples=[True, False])
    continued_payment_provider: Optional[bool] = Field(alias="Dblr", description="Doorbetaler i.v.m. doorbetaaldloonregeling", default=None, examples=[True, False])
    senior_exemption: Optional[bool] = Field(alias="OuVr", description="Ouderenvrijstelling", default=None, examples=[True, False])
    conscientious_objection: Optional[bool] = Field(alias="Cons", description="Gemoedsbezwaard", default=None, examples=[True, False])
    marginal_work_exemption: Optional[bool] = Field(alias="PMA", description="Premievrijstelling marginale arbeid", default=None, examples=[True, False])
    no_risk_insurance_policy: Optional[bool] = Field(alias="NRsk", description="No-riskpolis", default=None, examples=[True, False])
    wage_cost_disabled_worker: Optional[bool] = Field(alias="PiAw", description="LKV arbeidsgehandicapte werknemer", default=None, examples=[True, False])
    wage_cost_job_agreement: Optional[bool] = Field(alias="PkBa", description="LKV banenafspraak / scholingsbelemmerden", default=None, examples=[True, False])
    wage_cost_replaced_disabled: Optional[bool] = Field(alias="PkHa", description="LKV herplaatsen arbeidsgehandicapte werknemer", default=None, examples=[True, False])
    foreign_withholding_tax: Optional[bool] = Field(alias="PkBc", description="Bronheffing buitenland", default=None, examples=[True, False])
    wage_cost_benefit_end_date: Optional[date] = Field(alias="DaEk", description="Einddatum loonkostenvoordeel", default=None, examples=[date(2021, 12, 31)])
    lkv_senior: Optional[bool] = Field(alias="Lkvo", description="LKV oudere werknemer", default=None, examples=[True, False])
    ww_revised: Optional[bool] = Field(alias="WWHe", description="WW herzien", default=None, examples=[True, False])
    cao_code_hirer: Optional[SectorRiskGroupCAOEnum] = Field(alias="CAHi", description="Cao-code inlener", default=None, examples=[list(SectorRiskGroupCAOEnum)])

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
