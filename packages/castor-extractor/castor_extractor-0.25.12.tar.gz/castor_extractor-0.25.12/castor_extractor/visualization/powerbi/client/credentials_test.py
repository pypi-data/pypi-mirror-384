from .credentials import DEFAULT_SCOPE, PowerbiCredentials


def test_credentials():
    tenant_id = "any_tenant_id"
    client_id = "any_client_id"
    secret = "🤫"

    # no scopes provided
    credentials = PowerbiCredentials(
        tenant_id=tenant_id,
        client_id=client_id,
        secret=secret,
    )
    assert credentials.scopes == [DEFAULT_SCOPE]

    credentials = PowerbiCredentials(
        tenant_id=tenant_id,
        client_id=client_id,
        secret=secret,
        scopes=None,
    )
    assert credentials.scopes == [DEFAULT_SCOPE]

    # empty scopes
    credentials = PowerbiCredentials(
        tenant_id=tenant_id,
        client_id=client_id,
        secret=secret,
        scopes=[],
    )
    assert credentials.scopes == []

    # with scopes
    scopes = ["foo"]
    credentials = PowerbiCredentials(
        tenant_id=tenant_id,
        client_id=client_id,
        secret=secret,
        scopes=scopes,
    )
    assert credentials.scopes == scopes
