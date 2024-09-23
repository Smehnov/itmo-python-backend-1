from collections import defaultdict
from inspect import signature
from typing import Callable, Tuple, Annotated, get_origin
from urllib.parse import parse_qs
import json
import re

class Query:
    def __init__(self) -> None:
        pass
    

class JSONResponse:
    def __init__(self, data: dict = {}, status: int = 200) -> None:
        self.data = data
        self.status = status

    def body_bytes(self):
        return json.dumps(self.data).encode('utf-8')


class HTTPException(Exception):
    def __init__(self, status_code: int, detail=""):            
        super().__init__(detail)

        self.status = status_code
        self.detail = detail

    def to_json_response(self)->JSONResponse:
        return JSONResponse(
            {"error": self.detail},
            status = self.status
        )



class SimpleJsonApi:
    def __init__(self) -> None:
        self.handlers = defaultdict(dict)


    def get_handler(self, method: str, path: str) -> Tuple[Callable, dict]:
        for pattern, handler in self.handlers.get(method, {}).items():
            match = re.fullmatch(pattern, path)
            if match:
                print(match.groupdict())
                return handler, match.groupdict()
        raise HTTPException(404, "not found")


    def get(self, path: str):
        pattern = re.sub(r'\{(\w+)\}', r'(?P<\1>[^/]+)', path)

        def inner(func):
            self.handlers['GET'][pattern] = func

            return func
        return inner

    async def send_response(self, resp, send):
        await send({
            'type': 'http.response.start',
            'status': resp.status,
            'headers': [
                [b'content-type', b'application/json'],
            ],
        })
        await send({
            'type': 'http.response.body',
            'body': resp.body_bytes(),
        })
    
    async def process_request(self, scope, receive):
        assert scope['type'] == 'http'
        message = await receive()
        body_bytes = message['body']
        print(message)
        data = json.loads(body_bytes.decode('utf-8')) if body_bytes else None
        
        method = scope['method']
        path = scope['path']
        handler, path_match = self.get_handler(method, path)
        query_params = parse_qs(scope['query_string'].decode('utf-8'))

        if handler:
            try:
                handler_args = dict()
                handler_params = signature(handler).parameters
                for param_name, param_desc in handler_params.items():
                    annotation = param_desc.annotation
                    if get_origin(annotation) is Annotated:
                        if type(annotation.__metadata__[0]) is Query:
                            handler_args[param_name] = annotation.__origin__(query_params[param_name][-1])

                    if param_name in path_match:
                        handler_args[param_name] = annotation(path_match[param_name])
            except Exception as _e:
                 raise HTTPException(422, "Can't process")

            
            if 'data' in handler_params:
                if data is None:
                    raise HTTPException(422, "Can't process")
                handler_args['data'] = data
             
            handler_coroutine = handler(**handler_args)
            resp = await handler_coroutine
        else:
            resp = JSONResponse({"error": "no such endpoint"}, 404)
        return resp

    async def __call__(self, scope, receive, send):
        try:
            resp = await self.process_request(scope, receive)
        except HTTPException as e:
            resp = e.to_json_response()

        await self.send_response(resp, send)

