#general imports
from re import L
from typing import Optional, List, Union, Literal
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
    ContractTypeEnum, EmployeeTypeEnum, EmploymentCodeEnum,
    OutOfServiceReasonEnum, TerminationInitiatedByEnum, ProbationPeriodEnum, EmploymentStartReasonEnum,
    TerminationReasonEnum, WorkRelationTypeEnum, FundingSourceEnum, InsuranceEnum, PeriodicRaiseBehaviorEnum,
    EmploymentPhaseClassificationEnum, FlexEmploymentEndReasonEnum, ChainEnum, EducationLevelEnum,
    ContractSpecificationEnum, EmploymentLegalStatusEnum, ContractCategoryEnum, RSZType1Enum, RSZType2Enum,
    SalaryCalculationMethodEnum, RecruitmentTypeEnum, PerformanceExceptionEnum, EducationStatusEnum,
    OccupationCategoryEnum, DFMARiskClassEnum, FixedTermContractEnum, WorkTimeRegimeEnum, RSZCategoryEnum,
    RetroactivePaymentTypeEnum, ApprenticeshipTypeEnum, EducationLevelAdditionEnum, RiskClassAdditionEnum,
    ContractTypeAdditionEnum, CompanyPlanEnum, PreviousWorkerTypeEnum, IPAGCodeEnum, HistoricContractTypeEnum,
    ContractDurationUnitEnum, FiscalRegimeEnum, FiscalRegimeExemptionEnum, RIZIVPeriodicityEnum,
    PartenaEducationLevelCodeEnum, PartenaContractPrecisionCodeEnum, PartenaLearningContractRegionEnum,
    PartenaDismissalReasonEnum, PartenaTemporaryContractEnum, PartenaTitleEnum, PartenaLearnerTypeEnum,
    PartenaContractCategoryEnum, PartenaContractTypeEnum
)

