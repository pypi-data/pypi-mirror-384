import asyncio
from typing import Any, Dict, Optional, Union

import pandas as pd

from .exceptions import AFASUpdateError
from .schemas.bank_account import (
    BankAccountElement,
    BankAccountElementItem,
    BankAccountPayload,
    BankAccountPerson,
    GetBankAccountSchema,
    KnBankAccount,
    KnBankAccountObject,
    PostBankAccountPerson,
)
from .schemas.person import PersonElementBase


def _as_bool(value: Any) -> Optional[bool]:
    """Convert common truthy/falsy representations to bool."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        return cleaned.lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


class PersonBankAccountHandler:
    """Wrapper class to provide person-specific bank account operations."""

    def __init__(self, bank_account_instance: "BankAccount") -> None:
        """
        Initialize with a BankAccount service instance.

        Args:
            bank_account_instance: The BankAccount class instance from afas_connector.
        """
        self._bank_account = bank_account_instance

    def create(self, data: Union[pd.Series, Dict[str, Any]], *, return_meta: bool = True):
        """
        Create bank account for person.

        Args:
            data: Bank account data as dictionary or Series.
            return_meta: Whether to return metadata from API response.

        Returns:
            API response metadata if return_meta=True, otherwise None.
        """
        if isinstance(data, pd.Series):
            data = data.to_dict()
        if not isinstance(data, dict):
            data = dict(data)

        # Set defaults for person creation if not provided
        if "auto_number" not in data:
            data = dict(data)
            data.setdefault("match_person", "7")  # Always create new
            data.setdefault("auto_number", True)  # Generate new person_id

        return self._bank_account.create(data, return_meta=return_meta)

    def update(self, data: Union[pd.Series, Dict[str, Any]], *, return_meta: bool = True):
        """
        Update bank account for person.

        Args:
            data: Bank account data as dictionary or Series.
            return_meta: Whether to return metadata from API response.

        Returns:
            API response metadata if return_meta=True, otherwise None.
        """
        if isinstance(data, pd.Series):
            data = data.to_dict()
        if not isinstance(data, dict):
            data = dict(data)

        # Set match_person to find existing person by person_id
        if "match_person" not in data and data.get("person_id") is not None:
            data = dict(data)
            data["match_person"] = "0"  # Match existing person on person_id

        return self._bank_account.update(data, return_meta=return_meta)


class BankAccount:
    """Bank account management class for AFAS integration."""

    def __init__(self, afas_connector: Any) -> None:
        self.afas = afas_connector
        self.get_url = f"{self.afas.base_url}/brynq_sdk_bank_accounts"

    def get(self, filter_fields: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Retrieve bank account information from AFAS."""
        return asyncio.run(
            self.afas.base_get(
                url=self.get_url,
                schema=GetBankAccountSchema,
                filter_fields=filter_fields,
            )
        )

    def create(self, data: Union[pd.Series, Dict[str, Any]], *, return_meta: bool = True) -> Optional[dict]:
        """Create a bank account record for a person via KnPerson connector."""
        try:
            normalised = self._normalise_input(data)
            payload = self._build_person_payload_dict(normalised, action="insert", for_update=False)
            return self.afas.base_post("KnPerson", payload, return_meta=return_meta)
        except AFASUpdateError:
            raise
        except Exception as exc:
            raise Exception(f"Unexpected error in BankAccount.create: {exc}") from exc

    def update(self, data: Union[pd.Series, Dict[str, Any]], *, return_meta: bool = True) -> Optional[dict]:
        """Update a bank account record for a person via KnPerson connector."""
        try:
            normalised = self._normalise_input(data)
            if not normalised.get("person_id"):
                raise ValueError("person_id is required when updating a bank account.")
            payload = self._build_person_payload_dict(normalised, action="update", for_update=True)
            return self.afas.base_put("KnPerson", payload, return_meta=return_meta)
        except AFASUpdateError:
            raise
        except Exception as exc:
            raise Exception(f"Unexpected error in BankAccount.update: {exc}") from exc

    def _normalise_input(self, data: Union[pd.Series, Dict[str, Any]]) -> Dict[str, Any]:
        """Ensure input is a plain mutable dictionary."""
        if isinstance(data, pd.Series):
            data = data.to_dict()
        if not isinstance(data, dict):
            try:
                data = dict(data)
            except Exception as exc:  # pragma: no cover - defensive conversion
                raise TypeError("BankAccount expects dict-like input data.") from exc
        return dict(data)

    def _build_person_payload_dict(
        self,
        data: Dict[str, Any],
        *,
        action: Optional[str],
        for_update: bool,
    ) -> Dict[str, Any]:
        """Construct the nested KnPerson payload for person bank account operations."""
        person_fields = self._build_person_fields(data, for_update=for_update)
        bank_fields = self._build_bank_fields(data)

        payload_model = BankAccountPayload(
            kn_person=BankAccountPerson(
                element=BankAccountElement(
                    fields=person_fields,
                    objects=[
                        KnBankAccountObject(
                            kn_bank_account=KnBankAccount(
                                element=[BankAccountElementItem(fields=bank_fields)]
                            )
                        )
                    ],
                )
            )
        )

        payload = payload_model.model_dump(by_alias=True, mode="json", exclude_none=True)
        element_payload = payload.get("KnPerson", {}).get("Element", {})

        if action is None:
            element_payload.pop("@action", None)
        elif action != "insert":
            element_payload["@action"] = action

        return payload

    def _build_person_fields(self, data: Dict[str, Any], *, for_update: bool) -> PersonElementBase:
        """Extract and validate the person element fields."""
        person_keys = PersonElementBase.model_fields.keys()
        person_data = {key: data[key] for key in person_keys if key in data}

        if for_update:
            person_data.pop("auto_number", None)
            if not person_data.get("person_id"):
                raise ValueError("person_id is required for person bank account updates.")
        else:
            if not person_data.get("person_id"):
                person_data.setdefault("auto_number", True)

        for bool_field in ("auto_number", "equals_mail_address", "add_to_portal"):
            if bool_field in person_data:
                person_data[bool_field] = _as_bool(person_data[bool_field])

        return PersonElementBase(**person_data)

    def _build_bank_fields(self, data: Dict[str, Any]) -> PostBankAccountPerson:
        """Extract and validate the bank account fields for a person."""
        bank_keys = PostBankAccountPerson.model_fields.keys()
        bank_data: Dict[str, Any] = {key: data[key] for key in bank_keys if key in data}


        for bool_field in ("iban_check", "accept_blocked_bank_account", "accept_cheque"):
            if bool_field in bank_data:
                bank_data[bool_field] = _as_bool(bank_data[bool_field])

        return PostBankAccountPerson(**bank_data)
