"""Patch prometheus-fastapi-instrumentator routing for FastAPI 0.137+.

FastAPI 0.137 changed include_router() to create _IncludedRouter objects in
app.routes instead of expanding routes flat. These objects lack a .path
attribute, causing AttributeError in PFI's _get_route_name traversal.

This module monkey-patches PFI's routing._get_route_name to skip any route
object without .path. PFI gracefully falls back to the raw request URL path
when get_route_name returns None, so metrics still record — just without
route templating for those entries.

Import this module once near the top of main.py, after the PFI import.
"""

try:
    import prometheus_fastapi_instrumentator.routing as _pfi_routing
    from starlette.routing import Match, Mount

    def _safe_get_route_name(scope, routes, route_name=None):
        for route in routes:
            match, child_scope = route.matches(scope)
            if match == Match.FULL:
                if not hasattr(route, "path"):
                    return None
                route_name = route.path
                child_scope = {**scope, **child_scope}
                if isinstance(route, Mount) and route.routes:
                    child = _safe_get_route_name(child_scope, route.routes, route_name)
                    route_name = None if child is None else route_name + child
                return route_name
            elif match == Match.PARTIAL and route_name is None:
                if hasattr(route, "path"):
                    route_name = route.path
        return None

    _pfi_routing._get_route_name = _safe_get_route_name

except ImportError:
    pass
