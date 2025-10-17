import pandera as pa
from pandera.typing import Series
from .enums import deliveryCondition, deliveryMethod, barcodeType, ProcessingMethod, collectionMethod, saleRelationType
from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Optional, List, Union
from datetime import date
from decimal import Decimal
from .organisation import OrganisationPayload, PostKnOrganisationFields, OrganisationObject, OrganisationElement


class DebtorGetSchema(pa.DataFrameModel):
    debtor_id: Series[str] = pa.Field(coerce=True)
    debtor_name: Series[str] = pa.Field(coerce=True)
    bcco: Series[str] = pa.Field(coerce=True)
    search_name: Series[str] = pa.Field(coerce=True,nullable=True)
    address_line_1: Series[str] = pa.Field(coerce=True)
    address_line_3: Series[str] = pa.Field(coerce=True)
    address_line_4: Series[str] = pa.Field(coerce=True, nullable=True)
    tel_nmbr: Series[str] = pa.Field(coerce=True,nullable=True)
    email: Series[str] = pa.Field(coerce=True, nullable=True)
    iban: Series[str] = pa.Field(coerce=True, nullable=True)
    btw_nmbr: Series[str] = pa.Field(coerce=True, nullable=True)
    ch_of_comm_nmbr: Series[str] = pa.Field(coerce=True, nullable=True)
    collect_account: Series[str] = pa.Field(coerce=True)
    pay_con: Series[str] = pa.Field(coerce=True)
    vat_duty: Series[str] = pa.Field(coerce=True)
    blocked: Series[bool] = pa.Field(coerce=True)
    credit_limit: Series[float] = pa.Field(coerce=True)
    currency_id: Series[str] = pa.Field(coerce=True)
    auto_payment: Series[bool] = pa.Field(coerce=True)
    create_date: Series[str] = pa.Field(coerce=True)
    modified_date: Series[str] = pa.Field(coerce=True)

    class Config:
        coerce = True
        strict = True

