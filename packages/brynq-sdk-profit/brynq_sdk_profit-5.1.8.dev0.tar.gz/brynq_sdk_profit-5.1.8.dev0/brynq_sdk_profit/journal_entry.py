import asyncio
import pandas as pd
from typing import Optional, Tuple, List
import requests

from .schemas.journal_entry import (JournalentryGetSchema,
                                    JournalFinancialEntryParametersCreate,
                                    JournalFinancialEntryCreate,
                                    JournalFinancialDimEntries)
from brynq_sdk_functions import Functions

class JournalEntry:
    """Journal Entry management class for AFAS integration"""

    def __init__(self, afas_connector):
        """
        Initialize JournalEntry class with AFAS connector

        Args:
            afas_connector: AFAS connection handler instance
        """
        self.afas = afas_connector
        self.get_url = f"{self.afas.base_url}/brynq_sdk_journal_entry"


    def get(self, filter_fields: dict = None) -> pd.DataFrame:
        """
        Get journal entry information from AFAS

        Args:
            filter_fields (dict, optional): Dictionary of filters in format {field_name: value}

        Returns:
            pd.DataFrame: DataFrame containing journal entry information

        Raises:
            Exception: If get journal entry operation fails
        """
        try:
            return asyncio.run(self.afas.base_get(url=self.get_url, schema=JournalentryGetSchema, filter_fields=filter_fields))
        except Exception as e:
            raise Exception(f"Get journal entry failed: {str(e)}") from e

    def _build_payload(self, df: pd.DataFrame) -> dict:
        """
        Creates request body for journal entries

        Args:
            df: data with journal entries

        Returns:
            dict: Request body for AFAS API

        Raises:
            Exception: If building request body fails
        """
        try:
            # Get the fields required by the parameter schema
            param_fields = JournalFinancialEntryParametersCreate.model_fields.keys()

            # Select the first row as a dictionary
            first_row = df.iloc[0].to_dict()

            # Dynamically create the parameter dictionary
            parameters_data = {
                field: first_row.get(field)
                for field in param_fields
                if field in first_row
            }

            # Initialize the main parameters schema with dynamic data
            parameters = JournalFinancialEntryParametersCreate(**parameters_data)

            base_body = {
                "FiEntryPar": {
                    "Element": {
                        "Fields": {
                            **parameters.model_dump(by_alias=True, mode="json", exclude_none=True)
                        },
                        "Objects": [
                            {
                                "FiEntries": {
                                    "Element": []
                                }
                            }
                        ]
                    }
                }
            }

            # Get the fields required by the entry schema for dynamic selection
            entry_fields = JournalFinancialEntryCreate.model_fields.keys()
            # Get the fields required by the dimension schema
            dim_fields = JournalFinancialDimEntries.model_fields.keys()

            for row in df.to_dict(orient='records'):
                # Convert pandas Timestamp objects to strings
                for key, value in row.items():
                    if isinstance(value, pd.Timestamp):
                        row[key] = value.strftime('%Y-%m-%d')
                    elif pd.api.types.is_integer_dtype(pd.Series([value])):
                        row[key] = int(value)
                    elif pd.api.types.is_float_dtype(pd.Series([value])):
                        row[key] = float(value)

                # Filter the row data to match the main entry schema fields
                entry_data = {
                    field: row.get(field)
                    for field in entry_fields
                    if field in row and pd.notna(row.get(field))
                }

                # Apply default for account_reference if it's not provided
                if 'account_reference' not in entry_data:
                    entry_data['account_reference'] = '1'

                entry = JournalFinancialEntryCreate(**entry_data)

                # Filter the row data to match the dimension schema fields
                dim_data = {
                    field: row.get(field)
                    for field in dim_fields
                    if field in row and pd.notna(row.get(field))
                }

                dim_entries = JournalFinancialDimEntries(**dim_data)

                entry_payload = {
                    "Fields": {
                        **entry.model_dump(by_alias=True, mode="json", exclude_none=True)
                    },
                    "Objects": [
                        {
                            "FiDimEntries": {
                                "Element": {
                                    "Fields": {
                                        **dim_entries.model_dump(by_alias=True, mode="json", exclude_none=True)
                                    }
                                }
                            }
                        }
                    ]
                }

                base_body['FiEntryPar']["Element"]["Objects"][0]["FiEntries"]["Element"].append(entry_payload)

            return base_body
        except Exception as e:
            raise Exception(f"Build request body failed: {str(e)}")


    def create(self, df: pd.DataFrame, return_meta: bool = True) -> Tuple[List[str], List[int], requests.Response]:
        payload = self._build_payload(df)
        return self.afas.base_post("FiEntries", payload, return_meta=return_meta)

    def delete(self, year, entry_no) -> requests.Response:
        return self.afas.session.delete(
            url=f"{self.afas.base_url}/FiEntries/FiEntryPar/Year,UnId/{year},{entry_no}",
            timeout=self.afas.timeout
        )