class ContractCreate(BaseModel):
    """Pydantic schema for creating a new salary record"""
    #required according to api are marked with *
    # --- General AFAS contract fields ---
    start_date_contract: Optional[date] = Field(alias="DaBe", description = "Begindatum contract", default=None, examples=[date(2020,1,1)]) #*
    end_date_contract: Optional[date] = Field(alias="DaEn", description = "Einddatum contract", default=None, examples=[date(2021,1,1)])
    cao: Optional[str] = Field(alias="ClId", description = "Cao (cla)", default = None, max_length=15, examples=[""]) #* TODO example
    terms_of_employment: Optional[str] = Field(alias="WcId", description = "Arbeidsvoorwarde", default = None, max_length = 15) #* TODO exmaple
    contract_type: Optional[ContractTypeEnum] = Field(alias="ApCo", description = "Type contract", default = None, examples=[list(ContractTypeEnum)]) #*
    employment_type: Optional[str] = Field(alias="PEmTy", description = "Type dienstverband", default = None, max_length = 1)
    employment_sequence_number: Optional[int] = Field(alias="DvSn", description = "Volgnummer dienstverband", default = None, examples=[1])
    employment_id: Optional[int] = Field(alias="EnSe", description = "Dienstverband", default = None, examples=[1])
    last_working_day: Optional[date] = Field(alias="ArvDaLw", description="Laatste werkdag", default=None, examples=[date(2020,12,31)])
    pension_scheme_start_code: Optional[str] = Field(alias="ArvStPn", description="Start pensioenregeling", default=None, max_length=10, examples=["PEN01"])
    pension_start_weeks: Optional[int] = Field(alias="ArvStwp", description="Start weken pensioen", default=None, examples=[26])
    second_pension_pillar_contribution: Optional[bool] = Field(alias="B2Pp", description="Bijdrage 2e pensioenpijler", default=None, examples=[True, False])
    employer: Optional[str] = Field(alias="CmId", description = "Werkgever", default = None, max_length = 15, examples=[""]) #* TODO example
    date_in_service_original: Optional[date] = Field(alias="DbYs", description = "Datum in dienst (i.v.m. dienstjaren)", default = None, examples=[date(2020,1,1)])
    transition_service_date: Optional[date] = Field(alias="DbYT", description="Indienst i.v.m. transitieverg.", default=None, examples=[date(2020,1,1)])
    out_of_service_date: Optional[date] = Field(alias="DaEe", description = "Datum uit dienst", default = None, examples=[date(2021,1,1)])
    employee_type: Optional[EmployeeTypeEnum] = Field(alias="EmMt", description = "Soort medewerker", default = None, examples=[list(EmployeeTypeEnum)])
    employment_code: Optional[EmploymentCodeEnum] = Field(alias="ViEt", description = "Dienstbetrekking", default = None, examples=[list(EmploymentCodeEnum)])
    termination_reason: Optional[OutOfServiceReasonEnum] = Field(alias="ViRe", description = "Reden", default = None, examples=[list(OutOfServiceReasonEnum)])
    termination_iniative: Optional[TerminationInitiatedByEnum] = Field(alias="ViIe", description = "Iniatief", default = None, examples=[list(TerminationInitiatedByEnum)])
    probation_period: Optional[ProbationPeriodEnum] = Field(alias="ViTo", description = "Proeftijd", default = None, examples=[list(ProbationPeriodEnum)])
    probation_end_date: Optional[date] = Field(alias="DaEt", description = "Einde proeftijd per", default = None, examples=[date(2021,1,1)])
    periodic_period_number: Optional[int] = Field(alias="PeNo", description = "Periodenummer periodiek", default = None, examples=[1])
    repeat_after_periods: Optional[int] = Field(alias="PeRp", description = "Herhaal na (perioden)", default = None, examples=[1])
    next_raise_period: Optional[str] = Field(alias="PeFt", description = "Periode volgende verhoging", default = None, examples=["1"], max_length = 15)
    employment_start_reason: Optional[EmploymentStartReasonEnum] = Field(alias="ViBg", description = "Reden in dienst", default = None, examples=[list(EmploymentStartReasonEnum)])
    apply_waiting_days: Optional[bool] = Field(alias="RtDa", description = "wachtdagen toepassen", default = None, examples=[True, False])
    termination_reason_tkp: Optional[TerminationReasonEnum] = Field(alias="TkRe", description = "Reden uit dienst (TKP Vervoer)", default = None, examples=[list(TerminationReasonEnum)])
    termination_reason_tkp_general: Optional[str] = Field(alias="ViTK", description = "Reden uit dienst (TKP)", default = None, max_length=20, examples=["01"])
    employment_relation_type: Optional[WorkRelationTypeEnum] = Field(alias="TpWr", description = "Aard arbeidsrelatie", default = None, examples=[list(WorkRelationTypeEnum)])
    funding_source: Optional[FundingSourceEnum] = Field(alias="FiBr", description = "Financieringsbron", default = None, examples=[list(FundingSourceEnum)])
    insurance_type: Optional[InsuranceEnum] = Field(alias="InTp", description = "Verzekering", default = None, examples=[list(InsuranceEnum)])
    raise_method: Optional[PeriodicRaiseBehaviorEnum] = Field(alias="InMe", description = "Gedrag periodiek toekennen", default = None, examples=[list(PeriodicRaiseBehaviorEnum)])
    deviation_factor_min_max: Optional[float] = Field(alias="Pfmm", description = "Afwijkende factor min/max", default = None, examples=[1.0])
    raise_amount: Optional[float] = Field(alias="InVl", description = "Verhoging met bedrag", default = None, examples=[1.0])
    raise_percentage: Optional[float] = Field(alias="InPc", description = "Verhoging met percentage", default = None, examples=[1.0])
    employment_phase_classification: Optional[EmploymentPhaseClassificationEnum] = Field(alias="ViFz", description = "Fase-indeling Flex en Zekerheid ", default = None, examples=[list(EmploymentPhaseClassificationEnum)])
    flex_employment_end_reason: Optional[FlexEmploymentEndReasonEnum] = Field(alias="ViRf", description = "Reden einde inkomstenverhouding flexwerker", default = None, examples=[list(FlexEmploymentEndReasonEnum)])
    contract_chain_start_date: Optional[date] = Field(alias="DaSc", description = "Begindatum contractketen", default = None, examples=[date(2020,1,1)])
    chain_code: Optional[ChainEnum] = Field(alias="ViKe", description = "Contractketen code", default = None, examples=["0"])
    number_income_ratio: Optional[int] = Field(alias="EnS2", description = "Nr. inkomstenverhouding", default = None, examples=[1])
    planned_hours_q1: Optional[int] = Field(alias="PdQ1", description = "Geplande uren (1e kw.)", default = None, examples=[100])
    planned_hours_q2: Optional[int] = Field(alias="PdQ2", description = "Geplande uren (2e kw.)", default = None, examples=[100])
    planned_hours_q3: Optional[int] = Field(alias="PdQ3", description = "Geplande uren (3e kw.)", default = None, examples=[100])
    planned_hours_q4: Optional[int] = Field(alias="PdQ4", description = "Geplande uren (4e kw.)", default = None, examples=[100])
    planned_hours_q5: Optional[int] = Field(alias="PdQ5", description = "Geplande uren (5e kw.)", default = None, examples=[100])
    paritary_commission_indexation: Optional[str] = Field(alias="JcIn", description = "Commission paritaire indexatie", default = None, examples=["0"], max_length = 7)
    education_level: Optional[EducationLevelEnum] = Field(alias="AcDe", description = "Opleidingsgraad", default = None, examples=[list(EducationLevelEnum)])
    rddf: Optional[bool] = Field(alias="RDDF", description = "RDDF", default = None, examples=[True, False])
    appointment_basis: Optional[str] = Field(alias="BaAp", description = "Benoemingsgrondslag", default = None, max_length=10)
    education_field_1: Optional[str] = Field(alias = "Sco1", description = "Onderwijsterrein 1", default= None, max_length = 10)
    education_field_2: Optional[str] = Field(alias = "Sco2", description = "Onderwijsterrein 2", default= None, max_length = 10)
    education_field_3: Optional[str] = Field(alias = "Sco3", description = "Onderwijsterrein 3", default= None, max_length = 10)
    education_field_4: Optional[str] = Field(alias = "Sco4", description = "Onderwijsterrein 4", default= None, max_length = 10)
    contract_specification: Optional[ContractSpecificationEnum] = Field(alias = "PCK", description = "Precisering contract", default= None, examples=[list(ContractSpecificationEnum)])
    employment_legal_status: Optional[EmploymentLegalStatusEnum] = Field(alias = "EmSt", description = "Statuut", default= None, examples=[list(EmploymentLegalStatusEnum)]) #seems belgian specific
    employment_status_code: Optional[EmploymentLegalStatusEnum] = Field(alias="Stat", description="Statuut (DvB)", default=None, examples=[list(EmploymentLegalStatusEnum)])
    # --- Belgian RSZ/DMFA related fields ---
    contract_category: Optional[ContractCategoryEnum] = Field(alias = "CtTy", description = "Contractsoort", default= None, examples=[list(ContractCategoryEnum)])
    rsz_type_1: Optional[RSZType1Enum] = Field(alias = "TRsz", description = "Type #1 medewerker", default= None, examples=[list(RSZType1Enum)])
    rsz_type_2: Optional[RSZType2Enum] = Field(alias = "TRs2", description = "Type #2 medewerker", default= None, examples=[list(RSZType2Enum)])
    salary_calculation_method: Optional[SalaryCalculationMethodEnum] = Field(alias = "SCAc", description = "Salarisverwerking", default= None, examples=[list(SalaryCalculationMethodEnum)])
    right_to_payroll_reduction: Optional[bool] = Field(alias = "RSRi", description = "Vermindering en datum recht", default= None, examples=[True, False])
    rsz_reduction_start_date: Optional[date] = Field(alias = "RSDa", description = "Start RSZ-vermindering", default= None, examples=[date(2020,1,1)])
    seniority_start_date: Optional[date] = Field(alias = "StAc", description = "Startdatum anciënniteit", default= None, examples=[date(2020,1,1)])
    adjusted_seniority_date: Optional[date] = Field(alias = "FiAn", description = "Fictieve anciënniteitsdatum", default= None, examples=[date(2020,1,1)])
    recruitment_type_start_date: Optional[date] = Field(alias = "DaRt", description = "Begin aanwervingskader", default= None, examples=[date(2020,1,1)])
    recruitment_type: Optional[RecruitmentTypeEnum] = Field(alias = "ReTy", description = "Aanwervingskader", default= None, examples=[list(RecruitmentTypeEnum)])
    sociale_maribel: Optional[float] = Field(alias = "SoMb", description = "Sociale maribel", default= None, examples=[1.0])
    performance_exception: Optional[PerformanceExceptionEnum] = Field(alias = "PeEx", description = "Notie vrijstelling prestaties", default= None, examples=[list(PerformanceExceptionEnum)])
    exception_start_date: Optional[date] = Field(alias = "DaEx", description = "Begindatum vrijstelling", default= None, examples=[date(2020,1,1)])
    education_status_start_date: Optional[date] = Field(alias = "DaEd", description = "Begindatum status vorming", default= None, examples=[date(2020,1,1)])
    education_status: Optional[EducationStatusEnum] = Field(alias = "StEd", description = "Status vorming", default= None, examples=[list(EducationStatusEnum)])
    has_written_contract: Optional[bool] = Field(alias = "WrCt", description = "Schriftelijk arbeidsovereenkomst", default= None, examples=[True, False])
    management_group_key: Optional[str] = Field(alias = "StCd", description = "sturingsgroep sleutel", default= None, max_length=20, examples=["0"]) #TODO exmaples
    occupation_category: Optional[OccupationCategoryEnum] = Field(alias = "ViAc", description = "Beroepscategorie", default= None, examples=[list(OccupationCategoryEnum)])
    invoice_group: Optional[int] = Field(alias = "FaGr", description = "Facturatiegroep", default= None, examples=[1])
    rsz_id: Optional[str] = Field(alias = "KRS", description = "Kengetal RSZ", default = None, max_length = 20, examples=["0"])
    risk_class_dfma: Optional[DFMARiskClassEnum] = Field(alias = "RMfa", description = "Risicoklasse DMFA", default= None, examples=[list(DFMARiskClassEnum)])
    fixed_term_contract: Optional[FixedTermContractEnum] = Field(alias = "Z36", description = "Contract bepaalde duur", default= None, examples=[list(FixedTermContractEnum)])
    work_time_regime: Optional[WorkTimeRegimeEnum] = Field(alias = "CDT", description = "Fulltime/parttime ", default= None, examples=[list(WorkTimeRegimeEnum)])
    subject_to_rsz: Optional[bool] = Field(alias = "COR", description = "Onderworpen RSZ", default= None, examples=[True, False])
    rsz_category: Optional[RSZCategoryEnum] = Field(alias = "CCW", description = "RSZ-categorie", default= None, examples=[list(RSZCategoryEnum)])
    foreign_origin_number: Optional[float] = Field(alias = "BOR", description = "Buitenlandse origine", default= None, examples=[1.0])
    notice_date: Optional[date] = Field(alias = "DtIn", description = "aangezegd op", default= None, examples=[date(2020,1,1)])
    cao_three_of_five_start: Optional[date] = Field(alias = "Yh35", description = "3 uit 5 jaar in cao vanaf", default= None, examples=[date(2020,1,1)])
    cao_five_consecutive_years_from: Optional[date] = Field(alias = "Yh5c", description = "5 jaar aaneengesloten in cao vanaf", default= None, examples=[date(2020,1,1)])
    retroactive_payment_type: Optional[RetroactivePaymentTypeEnum] = Field(alias = "ViPp", description = "Soort nabetaling", default= None, examples=[list(RetroactivePaymentTypeEnum)])
    # --- Partena-specific fields ---
    sd_worx_group: Optional[str] = Field(alias = "SDGr", description = "Group SD Worx", default= None, max_length=20, examples=["SD001"])
    partena_cao_42: Optional[bool] = Field(alias = "PaCa", description = "CAO42", default= None, examples=[True, False])
    partena_professional_seniority_date: Optional[date] = Field(alias = "PaDp", description = "Prof anciënniteit", default= None, examples=[date(2020,1,1)])
    partena_last_study_end_date: Optional[date] = Field(alias = "PaEd", description = "Einddatum laatste studie", default= None, examples=[date(2020,1,1)])
    partena_fictive_seniority_years: Optional[float] = Field(alias = "PaJf", description = "Jaren fictieve anciënniteit", default= None, examples=[1.5])
    partena_professional_years: Optional[float] = Field(alias = "PaPr", description = "Prof jaren", default= None, examples=[2.0])
    partena_student_number: Optional[str] = Field(alias = "PaNr", description = "Nummer leerling", default= None, max_length=15, examples=["ST123"])
    partena_education_level_code: Optional[PartenaEducationLevelCodeEnum] = Field(alias = "PaOp", description = "Opleidingsniveau", default= None, examples=[list(PartenaEducationLevelCodeEnum)])
    partena_contract_precision_code: Optional[PartenaContractPrecisionCodeEnum] = Field(alias = "PaPc", description = "Precisering contract", default= None, examples=[list(PartenaContractPrecisionCodeEnum)])
    partena_learning_contract_region: Optional[PartenaLearningContractRegionEnum] = Field(alias = "PaRe", description = "Regio leercontract", default= None, examples=[list(PartenaLearningContractRegionEnum)])
    partena_dismissal_reason: Optional[PartenaDismissalReasonEnum] = Field(alias = "PaRu", description = "Reden uit dienst", default= None, examples=[list(PartenaDismissalReasonEnum)])
    partena_temporary_contract: Optional[PartenaTemporaryContractEnum] = Field(alias = "PaTc", description = "Tijdelijk contract", default= None, examples=[list(PartenaTemporaryContractEnum)])
    partena_title: Optional[PartenaTitleEnum] = Field(alias = "PaTi", description = "Titel", default= None, examples=[list(PartenaTitleEnum)])
    partena_learner_type: Optional[PartenaLearnerTypeEnum] = Field(alias = "PaTl", description = "Type leerling", default= None, examples=[list(PartenaLearnerTypeEnum)])
    partena_group: Optional[str] = Field(alias = "PaGr", description = "Groep partena", default= None, max_length=20, examples=["GRP001"])
    partena_contract_category: Optional[PartenaContractCategoryEnum] = Field(alias = "PaCc", description = "Contract categorie", default= None, examples=[list(PartenaContractCategoryEnum)])
    partena_contract_type: Optional[PartenaContractTypeEnum] = Field(alias = "PaCt", description = "Type Contract", default= None, examples=[list(PartenaContractTypeEnum)])
    statutory_pension_date: Optional[date] = Field(alias="PeDa", description="Wettelijke pensioendatum", default=None, examples=[date(2025,1,1)])
    # --- DvB-specific fields ---
    dvb_medical_service_required: Optional[bool] = Field(alias="DvbAGK", description="Onderworpen aan arbeidsgeneeskunde", default=None, examples=[True, False])
    dvb_absence_id: Optional[int] = Field(alias="DvbAbId", description="Verzuim", default=None, examples=[101])
    dvb_special_social_security: Optional[bool] = Field(alias="DvbBSZ", description="Onderworpen bijz. soc. Zekerheid", default=None, examples=[True, False])
    dvb_borrower_cao_code: Optional[str] = Field(alias="DvbCAHi", description="Cao-code inlener", default=None, max_length=10, examples=["CAO10"])
    dvb_contract_category: Optional[str] = Field(alias="DvbCCK", description="Contractcategorie", default=None, max_length=10, examples=["CAT01"])
    dvb_riziv_pension_code: Optional[str] = Field(alias="DvbCPI", description="RIZIV pensioen", default=None, max_length=10, examples=["RIZ01"])
    dvb_contract_type: Optional[str] = Field(alias="DvbCtTy", description="ContractType", default=None, max_length=10, examples=["CT01"])
    dvb_prepension_start_date: Optional[date] = Field(alias="DvbDAP", description="Begindatum (brug)pensioen", default=None, examples=[date(2020,1,1)])
    dvb_notice_start_date: Optional[date] = Field(alias="DvbDaDi", description="Begindatum opzegging", default=None, examples=[date(2020,6,1)])
    dvb_last_allocation_date: Optional[date] = Field(alias="DvbDaLa", description="Datum laatste toekenning", default=None, examples=[date(2020,12,1)])
    dvb_debtor_note: Optional[str] = Field(alias="DvbDeNo", description="Notie debiteur", default=None, max_length=10, examples=["DEB01"])
    dvb_declare_replacement_fund: Optional[bool] = Field(alias="DvbDecl", description="Declareren bij Vervangingsfonds", default=None, examples=[True, False])
    dvb_employment_id: Optional[int] = Field(alias="DvbEnSe", description="Dienstverband (DvB)", default=None, examples=[1])
    dvb_dismissal_method: Optional[str] = Field(alias="DvbFiTy", description="Ontslagwijze", default=None, max_length=10, examples=["DIS01"])
    dvb_compensation_end_date_joint_agreement: Optional[date] = Field(alias="DvbGmAk", description="Einddatum vergoeding in gemeenschappelijk akkoord", default=None, examples=[date(2021,1,1)])
    dvb_registration_number: Optional[str] = Field(alias="DvbIBZ", description="Inschrijfnummer", default=None, max_length=8, examples=["12345678"])
    dvb_internal_replacement: Optional[bool] = Field(alias="DvbInFt", description="Vervanging binnen eigen FTE bij vrijwillige verz.", default=None, examples=[True, False])
    dvb_extension: Optional[bool] = Field(alias="DvbIsAt", description="Uitbreiding", default=None, examples=[True, False])
    dvb_leave_id: Optional[int] = Field(alias="DvbLeId", description="Verlof", default=None, examples=[5])
    dvb_reemployment_measure: Optional[str] = Field(alias="DvbMaWe", description="Maatregel werkhervatting", default=None, max_length=10, examples=["MEAS1"])
    dvb_dmfa_fraction_numerator: Optional[int] = Field(alias="DvbNoDm", description="Teller breuk DMFA", default=None, examples=[2])
    dvb_employee_number: Optional[float] = Field(alias="DvbPNR", description="Medewerkernummer", default=None, examples=[1001])
    dvb_riziv_periodicity: Optional[str] = Field(alias="DvbPRR", description="Periodiciteit RIZIV", default=None, max_length=10, examples=["PR1"])
    dvb_riziv_periodicity_code: Optional[str] = Field(alias="DvbPRiz", description="Periodiciteit RIZIV (code)", default=None, max_length=10, examples=["PR2"])
    dvb_pool_substitute: Optional[bool] = Field(alias="DvbPool", description="Poolvervanger", default=None, examples=[True, False])
    dvb_out_of_service_reason_code: Optional[str] = Field(alias="DvbREAc", description="Reden uit dienst (code)", default=None, max_length=10, examples=["RE01"])
    dvb_out_of_service_reason_description: Optional[str] = Field(alias="DvbRESd", description="Reden uit dienst", default=None, max_length=10, examples=["RE02"])
    dvb_riziv_code: Optional[str] = Field(alias="DvbRizi", description="RIZIV code", default=None, max_length=10, examples=["RZ01"])
    dvb_replacement_register_number: Optional[str] = Field(alias="DvbRrRe", description="Rijksregisternr vervanger", default=None, max_length=11, examples=["75010112345"])
    dvb_rvp_category: Optional[str] = Field(alias="DvbRvpC", description="RVP categorie", default=None, max_length=10, examples=["RVP1"])
    dvb_special_social_security_code: Optional[str] = Field(alias="DvbSBZ", description="Bijz. soc. Zekerheid", default=None, max_length=10, examples=["SBZ1"])
    dvb_leave_service_id: Optional[int] = Field(alias="DvbSEns", description="DV Verlof", default=None, examples=[3])
    dvb_startbaan_agreement: Optional[str] = Field(alias="DvbSbo", description="Startbaanovereenkomst", default=None, max_length=10, examples=["STB1"])
    dvb_notice_send_date: Optional[date] = Field(alias="DvbSdDa", description="Datum verzending opzegging", default=None, examples=[date(2020,7,1)])
    dvb_notice_delivery_date: Optional[date] = Field(alias="DvbSdDi", description="Betekening opzegging", default=None, examples=[date(2020,7,10)])
    dvb_sd_worx_identifier: Optional[str] = Field(alias="DvbSdNr", description="Identificatie SD Worx", default=None, max_length=2, examples=["01"])
    dvb_acerta_sequence_number: Optional[int] = Field(alias="DvbSeAc", description="Volgnummer Acerta", default=None, examples=[12])
    dvb_seniority_start_date: Optional[date] = Field(alias="DvbStAn", description="Startdatum anciënniteit (DvB)", default=None, examples=[date(2019,1,1)])
    dvb_employment_status: Optional[str] = Field(alias="DvbStat", description="Statuut (DvB)", default=None, max_length=10, examples=["ST01"])
    dvb_replacement_employment: Optional[bool] = Field(alias="DvbSuDv", description="Vervangingsdienstverband", default=None, examples=[True, False])
    dvb_replaced_employee: Optional[str] = Field(alias="DvbSubs", description="Vervangt", default=None, max_length=15, examples=["EMP123"])
    dvb_bridge_pension_code: Optional[str] = Field(alias="DvbSwt", description="Code brugpensioen", default=None, max_length=10, examples=["BP01"])
    dvb_rsz_type_2: Optional[RSZType2Enum] = Field(alias="DvbTRs2", description="Type #2 medewerker (DvB)", default=None, examples=[list(RSZType2Enum)])
    dvb_rsz_type_1: Optional[RSZType1Enum] = Field(alias="DvbTRsz", description="Type #1 medewerker (DvB)", default=None, examples=[list(RSZType1Enum)])
    dvb_tax_exemption_code: Optional[str] = Field(alias="DvbTxEm", description="Fiscale vrijstelling ontslag", default=None, max_length=10, examples=["TX01"])
    dvb_reason_end_contract: Optional[str] = Field(alias="DvbViAo", description="Reden einde arbeidsovereenkomst", default=None, max_length=10, examples=["EA01"])
    dvb_contract_form: Optional[str] = Field(alias="DvbViCv", description="Contractvorm", default=None, max_length=10, examples=["CV01"])
    dvb_method_end_employment_be: Optional[str] = Field(alias="DvbViMa", description="Wijze einde dienstverband België", default=None, max_length=10, examples=["EM01"])
    dvb_reason_end_employment_be: Optional[str] = Field(alias="DvbViRe", description="Reden einde dienstverband België", default=None, max_length=10, examples=["ER01"])
    dvb_notice_method: Optional[str] = Field(alias="DvbViSs", description="Wijze betekening", default=None, max_length=10, examples=["WB01"])
    dvb_ww_revised: Optional[bool] = Field(alias="DvbWWHe", description="WW herzien", default=None, examples=[True, False])
    dvb_medical_service_code: Optional[float] = Field(alias="DvbZ27", description="Medische dienst", default=None, examples=[27])
    dvb_notice_compensation_end_date: Optional[date] = Field(alias="DvbZ59", description="Einde opzegvergoeding", default=None, examples=[date(2020,8,31)])
    dvb_ziv_withholding_code: Optional[str] = Field(alias="DvbZIV", description="Afhouding Z.I.V.", default=None, max_length=10, examples=["ZIV01"])

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


