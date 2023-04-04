import json
from mp3relay import MP3Relay

def startRelays(relays: list[MP3Relay]):
    for _relay in relays:
        _relay.startRelay()

def stopRelays(relays: list[MP3Relay]):
    for _relay in relays:
        _relay.stopRelay()

if __name__ == '__main__':
    configs = []
    with open('config.json', 'r', encoding="utf-8") as configjson:
        config = json.load(configjson)
    bind_address = config["bind_addr"]

    for relayconfig in config["relays"]:
        relay: MP3Relay = MP3Relay()
        relay.stream = relayconfig["ip"]
        relay.port = relayconfig["port"]
        relay.bind_address = bind_address
        if("name" in relayconfig):
            relay.name = relayconfig["name"]
        configs.append(relay)
    startRelays(configs)