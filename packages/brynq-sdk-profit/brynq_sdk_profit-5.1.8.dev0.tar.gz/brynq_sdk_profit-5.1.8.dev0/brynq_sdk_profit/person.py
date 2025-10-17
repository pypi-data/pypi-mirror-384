import asyncio
import random
import string
import pandas as pd
from pathlib import Path
from typing import Optional, Union
from functools import lru_cache
#brynq
from brynq_sdk_functions import Functions
# Assuming these imports are in a file in the same directory
from .schemas.person import PostKnPersonFieldsSchema, PersonPayload, PersonObject, PersonElement, GetPerson
from .exceptions import AFASUpdateError
from .city import City
from .address import PersonAddressHandler, Address
from .bankaccount import BankAccount, PersonBankAccountHandler

class Person:
    """Person management class for AFAS integration"""

    def __init__(self, afas_connector):
        """
        Initialize Person class with AFAS connector

        Args:
            afas_connector: AFAS connection handler instance
        """
        self.afas = afas_connector
        self.get_url = f"{self.afas.base_url}/Profit_OrgPer"
        # The self.use_examples flag is instance-specific, so it's best to store it on self.
        self.use_examples = False
        self._address_handler = None
        self._bank_account_handler = None

        #subclasses
        self.address = PersonAddressHandler(Address(self.afas))
        self.bank_account = PersonBankAccountHandler(BankAccount(self.afas))

    def get(self) -> pd.DataFrame:
        """
        Get person information from AFAS
        """
        return asyncio.run(self.afas.base_get(url=self.get_url, schema=GetPerson))

    def create(self, data: Union[pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """
        POST KnPerson.
        """
        try:
            if isinstance(data, pd.Series):
                data = data.to_dict()
            if isinstance(data, pd.DataFrame):
                # If data is a DataFrame, convert it to a list of dicts (records)
                data = data.to_dict(orient="records")

            #default behaviour: always create new person if match_person is not provided along with an auto generated number
            if 'match_person' and "auto_number" not in data:
                data['match_person'] = "7" #always create new
                data["auto_number"] = True #generate new person_id

            #hardcoded extra_validation based on Afas Profit configuration, independent of the schema.
            #validate title;
            # if 'title' in list(data.keys()):
            #     df_title = self.afas.title.get()
            #     if df_title.empty:
            #         raise ValueError("No titles found in available Afas Profit titles, make sure titles are present in the Profit configuration.")
            #     elif data['title'] not in df_title['title'].values:
            #         raise ValueError(f"Title {data['title']} not found in available Afas Profit titles: {df_title['title'].values}")
            #     elif data['second_title'] not in df_title['title'].values:
            #         raise ValueError(f"Second title {data['second_title']} not found in title list: {df_title['title'].values}")

            # #validate birth place and corresponding country;
            # if 'city_of_birth' in list(data.keys()):
            #     df_city = self.afas.city.get()
            #     if df_city.empty:
            #         raise ValueError("No cities found in available Afas Profit cities, make sure cities are present in the Profit configuration.")
            #     if data['city_of_birth'] not in df_city['city'].values:
            #         raise ValueError(f"Birth place {data['city_of_birth']} not found in available Afas Profit cities: {df_city['city'].values[:5]}...")
            #     elif 'birth_country' in list(data.keys()):
            #         corresponding_country = df_city.loc[df_city['city'] == data['city_of_birth'], 'country_id'].values[0]
            #         if data['birth_country'] != corresponding_country:
            #             raise ValueError(f"Birth country {data['birth_country']} does not correspond to birth place {data['city_of_birth']}, it should be {corresponding_country}.")


            fields = PostKnPersonFieldsSchema(**data)
            payload_model = PersonPayload(
                kn_person=PersonObject(
                    element=PersonElement(
                        fields=fields,
                    )
                )
            )
            payload = payload_model.model_dump(
                by_alias=True, mode="json", exclude_none=True
            )
            return self.afas.base_post("KnPerson", payload, return_meta=return_meta)
        except AFASUpdateError:
            raise
        except Exception as e:
            raise

    def update(self, data: Union[pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """
        PUT KnPerson.
        """
        try:
            #default behaviour: always match existing person on person_id (" Zoek op BcCo (Persoons-ID)")
            if 'match_person' not in data and 'person_id' in data:
                data['match_person'] = "0" #match existing person on person_id (" Zoek op BcCo (Persoons-ID)")
            if isinstance(data, pd.Series):
                data = data.to_dict()
            fields = PostKnPersonFieldsSchema(**data)
            payload_model = PersonPayload(
                kn_person=PersonObject(
                    element=PersonElement(
                        fields=fields,
                    )
                )
            )
            payload = payload_model.model_dump(
                by_alias=True, mode="json", exclude_none=True
            )
            return self.afas.base_put("KnPerson", payload, return_meta=return_meta)
        except AFASUpdateError:
            raise
        except Exception as e:
            raise Exception(f"Unexpected error in Person update: {e}") from e
