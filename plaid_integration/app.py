import os
import logging # Import the logging module
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
import datetime

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

# --- Plaid Client Configuration ---
PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID')
PLAID_SECRET = os.getenv('PLAID_SECRET')
PLAID_ENV = os.getenv('PLAID_ENV', 'sandbox') # Default to sandbox if not set

# Validate essential Plaid configuration
if not PLAID_CLIENT_ID or not PLAID_SECRET:
    raise ValueError("PLAID_CLIENT_ID and PLAID_SECRET must be set in the environment or .env file.")

# Define Plaid products and country codes (customize as needed)
PLAID_PRODUCTS = [Products('auth'), Products('transactions')]
PLAID_COUNTRY_CODES = [CountryCode('US')]

# Determine Plaid environment
if PLAID_ENV == 'sandbox':
    host = plaid.Environment.Sandbox
elif PLAID_ENV == 'development':
    host = plaid.Environment.Development
elif PLAID_ENV == 'production':
    host = plaid.Environment.Production
else:
    raise ValueError(f"Invalid PLAID_ENV: {PLAID_ENV}. Must be 'sandbox', 'development', or 'production'.")

# Configure Plaid API client
configuration = plaid.Configuration(
    host=host,
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_SECRET,
    }
)
api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

# In-memory store for access tokens (IMPORTANT: Not suitable for production!)
# In a real application, use a secure database to store access tokens.
access_tokens = {} # Stores {item_id: access_token}

# --- Flask Routes ---

@app.route('/create_link_token', methods=['POST'])
def create_link_token():
    """
    Creates a Plaid Link token.
    The Link token is used by the Plaid Link front-end component to initialize the Link flow.
    """
    try:
        # Unique ID for each user, this should be persistent for the same user
        # For this example, we generate a random one each time.
        # In a real application, use a stable user ID from your system.
        user_client_id = str(os.urandom(24).hex())

        link_request = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id=user_client_id),
            client_name="My Plaid App", # Your application name
            products=PLAID_PRODUCTS,
            country_codes=PLAID_COUNTRY_CODES,
            language='en',
            # redirect_uri='https://yourapp.com/oauth-callback' # Optional: For OAuth Link flows
        )
        response = client.link_token_create(link_request)
        app.logger.info("Link token created successfully.")
        return jsonify(response.to_dict())
    except plaid.ApiException as e:
        # Log the detailed error and return a generic message to the client
        app.logger.error(f"Plaid API error during link token creation: {e.body}", exc_info=True)
        error_response = e.body if hasattr(e, 'body') else str(e)
        return jsonify({'error': 'Could not initialize Plaid Link. Please try again later.', 'details': error_response}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error during link token creation: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected server error occurred.'}), 500

@app.route('/exchange_public_token', methods=['POST'])
def exchange_public_token():
    """
    Exchanges a public token received from Plaid Link for an access token.
    The access token is then stored securely and used to access Plaid API endpoints for that Item.
    """
    data = request.get_json()
    public_token = data.get('public_token')

    if not public_token:
        app.logger.warning("Public token missing in /exchange_public_token request.")
        return jsonify({'error': 'Public token is required.'}), 400

    try:
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(exchange_request)

        access_token = exchange_response['access_token']
        item_id = exchange_response['item_id']

        # IMPORTANT: Store access_token and item_id securely (e.g., in an encrypted database)
        # For this example, we use an in-memory dictionary (NOT FOR PRODUCTION)
        access_tokens[item_id] = access_token

        app.logger.info(f"Public token exchanged successfully for item_id: {item_id}")
        # Do NOT log the access_token itself unless in a very controlled debug environment.
        # print(f"Access Token: {access_token}") # Avoid logging access tokens
        # print(f"Item ID: {item_id}")

        return jsonify({'message': 'Public token exchanged successfully. Account connected.'})
    except plaid.ApiException as e:
        app.logger.error(f"Plaid API error during public token exchange: {e.body}", exc_info=True)
        error_response = e.body if hasattr(e, 'body') else str(e)
        return jsonify({'error': 'Could not connect your account. Please try again.', 'details': error_response}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error during public token exchange: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected server error occurred.'}), 500

@app.route('/transactions')
def get_transactions():
    """
    Fetches transactions for a connected Item.
    Requires a valid access_token for the Item.
    """
    # Simplified: uses the first available access_token.
    # In a real app, you'd identify the user and use their specific access_token.
    if not access_tokens:
        app.logger.warning("Attempted to access /transactions without any stored access tokens.")
        # Redirect to home or show a more specific message in the template
        return render_template('transactions.html', transactions=None, error_message="No bank account connected. Please connect an account via Plaid Link first.")

    # For this example, just grab the first (and likely only) access token.
    # In a multi-user system, you would need to fetch the access token associated with the logged-in user.
    item_id = list(access_tokens.keys())[0]
    current_access_token = access_tokens[item_id]

    try:
        # Set date range for transactions (e.g., last 30 days)
        start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).date()
        end_date = datetime.datetime.now().date()

        options = TransactionsGetRequestOptions(count=100) # Fetch up to 100 transactions
        transactions_request = TransactionsGetRequest(
            access_token=current_access_token,
            start_date=start_date,
            end_date=end_date,
            options=options
        )

        response = client.transactions_get(transactions_request)
        transactions_data = response.get('transactions', [])

        app.logger.info(f"Successfully fetched {len(transactions_data)} transactions for item_id: {item_id}")
        return render_template('transactions.html', transactions=transactions_data, error_message=None)

    except plaid.ApiException as e:
        app.logger.error(f"Plaid API error while fetching transactions for item_id {item_id}: {e.body}", exc_info=True)
        error_message = "Could not fetch transactions. The connection with your bank may have issues or your session may have expired. Please try re-connecting."
        # You might want to check e.body for specific Plaid error codes like ITEM_LOGIN_REQUIRED
        # and guide the user to re-link if necessary.
        plaid_error_details = e.body if hasattr(e, 'body') else str(e)
        return render_template('transactions.html', transactions=None, error_message=error_message, plaid_error_details=plaid_error_details)
    except Exception as e:
        app.logger.error(f"Unexpected error while fetching transactions for item_id {item_id}: {e}", exc_info=True)
        return render_template('transactions.html', transactions=None, error_message="An unexpected server error occurred while fetching transactions.")

@app.route('/')
def index():
    """
    Renders the main page with the Plaid Link button.
    """
    return render_template('index.html')

if __name__ == '__main__':
    # Basic logging setup
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # For development, Flask's reloader can cause issues with some Plaid client initializations if not careful.
    # use_reloader=False can be helpful if you encounter strange Plaid client errors during development.
    app.run(port=os.getenv("PORT", 5000), debug=(PLAID_ENV != 'production'))
