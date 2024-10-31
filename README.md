# CBL Discord Bot

This Discord bot is used by the CommunityBanList to perform administrative tasks via Discord. It provides a range of administrative commands for managing organizations and ban lists in a MySQL database. Only users with the "Lead" role are permitted to execute commands.

## Features

- **Add Organization with Ban List**: Allows adding a new organization along with an initial ban list.
- **Update Organization's Discord Link**: Updates the Discord link for an existing organization.
- **Add New Ban List to Organization**: Adds a new ban list to an existing organization.
- **List Organizations**: Lists all organizations in the database.
- **List Ban Lists with Organization Names**: Lists all ban lists along with their associated organization names.
- **Help Command**: Displays information about available commands.

## Prerequisites

- **Python** 3.8 or later
- **Discord Bot Token**: Create a bot at the [Discord Developer Portal](https://discord.com/developers/applications).
- **MySQL Database**: Set up a MySQL database to store organizations and ban lists.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/got2bhockey/cbl-discord-bot/
   cd cbl-discord-bot
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root and add the following variables:

   ```env
   DISCORD_TOKEN=your_discord_bot_token
   MYSQL_HOST=your_mysql_host
   MYSQL_USER=your_mysql_user
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_DATABASE=your_mysql_database
   ERROR_CHANNEL_ID=your_error_logging_channel_id
   ```


## Usage

Run the bot:
```bash
python bot.py
```

## Commands

All commands require the user to have the "Lead" role.

1. **`/cbl_add_org_with_ban_list`**
   - Adds a new organization along with an initial ban list.
   - Parameters: `organization_name`, `discord_link`, `ban_list_name`, `ban_list_guid`

2. **`/cbl_update_org_discord`**
   - Updates the Discord link for an existing organization.
   - Parameters: `organization_name`, `new_discord_link`

3. **`/cbl_add_ban_list_to_org`**
   - Adds a new ban list to an existing organization.
   - Parameters: `organization_name`, `ban_list_name`, `ban_list_guid`

4. **`/cbl_list_organizations`**
   - Lists all organizations in the database.

5. **`/cbl_list_ban_lists`**
   - Lists all ban lists along with their associated organization names.

6. **`/cbl_help`**
   - Displays a help message listing all available commands.

## Error Logging

The bot logs errors to the channel specified by `ERROR_CHANNEL_ID` in the `.env` file.

## Permissions

Only users with the role "Lead" can execute these commands.

## License

This project is licensed under the MIT License.
