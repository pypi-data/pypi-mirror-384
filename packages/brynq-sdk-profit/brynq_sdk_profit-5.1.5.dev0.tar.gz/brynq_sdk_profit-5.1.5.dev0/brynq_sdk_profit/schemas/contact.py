from pydantic import BaseModel, Field, EmailStr, AnyUrl
from typing import Union
from pydantic.config import ConfigDict
from typing import Optional, List
#local imports
from .enums import ContactType, FunctionType, PreferredMediumEnum

#fields: base schemas for contact updates (puts)
class PutContactSchema(BaseModel):
    """
    put /connectors/KnContact
    https://docs.afas.help/apidoc/nl/Organisaties%20en%20personen#put-/connectors/KnContact
    https://help.afas.nl/help/NL/SE/App_Conect_UpdDsc_030.htm
    KnContact Pydantic schema for contact updates based on the contact fields specification.
    These are all the fields belonging specifically to a contact.
    subschemas include  KnContactAutRole,  KnBasicAddressAdr,  KnBasicAddressPad"""

    # Required Fields
    contact_id: int = Field(serialization_alias="CdId", description="Contact")

    # Optional Fields
    organisation_code: Optional[str] = Field(default=None, max_length=15, serialization_alias="BcCoOga", description="Code organisatie")
    person_code: Optional[str] = Field(default=None, max_length=15, serialization_alias="BcCoPer", description="Code persoon")
    is_postal_address: Optional[bool] = Field(default=None, serialization_alias="PadAdr", description="Postadres is adres")
    department: Optional[str] = Field(default=None, serialization_alias="ExAd", description="Afdeling")

    # Enum fields
    contact_type: Optional[ContactType] = Field(default=None, serialization_alias="ViKc", description="Soort contact AFD = Afdeling bij organisatie; PRS = Persoon bij organisatie; AFL = Afleveradres; ORG = Organisatie; PER = Persoon")
    function: Optional[FunctionType] = Field(default=None, serialization_alias="ViFu", description="Functie 100 = Directeur; 200 = Administratief medewerker; 300 = Hoofd salarisadministratie")
    preferred_medium: Optional[PreferredMediumEnum] = Field(default=None, serialization_alias="ViMd", description="Voorkeursmedium EMA = E-mail; FAX = Fax; PRS = Persoonlijk; PST = Post; TEL = Telefoonnr.")

    # Contact information fields
    function_on_business_card: Optional[str] = Field(default=None, max_length=50, serialization_alias="FuDs", description="Functie op visitekaart")
    correspondence: Optional[bool] = Field(default=None, serialization_alias="Corr", description="Correspondentie")
    phone_number_work: Optional[str] = Field(default=None, serialization_alias="TeNr", description="Telefoonnr. werk")
    fax_work: Optional[str] = Field(default=None, serialization_alias="FaNr", description="Fax werk")
    mobile_number_work: Optional[str] = Field(default=None, max_length=20, serialization_alias="MbNr", description="Mobiel werk")
    email_work: Optional[EmailStr] = Field(default=None, serialization_alias="EmAd", description="E-mail werk")
    website: Optional[AnyUrl] = Field(default=None, serialization_alias="HoPa", description="Website")
    reaction: Optional[Union[bytes, str]] = Field(default=None, serialization_alias="Re", description="Toelichting")
    blocked: Optional[bool] = Field(default=None, serialization_alias="Bl", description="Geblokkeerd")
    attention_line: Optional[str] = Field(default=None, serialization_alias="AtLn", description="T.a.v. regel")
    salutation: Optional[str] = Field(default=None, serialization_alias="LeHe", description="Briefaanhef")
    social_network: Optional[AnyUrl] = Field(default=None, serialization_alias="SocN", description="Sociale netwerken")
    facebook: Optional[str] = Field(default=None, serialization_alias="Face", description="Facebook")
    linkedin: Optional[str] = Field(default=None, serialization_alias="Link", description="LinkedIn")
    twitter: Optional[str] = Field(default=None, serialization_alias="Twtr", description="X (voorheen Twitter)")
    add_to_portal: Optional[bool] = Field(default=None, serialization_alias="AddToPortal", description="Persoon toegang geven tot afgeschermde deel van de portal(s)")
    email_portal: Optional[str] = Field(default=None, serialization_alias="EmailPortal", description="E-mail toegang")

    model_config = ConfigDict(serialize_by_alias=True,
                              str_strip_whitespace=True,
                              str_min_length=0,
                              str_max_length=255,
                              coerce_numbers_to_str=False,
                              extra='allow',
                              frozen=True,
                              allow_inf_nan=False,
                              ser_json_timedelta='iso8601',
                              ser_json_bytes='base64',
                              validate_default=True,
                              use_enum_values=True,
                              )

