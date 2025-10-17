import asyncio
import pandas as pd
from typing import Optional, List, Dict, Any
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import ValidationError
# Assume 'afas_connector' is your authenticated AFAS connection handler instance.
# Assume all the 'KnSubject...' Pydantic schemas you provided are in a file named 'schemas.py'
from .schemas.subject_reaction import KnSubjectPutSchema, KnSubjectElement, KnSubjectFields, Objects, KnSubjectLink, KnSubjectAttachment, KnSubjectWrapper

class Subject:
    """Subject management class for AFAS integration; connector KnSubject."""

    def __init__(self, afas_connector):
        """
        Initialize Subject class with AFAS connector.

        Args:
            afas_connector: An AFAS connection handler instance with a 'session' and 'base_url'.
        """
        self.afas = afas_connector
        # The URL for the PUT request to update a KnSubject item.
        self.put_url = f"{self.afas.base_url}/KnSubject"

    def update(
        self,
        sb_id: int,
        st: bool,
        dt_st: datetime,
        attachments: Optional[List[KnSubjectAttachment]] = None,
        links: Optional[List[KnSubjectLink]] = None,
        additional_fields: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """
        Updates a dossier item (KnSubject) in AFAS.
        """
        try:
            fields_data = KnSubjectFields(
                st=st,
                dt_st=dt_st,
                additional_fields=additional_fields or {}
            )

            # Only create an Objects model if attachments or links are provided.
            objects_data = None
            if attachments or links:
                objects_data = Objects(
                    kn_subject_attachment=attachments,
                    kn_subject_link=links
                )

            # Build the payload using the schema structure.
            subject_element = KnSubjectElement(
                sb_id=sb_id,
                fields=fields_data,
                objects=objects_data
            )

            # This now wraps the data in {"Element": ...}
            subject_wrapper = KnSubjectWrapper(element=subject_element)

            # This wraps it all in {"KnSubject": ...}
            payload_schema = KnSubjectPutSchema(kn_subject=subject_wrapper)

            # Convert to a clean JSON string, omitting any keys that are None.
            request_body_json = payload_schema.model_dump_json(by_alias=True, exclude_none=True)

            response = self.afas.session.put(
                url=self.put_url,
                data=request_body_json,
                headers={'Content-Type': 'application/json'},
                timeout=self.afas.timeout
            )
            response.raise_for_status()
            return response

        except ValidationError as e:
            raise Exception(f"Invalid data for updating subject {sb_id}: {e}") from e
        except Exception as e:
            raise Exception(f"Failed to update subject {sb_id}: {e}") from e
