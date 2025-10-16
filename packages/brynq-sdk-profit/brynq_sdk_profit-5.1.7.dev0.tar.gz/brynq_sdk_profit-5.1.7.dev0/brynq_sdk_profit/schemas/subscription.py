from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    constr,
    field_validator
)
from typing import Optional, List, Literal, Union
from datetime import date
from .enums import ItemTypeEnum

#--- PUT or POST SCHEMA ---
class PostSubscriptionHeaderFields(BaseModel):
    """
    Pydantic schema for creating or updating a subscription header (FbSubscription Fields).
    part of 'AFAS Verkoop en Orders API'
    https://docs.afas.help/apidoc/nl/Verkoop%20en%20Orders#post-/connectors/FbSubscription
    """

    # All fields are optional to allow flexibility
    subscription_id: Optional[int] = Field(default=None, serialization_alias="SuNr", description="The ID of the subscription (Nummer abonnement)")
    person_id_in_organisation: Optional[str] = Field(default=None, max_length=15, serialization_alias="BcId", description="The ID of the person in the organisation (Organisatie/persoon)")
    contact_id: Optional[int] = Field(default=None, serialization_alias="CtPe", description="The ID of the contact person (Contactpersoon)")
    invoice_deviating_customer: Optional[bool] = Field(default=None, serialization_alias="AltSRe", description="Whether the invoice has an alternative client (Factuur naar afwijkende verkooprelatie)")
    debtor_id: Optional[str] = Field(default=None, max_length=16, serialization_alias="DbId", description="The customer (Verkooprelatie)")
    deviating_contact: Optional[int] = Field(default=None, serialization_alias="CtI1", description="The ID of the deviating contact person (Afwijkende contactpersoon)")
    start_date_subscription: Optional[date] = Field(default=None, serialization_alias="SuSt", description="The start date of the subscription (Begindatum abonnement)")
    invoice_cycle: Optional[Literal['D7', 'I', 'J1', 'M1', 'W1']] = Field(default=None, serialization_alias="VaIn", description="The invoice cycle frequency (Cyclus facturering)")
    start_date_invoice_cycle: Optional[date] = Field(default=None, serialization_alias="DaSt", description="The start date of the invoice cycle (Begindatum factuurcyclus)")
    nr_days_before: Optional[int] = Field(default=None, serialization_alias="DaAm", description="Number of days before invoicing (Aantal dagen vooraf)")
    end_date_subscription: Optional[date] = Field(default=None, serialization_alias="SuEn", description="The end date of the subscription (Einddatum abonnement)")
    currency: Optional[str] = Field(default=None, max_length=3, serialization_alias="CuId", description="The currency code (Valuta)")
    rate: Optional[float] = Field(default=None, serialization_alias="Rate", description="The exchange rate (Valutakoers)")
    cycle_extention: Optional[Literal['D7', 'I', 'J1', 'M1', 'W1']] = Field(default=None, serialization_alias="VaRe", description="The cycle extension period (Cyclusverlenging)")
    date_extention: Optional[date] = Field(default=None, serialization_alias="DaRe", description="The extension date (Datum verlenging)")
    subscription_type: Optional[str] = Field(default=None, max_length=20, serialization_alias="VaSu", description="The type of subscription (Type abonnement)")
    accounting_allocation_code_1: Optional[str] = Field(default=None, max_length=16, serialization_alias="V1Cd", description="Accounting allocation code 1 (Code verbijzonderingsas 1)")
    accounting_allocation_code_2: Optional[str] = Field(default=None, max_length=16, serialization_alias="V2Cd", description="Accounting allocation code 2 (Code verbijzonderingsas 2)")
    accounting_allocation_code_3: Optional[str] = Field(default=None, max_length=16, serialization_alias="V3Cd", description="Accounting allocation code 3 (Code verbijzonderingsas 3)")
    accounting_allocation_code_4: Optional[str] = Field(default=None, max_length=16, serialization_alias="V4Cd", description="Accounting allocation code 4 (Code verbijzonderingsas 4)")
    accounting_allocation_code_5: Optional[str] = Field(default=None, max_length=16, serialization_alias="V5Cd", description="Accounting allocation code 5 (Code verbijzonderingsas 5)")
    payment_terms: Optional[constr(max_length=5)] = Field(default=None, max_length=5, serialization_alias="PaCd", description="Payment terms code (Betaalvoorwaarde)")
    auto_billing: Optional[bool] = Field(default=None, serialization_alias="AuIn", description="Whether to automatically bill (Automatisch factureren)")
    reason_termination: Optional[str] = Field(default=None, max_length=20, serialization_alias="VaRs", description="Reason for termination (Reden beëindiging)")
    no_invoice: Optional[bool] = Field(default=None, serialization_alias="NoIn", description="Whether to not generate invoices (Niet factureren)")
    immediate_invoice_sale: Optional[bool] = Field(default=None, serialization_alias="InDi", description="Whether to invoice sales immediately (Verkoop direct factureren)")
    project_id: Optional[str] = Field(default=None, max_length=15, serialization_alias="PrId", description="The project ID (Project)")
    project_phase: Optional[str] = Field(default=None, max_length=15, serialization_alias="PrSt", description="The project phase (Projectfase)")
    do_not_invoice_sale: Optional[bool] = Field(default=None, serialization_alias="NoSi", description="Whether to not invoice sales (Verkoop niet factureren)")
    payment_collection: Optional[bool] = Field(default=None, serialization_alias="AtIn", description="Whether to enable payment collection (Incasseren)")
    invoice_in_advance: Optional[bool] = Field(default=None, serialization_alias="InAd", description="Whether to invoice in advance (Voorschotfactuur)")
    administration_id: Optional[int] = Field(default=None, serialization_alias="UnFi", description="The administration ID (Administratie)")
    include_vat: Optional[bool] = Field(default=None, serialization_alias="InVa", description="Whether prices include VAT (Prijzen inclusief btw)")
    licence_name: Optional[str] = Field(default=None, max_length=50, serialization_alias="LiNa", description="The license name (Naam licentie)")
    licence_type: Optional[str] = Field(default=None, max_length=20, serialization_alias="VaLs", description="The license type (Type licentie)")
    software_code: Optional[str] = Field(default=None, max_length=20, serialization_alias="VaPe", description="The software code (Programmatuurcode)")
    version: Optional[str] = Field(default=None, max_length=20, serialization_alias="VaVe", description="The version number (Versie)")
    discount_allowed_from_date: Optional[date] = Field(default=None, serialization_alias="LaFr", description="Date from which discount is allowed (Verlaging toegestaan vanaf)")
    order_reference: Optional[str] = Field(default=None, max_length=100, serialization_alias="RfCs", description="Order number or reference (Opdrachtnummer/referentie)")
    exclude_from_consolidated_invoice: Optional[bool] = Field(default=None, serialization_alias="NoCt", description="Whether to exclude from consolidated invoice (Uitsluiten van verzamelfactuur)")
    deviating_bank_account_number: Optional[str] = Field(default=None, max_length=40, serialization_alias="Bankaccount", description="Deviating bank account number (Banknummer afwijkend)")
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
        validate_by_alias=True, # Also allows initializing using the alias (e.g., 'PadAdr').
    )

