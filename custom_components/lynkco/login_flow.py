"""Methods for authenticating with Lynk & Co."""

import json
import logging
import urllib.parse
from urllib.parse import quote_plus, unquote

import aiohttp
import pkce
import yarl
from aiohttp.client_exceptions import NonHttpUrlRedirectClientError

_LOGGER = logging.getLogger(__name__)
login_b2c_url = "https://login.lynkco.com/lynkcoprod.onmicrosoft.com/b2c_1a_signin_mfa/"
client_id = "c3e13a0c-8ba7-4ea5-9a21-ecd75830b9e9"
scope_base_url = "https://lynkcoprod.onmicrosoft.com/mobile-app-web-api/mobile"
redirect_uri = "msauth://prod.lynkco.app.crisp.prod/2jmj7l5rSw0yVb%2FvlWAYkK%2FYBwk%3D"
user_lifecycle_base_url = "https://user-lifecycle-tls.aion.connectedcar.cloud/user-lifecycle/api/provisioning/v1/users/"


async def login(
    email: str, password: str, session: aiohttp.ClientSession
) -> tuple[str | None, str | None, str | None, str | None, str | None]:
    """Start login flow using email and password."""

    # Generate authorization URL and query it to fetch cookies
    auth_url, code_verifier, code_challenge = get_auth_uri()
    async with session.get(
        auth_url,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        },
    ) as response:
        if response.status == 200:
            page_view_id = response.headers.get("x-ms-gateway-requestid", "")
            if not page_view_id:
                _LOGGER.error("Authorization failed, page_view_id missing")
                return None, None, None, None, None
            _LOGGER.debug("GET request for authorization successful")
        else:
            _LOGGER.error(
                "GET request for authorization failed with status code: %d",
                response.status,
            )
            return None, None, None, None, None

    cookie_jar = session.cookie_jar.filter_cookies(yarl.URL("https://login.lynkco.com"))
    cookie = cookie_jar.get("x-ms-cpim-trans")
    x_ms_cpim_trans_value = cookie.value if cookie else None
    cookie = cookie_jar.get("x-ms-cpim-csrf")
    x_ms_cpim_csrf_token = cookie.value if cookie else None
    if x_ms_cpim_csrf_token is None or x_ms_cpim_trans_value is None:
        _LOGGER.error("Authorization failed, missing cookies")
        return None, None, None, None, None
    _LOGGER.debug("Authorization successful")

    # Perform login with credentials
    success = await postLogin(
        email, password, x_ms_cpim_trans_value, x_ms_cpim_csrf_token, session
    )
    if success is False:
        _LOGGER.error("Login failed. Exiting")
        return None, None, None, None, None
    _LOGGER.debug("Credentials accepted")

    # Query to retrieve page view ID and referer URL for MFA
    page_view_id, referer_url = await getCombinedSigninAndSignup(
        x_ms_cpim_csrf_token,
        x_ms_cpim_trans_value,
        page_view_id,
        code_challenge,
        session,
    )
    return (
        x_ms_cpim_trans_value,
        x_ms_cpim_csrf_token,
        page_view_id,
        referer_url,
        code_verifier,
    )


def get_auth_uri() -> tuple[str, str, str]:
    """Generate the authorization URL with PKCE parameters."""

    code_verifier, code_challenge = pkce.generate_pkce_pair()

    base_url = f"{login_b2c_url}oauth2/v2.0/authorize"
    params = {
        "response_type": "code",
        "scope": f"{scope_base_url}.read {scope_base_url}.write profile offline_access",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "redirect_uri": redirect_uri,
        "client_id": client_id,
    }

    # Build the full URL with query parameters
    auth_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return auth_url, code_verifier, code_challenge


async def get_tokens_from_redirect_uri(
    uri: str,
    code_verifier: str,
    session: aiohttp.ClientSession,
) -> tuple[str | None, str | None, str | None]:
    """Extract access and refresh tokens from a redirect URI."""

    _LOGGER.debug(f"get_tokens_from_redirect_uri: Parsing URI: {uri}")
    parsed_url = urllib.parse.urlparse(uri)
    _LOGGER.debug(f"get_tokens_from_redirect_uri: Query string: {parsed_url.query}")
    code = urllib.parse.parse_qs(parsed_url.query).get("code", [None])[0]
    _LOGGER.debug(f"get_tokens_from_redirect_uri: Extracted code exists: {code is not None}")

    access_token, refresh_token, id_token = await getTokens(
        code,
        code_verifier,
        session,
    )

    if access_token is None or refresh_token is None or id_token is None:
        _LOGGER.error("Failed to get tokens. Exiting")
        return None, None, None
    return access_token, refresh_token, id_token


