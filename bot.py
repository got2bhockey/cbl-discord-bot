import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import has_role
import mysql.connector
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
ERROR_CHANNEL_ID = int(os.getenv('ERROR_CHANNEL_ID'))
REQUIRED_ROLE = os.getenv('REQUIRED_ROLE')


# Define intents and initialize bot
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
bot = commands.Bot(command_prefix=None, intents=intents)

# Function to log errors to a Discord channel
async def log_error(message):
    channel = bot.get_channel(ERROR_CHANNEL_ID)
    if channel:
        await channel.send(f"Error: {message}")

# Initialize MySQL Database Connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        return connection
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

def has_required_role(interaction: discord.Interaction) -> bool:
    """Check if the user has the required role."""
    return REQUIRED_ROLE in [role.name for role in interaction.user.roles]

# Event for when bot is ready
@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands synced: {len(synced)} commands")
    except Exception as e:
        await log_error(f"Failed to sync commands: {e}")

# Command: Add Organization with Initial Ban List
@bot.tree.command(name="cbl_add_org_with_ban_list", description="Add a new organization and an initial ban list")
@has_role("Lead")
@app_commands.describe(organization_name="Name of the organization", discord_link="Link to the organization's Discord", ban_list_name="Name of the initial ban list", ban_list_guid="GUID of the initial ban list")
async def cbl_add_org_with_ban_list(interaction: discord.Interaction, organization_name: str, discord_link: str, ban_list_name: str, ban_list_guid: str):
    if not has_required_role(interaction):
        await interaction.response.send_message(f"You do not have permission to use this command. (Requires {REQUIRED_ROLE} role)", ephemeral=True)
        return
    confirmation_message = await interaction.response.send_message(
        f"Please confirm adding the following:\n"
        f"**Organization Name**: {organization_name}\n"
        f"**Discord Link**: {discord_link}\n"
        f"**Ban List Name**: {ban_list_name}\n"
        f"**Ban List GUID**: {ban_list_guid}\n\n"
        "React with ✅ to confirm or ❌ to cancel."
    )
    message = await interaction.original_response()
    await message.add_reaction("✅")
    await message.add_reaction("❌")

    def check(reaction, user):
        return user == interaction.user and str(reaction.emoji) in ["✅", "❌"]

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=30.0, check=check)
        if str(reaction.emoji) == "✅":
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SET autocommit = 0")
                cursor.execute("START TRANSACTION")
                
                # Insert organization
                cursor.execute(
                    "INSERT INTO Organisations (name, discord, createdAt, updatedAt) VALUES (%s, %s, NOW(), NOW())",
                    (organization_name, discord_link)
                )
                org_id = cursor.lastrowid

                # Insert initial ban list for the organization
                cursor.execute(
                    "INSERT INTO BanLists (name, type, source, createdAt, updatedAt, Organisation) VALUES (%s, 'battlemetrics', %s, NOW(), NOW(), %s)",
                    (ban_list_name, ban_list_guid, org_id)
                )
                conn.commit()
                cursor.execute("UNLOCK TABLES")
                cursor.close()
                conn.close()
                await interaction.followup.send(f"Organization '{organization_name}' and initial ban list '{ban_list_name}' added successfully.")
            else:
                await interaction.followup.send("Database connection failed.", ephemeral=True)
                await log_error("Database connection failed.")
        else:
            await interaction.followup.send("Operation canceled.")
    except Exception as e:
        await interaction.followup.send("Confirmation timed out or failed.")
        await log_error(f"Error in cbl_add_org_with_ban_list command: {e}")

# Command: Update Organization's Discord Link
@bot.tree.command(name="cbl_update_org_discord", description="Update the Discord link for an existing organization")
@has_role("Lead")
@app_commands.describe(organization_name="Name of the organization", new_discord_link="New Discord link for the organization")
async def cbl_update_org_discord(interaction: discord.Interaction, organization_name: str, new_discord_link: str):
    if not has_required_role(interaction):
        await interaction.response.send_message(f"You do not have permission to use this command. (Requires {REQUIRED_ROLE} role)", ephemeral=True)
        return
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE Organisations SET discord = %s, updatedAt = NOW() WHERE name = %s", (new_discord_link, organization_name))
            conn.commit()
            cursor.close()
            conn.close()
            await interaction.response.send_message(f"Discord link updated for organization '{organization_name}'.")
        else:
            await interaction.response.send_message("Database connection failed.", ephemeral=True)
            await log_error("Database connection failed.")
    except mysql.connector.Error as e:
        await interaction.response.send_message("An error occurred.", ephemeral=True)
        await log_error(f"Error in cbl_update_org_discord command: {e}")

