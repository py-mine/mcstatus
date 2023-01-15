from mcstatus import JavaServer

server = JavaServer.lookup("play.hypixel.net")
query = server.query()

if query.players.names:
    print("Players online:", ", ".join(query.players.names))
else:
    status = server.status()

    if not status.players.sample:
        print("Cant find players list, no one online or the server disabled this.")
    else:
        print("Players online:", ", ".join([player.name for player in status.players.sample]))
