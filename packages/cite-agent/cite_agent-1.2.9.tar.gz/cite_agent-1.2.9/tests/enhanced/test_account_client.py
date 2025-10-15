def test_academic_email_validation_accepts_common_domains():
    from nocturnal_archive.setup_config import NocturnalConfig

    config = NocturnalConfig()

    assert config._is_academic_email("student@university.edu")
    assert config._is_academic_email("researcher@college.ac.uk")
    assert not config._is_academic_email("user@example.com")


def test_account_client_offline_credentials_are_deterministic():
    from nocturnal_archive.account_client import AccountClient

    email = "student@university.edu"
    password = "p@ssw0rd!"

    client = AccountClient(base_url=None)
    creds_a = client.provision(email=email, password=password)
    creds_b = client.provision(email=email, password=password)

    assert creds_a == creds_b
    assert creds_a.api_key.startswith("gsk_")
    assert creds_a.account_id
    assert creds_a.auth_token
    assert creds_a.telemetry_token


def test_account_client_respects_control_plane_env(monkeypatch):
    from nocturnal_archive.account_client import AccountClient, AccountProvisioningError

    # With a bogus control plane URL and no requests package we expect a provisioning error.
    monkeypatch.setenv("NOCTURNAL_CONTROL_PLANE_URL", "https://invalid.local")
    client = AccountClient()
    try:
        client.provision("user@school.edu", "password123")
    except AccountProvisioningError:
        pass
    else:
        assert False, "Expected AccountProvisioningError when control plane is unreachable"
    finally:
        monkeypatch.delenv("NOCTURNAL_CONTROL_PLANE_URL", raising=False)
