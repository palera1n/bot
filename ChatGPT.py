import os
import discord
from dotenv import load_dotenv
from revChatGPT.V1 import Chatbot

# Load environment variables from .env file
load_dotenv()


# Create chatbot instance with email and password
chatbot = Chatbot(config={"email": os.getenv("OPENAI_EMAIL"), "password": os.getenv("OPENAI_PASSWORD")})

# Create a Discord client
intents = discord.Intents.default()
intents.members = True  # Required to access member information
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return

    # Ignore messages starting with "--"
    if message.content.startswith("--"):
        return

    # Check if the message was sent in a DM
    if isinstance(message.channel, discord.DMChannel) or message.channel.id == 1049028101939658893:

        # Get user input
        user_input = message.content.strip()
        print(user_input)

        # Show typing status
        async with message.channel.typing():

            # Get chatbot response
            response = ""
            for data in chatbot.ask(user_input):
                response = data["message"]

    # Send chatbot response as a text message if it is short enough, otherwise send it as a file attachment
        if len(response) >= 2000:
            # Write chatbot response to a temporary file
            with open("response.txt", "w") as f:
                f.write(response)

            # Send chatbot response as a text file attachment
            with open("response.txt", "r") as f:
                await message.reply("The response was too long! I've attempted to upload it as a file below.", file=discord.File("response.txt"))
            os.remove("response.txt")
        else: 
            await message.reply(response)



# Start the Discord client
client.run(os.getenv("GIR_TOKEN"))