# Contact authorization role update schema
class ContactAutRoleUpdateSchema(BaseModel):
    """
    Schema for updating contact authorization roles
    """
    authorization_role_description: Optional[str] = Field(default=None, max_length=80, serialization_alias="AutRoleDs", description="Autorisatierol")

    model_config = ConfigDict(serialize_by_alias=True,
                              str_strip_whitespace=True,
                              str_min_length=0,
                              str_max_length=255,
                              coerce_numbers_to_str=False,
                              extra='allow',
                              frozen=True,
                              allow_inf_nan=False,
                              ser_json_timedelta='iso8601',
                              ser_json_bytes='base64',
                              validate_default=True,
                              use_enum_values=True,
                              )

# --- Nested API Payload Structure Classes ---

class ContactAutRoleElement(BaseModel):
    """Element containing contact authorization role fields"""
    fields: ContactAutRoleUpdateSchema = Field(serialization_alias="Fields")

class ContactAutRoleObject(BaseModel):
    """Object containing contact authorization role elements"""
    element: Optional[List[ContactAutRoleElement]] = Field(default=None, serialization_alias="Element")

class ContactAutRoleSchema(BaseModel):
    """Schema for contact authorization role"""
    kn_contact_aut_role: ContactAutRoleObject = Field(serialization_alias="KnContactAutRole")

class ContactElement(BaseModel):
    """Element containing contact fields and objects"""
    fields: PutContactSchema = Field(serialization_alias="Fields")
    objects: Optional[List[ContactAutRoleSchema]] = Field(default=None, serialization_alias="Objects")

class ContactObject(BaseModel):
    """Object containing contact element"""
    element: ContactElement = Field(serialization_alias="Element")

class ContactPayload(BaseModel):
    """
    Top-level payload structure matching the KnContact API endpoint

    Symbolic JSON structure:
    {
        "KnContact": {
            "Element": {
                "Fields": {
                    "CdId": integer,        // Contact
                    "BcCoOga": string,      // Code organisatie
                    "BcCoPer": string,      // Code persoon
                    "PadAdr": boolean,      // Postadres is adres
                    "ExAd": string,         // Afdeling
                    "ViKc": enum,           // Soort contact
                    "ViFu": enum,           // Functie
                    "ViMd": enum,           // Voorkeursmedium
                    "FuDs": string,         // Functie op visitekaart
                    "Corr": boolean,        // Correspondentie
                    "TeNr": string,         // Telefoonnr. werk
                    "FaNr": string,         // Fax werk
                    "MbNr": string,         // Mobiel werk
                    "EmAd": string,         // E-mail werk
                    "HoPa": string,         // Website
                    "Re": bytes,            // Toelichting
                    "Bl": boolean,          // Geblokkeerd
                    "AtLn": string,         // T.a.v. regel
                    "LeHe": string,         // Briefaanhef
                    "SocN": string,         // Sociale netwerken
                    "Face": string,         // Facebook
                    "Link": string,         // LinkedIn
                    "Twtr": string,         // X (voorheen Twitter)
                    "AddToPortal": boolean, // Persoon toegang geven tot afgeschermde deel van de portal(s)
                    "EmailPortal": string   // E-mail toegang
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
                    }
                ]
            }
        }
    }
    """
    kn_contact: ContactObject = Field(serialization_alias="KnContact")
