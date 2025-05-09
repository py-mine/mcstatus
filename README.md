# <img src="https://i.imgur.com/nPCcxts.png" height="25" style="height: 25px"> MCStatus

[![discord chat](https://img.shields.io/discord/936788458939224094.svg?logo=Discord)](https://discord.gg/C2wX7zduxC)
![supported python versions](https://img.shields.io/pypi/pyversions/mcstatus.svg)
[![current PyPI version](https://img.shields.io/pypi/v/mcstatus.svg)](https://pypi.org/project/mcstatus/)
[![Docs](https://img.shields.io/readthedocs/mcstatus?label=Docs)](https://mcstatus.readthedocs.io/)
[![Validation](https://github.com/py-mine/mcstatus/actions/workflows/validation.yml/badge.svg)](https://github.com/py-mine/mcstatus/actions/workflows/validation.yml)
[![Unit Tests](https://github.com/py-mine/mcstatus/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/py-mine/mcstatus/actions/workflows/unit-tests.yml)

Mcstatus provides an API and command line script to fetch publicly available data from Minecraft servers. Specifically, mcstatus retrieves data by using these protocols: [Server List Ping](https://wiki.vg/Server_List_Ping) and [Query](https://wiki.vg/Query). Because of mcstatus, you do not need to fully understand those protocols and can instead skip straight to retrieving minecraft server data quickly in your own programs.

## Installation

Mcstatus is available on [PyPI](https://pypi.org/project/mcstatus/), and can be installed trivially with:

```bash
python3 -m pip install mcstatus
```

## Usage

### Python API

#### Java Edition

```python
from mcstatus import JavaServer

# You can pass the same address you'd enter into the address field in minecraft into the 'lookup' function
# If you know the host and port, you may skip this and use JavaServer("example.org", 1234)
server = JavaServer.lookup("example.org:1234")

# 'status' is supported by all Minecraft servers that are version 1.7 or higher.
# Don't expect the player list to always be complete, because many servers run
# plugins that hide this information or limit the number of players returned or even
# alter this list to contain fake players for purposes of having a custom message here.
status = server.status()
print(f"The server has {status.players.online} player(s) online and replied in {status.latency} ms")

# 'ping' is supported by all Minecraft servers that are version 1.7 or higher.
# It is included in a 'status' call, but is also exposed separate if you do not require the additional info.
latency = server.ping()
print(f"The server replied in {latency} ms")

# 'query' has to be enabled in a server's server.properties file!
# It may give more information than a ping, such as a full player list or mod information.
query = server.query()
print(f"The server has the following players online: {', '.join(query.players.names)}")
```

#### Bedrock Edition

```python
from mcstatus import BedrockServer

# You can pass the same address you'd enter into the address field in minecraft into the 'lookup' function
# If you know the host and port, you may skip this and use BedrockServer("example.org", 19132)
server = BedrockServer.lookup("example.org:19132")

# 'status' is the only feature that is supported by Bedrock at this time.
# In this case status includes players.online, latency, motd, map, gamemode, and players.max. (ex: status.gamemode)
status = server.status()
print(f"The server has {status.players.online} players online and replied in {status.latency} ms")
```

See the [documentation](https://mcstatus.readthedocs.io) to find what you can do with our library!

### Command Line Interface

The mcstatus library includes a simple CLI. Once installed, it can be used through:

```bash
python3 -m mcstatus --help
```

## License

Mcstatus is licensed under the Apache 2.0 license. See LICENSE for full text.
