# Copyright © 2025 Contrast Security, Inc.
# See https://www.contrastsecurity.com/enduser-terms-0317a for more details.
import io
from operator import attrgetter

from aiohttp.web import BaseRequest
from contrast.agent.assess.policy.source_policy import (
    cs__apply_source,
    build_source_node,
)
from contrast.agent.request_context import RequestContext
from contrast.utils.decorators import fail_loudly


# the following sources are purposely omitted from source tracking:
# version
# method
# scheme
AIOHTTP_REQUEST_SOURCES = {
    "url._val": "URI",
    "rel_url._val": "URI",
    "host": "HEADER",
    "remote": "OTHER",
    "path_qs": "URI",
    "path": "URI",
    "raw_path": "URI",
    "query": "PARAMETER",
    "query_string": "QUERYSTRING",
    "headers": "HEADER",
    "raw_headers": "HEADER",
    "cookies": "COOKIE",
    "content_type": "HEADER",
    "charset": "HEADER",
    # body sources handled in policy
}


SOURCE_DICT = {
    "module": "aiohttp.web.BaseRequest",
    "instance_method": False,
    "target": "RETURN",
    "policy_patch": False,
}


@fail_loudly("Failed to convert aiohttp request to environ dict")
async def aiohttp_request_to_environ(request):
    """
    Converts an aiohttp.web.BaseRequest object to a valid WSGI environ dictionary
    """
    if ":" in request.host:
        host, port = request.host.split(":", 1)
    else:
        host = request.host
        port = "80"

    if request.content_type == "multipart/form-data":
        body = (
            b"Contrast placeholder - "
            b"we cannot safely capture aiohttp multipart form data"
        )
        real_body = False
    else:
        body = await request.read()
        real_body = True

    path = request.path
    query_string = request.query_string

    environ = {
        "REQUEST_METHOD": request.method,
        "SCRIPT_NAME": "",
        "SERVER_NAME": host,
        "SERVER_PORT": port,
        "PATH_INFO": path,
        "QUERY_STRING": query_string,
        "SERVER_PROTOCOL": f"HTTP/{request.version[0]}.{request.version[1]}",
        "REMOTE_ADDR": request.remote,
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": request.scheme,
        "wsgi.input": io.BytesIO(body),
        "wsgi.errors": io.BytesIO(),
        "wsgi.multithread": True,
        "wsgi.multiprocess": True,
        "wsgi.run_once": False,
    }

    if request.content_length is not None:
        environ["CONTENT_LENGTH"] = (
            request.content_length if real_body else str(len(body))
        )
    if request.content_type is not None:
        environ["CONTENT_TYPE"] = request.content_type if real_body else "text/plain"

    for name, value in request.headers.items():
        if name.lower() in ("content-length", "content-type"):
            continue
        corrected_name = f"HTTP_{name.upper().replace('-', '_')}"
        if corrected_name in environ:
            value = environ[corrected_name] + "," + value
        environ[corrected_name] = value

    return environ


def track_aiohttp_request_sources(context: RequestContext, request: BaseRequest):
    """
    Explicitly tracks all relevant attributes of an aiohttp.web.BaseRequest object. This
    is similar to the environ/scope trackers.
    """
    if not context.assess_enabled:
        return

    for src_name, src_type in AIOHTTP_REQUEST_SOURCES.items():
        if attr := attrgetter(src_name)(request):
            node = build_source_node(SOURCE_DICT, src_name, src_type)
            cs__apply_source(
                context, node, attr, request, attr, (), {}, source_name=src_name
            )
