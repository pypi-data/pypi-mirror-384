#general imports
from typing import Optional, List, Union, Literal
from datetime import date
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
    MaritalStatusEnum, PreferredMediumEnum, AmountOfEmployeesEnum
)

#--- PUT or POST SCHEMA ---
class PersonElementBase(BaseModel):
    """Base schema for employee element fields - shared across address, bank account, and person schemas"""
    # Required Fields
    auto_number: Optional[bool] = Field(default=None, alias="AutoNum", description="Autonummering")
    equals_mail_address: Optional[Union[bool, Literal["0", "1"]]] = Field(default=None, alias="PadAdr", description="Postadres is adres")
    # if autonumber is False, person
    # _id is required
    person_id: Optional[str] = Field(default=None, max_length=15, alias="BcCo", description="Nummer", examples=["1234567890", "9876543210", "1122334455"])
    match_person: Optional[MatchPersonEnum] = Field(default=None, alias="MatchPer", description="Persoon vergelijken op")

    employee_id: Optional[int] = Field(default=None, alias="BcId", description="Organisatie persoon ID", examples=list(range(1,10)))
    add_to_portal: Optional[bool] = Field(default=None, alias="AddToPortal", description="Persoon toegang geven tot afgeschermde deel van de portal(s)", examples=[True, False])

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
    def _validate_autonum_vs_person_id(self):
        pid_present = self.person_id is not None
        auto_number_present = self.auto_number is not None

        # Both may be omitted, either may be supplied, but not both
        if pid_present and auto_number_present:
            raise ValueError(
                "Only one of 'auto_number' or 'person_id' may be provided (not both)."
            )
        return self

