# A toy/sample integration with Shinkansen

Live at: http://tamagotchi.fly.dev/

## Development

Install pre-commit hooks:

    $ pre-commit install

Install and run with poetry:

    $ poetry install
    $ poetry shell

Then set the following environment variables:

  - `FLASK_SECRET_KEY`: A random string.
  - `SHINKANSEN_CERTIFICATE_1` A certificate to validate Shinkansen's messages 
    (as a PEM string)
  - `SHINKANSEN_CERTIFICATE_2` An optional additional certificate to validate 
    Shinkansen's messages (as a PEM string)    
  - `TAMAGOTCHI_API_KEY`: A valid API Key for the Shinkansen's testing network
  - `TAMAGOTCHI_CERTIFICATE`: A certificate registered in Shinkansen's testing
    network (as a PEM string).
  - `TAMAGOTCHI_CERTIFICATE_PRIVATE_KEY`: The certificate private key
    (as a PEM string).
  - `TAMAGOTCHI_SENDER`: The identifier of the financial institution sending
     messages in the Shinkansen's testing network. Defaults to "TAMAGOTCHI" if
     not set.
  - `TAMAGOTCHI_LEGAL_NAME`: The legal name to be used for the sender.
    Defaults to "Fictional Tamagotchi SpA" if not set.
  - `TAMAGOTCHI_RUT`: The tax id to be used for the sender. Defaults to
    "11111111-1" if not set.
  - `TAMAGOTCHI_EMAIL`: The email used by the sender. Defaults to 
    team@shinkansen.cl if not set.
  - `TAMAGOTCHI_ACCOUNT_NUMBER`: The account number to be used for the sender.
    Defaults to "4242424242424242" if not set.
  - `TAMAGOTCHI_MAX_AMOUNT`: The maximum amount to allow in a payout. All payouts are 
    automatically capped up to this amount. 



And finally run it (inside the poetry shell):

    $ flask --app tamagotchi init-db
    $ flask --app tamagotchi --debug run

## Deploy

The current deploy was hastily put together and should be improved. But works.

It's a fairly simple docker image (see `Dockerfile`) which can be tested with
docker-compose up (see `docker-compose.yml`) and deployed to fly.io (see
`fly.toml`).

Deploy with:

    $ flyctl deploy && flyctl deploy -a tamagotchi-bice

(Make sure the env variables are set via `flyctl secrets add VAR=...`)
