#!/usr/bin/env python3

import argparse
import json
import requests
import sys
import base64


def decode_jwt_payload(token):
    """Decode the payload part of a JWT token."""
    parts = token.split('.')
    if len(parts) != 3:
        print("Error: Invalid JWT token format")
        sys.exit(1)
    
    # Decode the payload (middle part)
    payload = parts[1]
    # Add padding if needed
    payload += '=' * ((4 - len(payload) % 4) % 4)
    try:
        decoded = base64.b64decode(payload).decode('utf-8')
        return json.loads(decoded)
    except Exception as e:
        print(f"Error decoding JWT payload: {str(e)}")
        sys.exit(1)


def extract_api_url_from_token(token):
    """Extract API base URL from the 'aud' claim in JWT token."""
    payload = decode_jwt_payload(token)
    
    if 'aud' not in payload:
        print("Error: JWT token missing 'aud' claim")
        sys.exit(1)
    
    aud = payload['aud']
    
    # Ensure aud contains the expected API path
    if '/api/v2/' not in aud:
        print(f"Error: aud claim does not contain '/api/v2/': {aud}")
        sys.exit(1)
    
    # Return the full aud value
    return aud


def create_user(auth0_token, email, role_id, api_url, debug=False):
    """Create a user in Auth0 and assign a role."""
    headers = {
        "Authorization": f"Bearer {auth0_token}",
        "Content-Type": "application/json"
    }
    
    # Create user
    user_url = f"{api_url}users"
    user_data = {
        "email": email,
        "connection": "Username-Password-Authentication",
        "password": "Temp1234!",  # Temporary password
        "email_verified": True
    }
    
    if debug:
        print("\n=== DEBUG: User Creation Request ===")
        print(f"URL: {user_url}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Payload: {json.dumps(user_data, indent=2)}")
        # Mock a successful response for debug mode
        mock_user_id = f"auth0|debug-{email.replace('@', '-at-')}"
        mock_response = {
            "user_id": mock_user_id,
            "email": email,
            "email_verified": True,
            "created_at": "2023-01-01T00:00:00.000Z",
            "updated_at": "2023-01-01T00:00:00.000Z",
            "identities": [
                {
                    "connection": "Username-Password-Authentication",
                    "user_id": mock_user_id.split("|")[1],
                    "provider": "auth0",
                    "isSocial": False
                }
            ]
        }
        print(f"Mock Response: {json.dumps(mock_response, indent=2)}")
        user_id = mock_user_id
    else:
        user_response = requests.post(user_url, headers=headers, json=user_data)
        
        if user_response.status_code != 201:
            return {
                "success": False,
                "error": f"Failed to create user: {user_response.text}",
                "status_code": user_response.status_code
            }
        
        user_id = user_response.json()["user_id"]
    
    # Assign role to user
    role_url = f"{api_url}users/{user_id}/roles"
    role_data = {"roles": [role_id]}
    
    if debug:
        print("\n=== DEBUG: Role Assignment Request ===")
        print(f"URL: {role_url}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Payload: {json.dumps(role_data, indent=2)}")
        print("Mock Response: No content (204)")
        return {
            "success": True,
            "user": mock_response if debug else user_response.json(),
            "role_assigned": True,
            "debug_mode": True
        }
    else:
        role_response = requests.post(role_url, headers=headers, json=role_data)
        
        if role_response.status_code != 204:
            return {
                "success": False,
                "error": f"Failed to assign role: {role_response.text}",
                "user_created": user_response.json(),
                "status_code": role_response.status_code
            }
    
        return {
            "success": True,
            "user": user_response.json(),
            "role_assigned": True
        }


def main():
    parser = argparse.ArgumentParser(description="Create Auth0 users with incremental emails")
    parser.add_argument("--token", required=True, help="Auth0 Management API token")
    parser.add_argument("--email", required=True, help="Email template with {$} placeholder")
    parser.add_argument("--start", type=int, required=True, help="Starting number for email replacement")
    parser.add_argument("--end", type=int, required=True, help="Ending number for email replacement")
    parser.add_argument("--role-id", required=True, help="Role ID to assign to users")
    parser.add_argument("--output", default="auth0_users.json", help="Output file for successful responses")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode without making actual API calls")
    
    args = parser.parse_args()
    
    if args.debug:
        print("=== RUNNING IN DEBUG MODE - NO ACTUAL API CALLS WILL BE MADE ===")
    
    # Extract API URL from token
    api_url = extract_api_url_from_token(args.token)
    print(f"API URL extracted from token: {api_url}")
    
    if "{$}" not in args.email:
        print("Error: Email template must contain {$} placeholder")
        sys.exit(1)
    
    if args.start > args.end:
        print("Error: Start number must be less than or equal to end number")
        sys.exit(1)
    
    results = []
    
    try:
        for num in range(args.start, args.end + 1):
            email = args.email.replace("{$}", str(num))
            print(f"Creating user with email: {email}")
            
            response = create_user(args.token, email, args.role_id, api_url, args.debug)
            
            if response["success"]:
                user_id = response["user"]["user_id"]
                print(f"  ✓ User created successfully with ID: {user_id}")
                results.append(response)
            else:
                print(f"  ✗ Error: {response['error']}")
                # Save successful results before exiting
                if results:
                    with open(args.output, "w") as f:
                        json.dump(results, f, indent=2)
                    print(f"Saved {len(results)} successful results to {args.output}")
                sys.exit(1)
        
        # Save all successful results
        if results:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            print(f"Successfully created {len(results)} users. Results saved to {args.output}")
            if args.debug:
                print("\nNOTE: Since this was run in debug mode, no actual users were created.")
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        # Save successful results before exiting
        if results:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            print(f"Saved {len(results)} successful results to {args.output}")
        sys.exit(1)


if __name__ == "__main__":
    main() 