async def two_factor_authentication(
    verification_code: str | None,
    x_ms_cpim_trans_value: str | None,
    x_ms_cpim_csrf_token: str | None,
    page_view_id: str | None,
    referer_url: str | None,
    code_verifier: str | None,
    session: aiohttp.ClientSession,
) -> tuple[str | None, str | None, str | None]:
    """Flow to finish login with user provided verification code."""

    # Post the verification code
    success = await postVerification(
        verification_code, x_ms_cpim_trans_value, x_ms_cpim_csrf_token, session
    )
    if success is False:
        _LOGGER.error("Verification failed. Exiting")
        return None, None, None
    _LOGGER.debug("Verification successful")

    # Fetch authorization code from redirect
    code = await getRedirect(x_ms_cpim_trans_value, page_view_id, referer_url, session)
    if code is None:
        _LOGGER.error("Failed to get redirect code. Exiting")
        return None, None, None

    # Exchange authorization code for tokens
    access_token, refresh_token, id_token = await getTokens(
        code,
        code_verifier,
        session,
    )

    if access_token is None or refresh_token is None or id_token is None:
        _LOGGER.error("Failed to get tokens. Exiting")
        return None, None, None
    return access_token, refresh_token, id_token


async def authorize(code_challenge, session):
    base_url = f"{login_b2c_url}oauth2/v2.0/authorize"

    params = {
        "response_type": "code",
        "scope": f"{scope_base_url}.read {scope_base_url}.write profile offline_access",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "redirect_uri": "msauth.com.lynkco.prod.lynkco-app://auth",
        "client_id": client_id,
    }
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    async with session.get(base_url, params=params, headers=headers) as response:
        if response.status == 200:
            page_view_id = response.headers.get("x-ms-gateway-requestid", "")
            _LOGGER.debug("GET request for authorization successful.")
            return page_view_id
        else:
            _LOGGER.error(
                "GET request for authorization failed with status code:",
                response.status,
            )
    return None


