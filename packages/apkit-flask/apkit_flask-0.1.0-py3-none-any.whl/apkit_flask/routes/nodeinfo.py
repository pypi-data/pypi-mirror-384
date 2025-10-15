import functools

from flask import Request, Response, request, jsonify, url_for
from werkzeug.routing import BuildError

@functools.cache
def nodeinfo_links(request: Request):
    links = []

    try:
        ni20_url = url_for("__apkit_nodeinfo_2.0", _external=True)
        links.append({
            "rel": "http://nodeinfo.diaspora.software/ns/schema/2.0",
            "href": str(ni20_url)
        })
    except BuildError:
        pass

    try:
        ni21_url = url_for("__apkit_nodeinfo_2.1")
        links.append({
            "rel": "http://nodeinfo.diaspora.software/ns/schema/2.1",
            "href": str(ni21_url)
        })
    except BuildError:
        pass

    return jsonify({
        "links": links
    })

def nodeinfo_links_route() -> Response:
    return nodeinfo_links(request=request)
    