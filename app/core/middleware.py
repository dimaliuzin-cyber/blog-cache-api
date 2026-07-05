from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.request_context import reset_request_id, set_request_id


REQUEST_ID_HEADER = b"x-request-id"


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        request_id = self._get_request_id(scope)
        token = set_request_id(request_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((REQUEST_ID_HEADER, request_id.encode("utf-8")))
                message["headers"] = headers

            await send(message)

        try:
            await self._app(scope, receive, send_with_request_id)
        finally:
            reset_request_id(token)

    def _get_request_id(self, scope: Scope) -> str:
        headers = dict(scope.get("headers", []))
        raw_request_id = headers.get(REQUEST_ID_HEADER)

        if raw_request_id is None:
            return str(uuid4())

        try:
            request_id = raw_request_id.decode("utf-8").strip()
        except UnicodeDecodeError:
            return str(uuid4())

        return request_id or str(uuid4())
