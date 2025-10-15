# src/nexgenomics/threads.py

import os
import requests
import dateutil
from . import _internals

class Thread:
    """
    """
    def __init__(self, *, threadid, creator="", created_at=None, updated_at=None):
        self.threadid = threadid
        self.creator = creator
        self.created_at = created_at
        self.updated_at = updated_at
    def __repr__(self):
        return f"Thread({self.threadid!r} creator {self.creator!r} created {self.created_at} updated {self.updated_at})"

    def post_message(self,m):
        url = f"{_internals._get_api_url_stem()}/api/v0/thread/{self.threadid}/message"
        headers = {"Authorization": f"Bearer {_internals._get_api_auth_token()}"}
        data = {
            "msg": m,
        }
        resp = requests.post(url,json=data,headers=headers)
        _internals._handle_api_error(resp)
        return resp.json()["id"]

    def get_messages(self,m):
        url = f"{_internals._get_api_url_stem()}/api/v0/thread/{self.threadid}/messages"
        headers = {"Authorization": f"Bearer {_internals._get_api_auth_token()}"}
        resp = requests.get(url,headers=headers)
        _internals._handle_api_error(resp)
        print (resp)
        return resp.json()

    def call_assistant(self,*,message="",assistant={},context=[]):
        url = f"{_internals._get_api_url_stem()}/api/v0/thread/{self.threadid}/assistant"
        headers = {"Authorization": f"Bearer {_internals._get_api_auth_token()}"}
        data = {
            "msg": message,
            "assistant": assistant,
            "context": context,
        }
        resp = requests.post(url,json=data,headers=headers)
        _internals._handle_api_error(resp)
        return resp.json()

def ping():
    """
    """
    url = f"{_internals._get_api_url_stem()}/api/v0/ping"
    headers = {
        "Authorization": f"Bearer {_internals._get_api_auth_token()}",
    }
    resp = requests.get(url,headers=headers)
    _internals._handle_api_error(resp)
    return resp.json()

def new(*,metadata={},title):
    """
    """
    url = f"{_internals._get_api_url_stem()}/api/v0/thread"
    data = {
        "metadata":metadata,
        "title":title,
    }
    headers = {
        "Authorization": f"Bearer {_internals._get_api_auth_token()}",
    }
    resp = requests.put(url,json=data,headers=headers)
    _internals._handle_api_error(resp)
    t = resp.json()
    return Thread(threadid=t["thread_id"])



def get_list(query_parms={}):
    """
    """
    url = f"{_internals._get_api_url_stem()}/api/v0/threads/list"
    data = {
        # parameters will go here...
    }
    headers = {
        "Authorization": f"Bearer {_internals._get_api_auth_token()}",
    }
    # NB this is a post rather than a get, so we can pass query parms.
    resp = requests.post(url,json=data,headers=headers)
    _internals._handle_api_error(resp)

    threadlist = resp.json()

    def parse_time(t):
        try:
            return dateutil.parser.parse(t)
        except:
            return None

    return [Thread(threadid=x["id"],
        creator=x["creator"],
        created_at=parse_time(x["created_at"]),
        updated_at=parse_time(x["updated_at"]))
        for x in threadlist]
