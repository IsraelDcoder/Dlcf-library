import json
import http.client
import os
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class SupabaseError(RuntimeError):
    pass


def _request(path, method="GET", payload=None, access_token=None, service_role=False):
    base_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    api_key = service_key if service_role else anon_key
    if not base_url or not api_key:
        raise SupabaseError("Supabase is not configured.")

    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"apikey": api_key, "Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    elif service_role:
        headers["Authorization"] = f"Bearer {service_key}"

    request = Request(f"{base_url}{path}", data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=15) as response:
            response_body = response.read()
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise SupabaseError(f"Supabase request failed ({error.code}): {detail}") from error
    except URLError as error:
        raise SupabaseError("Could not reach Supabase.") from error

    if not response_body:
        return {}
    return json.loads(response_body.decode("utf-8"))


def sign_in(email, password):
    return _request(
        "/auth/v1/token?grant_type=password",
        method="POST",
        payload={"email": email, "password": password},
    )


def sign_up(email, password, name):
    return _request(
        "/auth/v1/signup",
        method="POST",
        payload={"email": email, "password": password, "data": {"name": name}},
    )


def get_user(access_token):
    return _request("/auth/v1/user", access_token=access_token)


def refresh_session(refresh_token):
    return _request(
        "/auth/v1/token?grant_type=refresh_token",
        method="POST",
        payload={"refresh_token": refresh_token},
    )


def sign_out(access_token):
    return _request("/auth/v1/logout", method="POST", access_token=access_token)


def update_password(access_token, password):
    return _request("/auth/v1/user", method="PUT", payload={"password": password}, access_token=access_token)


def storage_upload(bucket, object_path, file_stream, content_type):
    base_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not base_url or not service_key:
        raise SupabaseError("Supabase Storage is not configured.")

    encoded_path = quote(object_path, safe="/")
    parsed_url = urlsplit(base_url)
    connection_type = http.client.HTTPSConnection if parsed_url.scheme == "https" else http.client.HTTPConnection
    connection = connection_type(parsed_url.netloc, timeout=60)
    path = f"{parsed_url.path}/storage/v1/object/{quote(bucket, safe='')}/{encoded_path}"
    file_stream.seek(0, os.SEEK_END)
    content_length = file_stream.tell()
    file_stream.seek(0)
    try:
        connection.putrequest("POST", path)
        connection.putheader("apikey", service_key)
        connection.putheader("Authorization", f"Bearer {service_key}")
        connection.putheader("Content-Type", content_type or "application/octet-stream")
        connection.putheader("Content-Length", str(content_length))
        connection.putheader("x-upsert", "false")
        connection.endheaders()
        while chunk := file_stream.read(1024 * 1024):
            connection.send(chunk)
        response = connection.getresponse()
        response_body = response.read()
        if response.status < 200 or response.status >= 300:
            detail = response_body.decode("utf-8", errors="replace")
            raise SupabaseError(f"Supabase Storage upload failed ({response.status}): {detail}")
        return json.loads(response_body.decode("utf-8")) if response_body else {}
    except OSError as error:
        raise SupabaseError("Could not reach Supabase Storage.") from error
    finally:
        connection.close()


def storage_download(bucket, object_path):
    base_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not base_url or not service_key:
        raise SupabaseError("Supabase Storage is not configured.")

    encoded_path = quote(object_path, safe="/")
    url = f"{base_url}/storage/v1/object/{quote(bucket, safe='')}/{encoded_path}"
    request = Request(url, headers={"apikey": service_key, "Authorization": f"Bearer {service_key}"})
    try:
        with urlopen(request, timeout=60) as response:
            return response.read(), response.headers.get_content_type()
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise SupabaseError(f"Supabase Storage download failed ({error.code}): {detail}") from error
    except URLError as error:
        raise SupabaseError("Could not reach Supabase Storage.") from error


def storage_signed_url(bucket, object_path, expires_in=120, download=False):
    encoded_path = quote(object_path, safe="/")
    response = _request(
        f"/storage/v1/object/sign/{quote(bucket, safe='')}/{encoded_path}",
        method="POST",
        payload={"expiresIn": expires_in, "download": download},
        service_role=True,
    )
    signed_path = response.get("signedURL") or response.get("signedUrl")
    if not signed_path:
        raise SupabaseError("Supabase did not return a signed file URL.")
    if signed_path.startswith("http://") or signed_path.startswith("https://"):
        return signed_path
    return f"{os.environ['SUPABASE_URL'].rstrip('/')}{signed_path}"


def storage_delete(bucket, object_path):
    return _request(
        f"/storage/v1/object/{quote(bucket, safe='')}",
        method="DELETE",
        payload={"prefixes": [object_path]},
        service_role=True,
    )


def update_user_app_metadata(user_id, app_metadata):
    return _request(
        f"/auth/v1/admin/users/{quote(str(user_id), safe='')}",
        method="PUT",
        payload={"app_metadata": app_metadata},
        service_role=True,
    )


def user_has_role(access_token, *allowed_roles):
    if not access_token:
        return False
    try:
        user_data = get_user(access_token)
    except SupabaseError:
        return False

    app_metadata = user_data.get("app_metadata") or {}
    user_metadata = user_data.get("user_metadata") or {}
    role = app_metadata.get("role") or user_metadata.get("role") or "student"
    return role.lower() in {allowed_role.lower() for allowed_role in allowed_roles}


def session_role(access_token):
    if not access_token:
        return "student"
    try:
        user_data = get_user(access_token)
    except SupabaseError:
        return "student"

    app_metadata = user_data.get("app_metadata") or {}
    user_metadata = user_data.get("user_metadata") or {}
    role = app_metadata.get("role") or user_metadata.get("role") or "student"
    return role if role in {"admin", "teacher", "student"} else "student"