class DebtorCreate(BaseModel):
    """
    Pydantic schema for debtor creates.
    This schema allows validation of both flat and nested dictionaries through field aliases.
    """
    # Required Fields
    debtor_id: Optional[str] = Field(serialization_alias="DbId", default = None, description="Nummer debiteur") #only required inupdate, not create

    # Base Fields
    iban_default: Optional[str] = Field(serialization_alias="Iban", default = None, description="Voorkeur Iban nummer", max_length = 40,)
    bank_account_default: Optional[str] = Field(serialization_alias="BaAc", default = None, description="Voorkeur bank-/gironummer", max_length = 40, )
    bank_country_default: Optional[str] = Field(serialization_alias="CoId", default = None, description="Voorkeur bank-/gironummer land code", max_length = 3)
    is_debtor: Optional[bool] = Field(serialization_alias="IsDb", default = None, description="Is debiteur")
    contra_account_default: Optional[str] = Field(serialization_alias="ToAc", default = None, description="Voorkeur tegenrekening", max_length = 16)
    vat_id: Optional[str] = Field(serialization_alias="VaId", default = None, description="Btw-identificatienummer", max_length = 21)
    payment_conditions: Optional[str] = Field(serialization_alias="PaCd", default = None, description="Betalingsvoorwaarde", max_length = 5)
    representative: Optional[str] = Field(serialization_alias="VeId", default = None, description="Vertegenwoordiger", max_length = 16)
    language: Optional[str] = Field(serialization_alias="LgId", default = None, description="Taal", max_length = 3)
    currency: Optional[str] = Field(serialization_alias="CuId", default = None, description="Valuta", max_length = 3)
    dunning_scheme_id: Optional[int] = Field(serialization_alias="DsId", default = None, description="Afwijkende aanmaningsset")
    responsible_employee_id: Optional[int] = Field(serialization_alias="EmId", default = None, description="Verantwoordelijke", max_length = 15)
    vat_duty: Optional[str] = Field(serialization_alias="VaDu", default = None, description="Btw-plicht", max_length = 3)
    profile_id: Optional[str] = Field(serialization_alias="PrId", default = None, description="Profiel", max_length = 16)
    line_level_discount: Optional[float] = Field(serialization_alias="PrLi", default = None, description="% Regelkorting")
    invoice_discount: Optional[float] = Field(serialization_alias="PrFc", default = None, description="% Factuurkorting")
    credit_restriction: Optional[float] = Field(serialization_alias="ClPc", default = None, description="Kredietbeperking")
    payment_discount: Optional[float] = Field(serialization_alias="PrPt", default = None, description="% Betalingskorting")
    credit_limit: Optional[float] = Field(serialization_alias="KrLi", default = None, description="Kredietlimiet")
    invoice_to: Optional[str] = Field(serialization_alias="FaTo", default = None, description="Factureren aan", max_length = 16)
    transporter: Optional[str] = Field(serialization_alias="TrPt", default = None, description="Vervoerder", max_length = 16)
    transport_priority: Optional[int] = Field(serialization_alias="PrDl", default = None, description="Prioriteit levering")
    to_price_from: Optional[str] = Field(serialization_alias="PrVn", default = None, description="Prijzen van", max_length=16)
    price_list_default: Optional[str] = Field(serialization_alias="PrLs", default = None, description="Voorkeur prijslijst", max_length=5)
    warehouse_default: Optional[str] = Field(serialization_alias="VkMa", default = None, description="Voorkeur magazijn", max_length=15)
    transfer_blocked: Optional[bool] = Field(serialization_alias="Bl", default = None, description="Geblokkeerd voor levering")
    total_block: Optional[bool] = Field(serialization_alias="BlTl", default = None, description="Volledig blokkeren, niet meer zichtbaar")
    vat_listing: Optional[bool] = Field(serialization_alias="VaLi", default = None, description="Btw-listing")
    principal_declarant: Optional[str] = Field(serialization_alias="LDId", default = None, description="Hoofddeclarant", max_length = 15)
    exceptional_vat_rate_group: Optional[bool] = Field(serialization_alias="VaYN", default = None, description="Afwijkende btw-tariefgroep")
    send_payment_reminder: Optional[bool] = Field(serialization_alias="DuYN", default = None, description="Aanmaning verzenden")
    code_group_administration: Optional[str] = Field(serialization_alias="VaIg", default = None, description="Code groepsadministratie", max_length = 20)
    status_monitoring: Optional[str] = Field(serialization_alias="VaGu", default = None, description=" Status bewaking", max_length = 20)
    discount_group: Optional[str] = Field(serialization_alias="DsGr", default = None, description="Kortingsgroep", max_length = 5)
    net_price: Optional[bool] = Field(serialization_alias="NtPr", default = None, description="Nettoprijs")
    price_vat_included: Optional[bool] = Field(serialization_alias="VtIn", default = None, description="Prijs incl. btw")
    invoice_text: Optional[str] = Field(serialization_alias="InTx", default = None, description="Factuurtekst", max_length = 40)
    condense_invoice: Optional[bool] = Field(serialization_alias="CITo", default = None, description="Factuur geheel verdichten")
    condensed_invoice_text: Optional[str] = Field(serialization_alias="TxTc", default = None, description="Geheel verdichte factuurtekst", max_length = 40)
    strict_maximum: Optional[bool] = Field(serialization_alias="StMa", default = None, description="Strikt maximum")
    maximum_invoice_amount: Optional[float] = Field(serialization_alias="MaIn", default = None, description="Maximum factuurbedrag")
    strict_minimum: Optional[bool] = Field(serialization_alias="StMi", default = None, description="Strikt minimum")
    minimum_invoice_amount: Optional[float] = Field(serialization_alias="MiIn", default = None, description="Minimum factuurbedrag")
    rounding_method: Optional[str] = Field(serialization_alias="RoOf", default = None, description="Afrondingsmethode", max_length = 5)
    declarant: Optional[str] = Field(serialization_alias="DeId", default = None, description="Declarant", max_length = 15)
    collection_specification: Optional[bool] = Field(serialization_alias="PaSp", default = None, description="Incassospecificatie")
    automatic_collection: Optional[bool] = Field(serialization_alias="AuPa", default = None, description="Automatisch incasseren")
    condense: Optional[bool] = Field(serialization_alias="PaCo", default = None, description="Verdichten")
    one_off_mandate_required: Optional[bool] = Field(serialization_alias="SiPA", default = None, description="Eenmalige incassomachtiging vereist")
    show_order_quote_warning: Optional[bool] = Field(serialization_alias="WaOr", default = None, description="Waarschuwing bij order/offerte")
    warning_text: Optional[str] = Field(serialization_alias="WaTx", default = None, description="Waarschuwingstekst")
    cbs_types: Optional[str] = Field(serialization_alias="CsTy", default = None, description="CBS types", max_length = 1)
    reaction: Optional[bytes] = Field(serialization_alias="Rm", default = None, description="Opmerking")
    default_delivery_address: Optional[int] = Field(serialization_alias="DeACdDad", default = None, description="Voorkeur afleveradres")
    contact_person: Optional[int] = Field(serialization_alias="CtP1", default = None, description="Contactpersoon")
    extra_contact_person: Optional[int] = Field(serialization_alias="CtP2", default = None, description="Extra contactpersoon")
    collection_account: Optional[str] = Field(serialization_alias="ColA", default = None, description="Verzamelrekening", max_length = 16)
    customer_since: Optional[date] = Field(serialization_alias="CsDa", default = None, description="Klant sinds")
    referred_by: Optional[str] = Field(serialization_alias="BcBy", default = None, description="Aangebracht door", max_length = 15)
    delivery_condition: Optional[deliveryCondition] = Field(serialization_alias="DeCo", default = None, description="Leveringsconditie")
    default_contract: Optional[int] = Field(serialization_alias="CtI1", default = None, description="Voorkeur contract")
    default_delivery_method: Optional[deliveryMethod] = Field(serialization_alias="InPv", default = None, description="Voorkeur verstrekkingswijze")
    order_sorting: Optional[str] = Field(serialization_alias="SoId", default = None, description=" Ordersortering", max_length = 8)
    barcode_type: Optional[barcodeType] = Field(serialization_alias="VaBc", default = None, description="Type barcode")
    barcode: Optional[str] = Field(serialization_alias="BaCo", default = None, description="Barcode", max_length = 30)
    discount_surcharge_scale: Optional[str] = Field(serialization_alias="CoDs", default = None, description=" Korting-/toeslagschaal", max_length = 8)
    mandated_order_number_or_sales_relation: Optional[bool] = Field(serialization_alias="MnOr", default = None, description="Opdrachtnummer/ref. verkooprelatie verplicht")
    use_invoice_address_for_edi_packing_slip: Optional[bool] = Field(serialization_alias="EDDn", default = None, description="Adressering EDI-pakbon conform EDI-factuur")
    custom_field_a1: Optional[str] = Field(serialization_alias="VaA1", default = None, description="VaA1", max_length = 10)
    custom_field_a2: Optional[str] = Field(serialization_alias="VaA2", default = None, description="VaA2", max_length = 10)
    custom_field_a3: Optional[str] = Field(serialization_alias="VaA3", default = None, description="VaA3", max_length = 10)
    custom_field_a4: Optional[str] = Field(serialization_alias="VaA4", default = None, description="VaA4", max_length = 10)
    custom_field_a5: Optional[str] = Field(serialization_alias="VaA5", default = None, description="VaA5", max_length = 10)
    password: Optional[str] = Field(serialization_alias="Pwrd", default = None, description="Wachtwoord")
    activation_code: Optional[str] = Field(serialization_alias="AtCd", default = None, description=" Activeringscode")
    account_type: Optional[str] = Field(serialization_alias="AcTp", default = None, description="Account type")
    order_processing_method: Optional[ProcessingMethod] = Field(serialization_alias="OrPr", default = None, description="Verwerking order")
    assortment: Optional[str] = Field(serialization_alias="AsGr", default = None, description="Assortiment", max_length = 5)
    allow_deviating_assortment: Optional[bool] = Field(serialization_alias="AsYN", default = None, description="Afwijkend assortiment toestaan")
    OIN_number: Optional[str] = Field(serialization_alias="OINr", default = None, description="OIN nummer", max_length = 40)
    payment_collection_method: Optional[collectionMethod] = Field(serialization_alias="VaDt", default = None, description="Incassowijze")
    e_verbinding_company_id: Optional[str] = Field(serialization_alias="EnId", default = None, description=" Bedrijfs-Id eVerbinding", max_length = 50)
    sales_relation_type: Optional[saleRelationType] = Field(serialization_alias="VaTp", default = None, description="Type verkooprelatie", max_length = 5)
    apply_disposal_fee: Optional[bool] = Field(serialization_alias="ReCo", default = None, description="Verwijderingsbijdrage toepassen")
    EORI_number: Optional[str] = Field(serialization_alias="EORI", default = None, description="EORI-nummer", max_length = 17)

    @model_validator(mode="after")
    def _validate_multiple_of_0_01(self):
        # Validate that all float fields are multiples of 0.01 if not None
        for field_name in ["line_level_discount", "invoice_discount", "credit_restriction", "payment_discount"]:
            value = getattr(self, field_name)
            if value is not None:
                # To accurately check for multiples, use Decimal to avoid float precision errors.
                if Decimal(str(value)) % Decimal("0.01") != Decimal("0"):
                    raise ValueError(f"{field_name} must be a multiple of 0.01")
        return self

    @model_validator(mode="after")
    def validate_multiple_of_1e_10(self):
        for field_name in ["maximum_invoice_amount", "minimum_invoice_amount"]:
            value = getattr(self, field_name)
            if value is not None:
                # Use Decimal for precision, as float math is not reliable at this scale.
                # A value is a multiple if the remainder after division by the step is zero.
                if Decimal(str(value)) % Decimal("1e-10") != Decimal("0"):
                    raise ValueError(f"{field_name} must be a multiple of 1e-10")
            return self

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

