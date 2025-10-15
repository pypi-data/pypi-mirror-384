"""

Response Generator for Toy API

Generates dummy response data for various API endpoints to enable realistic testing
of API Box route restrictions and functionality.

License: BSD 3-Clause

"""

#
# IMPORTS
#
from typing import Any, Dict, Union

from toy_api import dummy_data_generator


#
# PUBLIC
#
def generate_response(response_type: Union[str, Dict, list], params: Dict[str, str], path: str) -> Union[Dict[str, Any], list]:
    """Generate dummy response data based on response type.

    Supports two types of responses:
    1. Object-based: String reference to object (e.g., 'core.user', 'test.test_user')
    2. Explicit: Direct dict/list response data from config

    Args:
        response_type: Object reference string OR explicit dict/list response.
        params: URL parameters extracted from the route.
        path: Route path for additional context.

    Returns:
        Dictionary or list containing the response data.
    """
    # Handle explicit response (dict or list) - return as-is with param substitution
    if isinstance(response_type, (dict, list)):
        return _substitute_params(response_type, params)

    # Handle object-based response (string reference)
    if isinstance(response_type, str):
        # Use hash of params for consistent generation
        row_idx = hash(str(sorted(params.items()))) % 1000 if params else 0

        # Generate response from object definition
        print("HI!!!!!!!!!!!!!!!!!!", response_type)
        try:
            return dummy_data_generator.generate_object(
                response_type,
                params=params,
                row_idx=row_idx
            )
        except ValueError as e:
            # Object not found, return error response
            return {
                "error": "Response type not found",
                "response_type": response_type,
                "message": str(e),
                "path": path,
                "params": params
            }

    # Unexpected type
    return {
        "error": "Invalid response type",
        "response_type": str(type(response_type)),
        "path": path
    }


#
# INTERNAL
#
def _substitute_params(response_data: Union[Dict, list], params: Dict[str, str]) -> Union[Dict, list]:
    """Substitute {{param}} placeholders in explicit response data.

    Args:
        response_data: Dict or list with potential {{param}} placeholders.
        params: URL parameters to substitute.

    Returns:
        Response data with substituted parameters.
    """
    import json
    import re

    # Convert to JSON string, substitute, convert back
    json_str = json.dumps(response_data)

    # Replace {{param}} with actual values
    for key, value in params.items():
        pattern = r'\{\{' + key + r'\}\}'
        json_str = re.sub(pattern, str(value), json_str)

    return json.loads(json_str)