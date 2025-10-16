import pandas as pd
from typing import Optional, Union
from functools import partial

from .schemas.debtor import (
    DebtorCreate,
    SalesRelationPayload,
    SalesRelationObject,
    SalesRelationElement
)
from .schemas.organisation import (
    PostKnOrganisationFields,
    OrganisationPayload,
    OrganisationObject,
    OrganisationElement
)
from .exceptions import AFASUpdateError

class Debtor:
    """Debtor management class for AFAS integration"""

    def __init__(self, afas_connector):
        """
        Initialize Debtor class with AFAS connector

        Args:
            afas_connector: AFAS connection handler instance
        """
        self.afas = afas_connector

    def create(self, data: Union[pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """
        POST KnSalesRelationOrg.
        """
        try:
            if isinstance(data, pd.Series):
                data = data.to_dict()
            if isinstance(data, pd.DataFrame):
                # If data is a DataFrame, convert it to a list of dicts (records)
                data = data.to_dict(orient="records")

            # Extract organisation connection fields from data if present
            org_connection_fields = {}
            if 'match_organisation' in data:
                org_connection_fields['match_organisation'] = data.pop('match_organisation')
            if 'organisation_id' in data:
                org_connection_fields['organisation_id'] = data.pop('organisation_id')

            fields = DebtorCreate(**data)

            # Handle organisation connection if match_organisation and organisation_id are provided
            objects = None
            if (org_connection_fields.get('match_organisation') is not None and
                org_connection_fields.get('organisation_id') is not None):

                # Create minimal organisation payload for connection
                org_fields = PostKnOrganisationFields(
                    match_organisation=org_connection_fields['match_organisation'],
                    organisation_id=org_connection_fields['organisation_id']
                )

                org_payload = OrganisationPayload(
                    kn_organisation=OrganisationObject(
                        element=OrganisationElement(
                            fields=org_fields
                        )
                    )
                )

                objects = [org_payload]

            payload_model = SalesRelationPayload(
                kn_sales_relation_org=SalesRelationObject(
                    element=SalesRelationElement(
                        fields=fields,
                        objects=objects
                    )
                )
            )
            payload = payload_model.model_dump(
                by_alias=True, mode="json", exclude_none=True
            )
            return self.afas.base_post("KnSalesRelationOrg", payload, return_meta=return_meta)
        except AFASUpdateError:
            raise
        except Exception as e:
            raise Exception(f"Unexpected error in Debtor create: {e}") from e

    def update(self, data: Union[pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """
        PUT KnSalesRelationOrg.
        """
        try:
            if isinstance(data, pd.Series):
                data = data.to_dict()

            # Extract organisation connection fields from data if present
            org_connection_fields = {}
            if 'match_organisation' in data:
                org_connection_fields['match_organisation'] = data.pop('match_organisation')
            if 'organisation_id' in data:
                org_connection_fields['organisation_id'] = data.pop('organisation_id')

            fields = DebtorCreate(**data)

            # Handle organisation connection if match_organisation and organisation_id are provided
            objects = None
            if (org_connection_fields.get('match_organisation') is not None and
                org_connection_fields.get('organisation_id') is not None):

                # Create minimal organisation payload for connection
                org_fields = PostKnOrganisationFields(
                    match_organisation=org_connection_fields['match_organisation'],
                    organisation_id=org_connection_fields['organisation_id']
                )

                org_payload = OrganisationPayload(
                    kn_organisation=OrganisationObject(
                        element=OrganisationElement(
                            fields=org_fields
                        )
                    )
                )

                objects = [org_payload]

            payload_model = SalesRelationPayload(
                kn_sales_relation_org=SalesRelationObject(
                    element=SalesRelationElement(
                        fields=fields,
                        objects=objects
                    )
                )
            )
            payload = payload_model.model_dump(
                by_alias=True, mode="json", exclude_none=True
            )
            return self.afas.base_put("KnSalesRelationOrg", payload, return_meta=return_meta)
        except AFASUpdateError:
            raise
        except Exception as e:
            raise Exception(f"Unexpected error in Debtor update: {e}") from e
