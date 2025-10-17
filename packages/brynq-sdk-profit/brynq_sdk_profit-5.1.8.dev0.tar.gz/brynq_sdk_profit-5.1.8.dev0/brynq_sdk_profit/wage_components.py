import asyncio
import pandas as pd
from typing import Dict, Optional, Any, List, Union
from pydantic import ValidationError

from .schemas.wage_component import WageComponentGetSchema, WageComponentPost, WageComponentPayload, WageComponentElement, WageComponentObject
from .exceptions import AFASUpdateError


class WageComponents:
    """Wage component management class for AFAS integration"""

    def __init__(self, afas_connector: Any):
        """
        Initialize WageComponent class with AFAS connector

        Args:
            afas_connector: AFAS connection handler instance
        """
        self.afas = afas_connector
        self.get_url = f"{self.afas.base_url}/HrVarValue"

    def get(self, filter_fields: dict = None) -> pd.DataFrame:
        """
        Get wage components information from AFAS

        Args:
            filter_fields (dict, optional): Dictionary of filters in format {field_name: value}

        Returns:
            pd.DataFrame: DataFrame containing wage components information

        Raises:
            Exception: If get wage components operation fails
        """
        try:
            return asyncio.run(self.afas.base_get(url=self.get_url, schema=WageComponentGetSchema, filter_fields=filter_fields))
        except Exception as e:
            raise Exception(f"Get wage components failed: {str(e)}") from e

    def create(self, data: Union[pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """
        POST HrVarValue.
        """
        try:
            if isinstance(data, pd.Series):
                data = data.to_dict()
            if isinstance(data, pd.DataFrame):
                # If data is a DataFrame, convert it to a list of dicts (records)
                data = data.to_dict(orient="records")

            fields = WageComponentPost(**data)
            payload_model = WageComponentPayload(
                hr_var_value=WageComponentObject(
                    element=WageComponentElement(
                        fields=fields,
                    )
                )
            )
            payload = payload_model.model_dump(
                by_alias=True, mode="json", exclude_none=True
            )
            return self.afas.base_post("HrVarValue", payload, return_meta=return_meta)
        except AFASUpdateError:
            raise
        except Exception as e:
            raise Exception(f"Unexpected error in WageComponent create: {e}") from e

    def update(self, data: Union[pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """
        PUT HrVarValue.
        """
        try:
            if isinstance(data, pd.Series):
                data = data.to_dict()
            fields = WageComponentPost(**data)
            payload_model = WageComponentPayload(
                hr_var_value=WageComponentObject(
                    element=WageComponentElement(
                        fields=fields,
                    )
                )
            )
            payload = payload_model.model_dump(
                by_alias=True, mode="json", exclude_none=True
            )
            return self.afas.base_put("HrVarValue", payload, return_meta=return_meta)
        except AFASUpdateError:
            raise
        except Exception as e:
            raise Exception(f"Unexpected error in WageComponent update: {e}") from e

    # def delete(self, data: dict) -> requests.Response:
    #     """
    #     Delete wage component in AFAS

    #     Args:
    #         data: Dictionary containing wage component data with at least parameter, employee_id, and start_date

    #     Returns:
    #         requests.Response: Response from AFAS API

    #     Raises:
    #         ValueError: If deletion fails
    #     """
    #     try:
    #         # Validate required fields for deletion
    #         required_fields = ['parameter', 'employee_id', 'start_date']
    #         missing_fields = [field for field in required_fields if field not in data]
    #         if missing_fields:
    #             raise ValueError(f"Delete operation requires the following fields: {missing_fields}")

    #         # Format the date for the URL
    #         start_date_str = pd.to_datetime(data["start_date"]).strftime("%Y-%m-%d")

    #         url = f'{self.afas.base_url}/HrVarValue/HrVarValue/@VaId,EmId,DaBe/{data["parameter"]},{data["employee_id"]},{start_date_str}'
    #         return self.afas.session.delete(url=url, timeout=self.afas.timeout)
    #     except Exception as e:
    #         raise ValueError(f"Wage component deletion failed: {str(e)}")
