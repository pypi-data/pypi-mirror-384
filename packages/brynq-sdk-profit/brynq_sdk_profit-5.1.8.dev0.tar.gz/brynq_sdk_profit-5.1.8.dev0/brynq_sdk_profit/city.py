import asyncio
from .schemas.city import GetCity
import pandas as pd

class City:
    """City management class for AFAS integration"""

    def __init__(self, afas_connector):
        """
        Initialize City class with AFAS connector

        Args:
            afas_connector: AFAS connection handler instance
        """
        self.afas = afas_connector
        self.get_url = f"{self.afas.base_url}/Profit_Residence"

    def get(self) -> pd.DataFrame:
        """
        Get city information from AFAS
        """
        try:
            return asyncio.run(self.afas.base_get(url=self.get_url, schema=GetCity))
        except Exception as e:
            raise Exception(f"Get city failed: {str(e)}") from e