class PostSubscriptionLineFields(BaseModel):
    """
    Pydantic schema for creating or updating a subscription line item (FbSubscriptionLines Fields).
    """

    # All fields are optional to allow flexibility
    item_type: Optional[ItemTypeEnum] = Field(default=None, serialization_alias="VaIt", description="Item type (Type item)")
    item_code: Optional[str] = Field(default=None, max_length=40, serialization_alias="ItCd", description="Item code (Itemcode)")
    invoice_from: Optional[date] = Field(default=None, serialization_alias="InFr", description="Invoice from date (Factureren vanaf)")

    # Optional fields
    line_number: Optional[int] = Field(default=None, serialization_alias="Id", description="Line ID (Regelnummer)")
    start_date: Optional[date] = Field(default=None, serialization_alias="DaSt", description="Start date (BeginDatum)")
    quantity: Optional[float] = Field(default=None, serialization_alias="Qu", description="Quantity (Aantal)")
    discount_is_percentage: Optional[bool] = Field(default=None, serialization_alias="IsPc", description="Is percentage (Korting op basis van percentage)")
    sale_discount_is_percentage: Optional[bool] = Field(default=None, serialization_alias="IsPS", description="Is sale discount percentage (verkoopkorting op basis van percentage)")
    deviating_price_base_currency: Optional[float] = Field(default=None, serialization_alias="Pric", description="Deviating price in base currency (Afwijkende prijs basisvaluta)")
    discount_base_currency: Optional[str] = Field(default=None, serialization_alias="NFPr", description="Net price (Afwijkende prijs vreemde valuta)")
    discount: Optional[float] = Field(default=None, serialization_alias="Disc", description="Discount in base currency (Korting basisvaluta)")
    net_discount: Optional[str] = Field(default=None, serialization_alias="NFDi", description="Net discount (Korting vreemde valuta)")
    discount_percentage: Optional[float] = Field(default=None, serialization_alias="DcPr", description="Discount percentage (Kortingspercentage)")
    end_date: Optional[date] = Field(default=None, serialization_alias="DaEn", description="End date (Einddatum)")
    sales_price: Optional[float] = Field(default=None, serialization_alias="SaPr", description="Sales price (Afw. verkoopprijs basisvaluta)")
    sales_final_price: Optional[str] = Field(default=None, serialization_alias="SFPr", description="Sales final price (Afw. verkoop prijs vreemde valuta)")
    sales_discount: Optional[float] = Field(default=None, serialization_alias="SaDi", description="Sales discount (Kortingsbedrag verkoop basisvaluta)")
    sales_final_discount: Optional[str] = Field(default=None, serialization_alias="SFDi", description="Sales final discount (Kortingsbedrag verkoop vreemde valuta)")
    discount_price: Optional[float] = Field(default=None, serialization_alias="DiPr", description="Discount price percentage (percentage Korting verkoop)")
    purchase_date: Optional[date] = Field(default=None, serialization_alias="DaPu", description="Purchase date (Aanschafdatum)")
    accounting_code_1: Optional[str] = Field(default=None, serialization_alias="V1Cd", description="Accounting code 1 (Code verbijzonderingsas 1)")
    accounting_code_2: Optional[str] = Field(default=None, serialization_alias="V2Cd", description="Accounting code 2 (Code verbijzonderingsas 2)")
    accounting_code_3: Optional[str] = Field(default=None, serialization_alias="V3Cd", description="Accounting code 3 (Code verbijzonderingsas 3)")
    accounting_code_4: Optional[str] = Field(default=None, serialization_alias="V4Cd", description="Accounting code 4 (Code verbijzonderingsas 4)")
    accounting_code_5: Optional[str] = Field(default=None, serialization_alias="V5Cd", description="Accounting code 5 (Code verbijzonderingsas 5)")
    termination_reason: Optional[str] = Field(default=None, serialization_alias="VaRs", description="Reason for termination (Reden beëindiging)")
    subscription_creditor: Optional[bool] = Field(default=None, serialization_alias="SuCr", description="Subscription creditor (Abonnement crediteren)")
    credit_from: Optional[date] = Field(default=None, serialization_alias="CrFr", description="Credit from date (Crediteren vanaf)")
    credit_si: Optional[bool] = Field(default=None, serialization_alias="CrSi", description="Credit SI (Verkoop crediteren)")
    model_config = ConfigDict(
        serialize_by_alias=True,
        str_strip_whitespace=True,
        str_min_length=0,
        str_max_length=255,
        coerce_numbers_to_str=False,
        extra='allow',  # Allow extra fields for subscription lines
        frozen=True,
        allow_inf_nan=False,
        ser_json_timedelta='iso8601',
        ser_json_bytes='base64',
        validate_default=True,
        use_enum_values=True,
        # Why: These two settings replace the deprecated 'populate_by_name=True'.
        validate_by_name=True,  # Allows initializing the model using Python field names (e.g., 'is_postal_address').
        validate_by_alias=True, # Also allows initializing using the alias (e.g., 'PadAdr').
    )

