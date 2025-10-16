import pandas as pd
from typing import Any, List, Optional
from pydantic import ValidationError
from .schemas.subscription import (
    SubscriptionPayload, SubscriptionObject, SubscriptionElement,
    SubscriptionLinesSchema, SubscriptionLinesObject, SubscriptionLineElement,
    PostSubscriptionLineFields, PostSubscriptionHeaderFields
)
from .exceptions import AFASUpdateError

class Subscription:
    """Subscription management class for AFAS integration, part of 'AFAS Verkoop en Orders API'
       https://docs.afas.help/apidoc/nl/Verkoop%20en%20Orders#post-/connectors/FbSubscription"""

    def __init__(self, afas_connector: Any) -> None:
        """
        Initialize Subscription class with AFAS connector

        Args:
            afas_connector: AFAS connection handler instance
        """
        self.afas = afas_connector

    def create(self, df: pd.DataFrame, *, return_meta: bool = True) -> Optional[List[dict]]:
        """
        POST FbSubscription.

        Args:
            df: DataFrame containing subscription header and line data, grouped by subscription_id
            return_meta: Whether to return metadata from the API response

        Returns:
            List of response metadata if return_meta=True, otherwise None

        Raises:
            ValueError: If validation fails or required columns are missing
            AFASUpdateError: If the AFAS API returns an error
        """
        try:
            if "person_id_in_organisation" not in df.columns:
                raise ValueError("DataFrame must contain a 'person_id_in_organisation' column. which will collect all sublines.")

            # Check if any person_id_in_organisation values are None or empty string
            if df["person_id_in_organisation"].isna().any() or (df["person_id_in_organisation"] == "").any():
                raise ValueError("person_id_in_organisation cannot be None or empty string")

            results = []

            # Each group represents one complete subscription with all its lines
            for sub_id, group_df in df.groupby("person_id_in_organisation"):
                # Prepare the DataFrame group for Pydantic

                # Get header field names from schema
                header_field_names = set(PostSubscriptionHeaderFields.model_fields.keys())
                header_aliases = {
                    field_info.alias
                    for field_info in PostSubscriptionHeaderFields.model_fields.values()
                    if field_info.alias
                }
                all_header_field_identifiers = header_field_names | header_aliases

                # Build header fields from first row (only header schema fields)
                first_row = group_df.iloc[0].to_dict()
                header_data = {k: v for k, v in first_row.items() if k in all_header_field_identifiers}
                header_fields = PostSubscriptionHeaderFields(**header_data)

                # Create line elements (exclude header fields, include extra fields)
                line_elements = [
                    SubscriptionLineElement(
                        fields=PostSubscriptionLineFields(**{k: v for k, v in row.items() if k not in all_header_field_identifiers})
                    )
                    for row in group_df.to_dict(orient="records")
                ]

                # Assemble the final nested payload structure
                payload_model = SubscriptionPayload(
                    fb_subscription=SubscriptionObject(
                        element=SubscriptionElement(
                            fields=header_fields,
                            objects=[
                                SubscriptionLinesSchema(
                                    fb_subscription_lines=SubscriptionLinesObject(
                                        element=line_elements
                                    )
                                )
                            ]
                        )
                    )
                )

                payload = payload_model.model_dump(
                    by_alias=True, mode="json", exclude_none=True
                )

                result = self.afas.base_post("FbSubscription", payload, return_meta=return_meta)
                if return_meta and result:
                    results.append(result)

            return results if return_meta else None

        except AFASUpdateError:
            raise
        except ValidationError as e:
            raise ValueError(f"Validation error: {str(e)}") from e
        except Exception as e:
            raise Exception(f"Unexpected error in Subscription create: {e}") from e

    def update(self, df: pd.DataFrame, *, return_meta: bool = True) -> Optional[List[dict]]:
        """
        PUT FbSubscription.

        Args:
            df: DataFrame containing subscription header and line data, grouped by subscription_id
            return_meta: Whether to return metadata from the API response

        Returns:
            List of response metadata if return_meta=True, otherwise None

        Raises:
            ValueError: If validation fails or required columns are missing
            AFASUpdateError: If the AFAS API returns an error
        """
        try:
            if "subscription_id" not in df.columns:
                raise ValueError("DataFrame must contain a 'subscription_id' column.")

            # Check if any subscription_id values are None or empty string
            if df["subscription_id"].isna().any() or (df["subscription_id"] == "").any():
                raise ValueError("subscription_id cannot be None or empty string")

            results = []

            # Each group represents one complete subscription with all its lines
            for sub_id, group_df in df.groupby("subscription_id"):
                # Prepare the DataFrame group for Pydantic
                group_df_cleaned = group_df.copy()
                for col in group_df_cleaned.select_dtypes(include='datetime64[ns]').columns:
                    group_df_cleaned[col] = group_df_cleaned[col].dt.date.replace({pd.NaT: None})

                group_df_cleaned = group_df_cleaned.replace({float('nan'): None})

                # Get header field names from schema
                header_field_names = set(PostSubscriptionHeaderFields.model_fields.keys())
                header_aliases = {
                    field_info.alias
                    for field_info in PostSubscriptionHeaderFields.model_fields.values()
                    if field_info.alias
                }
                all_header_field_identifiers = header_field_names | header_aliases

                # Build header fields from first row (only header schema fields)
                first_row = group_df_cleaned.iloc[0].to_dict()
                header_data = {k: v for k, v in first_row.items() if k in all_header_field_identifiers}
                header_fields = PostSubscriptionHeaderFields(**header_data)

                # Create line elements (exclude header fields, include extra fields)
                line_elements = [
                    SubscriptionLineElement(
                        fields=PostSubscriptionLineFields(**{k: v for k, v in row.items() if k not in all_header_field_identifiers})
                    )
                    for row in group_df_cleaned.to_dict(orient="records")
                ]

                # Assemble the final nested payload structure
                payload_model = SubscriptionPayload(
                    fb_subscription=SubscriptionObject(
                        element=SubscriptionElement(
                            fields=header_fields,
                            objects=[
                                SubscriptionLinesSchema(
                                    fb_subscription_lines=SubscriptionLinesObject(
                                        element=line_elements
                                    )
                                )
                            ]
                        )
                    )
                )

                payload = payload_model.model_dump(
                    by_alias=True, mode="json", exclude_none=True
                )

                result = self.afas.base_put("FbSubscription", payload, return_meta=return_meta)
                if return_meta and result:
                    results.append(result)

            return results if return_meta else None

        except AFASUpdateError:
            raise
        except ValidationError as e:
            raise ValueError(f"Validation error: {str(e)}") from e
        except Exception as e:
            raise Exception(f"Unexpected error in Subscription update: {e}") from e
