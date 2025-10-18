"""Key management service module."""

import time
from typing import Any, Optional

import requests
from rich.table import Table

from testpulcli.exceptions import APIError, KeyManagementError
from testpulcli.utils.auth import get_auth_headers
from testpulcli.utils.console import Console


class KeyManager:
    """Service for managing developer keys."""

    def __init__(self, backend_url: str = "http://localhost:5000") -> None:
        self.backend_url = backend_url

    def create_invoice(self, token: str) -> Optional[dict[str, Any]]:
        """Create invoice + developer key (inactive until paid)."""
        try:
            headers = get_auth_headers(token)
            payload = {"amountDue": 5.0, "currency": "TAO", "purpose": "buy_key"}

            response = requests.post(
                f"{self.backend_url}/api/v1/invoice/create",
                json=payload,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            invoice_data = data["data"]
            Console.success("✅ Invoice created!")
            table = Table(show_header=True)
            table.add_column("Invoice Details", justify="center")
            table.add_row(f"Id: {invoice_data['invoiceId']}")
            Console.print(table)

            return invoice_data
        except requests.RequestException as e:
            raise APIError(f"Failed to create invoice: {e}")
        except Exception as e:
            raise KeyManagementError(f"Failed to create invoice: {e}")

    def get_developer_key_from_backend(self, token: str) -> Optional[str]:
        """Fetch the active developer key from backend."""
        try:
            headers = get_auth_headers(token)
            response = requests.get(f"{self.backend_url}/api/v1/developer/key", headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == 200 and "data" in data:
                return data["data"].get("developerKey") or data["data"].get("key") or data["data"].get("apiKey")  # type: ignore
            return None
        except Exception:
            return None

    def get_invoice_status(self, token: str, invoice_id: str) -> tuple[bool, Optional[str]]:
        """Get invoice status and return (is_paid, developer_key)."""
        try:
            headers = get_auth_headers(token)
            response = requests.get(f"{self.backend_url}/api/v1/invoice/{invoice_id}", headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            invoice = data.get("data", {})

            status = invoice.get("status", "unknown")
            is_paid = status == "paid"

            # Extract developer key if available
            developer_key = invoice.get("developerKey") or invoice.get("key") or invoice.get("apiKey")

            return is_paid, developer_key
        except Exception as e:
            raise APIError(f"Error fetching invoice: {e}")

    def display_invoice_status(self, token: str, invoice_id: str) -> tuple[bool, Optional[str]]:
        """Display invoice status and return (is_paid, developer_key)."""
        is_paid, developer_key = self.get_invoice_status(token, invoice_id)

        invoice = self._get_invoice_details(token, invoice_id)
        status: str = invoice.get("status", "unknown")
        status_icon = "✅" if is_paid else "⏳"

        Console.print_table(
            f"{status_icon} Invoice {invoice_id}",
            [
                f"{'Status:':<20} {status.upper()}",
                f"{'Amount:':<20} {invoice.get('amountDue', 0)} TAO",
                f"{'TX Hash:':<20} {invoice.get('txHash', 'N/A')[:20]}..." if invoice.get("txHash") else "N/A",
                f"{'Paid At:':<20} {invoice.get('paidAt', 'Not Paid')[:19]}",  # type: ignore
            ],
        )

        return is_paid, developer_key

    def _get_invoice_details(self, token: str, invoice_id: str) -> dict[str, Any]:
        """Get detailed invoice information."""
        try:
            headers = get_auth_headers(token)
            response = requests.get(f"{self.backend_url}/api/v1/invoice/{invoice_id}", headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("data", {})  # type: ignore
        except Exception:
            return {}

    def monitor_payment(self, token: str, invoice_id: str, developer_key: str) -> bool:
        """Monitor payment status with user interaction."""
        # Show developer key prominently
        key_display = developer_key if developer_key else "Key not returned"
        Console.print_table(
            "🔑 YOUR DEVELOPER KEY (INACTIVE)",
            [
                f"{'Key:':<20} {key_display}",
                f"{'Status:':<20} ⏳ INACTIVE - Pay to activate",
                f"{'Invoice ID:':<20} {invoice_id}",
                f"{'Cost:':<20} 5 TAO",
            ],
        )

        Console.info("👀 Monitoring payment status (Ctrl+C to stop)...")

        try:
            while True:
                time.sleep(10)
                is_paid, _ = self.display_invoice_status(token, invoice_id)
                if is_paid:
                    Console.success("🎉 PAYMENT CONFIRMED! Key is now ACTIVE!")
                    Console.print_table(
                        "✅ ACTIVE DEVELOPER KEY",
                        [
                            f"{'Status:':<20} ✅ ACTIVE",
                            f"{'Invoice:':<20} PAID",
                        ],
                    )
                    break
        except KeyboardInterrupt:
            Console.info("Monitoring stopped.")

    def list_developer_keys(
        self, token: str, page: int = 1, limit: int = 15, status: Optional[str] = None
    ) -> dict[str, Any]:
        """list all developer keys for a wallet."""
        try:
            headers = get_auth_headers(token)
            params = {"page": page, "limit": limit, "sortBy": "createdAt", "order": "desc"}
            if status:
                params["status"] = status

            Console.info("Fetching developer keys...")
            response = requests.get(
                f"{self.backend_url}/api/v1/developer-key/get/list",
                headers=headers,
                params=params,  # type: ignore
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            # Add null check before accessing nested data
            if data.get("data") is None:
                raise KeyManagementError("Invalid response: 'data' field is None")

            keys_data = data["data"].get("data", [])
            pagination = data["data"].get("pagination", {})

            Console.display_keys_table(keys_data)
            return {"keys": keys_data, "pagination": pagination}
        except requests.RequestException as e:
            raise APIError(f"API request failed: {e}")
        except Exception as e:
            raise KeyManagementError(f"Error fetching keys: {e}")

    def display_keys_list(self, keys_data: list[dict[str, Any]], pagination: dict[str, Any], wallet_name: str) -> None:
        """Display developer keys in a 3-column table."""
        if not keys_data:
            Console.warning("No developer keys found for this wallet.")
            Console.info(f"Create a new key: testpulcli key create --wallet-name {wallet_name}")
            return

        Console.success(f"Found {pagination.get('total', len(keys_data))} developer key(s)\n")

        rows = []
        for idx, key in enumerate(keys_data, 1):
            key_display = key.get("apiKey", "N/A")
            key_status = key.get("status", "unknown").upper()
            rows.append([str(idx), key_display, key_status])

        # Pagination info
        if pagination:
            total_pages = pagination.get("totalPages", 1)
            current_page = pagination.get("page", 1)
            Console.info(f"Page {current_page} of {total_pages}")
            if current_page < total_pages:
                Console.info(f"Next page: testpulcli key list --wallet-name {wallet_name} --page {current_page + 1}")
