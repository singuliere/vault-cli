import pytest

from vault_cli import client


def get_client(backend, **additional_kwargs):
    kwargs = {
        "backend": backend,
        "url": "http://vault:8000",
        "verify": True,
        "base_path": "bla",
        "certificate": None,
        "token": "tok",
        "username": None,
        "password": None,
        "ca_bundle": None,
    }
    kwargs.update(additional_kwargs)
    return client.get_client_from_kwargs(**kwargs)


@pytest.mark.parametrize("backend", ["requests", "hvac"])
def test_token(requests_mock, backend):
    client_obj = get_client(backend)
    requests_mock.get("http://vault:8000/v1/bla/a",
                      request_headers={'X-Vault-Token': 'tok'},
                      json={"data": {"value": "b"}})

    client_obj.get_secret("a")

    assert requests_mock.called


@pytest.mark.parametrize("backend", ["requests", "hvac"])
def test_userpass(requests_mock, backend):
    requests_mock.post("http://vault:8000/v1/auth/userpass/login/myuser",
                       json={"auth": {"client_token": "newtok"}})

    # Initialize a client, check that we get a token
    client_obj = get_client(
        backend=backend,
        token=None,
        username="myuser",
        password="pass",
    )

    # Check that the token is used
    requests_mock.get("http://vault:8000/v1/bla/a",
                      request_headers={'X-Vault-Token': 'newtok'},
                      json={"data": {"value": "b"}})
    assert client_obj.get_secret("a") == "b"

    # Check that we sent the right pasword
    assert requests_mock.request_history[0].json() == {'password': 'pass'}


@pytest.mark.parametrize("backend", ["requests", "hvac"])
def test_get_secret(requests_mock, backend):
    client_obj = get_client(backend)
    requests_mock.get("http://vault:8000/v1/bla/a",
                      json={"data": {"value": "b"}})
    assert client_obj.get_secret("a") == "b"


@pytest.mark.parametrize("backend", ["requests", "hvac"])
def test_get_secret_not_found(requests_mock, backend):
    client_obj = get_client(backend)
    requests_mock.get("http://vault:8000/v1/bla/a", status_code=404,
                      json={"errors": ["Not found"]})
    with pytest.raises(client.VaultAPIException):
        assert client_obj.get_secret("a")


@pytest.mark.parametrize("backend", ["requests", "hvac"])
def test_get_secret_no_verify(requests_mock, backend):
    client_obj = get_client(backend, verify=False)
    requests_mock.get("http://vault:8000/v1/bla/a",
                      json={"data": {"value": "b"}})
    assert client_obj.get_secret("a") == "b"
    assert requests_mock.last_request.verify is False


@pytest.mark.parametrize("backend", ["requests", "hvac"])
def test_list_secrets(requests_mock, backend):
    client_obj = get_client(backend)
    requests_mock.get("http://vault:8000/v1/bla/a?list=True",
                      json={"data": {"keys": ["b"]}})
    assert client_obj.list_secrets("a") == ["b"]


@pytest.mark.parametrize("backend", ["requests", "hvac"])
def test_list_secrets_empty(requests_mock, backend):
    client_obj = get_client(backend)
    requests_mock.get("http://vault:8000/v1/bla/a?list=True",
                      status_code=404,
                      json={"errors": ["not found"]})
    assert client_obj.list_secrets("a") == []


@pytest.mark.parametrize("backend", ["requests", "hvac"])
def test_list_secrets_other_error(requests_mock, backend):
    client_obj = get_client(backend)
    requests_mock.get("http://vault:8000/v1/bla/a?list=True",
                      status_code=500,
                      json={"errors": ["not found"]})

    with pytest.raises(Exception):
        client_obj.list_secrets("a")


@pytest.mark.parametrize("backend", ["requests", "hvac"])
def test_delete_secret(requests_mock, backend):
    client_obj = get_client(backend)
    requests_mock.delete("http://vault:8000/v1/bla/a", status_code=204)
    client_obj.delete_secret("a")

    assert requests_mock.called


@pytest.mark.parametrize("backend", ["requests", "hvac"])
def test_set_secret(requests_mock, backend):
    client_obj = get_client(backend)
    # Both post and put can be used
    requests_mock.put("http://vault:8000/v1/bla/a", status_code=204, json={})
    requests_mock.post("http://vault:8000/v1/bla/a", status_code=204, json={})
    client_obj.set_secret("a", "b")

    assert requests_mock.called
    assert requests_mock.request_history[0].json() == {'value': 'b'}
