import discord
import csv
import os
import sys
from dotenv import load_dotenv

load_dotenv() 

BOT_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID_STR = os.getenv('GUILD_ID')
CATEGORY_NAME = os.getenv('CATEGORY_NAME')
CSV_FILE = os.getenv('CSV_FILE')
PARTICIPANT_ROLE_NAME = os.getenv('PARTICIPANT_ROLE_NAME')
GLOBAL_TEAM_ACCESS_ROLE_NAME = os.getenv('GLOBAL_TEAM_ACCESS_ROLE_NAME')

if not all([BOT_TOKEN, GUILD_ID_STR, CATEGORY_NAME, CSV_FILE, PARTICIPANT_ROLE_NAME, GLOBAL_TEAM_ACCESS_ROLE_NAME]):
    print("Error: Missing required environment variables.")
    sys.exit(1)

try:
    GUILD_ID = int(GUILD_ID_STR)
except ValueError:
    print("Error: GUILD_ID in your .env file is not a valid integer.")
    sys.exit(1)


async def setup_teams_from_terminal(guild: discord.Guild):
    """
    This function contains the core logic for setting up teams.
    It's called automatically when the bot is ready.
    """
    print("--- Starting Hackathon Team Setup ---")
    
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if not category:
        print(f"❌ Error: Category '{CATEGORY_NAME}' not found. Please create it first.")
        return

    participant_role = await get_or_create_role(guild, PARTICIPANT_ROLE_NAME, "Creating role for HackIT participants")
    global_access_role = await get_or_create_role(guild, GLOBAL_TEAM_ACCESS_ROLE_NAME, "Creating role for global team channel access")
    if not participant_role or not global_access_role:
        return 

    print(f"\nProcessing teams from '{CSV_FILE}' in category '{CATEGORY_NAME}'...")
    processed_members = set()

    try:
        with open(CSV_FILE, mode='r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            next(reader)
            
            for row in reader:
                if not row: continue
                team_name = row[0].strip()
                team_members_names = [name.strip() for name in row[1:] if name.strip()]
                
                if not team_name or not team_members_names:
                    print(f"⚠️ Skipping invalid row: {row}")
                    continue

                channel_name = f"team-{team_name.lower().replace(' ', '-')}"
                print(f"\n--- Processing Team: {team_name} (Channel: #{channel_name}) ---")
                
                team_members, not_found_users = await find_team_members(guild, team_members_names, participant_role, processed_members)

                if not_found_users:
                    print(f"  - ⚠️ Warning: Could not find users: {', '.join(not_found_users)}. Ensure they are on the server.")

                if not team_members:
                    print(f"  - ❌ Error: No valid members found. Skipping channel setup for this team.")
                    continue

                existing_channel = discord.utils.get(category.text_channels, name=channel_name)

                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    global_access_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                for member in team_members:
                    overwrites[member] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                
                if not existing_channel:
                    print(f"  - Channel does not exist. Creating #{channel_name}...")
                    try:
                        new_channel = await guild.create_text_channel(
                            channel_name,
                            overwrites=overwrites,
                            category=category,
                            reason=f"Creating channel for team {team_name}"
                        )
                        print(f"  - ✅ Successfully created channel #{new_channel.name}.")
                        await new_channel.send(f"👋 Welcome, **Team {team_name}**! This is your private team channel.\nMembers: {', '.join([m.mention for m in team_members])}")
                    except discord.Forbidden:
                        print(f"  - ❌ Error: I don't have permission to create channels in '{CATEGORY_NAME}'.")
                        return
                    except Exception as e:
                        print(f"  - ❌ An unexpected error occurred creating channel for team '{team_name}': {e}")
                else:
                    print(f"  - Channel #{channel_name} already exists. Syncing permissions...")
                    
                    newly_added_members = []
                    for member in team_members:
                        current_overwrite = existing_channel.overwrites_for(member)
                        if not current_overwrite.read_messages:
                            newly_added_members.append(member)
                    
                    try:
                        await existing_channel.edit(overwrites=overwrites)
                        print(f"  - ✅ Successfully synced permissions for #{existing_channel.name}.")
                        
                        if newly_added_members:
                            mentions = ', '.join([m.mention for m in newly_added_members])
                            print(f"    - Detected {len(newly_added_members)} new member(s). Sending welcome message.")
                            await existing_channel.send(f"👋 Welcome {mentions}! You've been added to the team channel.")
                        else:
                            print("    - No new members detected for this team.")

                    except discord.Forbidden:
                        print(f"  - ⚠️ Warning: No permission to update permissions for #{existing_channel.name}.")
                    except Exception as e:
                        print(f"  - ❌ An error occurred updating permissions for #{existing_channel.name}: {e}")

    except FileNotFoundError:
        print(f"❌ Error: The file '{CSV_FILE}' was not found in the current directory.")
    except Exception as e:
        print(f"❌ An unexpected error occurred during file processing: {e}")

    print("\n--- Team setup and role assignment script complete! ---")


async def get_or_create_role(guild: discord.Guild, role_name: str, reason: str):
    """Finds a role by name or creates it if it doesn't exist."""
    role = discord.utils.get(guild.roles, name=role_name)
    if role:
        return role
    
    print(f"Role '{role_name}' not found. Creating it...")
    try:
        role = await guild.create_role(name=role_name, reason=reason)
        print(f"✅ Created new role: '{role_name}'.")
        return role
    except discord.Forbidden:
        print(f"❌ Error: I don't have permission to create roles. Please grant 'Manage Roles' permission.")
    except Exception as e:
        print(f"❌ An unexpected error occurred while creating role '{role_name}': {e}")
    return None

async def find_team_members(guild: discord.Guild, member_names: list, role: discord.Role, processed_ids: set):
    """Finds member objects and assigns roles."""
    members = []
    not_found = []
    for name in member_names:
        member = discord.utils.find(lambda m: str(m) == name or m.name == name or m.display_name == name, guild.members)
        if member:
            members.append(member)
            if role and member.id not in processed_ids:
                if role not in member.roles:
                    try:
                        await member.add_roles(role, reason="Assigned HackIT Participant role")
                        print(f"  - Assigned '{role.name}' role to {member.display_name} ({str(member)}).")
                    except discord.Forbidden:
                        print(f"  - ⚠️ Warning: No permission to assign roles to {member.display_name}.")
                processed_ids.add(member.id)
        else:
            not_found.append(name)
    return members, not_found


class StandaloneSetupBot(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user} ({self.user.id})')
        guild = self.get_guild(GUILD_ID)

        if not guild:
            print(f"❌ Error: Could not find the server with ID: {GUILD_ID}.")
            print("Please check the GUILD_ID in your .env file and ensure the bot is on that server.")
        else:
            print(f"Successfully connected to server: '{guild.name}'")
            await setup_teams_from_terminal(guild)

        print("Closing bot connection.")
        await self.close()

    async def on_error(self, event, *args, **kwargs):
        print(f"\n--- An unhandled error occurred in event: {event} ---")
        import traceback
        traceback.print_exc()
        print("--- End of error traceback ---")
        await self.close()


if __name__ == '__main__':
    intents = discord.Intents.default()
    intents.guilds = True
    intents.members = True 

    bot = StandaloneSetupBot(intents=intents)
    try:
        bot.run(BOT_TOKEN)
    except discord.errors.LoginFailure:
        print("❌ Error: Login failed. The DISCORD_TOKEN in your .env file is likely invalid.")
    except Exception as e:
        print(f"❌ An error occurred while trying to run the bot: {e}")