async def postLogin(
    email, password, x_ms_cpim_trans_value, x_ms_cpim_csrf_token, session
):
    tx_value = f"StateProperties={x_ms_cpim_trans_value}"
    encoded_tx_value = urllib.parse.quote(tx_value)
    query_params = f"p=B2C_1A_signin_mfa&tx={encoded_tx_value}"
    data = {
        "request_type": "RESPONSE",
        "signInName": email,
        "password": password,
    }
    base_url = f"{login_b2c_url}SelfAsserted"
    headers = {
        "x-csrf-token": x_ms_cpim_csrf_token,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    url_with_params = f"{base_url}?{query_params}"
    async with session.post(url_with_params, headers=headers, data=data) as response:
        if response.status == 200:
            _LOGGER.debug("POST request for login successful.")
            response_text = await response.text()
            _LOGGER.debug(f"Login response length: {len(response_text)} bytes")
            return True
        else:
            _LOGGER.error(
                f"POST request for login failed with status code: {response.status}"
            )
            try:
                response_text = await response.text()
                _LOGGER.error(f"Login error response: {response_text[:500]}")
            except Exception:
                pass
    return False


async def getCombinedSigninAndSignup(
    csrf_token, tx_value, page_view_id, code_challenge, session
):
    url = f"{login_b2c_url}api/CombinedSigninAndSignup/confirmed"
    referer_base_url = f"{login_b2c_url}v2.0/authorize"
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "sec-fetch-site": "same-origin",
        "sec-fetch-dest": "document",
        "accept-language": "en-GB,en;q=0.9",
        "sec-fetch-mode": "navigate",
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
        "referer": f"{referer_base_url}?x-client-Ver=1.2.22&state=ABC&client_info=1&prompt=select_account&response_type=code&x-app-name=Lynk%20%26%20Co&code_challenge_method=S256&x-app-ver=2.12.0&scope=https%3A%2F%2Flynkcoprod.onmicrosoft.com%2Fmobile-app-web-api%2Fmobile.read%20https%3A%2F%2Flynkcoprod.onmicrosoft.com%2Fmobile-app-web-api%2Fmobile.write%20openid%20profile%20offline_access&x-client-SKU=MSAL.iOS&x-client-OS=17.4.1&code_challenge={code_challenge}&x-client-CPU=64&redirect_uri=msauth.com.lynkco.prod.lynkco-app%3A%2F%2Fauth&client-request-id=0207E18F-1598-4BD7-AC0F-705414D8B0F7&client_id={client_id}&x-client-DM=iPhone&return-client-request-id=true&haschrome=1",
        "accept-encoding": "gzip, deflate, br",
    }
    params = {
        "rememberMe": "false",
        "csrf_token": csrf_token,
        "tx": f"StateProperties={tx_value}",
        "p": "B2C_1A_signin_mfa",
        "diags": json.dumps(
            {
                "pageViewId": page_view_id,
                "pageId": "CombinedSigninAndSignup",
                "trace": [],
            }
        ),
    }

    try:
        async with session.get(url, params=params, headers=headers, allow_redirects=False) as response:
            # Check for redirect responses (3xx status codes)
            if response.status in (301, 302, 303, 307, 308):
                location = response.headers.get("Location", "")
                _LOGGER.debug(f"Received redirect to: {location}")

                # If it's redirecting to the mobile app scheme with an error, handle it
                if location.startswith("msauth.com.lynkco"):
                    if "error=" in location:
                        _LOGGER.error(f"Azure AD B2C returned an error redirect: {location}")
                        if "error_description=" in location:
                            try:
                                error_desc_start = location.index("error_description=") + len("error_description=")
                                error_desc_end = location.find("&", error_desc_start)
                                if error_desc_end == -1:
                                    error_desc_end = len(location)
                                error_desc = unquote(location[error_desc_start:error_desc_end])
                                _LOGGER.error(f"Error description: {error_desc}")
                            except Exception:
                                pass
                        return None, None
                    # Otherwise, it's a successful auth - return as before
                    _LOGGER.debug("Successful redirect to mobile app scheme")
                    return None, None

            if response.status == 200:
                new_page_view_id = response.headers.get("x-ms-gateway-requestid")
                if new_page_view_id:
                    constructed_url = f"{url}?{'&'.join([f'{key}={value}' for key, value in params.items() if key != 'diags'])}"
                    diags_dict = json.loads(params["diags"])
                    encoded_diags = quote_plus(json.dumps(diags_dict))
                    constructed_url_with_diags = f"{constructed_url}&diags={encoded_diags}"
                    return new_page_view_id, constructed_url_with_diags
                else:
                    _LOGGER.error("New pageViewId not found in the response headers.")
                    return None, None
            else:
                _LOGGER.error(
                    f"GET request for CombinedSigninAndSignup failed with status code: {response.status}"
                )
    except NonHttpUrlRedirectClientError as e:
        # Azure AD B2C is redirecting to a mobile app deep link
        error_url = str(e)
        _LOGGER.error(f"Azure AD B2C authentication error: {error_url}")

        # Parse the error from the redirect URL
        if "error_description=" in error_url:
            try:
                error_desc_start = error_url.index("error_description=") + len("error_description=")
                error_desc_end = error_url.find("&", error_desc_start)
                if error_desc_end == -1:
                    error_desc_end = len(error_url)
                error_desc = unquote(error_url[error_desc_start:error_desc_end]).replace("%0d%0a", " ")
                _LOGGER.error(f"Authentication failed: {error_desc}")
            except Exception:
                pass

        _LOGGER.error(
            "The Lynk & Co authentication service is experiencing issues. "
            "This may be a temporary server problem. Please try again later, "
            "or check if the Lynk & Co mobile app is working properly."
        )
        return None, None
    return None, None


