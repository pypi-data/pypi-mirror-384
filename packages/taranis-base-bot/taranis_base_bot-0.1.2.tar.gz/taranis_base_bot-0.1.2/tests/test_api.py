def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data == {"status": "ok"}


def test_modelinfo(client):
    response = client.get("/modelinfo")
    assert response.status_code == 200
    data = response.get_json()
    assert data == {"model": "test"}


def test_root_avail(client):
    response = client.post("/", json={"text": "Health check text."})
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_request_parser_success(client_with_request_parser):
    response = client_with_request_parser.post("/", json={"text": "A valid dict"})
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    assert data["text"] == "A valid dict"


def test_request_parser_invalid_input(client_with_request_parser):
    response = client_with_request_parser.post("/", json={"another_key": "An invalid dict"})
    assert response.status_code == 400
    data = response.get_json()
    assert isinstance(data, dict)
    assert data["error"] == "Data must contain 'text' key"


def test_predict_success(client_with_predict):
    response = client_with_predict.post("/", json={"text": "a" * 15})
    assert response.status_code == 200
    result = response.get_json()
    assert isinstance(result, dict)
    assert result["len"] == 15


def test_predict_invalid_input(client_with_predict):
    response = client_with_predict.post("/", json={"text": ("this", "is", "not", "a", "string")})
    result = response.get_json()
    assert isinstance(result, dict)
    assert result["error"] == "Input is not a string!"


def test_invalid_json(client):
    response = client.post("/", data="notjson", content_type="application/json")
    assert response.status_code == 400


def test_valid_json_but_not_dict(client):
    """Test valid JSON that isn't a dictionary"""
    # This mimics: curl -d '"notjson"' (valid JSON string, not a dict)
    response = client.post("/", data='"notjson"', content_type="application/json")
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Payload must be a dict!"


def test_missing_authorization_header_with_api_key(client_with_api_key):
    """Test missing Authorization header when API key is required"""
    response = client_with_api_key.post("/", json={"text": "test"})
    assert response.status_code == 401
    data = response.get_json()
    assert data["error"] == "not authorized"


def test_malformed_authorization_header_syntax(client_with_api_key):
    """Test malformed Authorization header - the exact issue you encountered"""
    # This mimics: curl -H "Authorization Bearer: test-api-key-123" (missing colon after Authorization)
    headers = {"Authorization Bearer": "test-api-key-123"}
    response = client_with_api_key.post("/", json={"text": "test"}, headers=headers)
    assert response.status_code == 401
    data = response.get_json()
    assert data["error"] == "not authorized"


def test_malformed_authorization_header_no_bearer(client_with_api_key):
    """Test Authorization header without Bearer prefix"""
    headers = {"Authorization": "test-api-key-123"}  # Missing "Bearer " prefix
    response = client_with_api_key.post("/", json={"text": "test"}, headers=headers)
    assert response.status_code == 401
    data = response.get_json()
    assert data["error"] == "not authorized"


def test_correct_authorization_header(client_with_api_key):
    """Test correct Authorization header format"""
    headers = {"Authorization": "Bearer test-api-key-123"}
    response = client_with_api_key.post("/", json={"text": "test"}, headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_wrong_api_key(client_with_api_key):
    """Test wrong API key"""
    headers = {"Authorization": "Bearer wrong-api-key"}
    response = client_with_api_key.post("/", json={"text": "test"}, headers=headers)
    assert response.status_code == 401
    data = response.get_json()
    assert data["error"] == "not authorized"


def test_modelinfo_func_ok(requests_mock, client_with_modelinfo_fn):
    requests_mock.get(
        "https://huggingface.co/api/models/test_model",
        json={"model": "test_model", "ok": True},
        status_code=200,
    )

    response = client_with_modelinfo_fn.get("/modelinfo")
    assert response.status_code == 200

    data = response.get_json()
    assert data == {"model": "test_model", "ok": True}


def test_modelinfo_func_error(requests_mock, client_with_modelinfo_fn):
    """Modelinfo endpoint should handle network errors gracefully."""
    requests_mock.get(
        "https://huggingface.co/api/models/test_model",
        exc=Exception("Connection failed"),
    )

    response = client_with_modelinfo_fn.get("/modelinfo")
    assert response.status_code == 200

    data = response.get_json()
    assert data == {"model": "test_model", "error": "Connection failed"}
