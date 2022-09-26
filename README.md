# A toy/sample integration with Shinkansen

Live at: http://tamagotchi.fly.dev/

## Development

Install pre-commit hooks:

    $ pre-commit install

Install and run with poetry:

    $ poetry install
    $ poetry shell

Then set the following environment variables:
    - `TAMAGOTCHI_API_KEY`: A valid API Key for the Shinkansen's testing network
    - `TAMAGOTCHI_CERTIFICATE`: A certificate registered in Shinkansen's testing network
    - `TAMAGOTCHI_CERTIFICATE_PRIVATE_KEY`: The certificate private key
    - `TAMAGOTCHI_SENDER`: The identifier of the financial institution sending messages in the Shinkansen's testing network. Defaults to 'TAMAGOTCHI' if not set.
    - `FLASK_SECRET_KEY`: A random string


And finally run it (inside the poetry shell):

    $ flask --app tamagotchi init-db
    $ flask --app tamagotchi --debug run

## Deploy

The current deploy was hastily put together and should be improved. But works.

It's a fairly simple docker image (see `Dockerfile`) which can be tested with
docker-compose up (see `docker-compose.yml`) and deployed to fly.io (see
`fly.toml`).

Deploy with:

    $ flyctl deploy

(Make sure the env variables are set via `flyctl secrets add VAR=...`)
