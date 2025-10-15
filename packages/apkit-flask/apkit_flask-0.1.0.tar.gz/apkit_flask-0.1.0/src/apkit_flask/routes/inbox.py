import json
import sys
from typing import Callable, Dict, TYPE_CHECKING
import logging

import apmodel
from flask import Request, Response, jsonify

from ..types import Context
from apkit.config import AppConfig
from apkit.helper.inbox import InboxVerifier

if TYPE_CHECKING:
    from .. import ApkitIntegration

logger = logging.getLogger('activitypub.server.inbox')
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

def create_inbox_route(apkit: "ApkitIntegration", config: AppConfig, routes: Dict[type[apmodel.Activity], Callable]):
    def on_inbox_internal(request: Request) -> dict | Response | tuple[Response, int]:
        verifier = InboxVerifier(config)
        body = request.get_data()
        if isinstance(body, bytes):
            activity = apmodel.load(json.loads(body.decode("utf-8")))
            if isinstance(activity, apmodel.Activity) and (isinstance(activity.object, apmodel.Object) or isinstance(activity.object, str)):
                func = routes.get(type(activity))
    
                if func:
                    verify_result = verifier.verify(body, str(request.url), request.method, dict(request.headers))
                    if verify_result:
                        logger.debug(f"Activity received: {type(activity)}")
                        response = func(ctx=Context(_apkit=apkit, request=request, activity=activity))
                        return response
                    else:
                        return jsonify({"message": "Signature Verification Failed"}), 401
                else:
                    logger.debug(f"Activity received but no handler registered for activity type {type(activity)}")
                    return jsonify({"message": "Ok"}), 200
        return jsonify({"message": "Body is not Activity"}), 400
    return on_inbox_internal
