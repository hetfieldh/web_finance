# tests\test_auth.py


def test_login_page_loads(test_client):
    response = test_client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.data


def test_successful_login_and_logout(test_client, new_user):
    login_response = test_client.post(
        "/login",
        data={"login_ou_email": "testuser", "senha": "password"},
        follow_redirects=True,
    )

    assert login_response.status_code == 200
    assert b"Dashboard" in login_response.data
    assert b"Test" in login_response.data

    logout_response = test_client.get("/logout", follow_redirects=True)
    assert logout_response.status_code == 200
    assert b"Login" in logout_response.data


def test_failed_login_with_wrong_password(test_client, new_user):
    response = test_client.post(
        "/login",
        data={"login_ou_email": "testuser", "senha": "wrongpassword"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Login ou senha incorretos" in response.data
    assert b"Dashboard" not in response.data
