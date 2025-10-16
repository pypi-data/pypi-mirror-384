import asyncio
import pandas as pd
from typing import Optional, List, Dict, Any
import requests
import json
import base64
import warnings

from .schemas.subject_reaction import KnReaction, KnReactionAttachment, KnReactionLabel, KnReactionEmoji, VisibilityEnum, EmojiEnum, FileAttachment
from brynq_sdk_functions import Functions

class ReactionDossierItem:
    """Reaction Dossier Item management class for AFAS integration; connector KnSubjectReaction"""

    def __init__(self, afas_connector):
        """
        Initialize ReactionDossierItem class with AFAS connector

        Args:
            afas_connector: AFAS connection handler instance
        """
        self.afas = afas_connector
        # Remove /connectors from base_url and add /profitrestservices/subjectconnector
        base_without_connectors = self.afas.base_url.replace('/connectors', '')
        self.get_url = f"{base_without_connectors}/subjectconnector"
        self.create_url = f"{self.afas.base_url}/KnSubjectReaction"

    def __check_fields(self, data: dict, required_fields: List[str], allowed_fields: List[str]) -> None:
        """
        Check if required fields are present and if all fields are allowed (aligned with legacy pattern)

        Args:
            data: Dictionary with data to check
            required_fields: List of required field names
            allowed_fields: List of allowed field names

        Raises:
            ValueError: If required fields are missing or invalid fields are present
        """
        # Check required fields
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Check if all fields are allowed
        invalid_fields = [field for field in data.keys() if field not in allowed_fields and field not in required_fields]
        if invalid_fields:
            raise ValueError(f"Invalid fields: {invalid_fields}")

    def get_subject_attachment(self, subject_id: int = None, file_id: int = None) -> requests.Response:
        """
        Get subject attachment information from AFAS

        This method returns base64encoded binary data in the filedata key of the json response.
        You can process this by decoding it and writing it to a file using:
        blob = base64.b64decode(response.json()['filedata'])
        with open('{}/{}'.format(file_directory, filename), 'wb') as f:
            f.write(blob)

        Args:
            subject_id: Subject ID
            file_id: File ID

        Returns:
            requests.Response: Response from AFAS API

        Raises:
            Exception: If get attachment operation fails
        """
        try:
            # Use direct session approach to avoid pagination handling
            url = f"{self.get_url}/{subject_id}/{file_id}"
            request = requests.Request('GET', url=url)
            prepared_request = self.afas.session.prepare_request(request)
            response = self.afas.session.send(prepared_request, timeout=self.afas.timeout)

            return response
        except Exception as e:
            raise Exception(f"Get subject attachment failed: {str(e)}") from e

    def __build_request_body(self, reaction_data: KnReaction) -> dict:
        """
        Creates request body for reaction using the KnReaction schema

        Args:
            reaction_data: KnReaction object with reaction data

        Returns:
            dict: Request body for AFAS API

        Raises:
            Exception: If building request body fails
        """
        try:
            # Build the base payload structure (aligned with legacy pattern)
            payload = {
                "KnReaction": {
                    "Element": {
                        "Fields": {},
                        "Objects": []
                    }
                }
            }

            # Add required fields (aligned with legacy pattern)
            if reaction_data.sb_id is not None:
                payload["KnReaction"]["Element"]["Fields"]["SbId"] = reaction_data.sb_id

            if reaction_data.sb_tx is not None:
                # Convert bytes to string for JSON serialization
                if isinstance(reaction_data.sb_tx, bytes):
                    payload["KnReaction"]["Element"]["Fields"]["SbTx"] = reaction_data.sb_tx.decode('utf-8')
                else:
                    payload["KnReaction"]["Element"]["Fields"]["SbTx"] = reaction_data.sb_tx

            if reaction_data.va_re is not None:
                payload["KnReaction"]["Element"]["Fields"]["VaRe"] = reaction_data.va_re.value

            # Add optional fields
            if reaction_data.id is not None:
                payload["KnReaction"]["Element"]["Fields"]["Id"] = reaction_data.id

            if reaction_data.rt_id is not None:
                payload["KnReaction"]["Element"]["Fields"]["RTId"] = reaction_data.rt_id

            # Handle objects (attachments, labels, emojis)
            if reaction_data.objects:
                # Group objects by type
                attachments = []
                labels = []
                emojis = []

                for obj in reaction_data.objects:
                    if isinstance(obj, KnReactionAttachment):
                        attachments.append(obj)
                    elif isinstance(obj, KnReactionLabel):
                        labels.append(obj)
                    elif isinstance(obj, KnReactionEmoji):
                        emojis.append(obj)

                # Add attachments object
                if attachments:
                    attachment_body = {
                        "KnReactionAttachment": {
                            "Element": []
                        }
                    }
                    for attachment in attachments:
                        attachment_body["KnReactionAttachment"]["Element"].append({
                            "Fields": {
                                "FileName": attachment.file_name,
                                "FileStream": base64.b64encode(attachment.file_stream).decode("utf-8") if isinstance(attachment.file_stream, bytes) else attachment.file_stream
                            }
                        })
                    payload["KnReaction"]["Element"]["Objects"].append(attachment_body)

                # Add labels object
                if labels:
                    label_body = {
                        "KnReactionLabel": {
                            "Element": []
                        }
                    }
                    for label in labels:
                        label_body["KnReactionLabel"]["Element"].append({
                            "Fields": {
                                "SLId": label.sl_id
                            }
                        })
                    payload["KnReaction"]["Element"]["Objects"].append(label_body)

                # Add emojis object
                if emojis:
                    emoji_body = {
                        "KnReactionEmoji": {
                            "Element": []
                        }
                    }
                    for emoji in emojis:
                        emoji_body["KnReactionEmoji"]["Element"].append({
                            "Fields": {
                                "EmNa": emoji.em_na.value
                            }
                        })
                    payload["KnReaction"]["Element"]["Objects"].append(emoji_body)

            return payload

        except Exception as e:
            raise Exception(f"Build request body failed: {str(e)}")

    def create(self, reaction_data: KnReaction) -> requests.Response:
        """
        Creates a reaction in AFAS using the KnSubjectReaction connector

        Args:
            reaction_data: KnReaction object with reaction data

        Returns:
            requests.Response: Response from AFAS API

        Raises:
            ValueError: If validation fails
            Exception: If creation fails
        """
        try:
            # Validate the reaction data
            reaction_data.model_validate(reaction_data.model_dump())

            # Create request body
            body = self.__build_request_body(reaction_data)

            # Make API request
            response = self.afas.session.post(
                url=self.create_url,
                json=body,
                timeout=self.afas.timeout
            )

            return response

        except Exception as e:
            raise Exception(f"Create reaction failed: {str(e)}") from e



    def delete(self, reaction_id: int) -> requests.Response:
        """
        Delete a reaction by ID

        Args:
            reaction_id: ID of the reaction to delete

        Returns:
            requests.Response: Response from AFAS API
        """
        return self.afas.session.delete(
            url=f"{self.create_url}/{reaction_id}",
            timeout=self.afas.timeout
        )
