import typing
from typing import Optional
import traceback
import logging
import uuid
from types import TracebackType
from fastapi.exceptions import HTTPException

from starlette._utils import is_async_callable
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException, WebSocketException
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from starlette.websockets import WebSocket

from starlette.middleware.exceptions import ExceptionMiddleware


log = logging.getLogger("background_task_exceptions")


def get_last_traceback(tb: TracebackType) -> TracebackType:
    new_tb = getattr(tb, "tb_next")
    if new_tb is None:
        return tb
    else:
        return get_last_traceback(new_tb)


class ResponseCode:
    code: int = -1
    message: str = "ResponseCodeMsg"

    def __init__(self, code: int = -1, message: str = None):
        if message:
            self.message = message


# Not set against GraphQLError for now
class HandledException(HTTPException):
    # errorCode
    code: int
    # errorMessage
    message: str

    traceId: str
    systemMessage: Optional[str] = None
    systemStackTrace: Optional[str] = None


    def __init__(
        self,
        resp_code: ResponseCode,
        e: Exception = None,
        code: int = None,
        msg: str = None):
    
        super().__init__(status_code=200, detail=resp_code.message)
        self.code = resp_code.code
        self.message = resp_code.message

        delimeter = ": "
        if msg is not None:
            self.message = delimeter.join([
                self.message,
                msg,
            ])
        self.traceId = gen_logtrace_id()

        if e is None:
            self.systemMessage = self.message
            exc_type = type(self)
            filename = ""
            name = ""
            line = ""
            self.systemStackTrace = delimeter.join([
                f"{{ErrorType: {exc_type}}}",
            ])
        else:
            tb = e.__traceback__
            last_tb = get_last_traceback(tb)
            exc_type = e.__class__.__name__
            filename = last_tb.tb_frame.f_code.co_filename
            name = last_tb.tb_frame.f_code.co_name
            line = last_tb.tb_lineno
            stack = "".join(traceback.format_tb(e.__traceback__))
            exc_msg = f"{exc_type}: {str(e)}"
            self.systemMessage = f"{self.message}: {exc_msg}"
            self.systemStackTrace = "\n".join([
                f"ErrorType: {exc_type}",
                f"File: {filename}",
                f"Name: {name}",
                f"Line: {line}",
                f"Traceback: \n{stack}{exc_msg}",
            ])


    @property
    def logMessage(self) -> str:
        return "\n".join([
            "=" * 50,
            f"TraceID: {self.traceId}",
            f"CODE: {self.code}",
            f"MSG: {self.message}",
            f"SYSMSG: {self.systemMessage}",
            "=" * 50,
            f"StackTrace: \n{self.systemStackTrace}",
        ])


def gen_logtrace_id() -> str:
    return f"log-{str(uuid.uuid4())}"


class BackgroundTaskException(HandledException): ...


class BackgroundTaskExceptionMiddleware(ExceptionMiddleware):

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        response_started = False

        async def sender(message: Message) -> None:
            nonlocal response_started

            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, sender)
        except Exception as exc:
            real_exc = exc.__cause__
            # Expected: raised from original ExceptionMiddleware
            if real_exc:
                if isinstance(real_exc, BackgroundTaskException):
                    log.error(f"{real_exc.logMessage}")
                    raise real_exc
                else:
                    wrapped_exc = BackgroundTaskException(ResponseCode(message="UnHandled Error"), e=real_exc)
                    log.error(f"{wrapped_exc.logMessage}")
                    raise real_exc
            else:
                # Unexpected: Not raised from original ExceptionMiddleware
                wrapped_exc = BackgroundTaskException(ResponseCode(message="UnHandled Error"), e=exc)
                log.error(f"{wrapped_exc.logMessage}")
                raise exc
