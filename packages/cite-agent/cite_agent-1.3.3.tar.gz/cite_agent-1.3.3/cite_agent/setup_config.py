#!/usr/bin/env python3
"""
Automatic setup and configuration for Cite Agent
"""

import os
from getpass import getpass
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from .account_client import AccountClient, AccountCredentials, AccountProvisioningError

KEY_PLACEHOLDER = "__KEYRING__"
KEYRING_SERVICE = "Cite Agent"
DEFAULT_QUERY_LIMIT = 25

# Production: Users don't need API keys - backend has them
# Optional research API keys for advanced features (not required)
MANAGED_SECRETS: Dict[str, Dict[str, Any]] = {
    "OPENALEX_API_KEY": {
        "label": "OpenAlex",
        "prompt": "OpenAlex API key (optional)",
        "optional": True,
    },
    "PUBMED_API_KEY": {
        "label": "PubMed",
        "prompt": "PubMed API key (optional)",
        "optional": True,
    },
}

class NocturnalConfig:
    """Handles automatic configuration and setup"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".nocturnal_archive"
        self.config_file = self.config_dir / "config.env"
        self.ensure_config_dir()
        self._keyring = None
        try:
            import keyring  # type: ignore

            self._keyring = keyring
        except Exception:
            self._keyring = None
    
    def ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        self.config_dir.mkdir(exist_ok=True)
    
    def interactive_setup(self) -> bool:
        """Interactive setup for account authentication and configuration."""
        print("🚀 Cite Agent Beta Setup")
        print("=" * 40)
        print()

        # Check if session exists
        from pathlib import Path
        session_file = Path.home() / ".nocturnal_archive" / "session.json"
        
        # Check if we have actual credentials (not just auto-generated config)
        existing_config = self.load_config()
        has_credentials = (
            existing_config.get("NOCTURNAL_ACCOUNT_EMAIL") or 
            existing_config.get("NOCTURNAL_AUTH_TOKEN")
        )
        
        if session_file.exists() and has_credentials:
            print("✅ Configuration already exists!")
            response = input("Do you want to reconfigure? (y/N): ").strip().lower()
            if response not in ["y", "yes"]:
                return True
        elif has_credentials and not session_file.exists():
            print("⚠️  Found saved credentials but no active session.")
            print("Let's get you authenticated...")

        print("You'll use your institution-issued account to sign in. No invite codes or manual API keys required.")
        print()

        email = self._prompt_academic_email()
        if not email:
            return False

        password = self._prompt_password()
        if not password:
            return False

        if not self._confirm_beta_terms():
            print("❌ Terms must be accepted to continue")
            return False

        try:
            credentials = self._provision_account(email, password)
        except AccountProvisioningError as exc:
            print(f"❌ Could not verify your account: {exc}")
            return False

        # Save session.json for authentication
        import json
        session_data = {
            "email": credentials.email,
            "account_id": credentials.account_id,
            "auth_token": credentials.auth_token,
            "refresh_token": credentials.refresh_token,
            "issued_at": credentials.issued_at
        }
        session_file.parent.mkdir(parents=True, exist_ok=True)
        session_file.write_text(json.dumps(session_data, indent=2))

        print("\n🛡️  Recap of beta limitations:")
        for item in self._beta_limitations():
            print(f" • {item}")
        print()

        if not self._confirm("I understand the beta limitations above (Y/n): "):
            print("❌ Please acknowledge the beta limitations to continue")
            return False

        config: Dict[str, Any] = {
            "NOCTURNAL_ACCOUNT_EMAIL": credentials.email,
            "NOCTURNAL_ACCOUNT_ID": credentials.account_id,
            "NOCTURNAL_AUTH_TOKEN": credentials.auth_token,
            "NOCTURNAL_REFRESH_TOKEN": credentials.refresh_token,
            "NOCTURNAL_TELEMETRY_TOKEN": credentials.telemetry_token,
            "NOCTURNAL_ACCOUNT_ISSUED_AT": credentials.issued_at or "",
            "NOCTURNAL_TELEMETRY": "1",
            "NOCTURNAL_TERMS_ACCEPTED": "1",
            "NOCTURNAL_LIMITATIONS_ACK": "1",
            "NOCTURNAL_CONFIG_VERSION": "2.0.0",
        }

        self.save_config(config)

        print("\n✅ Configuration saved successfully!")
        print("🎉 You're ready to use Cite Agent!")

        return True

    def _confirm(self, prompt: str) -> bool:
        response = input(prompt).strip().lower()
        return response in ["", "y", "yes"]

    def _prompt_academic_email(self) -> Optional[str]:
        for attempt in range(5):
            email = input("Academic email address: ").strip()
            if not email:
                print("❌ Email cannot be empty")
                continue
            if not self._is_academic_email(email):
                print("❌ Email address must use an academic domain (e.g. .edu, .ac.uk)")
                continue
            return email.lower()
        print("❌ Could not capture a valid academic email after multiple attempts")
        return None

    def _prompt_password(self) -> Optional[str]:
        for attempt in range(5):
            password = getpass("Account password: ")
            if not password:
                print("❌ Password cannot be empty")
                continue
            if len(password) < 8:
                print("⚠️  Passwords should be at least 8 characters long.")
                confirm = input("Continue with this password? (y/N): ").strip().lower()
                if confirm not in ["y", "yes"]:
                    continue
            confirm_password = getpass("Confirm password: ")
            if password != confirm_password:
                print("❌ Passwords do not match")
                continue
            return password
        print("❌ Could not confirm password after multiple attempts")
        return None

    def _provision_account(self, email: str, password: str) -> AccountCredentials:
        client = AccountClient()
        return client.provision(email=email, password=password)

    def _is_academic_email(self, email: str) -> bool:
        if "@" not in email:
            return False
        local, domain = email.split("@", 1)
        if not local or not domain:
            return False
        domain = domain.lower()
        # Accept domains containing edu/ac anywhere except the top-most TLD (to allow edu.mx, ac.uk, etc.)
        parts = domain.split(".")
        if len(parts) < 2:
            return False
        academic_markers = {"edu", "ac"}
        return any(part in academic_markers for part in parts)

    def _store_secret(self, name: str, value: str) -> bool:
        if not value or not self._keyring:
            return False
        try:
            self._keyring.set_password(KEYRING_SERVICE, name, value)
            return True
        except Exception:
            return False

    def _persist_secret(self, name: str, value: Optional[str], persist_config: bool = True) -> bool:
        if not value:
            return False
        stored = self._store_secret(name, value)
        if stored and persist_config:
            config = self.load_config()
            config[name] = KEY_PLACEHOLDER
            config["NOCTURNAL_SECRET_BACKEND"] = "keyring"
            self.save_config(config)
        return stored

    def _configure_optional_secrets(self, existing_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        config_updates: Dict[str, Any] = {}
        current_config = existing_config or {}
        optional_keys = [key for key, meta in MANAGED_SECRETS.items() if meta.get("optional") and key != "GROQ_API_KEY"]
        if not optional_keys:
            return config_updates

        print("🔑 Optional integrations")
        print("Provide any additional API keys you already have. Press Enter to skip a provider.")
        for secret_name in optional_keys:
            meta = MANAGED_SECRETS[secret_name]
            if current_config.get(secret_name):
                continue
            prompt_text = f"{meta.get('prompt', secret_name)} (optional): "
            try:
                value = getpass(prompt_text)
            except Exception:
                value = input(prompt_text)
            if not value:
                continue
            stored = self._persist_secret(secret_name, value, persist_config=False)
            config_updates[secret_name] = KEY_PLACEHOLDER if stored else value
            if stored:
                print(f"   • Stored {meta.get('label', secret_name)} key securely in your keychain.")
            else:
                print(f"   • Saved {meta.get('label', secret_name)} key to config.env (plaintext). Consider configuring a keychain backend.")
        return config_updates

    def import_secrets(self, secrets: Dict[str, str], allow_plaintext: bool = True) -> Dict[str, Tuple[bool, str]]:
        results: Dict[str, Tuple[bool, str]] = {}
        config = self.load_config()
        for name, value in secrets.items():
            if name not in MANAGED_SECRETS:
                continue
            if not value:
                results[name] = (False, "empty value")
                continue
            stored = self._persist_secret(name, value, persist_config=False)
            if stored:
                config[name] = KEY_PLACEHOLDER
                results[name] = (True, "stored in keyring")
            elif allow_plaintext:
                config[name] = value
                results[name] = (True, "stored in config file")
            else:
                results[name] = (False, "keyring unavailable and plaintext disabled")
        if results:
            self.save_config(config)
        return results

    def import_from_env_file(self, path: str, allow_plaintext: bool = True) -> Dict[str, Tuple[bool, str]]:
        env_path = Path(path).expanduser()
        if not env_path.exists():
            raise FileNotFoundError(f"Secrets file not found: {env_path}")
        secrets: Dict[str, str] = {}
        with open(env_path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                secrets[key.strip()] = value.strip().strip('\"')
        return self.import_secrets(secrets, allow_plaintext=allow_plaintext)

    def _retrieve_secret(self, name: str) -> Optional[str]:
        if not self._keyring:
            return None
        try:
            return self._keyring.get_password(KEYRING_SERVICE, name)
        except Exception:
            return None

    def _notify_keyring_success(self):
        print("🔐 Stored Groq API key securely in your system keychain.")

    def _warn_keyring_fallback(self):
        if self._keyring is None:
            print("⚠️  Could not access the system keychain. Storing the key in config.env instead.")
        else:
            print("⚠️  Keychain write failed; falling back to plain-text storage in config.env.")

    def _ensure_query_limit(self, config: Dict[str, str]) -> bool:
        if config.get("NOCTURNAL_QUERY_LIMIT") != str(DEFAULT_QUERY_LIMIT):
            config["NOCTURNAL_QUERY_LIMIT"] = str(DEFAULT_QUERY_LIMIT)
            config.pop("NOCTURNAL_QUERY_LIMIT_SIG", None)
            return True
        if "NOCTURNAL_QUERY_LIMIT_SIG" in config:
            config.pop("NOCTURNAL_QUERY_LIMIT_SIG", None)
            return True
        return False

    def _beta_limitations(self) -> List[str]:
        return [
            "Daily usage capped at 25 queries per tester",
            "Complex shell / filesystem commands remain sandboxed",
            "Research API may rate-limit during heavy usage",
            "Telemetry is always on and streamed to the control plane",
            "Beta builds auto-update on launch"
        ]

    def _confirm_beta_terms(self) -> bool:
        print("📜 Beta Participation Terms")
        print("You are agreeing to: confidential use, providing feedback, and abiding by the usage limits.")
        print("For full details see the Beta Agreement included with your invite.")
        return self._confirm("Do you accept the beta terms? (Y/n): ")

    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            f.write("# Cite Agent Configuration\n")
            f.write("# Generated automatically - do not edit manually\n\n")
            
            for key, value in config.items():
                if value:  # Only save non-empty values
                    f.write(f"{key}={value}\n")
    
    def load_config(self) -> Dict[str, str]:
        """Load configuration from file"""
        config = {}
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
        return config
    
    def setup_environment(self):
        """Set up environment variables from config"""
        config = self.load_config()
        dirty = False
        if self._ensure_query_limit(config):
            dirty = True
        limit_value = int(config.get("NOCTURNAL_QUERY_LIMIT", str(DEFAULT_QUERY_LIMIT)))
        os.environ["NOCTURNAL_QUERY_LIMIT"] = str(limit_value)
        os.environ.pop("NOCTURNAL_QUERY_LIMIT_SIG", None)
        for key, value in config.items():
            if key not in MANAGED_SECRETS:
                if not os.getenv(key) and value:
                    os.environ[key] = value
                continue

            if value == KEY_PLACEHOLDER:
                secret = self._retrieve_secret(key)
                if secret and not os.getenv(key):
                    os.environ[key] = secret
                continue

            if value and value != KEY_PLACEHOLDER and self._store_secret(key, value):
                config[key] = KEY_PLACEHOLDER
                config["NOCTURNAL_SECRET_BACKEND"] = "keyring"
                if not os.getenv(key):
                    os.environ[key] = value
                dirty = True
                continue

            if not os.getenv(key) and value:
                os.environ[key] = value
        if dirty:
            self.save_config(config)
        return len(config) > 0
    
    def check_setup(self) -> bool:
        """Check if setup is complete"""
        config = self.load_config()
        return (
            self.config_file.exists()
            and bool(config.get('NOCTURNAL_ACCOUNT_EMAIL'))
            and bool(config.get('NOCTURNAL_AUTH_TOKEN'))
        )
    
    def get_setup_status(self) -> Dict[str, Any]:
        """Get detailed setup status"""
        config = self.load_config()
        secret_status: Dict[str, bool] = {}
        for key in MANAGED_SECRETS:
            in_config = config.get(key)
            if in_config == KEY_PLACEHOLDER:
                secret_status[key] = bool(self._retrieve_secret(key)) or bool(os.getenv(key))
            else:
                secret_status[key] = bool(in_config) or bool(os.getenv(key))
        return {
            "configured": self.check_setup(),
            "config_file": str(self.config_file),
            "openalex_configured": secret_status.get('OPENALEX_API_KEY', False),
            "pubmed_configured": secret_status.get('PUBMED_API_KEY', False),
            "account_email": config.get('NOCTURNAL_ACCOUNT_EMAIL'),
            "account_id": config.get('NOCTURNAL_ACCOUNT_ID'),
            "terms_accepted": config.get('NOCTURNAL_TERMS_ACCEPTED') == '1',
            "config_keys": list(config.keys())
        }

def auto_setup():
    """Automatic setup function"""
    config = NocturnalConfig()
    
    # Try to setup environment from existing config
    if config.setup_environment():
        return True
    
    # If no config exists, run interactive setup
    print("🔧 Cite Agent needs initial setup")
    return config.interactive_setup()

def get_config():
    """Get configuration instance"""
    return NocturnalConfig()

if __name__ == "__main__":
    auto_setup()
