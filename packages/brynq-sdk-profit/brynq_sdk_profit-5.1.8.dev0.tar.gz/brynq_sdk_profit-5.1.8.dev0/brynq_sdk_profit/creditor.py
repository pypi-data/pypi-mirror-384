import asyncio
import pandas as pd
import requests
from typing import Optional

from .schemas.creditor import CreditorGetSchema, CreditorCreateSchema, CreditorUpdateSchema


class Creditor:
    """Creditor management class for AFAS integration"""

    def __init__(self, afas_connector):
        """
        Initialize Creditor class with AFAS connector

        Args:
            afas_connector: AFAS connection handler instance
        """
        self.afas = afas_connector
        self.get_url = f"{self.afas.base_url}/brynq_sdk_creditor"
        self.update_url = f"{self.afas.base_url}/KnPurchaseRelationPer"

    def get(self, filter_fields: dict = None) -> pd.DataFrame:
        """
        Get creditor information from AFAS

        Args:
            filter_fields (dict, optional): Dictionary of filters in format {field_name: value}

        Returns:
            pd.DataFrame: DataFrame containing creditor information

        Raises:
            Exception: If get creditor operation fails
        """
        try:
            return asyncio.run(self.afas.base_get(url=self.get_url, schema=CreditorGetSchema, filter_fields=filter_fields))
        except Exception as e:
            raise Exception(f"Get creditor failed: {str(e)}") from e

    def __build_req_body(self, data: dict, overload_fields: dict) -> dict:
        """
        Creates the request body for creditor operations

        Args:
            data: Dictionary containing creditor data

        Returns:
            dict: Formatted request body for AFAS API

        Raises:
            ValueError: If validation fails
        """
        try:
            base_body = {
                "KnPurchaseRelationPer": {
                    "Element": {
                        "Fields": {
                            "CuId": data.get("currency")
                        },
                        "Objects": {
                            "KnPerson": {
                                "Element": {
                                    "Fields": {
                                        "MatchPer": data.get('match_person_on', '0'),
                                    },
                                }
                            }
                        }
                    }
                }
            }

            # Add creditor ID if present and not None
            if data.get('creditor_id') is not None:
                base_body['KnPurchaseRelationPer']['Element'].update({"@CrId": data['creditor_id']})

            # Handle base creditor fields
            base_fields = {
                'is_creditor': 'IsCr',
                'payment_to_external': 'IB47',
                'preferred_iban': 'Iban',
                'remark': 'Rm',
                'payment_condition': 'PaCd',
                'collective_account': 'ColA',
                'preferred_delivery_method': 'InPv',
                'automatic_payment': 'AuPa',
                'compact': 'PaCo',
                'payment_specification': 'PaSp',
                'preferred_provisioning': 'InPv'
            }

            base_updates = {}
            for key in base_fields.keys():
                if key in data:
                    if data[key] != '' and pd.notna(data[key]):
                        base_updates[base_fields[key]] = data[key]

            base_body['KnPurchaseRelationPer']['Element']['Fields'].update(base_updates)

            # Handle person fields
            person_fields = {
                'internal_id': 'BcId',
                'person_id': 'BcCo',
                'log_birthname_seperately': 'SpNm',
                'postal_address_applied': 'PadAdr',
                'auto_number': 'AutoNum',
                'last_name': 'LaNm',
                'first_name': 'FiNm',
                'middle_name': 'Is',
                'gender': 'ViGe',
                'salutation': 'TtId',
                'correspondence': 'Corr',
            }

            person_updates = {}
            for key in person_fields:
                if key in data:
                    if data[key] != '' and pd.notna(data[key]):
                        person_updates[person_fields[key]] = data[key]
            base_body['KnPurchaseRelationPer']['Element']['Objects']['KnPerson']['Element']['Fields'].update(person_updates)

            # Handle address fields
            address_fields = {
                'country': 'CoId',
                'address_is_postal_address': 'PbAd',
                'street': 'Ad',
                'house_number': 'HmNr',
                'house_number_addition': 'HmAd',
                'postal_code': 'ZpCd',
                'city': 'Rs',
                'match_city_on_postal_code': 'ResZip',
                'mailbox_address': 'PbAd'

            }

            address_updates = {}
            for key in address_fields:
                if key in data:
                    if data[key] != '' and pd.notna(data[key]):
                        address_updates[address_fields[key]] = data[key]
            base_body['KnPurchaseRelationPer']['Element']['Objects']['KnPerson']['Element']['Fields'].update(
                address_updates)

            if address_updates:
                new_address = {
                    "KnBasicAddressAdr": {
                        "Element": {
                            "Fields": address_updates
                        }
                    }
                }
                if address_updates:
                    if 'Objects' in base_body['KnPurchaseRelationPer']['Element']['Objects']['KnPerson']['Element']:
                        base_body['KnPurchaseRelationPer']['Element']['Objects']['KnPerson']['Element']['Objects'].append(
                            new_address)
                    else:
                        base_body['KnPurchaseRelationPer']['Element']['Objects']['KnPerson']['Element']['Objects'] = [new_address]

            # Handle bank account fields
            bank_fields = {
                'country_of_bank': 'CoId',
                'iban_check': 'IbCk',
                'iban': 'Iban'
            }

            bank_updates = {}
            for key in bank_fields:
                if key in data:
                    if data[key] != '' and pd.notna(data[key]):
                        bank_updates[bank_fields[key]] = data[key]

            if bank_updates:
                new_bank = {
                    "KnBankAccount": {
                        "Element": {
                            "Fields": bank_updates
                        }
                    }
                }
                base_body['KnPurchaseRelationPer']['Element']['Objects']['KnPerson']['Element']['Objects'].append(new_bank)
            if overload_fields:
                # Add overload fields to base element fields
                base_body['KnPurchaseRelationPer']['Element']['Fields'].update(overload_fields)
                # Add overload fields to person fields
                base_body['KnPurchaseRelationPer']['Element']['Objects']['KnPerson']['Element']['Fields'].update(
                    overload_fields)

            return base_body
        except Exception as e:
            raise Exception("Build request body failed: " + str(e)) from e

    def create(self, data: dict, overload_fields: dict = None) -> Optional[requests.Response]:
        """
        Create creditor in AFAS

        Args:
            data: Dictionary containing creditor data
            overload_fields: Dictionary of custom fields to be included

        Returns:
            requests.Response: Response from AFAS API

        Raises:
            ValueError: If validation fails
        """
        try:
            try:
                valid_data = CreditorCreateSchema(**data).model_dump()
            except Exception as e:
                raise Exception("Data validation failed: " + str(e))

            body = self.__build_req_body(valid_data, overload_fields)

            return self.afas.session.post(
                url=self.update_url,
                json=body,
                timeout=self.afas.timeout
            )
        except Exception as e:
            raise ValueError("Create creditor failed: " + str(e))

    def update(self, data: dict, overload_fields: dict = None) -> Optional[requests.Response]:
        """
        Update creditor in AFAS

        Args:
            data: Dictionary containing creditor data
            overload_fields: Dictionary of custom fields to be included

        Returns:
            requests.Response: Response from AFAS API

        Raises:
            ValueError: If validation fails or invalid method provided
        """
        try:
            try:
                valid_data = CreditorUpdateSchema(**data).model_dump()
            except Exception as e:
                raise Exception("Data validation failed: " + str(e))

            body = self.__build_req_body(valid_data, overload_fields)

            return self.afas.session.put(
                url=self.update_url,
                json=body,
                timeout=self.afas.timeout
            )
        except Exception as e:
            raise ValueError("Update creditor failed: " + str(e))
