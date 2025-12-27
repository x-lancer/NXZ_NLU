#!/usr/bin/env python3
# coding=utf-8
import requests
from pprint import pprint


def demo():
    domain_url = "http://localhost:8000/api/v1/nlu/domain"
    intent_url = "http://localhost:8000/api/v1/nlu/intent"
    resp = requests.post(intent_url, json={
        "domain": "车控",
        "text": "打开主驾车窗",
        "context": {},
        "session_id": "session_123"
    })
    pprint(resp.json())


if __name__ == '__main__':
    demo()
