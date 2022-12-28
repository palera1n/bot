# Cosmo

Cosmo is a sophisticated moderation and miscellaneous utilities Discord bot for the [palera1n Discord server](https://dsc.gg/palera1n) based of [GIR](https://gir.gay). It features:

- Completely based on Discord's Slash Commands, written in the [Discord.py library](https://github.com/Rapptz/discord.py)
- Standard moderation commands such as warn, mute, kick, ban, ...
- XP and role-based permissions system
- An advanced filter and anti-raid system
- A logging and message mirroring system
- Self-assignable roles
- Miscellaneous utilities like `/canijailbreak`
- And much more!

Cosmo is custom made and therefore there is no publicly running bot you can invite to your own server. However, you can self-host it as is or fork the code and modify it to your own requirements!

> See also: [Bloo](https://github.com/DiscordGIR/Bloo) and [GIR](https://github.com/DiscordGIR/GIRRewrite)

---

## Pre-setup instructions
These instructions *should* work on macOS, Windows and Linux.

### Setting up the `.env` file
1. Copy the `.env.example` to a file called `.env`
2. Start filling in the values as you want it set up. Follow the comments for hints.
3. For the `DB_HOST` variable:
    - If running the bot without Docker (not recommended), you can change `DB_HOST` to `localhost` instead. 
    - If running Mongo without Docker, `host.docker.internal` works on macOS and Windows, on Linux you can use `172.17.0.1`. 
    - If running Mongo in Docker, set `DB_HOST` to `mongo`

> **NOT RECOMMENDED FOR PRODUCTION DUE TO POOR PERFORMANCE**
Optionally, you can use [MongoDB Atlas](https://www.mongodb.com/atlas/database) instead of a local Mongo server. In that case, you use:
`DB_CONNECTION_STRING=mongodb+srv://.....` instead of `DB_HOST` and `DB_PORT`.

## Setting up the bot

### Production setup
This setup uses Docker for deployment. You will need the following:
- Docker
- `docker-compose`
- Mongo installation (optional, but recommended because it makes the setup easier. Advanced uses can also run Mongo in Docker, follow the instructions in `docker-compose.yml`).

> Alternatively, you could set up the bot without Docker using PM2 but I won't provide instructions for that.

#### Steps
1. Set up the `.env`. file. Keep in mind whether or not you want to use Mongo in Docker or not. 
2. Set up the database.
3. Skip this step if running Mongo without Docker. If you want to run Mongo in Docker, you will need to edit `docker-compose.yml` slightly. Open it and follow the comments.
4. Run the bot using `docker-compose up -d --build`.

If everything is successful, the bot should be online in a few seconds. Otherwise, check the container's logs: `docker-compose logs gir`.

> **IMPORTANT**: Slash commands are not synced automatically. Instead, the bot owner can DM the bot `!sync` to sync slash commands with Discord. This only needs to be done once when the bot is set up, or when you change any of the command data (such adding a new command, changing a command's name or description, etc.) 

The bot can be updated in the future by running: `git pull && docker-compose up -d --build --force-recreate`

---

### Development setup: with Docker (recommended!)
You will need the following installed:
- Docker
- Visual Studio Code to run the development container
- MongoDB running on the host machine or [MongoDB Atlas](https://www.mongodb.com/atlas/database).

#### Steps
1. Clone the repository and open the folder in Visual Studio Code
2. Install the [Microsoft Remote Development](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack) plugin
3. Make sure that Docker is running
4. Open the Command Palette (`CMD+Shift+P` or `CTRL+Shift+P`) and run "Remote-Containers: Reopen In Container"
5. VSCode should build the Docker image and open it automatically; this may take a couple of minutes as it has to install some extensions as well.
6. Set up the `.env` file as shown [here](#env-file).
7. Make sure the database is set up (see below).
8. Open the integrated terminal in VSCode and run the `gir` command to start the bot with hot reload!

> Note that if you make changes to the `Dockerfile`, `.devcontainer.json`, or need to install a new requirement, you need to rebuild the Docker image. You can do this through the Command Palette again, run "Remote-Containers: Rebuild Container".

---

### Development setup: without Docker (not recommended)
You will need the following installed:
- `python3.9+`
- `venv` (Python's virtualenv module)
- MongoDB running on the host machine or [MongoDB Atlas](https://www.mongodb.com/atlas/database).

#### Steps
1. Inside the root folder of the project, run `python3 -m venv venv/`
2. `source venv/bin/activate`
3. `pip3 install -r requirements.txt`
4. Set up the .env file as shown [here](#env-file).
5. Make sure the database is set up (see below).
6. `python3 main.py`

---

### Database setup
If you have an existing dump of the database, make sure Mongo is running, then you can run `mongorestore <dump foldername>`. This can also be done if running Mongo in Docker by first copying the dump to the Mongo container with `docker cp`.

If setting up the database from scratch, follow these instructions:
1. Make sure you filled out the right values for the `.env` file as explained above.
2. Open up `setup.py` and fill in **ALL** the values. The bot's permissions, and as a result the bot itself, will not work without them.
3. Run `setup.py`:
    - If running the bot without Docker, follow the first few setup instructions until you need to set up the database, activate the `virtualenv` and then run `python3 setup.py`. Then you can proceed with the rest of the setup instructions.
    - If running the bot with Docker in production, start the container then run: `docker exec -it <Cosmo container name> python3 setup.py` (if you get an error about the container restarting, restart the container and try to run the command again immediately). You can find the container name by running `docker container ls` in the project folder. After it's setup, restart the container. **Note:** changes to `setup.py` won't be transferred until you rebuild the container. So build the container AFTER `setup.py` is set up how you want.
    - If running the bot with Docker in development, you can just run `python3 setup.py` in the integrated bash shell.

If you want to inspect or change database values:
- If running MongoDB locally, you can install Robo3T.
- If running MongoDB in Docker, you can use the web GUI at http://127.0.0.1:8081

---

## Contributors / special thanks

Thanks to the GIR team and others for making Cosmo possible.

Please see GIR's contributors and special thanks section [here](https://github.com/DiscordGIR/GIRRewrite#contributors).