# Command: Add a New Ban List to an Existing Organization
@bot.tree.command(name="cbl_add_ban_list_to_org", description="Add a new ban list to an existing organization")
@has_role("Lead")
@app_commands.describe(organization_name="Name of the organization", ban_list_name="Name of the ban list", ban_list_guid="GUID of the ban list")
async def cbl_add_ban_list_to_org(interaction: discord.Interaction, organization_name: str, ban_list_name: str, ban_list_guid: str):
    if not has_required_role(interaction):
        await interaction.response.send_message(f"You do not have permission to use this command. (Requires {REQUIRED_ROLE} role)", ephemeral=True)
        return
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)

            # Find organization by name
            cursor.execute("SELECT id FROM Organisations WHERE name = %s", (organization_name,))
            org_result = cursor.fetchone()
            if org_result:
                org_id = org_result["id"]

                # Insert new ban list for this organization
                cursor.execute(
                    "INSERT INTO BanLists (name, type, source, createdAt, updatedAt, Organisation) VALUES (%s, 'battlemetrics', %s, NOW(), NOW(), %s)",
                    (ban_list_name, ban_list_guid, org_id)
                )
                conn.commit()
                cursor.close()
                conn.close()
                await interaction.response.send_message(f"Ban list '{ban_list_name}' added for organization '{organization_name}'.")
            else:
                await interaction.response.send_message(f"Organization '{organization_name}' not found.", ephemeral=True)
        else:
            await interaction.response.send_message("Database connection failed.", ephemeral=True)
            await log_error("Database connection failed.")
    except mysql.connector.Error as e:
        await interaction.response.send_message("An error occurred.", ephemeral=True)
        await log_error(f"Error in cbl_add_ban_list_to_org command: {e}")

# Slash Command: Help
@bot.tree.command(name="cbl_help", description="Provides information about the bot and available commands")
@has_role("Lead")
async def cbl_help(interaction: discord.Interaction):
    if not has_required_role(interaction):
        await interaction.response.send_message(f"You do not have permission to use this command. (Requires {REQUIRED_ROLE} role)", ephemeral=True)
        return
    help_message = (
        "**Bot Commands**\n"
        "/cbl_add_org_with_ban_list - Add an organization and an initial ban list.\n"
        "/cbl_update_org_discord - Update the Discord link for an organization.\n"
        "/cbl_add_ban_list_to_org - Add a new ban list to an existing organization.\n"
        "/cbl_list_organizations - List all organizations in the database.\n"
        "/cbl_list_ban_lists - List all ban lists in the database.\n"
        "/cbl_help - Display this help message."
    )
    await interaction.response.send_message(help_message)

# Slash Command: List Organizations
@bot.tree.command(name="cbl_list_organizations", description="Lists all organizations in the database")
@has_role("Lead")
async def cbl_list_organizations(interaction: discord.Interaction):
    if not has_required_role(interaction):
        await interaction.response.send_message(f"You do not have permission to use this command. (Requires {REQUIRED_ROLE} role)", ephemeral=True)
        return
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Organisations")
            results = cursor.fetchall()
            organizations = "\n".join([f"{org['id']}: {org['name']} - {org['discord']}" for org in results])
            await interaction.response.send_message(f"**Organizations:**\n{organizations}")
            cursor.close()
            conn.close()
        else:
            await interaction.response.send_message("Database connection failed.", ephemeral=True)
            await log_error("Database connection failed.")
    except mysql.connector.Error as e:
        await interaction.response.send_message("An error occurred.", ephemeral=True)
        await log_error(f"Error in cbl_list_organizations command: {e}")

# Slash Command: List Ban Lists with Organization Names
@bot.tree.command(name="cbl_list_ban_lists", description="Lists all ban lists in the database with associated organization names")
@has_role("Lead")
async def cbl_list_ban_lists(interaction: discord.Interaction):
    if not has_required_role(interaction):
        await interaction.response.send_message(f"You do not have permission to use this command. (Requires {REQUIRED_ROLE} role)", ephemeral=True)
        return
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            # Join BanLists with Organisations to include organization name
            cursor.execute("""
                SELECT BanLists.id, BanLists.name AS ban_list_name, BanLists.source, Organisations.name AS org_name
                FROM BanLists
                LEFT JOIN Organisations ON BanLists.Organisation = Organisations.id
            """)
            results = cursor.fetchall()
            ban_lists = "\n".join([f"{bl['id']}: {bl['ban_list_name']} - {bl['source']} (Organization: {bl['org_name']})" for bl in results])
            await interaction.response.send_message(f"**Ban Lists with Organizations:**\n{ban_lists}")
            cursor.close()
            conn.close()
        else:
            await interaction.response.send_message("Database connection failed.", ephemeral=True)
            await log_error("Database connection failed.")
    except mysql.connector.Error as e:
        await interaction.response.send_message("An error occurred.", ephemeral=True)
        await log_error(f"Error in cbl_list_ban_lists command: {e}")

# Run Bot
bot.run(DISCORD_TOKEN)
