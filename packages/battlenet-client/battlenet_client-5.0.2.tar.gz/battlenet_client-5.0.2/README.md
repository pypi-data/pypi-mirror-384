# Battlenet Client

![Pipeline Status](https://gitlab.com/battlenet-client/api/battlenet-client/badges/main/pipeline.svg)
![Release](https://gitlab.com/battlenet-client/api/battlenet-client/-/badges/release.svg?order_by=release_at)
![coverage](https://gitlab.com/battlenet-client/api/battlenet-client/badges/main/coverage.svg?job=coverage)

## Introduction
While this package can be used as a standalone, it works better when coupled with one of the API packages:

- [Diablo III Battlenet API](https://gitlab.com/battlenet-client/api/battlenet-d3)
- [Hearthstone Battlenet API](https://gitlab.com/battlenet-client/api/battlenet-hs)
- [Overwatch League Battlenet API](https://gitlab.com/battlenet-client/api/battlenet-owl)
- [Starcraft II Battlenet API](https://gitlab.com/battlenet-client/api/battlenet-sc2)
- [World of Warcraft Battlenet API](https://gitlab.com/battlenet-client/api/battlenet-wow)

## Installation

### Base Install
`pip install battlenet-client`

### Optional Installs

- Developement Install: `pip install battlenet-client[dev]`
- Full Client Install: `pip install battlenet-client[client]`
- MongoDB Backend:  `pip install battlenet-client[mongo]`
- PostgreSQL Backend: `pip install battlenet-client[postgresql]`
- MySQL or MariaDB Backend: `pip install battlenet-client[mysql]`

## Usage:

To use the client crediential workflow

    from battlenet_client.client import BattlenetClient
    client = BattlenetClient.client_credentials(<region abbreviation>, <client id>, <client secret>)

To use the authorization workflow and Open ID Connect, you will need a webserver that will handle the callback

    from battlenet_client.client import BattlenetClient
    client = BattlenetClient.authorization_code(<region abbreviation>, <client id>, <client secret>, <redirect uri>
                                                <scope>)
    redirect(client.get_authorization_url()

User logs into Battl.net with user name and password. After successful login, the user is redirected to "<redirect_uri>"
As part of the example code uses a Flask app to perform the role of the web server.

    @app.route(<redirect uri>)
    def callback():
        client.callback(request.args.get("code"), request.args.get("state"))
        ...

The webserver then processes and save the new token for the user

See the instructions for the specific module for further details.