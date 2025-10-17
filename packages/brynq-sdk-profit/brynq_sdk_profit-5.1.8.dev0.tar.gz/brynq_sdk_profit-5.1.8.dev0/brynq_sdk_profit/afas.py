import base64
import requests
import pandas as pd
import json
import warnings

from brynq_sdk_brynq import BrynQ
from brynq_sdk_functions import Functions

from .exceptions import AFASUpdateError

from .address import Address
from .employees import Employees
from .person import Person
from .organisation import Organisation
from .organisational_unit import OrganisationalUnit
from .costcenter import CostCenter
from .costcarrier import CostCarrier
from .bankaccount import BankAccount
#from .debtor_creditor import Debtor, Creditor
from .creditor import Creditor
from .journal_entry import JournalEntry
from .postcalculation import PostCalculation
from .functions import EmployeeFunction
from .custom_connector import CustomGetConnector
from .subject_reaction import ReactionDossierItem
from .subject import Subject
from .schemas.afas_response import AFASResponseSchema
from .city import City
from .title import Title
from .debtor import Debtor
from .schemas.mappings import Mappings
from .subscription import Subscription
from .wage_components import WageComponents
import pandera as pa
from typing import Dict, Any, Type, Optional, List, Literal, Union
import datetime
import aiohttp
import asyncio

