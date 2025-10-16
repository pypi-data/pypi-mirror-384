#general imports
from typing import Optional, List, Union
from datetime import date
#pydantic imports
from pydantic import BaseModel, Field, EmailStr, AnyUrl, model_validator
from pydantic.config import ConfigDict
#local imports
from .enums import MatchOrganisationEnum, LegalStructureEnum, BrancheEnum, PreferredMediumEnum, AmountOfEmployeesEnum

#--- PUT or POST SCHEMA ---
class OrganisationElementBase(BaseModel):
    """Base schema for employee element fields - shared across address, bank account, and person schemas"""
    # Required Fields
    equals_mail_address: Optional[bool] = Field(default=None, serialization_alias="PadAdr", description="Postadres is adres")
    auto_number: Optional[bool] = Field(default=None, serialization_alias="AutoNum", description="Autonummering")

    # if autonumber is False, organisation_id is required
    organisation_id: Optional[str] = Field(default=None, max_length=15, serialization_alias="BcCo", description="Nummer", examples=["1234567890", "9876543210", "1122334455"])
    match_organisation: Optional[MatchOrganisationEnum] = Field(default=None, serialization_alias="MatchOga", description="Organisatie vergelijken op")

    organisation_person_id: Optional[int] = Field(default=None, serialization_alias="BcId", description="Organisatie persoon ID", examples=list(range(1,10)))

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

    #validations
    @model_validator(mode="after")
    def _validate_autonum_vs_organisation_id(self):
        pid_present = self.organisation_id is not None
        if self.auto_number == pid_present:
            # (True,True) or (False,False) are both invalid per business rule
            raise ValueError(
                "Exactly one of {auto_number=True, organisation_id provided} must be set: "
                "provide organisation_id when auto_number=False, omit it when auto_number=True."
            )
        return self