class PostKnPersonFieldsSchema(PersonElementBase):
    """Pydantic schema for creating or updating a person's information"""
    # Optional Fields
    search_name: Optional[str] = Field(default=None, max_length=10, alias="SeNm", description="Zoeknaam", examples=["John", "Jane", "Ruben", "Corinde", "Cody"])
    preferred_name: Optional[str] = Field(default=None, max_length=80, alias="CaNm", description="Roepnaam", examples=["John", "Jane", "Ruben", "Corinde", "Cody"])
    first_name: Optional[str] = Field(default=None, max_length=50, alias="FiNm", description="Voornaam", examples=["John", "Jane", "Ruben", "Corinde", "Cody"])
    initials: Optional[str] = Field(default=None, max_length=15, alias="In", description="Voorletters", examples=["J", "J.", "JD", "R.A.J.", "R.", "C.C.", "CC", "C.G."])
    prefix: Optional[str] = Field(default=None, max_length=15, alias="Is", description="Voorvoegsel", examples=["van", "van der", "van de", "de"])
    last_name: Optional[str] = Field(default=None, max_length=80, alias="LaNm", description="Achternaam", examples=["Doe", "Smith", "Johnson", "Williams", "Brown", "Swarts"])
    separate_birth_name: Optional[bool] = Field(default=None, alias="SpNm", description="Geboortenaam apart vastleggen", examples=[True, False])
    birth_name_prefix: Optional[str] = Field(default=None, max_length=15, alias="IsBi", description="Voorv. geb.naam", examples=["van", "van der", "van de", "de"])
    birth_name: Optional[str] = Field(default=None, max_length=80, alias="NmBi", description="Geboortenaam", examples=["Doe", "Smith", "Johnson", "Williams", "Brown", "Swarts"])
    partner_prefix: Optional[str] = Field(default=None, max_length=15, alias="IsPa", description="Voorvoegsel partner", examples=["van", "van der", "van de", "de"])
    partner_name: Optional[str] = Field(default=None, max_length=80, alias="NmPa", description="Geb.naam partner", examples=["Doe", "Smith", "Johnson", "Williams", "Brown", "Swarts"])
    name_use: Optional[NameUseEnum] = Field(default=None, alias="ViUs", description="Naamgebruik", examples=list(NameUseEnum))
    gender: Optional[GenderEnum] = Field(default=None, alias="ViGe", description="Geslacht", examples=list(GenderEnum))
    nationality: Optional[NationalityEnum] = Field(default=None, alias="PsNa", description="Nationaliteit", examples=list(NationalityEnum))
    # TODO: no other date earlier than birhtdate.
    date_of_birth: Optional[Union[date, Literal[""]]] = Field(default=None, alias="DaBi", description="Geboortedatum", examples=[date(1990, 1, 1), date(2001, 1, 30), date(1989, 4, 2)])

    #TODO: make sure make sure birth place and country are consistent using city.get()
    country_of_birth: Optional[str] = Field(default=None, max_length=3, alias="CoBi", description="Geboorteland", examples=["NL", "B","D"])
    city_of_birth: Optional[str] = Field(default=None, max_length=50, alias="RsBi", description="Geboorteplaats", examples=["Amsterdam", "Rotterdam", "Utrecht", "Gouda"])

    bsn: Optional[str] = Field(default=None, max_length=25, alias="SoSe", description="BSN", examples=["264526673", "645281682", "269484127", "356573758", "255369608"])
    personal_id: Optional[str] = Field(default=None, max_length=10, alias="Sdla", description="Id-nummer", examples=["1234567890", "0987654321", "9087654321"])
    marital_status: Optional[MaritalStatusEnum] = Field(default=None, alias="ViCs", description="Burgerlijke staat", examples=list(MaritalStatusEnum))

    date_of_marriage: Optional[Union[date, Literal[""]]] = Field(default=None, alias="DaMa", description="Huwelijksdatum", examples=[date(2010, 1, 1), date(2011, 1, 30), date(2012, 4, 2)])
    #TODO divorce date later than marriage date
    date_of_divorce: Optional[Union[date, Literal[""]]] = Field(default=None, alias="DaDi", description="Datum scheiding", examples=[date(2015, 1, 1), date(2016, 1, 30), date(2017, 4, 2)])
    #TODO: death date later than other personal datess
    date_of_death: Optional[Union[date, Literal[""]]] = Field(default=None, alias="DaDe", description="Overlijdensdatum", examples=[date(2020, 1, 1), date(2021, 1, 30), date(2022, 4, 2)])

    #TODO: validate titles on get.title()
    title: Optional[str] = Field(default=None, alias="TtId", description="Titel/aanhef")
    second_title: Optional[str] = Field(default=None, alias="TtEx", description="Tweede titel")
    salutation: Optional[str] = Field(default=None, alias="LeHe", description="Briefaanhef")

    #TODO: private != work
    phone_work: Optional[str] = Field(default=None,alias="TeNr",description="Telefoonnr. werk",examples=["0318-149621", "020-1234567", "010-9876543"])
    phone_private: Optional[str] = Field(default=None,alias="TeN2",description="Telefoonnr. privé",examples=["0318-149621", "06-12345678", "030-7654321"])
    fax_work: Optional[str] = Field(default=None, alias="FaNr", description="Fax werk", examples=["+31-20-123-4567", "0031-20-123-4567", "0201234567", "+311821234567"])
    mobile_work: Optional[str] = Field(default=None, alias="MbNr", description="Mobiel werk", examples=["06-12345678", "06-98765432", "06-55555555"])
    mobile_private: Optional[str] = Field(default=None, alias="MbN2", description="Mobiel privé", examples=["06-12345678", "06-98765432", "06-55555555"])
    mail_work: Optional[EmailStr] = Field(default=None, alias="EmAd", description="E-mail werk", examples=["ruben.swarts@brynq.com", "bert@gmail.com", "gandalf@email.nl"])
    mail_private: Optional[EmailStr] = Field(default=None, alias="EmA2", description="E-mail privé", examples=["ruben.swarts@brynq.com", "bert@gmail.com", "gandalf@email.nl"])
    website: Optional[AnyUrl] = Field(default=None, alias="HoPa", description="Website")
    correspondence: Optional[bool] = Field(default=None, alias="Corr", description="Correspondentie", examples=[True, False])
    preferred_medium: Optional[PreferredMediumEnum] = Field(default=None, alias="ViMd", description="Voorkeursmedium", examples=list(PreferredMediumEnum))
    remarks: Optional[bytes] = Field(default=None, alias="Re", description="Opmerking")
    status: Optional[str] = Field(default=None, max_length=20, alias="StId", description="Status", examples=["Actief", "Inactief", "Geschorst"])
    social_network: Optional[AnyUrl] = Field(default=None, alias="SocN", description="Sociale netwerken")
    crib_number: Optional[str] = Field(default=None, max_length=9, alias="CrIb", description="CRIB nummer", examples=["123456789", "987654321", "456789123"])
    facebook: Optional[str] = Field(default=None, alias="Face", description="Facebook", examples=["jan.jansen", "piet.bakker", "klaas.visser"])
    linkedin: Optional[str] = Field(default=None, alias="Link", description="LinkedIn", examples=["jan-jansen", "piet-bakker", "klaas-visser"])
    twitter: Optional[str] = Field(default=None, alias="Twtr", description="X (voorheen Twitter)", examples=["@janjansen", "@pietbakker", "@klaasvisser"])
    language: Optional[str] = Field(default=None, max_length=3, alias="LgId", description="Taal", examples=["NL", "B", "D"])
    law_country: Optional[str] = Field(default=None, max_length=2, alias="CoLw", description="Land wetgeving", examples=["NL", "B", "D"])
    kvk_number: Optional[str] = Field(default=None, max_length=30, alias="CcNr", description="KvK-nummer", examples=["12345678", "87654321", "11223344"])
    kvk_date: Optional[Union[date, Literal[""]]] = Field(default=None, alias="CcDa", description="Datum KvK")
    branch_number: Optional[str] = Field(default=None, max_length=30, alias="BrNr", description="Vestigingsnummer", examples=["000012345678", "000087654321", "000011223344"])
    tax_number: Optional[str] = Field(default=None, max_length=9, alias="FiNr", description="Fiscaalnummer", examples=["123456789", "987654321", "456789123"])
    amount_of_employees: Optional[AmountOfEmployeesEnum] = Field(default=None, alias="EmAm", description="Aantal medewerkers", examples=list(AmountOfEmployeesEnum))
    sbi_code: Optional[str] = Field(default=None, max_length=10, alias="SBIc", description="SBI-code", examples=["62010", "62020", "62030"])
    # examples inside .example folder:
    file_id: Optional[str] = Field(default=None, max_length=32, alias="FileId", description="Bestand")
    file_name: Optional[str] = Field(default=None, alias="FileName", description="Bestandsnaam")
    file_stream: Optional[bytes] = Field(default=None, alias="FileStream", description="Afbeelding")
    email_portal: Optional[str] = Field(default=None, alias="EmailPortal", description="E-mail toegang", examples=["jan@bedrijf.nl", "piet@bedrijf.nl", "klaas@bedrijf.nl"])

