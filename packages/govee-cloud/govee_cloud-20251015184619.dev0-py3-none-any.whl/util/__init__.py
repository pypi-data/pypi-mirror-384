import logging
from types import SimpleNamespace

from aiohttp import ClientSession, TraceRequestStartParams, TraceRequestEndParams

logger = logging.getLogger("govee-cloud")


async def on_request_start(
    session: ClientSession, context: SimpleNamespace, params: TraceRequestStartParams
) -> None:
    logger.info("making %s request to %s", params.method, params.url)


async def on_request_end(
    session: ClientSession, context: SimpleNamespace, params: TraceRequestEndParams
) -> None:
    data = await params.response.read()
    data = data.decode("utf-8") if data else None
    logger.info(
        "%s request to %s completed with status %s and data %s",
        params.method,
        params.url,
        params.response.status,
        data,
    )
