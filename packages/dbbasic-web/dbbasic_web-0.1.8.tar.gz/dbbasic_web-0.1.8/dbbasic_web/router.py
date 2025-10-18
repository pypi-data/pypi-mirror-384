"""Filesystem-based routing - like CGI but async"""
import importlib
import importlib.util
import urllib.parse
from pathlib import Path
from .settings import BASE_DIR
from .responses import html, text
from .templating import render
from .static import serve_static
from .request import Request


def parse_query_string(query_string: str) -> dict:
    """Parse URL query string into dict"""
    if not query_string:
        return {}
    return dict(urllib.parse.parse_qsl(query_string))


def parse_form_data(body: bytes, content_type: str) -> dict:
    """Parse form data from request body"""
    if not body:
        return {}

    # Handle application/x-www-form-urlencoded
    if "application/x-www-form-urlencoded" in content_type:
        return dict(urllib.parse.parse_qsl(body.decode("utf-8")))

    # Handle multipart/form-data (requires python-multipart)
    if "multipart/form-data" in content_type:
        try:
            from multipart import parse_form_data as parse_multipart
            # TODO: Implement multipart parsing
            return {}
        except ImportError:
            return {}

    return {}


def parse_cookies(headers: list) -> dict:
    """Parse cookies from request headers"""
    cookies = {}
    for name, value in headers:
        if name.lower() == b"cookie":
            cookie_str = value.decode("utf-8") if isinstance(value, bytes) else value
            for cookie in cookie_str.split(";"):
                cookie = cookie.strip()
                if "=" in cookie:
                    key, val = cookie.split("=", 1)
                    cookies[key.strip()] = val.strip()
    return cookies


def route(scope: dict, body: bytes = b"") -> tuple[int, list, list]:
    """
    Route a request based on filesystem conventions.

    Routing order:
    1. API handlers: api/{path}.py or parent api handlers
    2. Templates: templates/{path}.html
    3. Static files: public/{path}
    4. 404

    API handlers can handle sub-paths:
    - /user/123 → api/user.py gets request with path_parts=['user', '123']
    """
    method = scope["method"]
    path = scope["path"]
    query_string = scope.get("query_string", b"").decode("utf-8")
    headers = scope.get("headers", [])

    # Get content type for form parsing
    content_type = ""
    for name, value in headers:
        if name.lower() == b"content-type":
            content_type = value.decode("utf-8") if isinstance(value, bytes) else value
            break

    # Clean path
    clean_path = path.strip("/")
    path_parts = [p for p in clean_path.split("/") if p] if clean_path else []

    # Build request context
    request = Request({
        "method": method,
        "path": path,
        "path_parts": path_parts,
        "query": parse_query_string(query_string),
        "form": parse_form_data(body, content_type),
        "cookies": parse_cookies(headers),
        "headers": headers,
        "body": body,
        "scope": scope,
    })

    # 1. Try API handlers (with hierarchical fallback)
    api_result = try_api_handler(path_parts, request)
    if api_result:
        return api_result

    # 2. Try templates (GET only)
    if method == "GET":
        template_result = try_template(path_parts)
        if template_result:
            return template_result

    # 3. Try static files (GET only)
    if method == "GET":
        static_result = serve_static(clean_path)
        if static_result[0] != 404:
            return static_result

    # 4. 404
    return 404, [("content-type", "text/plain")], [b"Not Found"]


def try_api_handler(path_parts: list[str], request: dict):
    """
    Try to find an API handler, checking from most specific to least specific.

    For /user/123/edit:
    1. Try api/user/123/edit.py (exact match)
    2. Try api/user/123/[xxx].py (pattern match)
    3. Try api/user/123.py (parent handler)
    4. Try api/user/[id].py (pattern match)
    5. Try api/user.py (parent handler)
    6. Try api.py (root handler)

    Pattern matching: [id], [slug], [name] extract the value and pass as kwarg
    """
    api_dir = BASE_DIR / "api"

    if not path_parts:
        # Root path: try api.py only
        root_handler = BASE_DIR / "api.py"
        if root_handler.exists():
            return load_and_call_handler(root_handler, request)
        return None

    # Try increasingly general paths
    for i in range(len(path_parts), 0, -1):
        # Try exact match first
        partial_path = "/".join(path_parts[:i])
        handler_file = api_dir / f"{partial_path}.py"

        # Try pattern match before exact match fallback
        # For /tasks/123, when i=2, check api/tasks/[id].py before api/tasks.py
        parent_parts = path_parts[:i-1]
        current_segment = path_parts[i-1]

        if parent_parts:
            parent_dir = api_dir / "/".join(parent_parts)
        else:
            parent_dir = api_dir

        if parent_dir.exists() and parent_dir.is_dir():
            # Find pattern files like [id].py, [slug].py
            # Must escape brackets in glob: [[]*.py matches literal [
            for pattern_file in parent_dir.glob("[[]*.py"):
                # Extract parameter name from [id].py -> id
                param_name = pattern_file.stem.strip("[]")
                param_value = current_segment

                request["matched_parts"] = path_parts[:i]
                request["remaining_parts"] = path_parts[i:]
                request["path_params"] = {param_name: param_value}

                return load_and_call_handler(pattern_file, request, **{param_name: param_value})

        # Now try exact match as fallback
        if handler_file.exists():
            request["matched_parts"] = path_parts[:i]
            request["remaining_parts"] = path_parts[i:]
            return load_and_call_handler(handler_file, request)

    # Try root api handler
    root_handler = BASE_DIR / "api.py"
    if root_handler.exists():
        return load_and_call_handler(root_handler, request)

    # Try package handlers as fallback (e.g., dbbasic_admin.api.{path})
    package_result = try_package_handler(path_parts, request)
    if package_result:
        return package_result

    return None


