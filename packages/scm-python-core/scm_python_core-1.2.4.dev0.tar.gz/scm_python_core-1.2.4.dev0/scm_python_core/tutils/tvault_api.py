import tlog.tlogging as tl
import os, platform
import json
import tutils.context_opt as tcontext
import tutils.thpe as thpe
import tio.tfile as tf

import logging
import http.client as http_client

log = tl.log if hasattr(tl, "log") else None

if tl.PRINT_DETAILS:
    http_client.HTTPConnection.debuglevel = 1
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.DEBUG)
    logging.getLogger("urllib3").propagate = True

VAULT_API_BASE_URL = "http://192.168.50.246:8200/v1"


def vault_server_authorization_header(vault_template={}):
    token = (
        vault_template["vault-token"]
        if "vault-token" in vault_template
        else tf.dotenv("vault-root-token")
    )
    headers = {
        "X-Vault-Token": token,
    }
    return headers


def vault_context(**kwargs) -> dict:
    context = thpe.create_env_context()
    vault_template = thpe.load_yaml_from_install(
        f"vilink/vault-template/vault-context", "vilink", skip_replace=True
    )
    extends_dict = tcontext.deep_merge({}, vault_template)
    for key, value in kwargs.items():
        if key.endswith("_LIST") and isinstance(value, list):
            key = f'list::{key.replace("_LIST", "")}'
        extends_dict[key] = value
    return tcontext.deep_merge(context, extends_dict)


def vault_get_sys_keys():
    return thpe.load_yaml_from_install(
        f"vilink/vault-template/vault-sys-keys", "vilink", skip_replace=True
    )


JWT_CLIENT_TOKEN_FILE = (
    os.path.join("/sh", "lib", "jwt_client_token.txt")
    if "Linux" == platform.system()
    else os.path.join(os.path.expanduser("~"), "jwt_client_token.txt")
)


def vault_secret(key: str):
    vault_app_name = "ssz"
    if "VAULT_APP_NAME" in os.environ:
        vault_app_name = os.getenv("VAULT_APP_NAME")
    vault_client_token = (
        tf.readlines(JWT_CLIENT_TOKEN_FILE)[0]
        if os.path.exists(JWT_CLIENT_TOKEN_FILE)
        else "${dotenv::'vault_client_token'}"
    )
    vault_template = {
        "vault-token": vault_client_token,
        "api-cmd": f"secret/data/{vault_app_name}/${{USER_NAME}}",
    }
    try:
        return vault_get(
            context=vault_context(USER_NAME=key),
            vault_template=vault_template,
            filed_name="data",
        )["data"]["password"]
    except Exception as e:
        log.error(e)
        return key


def vault_request(
    context: dict, vault_template_key: str, data_hander=None, filed_name: str = ""
):
    vault_template = thpe.load_yaml_from_install(
        f"vilink/vault-template/{vault_template_key}", "vilink", skip_replace=True
    )
    request_method = vault_template["X"]  # type: ignore
    if request_method == "POST":
        return vault_post(
            context=context, data_hander=data_hander, vault_template=vault_template
        )
    if request_method == "PUT":
        return vault_put(
            context=context, data_hander=data_hander, vault_template=vault_template
        )
    if request_method == "GET":
        return vault_get(
            context=context, filed_name=filed_name, vault_template=vault_template
        )
    if request_method == "LIST":
        return vault_list(
            context=context, filed_name=filed_name, vault_template=vault_template
        )


def vault_post(
    context: dict, vault_template_key="", data_hander=None, vault_template={}
):
    if not vault_template:
        vault_template = thpe.load_yaml_from_install(
            f"vilink/vault-template/{vault_template_key}", "vilink", skip_replace=True
        )
    tcontext.replace_object(context, vault_template)
    api_cmd = vault_template["api-cmd"]  # type: ignore
    url = f"{VAULT_API_BASE_URL}/{api_cmd}"
    data = vault_template["body"] if "body" in vault_template else None  # type: ignore
    if data_hander:
        data_hander(context, data)
    print("-----vault_post", api_cmd, data)
    response = thpe.get_request_session().post(
        url,
        headers=vault_server_authorization_header(vault_template),
        data=json.dumps(data) if data else None,
    )
    if tl.PRINT_DETAILS:
        print(response.request.headers)
        print(response.status_code)
    if response.status_code in (200, 201, 204):
        return response.json() if response.text else response
    else:
        raise Exception(response.text)  # response.text


def vault_put(
    context: dict, vault_template_key="", data_hander=None, vault_template={}
) -> bool:
    if not vault_template:
        vault_template = thpe.load_yaml_from_install(
            f"vilink/vault-template/{vault_template_key}", "vilink", skip_replace=True
        )
    tcontext.replace_object(context, vault_template)
    api_cmd = vault_template["api-cmd"]  # type: ignore
    url = f"{VAULT_API_BASE_URL}/{api_cmd}"
    data = vault_template["body"] if "body" in vault_template else None  # type: ignore
    if data_hander:
        data_hander(context, data)
    print("-----vault_put", api_cmd, data)
    response = thpe.get_request_session().put(
        url,
        headers=vault_server_authorization_header(),
        json=data,
    )
    if response.status_code in (200, 204):
        return True
    else:
        raise Exception(response.text)


def vault_get(
    context: dict, vault_template_key="", filed_name: str = "", vault_template={}
):
    if not vault_template:
        vault_template = thpe.load_yaml_from_install(
            f"vilink/vault-template/{vault_template_key}", "vilink", skip_replace=True
        )
    tcontext.replace_object(context, vault_template)
    api_cmd = vault_template["api-cmd"]  # type: ignore
    url = f"{VAULT_API_BASE_URL}/{api_cmd}"
    if tl.PRINT_DETAILS:
        log.info(f"{url}")
    response = thpe.get_request_session().get(
        url,
        headers=vault_server_authorization_header(vault_template),
    )
    if response.status_code in (200, 201):
        return response.json()[filed_name] if filed_name else response.json()
    else:
        raise Exception(response.text)


def vault_list(
    context: dict, vault_template_key="", filed_name: str = "", vault_template={}
):
    if not vault_template:
        vault_template = thpe.load_yaml_from_install(
            f"vilink/vault-template/{vault_template_key}", "vilink", skip_replace=True
        )
    tcontext.replace_object(context, vault_template)
    api_cmd = vault_template["api-cmd"]  # type: ignore
    url = f"{VAULT_API_BASE_URL}/{api_cmd}"
    if tl.PRINT_DETAILS:
        log.info(f"{url}")
    response = thpe.get_request_session().request(
        "LIST",
        url,
        headers=vault_server_authorization_header(),
    )
    if tl.PRINT_DETAILS:
        print(response.request.headers)
        print(response.status_code)
    if response.status_code in (200, 201):
        return response.json()[filed_name] if filed_name else response.json()
    else:
        raise Exception(response.text)
