import time as _time
import typing as _typing

import fastapi as _fastapi
import starlette.middleware.base as _starlette_middleware_base
import starlette.middleware.cors as _starlette_middleware_cors

from .metrics import (
    HTTP_REQUEST_DURATION,
    HTTP_REQUESTS_COUNT,
    REQUEST_SIZE,
    RESPONSE_SIZE,
)


class PrometheusMiddleware(_starlette_middleware_base.BaseHTTPMiddleware):
    async def dispatch(self, request: _fastapi.Request, call_next):

        if "authorization" in request.headers:
            auth_type = (
                request.headers["authorization"].split()[0]
                if " " in request.headers["authorization"]
                else "none"
            )
        elif "x-api-key" in request.headers:
            auth_type = "X-API-KEY"
        else:
            auth_type = "none"

        route = request.scope.get("route")
        endpoint = getattr(
            route, "path", request.scope.get("path")
        )  # prefer templated path

        start = _time.perf_counter()
        response = await call_next(request)
        duration = _time.perf_counter() - start

        HTTP_REQUESTS_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code,
            auth_type=auth_type,
        ).inc()

        try:
            body = await request.body()
            size = len(body)
        except Exception:
            size = 0

        REQUEST_SIZE.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(size)

        try:
            body = await response.body()
            size = len(body)
        except Exception:
            size = 0

        RESPONSE_SIZE.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(size)

        HTTP_REQUEST_DURATION.labels(
            endpoint=endpoint,
            method=request.method,
        ).observe(duration)

        return response


def add_middleware(
    app: "_fastapi.FastAPI",
    include: _typing.Optional[list[_typing.Literal["metrics", "cors"]]] = None,
):
    """
    Add middleware to the FastAPI app.
    :param app: The FastAPI app to add middleware to.
    :param include: A list of middleware to include. If not provided, all middleware will be added.
    """
    if include is None:
        include = ["metrics", "cors"]

    if "cors" in include:
        app.add_middleware(
            _starlette_middleware_cors.CORSMiddleware,
            allow_origins=[
                "http://localhost:5173",  # vite dev server
                "http://localhost:4173",  # vite preview server
            ],
            allow_origin_regex=r"^https://([a-zA-Z0-9-]+\.)*crypticorn\.(dev|com)/?$",  # matches (multiple or no) subdomains of crypticorn.dev and crypticorn.com
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    if "metrics" in include:
        app.add_middleware(PrometheusMiddleware)
