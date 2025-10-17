import time
from uuid import UUID
import multiprocessing
import uvicorn
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, JSONResponse
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
import sys
from fastdup.vldbaccess import connection_manager

from fastdup.vl.common.logging_init import get_fastdup_logger
from fastdup.vl.common import settings
from fastdup.clustplorer.web import create_app
from fastdup.vl.utils import sentry
from cryptography.fernet import Fernet
from fastdup.vldbaccess.user import UserDB
from fastdup.fastdup_runner.fastdup_runner_server.server_watcher import check_server_running_for_dataset_id
from fastdup.fastdup_runner.utilities import GETTING_STARTED_LINK

LAUNCH_SERVER_MSG_TEMPLATE = f"""
The Visual Layer application was launched on your machine, you can find it on {{}} in your web browser.
Use Ctrl + C to stop the application server.

For more information, use help(fastdup) or check our documentation {GETTING_STARTED_LINK}."""

logger = get_fastdup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_time = time.time()
    yield
    sentry.metrics_distribution("fastdup_exploration_server_runtime", int(time.time() - start_time))
    connection_manager.close_connection_pool()
    await connection_manager.close_async_connection_pool()


class AuthTokenMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if not request.cookies.get('FD_TOKEN', None):
            session_cookie = request.cookies.get('SESSION', None)
            origin_cookie = request.cookies.get('user_origin', None)
            if session_cookie and origin_cookie == 'google':
                user = UserDB.get_by_id(UUID(session_cookie))
                if user:
                    encrypted_user_email = Fernet(settings.Settings.STORAGE_KEY.encode()).encrypt(
                        user.email.encode()).decode()
                    response.set_cookie(key='FD_TOKEN', value=encrypted_user_email, max_age=604800)
                    encrypted_user_avatar = Fernet(settings.Settings.STORAGE_KEY.encode()).encrypt(
                        (user.avatar_uri or "").encode()).decode()
                    response.set_cookie(key='FD_AV', value=encrypted_user_avatar, max_age=604800)
                else:
                    response.delete_cookie(key='SESSION')
                    response.delete_cookie(key='user_origin')
        return response


class UserMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path == "/api/v1/user":
            encrypted_user_email = request.cookies.get('FD_TOKEN', None)
            encrypted_user_avatar = request.cookies.get('FD_AV', None)
            user_email = None
            user_avatar = None
            if encrypted_user_email:
                user_email = Fernet(settings.Settings.STORAGE_KEY.encode()).decrypt(
                    encrypted_user_email.encode()).decode()
                user_avatar = Fernet(settings.Settings.STORAGE_KEY.encode()).decrypt(
                    encrypted_user_avatar.encode()).decode()
            return JSONResponse({"user_id": "1234", "email": user_email, "avatar_uri": user_avatar}, status_code=200)

        # For other endpoints, proceed with the normal request handling
        response = await call_next(request)
        return response


class RedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "" or request.url.path == "/" or request.url.path.startswith(f"/datasets"):
            new_path = f"/dataset/{str(settings.Settings.DATASET_ID)}/data"
            redirect_url = request.url.replace(path=new_path, query='page=1')
            return RedirectResponse(url=str(redirect_url), status_code=307)

        response = await call_next(request)
        return response


def run_server_process(port: int) -> None:
    app = create_app(lifespan=lifespan)

    @app.exception_handler(StarletteHTTPException)
    async def custom_404_handler(request, exc):
        if exc.status_code == 500:
            sentry.sentry_capture_exception("server", exc, extra_tags={"path": request.url.path})
        if exc.status_code == 404 and (
                request.url.path.startswith("/dataset/") or request.url.path.startswith("/login")):
            return FileResponse(path=f"{settings.Settings.LOCAL_FE_DIR}/index.html")
        # If not a 404 error, use the default exception handler
        return await http_exception_handler(request, exc)

    cdn = StaticFiles(directory=settings.Settings.PIPELINE_ROOT / settings.Settings.CDN_FULLPATH,
                      follow_symlink=settings.Settings.COPY_IMAGE_WITH_SYMLINK)
    cdn.__name__ = "cdn"
    app.mount("/cdn", cdn, name="cdn")
    frontend = StaticFiles(directory=settings.Settings.LOCAL_FE_DIR, html=True)
    frontend.__name__ = "frontend"
    app.mount("/", frontend, name="static")
    app.add_middleware(RedirectMiddleware)
    app.add_middleware(AuthTokenMiddleware)
    app.add_middleware(UserMiddleware)

    if 'ipykernel' in sys.modules:  # jupyter notebook
        import nest_asyncio
        nest_asyncio.apply()

    uvicorn.run(app, host="0.0.0.0", port=port, log_level=settings.Settings.LOG_LEVEL)


def launch_server(port: int) -> None:
    multiprocessing.Process(target=check_server_running_for_dataset_id,
                            args=(str(settings.Settings.DATASET_ID), port)).start()

    try:
        run_server_process(port)
    except KeyboardInterrupt as e:
        print('\nThank you for using Visual Layer, the application server on your machine is now closed.\nBye!')