#--- nested paylaod structure for put/post/patch ---#
# --- Nested API Payload Structure Classes ---
#rename
PostKnSalesRelationOrgFields = DebtorCreate
PutKnSalesRelationOrgFields = DebtorCreate
#elemnt only contains the field (see DebtorCreate) and as object the 'OrganisationPayload'.
class SalesRelationElement(BaseModel):
    """Element containing sales relation fields and objects"""
    fields: DebtorCreate = Field(serialization_alias="Fields")
    objects: Optional[List[OrganisationPayload]] = Field(default=None, serialization_alias="Objects")

class SalesRelationObject(BaseModel):
    """Object containing sales relation element"""
    element: SalesRelationElement = Field(serialization_alias="Element")

class SalesRelationPayload(BaseModel):
    """
    Top-level payload structure for KnSalesRelationOrg

    Symbolic JSON structure:
    {
        "KnSalesRelationOrg": {
            "Element": {
                "Fields": {
                    "DbId": string,  // Nummer debiteur (required)
                    "Iban": string,   // Voorkeur Iban nummer
                    "BaAc": string,  // Voorkeur bank-/gironummer
                    // ... all other debtor fields
                },
                "Objects": [
                    {
                        "KnOrganisation": { // queue this as 'OrganisationPayload'
                                ...
                            }
                            }
                            ]
                        }
                    }
                ]
            }
        }
    }
    """
    kn_sales_relation_org: SalesRelationObject = Field(serialization_alias="KnSalesRelationOrg")
