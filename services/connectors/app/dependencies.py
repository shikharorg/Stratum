from arq.connections import ArqRedis
from fastapi import Request

from stratum_libs.auth import RequestContext
from stratum_libs.auth import get_request_context as get_request_context  # noqa: F401


async def get_arq_pool(request: Request) -> ArqRedis:
    return request.app.state.arq_pool
