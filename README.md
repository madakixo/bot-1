# bot-1

Telegram bot designed to connect users across Nigeria based on their location.

The bot collects and securely stores user contact information using encryption and a SQLite database. 

It uses the Nominatim API to determine the Nigerian state from a user's shared location.

Table of ContentsFeatures (#features)

Prerequisites (#prerequisites)
Local Setup & Configuration (#local-setup--configuration)
Clone the Repository (#clone-the-repository)
Install Dependencies (#install-dependencies)
Telegram Bot Setup (#telegram-bot-setup)
Environment Variables (#environment-variables)

Running the Bot Locally (#running-the-bot-locally)
Deployment (Heroku Example) (#deployment-heroku-example)Create a Procfile (#create-a-procfile)

Usage (#usage)
Notes (#notes)

FeaturesUser Interaction: Users can start a conversation with /start, choose to connect, 
and share their location to find connections in their Nigerian state.


Location Detection: Uses the Nominatim API to identify the Nigerian state from shared coordinates.

Secure Data Storage: Stores user contact information (name and phone number) encrypted in a SQLite database.

Admin Command: Admins can use /user_count to view the total number of registered users.

Conversation Flow: Guides users through selecting an action, sharing a location, and providing contact info, with a cancel option (/cancel).

Privacy: Encrypts sensitive user data using the cryptography library.

PrerequisitesPython: Version 3.8 or higher.

Git: For version control and cloning the repository.

Telegram Account: To create and manage the bot.

Deployment Platform (optional): A server or platform-as-a-service like Heroku, DigitalOcean, or Vultr for production.

Local Setup & ConfigurationClone the RepositoryClone the project repository to your local machine:bash

git clone <your-repo-url>

cd <your-repo-directory>

Note: Replace <your-repo-url> and <your-repo-directory> with your actual repository URL and directory name.

Install DependenciesCreate a requirements.txt file in the project root with the following:txt

python-telegram-bot[ext]
requests
cryptography
python-dotenv

Install the dependencies:bash

pip install -r requirements.txt

Tip: Use a virtual environment to isolate dependencies:bash

python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

Telegram Bot SetupOpen Telegram and chat with @BotFather
.
Send /newbot, choose a name (e.g., "Nigeria Connect") and a username (e.g., @NigeriaConnectBot).
Save the HTTP API Token provided by BotFather. This is your TELEGRAM_TOKEN.
Set a bot description using /setdescription to inform users about the bot’s purpose and data policy.

Environment VariablesCreate a .env file in the project root to store sensitive information:env

TELEGRAM_TOKEN="your_telegram_bot_token"
ENCRYPTION_KEY="your_encryption_key"
ADMIN_USER_ID="your_telegram_user_id"
BOT_WEBHOOK_URL="https://your-app-name.herokuapp.com"

Instructions for each variable:TELEGRAM_TOKEN: Obtained from @BotFather
.
ENCRYPTION_KEY: Generate a key using:python

from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())

ADMIN_USER_ID: Get your Telegram user ID by chatting with @userinfobot
.
BOT_WEBHOOK_URL: Set to your deployment URL (e.g., Heroku app URL) or a placeholder for local testing.

Add .env to your .gitignore file to prevent committing sensitive data:txt

.env
user_data.db

Running the Bot LocallyEnsure all dependencies are installed and the .env file is configured.
Run the bot:bash

python main_bot.py

The bot will start in polling mode, listening for Telegram messages.
Test the bot by sending /start to your bot on Telegram and following the conversation flow.

Deployment (Heroku Example)For production, webhooks are recommended for resource efficiency compared to polling.
Create a ProcfileCreate a Procfile in the project root to instruct Heroku how to run the bot:txt

web: python main_bot.py

Deploy to Heroku:Install the Heroku CLI.
Log in: heroku login.
Create a Heroku app: heroku create your-app-name.
Push code to Heroku: git push heroku main.
Set environment variables:bash

heroku config:set TELEGRAM_TOKEN="your_telegram_bot_token"
heroku config:set ENCRYPTION_KEY="your_encryption_key"
heroku config:set ADMIN_USER_ID="your_telegram_user_id"
heroku config:set BOT_WEBHOOK_URL="https://your-app-name.herokuapp.com"

Switch to webhook mode:In main_bot.py, uncomment the application.run_webhook(...) line and comment out application.run_polling().
Update the webhook URL:bash

heroku config:set BOT_WEBHOOK_URL="https://your-app-name.herokuapp.com"

UsageStart the Bot: Send /start to initiate the conversation.


Connect: Choose "Yes, find a connection" to proceed.

Share Location: Send your current or live location via Telegram’s paperclip icon.

Provide Contact Info: Enter your name and phone number when prompted.

Receive Connection: The bot provides sample connection details (e.g., name and phone number).

Admin Command: Admins can use /user_count to view the total number of users in the database.

Cancel: Send /cancel at any time to end the conversation.

NotesSecurity: User contact information is encrypted and stored in a SQLite database (user_data.db). 

Ensure this file is added to .gitignore to avoid committing sensitive data.

Database: The bot creates a user_data.db file in the project root to store user data. 

Ensure write permissions in the directory.

Testing: Test locally with polling before deploying. For production, switch to webhooks for better performance.

Limitations: The bot currently provides static connection details (e.g., "Jane Doe"). 

Extend the code to integrate dynamic data sources if needed.

Dependencies: Ensure all required packages are installed. 

If you encounter ModuleNotFoundError, verify the Python environment and run pip install -r requirements.txt.

For further assistance, refer to the Telegram Bot API documentation or contact the repository maintainer.

