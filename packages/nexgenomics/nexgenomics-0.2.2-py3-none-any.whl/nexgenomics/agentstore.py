# src/nexgenomics/agentstore.py


import requests
from typing import Union
from . import _internals


def get_agents():
    print ("balls")




class Agentstore:
    def __init__(self,auth_token=""):
        self.auth_token = auth_token

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def ping(self) -> Union[str,dict]:
        url = "https://agentstore.nexgenomics.ai/api/ping"
        headers = {
            "Authorization": f"Bearer {self.auth_token}"
        }
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        else:
            raise RuntimeError (f"api call status {resp.status_code}")

    def agents(self):
        url = "https://agentstore.nexgenomics.ai/api/agents"
        headers = {
            "Authorization": f"Bearer {self.auth_token}"
        }
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        else:
            raise RuntimeError (f"api call status {resp.status_code}")