class PostKnOrganisationFields(OrganisationElementBase):
    """Pydantic schema for creating or updating an organisation's information"""
    # Required Fields; TODO figure out exactly WHEN it is required, for now  set optional to just test the API. All these fields are denoted as required in the API documentation, but they are only required circumstantially.
    name_organisation: Optional[str] = Field(default=None, serialization_alias="Nm", description="The name of the organisation (Naam)")
    equals_mail_address: Optional[bool] = Field(default=None, serialization_alias="PadAdr", description="Whether the address is a postal address (Postadres is adres)")
    auto_number: Optional[bool] = Field(default=None, serialization_alias="AutoNum", description="Whether the number is automatically generated (Autonummering)")
    organisation_id: Optional[str] = Field(default=None, max_length=15, serialization_alias="BcCo", description="The ID of the organisation (Nummer)") #depends on autonumbering
    match_organisation: Optional[MatchOrganisationEnum] = Field(default=None, serialization_alias="MatchOga", description="Organisatie vergelijken op (0=Zoek op BcCo, 1=KvK-nummer, 2=Fiscaal nummer, 3=Naam, 4=Adres, 5=Postadres, 6=Altijd nieuw toevoegen)")
    person_id_in_organisation: Optional[int] = Field(default=None, serialization_alias="BcId", description="The ID of the person in the organisation (Organisatie/persoon (intern))")

    # Optional Fields
    search_name: Optional[str] = Field(default=None, max_length=10, serialization_alias="SrNm", description="The search name of the organisation (Zoeknaam)")
    legal_structure: Optional[LegalStructureEnum] = Field(default=None, serialization_alias="ViLe", description="The legal structure of the organisation (Rechtsvorm)")
    branche: Optional[BrancheEnum] = Field(default=None, serialization_alias="ViLb", description="The branche of the organisation (Branche)")
    kvk_number: Optional[str] = Field(default=None, max_length=30, serialization_alias="CcNr", description="The KvK number of the organisation (KvK-nummer)")
    kvk_date: Optional[date] = Field(default=None, serialization_alias="CcDa", description="Datum KvK")
    branche_number: Optional[str] = Field(default=None, max_length=30, serialization_alias="BrNr", description="Vestigingsnummer")
    registered_name: Optional[str] = Field(default=None, max_length=80, serialization_alias="NmRg", description="Naam (statutair)")
    registered_office: Optional[str] = Field(default=None, max_length=80, serialization_alias="RsRg", description="Vestiging (statutair)")
    courtesy_title: Optional[str] = Field(default=None, max_length=3, serialization_alias="TtId", description="Titel/aanhef")
    salutation: Optional[str] = Field(default=None, serialization_alias="LeHe", description="Briefaanhef")
    organisational_unit: Optional[str] = Field(default=None, max_length=10, serialization_alias="OuId", description="Organisatorische eenheid")
    phone_work: Optional[str] = Field(default=None, serialization_alias="TeNr", description="Telefoonnr. werk")
    fax_work: Optional[str] = Field(default=None, serialization_alias="Fanr", description="Fax werk")
    mobile_work: Optional[str] = Field(default=None, max_length=20, serialization_alias="MbNr", description="Mobiel werk")
    mail_work: Optional[EmailStr] = Field(default=None, serialization_alias="EmAd", description="E-mail werk")
    website: Optional[AnyUrl] = Field(default=None, serialization_alias="HoPa", description="Website")
    correspondence: Optional[bool] = Field(default=None, serialization_alias="Corr", description="Correspondentie")
    preferred_medium: Optional[PreferredMediumEnum] = Field(default=None, serialization_alias="ViMd", description="Voorkeursmedium", examples=list(PreferredMediumEnum))
    remarks: Optional[bytes] = Field(default=None, serialization_alias="Re", description="Opmerking")
    tax_identification_number: Optional[str] = Field(default=None, max_length=9, serialization_alias="FiNr", description="Fiscaal nummer")
    status: Optional[str] = Field(default=None, max_length=20, serialization_alias="StId", description="Status")
    amount_of_employees: Optional[AmountOfEmployeesEnum] = Field(default=None, serialization_alias="EmAm", description="Aantal medewerkers", examples=list(AmountOfEmployeesEnum))
    social_network: Optional[AnyUrl] = Field(default=None, serialization_alias="SocN", description="Sociale netwerken")
    crib_number: Optional[str] = Field(default=None, max_length=9, serialization_alias="CrIb", description="CRIB nummer")
    facebook: Optional[str] = Field(default=None, serialization_alias="Face", description="Facebook", examples=["jan.jansen", "piet.bakker", "klaas.visser"])
    linkedin: Optional[str] = Field(default=None, serialization_alias="Link", description="LinkedIn", examples=["jan-jansen", "piet-bakker", "klaas-visser"])
    twitter: Optional[str] = Field(default=None, serialization_alias="Twtr", description="X (voorheen Twitter)", examples=["@janjansen", "@pietbakker", "@klaasvisser"])
    language: Optional[str] = Field(default=None, max_length=3, serialization_alias="LgId", description="Taal", examples=["NL", "B", "D"])
    external_key: Optional[str] = Field(default=None, max_length=40, serialization_alias="XpRe", description="Extern key")
    sbi_code: Optional[str] = Field(default=None, max_length=10, serialization_alias="SBIc", description="SBI-code")
    department: Optional[str] = Field(default=None, max_length=15, serialization_alias="BcPa", description="Onderdeel van organisatie")
    file_id: Optional[str] = Field(default=None, max_length=32, serialization_alias="FileId", description="Bestand")
    file_name: Optional[str] = Field(default=None, serialization_alias="FileName", description="Bestandsnaam")
    file_stream: Optional[bytes] = Field(default=None, serialization_alias="FileStream", description="Afbeelding")

    #validations
    # TODO: Re-enable this validation once we determine exact requirements
    # @model_validator(mode="after")
    # def _validate_autonum_vs_organisation_id(self):
    #     pid_present = self.organisation_id is not None
    #     if self.auto_number == pid_present:
    #         # (True,True) or (False,False) are both invalid per business rule
    #         raise ValueError(
    #             "Exactly one of {auto_number=True, organisation_id provided} must be set: "
    #             "provide organisation_id when auto_number=False, omit it when auto_number=True."
    #         )
    #     return self

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
        validate_by_name=True,  # Allows initializing the model using Python field names.
        validate_by_alias=True, # Also allows initializing using the serialization_alias.
    )

class PutKnOrganisationFieldsSchema(PostKnOrganisationFields):
    """Pydantic schema for updating an organisation"""

# --- Nested API Payload Structure Classes ---
class OrganisationBankAccountElement(BaseModel):
    """Element containing organisation bank account fields"""
    fields: dict = Field(serialization_alias="Fields")  # Placeholder for bank account fields

class OrganisationBankAccountObject(BaseModel):
    """Object containing organisation bank account elements"""
    element: Optional[List[OrganisationBankAccountElement]] = Field(default=None, serialization_alias="Element")

