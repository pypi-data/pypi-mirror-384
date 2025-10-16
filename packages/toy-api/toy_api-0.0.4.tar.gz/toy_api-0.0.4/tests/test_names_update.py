#!/usr/bin/env python3
"""
Test script for name and job updates

License: BSD 3-Clause
"""
import sys
sys.path.insert(0, '/workspace/toy_api')

from toy_api.response_generator import generate_user, _generate_user_profile

# Test diverse name generation
print("Testing diverse name generation:")
print("=" * 50)

for i in range(10):
    user = generate_user(i + 1)
    profile = _generate_user_profile(str(i + 1))
    print(f"User {i+1}: {user['name']}")
    print(f"Bio: {profile['bio']}")
    print(f"Email: {user['email']}")
    print("-" * 30)

print("\nDiversity test completed! You should see:")
print("- Names from different cultures (including Parsi names like Cyrus, Delna, etc.)")
print("- Silly names like Moonbeam, Pickle, etc.")
print("- Silly job titles like 'Rainbow Chaser', 'Professional Cloud Watcher', etc.")
print("- Traditional surnames like Tata, Wadia, Mistry (Parsi), etc.")