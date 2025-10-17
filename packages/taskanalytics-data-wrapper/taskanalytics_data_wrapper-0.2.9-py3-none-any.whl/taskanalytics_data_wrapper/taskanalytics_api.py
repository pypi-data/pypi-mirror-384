# %%
import json
import logging

import requests
from tqdm.auto import tqdm

logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# %%
def log_in_taskanalytics(username: str, password: str) -> requests.Response:
    """
    Log into Task Analytics
    """
    session = requests.Session()
    login_url = "https://api-admin.taskanalytics.com/api/v3/auth/login"
    auth = json.dumps(
        {"grant_type": "password", "username": username, "password": password}
    )
    content_type = "application/json"
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/75.0.3770.90 Chrome/75.0.3770.90 Safari/537.36"
    headers: dict[str, str | bytes] = {
        "Content-Type": content_type,
        "user-agent": user_agent,
    }
    session.headers = headers
    try:
        response = session.post(login_url, data=auth)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    return response


# %%
def get_survey_metadata(
    username: str, password: str, survey_id: str, filename_path: str
) -> requests.Response:
    """
    Get survey metadata

    TODO return the data as a json file with option to specify filepath
    """
    session = requests.Session()
    login_url = "https://api-admin.taskanalytics.com/api/v3/auth/login"
    auth = json.dumps(
        {"grant_type": "password", "username": username, "password": password}
    )
    content_type = "application/json"
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/75.0.3770.90 Chrome/75.0.3770.90 Safari/537.36"
    headers: dict[str, str | bytes] = {
        "Content-Type": content_type,
        "user-agent": user_agent,
    }
    session.headers = headers
    try:
        response = session.post(login_url, data=auth)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    obj = json.loads(response.text)
    try:
        data = session.get(
            f"https://api-admin.taskanalytics.com/api/v3/surveys/tm_{survey_id}",
            timeout=120,
            headers={"Authorization": "JWT " + obj["access_token"]},
        )
        response.raise_for_status()
        with tqdm.wrapattr(
            open(filename_path, "wb"),
            "write",
            miniters=1,
            total=int(data.headers.get("content-length", 0)),
            desc=filename_path,
        ) as fout:
            for chunk in data.iter_content(chunk_size=8192):
                fout.write(chunk)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    logging.info("Downloaded metadata for survey %s", survey_id)
    return data


# %%
def download_survey(
    username: str, password: str, survey_id: str, filename_path: str
) -> requests.Response:
    """
    Download a Top Task survey from Task Analytics
    """
    session = requests.Session()
    login_url = "https://api-admin.taskanalytics.com/api/v3/auth/login"
    auth = json.dumps(
        {"grant_type": "password", "username": username, "password": password}
    )
    content_type = "application/json"
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/75.0.3770.90 Chrome/75.0.3770.90 Safari/537.36"
    headers: dict[str, str | bytes] = {
        "Content-Type": content_type,
        "user-agent": user_agent,
        "Accept": "text/csv",
    }
    session.headers = headers
    try:
        response = session.post(login_url, data=auth)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    obj = json.loads(response.text)
    try:
        data = session.post(
            f"https://api-admin.taskanalytics.com/api/v3/export/tm_{survey_id}?",
            timeout=120,
            headers={"Authorization": "JWT " + obj["access_token"]},
        )
        response.raise_for_status()
        with tqdm.wrapattr(
            open(filename_path, "wb"),
            "write",
            miniters=1,
            total=int(data.headers.get("content-length", 0)),
            desc=filename_path,
        ) as fout:
            for chunk in data.iter_content(chunk_size=8192):
                fout.write(chunk)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    logging.info("Downloaded survey %s", survey_id)
    return data


# %%
def download_discovery_survey(
    username: str,
    password: str,
    organization_id: str,
    survey_id: str,
    filename_path: str,
) -> requests.Response:
    """
    Download a discovery survey from Task analytics
    """
    session = requests.Session()
    login_url = "https://api-admin.taskanalytics.com/api/v3/auth/login"
    auth = json.dumps(
        {"grant_type": "password", "username": username, "password": password}
    )
    content_type = "application/json"
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/75.0.3770.90 Chrome/75.0.3770.90 Safari/537.36"
    headers: dict[str, str | bytes] = {
        "Content-Type": content_type,
        "user-agent": user_agent,
        "Accept": "text/csv",
    }
    session.headers = headers
    try:
        response = session.post(login_url, data=auth)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    obj = json.loads(response.text)
    try:
        data = session.get(
            f"https://api-admin.taskanalytics.com/api/v3/organisations/{organization_id}/surveys/tm_{survey_id}/discovery?",
            timeout=120,
            headers={
                "Authorization": "JWT " + obj["access_token"],
                "Accept": "application/json",
            },
        )
        response.raise_for_status()
        with tqdm.wrapattr(
            open(filename_path, "wb"),
            "write",
            miniters=1,
            total=int(data.headers.get("content-length", 0)),
            desc=filename_path,
        ) as fout:
            for chunk in data.iter_content(chunk_size=8192):
                fout.write(chunk)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    logging.info("Downloaded survey %s", survey_id)
    return data


# %%
def get_organization_metadata(
    username: str, password: str, organization_id: str, filename_path: str
) -> requests.Response:
    """
    Download metadata for the organization account, including the surveys object
    """
    session = requests.Session()
    login_url = "https://api-admin.taskanalytics.com/api/v3/auth/login"
    auth = json.dumps(
        {"grant_type": "password", "username": username, "password": password}
    )
    content_type = "application/json"
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/75.0.3770.90 Chrome/75.0.3770.90 Safari/537.36"
    headers: dict[str, str | bytes] = {
        "Content-Type": content_type,
        "user-agent": user_agent,
        "Accept": "text/csv",
    }
    session.headers = headers
    try:
        response = session.post(login_url, data=auth)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    obj = json.loads(response.text)
    try:
        data = session.get(
            f"https://api-admin.taskanalytics.com/api/v3/organisations/{organization_id}",
            timeout=120,
            headers={
                "Authorization": "JWT " + obj["access_token"],
                "Accept": "application/json",
            },
        )
        response.raise_for_status()
        with tqdm.wrapattr(
            open(filename_path, "wb"),
            "write",
            miniters=1,
            total=int(data.headers.get("content-length", 0)),
            desc=filename_path,
        ) as fout:
            for chunk in data.iter_content(chunk_size=8192):
                fout.write(chunk)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    logging.info("Downloaded metadata for organization ID %s", organization_id)
    return data