# --- Nested API Payload Structure Classes ---
class UploadConfig(BaseModel):
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
class PersonContactAutRoleElement(UploadConfig):
    """Element containing person contact authorization role fields"""
    fields: dict = Field(alias="Fields")  # Placeholder for ContactAutRoleUpdateSchema fields

class PersonContactAutRoleObject(UploadConfig):
    """Object containing person contact authorization role elements"""
    element: Optional[List[PersonContactAutRoleElement]] = Field(default=None, alias="Element")

class PersonContactAutRoleSchema(UploadConfig):
    """Schema for person contact authorization role"""
    kn_contact_aut_role: PersonContactAutRoleObject = Field(alias="KnContactAutRole")

class PersonBankAccountElement(UploadConfig):
    """Element containing person bank account fields"""
    fields: dict = Field(alias="Fields")  # Placeholder for PostBankAccountSchema fields

class PersonBankAccountObject(UploadConfig):
    """Object containing person bank account elements"""
    element: Optional[List[PersonBankAccountElement]] = Field(default=None, alias="Element")

class PersonBankAccountSchema(UploadConfig):
    """Schema for person bank account"""
    kn_bank_account: PersonBankAccountObject = Field(alias="KnBankAccount")

class PersonAddressElement(UploadConfig):
    """Element containing person address fields"""
    fields: dict = Field(alias="Fields")  # Placeholder for PutBasicAddressAdrSchema fields

class PersonAddressObject(UploadConfig):
    """Object containing person address elements"""
    element: Optional[List[PersonAddressElement]] = Field(default=None, alias="Element")

class PersonAddressSchema(UploadConfig):
    """Schema for person address"""
    kn_basic_address_adr: PersonAddressObject = Field(alias="KnBasicAddressAdr")

class PersonPostalAddressSchema(UploadConfig):
    """Schema for person postal address"""
    kn_basic_address_pad: PersonAddressObject = Field(alias="KnBasicAddressPad")