class AFAS(BrynQ):
    Language: Literal['nl-NL', 'en-US'] = 'nl-NL'

    def __init__(self, system_type: Optional[Literal['source', 'target']] = None, test_environment: bool = False, debug: bool = False):
        """
        Initialize AFAS connection handler

        Args:
            system_type: Connection system_type for credentials
            test_environment: Whether to use test environment
            debug: Whether to enable debug mode
        """
        super().__init__()
        #setup base variables

        self.debug = debug
        self.timeout = 3600
        #set environment and base url, using credentials from Brynq
        self.test_environment = test_environment
        credentials = self.interfaces.credentials.get(system="profit", system_type=system_type, test_environment=test_environment)
        self.environment = credentials["data"]['environment']
        base64token = base64.b64encode(credentials['data']['token'].encode('utf-8')).decode()
        if test_environment:
            self.base_url = f'https://{self.environment}.resttest.afas.online/ProfitRestServices/connectors'
        else:
            self.base_url = f'https://{self.environment}.rest.afas.online/profitrestservices/connectors'

        # Initialize session with headers, used for update/create
        self.session = requests.Session()

        self.session.headers.update({
            'Authorization': 'AfasToken ' + base64token,
            'IntegrationId': '38092_135680',
            'Content-Type': 'application/json',
            "accept-language": self.Language,
            "accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, zstd",
        })

        # Initialize all service classes
        self.address = Address(self)
        self.city = City(self)
        self.title = Title(self)
        self.employees = Employees(self)
        # expose singular alias for new employee interface
        self.employee = self.employees
        self.person = Person(self)
        self.organisation = Organisation(self)
        self.organisational_unit = OrganisationalUnit(self)
        self.cost_center = CostCenter(self)
        self.cost_carrier = CostCarrier(self)
        self.bank_account = BankAccount(self)
        self.debtor = Debtor(self)
        self.creditor = Creditor(self)
        self.journal_entry = JournalEntry(self)
        self.post_calculation = PostCalculation(self)
        self.function = EmployeeFunction(self)
        self.post_calculation = PostCalculation(self)
        self.custom_connector: CustomGetConnector = CustomGetConnector(self)
        self.reaction_dossier_item = ReactionDossierItem(self)
        self.subject = Subject(self)
        self.debtor = Debtor(self)
        self.mappings = Mappings()
        self.wage_components = WageComponents(self)
        self.subscription = Subscription(self)
    #-- GET methods
    async def base_get(self, url: str, schema: Type[pa.DataFrameModel] = None, schema_required: bool = True,
                       filter_fields: Optional[dict] = None, batch_size: int = 8, take: int = 40000) -> Union[pd.DataFrame, str]:
        """
        Base GET method for AFAS API calls (async version, batched like legacy)

        Args:
            url: Base URL for the endpoint
            schema: Pandera schema for validation. Is required for all endpoints, except for custom connectors.
            schema_required: For safety: Whether the schema is required for the endpoint. Should only be set to False for custom connectors.
            filter_fields: Optional filters to apply
            batch_size: Number of pages to fetch concurrently per batch
            take: Page size (defaults to legacy value of 40000)

        Returns:
            pd.DataFrame: Validated response data
        """
        if schema_required and schema is None:
            raise ValueError("Schema is required for this endpoint")

        if filter_fields:
            filter_params = {
                'filterfieldids': ','.join(filter_fields.keys()),
                'filtervalues': ','.join(str(value) for value in filter_fields.values()),
                'operatortypes': ','.join(['1'] * len(filter_fields))
            }
            url = f"{url}?{'&'.join(f'{k}={v}' for k, v in filter_params.items())}"

        # Batched concurrent pagination (like legacy async implementation)
        rows: List[dict] = []

        conn = aiohttp.TCPConnector(
            force_close=True,
            enable_cleanup_closed=True,
        )

        timeout = aiohttp.ClientTimeout(total=self.timeout)

        async def fetch_page(session: aiohttp.ClientSession, page_skip: int) -> List[dict]:
            try:
                async with session.get(url, verify_ssl=False, params={'skip': page_skip, 'take': take}) as resp:
                    resp.raise_for_status()
                    payload = await resp.json()
                    if not payload:
                        return []
                    return payload.get("rows", [])
            except aiohttp.ClientResponseError as http_error:
                error_message = f" HTTP STATUS CODE == '{http_error.status}'. HTTP ERROR MESSAGE == '{getattr(http_error, 'message', str(http_error))}'."
                if http_error.headers and 'X-Profit-Error' in http_error.headers:
                    error_header = http_error.headers['X-Profit-Error']
                    try:
                        decoded_error = base64.b64decode(error_header).decode('utf-8')
                        error_message += f" DECODED ERROR MESSAGE == '{decoded_error}'."
                    except Exception:
                        error_message += f" (Failed to decode 'X-Profit-Error' header: {error_header})"

                request_url = http_error.request_info.url if hasattr(http_error, 'request_info') and http_error.request_info else 'unknown URL'
                # Re-raise the original exception with enhanced message
                http_error.message = f"{error_message}, URL='{request_url}'"
                raise
            except aiohttp.ClientError as client_error:
                request_url = getattr(client_error, 'url', 'unknown URL')
                raise type(client_error)(f"Client Error in pagination: {client_error}, URL='{request_url}'") from client_error
            except asyncio.TimeoutError as timeout_error:
                raise asyncio.TimeoutError(f"Timeout Error in pagination: The request took too long to complete. Original error: {timeout_error}") from timeout_error
            except Exception as general_error:
                raise Exception(f"An unexpected error occurred during pagination: {general_error}") from general_error

        async with aiohttp.ClientSession(
                headers=self.session.headers,
                connector=conn,
                timeout=timeout
        ) as session:
            got_all_results = False
            batch_number = 0
            while not got_all_results:
                tasks = []
                for i in range(batch_size):
                    page_skip = take * (i + batch_number * batch_size)
                    tasks.append(fetch_page(session, page_skip))

                batch_results: List[List[dict]] = await asyncio.gather(*tasks)

                # Flatten and detect end
                for page_rows in batch_results:
                    if not page_rows:
                        got_all_results = True
                    rows.extend(page_rows)
                    if len(page_rows) < take:
                        got_all_results = True

                batch_number += 1
                # Be polite between batches
                await asyncio.sleep(0.05)

        df = pd.DataFrame(rows)

        if 'Btw-nummer' in df.columns:
            df = df.rename(columns={'Btw-nummer': 'Btw_nummer'})

        #if schema is provided, validate the data, otherwise return the raw data if response_data is not empty
        if not df.empty:
            if schema_required and schema:
                valid_data, invalid_data = Functions.validate_data(
                    df=df,
                    schema=schema,
                    debug=True
                )
                return valid_data
            else:
                return df
        else:
            warnings.warn(f"No record found! Returning empty response DataFrame for {url}")
            return pd.DataFrame(rows)

    async def get_paginated_result(self, request: requests.Request) -> List:
        """
        Handle paginated requests to AFAS (async version)

        Args:
            request: Request object to send

        Returns:
            List of results from all pages
        """
        skip = 0
        take = 5000
        result_data = []

        conn = aiohttp.TCPConnector(
            force_close=True,
            enable_cleanup_closed=True,
        )

        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(
                headers=self.session.headers,
                connector=conn,
                timeout=timeout
        ) as session:
            while True:
                try:
                    if request.params is None:
                        request.params = {}
                    request.params.update({
                        'skip': skip,
                        'take': take
                    })

                    async with session.get(request.url, params=request.params) as resp:
                        resp.raise_for_status()
                        response_data = await resp.json()

                        if not response_data:
                            break

                        result_data.extend(response_data["rows"])

                        if len(response_data["rows"]) < take:
                            break

                        skip += take

                    await asyncio.sleep(0.1)

                #-- error handling
                except aiohttp.ClientResponseError as http_error:
                    error_message = f" HTTP STATUS CODE == '{http_error.status}'. HTTP ERROR MESSAGE == '{getattr(http_error, 'message', str(http_error))}'."
                    #detailed error message is b64 encoded inside the X-Profit-Error header (if present)
                    if http_error.headers and 'X-Profit-Error' in http_error.headers:
                        error_header = http_error.headers['X-Profit-Error']
                        try:
                            decoded_error = base64.b64decode(error_header).decode('utf-8')
                            error_message += f" DECODED ERROR MESSAGE == '{decoded_error}'."
                        except Exception:
                            error_message += f" (Failed to decode 'X-Profit-Error' header: {error_header})"

                    # Include the URL that caused the error if available
                    request_url = http_error.request_info.url if hasattr(http_error, 'request_info') and http_error.request_info else 'unknown URL'
                    # Re-raise the original exception with enhanced message
                    http_error.message = f"{error_message}, URL='{request_url}'"
                    raise

                except (aiohttp.ClientError, asyncio.TimeoutError) as client_error:
                    request_url = getattr(client_error, 'url', 'unknown URL')
                    raise RuntimeError(f"Client Error in pagination: {client_error}, URL='{request_url}'") from client_error

                except Exception as general_error:
                    raise RuntimeError(f"An unexpected error occurred during pagination: {general_error}") from general_error

        return result_data

    #-- update/create methods
    def _base_update(self, method: str, url: str, payload: dict, timeout_sec: Optional[int] = None, *, return_meta: bool = False):
        timeout = timeout_sec or self.timeout

        try:
            resp = self.session.request(method.upper(), url, json=payload, timeout=timeout)

            if resp.status_code >= 400:
                # Decode the full error message from X-Profit-Error header if present
                decoded_error = None
                if 'X-Profit-Error' in resp.headers:
                    try:
                        decoded_error = base64.b64decode(resp.headers['X-Profit-Error']).decode('utf-8')
                    except Exception:
                        decoded_error = resp.headers.get('X-Profit-Error', '')

                raise AFASUpdateError(
                    request_info=None,  # requests doesn't have request_info like aiohttp
                    history=tuple(),
                    status=resp.status_code,
                    message=(resp.reason or ""),
                    headers=dict(resp.headers),
                    text=decoded_error or resp.text,  # Use decoded error if available, otherwise raw body
                    url=url,  # Include the URL for better error reporting
                    payload=payload,  # Include the payload for debugging/replication
                )

            # ---- success path ----
            text = resp.text
            body_json = None
            if text.strip():
                try:
                    body_json = json.loads(text)
                except json.JSONDecodeError:
                    pass

            # Decode AFAS success result header if present
            hdrs = dict(resp.headers)
            result_json, result_text = self._decode_b64_header_json(hdrs, "X-Profit-Result")

            if not return_meta:
                # Backward-compatible: return body JSON (or None) exactly like before
                return body_json

            # Build typed response with everything callers might need
            request_id = (
                hdrs.get("X-Request-ID")
                or hdrs.get("Request-Id")
                or hdrs.get("X-Profit-RequestId")
                or hdrs.get("X-Correlation-ID")
            )
            return AFASResponseSchema(
                ok=True,
                status_code=resp.status_code,
                reason=resp.reason or "",
                request_url=str(resp.url),
                headers=hdrs,
                request_id=request_id,
                location=hdrs.get("Location"),
                body_json=body_json,
                body_text=None if body_json is not None else text,
                result_json=result_json if result_json is not None else (
                    # convenience: if body_json contains an obvious results node, surface it
                    body_json.get("results") if isinstance(body_json, dict) and "results" in body_json else None
                ),
                result_text=result_text,
                request_payload=payload,  # Include the request payload for debugging
            )
        except Exception as e:
            raise

    def base_post(self, connector: str, payload: dict, *, return_meta: bool = True):
        return self._base_update("POST", f"{self.base_url}/{connector}", payload, return_meta=return_meta)

    def base_put(self, connector: str, payload: dict, *, return_meta: bool = True):
        return self._base_update("PUT", f"{self.base_url}/{connector}", payload, return_meta=return_meta)

    # Helper function for update/create
    @staticmethod
    def _decode_b64_header_json(headers: dict, key: str) -> tuple[Optional[dict], Optional[str]]:
        """
        Try to base64-decode a header and parse JSON. Return (json, text).

        Args:
            headers (dict): The headers dictionary from which to extract the value.
            key (str): The header key to decode.

        Returns:
            tuple[Optional[dict], Optional[str]]: Tuple of (parsed_json, raw_text). If decoding or parsing fails, returns (None, None) or (None, text).
        """
        val = headers.get(key)
        if not val:
            return None, None
        try:
            txt = base64.b64decode(val).decode("utf-8", errors="replace")
        except Exception:
            return None, None
        try:
            return json.loads(txt), None
        except json.JSONDecodeError:
            return None, txt

    @staticmethod
    async def _safe_parse_json(resp: aiohttp.ClientResponse):
        """
        Safely parse JSON from an aiohttp response.

        Args:
            resp (aiohttp.ClientResponse): The aiohttp response object.

        Returns:
            dict or None: Parsed JSON dictionary, or {"raw": text} if JSON decoding fails, or None if response is empty.
        """
        txt = await resp.text()
        if not txt.strip():
            return None
        try:
            return json.loads(txt)
        except json.JSONDecodeError:
            return {"raw": txt}

    #helper functions for validation
    def get_metadata(self, connector: str = None, connector_type: Literal['get', 'update', None] = 'get') -> dict:
        """
        Get metadata information for connectors

        Args:
            connector: Name of the connector to get metadata for
            connector_type: Type of metadata ('get', 'update', or None)

        Returns:
            dict: Metadata information

        Raises:
            Exception: If metadata retrieval fails
        """
        return self.custom_connector.get_metadata(connector=connector, type=connector_type)

    def list_connectors(self, connector_type: Literal['get', 'update'] = 'get') -> List[str]:
        """
        Get list of available connectors

        Args:
            connector_type: Type of connectors to list ('get' or 'update')

        Returns:
            List[str]: List of connector names

        Raises:
            Exception: If listing connectors fails
        """
        try:
            metadata = self.get_metadata(connector_type=connector_type)
            if isinstance(metadata, dict):
                return list(metadata.keys())
            elif isinstance(metadata, list):
                return [conn.get('name', '') for conn in metadata if 'name' in conn]
            else:
                return []
        except Exception as e:
            raise Exception(f"List connectors failed: {str(e)}") from e

    #LEGACY METHODS; TO BE REMOVED
    #validaiton and its helper functions
    def validate(self, schema: Type[pa.DataFrameModel], data: dict) -> dict:
        """
        Validate data against a Pandera schema.

        Args:
            schema (Type[pa.DataFrameModel]): The Pandera schema to validate against.
            data (dict): The data to validate.

        Returns:
            dict: The validated data.
        """
        try:
            empty_df = self.create_typed_empty_df(schema)
            df = self.fill_empty_df(empty_df=empty_df, data=data)
            valid_data, invalid_data = Functions.validate_data(schema=schema, df=df)
            if valid_data.empty:
                raise ValueError(f"Data validation failed. Invalid data: {invalid_data}")

            return valid_data.to_dict('records')[0]
        except Exception as e:
            raise Exception(f"Validation error: {str(e)}")

    @staticmethod
    def create_typed_empty_df(schema: Type[pa.DataFrameModel]) -> pd.DataFrame:
        """
        Create an empty DataFrame with columns matching the schema's data types.

        Args:
            schema (pa.DataFrameModel): The Pandera schema to use for generating the DataFrame.

        Returns:
            pd.DataFrame: An empty DataFrame with schema-matching column types.
        """
        # Extract schema columns and their definitions
        schema_columns = schema.to_schema().columns

        # Prepare a dictionary for columns and their corresponding dtypes
        column_dtypes: Dict[str, Any] = {}

        for column_name, column_properties in schema_columns.items():
            # Extract the column's dtype
            dtype = column_properties.dtype.type

            # Assign the dtype to the column name
            column_dtypes[column_name] = dtype

        # Create an empty DataFrame with the defined dtypes
        empty_df = pd.DataFrame({col: pd.Series(dtype=dtype) for col, dtype in column_dtypes.items()})

        return empty_df

    @staticmethod
    def clean_nans(df):
        """
        Clean NaN values from DataFrame

        Args:
            df: DataFrame to clean

        Returns:
            pd.DataFrame: Cleaned DataFrame
        """
        # String columns: NaN -> ""
        string_cols = df.select_dtypes(include=['object']).columns
        df[string_cols] = df[string_cols].fillna("")

        # Numeric columns: NaN -> 0
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        df[numeric_cols] = df[numeric_cols].fillna('').replace({'': 0})

        # Boolean columns: NaN -> False
        bool_cols = df.select_dtypes(include=['bool']).columns
        df[bool_cols] = df[bool_cols].fillna(False)

        return df

    def fill_empty_df(self,empty_df:pd.DataFrame,data:dict)->pd.DataFrame:
        for column in empty_df.columns:
            if column in data:
                value = data[column]
                empty_df.at[0, column] = None if pd.isna(value) else value
            else:
                empty_df.at[0, column] = None
        empty_df = self.clean_nans(empty_df)
        return empty_df