async def postVerification(
    verification_code, x_ms_cpim_trans_value, x_ms_cpim_csrf_token, session
):
    tx_value = f"StateProperties={x_ms_cpim_trans_value}"
    query_params = f"p=B2C_1A_signin_mfa&tx={urllib.parse.quote(tx_value)}"
    data = {"verificationCode": verification_code, "request_type": "RESPONSE"}
    url = f"{login_b2c_url}SelfAsserted?{query_params}"
    headers = {
        "x-csrf-token": x_ms_cpim_csrf_token,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    async with session.post(url, headers=headers, data=data) as response:
        if response.status == 200:
            _LOGGER.debug("POST request for verification successful.")
            return True
        else:
            _LOGGER.error(
                f"POST verification failed with status code: {response.status}"
            )
    return False


async def getRedirect(tx_value, page_view_id, referer_url, session):
    url = f"{login_b2c_url}api/SelfAsserted/confirmed"
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "sec-fetch-site": "same-origin",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "accept-language": "en-GB,en;q=0.9",
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS like Mac OS X) AppleWebKit (KHTML, like Gecko) Version Mobile Safari",
    }
    # Only add referer if it's not None
    if referer_url:
        headers["referer"] = referer_url

    cookie = session.cookie_jar.filter_cookies("https://login.lynkco.com").get(
        "x-ms-cpim-csrf"
    )
    x_ms_cpim_csrf_token = cookie.value if cookie else None
    params = {
        "csrf_token": x_ms_cpim_csrf_token,
        "tx": f"StateProperties={tx_value}",
        "p": "B2C_1A_signin_mfa",
        "diags": json.dumps(
            {
                "pageViewId": page_view_id,
                "pageId": "SelfAsserted",
                "trace": [],
            }
        ),
    }
    async with session.get(
        url, headers=headers, params=params, allow_redirects=False
    ) as response:
        if response.status in [301, 302]:
            location_header = response.headers.get("location", "")
            code = urllib.parse.parse_qs(
                urllib.parse.urlparse(location_header).query
            ).get("code", [None])[0]
            return code
        else:
            _LOGGER.error(
                f"GET redirect request failed with status code: {response.status}"
            )
    return None


async def getTokens(code, code_verifier, session):
    data = {
        "client_info": "1",
        "scope": f"{scope_base_url}.read {scope_base_url}.write openid profile offline_access",
        "code": code,
        "grant_type": "authorization_code",
        "code_verifier": code_verifier,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
    }

    headers = {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br",
        "x-ms-pkeyauth+": "1.0",
        "x-client-last-telemetry": "4|0|||",
        "x-client-ver": "1.2.22",
        "content-type": "application/x-www-form-urlencoded",
        "user-agent": "LynkCo/3047 CFNetwork/1494.0.7 Darwin/23.4.0",
    }

    url = f"{login_b2c_url}oauth2/v2.0/token"

    _LOGGER.debug(f"getTokens: Requesting tokens from {url}")
    _LOGGER.debug(f"getTokens: code exists: {code is not None}, code_verifier exists: {code_verifier is not None}")

    async with session.post(url, data=data, headers=headers) as response:
        if response.status == 200:
            json_response = await response.json()
            access_token = json_response.get("access_token")
            refresh_token = json_response.get("refresh_token")
            id_token = json_response.get("id_token")

            return access_token, refresh_token, id_token
        else:
            response_text = await response.text()
            _LOGGER.error(f"Failed to obtain tokens. Status code: {response.status}")
            _LOGGER.error(f"Response body: {response_text}")
            _LOGGER.debug(f"Request data keys: {list(data.keys())}")
    return None, None, None


async def get_user_vins(ccc_token: str, user_id: str) -> list[str]:
    """Retrieve VINs associated with a user ID using the CCC token."""

    url = f"{user_lifecycle_base_url}{user_id}/activevehicles"
    headers = {
        "Authorization": f"Bearer {ccc_token}",
        "Content-Type": "application/json",
    }

    _LOGGER.debug(f"Requesting VINs from URL: {url}")
    _LOGGER.debug(f"Using user_id: {user_id}")
    _LOGGER.debug(f"CCC token length: {len(ccc_token) if ccc_token else 0}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, ssl=False) as response:
                _LOGGER.debug(f"VIN retrieval response status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.debug(f"VIN retrieval response data: {data}")
                    # Extract VINs from the response (roles array)
                    vins = []
                    roles = data.get("roles", [])
                    _LOGGER.debug(f"Roles array: {roles}")
                    for role in roles:
                        vin = role.get("vin")
                        if vin:
                            vins.append(vin)
                    _LOGGER.debug(f"Found {len(vins)} VINs for user {user_id}")
                    return vins
                else:
                    response_text = await response.text()
                    _LOGGER.error(
                        f"Failed to retrieve VINs. Status code: {response.status}, Response: {response_text}"
                    )
    except Exception as e:
        _LOGGER.error(f"Error retrieving VINs: {e}", exc_info=True)

    return []
