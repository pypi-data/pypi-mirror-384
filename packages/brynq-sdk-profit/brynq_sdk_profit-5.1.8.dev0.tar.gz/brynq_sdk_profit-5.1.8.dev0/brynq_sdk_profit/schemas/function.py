import pandera as pa
from pandera.typing import Series
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from datetime import datetime, date
from typing import Optional
from .enums import (
    SocialSecurityBenefitEnum, StatuutEnum, SpecificFunctionTypeEnum,
    FunctionTitleEnum, DisabilityRiskGroupEnum, APEPlanEnum, FunctionLevelEnum,
    PensionInsuranceProviderEnum, ResearchTypeEnum, HealthcareGradeFunctionEnum,
    HealthcarePersonnelCategoryEnum, HealthcareFunctionEnum, HealthcareQualificationEnum,
    PersonnelCategoryType1Enum, PersonnelType2Enum, CommunityEnum, RegionEnum
)

class FunctionCreate(BaseModel):
    """Pydantic schema for AfasOrgunitFunction fields"""
    # --- General AFAS orgunit function fields ---
    guid: Optional[str] = Field(alias="GUID", description="GUID", default=None, max_length=38, examples=["00000000-0000-0000-0000-000000000000"])
    start_date_job: Optional[date] = Field(alias="DaBe", description="Begindatum functie", default=None, examples=[date(2020, 1, 1)])
    organisational_unit: Optional[str] = Field(alias="DpId", description="Organisatorische eenheid", default=None, max_length=10)
    function_id: Optional[str] = Field(alias="FuId", description="Functie", default=None, max_length=10)
    cost_carrier: Optional[str] = Field(alias="CcId", description="Kostendrager", default=None, max_length=30)
    cost_center: Optional[str] = Field(alias="CrId", description="Kostenplaats", default=None, max_length=30)
    project: Optional[str] = Field(alias="PjId", description="Project", default=None, max_length=15)
    team_member_profile: Optional[int] = Field(alias="TmPr", description="Teamlid profiel", default=None, examples=[1])
    service_number: Optional[int] = Field(alias="DvSn", description="Volgnummer dienstverband", default=None, examples=[1])
    formation_place: Optional[str] = Field(alias="FpId", description="Formatieplaats", default=None, max_length=15)
    educational_institution: Optional[str] = Field(alias="EIId", description="Onderwijsinstelling", default=None, max_length=15)
    higher_education_function: Optional[bool] = Field(alias="BFun", description="Bovenschoolse functie", default=None, examples=[True, False])
    research_percentage: Optional[int] = Field(alias="RePe", description="Percentage onderzoek", default=None, examples=[1])

    # --- Belgian-specific orgunit extensions? ---
    social_security_benefit: Optional[SocialSecurityBenefitEnum] = Field(alias="SoSe", description="Sociale voorziening", default=None, examples=[list(SocialSecurityBenefitEnum)])
    activity: Optional[str] = Field(alias="PaAc", description="Activiteit", default=None, max_length=20)
    branch: Optional[str] = Field(alias="PaBr", description="Branche", default=None, max_length=20)
    function_legal_status: Optional[StatuutEnum] = Field(alias="PaSt", description="Statuut", default=None, examples=[list(StatuutEnum)])
    specific_function_type: Optional[SpecificFunctionTypeEnum] = Field(alias="PaSb", description="Specifieke betrekking", default=None, examples=[list(SpecificFunctionTypeEnum)])
    is_management: Optional[bool] = Field(alias="PaDi", description="Directie", default=None, examples=[True, False])
    function_title: Optional[FunctionTitleEnum] = Field(alias="PaTi", description="Titel", default=None, examples=[list(FunctionTitleEnum)])
    salary_scale_category: Optional[str] = Field(alias="PaBa", description="Barema categorie", default=None, max_length=10)
    salary_scale_date: Optional[date] = Field(alias="PaBd", description="Barema datum", default=None, examples=[date(2020, 1, 1)])
    is_retired_employee: Optional[bool] = Field(alias="PaGm", description="Gepensioneerde medewerker", default=None, examples=[True, False])
    disability_risk_group: Optional[DisabilityRiskGroupEnum] = Field(alias="PaRi", description="Risicogroep AO", default=None, examples=[list(DisabilityRiskGroupEnum)])
    ape_plan: Optional[APEPlanEnum] = Field(alias="PaAp", description="A.P.E.", default=None, examples=[list(APEPlanEnum)])
    function_level: Optional[FunctionLevelEnum] = Field(alias="FuLe", description="Functieniveau", default=None, examples=[list(FunctionLevelEnum)])
    pension_insurance_provider: Optional[PensionInsuranceProviderEnum] = Field(alias="DeGi", description="Afw. kas groepsverz.", default=None, examples=[list(PensionInsuranceProviderEnum)])
    research_type: Optional[ResearchTypeEnum] = Field(alias="ReTy", description="Type onderzoek", default=None, examples=[list(ResearchTypeEnum)])
    grade_function: Optional[HealthcareGradeFunctionEnum] = Field(alias="GrFu", description="Graad/functie", default=None, examples=[list(HealthcareGradeFunctionEnum)])
    healthcare_personnel_category: Optional[HealthcarePersonnelCategoryEnum] = Field(alias="MPCa", description="MZG-personeelscategorie", default=None, examples=[list(HealthcarePersonnelCategoryEnum)])
    healthcare_function: Optional[HealthcareFunctionEnum] = Field(alias="MFun", description="MZG-functie", default=None, examples=[list(HealthcareFunctionEnum)])
    healthcare_qualification: Optional[HealthcareQualificationEnum] = Field(alias="MQua", description="MZG-kwalificatie", default=None, examples=[list(HealthcareQualificationEnum)])
    healthcare_nursing_unit: Optional[str] = Field(alias="MNun", description="MZG-verpleegeenheid", default=None, max_length=20)
    healthcare_campus_code: Optional[str] = Field(alias="MCCd", description="MZG-campuscode", default=None, max_length=20)
    historical_physical_department: Optional[str] = Field(alias="HiPh", description="Hist. fysische afdeling", default=None, max_length=20)
    personnel_category_type1: Optional[PersonnelCategoryType1Enum] = Field(alias="PeT1", description="Personeelscat-aard1", default=None, examples=[list(PersonnelCategoryType1Enum)])
    personnel_type2: Optional[PersonnelType2Enum] = Field(alias="PeT2", description="Personeelstype-aard2", default=None, examples=[list(PersonnelType2Enum)])
    group_insurance_policy_number: Optional[str] = Field(alias="NVP", description="Polisnr. groepsverzekering", default=None, max_length=12)
    group_insurance_company: Optional[float] = Field(alias="CVM", description="Maatschappij voor groepsverzekering", default=None, examples=[1.0])
    has_group_insurance: Optional[bool] = Field(alias="CVR", description="Groepsverzekering", default=None, examples=[True, False])
    work_location_place: Optional[str] = Field(alias="RsWk", description="Plaats werklocatie", default=None, max_length=24)
    establishment_number: Optional[str] = Field(alias="W06", description="Vestigingsnummer", default=None, max_length=20)
    accident_insurance_company_code: Optional[str] = Field(alias="Z26", description="Code verzekeringsmaatschappij ongeval", default=None, max_length=3)
    community: Optional[CommunityEnum] = Field(alias="Z28", description="Gemeenschap", default=None, examples=[list(CommunityEnum)])
    region: Optional[RegionEnum] = Field(alias="Z29", description="Gewest", default=None, examples=[list(RegionEnum)])
    work_location_postal_code: Optional[str] = Field(alias="ZpWk", description="Postcode van werklocatie", default=None, max_length=5)

    model_config = ConfigDict(
        serialize_by_alias=True,
        str_strip_whitespace=True,
        str_min_length=0,
        str_max_length=255,
        coerce_numbers_to_str=False,
        extra="allow",
        frozen=True,
        allow_inf_nan=False,
        ser_json_timedelta="iso8601",
        ser_json_bytes="base64",
        validate_default=True,
        use_enum_values=True,
        validate_by_name=True,
        validate_by_alias=True,
    )