class OrganisationBankAccountSchema(BaseModel):
    """Schema for organisation bank account"""
    kn_bank_account: OrganisationBankAccountObject = Field(serialization_alias="KnBankAccount")

class OrganisationAddressElement(BaseModel):
    """Element containing organisation address fields"""
    fields: dict = Field(serialization_alias="Fields")  # Placeholder for address fields

class OrganisationAddressObject(BaseModel):
    """Object containing organisation address elements"""
    element: Optional[List[OrganisationAddressElement]] = Field(default=None, serialization_alias="Element")

class OrganisationAddressSchema(BaseModel):
    """Schema for organisation address"""
    kn_basic_address_adr: OrganisationAddressObject = Field(serialization_alias="KnBasicAddressAdr")

class OrganisationPostalAddressSchema(BaseModel):
    """Schema for organisation postal address"""
    kn_basic_address_pad: OrganisationAddressObject = Field(serialization_alias="KnBasicAddressPad")

class OrganisationNestedPersonElement(BaseModel):
    """Element containing nested person fields"""
    fields: dict = Field(serialization_alias="Fields")  # Placeholder for nested person fields

class OrganisationNestedPersonObject(BaseModel):
    """Object containing nested person element"""
    element: Optional[List[OrganisationNestedPersonElement]] = Field(default=None, serialization_alias="Element")

class OrganisationNestedPersonSchema(BaseModel):
    """Schema for nested person within organisation contact"""
    kn_person: OrganisationNestedPersonObject = Field(serialization_alias="KnPerson")

class OrganisationContactElement(BaseModel):
    """Element containing organisation contact fields"""
    fields: dict = Field(serialization_alias="Fields")  # Contact fields
    objects: Optional[List[Union[OrganisationAddressSchema, OrganisationPostalAddressSchema, OrganisationNestedPersonSchema]]] = Field(default=None, serialization_alias="Objects")

class OrganisationContactObject(BaseModel):
    """Object containing organisation contact elements"""
    element: Optional[List[OrganisationContactElement]] = Field(default=None, serialization_alias="Element")

class OrganisationContactSchema(BaseModel):
    """Schema for organisation contact"""
    kn_contact: OrganisationContactObject = Field(serialization_alias="KnContact")

class OrganisationElement(BaseModel):
    """Element containing organisation fields and objects"""
    fields: PostKnOrganisationFields = Field(serialization_alias="Fields")
    objects: Optional[List[Union[OrganisationBankAccountSchema, OrganisationAddressSchema, OrganisationPostalAddressSchema, OrganisationContactSchema]]] = Field(default=None, serialization_alias="Objects")

class OrganisationObject(BaseModel):
    """Object containing organisation element"""
    element: OrganisationElement = Field(serialization_alias="Element")

class OrganisationPayload(BaseModel):
    """
    Top-level payload structure matching the KnOrganisation API endpoint

    Symbolic JSON structure:
    {
        "KnOrganisation": {
            "Element": {
                "Fields": {
                    "PadAdr": boolean,  // Postadres is adres
                    "AutoNum": boolean,  // Autonummering
                    "MatchOga": enum,  // Organisatie vergelijken op
                    "BcId": integer,  // Organisatie/persoon (intern)
                    "BcCo": string,  // Nummer
                    "Nm": string,  // Naam
                    // ... all other organisation fields
                },
                "Objects": [
                    {
                        "KnBankAccount": {
                            "Element": [
                                {
                                    "Fields": {
                                        // ... bank account fields
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "KnBasicAddressAdr": {
                            "Element": [
                                {
                                    "Fields": {
                                        // ... address fields
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "KnBasicAddressPad": {
                            "Element": [
                                {
                                    "Fields": {
                                        // ... postal address fields
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "KnContact": {
                            "Element": [
                                {
                                    "Fields": {
                                        // ... contact fields
                                    },
                                    "Objects": [
                                        {
                                            "KnBasicAddressAdr": {
                                                "Element": [
                                                    {
                                                        "Fields": {
                                                            // ... address fields
                                                        }
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "KnBasicAddressPad": {
                                                "Element": [
                                                    {
                                                        "Fields": {
                                                            // ... postal address fields
                                                        }
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "KnPerson": {
                                                "Element": [
                                                    {
                                                        "Fields": {
                                                            // ... nested person fields
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }
    }
    """
    kn_organisation: OrganisationObject = Field(serialization_alias="KnOrganisation")
