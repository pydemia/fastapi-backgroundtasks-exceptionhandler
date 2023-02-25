from typing import Union

from typing import Dict
import time
import json
import logging

from fastapi import FastAPI, BackgroundTasks, HTTPException, status, Request, Response
from fastapi.responses import JSONResponse


app = FastAPI()

log = logging.getLogger("fastapi_app")
log.setLevel("DEBUG")


# Settings: Default

@app.get("/")
async def read_root():
    log.debug(f"request to: 'read_root'")
    return {"Hello": "World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: Union[str, None] = None):
    resp = {"item_id": item_id, "q": q}
    log.debug(f"request to: 'read_item'")
    log.debug(f"response is:\n{resp}")
    return resp


@app.exception_handler(ValueError)
async def http_exception_handler(request, exc):
    return JSONResponse(
        {"request": str(dict(request)), "raw_exception": str(exc)},
        status_code=status.HTTP_510_NOT_EXTENDED
    )

@app.exception_handler(Exception)
async def unknown_exception_handler(request, exc):
    return JSONResponse(
        {"request": str(dict(request)), "raw_exception": str(exc)},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

# Settings for BackgroundTaskException

from .middlewares import BackgroundTaskExceptionMiddleware, BackgroundTaskException, ResponseCode

@app.exception_handler(BackgroundTaskException)
async def background_task_exception_handler(request, exc):
    log.error(f"{exc.__class__.__name__}: \n{exc}")


app.add_middleware(
    BackgroundTaskExceptionMiddleware,
    handlers=app.exception_handlers,
)

# BackgroundTask without Exceptions: BackgroundTaskException
def send_delayed_results(resp: Dict):
    for i in range(3):
        time.sleep(1)
        log.debug(f"background task is running: {i + 1}/3")
    try:
        q = resp["q"]
        if q:
            log.debug(f"'q' is {int(q) - 1}")
        else:
            log.debug("'q' is None.")
    except BackgroundTaskException as bg_e:
        raise bg_e
    except Exception as e:
        log.debug(f"Unexpected Error: {e}")

@app.get("/tasks")
async def read_task(
    background_tasks: BackgroundTasks,
    q: Union[str, None] = None,
):
    resp = {"q": q}
    log.debug(f"request to: 'read_task'")
    log.debug(f"response is:\n{resp}")
    background_tasks.add_task(send_delayed_results, resp=resp)
    return resp


# BackgroundTask with Exceptions: BackgroundTaskException
def send_delayed_results_with_exceptions(resp: Dict):
    for i in range(3):
        time.sleep(1)
        log.debug(f"background task is running: {i + 1}/3")
    try:
        q = resp["q"]
        if q:
            log.debug(f"'q' is {int(q) - 1}")
        else:
            log.debug("'q' is None.")
            raise BackgroundTaskException(
                resp_code=ResponseCode(message="'q' cannot be 'None'.")
            )
    except BackgroundTaskException as bg_e:
        raise bg_e
    except Exception as e:
        log.debug(f"Unexpected Error: {e}")
        raise BackgroundTaskException(
            resp_code=ResponseCode(message="Unhandled Error"),
            e=e,
        )


@app.get("/tasks/bg")
async def read_task(
    background_tasks: BackgroundTasks,
    q: Union[str, None] = None,
):
    resp = {"q": q}
    log.debug(f"request to: 'read_task'")
    log.debug(f"response is:\n{resp}")
    background_tasks.add_task(send_delayed_results_with_exceptions, resp=resp)
    return resp
