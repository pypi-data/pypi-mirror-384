import asyncio
import pandas as pd
from typing import Dict, Optional, Any, Literal, Union, List

# Use your actual import paths
from .schemas.address import (
    AddressGetSchema, AddressPayload, AddressObject, AddressElement,
    AddressCreate, ElementItem, KnBasicAddressAdr, KnBasicAddressPad,
    KnBasicAddressAdrObject, KnBasicAddressPadObject
)
from .schemas.person import PersonElementBase
from .schemas.organisation import OrganisationElementBase

class Address:
    """Address management class for AFAS integration."""

    def __init__(self, afas_connector: Any) -> None:
        """Initializes the Address class with an AFAS connector."""
        self.afas = afas_connector
        self.get_url = f"{self.afas.base_url}/brynq_sdk_address"
        self.address_url = f"{self.afas.base_url}/KnPerson"

    def get(self, filter_fields: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Gets address information from AFAS."""
        return asyncio.run(self.afas.base_get(url=self.get_url, schema=AddressGetSchema, filter_fields=filter_fields))


    def create(self, data: Union[pd.Series, dict], *, return_meta: bool = True, entity_type: Literal["person", "organisation"] = "person", action='insert'):
        """Creates a new person/address record in AFAS."""
        if isinstance(data, pd.Series):
            data = data.to_dict()

        validated_data = self._validate_and_build_nested_request_body(data, entity_type=entity_type, action=action) #build and validate the request body in pydantic schema format (AddressPayload)
        payload = validated_data.model_dump(by_alias=True, mode = "json", exclude_none=True)                                                              #dump to a JSON compatible dict
        endpoint = "KnOrganisation" if entity_type == "organisation" else "KnPerson"
        return self.afas.base_post(endpoint, payload, return_meta=return_meta)

    def update(self, data: Union[pd.Series, dict], *, return_meta: bool = True, entity_type: Literal["person", "organisation"] = "person"):
        """Updates an existing person/address record in AFAS."""
        if isinstance(data, pd.Series):
            data = data.to_dict()

        validated_data = self._validate_and_build_nested_request_body(data, entity_type=entity_type, action=None) #build and validate the request body in pydantic schema format (AddressPayload)
        payload = validated_data.model_dump(by_alias=True, mode = "json", exclude_none=True)                                                          #dump to a JSON compatible dict
        endpoint = "KnOrganisation" if entity_type == "organisation" else "KnPerson"
        return self.afas.base_put(endpoint, payload, return_meta=return_meta)

    def _validate_and_build_nested_request_body(
        self,
        data: dict,
        entity_type: Literal["person", "organisation"],
        action: Optional[Literal["insert"]] = None,
    ) -> AddressPayload:
        """
        Builds and validates the nested request body for address operations.

        Args:
            data: The address data to validate and build.
            action: if create we need to add '@action: insert'
            address_equals_mailbox: If True, creates both a regular and PO Box address with the same data.
        """
        address_keys = AddressCreate.model_fields.keys()
        address_data = {k: v for k, v in data.items() if k in address_keys}

        # Determine address_equals_mailbox from data.equals_mail_address
        equals_mail_value = data.get("equals_mail_address", True)
        if isinstance(equals_mail_value, str):
            address_equals_mailbox = equals_mail_value.lower() in ('true', '1', 'yes', 'on')
        else:
            address_equals_mailbox = bool(equals_mail_value)

        objects_list: List[Union[KnBasicAddressAdrObject, KnBasicAddressPadObject]] = []
        if address_equals_mailbox:
            # Create two objects: one regular address and one identical PO Box address.
            adr_fields = AddressCreate(**{**address_data, "is_mail_address": False})
            pad_fields = AddressCreate(**{**address_data, "is_mail_address": True})

            adr_obj = KnBasicAddressAdrObject(kn_basic_address_adr=KnBasicAddressAdr(element=[ElementItem(fields=adr_fields)]))
            # Remove addition to house number for pad_obj (set addition_to_house_number to None)
            pad_fields_no_addition = pad_fields.model_copy(update={"house_number_addition": None})
            pad_obj = KnBasicAddressPadObject(kn_basic_address_pad=KnBasicAddressPad(element=[ElementItem(fields=pad_fields_no_addition)]))

            objects_list.extend([adr_obj, pad_obj])
        else:
            # Create a single address object based on the 'is_mail_address' flag in the data.
            is_mail_value = data.get("is_mail_address", False)
            # Handle both string and boolean values
            if isinstance(is_mail_value, str):
                is_mail = is_mail_value.lower() in ('true', '1', 'yes', 'on')
            else:
                is_mail = bool(is_mail_value)

            address_fields = AddressCreate(**address_data)

            if is_mail:
                # PO Box address (PbAd=True) -> KnBasicAddressPad
                # Remove house number addition for PO Box addresses
                pad_fields_no_addition = address_fields.model_copy(update={"house_number_addition": None})
                pad_obj = KnBasicAddressPadObject(kn_basic_address_pad=KnBasicAddressPad(element=[ElementItem(fields=pad_fields_no_addition)]))
                objects_list.append(pad_obj)
            else:
                # Regular address (PbAd=False) -> KnBasicAddressAdr
                adr_obj = KnBasicAddressAdrObject(kn_basic_address_adr=KnBasicAddressAdr(element=[ElementItem(fields=address_fields)]))
                objects_list.append(adr_obj)

        if entity_type == "person":
            person_keys = PersonElementBase.model_fields.keys()
            person_data = {k: v for k, v in data.items() if k in person_keys}
            person_data['equals_mail_address'] = address_equals_mailbox
            fields = PersonElementBase(**person_data)
        elif entity_type == "organisation":
            organisation_keys = OrganisationElementBase.model_fields.keys()
            organisation_data = {k: v for k, v in data.items() if k in organisation_keys}
            organisation_data['equals_mail_address'] = address_equals_mailbox
            fields = OrganisationElementBase(**organisation_data)
        else:
            raise ValueError(f"Invalid entity type: {entity_type}")

        # Assemble the final payload
        if entity_type == "person":
            payload = AddressPayload(
                kn_person=AddressObject(
                    element=AddressElement(
                        fields=fields,
                        objects=objects_list,
                        action=action,
                    )
                )
            )
        elif entity_type == "organisation":
            payload = AddressPayload(
                kn_organisation=AddressObject(
                    element=AddressElement(
                        fields=fields,
                        objects=objects_list,
                        action=action,
                    )
                )
            )
        else:
            raise ValueError(f"Invalid entity type: {entity_type}")

        return payload


class PersonAddressHandler:
    """Wrapper class to provide person-specific address operations."""

    def __init__(self, address_instance: "Address"):
        """
        Initialize with an address instance.

        Args:
            address_instance: The Address class instance from afas_connector.
        """
        self._address = address_instance

    def create(self, data: Union[pd.Series, dict], *, return_meta: bool = True):
        """
        Create address for person.

        Args:
            data: Address data dictionary or Series.
            return_meta: Whether to return metadata from API response.

        Returns:
            API response metadata if return_meta=True, otherwise None.
        """
        if isinstance(data, pd.Series):
            data = data.to_dict()
        if not isinstance(data, dict):
            data = dict(data)
        if "auto_number" not in data:
            data = dict(data)
            data.setdefault("match_person", "7")
            data.setdefault("auto_number", True)
        return self._address.create(data, return_meta=return_meta, entity_type="person")

    def update(self, data: Union[pd.Series, dict], *, return_meta: bool = True):
        """
        Update address for person.

        Args:
            data: Address data dictionary or Series.
            return_meta: Whether to return metadata from API response.

        Returns:
            API response metadata if return_meta=True, otherwise None.
        """
        if isinstance(data, pd.Series):
            data = data.to_dict()
        if not isinstance(data, dict):
            data = dict(data)
        if "match_person" not in data and data.get("person_id") is not None:
            data = dict(data)
            data["match_person"] = "0"
        return self._address.update(data, return_meta=return_meta, entity_type="person")


class OrganisationAddressHandler:
    """Wrapper class to provide organisation-specific address operations."""

    def __init__(self, address_instance: "Address"):
        """
        Initialize with an address instance.

        Args:
            address_instance: The Address class instance from afas_connector.
        """
        self._address = address_instance

    def create(self, data: Union[pd.Series, dict], *, return_meta: bool = True):
        """
        Create address for organisation.

        Args:
            data: Address data dictionary or Series.
            return_meta: Whether to return metadata from API response.

        Returns:
            API response metadata if return_meta=True, otherwise None.
        """
        return self._address.create(data, return_meta=return_meta, entity_type="organisation", action=None)

    def update(self, data: Union[pd.Series, dict], *, return_meta: bool = True):
        """
        Update address for organisation.

        Args:
            data: Address data dictionary or Series.
            return_meta: Whether to return metadata from API response.

        Returns:
            API response metadata if return_meta=True, otherwise None.
        """
        return self._address.update(data, return_meta=return_meta, entity_type="organisation")
