#!/usr/bin/env python3
"""
Quick validation of toy_api base endpoint changes

License: BSD 3-Clause
"""
import sys
sys.path.insert(0, '/workspace/toy_api')

from toy_api.config_discovery import find_config_path
from toy_api.app import create_app

def test_validate_base_endpoint():
    """Validate the base endpoint returns expected format."""
    print("Validating Toy API Base Endpoint Changes")
    print("=" * 50)

    # Test with basic config
    try:
        config_path, _ = find_config_path("basic")
        if not config_path:
            print("❌ Could not find basic config")
            return

        app = create_app(config_path)

        with app.test_client() as client:
            response = client.get('/')
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.get_json()

                # Check required fields
                required_fields = ['name', 'description', 'routes']
                missing_fields = [field for field in required_fields if field not in data]

                if missing_fields:
                    print(f"❌ Missing fields: {missing_fields}")
                else:
                    print("✅ All required fields present")

                # Check that port is NOT included
                if 'port' in data:
                    print("❌ Port should not be included in response")
                else:
                    print("✅ Port correctly excluded")

                # Check routes format
                if 'routes' in data and isinstance(data['routes'], list):
                    print(f"✅ Routes list contains {len(data['routes'])} routes")
                    if data['routes']:
                        first_route = data['routes'][0]
                        if 'path' in first_route and 'methods' in first_route:
                            print("✅ Route format is correct")
                        else:
                            print("❌ Route format missing path/methods")

                print(f"\nSample response:")
                print(f"Name: {data.get('name')}")
                print(f"Description: {data.get('description')}")
                print(f"Routes count: {len(data.get('routes', []))}")
            else:
                print(f"❌ Unexpected status code: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_validate_base_endpoint()