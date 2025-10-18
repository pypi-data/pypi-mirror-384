# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import logging
import multiprocessing
import sys
import traceback
from datetime import datetime
from http import HTTPStatus

import uvicorn
from aria_studio.app.common.args import Args
from aria_studio.app.constants import LOCALHOST, LOGGING_PATH, LOGGING_YML_PATH, WIN32

from aria_studio.app.routes import (
    app_routes,
    auth_routes,
    device_routes,
    explorer_routes,
    group_routes,
    local_files_routes,
    mps_routes,
    root_routes,
)
from aria_studio.app.utils import lifespan
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent caching
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        return response


app = FastAPI(title="Aria Studio", lifespan=lifespan)


@app.exception_handler(Exception)
async def validation_exception_handler(request: Request, exc: Exception):
    from aria_studio.app.local.local_log_manager import (
        LocalLogEntry,
        LocalLogEvent,
        LocalLogManager,
        LocalLogScreen,
        LocalLogSurface,
    )

    await LocalLogManager.log_event(
        LocalLogEntry(
            timestamp=int(datetime.now().timestamp()),
            surface=LocalLogSurface.BACK_END,
            event=LocalLogEvent.CRASH,
            screen=LocalLogScreen.CRASH,
            message=f"Failed method {request.method} at URL {request.url}",
            source="".join(traceback.format_exception(None, exc, exc.__traceback__)),
        )
    )

    return JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content={
            "message": (
                f"Failed method {request.method} at URL {request.url}."
                f" Exception message is {exc!r}."
            )
        },
    )


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# adding it so that users can't use public ip to access aria studio on other devices.
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", LOCALHOST])

# Add no-cache middleware to prevent browser caching
app.add_middleware(NoCacheMiddleware)

app.include_router(device_routes.router, prefix="/device")
app.include_router(local_files_routes.router, prefix="/local")
app.include_router(auth_routes.router, prefix="/auth")
app.include_router(mps_routes.router, prefix="/mps")
app.include_router(group_routes.router, prefix="/group")
app.include_router(explorer_routes.router, prefix="/explorer")
app.include_router(app_routes.router, prefix="/app")
app.include_router(root_routes.router, prefix="")


def configure_event_loop() -> asyncio.AbstractEventLoop:
    """
    Configure the appropriate event loop based on platform and requirements.
    Returns:
        asyncio.AbstractEventLoop: The configured event loop.
    """
    if sys.platform == WIN32:
        try:
            # Check if there's any existing event loop
            existing_loop: asyncio.AbstractEventLoop = (
                asyncio.get_event_loop_policy().get_event_loop()
            )
            if existing_loop is not None and not existing_loop.is_closed():
                existing_loop.close()

            # Set new event loop policy and create loop
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            loop: asyncio.ProactorEventLoop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(loop)
            logger.info("Successfully configured ProactorEventLoop")
            return loop

        except Exception as e:
            logger.warning(f"Failed to set ProactorEventLoop: {e}")
            try:
                # Fallback to SelectorEventLoop if needed
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                loop: asyncio.BaseEventLoop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                logger.info("Fallback to WindowsSelectorEventLoopPolicy successful")
                return loop
            except Exception as e:
                logger.error(f"Failed to set fallback event loop: {e}")
                raise
    else:
        # For non-Windows platforms, use the default event loop
        loop: asyncio.BaseEventLoop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.info(f"Configured default event loop for platform: {sys.platform}")
        return loop


def run() -> None:
    """
    Run the Uvicorn server.
    """
    ## Create log directory so that logging can be initialized for uvicorn
    LOGGING_PATH.mkdir(parents=True, exist_ok=True)
    args: object = Args.get_args()
    # configure event loop before starting the server
    configure_event_loop()
    config: uvicorn.Config = uvicorn.Config(
        "aria_studio.main:app",
        host=LOCALHOST,
        port=args.port,  # assuming args.port is an int
        reload=args.reload,  # assuming args.reload is a bool
        log_config=str(LOGGING_YML_PATH),
        workers=1,
        loop=(
            "none" if sys.platform == WIN32 else "auto"
        ),  # Let ProactorEventLoop handle it on Windows
    )
    server: uvicorn.Server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    """
    multiprocessing.freeze_support() is required for Windows to run the script as a standalone executable.
    It has to to the first line of if __name__ == "__main__" block.
    Any code should be after this line
    """
    multiprocessing.freeze_support()
    try:
        run()
    except (KeyboardInterrupt, RuntimeError):
        print("Shutting down...")
    except Exception as exc:

        async def async_log(exc: Exception):
            from aria_studio.app.local.local_log_manager import (
                LocalLogEntry,
                LocalLogEvent,
                LocalLogManager,
                LocalLogScreen,
                LocalLogSurface,
            )

            await LocalLogManager.log_event(
                LocalLogEntry(
                    timestamp=int(datetime.now().timestamp()),
                    surface=LocalLogSurface.BACK_END,
                    event=LocalLogEvent.CRASH,
                    screen=LocalLogScreen.CRASH,
                    message=f"Main method failed with exception {exc!r}",
                    source="".join(
                        traceback.format_exception(None, exc, exc.__traceback__)
                    ),
                )
            )

        asyncio.run(async_log(exc))

        raise exc
