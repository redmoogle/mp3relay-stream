import logging
from mp3relay import MP3Relay
import json

if __name__ == '__main__':
    relays = []

    def startRelays():
        for relay in relays:
            relay.startRelay()

    def stopRelays():
        for relay in relays:
            relay.stopRelay()

    with open('config.json', 'r') as configjson:
        config = json.load(configjson)
    bind_address = config["bind_addr"]

    for relayconfig in config["relays"]:
        relay: MP3Relay = MP3Relay()
        relay.stream = relayconfig["ip"]
        relay.port = relayconfig["port"]
        relay.bind_address = bind_address
        if("name" in relayconfig):
            relay.name = relayconfig["name"]
        relays.append(relay)
    try:
        print("Type `HELP` for a list of commands")
        while(True):
            inputstr = input().lower().strip()
            if(inputstr == "help"):
                print("""    | 1: Start Relays
    | 2: Stop Relays
    | 3: Display Relays
    | 4: Reload Relays""")
            if(inputstr == "1"):
                if(len(relays) == 1):
                    print(f"Started 1 relay")
                else:
                    print(f"Started {len(relays)} relays")
                startRelays()
            if(inputstr == "2"):
                if(len(relays) == 1):
                    print(f"Stopped 1 relay")
                else:
                    print(f"Stopped {len(relays)} relays")
                stopRelays()
            if(inputstr == "3"):
                print("Listing Relays")
                for relay in relays:
                    print(f"\t{relay}")
                    if(relay.packet):
                        print(f"{relay.packet}")
                    else:
                        print(f"\n\tDisconnected")
    except (KeyboardInterrupt, SystemExit):
        stopRelays()