class ContractAdditionCreate(BaseModel):
    """Pydantic schema for AfasContractAddition (contract additions)"""
    # --- Contract addition (Belgian) fields ---
    concern_date: Optional[date] = Field(alias="DaCo", description="Concerndatum", default=None, examples=[date(2020, 1, 1)])
    insurance_category: Optional[str] = Field(alias="InCa", description="Categorie wetsverzekering", default=None, max_length=20)
    retired_with_performance: Optional[Literal["1", "0"]] = Field(alias="ReAc", description="Gepensioneerd met prestaties (1 = Ja)", default=None, max_length=20, examples=["1"])
    half_time_retired: Optional[Literal["1", "0"]] = Field(alias="HaRe", description="Halftijds bruggepensioneerd (1 = Ja)", default=None, max_length=20, examples=["1"])
    bridging_cost_center: Optional[str] = Field(alias="CoRe", description="Kostplaats brugpensioen", default=None, max_length=5)
    bridging_hours_per_week: Optional[float] = Field(alias="HoRe", description="Uren per week brugpensioen dagprijs", default=None, examples=[38.0])
    apprenticeship_type: Optional[ApprenticeshipTypeEnum] = Field(alias="Ap", description="Leerovereenkomst", default=None, examples=[list(ApprenticeshipTypeEnum)])
    education_level_addition: Optional[EducationLevelAdditionEnum] = Field(alias="EdLe", description="Niveau opleiding", default=None, examples=[list(EducationLevelAdditionEnum)])
    education: Optional[str] = Field(alias="Ed", description="Opleiding", default=None, max_length=20)
    healthcare_education: Optional[str] = Field(alias="EdHc", description="Opleiding (zorg)", default=None, max_length=20)
    risk_class_addition: Optional[RiskClassAdditionEnum] = Field(alias="RiGr", description="Risicoklasse arbeidsongeschiktheid", default=None, examples=[list(RiskClassAdditionEnum)])
    contract_type_addition: Optional[ContractTypeAdditionEnum] = Field(alias="CoTy", description="Type contract", default=None, examples=[list(ContractTypeAdditionEnum)])
    agreement_type: Optional[Literal["3"]] = Field(alias="AgTy", description="Soort overeenkomst", default=None, examples=["3"])
    restructuring_start_date: Optional[date] = Field(alias="DaRb", description="Begindatum herstructurering", default=None, examples=[date(2020, 1, 1)])
    company_plan: Optional[CompanyPlanEnum] = Field(alias="CoPl", description="Bedrijfsplan", default=None, examples=[list(CompanyPlanEnum)])
    bbt_right_start_date: Optional[date] = Field(alias="DaBB", description="Begin recht BBT/BBK", default=None, examples=[date(2020, 1, 1)])
    campus_code: Optional[str] = Field(alias="CoIz", description="Campuscode IZAG", default=None, max_length=20)
    previous_worker_type: Optional[PreviousWorkerTypeEnum] = Field(alias="PrWN", description="Vroegere soort werknemer", default=None, examples=[list(PreviousWorkerTypeEnum)])
    ipag_code: Optional[IPAGCodeEnum] = Field(alias="IpIz", description="IPAG/IZAG", default=None, examples=[list(IPAGCodeEnum)])
    rights_deviation: Optional[Literal["1"]] = Field(alias="RiDe", description="Afwijking rechten (1 = contract niet verwerken in calculator)", default=None, examples=["1"])
    historic_contract_type: Optional[HistoricContractTypeEnum] = Field(alias="CtSb", description="Historisch contracttype sociaal balans", default=None, examples=[list(HistoricContractTypeEnum)])
    contract_duration_amount: Optional[float] = Field(alias="CDNu", description="Duur contract aantal", default=None, examples=[12.0])
    contract_duration_unit: Optional[ContractDurationUnitEnum] = Field(alias="CDUn", description="Duur contract eenheid", default=None, examples=[list(ContractDurationUnitEnum)])
    notice_before_2014_amount: Optional[float] = Field(alias="NDBn", description="Opzegtermijn vóór 2014 aantal", default=None, examples=[3.0])
    notice_before_2014_unit: Optional[ContractDurationUnitEnum] = Field(alias="NDBu", description="Opzegtermijn vóór 2014 eenheid", default=None, examples=[list(ContractDurationUnitEnum)])
    notice_from_2014_amount: Optional[float] = Field(alias="NDFn", description="Opzegtermijn vanaf 2014 aantal", default=None, examples=[3.0])
    notice_from_2014_unit: Optional[ContractDurationUnitEnum] = Field(alias="NDFu", description="Opzegtermijn vanaf 2014 eenheid", default=None, examples=[list(ContractDurationUnitEnum)])
    hours_decimal_places: Optional[int] = Field(alias="DcHr", description="Aantal decimalen tonen bij uren", default=None, examples=[2])
    fiscal_regime: Optional[FiscalRegimeEnum] = Field(alias="FiRe", description="Fiscaal regime", default=None, examples=[list(FiscalRegimeEnum)])
    fiscal_regime_exemption: Optional[FiscalRegimeExemptionEnum] = Field(alias="ExFi", description="Reden vrijstelling fiscaal regime", default=None, examples=[list(FiscalRegimeExemptionEnum)])
    riziv_departure_date: Optional[date] = Field(alias="LDRi", description="Vertrekdatum RIZIV", default=None, examples=[date(2020, 1, 1)])
    riziv_periodicity: Optional[RIZIVPeriodicityEnum] = Field(alias="PRiS", description="Periodiciteit RIZIV", default=None, examples=[list(RIZIVPeriodicityEnum)])

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
