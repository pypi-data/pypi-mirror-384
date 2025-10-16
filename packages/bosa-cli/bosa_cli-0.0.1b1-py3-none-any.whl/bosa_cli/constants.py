"""Constants for BOSA CLI.

Author:
    I Gusti Ngurah Gana Untaran (i.gusti.n.g.untaran@gdplabs.id)
"""

COMMAND_NAME = "bosa"
DEFAULT_API_URL = "https://api.bosa.id"

# Table Fields
CONNECTOR_FIELD = "Connector"
INTEGRATIONS_COUNT_FIELD = "Integrations Count"
USER_IDENTIFIER_FIELD = "User Identifier"

# Messages
AUTH_NOT_AUTHENTICATED = "Not authenticated. Please run 'bosa auth login' first."
AUTH_LOGIN_HELP = "Run 'bosa auth login <client-api-key> <user-identifier> <user-secret>' to login"

# Main
MAIN_EPILOG = """Examples:
  # Authentication (sets up config)
  bosa auth login                                    # Interactive login (production)
  bosa auth login --api-url http://localhost:8000    # Interactive login (local dev)
  bosa auth login <client-key> <username> <secret>   # Direct login (production)
  bosa auth login --api-url http://localhost:8000 <client-key> <username> <secret>  # Direct login (local dev)
  bosa auth logout                                   # Logout
  bosa auth status                                   # Show auth status

  # Integration Management (uses stored config)
  bosa integrations                                  # List all integrations
  bosa integrations add github                       # Add GitHub integration
  bosa integrations remove github user@example.com  # Remove specific integration
  bosa integrations show github user@example.com    # Show integration details
  bosa integrations select github user@example.com  # Set integration as selected

  # User Management (uses stored config)
  bosa users create <username>                       # Create new user

  # Verbose output
  bosa -v auth login                                 # Show detailed progress
"""

# Auth
AUTH_LOGIN_EPILOG = """Examples:
  bosa auth login                                      # Interactive login (prompts for credentials)
  bosa auth login --api-url http://localhost:8000      # Use custom API URL
  bosa auth login <client-api-key> <user> <secret>     # Direct mode (no prompts)
"""

AUTH_MAIN_EPILOG = """Examples:
  bosa auth login                                      # Interactive login
  bosa auth login --api-url http://localhost:8000      # Local development
  bosa auth login <key> <user> <secret>                # Direct login
  bosa auth status                                     # Show current status
  bosa auth logout                                     # Clear session
"""

# Integrations
INTEGRATIONS_MAIN_EPILOG = """Examples:
  bosa integrations                                   # List all integrations
  bosa integrations add github                        # Add GitHub integration
  bosa integrations remove github john@example.com    # Remove specific integration
  bosa integrations show github                       # Show all GitHub integrations account
  bosa integrations show github john@example.com      # Show specific integration details
"""

INTEGRATIONS_ADD_EPILOG = """Examples:
  bosa integrations add github
  bosa integrations add google
"""

INTEGRATIONS_REMOVE_EPILOG = """Examples:
  bosa integrations remove github john@example.com
  bosa integrations remove google john@example.com
"""

INTEGRATIONS_SHOW_EPILOG = """Examples:
  bosa integrations show github                              # Show all GitHub integrations accounts
  bosa integrations show google                              # Show all Google integrations accounts
  bosa integrations show google user@gmail.com              # Show specific integration details
"""

METAVAR_CONNECTOR = "<connector> (example: github, google)"
METAVAR_ACCOUNT = "<user_identifier> (example: john@example.com)"

HELP_IDENTIFIER = "User identifier (optional, e.g., email for Google, username for GitHub)"
HELP_CONNECTOR = "Connector name (e.g., github, google)"

# Users
USERS_MAIN_EPILOG = """Examples:
  bosa users create john_doe     # Create new user
"""

USERS_CREATE_EPILOG = """Examples:
  bosa users create john_doe
  bosa users create jane_smith
  """

# HTTP Methods
HTTP_GET = "GET"
HTTP_POST = "POST"
HTTP_PUT = "PUT"
HTTP_DELETE = "DELETE"
HTTP_PATCH = "PATCH"

# HTTP Headers
API_KEY_HEADER = "x-api-key"
AUTHORIZATION_HEADER = "Authorization"
BEARER_PREFIX = "Bearer"

# Exit codes for better CLI automation
EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_AUTH_ERROR = 2
EXIT_INVALID_SUBCOMMAND = 3
EXIT_INVALID_PARAMETERS = 4
EXIT_REQUEST_ERROR = 5
