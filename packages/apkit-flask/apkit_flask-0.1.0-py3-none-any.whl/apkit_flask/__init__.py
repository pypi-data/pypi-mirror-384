from typing import (
    Any,
    Callable,
    Optional,
    List,
    Awaitable,
    Literal
)

from apkit.abc.server import AbstractApkitIntegration
from apkit.config import AppConfig
from apkit.client import WebfingerResource
from apkit.types import ActorKey, Outbox
from apkit.models import Activity
from flask import Flask, Response, Request, request

from .routes.nodeinfo import nodeinfo_links_route
from .routes.inbox import create_inbox_route
from .routes.outbox import create_outbox_route
from .types import Context

class ApkitIntegration(AbstractApkitIntegration):
    def __init__(self, app: Flask, config: AppConfig = AppConfig()) -> None:
        self.__app = app
        self.__config = config
        
        self.__events = {}
        self.__outbox: Optional[Callable[[Context], Any]] = None
        self.__webfinger: Optional[Callable[[Request,WebfingerResource], Response]] = None
        
        if isinstance(config.actor_keys, Awaitable):
            raise TypeError(
                f"Configuration Error: apkit_flask required synchronous function, not {type(config.actor_keys)}"
            )
        
        self._get_actor_keys: Optional[Callable[[str], List["ActorKey"]]] = config.actor_keys # type: ignore[assignment]

    def __inbox_route(self):
        r = create_inbox_route(
            apkit=self, config=self.__config, routes=self.__events
        )
        return r(request=request)

    def __outbox_route(self):
        if self.__outbox:
            r = create_outbox_route(self, self.__outbox)
            if r:
                return r(request=request)
        return Response("Not Found", status=404)
    
    def __webfinger_route(self) -> Response:
        func = self.__webfinger
        if func:
            resource = request.args.to_dict().get("resource")
            if resource:
                acct = WebfingerResource.parse(resource)
                return func(request,acct)
        return Response("Not Found", status=404)
                
    def outbox(self, *args) -> None:
        for path in args:
            self.__app.add_url_rule(
                path,
                endpoint=f"__apkit_outbox_{path}",
                view_func=self.__outbox_route,
                methods=["GET"]
            )
            
    def inbox(self, *args) -> None:
        for path in args:
            self.__app.add_url_rule(
                path,
                endpoint=f"__apkit_inbox_{path}",
                view_func=self.__inbox_route,
                methods=["POST"]
            )
            
    def on(self, type: type[Activity] | type[Outbox], func: Optional[Callable] = None):
        def decorator(func: Callable) -> Callable:
            if  issubclass(type, Activity):
                self.__events[type] = func
            elif issubclass(type, Outbox):
                self.__outbox = func
            return func
        
        if func is not None:
            return decorator(func)

        return decorator

    def webfinger(self, func: Optional[Callable] = None):
        def decorator(func: Callable) -> Callable:
            self.__webfinger = func
            return func
        
        if func is not None:
            return decorator(func)

        return decorator

    def nodeinfo(
        self,
        route: str,
        version: Literal["2.0", "2.1"],
        func: Optional[Callable] = None,
    ) -> Callable:
        """Define Nodeinfo route.

        Args:
            route (str): route path.
            version (Literal[&quot;2.0&quot;, &quot;2.1&quot;]): nodeinfo version
            func (Optional[FunctionType], optional): If use that as decorator, ignore this. Defaults to None.

        Returns:
            Union[None, Callable]: no description
        """

        def decorator(fn: Callable) -> Callable:
            if version == "2.0":
                self.__app.add_url_rule(
                    route,
                    endpoint="__apkit_nodeinfo_2.0",
                    view_func=fn,
                    methods=["GET"]
                )
            elif version == "2.1":
                self.__app.add_url_rule(
                    route,
                    endpoint="__apkit_nodeinfo_2.1",
                    view_func=fn,
                    methods=["GET"]
                )
            return fn

        if func is not None:
            return decorator(func)

        return decorator
        
    def initialize(self):
        self.__app.add_url_rule(
            rule="/.well-known/webfinger",
            view_func=self.__webfinger_route,
            endpoint="__ap_webfinger",
            methods=["GET"]
        )
        self.__app.add_url_rule(
            rule="/.well-known/nodeinfo",
            view_func=nodeinfo_links_route,
            endpoint="__apkit_wellknown_nodeinfo", 
            methods=["GET"]
        )