def try_package_handler(path_parts: list[str], request: dict):
    """
    Try to find a handler in installed packages.

    For /admin/database, tries:
    1. dbbasic_admin.api.database module
    2. dbbasic_admin.api.admin.database module

    This allows packages like dbbasic-admin to provide default handlers.
    """
    if not path_parts:
        return None

    # For /admin/..., check dbbasic_admin package
    # For /other/..., check dbbasic_other package
    first_segment = path_parts[0]
    package_name = f"dbbasic_{first_segment}"

    try:
        # Try to import the package
        package = importlib.import_module(package_name)

        # Build module path: dbbasic_admin.api.database
        # Remove first segment since it's the package name
        remaining_parts = path_parts[1:] if len(path_parts) > 1 else []

        # Try direct API path first: dbbasic_admin.api.database
        if remaining_parts:
            module_path = f"{package_name}.api.{'.'.join(remaining_parts)}"
        else:
            # For /admin/ -> dbbasic_admin.api.__init__
            module_path = f"{package_name}.api"

        try:
            module = importlib.import_module(module_path)
            return load_and_call_package_handler(module, request)
        except (ImportError, AttributeError):
            pass

    except ImportError:
        pass

    return None


def load_and_call_package_handler(module, request: dict, **kwargs):
    """
    Call handler from an imported package module.

    Similar to load_and_call_handler but for already-imported modules.
    """
    try:
        # Try method-specific function first (GET, POST, PUT, DELETE, etc.)
        method = request.get("method", "GET")
        method_handler = getattr(module, method, None)

        if method_handler and callable(method_handler):
            result = method_handler(request, **kwargs)
        elif hasattr(module, "handle"):
            # Fall back to generic handle() function
            result = module.handle(request, **kwargs) if kwargs else module.handle(request)
        else:
            # No handler found
            return None

        # Support various return formats
        if isinstance(result, tuple) and len(result) == 3:
            return result
        else:
            return 500, [("content-type", "text/plain")], [b"Invalid handler return format"]

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        return 500, [("content-type", "text/plain")], [f"Package handler error: {e}\n\n{tb}".encode()]


def load_and_call_handler(handler_file: Path, request: dict, **kwargs):
    """
    Load a Python module and call the appropriate handler function.

    Supports two patterns:
    1. Method-specific functions: GET(request, **kwargs), POST(request, **kwargs), etc.
    2. Generic handle function: handle(request, **kwargs)

    Method-specific functions take precedence. Falls back to handle() if method function doesn't exist.
    """
    try:
        spec = importlib.util.spec_from_file_location("handler", handler_file)
        if not spec or not spec.loader:
            return 500, [("content-type", "text/plain")], [b"Failed to load handler"]

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Try method-specific function first (GET, POST, PUT, DELETE, etc.)
        method = request.get("method", "GET")
        method_handler = getattr(module, method, None)

        if method_handler and callable(method_handler):
            result = method_handler(request, **kwargs)
        elif hasattr(module, "handle"):
            # Fall back to generic handle() function
            result = module.handle(request, **kwargs) if kwargs else module.handle(request)
        else:
            # No handler found
            return 405, [("content-type", "text/plain")], [b"Method Not Allowed"]

        # Support various return formats
        if isinstance(result, tuple) and len(result) == 3:
            return result
        else:
            return 500, [("content-type", "text/plain")], [b"Invalid handler return format"]

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        return 500, [("content-type", "text/plain")], [f"Handler error: {e}\n\n{tb}".encode()]


def try_template(path_parts: list[str]):
    """Try to render a template"""
    if not path_parts:
        # Root: try index.html
        template_name = "index.html"
    else:
        # Try exact path
        template_name = "/".join(path_parts)
        if not template_name.endswith(".html"):
            template_name += ".html"

    template_file = BASE_DIR / "templates" / template_name

    if template_file.exists():
        try:
            rendered = render(template_name)
            return html(rendered)
        except Exception as e:
            return 500, [("content-type", "text/plain")], [f"Template error: {e}".encode()]

    return None
