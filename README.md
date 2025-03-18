# Auth0 User Creator

A command-line tool for creating Auth0 users with sequential email addresses and role assignments.

## Features

- Create multiple Auth0 users with sequential email addresses
- Assign roles to newly created users
- Interactive role selection from available Auth0 roles
- Export successful responses to a JSON file
- Smart output file handling: appends to existing data when possible
- Automatic extraction of Auth0 API URL from JWT token
- Debug mode to preview requests without making API calls
- Graceful error handling

## Requirements

- Python 3.6+
- `requests` library

## Setup

### Using a Virtual Environment (Recommended)

It's recommended to use a virtual environment to avoid conflicts with other Python packages:

```bash
# Create a virtual environment
python -m venv auth0_venv

# Activate the virtual environment
## On macOS/Linux:
source auth0_venv/bin/activate
## On Windows:
# auth0_venv\Scripts\activate

# Install dependencies
pip install requests

# When finished, deactivate the virtual environment
# deactivate
```

### Direct Installation

If you prefer not to use a virtual environment, you can install the dependency directly:

```bash
pip install requests
```

## Usage

```bash
python auth0_user_creator.py --token "YOUR_AUTH0_TOKEN" --email "client-test-e2e-{$}@example.com" --start 1 --end 10
```

### Required Arguments

- `--token`: Auth0 Management API token with the necessary permissions
- `--email`: Email template with `{$}` placeholder (e.g., `user-{$}@example.com`)
- `--start`: Starting number for email replacement
- `--end`: Ending number for email replacement

### Optional Arguments

- `--role-id`: Auth0 Role ID to assign to each user (if not provided, you'll be prompted to select from available roles)
- `--output`: Output JSON file for successful responses (default: `auth0_users.json`)
- `--debug`: Run in debug mode without making actual API calls

## Example

```bash
python auth0_user_creator.py --token "eyJhbGci..." --email "test-user-{$}@example.com" --start 1 --end 5
```

This will:
1. Extract the Auth0 API URL from the token's "aud" claim
2. Fetch available roles from Auth0 and display them for selection
3. Prompt you to select a role to assign to all users
4. Create 5 users with emails:
   - test-user-1@example.com
   - test-user-2@example.com
   - test-user-3@example.com
   - test-user-4@example.com
   - test-user-5@example.com
5. Assign each user the selected role

## Role Selection

If you don't provide the `--role-id` parameter, the script will:
1. Fetch all available roles from your Auth0 tenant
2. Display the roles with their names, descriptions, and IDs
3. Prompt you to select a role by entering its number
4. Use the selected role for all user creations

Example:
```
Available Roles:
----------------
1. Admin - Administrator role (ID: rol_123abc)
2. User - Regular user role (ID: rol_456def)
3. Editor - Content editor role (ID: rol_789ghi)

Select a role (enter number): 2

Selected role: User (ID: rol_456def)
```

You can still provide the `--role-id` directly if you prefer:

```bash
python auth0_user_creator.py --token "eyJhbGci..." --email "test-user-{$}@example.com" --start 1 --end 5 --role-id "rol_123abc"
```

## Output File Handling

The script intelligently handles output files:

- If the output file doesn't exist, it will create a new file
- If the output file exists and contains a valid JSON array, it will append new results to the existing data
- If the output file exists but doesn't contain valid JSON or doesn't contain a JSON array, it will overwrite the file

This means you can run the script multiple times with different parameters, and all successfully created users will be accumulated in the output file.

Example of appending to existing results:
```
$ python auth0_user_creator.py --token "..." --email "user-{$}@example.com" --start 1 --end 3
Successfully created 3 users. Total users in output file: 3

$ python auth0_user_creator.py --token "..." --email "user-{$}@example.com" --start 4 --end 6
Successfully created 3 users. Total users in output file: 6
```

## Debug Mode

Run the script with the `--debug` flag to preview API requests without making actual calls:

```bash
python auth0_user_creator.py --token "YOUR_AUTH0_TOKEN" --email "user-{$}@example.com" --start 1 --end 2 --debug
```

This will:
- Display detailed information about each request that would be made
- Show sample response data
- Not create any actual users in Auth0

Debug mode is useful for:
- Testing your configuration
- Understanding the API requests before executing them
- Validating that the token contains the correct API URL

## Error Handling

If an error occurs during user creation or role assignment, the script will:
1. Output the error message
2. Save all successful user creations to the specified output file
3. Exit with status code 1 