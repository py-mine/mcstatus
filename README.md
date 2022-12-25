# <img src="https://i.imgur.com/nPCcxts.png" height=25> MCStatus
[![discord chat](https://img.shields.io/discord/936788458939224094.svg?logo=Discord)](https://discord.gg/C2wX7zduxC)
![supported python versions](https://img.shields.io/pypi/pyversions/mcstatus.svg)
[![current PyPI version](https://img.shields.io/pypi/v/mcstatus.svg)](https://pypi.org/project/mcstatus/)
[![Validation](https://github.com/py-mine/mcstatus/actions/workflows/validation.yml/badge.svg)](https://github.com/py-mine/mcstatus/actions/workflows/validation.yml)
[![Tox test](https://github.com/py-mine/mcstatus/actions/workflows/tox-test.yml/badge.svg)](https://github.com/py-mine/mcstatus/actions/workflows/tox-test.yml)

Mcstatus provides an easy way to query Minecraft servers for any information they can expose.  
It includes three modes of access (`query`, `status` and `ping`), the differences of which are listed below in usage.

## Usage

We provide both an API which you can use in your projects, and a command line script, to quickly query a server.

### Python API

Java Edition
```python
from mcstatus import JavaServer

# You can pass the same address you'd enter into the address field in minecraft into the 'lookup' function
# If you know the host and port, you may skip this and use JavaServer("example.org", 1234)
server = JavaServer.lookup("example.org:1234")

# 'status' is supported by all Minecraft servers that are version 1.7 or higher.
status = server.status()
print(f"The server has {status.players.online} players and replied in {status.latency} ms")

# 'ping' is supported by all Minecraft servers that are version 1.7 or higher.
# It is included in a 'status' call, but is also exposed separate if you do not require the additional info.
latency = server.ping()
print(f"The server replied in {latency} ms")

# 'query' has to be enabled in a servers' server.properties file!
# It may give more information than a ping, such as a full player list or mod information.
query = server.query()
print(f"The server has the following players online: {', '.join(query.players.names)}")
```

Bedrock Edition
```python
from mcstatus import BedrockServer

# You can pass the same address you'd enter into the address field in minecraft into the 'lookup' function
# If you know the host and port, you may skip this and use MinecraftBedrockServer("example.org", 19132)
server = BedrockServer.lookup("example.org:19132")

# 'status' is the only feature that is supported by Bedrock at this time.
# In this case status includes players_online, latency, motd, map, gamemode, and players_max. (ex: status.gamemode)
status = server.status()
print(f"The server has {status.players.online} players online and replied in {status.latency} ms")
```

Status methods (`JavaServer.status` and `BedrockServer.status`) return similar answer objects, here is a scheme for them:

- `players`: Some players' info, like current online.
  - `online`: Current count of players, which playing on the server.
  - `max`: Maximum of possible players on the server.
  - (Java only) `sample`: List of players that playing at this moment.
    - `name`: Player's name.
    - `id`: Player's ID.
    - `uuid`: Alias to `id` because it's actually in UUID format.
- `version`: Some server's version info.
  - `name`: Version name, like `1.18.0`.
  - `protocol`: Version protocol. See [wiki](https://minecraft.fandom.com/wiki/Protocol_version).
  - (Bedrock only) `brand`: Version brand, like `MCPE` or something another.
- `motd`: Message of the Day (or just description) of the server.
- `description`: Alias to `motd`.
- `latency`: Latency between a server and the client (you). In milliseconds.
- (Java only) `icon`: Base64 encoded icon of the server.
- (Bedrock only) `map_name`: Name of the map in the server.
- (Bedrock only) `gamemode`: Gamemode of the server.

You should also check [`status_response.py`](https://github.com/py-mine/mcstatus/blob/master/mcstatus/status_response.py)
for type hints, if you're interested in those.

### Command Line Interface

At present time, this only works with Java servers, Bedrock is not yet supported.
```
$ mcstatus
Usage: mcstatus [OPTIONS] ADDRESS COMMAND [ARGS]...

  mcstatus provides an easy way to query Minecraft servers for any
  information they can expose. It provides three modes of access: query,
  status, and ping.

  Examples:

  $ mcstatus example.org ping
  21.120ms

  $ mcstatus example.org:1234 ping
  159.903ms

  $ mcstatus example.org status
  version: v1.8.8 (protocol 47)
  description: "A Minecraft Server"
  players: 1/20 ['Dinnerbone (61699b2e-d327-4a01-9f1e-0ea8c3f06bc6)']

  $ mcstatus example.org query
  host: 93.148.216.34:25565
  software: v1.8.8 vanilla
  plugins: []
  motd: "A Minecraft Server"
  players: 1/20 ['Dinnerbone (61699b2e-d327-4a01-9f1e-0ea8c3f06bc6)']

Options:
  -h, --help  Show this message and exit.

Commands:
  json    combination of several other commands with json formatting
  ping    prints server latency
  query   detailed server information
  status  basic server information
```

## Installation

Mcstatus is available on [PyPI](https://pypi.org/project/mcstatus/), and can be installed trivially with:

```bash
python3 -m pip install mcstatus
```

Alternatively, just clone this repo!

## License

Mcstatus is licensed under the Apache 2.0 license.
