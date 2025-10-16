"""

Flask Application for Toy API

YAML-configurable API with dummy data for testing API Box route restrictions.

License: BSD 3-Clause

"""

#
# IMPORTS
#
import re
from typing import Any, Dict, Optional

import yaml
from flask import Flask, jsonify

from toy_api.constants import DEFAULT_CONFIG_PATH
from toy_api.response_generator import generate_response


#
# PUBLIC
#
def create_app(config_path: Optional[str] = None) -> Flask:
    """Create a Flask app configured from YAML file.

    Args:
        config_path: Path to YAML configuration file.

    Returns:
        Configured Flask application.
    """
    print('CREATING APP', config_path)
    app = Flask(__name__)

    # Load configuration
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    try:
        config = _load_config(config_path)
    except FileNotFoundError:
        # Use default configuration if file not found
        config = _get_default_config()

    # Register routes from config
    _register_routes(app, config)

    return app


#
# INTERNAL
#
def _load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        config_path: Path to YAML configuration file.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        yaml.YAMLError: If config file is invalid YAML.
    """
    with open(config_path, 'r') as file:
        return yaml.safe_load(file) or {}


def _get_default_config() -> Dict[str, Any]:
    """Get default configuration with basic routes.

    Returns:
        Default configuration dictionary.
    """
    return {
        "name": "default-toy-api",
        "description": "Default toy API with basic routes",
        "port": 8000,
        "routes": [
            {"route": "/", "methods": ["GET"], "response": "core.api_info"},
            {"route": "/users", "methods": ["GET"], "response": "core.user_list"},
            {"route": "/users/{{user_id}}", "methods": ["GET"], "response": "core.user"},
            {"route": "/health", "methods": ["GET"], "response": "core.health_check"},
        ]
    }


def _register_routes(app: Flask, config: Dict[str, Any]) -> None:
    print('_register_routes', app, config)

    """Register routes from configuration.

    Args:
        app: Flask application instance.
        config: Configuration dictionary.
    """
    # Register API info endpoint
    @app.route("/")
    def api_info():
        # Create metadata response excluding port and other sensitive info
        metadata = {
            "name": config.get("name", "Toy API"),
            "description": config.get("description", "Configurable toy API server"),
            "routes": []
        }

        # Add route information (routes and methods only, not implementation details)
        for route_config in config.get("routes", []):
            route_info = {
                "route": route_config.get("route", "/"),
                "methods": route_config.get("methods", ["GET"])
            }
            metadata["routes"].append(route_info)

        return jsonify(metadata)

    # Register configured routes
    for route_config in config.get("routes", []):
        route = route_config["route"]
        methods = route_config.get("methods", ["GET"])
        response_type = route_config["response"]

        # Convert {{var}} notation to Flask <var> notation
        flask_route = _convert_route_notation(route)

        # Create handler function
        handler = _create_route_handler(response_type, route)

        # Register route with unique endpoint name
        endpoint_name = f"route_{flask_route.replace('/', '_').replace('<', '').replace('>', '')}"
        app.add_url_rule(flask_route, endpoint=endpoint_name, view_func=handler, methods=methods)


def _convert_route_notation(route: str) -> str:
    """Convert {{var}} notation to Flask's <var> notation.

    Args:
        route: Route with {{var}} placeholders.

    Returns:
        Route with <var> Flask placeholders.
    """
    # Convert {{variable}} to <variable>
    return re.sub(r'\{\{(\w+)\}\}', r'<\1>', route)


def _create_route_handler(response_type, path: str):
    """Create a handler function for a route.

    Args:
        response_type: Object reference (str) or explicit response (dict/list).
        path: Route path for context.

    Returns:
        Handler function that returns JSON response.
    """
    print('_create_route_handler!!!!!!!!!!', response_type)
    print('_create_route_handler!!!!!!!!!!', path)
    def handler(**kwargs):
        print('HANDLER!!!!!!!!!!', kwargs)
        response_data = generate_response(response_type, kwargs, path)
        return jsonify(response_data)

    return handler