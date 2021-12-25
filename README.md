# bcoin-trader
This is a Discord bot frontend to the associated bcoin backend API. It lets Discord users join and participant in a super serious, highly secure, definetely real crypto economy, trading in the hottest new coin, BCOIN. The B could stand for literally anything and definitely isn't one of my friends. 

Note: This project is *definitely* not secure, well-tested, etc. It was hacked together quickly and probably won't ever be maintained. You have been warned. 

## Tech
This project uses the awesome [discord.py](https://discordpy.readthedocs.io/en/stable/index.html) to accept user interaction and is set up to run inside a Docker image. 

## Configuration
Configuration values are loaded into env vars from a .env file. See [.env.template](.env.template) for an example. The configuration values are as follows:

| Config | Description |
| ------ | ----------- |
| DISCORD_TOKEN | You need to register your Discord bot, grab it's token, and put it here so it can talk to Discord |
| API_HOST | The hostname where the API can be reached |
| API_PORT | The port where the API can be reached |
| API_USERNAME | The basicauth username used to authenticate with the API |
| API_PASSWORD | The basicauth password used to authenticate with the API |
| CURRENCY_EMOJI | The emoji to use as the currency symbol for your BCOIN. The default is just the letter B. This is just the name of the emoji you want to use, so if your emoji is usually written as `:funny_emoji:`, set this to `funny_emoji` |
| PERMITTED_CHANNELS | Comma-separated list of channel ids that the bot will respond to. If users send the bot commands outside of one of these channels, the commands will be ignored. |

## Tests
Lol maybe someday

## Running
To run the bot, use the following commands:
```
docker build -t bcoin-trader:latest .
docker run --env-file .env --net="host" bcoin-trader
```

That option `--net="host"` makes it so your container sees `localhost` as the host's `localhost`, so you can connect to other services on the host directly. This is probably not secure and there's almost definitely a better way to do this, but yolo. 
