import uvicorn
from fastapi import FastAPI

from typing import Union, Optional, List, Tuple

def run_fastapi(
    app: Union[str, "FastAPI"],
    *,
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = True,
    workers: Optional[int] = None,
    log_level: str = "info",
    use_colors: bool = True,
    proxy_headers: bool = True,
    forwarded_allow_ips: str = "*",
    root_path: Optional[str] = None,
    ssl_keyfile: Optional[str] = None,
    ssl_certfile: Optional[str] = None,
    headers: Optional[List[Tuple[str, str]]] = None,
    factory: bool = False,
    lifespan: str = "auto",
    access_log: bool = True,
) -> None:
    """
    Run a FastAPI app with uvicorn (like Flask's app.run).

    Parameters
    ----------
    app : Union[str, FastAPI]
        Either a FastAPI instance **or** an import string "module:variable".
        Use the string form when `reload=True` for proper hot-reload.
    host : str
        Host to bind. Use "127.0.0.1" for local only or "0.0.0.0" to expose.
    port : int
        Port to bind.
    reload : bool
        Enable hot reload (development only). Requires `app` as "module:var".
    workers : Optional[int]
        Number of worker processes (production-ish). Incompatible with reload.
    log_level : str
        "critical" | "error" | "warning" | "info" | "debug" | "trace"
    use_colors : bool
        Colorize logs.
    proxy_headers : bool
        Respect X-Forwarded-* headers (useful behind reverse proxies).
    forwarded_allow_ips : str
        Which IPs to trust for proxy headers. "*" trusts all.
    root_path : Optional[str]
        ASGI root path (when behind a reverse proxy path prefix).
    ssl_keyfile / ssl_certfile : Optional[str]
        TLS key/cert to serve HTTPS directly.
    headers : Optional[List[Tuple[str, str]]]
        Extra HTTP response headers to set globally.
    factory : bool
        If True, `app` points to a factory callable "module:create_app".
    lifespan : str
        "auto" | "on" | "off" — controls ASGI lifespan handling.
    access_log : bool
        Enable request access log.
    """
    if reload and workers:
        raise ValueError("`workers` cannot be used with `reload=True`.")

    # If reload is requested, strongly prefer the string form for `app`
    # so Uvicorn can re-import on changes. If you pass a FastAPI instance
    # with reload on, hot-reload may not work reliably.
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        workers=workers or 1,
        log_level=log_level,
        use_colors=use_colors,
        proxy_headers=proxy_headers,
        forwarded_allow_ips=forwarded_allow_ips,
        root_path=root_path,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
        headers=headers,
        factory=factory,
        lifespan=lifespan,
        access_log=access_log,
    )