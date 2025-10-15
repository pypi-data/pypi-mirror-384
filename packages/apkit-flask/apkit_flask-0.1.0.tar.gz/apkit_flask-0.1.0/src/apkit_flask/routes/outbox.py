from typing import Any, Callable, Union, TYPE_CHECKING
import logging

import apmodel
from flask import Request, Response

from ..types import Context

if TYPE_CHECKING:
    from .. import ApkitIntegration

logger = logging.getLogger("activitypub.server.outbox")


def create_outbox_route(
    apkit: "ApkitIntegration", f: Callable[[Context], Any]
):
    def on_outbox_internal(request: Request) -> Union[dict, Response]:
        response = f(
            Context(_apkit=apkit, request=request, activity=apmodel.Activity())
        )
        return response

    return on_outbox_internal
