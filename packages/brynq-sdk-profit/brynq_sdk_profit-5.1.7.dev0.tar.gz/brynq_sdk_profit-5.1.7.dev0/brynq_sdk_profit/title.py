import asyncio
from .schemas.title import GetTitle
import pandas as pd

class Title:
    """Title management class for AFAS integration. Make sure to unlock the title in the Profit configuration."""

    def __init__(self, afas_connector):
        """
        Initialize Title class with AFAS connector

        Args:
            afas_connector: AFAS connection handler instance
        """
        self.afas = afas_connector
        # The self.use_examples flag is instance-specific, so it's best to store it on self.
        self.use_examples = False

    def get(self) -> pd.DataFrame:
        """
        Get title information from AFAS, with a fallback mechanism.
        """
        # Define potential endpoints to try in sequence.
        urls_to_try = [
            f"{self.afas.base_url}/ProfitTitles",
            f"{self.afas.base_url}/ProfitTitles_2" #work around in case title cannot be unblocked in Profit configuration.
        ]
        last_exception = None

        # Attempt each URL until one succeeds.
        for url in urls_to_try:
            try:
                # If the request is successful, the result is returned immediately.
                return asyncio.run(self.afas.base_get(url=url, schema=GetTitle))
            except Exception as e:
                last_exception = e

        # This code is only reached if all URLs in the loop failed.
        error_message = (
            f"Get title failed after trying all fallbacks: {last_exception}. "
            "Make sure to unblock the title in the Profit configuration or create a "
            "custom connector named and defined ProfitTitles_2 with the exact same schema if you do not have the rights to unblock the title in the Profit configuration."
        )
        # Raise a new exception that includes the context from the last failure.
        raise Exception(error_message) from last_exception
