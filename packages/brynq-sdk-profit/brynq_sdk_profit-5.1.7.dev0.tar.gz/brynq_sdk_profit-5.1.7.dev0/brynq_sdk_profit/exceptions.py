import base64
from typing import Optional
import requests


class AFASUpdateError(requests.RequestException):
    """
    AFAS update error that decodes X-Profit-Error and renders a ready-to-log string.
    No payload guessing; callers pick their own identifiers.
    """
    def __init__(self, *, request_info, history, status, message, headers, text: Optional[str], url: Optional[str] = None, payload: Optional[dict] = None):
        super().__init__(message)
        # Store attributes that requests.RequestException expects
        self.request_info = request_info
        self.history = history
        self.status = status
        self.message = message
        self.headers = dict(headers or {})
        self.text: str = (text or "")
        self.external_message: str = self._decode_external(self.headers, self.text)
        self.profit_log_reference: Optional[str] = self.headers.get("X-Profit-Log-Reference")
        self.content_type: str = self.headers.get("Content-Type", "application/json; charset=utf-8")
        self.url: Optional[str] = url  # Store the URL for better error reporting
        self.payload: Optional[dict] = payload  # Store the payload for debugging

    @staticmethod
    def _decode_external(headers: dict, body_text: str) -> str:
        """
        Prefer AFAS' X-Profit-Error (base64). Fallback to body text if header absent.
        Keep it simple; extend to JSON/XML if you ever need more.
        """
        xpe = headers.get("X-Profit-Error")
        if xpe:
            try:
                return base64.b64decode(xpe).decode("utf-8")
            except (ValueError, UnicodeDecodeError):
                return xpe
        return (body_text or "").strip() or "Onbekende fout"

    def __str__(self) -> str:
        """
        Produce the exact, human-friendly message you want when doing f"{e}".
        Example:
        HTTP STATUS CODE == '500'. REASON == 'Internal Server Error'.
        DECODED ERROR MESSAGE == 'Vul een waarde in bij 'Nummer'.'. LOG_REF == 'ABC123'. URL='...'. PAYLOAD == {...}
        """
        import json

        # In our raise-site we pass message=resp.reason, so .message is the reason phrase
        reason = self.message or ""
        parts = [
            f"HTTP STATUS CODE == '{self.status}'.",
            f"REASON == '{reason}'."
        ]
        if self.external_message:
            # Don't truncate - include the full decoded error message
            parts.append(f"DECODED ERROR MESSAGE == '{self.external_message}'.")
        if self.profit_log_reference:
            parts.append(f"LOG_REF == '{self.profit_log_reference}'.")
        # Use self.url if request_info is not available (for requests library calls)
        url_to_display = None
        if self.request_info and self.request_info.url:
            url_to_display = str(self.request_info.url)
        elif self.url:
            url_to_display = self.url
        if url_to_display:
            parts.append(f"URL='{url_to_display}'.")
        # Include the payload for debugging/replication
        if self.payload:
            try:
                payload_str = json.dumps(self.payload, indent=2, ensure_ascii=False)
                parts.append(f"PAYLOAD == {payload_str}")
            except Exception:
                parts.append(f"PAYLOAD == {str(self.payload)}")
        return " ".join(parts)
