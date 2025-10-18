"""Authentication service module."""

import json
from datetime import datetime
from typing import Optional, TYPE_CHECKING

import click
import requests

from testpulcli.exceptions import AuthenticationError
from testpulcli.utils.auth import (
    get_stored_session,
    is_authenticated,
    store_token,
)
from testpulcli.utils.bittensor_utils import get_wallet_by_name
from testpulcli.utils.console import Colors, Console

from bittensor_wallet import Wallet


class AuthService:
    """Service for handling authentication operations."""

    def __init__(self, backend_url: str = "http://localhost:5000") -> None:
        self.backend_url = backend_url

    def authenticate_with_wallet(
        self,
        wallet_name: str,
        hotkey: str = "default",
        force: bool = False,
    ) -> tuple[Optional[str], Optional[Wallet]]:
        """Handle full authentication flow and return token and wallet object."""

        """Handle full authentication flow and return token and wallet object."""
        stored_session = get_stored_session(wallet_name)
        if not force and stored_session and is_authenticated(self.backend_url, stored_session["token"]):
            # Console.info("Using existing valid session.")
            # Still need to load wallet for potential future operations
            wallet = get_wallet_by_name(wallet_name, hotkey=hotkey)
            return stored_session["token"], wallet

        # Console.warning("No valid session found. Performing fresh authentication...")

        # Get wallet - this will ask for password ONCE
        wallet = get_wallet_by_name(wallet_name, hotkey=hotkey)
        if not wallet:
            Console.error(f"Wallet '{wallet_name}' not found.")
            return None, None
        wallet.unlock_coldkey()

        address = wallet.coldkey.ss58_address
        if not address:
            Console.error("Could not retrieve wallet address.")
            return None, None

        Console.info(f"Using address: {address}")

        try:
            # Step 1: Get nonce
            # Console.info("Fetching nonce...")
            nonce_response = requests.get(
                f"{self.backend_url}/api/v1/auth/nonce",
                params={"walletaddress": address},
                timeout=10,
            )
            nonce_response.raise_for_status()
            nonce_data = nonce_response.json()

            if "data" not in nonce_data or "nonce" not in nonce_data["data"]:
                Console.error(f"Invalid nonce response: {nonce_data}")
                return None, None

            nonce = nonce_data["data"]["nonce"]
            # Console.success(f"Nonce: {nonce}")

            # Step 2: Get expected domain from backend
            expected_domain = nonce_data["data"].get("domain", "localhost:5000")
            issued_at = datetime.utcnow().isoformat()[:-3] + "Z"

            message = (
                f"{expected_domain} wants you to sign in with your Substrate account:\n"
                f"{address}\n\n"
                f"Welcome to Pool Operators! Sign in to manage your pools.\n\n"
                f"URI: {self.backend_url}\n"
                f"Version: 1.0.0\n"
                f"Nonce: {nonce}\n"
                f"Issued At: {issued_at}"
            )

            # Step 3: Sign message using already-decrypted wallet
            if click.confirm("Continue with wallet signing?"):
                try:
                    # Use the already decrypted coldkey - no password needed again
                    keypair = wallet.coldkey
                    signature_bytes = keypair.sign(message.encode("utf-8"))
                    signature = "0x" + signature_bytes.hex()
                    Console.success("Signature created successfully.")
                except Exception as sign_error:
                    Console.error(f"Failed to sign message: {sign_error}")
                    return None, None
            else:
                Console.info("Signing cancelled.")
                return None, None

            # Step 4: Verify with backend
            verify_payload = {
                "address": address,
                "message": message,
                "signature": signature,
            }
            verify_response = requests.post(f"{self.backend_url}/api/v1/auth/verify", json=verify_payload, timeout=10)
            verify_response.raise_for_status()
            verify_data = verify_response.json()

            if "data" not in verify_data or "token" not in verify_data["data"]:
                Console.error(f"Authentication failed: {verify_data}")
                return None, None

            token = verify_data["data"]["token"]
            store_token(wallet_name, token, self.backend_url, address)
            Console.success("Authentication successful! Token stored.")
            return token, wallet

        except requests.RequestException as e:
            Console.error(f"API request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    Console.error(f"Error details: {error_data}")
                except Exception:
                    Console.error(f"Response: {e.response.text}")
            return None, None
        except Exception as e:
            Console.error(f"Authentication error: {e}")
            return None, None

    def get_valid_token(self, wallet_name: str) -> Optional[str]:
        """Get a valid token for the wallet, or None if not authenticated."""
        stored_session = get_stored_session(wallet_name)
        if stored_session and is_authenticated(self.backend_url, stored_session["token"]):
            return stored_session["token"]  # type: ignore
        return None

    def logout_all(self) -> None:
        """Clear all stored authentication tokens."""
        from testpulcli.utils.auth import get_config_file

        config_file = get_config_file()
        if not config_file.exists():
            raise AuthenticationError("No stored sessions found.")

        try:
            with open(config_file) as f:
                config = json.load(f)

            if not config:
                raise AuthenticationError("No stored sessions found.")

            config.clear()

            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

            Console.success("All sessions cleared.")
        except Exception as e:
            raise AuthenticationError(f"Failed to clear sessions: {e}")