class PersonNestedElement(UploadConfig):
    """Element containing nested person fields only"""
    fields: PostKnPersonFieldsSchema = Field(alias="Fields")

class PersonNestedObject(UploadConfig):
    """Object containing nested person element"""
    element: Optional[List[PersonNestedElement]] = Field(default=None, alias="Element")

class PersonNestedSchema(UploadConfig):
    """Schema for nested person within contact"""
    kn_person: PersonNestedObject = Field(alias="KnPerson")

class PersonContactElement(UploadConfig):
    """Element containing person contact fields"""
    fields: dict = Field(alias="Fields")  # Contact fields
    objects: Optional[List[Union[PersonAddressSchema, PersonPostalAddressSchema, "PersonNestedSchema"]]] = Field(default=None, alias="Objects")

class PersonContactObject(UploadConfig):
    """Object containing person contact elements"""
    element: Optional[List[PersonContactElement]] = Field(default=None, alias="Element")

class PersonContactSchema(UploadConfig):
    """Schema for person contact"""
    kn_contact: PersonContactObject = Field(alias="KnContact")

class PersonElement(UploadConfig):
    """Element containing person fields and objects"""
    fields: PostKnPersonFieldsSchema = Field(alias="Fields")
    objects: Optional[List[Union[PersonContactAutRoleSchema, PersonBankAccountSchema, PersonAddressSchema, PersonPostalAddressSchema, PersonContactSchema]]] = Field(default=None, alias="Objects")
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

class PersonObject(UploadConfig):
    """Object containing person element"""
    element: PersonElement = Field(alias="Element")

class PersonPayload(UploadConfig):
    """
    Top-level payload structure matching the KnPerson API endpoint

    Symbolic JSON structure:
    {
        "KnPerson": {
            "Element": {
                "Fields": {
                    "PadAdr": boolean,  // Postadres is adres
                    "AutoNum": boolean,  // Autonummering
                    "MatchPer": enum,    // Persoon vergelijken op
                    "BcId": integer,     // Organisatie/persoon (intern)
                    "BcCo": string,      // Nummer
                    // ... all other person fields
                },
                "Objects": [
                    {
                        "KnContactAutRole": {
                            "Element": [
                                {
                                    "Fields": {
                                        "AutRoleDs": string  // Autorisatierol
                                    }
                                }
                            ]
                        }
                    },
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
                                                            // ... nested person fields only
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
    kn_person: PersonObject = Field(alias="KnPerson")

#--- GET SCHEMA ---
class GetPerson(BrynQPanderaDataFrameModel):
    """Schema for person get"""
    person_id: Series[str] = pa.Field(coerce=True, nullable=False, description="Nummer", alias="BcCo")
    person_type: Series[str] = pa.Field(coerce=True, nullable=True, description="Soort basic contact", alias="Type")
    search_name: Series[str] = pa.Field(coerce=True, nullable=True, description="Zoeknaam", alias="SearchName")
    name: Series[str] = pa.Field(coerce=True, nullable=True, description="Naam", alias="Name")
    address_line1: Series[str] = pa.Field(coerce=True, nullable=True, description="Adresregel 1 (straat - huisnr)", alias="AdressLine1")
    address_line3: Series[str] = pa.Field(coerce=True, nullable=True, description="Adresregel 3 (postc - wpl)", alias="AdressLine3")
    address_line4: Series[str] = pa.Field(coerce=True, nullable=True, description="Adresregel 4 (land)", alias="AdressLine4")
    phone_work: Series[str] = pa.Field(coerce=True, nullable=True, description="Telefoonnr. werk", alias="TelWork")
    mail_work: Series[str] = pa.Field(coerce=True, nullable=True, description="E-mail werk", alias="MailWork")
    website: Series[str] = pa.Field(coerce=True, nullable=True, description="Website", alias="Homepage")
    remarks: Series[str] = pa.Field(coerce=True, nullable=True, description="Opmerking", alias="Note")
    kvk_number: Series[str] = pa.Field(coerce=True, nullable=True, description="KvK-nummer", alias="ChOfCommNr")
    birth_date: Series[str] = pa.Field(coerce=True, nullable=True, description="Geboortedatum", alias="DateBirth")
    bsn: Series[str] = pa.Field(coerce=True, nullable=True, description="BSN", alias="BSN")

    class _Annotation:
        primary_key = "person_id"
        foreign_keys = {}
