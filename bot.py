import os
import json
import discord
from access_detector import *

# Bot requires root privileges, so it can execute
# - shutdown
# - reboot
if os.geteuid() != 0:
	exit('Bot needs to be run with root privileges')

# Setup discord intents
intents = discord.Intents.all()
intents.message_content = True

client = discord.Client(intents=intents)

# Load settings for the bot :)
with open('settings.json', 'r') as f:
	settings = json.load(f)
	print('settings loaded...')

@client.event
async def on_ready():
	print(f'We have logged in as {client.user}')
	await client.change_presence(
		activity=discord.Activity(
		type=discord.ActivityType.watching, name='SSH logs'))

	await watch_entries(client, settings)

@client.event
async def on_message(message):
	if message.author == client.user or message.author.id != settings['owner_id']:
		return

	if message.content.startswith('$clear'):
		async for msg in message.channel.history():
			await msg.delete()

	if message.content.startswith('$shutdown'):
		await message.channel.send('Shutting down immediately')
		os.system('shutdown now -h')

	if message.content.startswith('$cinfo'):
		await message.channel.send(f'Authorized pids: {authorized_pids}, Closed pids: {closed_pids}')

	if message.content.startswith('$ips'):
		await message.channel.send(f'Whitelisted IP-Addresses: {settings["ip_whitelist"]}')

client.run(settings['dc_token']);
