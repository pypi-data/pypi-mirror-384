
import os
import configparser


def _get_api_url_stem():
    if a := os.getenv("API_URL_STEM"):
        return a
    try:
        cfg = configparser.ConfigParser()
        cfgpth = os.path.expanduser("~/.nexgenomicsrc")
        cfg.read(cfgpth)
        return cfg["nexgenomics"]["api_url_stem"]
    except:
        pass

    return "https://agentstore.nexgenomics.ai"

def _get_api_auth_token():
    if a := os.getenv("API_AUTH_TOKEN"):
        return a
    try:
        cfg = configparser.ConfigParser()
        cfgpth = os.path.expanduser("~/.nexgenomicsrc")
        cfg.read(cfgpth)
        return cfg["nexgenomics"]["api_auth_token"]
    except:
        pass

    return "not_a_valid_token"

def _handle_api_error(resp):
    if resp.status_code != 200:
        try:
            msg = resp.json()["msg"]
        except:
            msg = ""
        raise Exception (f"status code {resp.status_code} {msg}")



