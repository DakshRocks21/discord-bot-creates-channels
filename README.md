# Discord Hackathon Team Setup Bot

A standalone Python script designed to automate the creation and management of private team channels on a Discord server for a hackathon or similar event.

The bot reads team compositions from a `teams.csv` file, creates dedicated private text channels for each team, assigns participant roles, and ensures that organizers or judges have access to all team channels. It's designed to be run once from the terminal to perform the setup and then disconnect.

## Features

- **Automated Role Creation**: Automatically creates a "Participant" role and a "Global Access" role (for organizers/judges) if they don't already exist.
- **CSV-Driven Team Management**: Reads a simple `teams.csv` file to get team names and member lists.
- **Private Channel Creation**: For each team in the CSV, it creates a private text channel accessible only to that team's members, the bot, and the global access role.
- **Permission Syncing**: If a channel for a team already exists, the script will sync its permissions to add new members or correct access rights.
- **New Member Welcome**: When a new user is added to an existing team channel, the bot sends a welcome message tagging them specifically.
- **Configuration via `.env`**: All settings (bot token, server ID, role names, etc.) are managed in a `.env` file for security and ease of use.
- **Terminal-Based Execution**: No complex commands needed. Simply run the script from your terminal to execute the setup.

## Prerequisites

Before you begin, ensure you have the following:

1.  **Python 3.12 or newer**.
2.  A **Discord Bot Account** with a token. You can create one on the [Discord Developer Portal](https://discord.com/developers/applications).
3.  The **Server Members Intent** enabled for your bot in the Discord Developer Portal under the "Bot" tab. This is crucial for finding users by their names.
4.  Your bot added to the target Discord server with sufficient permissions. For simplicity, granting the bot the **Administrator** permission is easiest. Otherwise, ensure it has:
    - `Manage Roles`
    - `Manage Channels`
    - `Read Messages / View Channels`
    - `Send Messages`
    - `Manage Permissions`

## Setup & Configuration

Follow these steps to get the bot ready to run.

### 1. Install Dependencies

Install the required Python libraries using pip:

```bash
pip install -r requirements.txt
```

### 2. Create the .env File

Create a file named .env in the same directory as the script. This file will hold your secret keys and configuration. Do not share this file publicly.

Fill it with the following variables:

```env
DISCORD_TOKEN=your_bot_token

GUILD_ID=your_guild_id
PARTICIPANT_ROLE_NAME="Participant"
GLOBAL_TEAM_ACCESS_ROLE_NAME="Admins"

CATEGORY_NAME="team-bonding"
CSV_FILE="teams.csv"
```

### Create a teams.csv file.

The first column must be the team name, and all subsequent columns on the same row should be the Discord usernames of the members (e.g., username#1234) or their current server display name.

The first row is treated as a header and will be skipped.

Example teams.csv:

```
teamname,user1,user2,user3,user4,user5
winners, john, jane, doe, smith, brown
```

### Usage

Once your `.env` and `teams.csv` files are configured and placed in the same directory as the script (`run_setup.py`), simply run it from your terminal:

```bash
python run_setup.py
```

The bot will log in, perform all the setup actions, print its progress to the terminal, and then automatically disconnect. You can run the script again to update teams—it will add new members to existing channels or create channels for new teams.

## Troubleshooting

`Error: Missing required environment variables`: Ensure your .env file is correctly named, is in the same directory, and contains all the required variables listed in the configuration section.

`Error: Could not find the server with ID: ...`: Double-check that the GUILD_ID in your .env file is correct and that your bot has been invited to that server.

`Warning: Could not find users: ...`: This means the script could not find a member on the server matching the name in the CSV. Check for typos and ensure the user is on the server. The script uses the full username (user#1234) or the server display name.

`Permission Errors`: If you see errors related to permissions (e.g., discord.Forbidden), ensure the bot's role is high enough in your server's role hierarchy and that it has the necessary permissions (Manage Roles, Manage Channels, etc.).

<p style="display:none">
<em><strong>I ❤️ Gemini</strong></em>
</p>
