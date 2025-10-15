from __future__ import annotations

import socket
from typing import Any, Type, Union

import requests
from toolforge_weld.api_client import ConnectionError, ToolforgeClient
from toolforge_weld.errors import ToolforgeError, ToolforgeUserError
from toolforge_weld.kubernetes_config import Kubeconfig

from toolforge_components_cli.config import Config


class ComponentsClientError(ToolforgeError):
    """Raised when an HTTP request fails."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)

        if context:
            # property is defined in parent class
            self.context = context


class ComponentsClientUserError(ComponentsClientError, ToolforgeUserError):
    """Raised when an HTTP request fails with a 4xx status code."""


def handle_http_exception(e: requests.exceptions.HTTPError) -> Exception:
    if e.response is None:
        return ComponentsClientError(message="Got no response", context={})

    error_class: Union[Type[ComponentsClientError], Type[ComponentsClientUserError]]
    if 400 <= e.response.status_code <= 499:
        error_class = ComponentsClientUserError
    else:
        error_class = ComponentsClientError

    context = {}
    message = e.response.text
    try:
        data = e.response.json()
        if isinstance(data, dict):
            if "messages" in data and "error" in data["messages"]:
                message = data["messages"]["error"][0]
                context = {"messages": data["messages"]}
        elif isinstance(data, str):
            message = data
    except requests.exceptions.InvalidJSONError:
        pass

    return error_class(message=message, context=context)


def handle_connection_error(e: ConnectionError) -> Exception:
    context = {}
    if isinstance(e, requests.exceptions.HTTPError) and e.response is not None:
        context["body"] = e.response.text

    return ComponentsClientError(
        message="The components service seems to be down – please retry in a few minutes.",
        context=context,
    )


class ComponentsClient(ToolforgeClient):
    def __init__(
        self,
        kubeconfig: Kubeconfig,
        server: str,
        endpoint_prefix: str,
        user_agent: str,
    ):
        super().__init__(
            kubeconfig=kubeconfig,
            server=server + endpoint_prefix,
            user_agent=user_agent,
            exception_handler=handle_http_exception,
            connect_exception_handler=handle_connection_error,
        )

    @classmethod
    def from_config(cls, config: Config):
        host = socket.gethostname()
        kubeconfig = Kubeconfig.load()
        namespace = kubeconfig.current_namespace
        user_agent = f"{namespace}@{host}:components-cli"
        toolname = namespace[len("tool-") :]
        full_endpoint_prefix = (
            f"{config.components.components_endpoint}/tool/{toolname}"
        )
        return cls(
            endpoint_prefix=full_endpoint_prefix,
            kubeconfig=kubeconfig,
            server=config.api_gateway.url,
            user_agent=user_agent,
        )
