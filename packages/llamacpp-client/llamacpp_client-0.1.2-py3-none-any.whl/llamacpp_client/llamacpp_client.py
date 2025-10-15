import dataclasses
import json
import logging
import random

import requests
import httpx


@dataclasses.dataclass
class LlamaCppServerAddress:
    host: str
    port: int


LOG = logging.getLogger("llamacpp_client")


class LlamaCppClient:
    def __init__(self, endpoints: list[LlamaCppServerAddress]):
        if not all(isinstance(endpoint, LlamaCppServerAddress) for endpoint in endpoints):
            raise ValueError("expected all endpoints to be instances of LlamaCppServerAddress")
        self.endpoints = endpoints

    def completion(self, prompt: str, **params) -> dict:
        endpoint = random.choice(self.endpoints)
        url = f"http://{endpoint.host}:{endpoint.port}/completion"
        req_payload = {"prompt": prompt, **params}
        LOG.debug("posting to %s: %s", url, json.dumps(req_payload, indent=4))
        response = requests.post(url, json=req_payload)
        resp_payload = response.json()
        LOG.debug("response from %s: %s", url, json.dumps(resp_payload, indent=4))
        return resp_payload

    def v1_chat_completions(self, messages: list, **params) -> dict:
        endpoint = random.choice(self.endpoints)
        url = f"http://{endpoint.host}:{endpoint.port}/v1/chat/completions"
        req_payload = {"messages": messages, **params}
        LOG.debug("posting to %s: %s", url, json.dumps(req_payload, indent=4))
        response = requests.post(url, json=req_payload)
        resp_payload = response.json()
        LOG.debug("response from %s: %s", url, json.dumps(resp_payload, indent=4))
        return resp_payload

    async def async_completion(self, prompt: str, **params):
        endpoint = random.choice(self.endpoints)
        url = f"http://{endpoint.host}:{endpoint.port}/completion"
        req_payload = {"prompt": prompt, **params}
        LOG.info("posting to %s: %s", url, json.dumps(req_payload, indent=4))
        client = httpx.AsyncClient(timeout=None)
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json=req_payload) as response:
                async for chunk in response.aiter_bytes():
                    LOG.debug(
                        "passing through stream chunk: %s",
                        chunk.decode("utf-8", errors="ignore"),
                    )
                    yield chunk

    async def async_v1_chat_completions(self, messages: list, **params):
        endpoint = random.choice(self.endpoints)
        url = f"http://{endpoint.host}:{endpoint.port}/v1/chat/completions"
        req_payload = {"messages": messages, **params}
        LOG.info("posting to %s: %s", url, json.dumps(req_payload, indent=4))
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json=req_payload) as response:
                async for chunk in response.aiter_bytes():
                    LOG.debug(
                        "passing through stream chunk: %s",
                        chunk.decode("utf-8", errors="ignore"),
                    )
                    yield chunk
