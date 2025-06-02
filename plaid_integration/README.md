# Plaid Integration Project

## Overview

This project is a sample Flask web application that demonstrates a basic integration with the Plaid API. It allows users to:
1. Connect their bank accounts using Plaid Link.
2. Exchange the public token received from Plaid Link for an access token.
3. Fetch and display account transactions using the access token.

This project is intended as a starting point and educational example. For production use, consider more robust error handling, security measures (like database storage for access tokens), and user management.

## Prerequisites

Before you begin, ensure you have the following installed:
- Python (3.7 or newer recommended)
- pip (Python package installer)
- Git (for cloning the repository)

## Setup Instructions

1.  **Clone the Repository (or Download Files):**
    ```bash
    git clone <repository_url> # Replace <repository_url> with the actual URL
    cd plaid_integration
    ```
    If you downloaded the files as a ZIP, extract them and navigate into the `plaid_integration` directory.

2.  **Create and Activate a Virtual Environment:**
    It's highly recommended to use a virtual environment to manage project dependencies.
    ```bash
    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    Install the required Python packages using the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Environment Variables:**
    The application requires Plaid API keys and other configuration settings to be stored as environment variables.
    -   A file named `.env.example` is provided in the root of the `plaid_integration` directory. Make a copy of this file and name it `.env`:
        ```bash
        cp .env.example .env
        ```
    -   Open the `.env` file and fill in your Plaid API credentials:
        -   `PLAID_CLIENT_ID`: Your Plaid client ID.
        -   `PLAID_SECRET`: Your Plaid secret key for the specified environment (e.g., sandbox secret).
        -   `PLAID_ENV`: The Plaid environment to use. Set to `sandbox` for testing. Other options are `development` or `production`.
        -   `PORT` (Optional): The port on which the Flask application will run (defaults to 5000 if not set).

    **Important:**
    -   Get your Plaid API keys from the [Plaid Dashboard](https://dashboard.plaid.com/team/keys).
    -   Ensure the `.env` file is **never** committed to version control, especially if it contains real production keys. The `.gitignore` file should already be configured to ignore `.env`.

## Running the Application

Once the setup is complete, you can run the Flask application:

```bash
python app.py
```

The application will start, and you should see output similar to this:
```
 * Serving Flask app 'app'
 * Debug mode: on  # (or off, if PLAID_ENV is 'production')
INFO:werkzeug: * Running on http://127.0.0.1:5000 (Press CTRL+C to quit)
```
You can access the application by opening `http://127.0.0.1:5000` (or the configured port) in your web browser.

## How to Use the Application

1.  **Homepage (`/`):**
    -   When you first open the application, you'll see a homepage with a "Connect a bank account" button.

2.  **Connect a Bank Account:**
    -   Click the "Connect a bank account" button.
    -   This will initialize Plaid Link, Plaid's secure front-end module.
    -   Follow the prompts within Plaid Link to select your institution and enter your credentials (Plaid provides sandbox credentials for testing).
    -   Upon successful connection, Plaid Link will provide a `public_token`.

3.  **Token Exchange:**
    -   The application automatically sends this `public_token` to the `/exchange_public_token` endpoint on the server.
    -   The server exchanges this `public_token` for an `access_token`, which is necessary to make API calls for that specific Item (bank connection).
    -   **Note:** In this example, the `access_token` is stored in memory, meaning it will be lost if the server restarts. A production application must store `access_tokens` securely in a database.
    -   You should see an "Account connected successfully!" alert.

4.  **View Transactions (`/transactions`):**
    -   After a successful connection, a "View Transactions" link will appear on the homepage.
    -   Click this link to navigate to the `/transactions` page.
    -   The application will use the stored `access_token` to fetch the last 30 days of transactions for the connected account and display them in a table.
    -   If there are any errors (e.g., the access token is missing or invalid), an error message will be displayed.

## Development Notes

-   **Logging:** The application uses basic logging. Errors and important events are logged to the console.
-   **Error Handling:** Basic error handling is in place for Plaid API calls and missing configurations.
-   **Security:** This application is a demo. For production, consider:
    -   Secure storage for access tokens.
    -   More robust input validation and sanitization.
    -   CSRF protection for Flask forms (if any were added).
    -   HTTPS.
-   **Virtual Environment:** Always ensure your virtual environment is activated when working on the project or running the application.

## Contributing

Contributions are welcome! Please follow standard Git practices:
1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes.
4.  Commit your changes and push to your fork.
5.  Submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details (if a `LICENSE` file is included in the repository).