class SalaryCostCreate(BaseModel):
    """Pydantic schema for AfasSalaryCost fields"""
    # --- General AFAS salary cost fields ---
    guid: Optional[str] = Field(alias="GUID", description="GUID", default=None, max_length=38, examples=["00000000-0000-0000-0000-000000000000"])
    organisational_unit: Optional[str] = Field(alias="DpId", description="Organisatorische eenheid", default=None, max_length=10)
    function: Optional[str] = Field(alias="FuId", description="Functie", default=None, max_length=10)
    cost_carrier: Optional[str] = Field(alias="CcId", description="Kostendrager", default=None, max_length=30)
    cost_center: Optional[str] = Field(alias="CrId", description="Kostenplaats", default=None, max_length=30)
    project: Optional[str] = Field(alias="PjId", description="Project", default=None, max_length=15)
    team_member_profile: Optional[int] = Field(alias="TmPr", description="Teamlid profiel", default=None, examples=[1])
    percentage: Optional[float] = Field(alias="Perc", description="Percentage", default=None, examples=[1.0])
    formation_place: Optional[str] = Field(alias="FpId", description="Formatieplaats", default=None, max_length=15)

    # --- Dashboard configuration fields ---
    exclude_absence_dashboard: Optional[bool] = Field(alias="ExAb", description="Uitsluiten voor verzuim in dashboards", default=None, examples=[True, False])
    exclude_formation_dashboard: Optional[bool] = Field(alias="ExEs", description="Uitsluiten voor formatie in dashboards", default=None, examples=[True, False])
    exclude_journaling: Optional[bool] = Field(alias="ExJo", description="Uitsluiten voor journalisering", default=None, examples=[True, False])
    has_different_head_manager: Optional[bool] = Field(alias="HdLg", description="Afwijkende hoofdleidinggevende voor de OE", default=None, examples=[True, False])

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


class EducationalLocationCreate(BaseModel):
    """Pydantic schema for AfasEducationalLocation fields"""
    # --- General AFAS educational location fields ---
    educational_location_sequence_number: Optional[int] = Field(alias="ElSn", description="Volgnummer onderwijslocatie", default=None, examples=[1])

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