class PutSubscriptionHeaderFields(PostSubscriptionHeaderFields):
    """Pydantic schema for updating a subscription header"""

class PutSubscriptionLineFields(PostSubscriptionLineFields):
    """Pydantic schema for updating a subscription line"""

# --- Nested API Payload Structure Classes ---
class SubscriptionLineElement(BaseModel):
    """Element containing subscription line fields"""
    fields: PostSubscriptionLineFields = Field(serialization_alias="Fields")

class SubscriptionLinesObject(BaseModel):
    """Object containing subscription line elements"""
    element: List[SubscriptionLineElement] = Field(serialization_alias="Element")

class SubscriptionLinesSchema(BaseModel):
    """Schema for subscription lines"""
    fb_subscription_lines: SubscriptionLinesObject = Field(serialization_alias="FbSubscriptionLines")

class SubscriptionElement(BaseModel):
    """Element containing subscription header fields and objects"""
    fields: PostSubscriptionHeaderFields = Field(serialization_alias="Fields")
    objects: Optional[List[SubscriptionLinesSchema]] = Field(default=None, serialization_alias="Objects")

class SubscriptionObject(BaseModel):
    """Object containing subscription element"""
    element: SubscriptionElement = Field(serialization_alias="Element")

class SubscriptionPayload(BaseModel):
    """
    Top-level payload structure matching the FbSubscription API endpoint

    Symbolic JSON structure:
    {
        "FbSubscription": {
            "Element": {
                "Fields": {
                    "SuNr": integer,  // Nummer abonnement
                    "BcId": string,   // Organisatie/persoon
                    // ... all other subscription header fields
                },
                "Objects": [
                    {
                        "FbSubscriptionLines": {
                            "Element": [
                                {
                                    "Fields": {
                                        "VaIt": enum,  // Type item
                                        "ItCd": string,  // Itemcode
                                        "Id": integer,  // Regelnummer
                                        // ... all other line fields
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
    fb_subscription: SubscriptionObject = Field(serialization_alias="FbSubscription")
