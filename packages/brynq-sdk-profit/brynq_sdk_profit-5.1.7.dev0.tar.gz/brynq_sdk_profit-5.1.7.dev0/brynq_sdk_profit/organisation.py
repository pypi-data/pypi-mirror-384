import pandas as pd
from typing import Optional, Union

from .schemas.organisation import (
    PostKnOrganisationFields,
    OrganisationPayload,
    OrganisationObject,
    OrganisationElement,
    OrganisationContactSchema,
    OrganisationContactObject,
    OrganisationContactElement,
    OrganisationNestedPersonSchema,
    OrganisationNestedPersonObject,
    OrganisationNestedPersonElement
)
from .schemas.person import PostKnPersonFieldsSchema
from .exceptions import AFASUpdateError

class Organisation:
    """Organisation management class for AFAS integration"""

    def __init__(self, afas_connector):
        """
        Initialize Organisation class with AFAS connector

        Args:
            afas_connector: AFAS connection handler instance
        """
        self.afas = afas_connector
        self._address_handler = None

    @property
    def address(self):
        """
        Get address handler for organisation-specific address operations

        Returns:
            OrganisationAddressHandler: Handler for address operations with entity_type="organisation"
        """
        if self._address_handler is None:
            from .address import Address, OrganisationAddressHandler
            self._address_handler = OrganisationAddressHandler(Address(self.afas))
        return self._address_handler

    def create(self, data: Union[pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """
        POST KnOrganisation.
        """
        try:
            if isinstance(data, pd.Series):
                data = data.to_dict()
            if isinstance(data, pd.DataFrame):
                # If data is a DataFrame, convert it to a list of dicts (records)
                data = data.to_dict(orient="records")

            fields = PostKnOrganisationFields(**data)
            payload_model = OrganisationPayload(
                kn_organisation=OrganisationObject(
                    element=OrganisationElement(
                        fields=fields,
                    )
                )
            )
            payload = payload_model.model_dump(
                by_alias=True, mode="json", exclude_none=True
            )
            return self.afas.base_post("KnOrganisation", payload, return_meta=return_meta)
        except AFASUpdateError:
            raise
        except Exception as e:
            raise Exception(f"Unexpected error in Organisation create: {e}") from e

    def update(self, data: Union[pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """
        PUT KnOrganisation.
        """
        try:
            if isinstance(data, pd.Series):
                data = data.to_dict()
            fields = PostKnOrganisationFields(**data)
            payload_model = OrganisationPayload(
                kn_organisation=OrganisationObject(
                    element=OrganisationElement(
                        fields=fields,
                    )
                )
            )
            payload = payload_model.model_dump(
                by_alias=True, mode="json", exclude_none=True
            )
            return self.afas.base_put("KnOrganisation", payload, return_meta=return_meta)
        except AFASUpdateError:
            raise
        except Exception as e:
            raise Exception(f"Unexpected error in Organisation update: {e}") from e

    def connect_contact_person(self, data: Union[pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """
        connect a contact person an organisation following the KnOrganisation/KnContact/KnPerson hierarchy.

        This method creates both the contact and person records in a single API call.

        Required fields:
        - organisation_id: The organisation ID (BcCo)
        - person_id: The person ID (BcCo for person)

        Standard values set automatically:
        - MatchOga = 0 (match organisation by BcCo)
        - ViKc = "PRS" (contact type = person)
        - MatchPer = 0 (match person by BcCo)

        Args:
            data: Dictionary containing required fields and any optional person fields
            return_meta: Whether to return metadata from the API response

        Returns:
            Response from AFAS API

        Example:
            afas.organisation.create_contact_person({
                'organisation_id': 'ORG001',  # Required
                'person_id': 'PERSON123',     # Required
                'first_name': 'John',         # Optional person field
                'last_name': 'Doe'            # Optional person field
            })
        """
        try:
            if isinstance(data, pd.Series):
                data = data.to_dict()

            # Validate required fields
            organisation_id = data.get('organisation_id')
            person_id = data.get('person_id')

            if not organisation_id:
                raise ValueError("organisation_id is required")
            if not person_id:
                raise ValueError("person_id is required")

            # Build organisation data with standard values
            organisation_data = {
                'organisation_id': organisation_id,
                'match_organisation': 0,  # MatchOga = 0 (match by BcCo)
                'auto_number': False      # We're providing organisation_id
            }

            # Build contact data with standard values
            contact_data = {
                'ViKc': 'PRS'  # Contact type = person
            }

            # Extract person fields (everything else that's not organisation_id)
            person_data = {k: v for k, v in data.items() if k != 'organisation_id'}

            # Add standard person values
            person_data.update({
                'person_id': person_id,
                'match_person': 0  # MatchPer = 0 (match by BcCo)
            })

            # start building payload building blocks
            organisation_fields = PostKnOrganisationFields(**organisation_data)
            person_fields = PostKnPersonFieldsSchema(**person_data)
            objects = []
            person_element = OrganisationNestedPersonElement(fields=person_fields.model_dump(by_alias=True, exclude_none=True))
            person_object = OrganisationNestedPersonObject(element=[person_element])
            person_schema = OrganisationNestedPersonSchema(kn_person=person_object)
            contact_element = OrganisationContactElement(
                fields=contact_data,
                objects=[person_schema]
            )
            contact_object = OrganisationContactObject(element=[contact_element])
            contact_schema = OrganisationContactSchema(kn_contact=contact_object)
            objects.append(contact_schema)

            # Build final payload using the building blocks
            payload = OrganisationPayload(
                kn_organisation=OrganisationObject(
                    element=OrganisationElement(
                        fields=organisation_fields,
                        objects=objects if objects else None
                    )
                )
            )

            payload_dict = payload.model_dump(by_alias=True, mode="json", exclude_none=True)

            # # CRITICAL FIX: Convert Objects from array to dictionary as AFAS expects
            # if "Objects" in payload_dict["KnOrganisation"]["Element"] and isinstance(payload_dict["KnOrganisation"]["Element"]["Objects"], list):
            #     objects_list = payload_dict["KnOrganisation"]["Element"]["Objects"]
            #     objects_dict = {}
            #     for obj in objects_list:
            #         # Each object has a single key (KnContact, etc.)
            #         # Merge all object dictionaries into one
            #         objects_dict.update(obj)
            #     payload_dict["KnOrganisation"]["Element"]["Objects"] = objects_dict

            # # Also fix nested Objects within KnContact if they exist
            # if "Objects" in objects_dict.get("KnContact", {}).get("Element", {}):
            #     contact_objects_list = objects_dict["KnContact"]["Element"]["Objects"]
            #     if isinstance(contact_objects_list, list):
            #         contact_objects_dict = {}
            #         for obj in contact_objects_list:
            #             contact_objects_dict.update(obj)
            #         objects_dict["KnContact"]["Element"]["Objects"] = contact_objects_dict

            return self.afas.base_post("KnOrganisation", payload_dict, return_meta=return_meta)
        except Exception as e:
            raise Exception(f"Create contact person failed: {str(e)}") from e
