# cattle_grid

THIS README needs to be updated for cattle_grid 0.2.0

cattle_grid is meant to simplify handling authentication in server to
server communication of the Fediverse. cattle_grid checks the HTTP
signatures based on the headers. For this public keys are retrieved
and cached.

For installation instructions see the [documentation](https://bovine.codeberg.page/cattle_grid/).

## Development

### Testing

You can run the pytest tests via

```bash
uv run pytest
```

or in watch mode

```bash
uv run ptw .
```

### Running behave tests

Build the container via

```bash
./update_docker.sh
```

This script uses the requirements from `pyproject.toml` via `uv export` to install
python dependencies in the container. This means this script needs to be rerun, if
you make changes to the dependencies. Startup the docker environment via

```bash
docker compose up
```

Open a runner container

```bash
docker compose run --rm --name runner cattle_grid_app /bin/sh
```

Inside this container, you now run

```bash
fediverse-features
behave
```

The first step downloads some features from [fediverse-features](https://codeberg.org/helge/fediverse-features)
and the second step runs the test suite.

### Building end 2 end reports  (as done by CI)

The process to build the end to end reports is described [here](./resources/report_builder/README.md). The reports should be published to [this repository](https://codeberg.org/helge/cattle_grid_reports) and then made available [here](https://helge.codeberg.page/cattle_grid_reports/).

### Running as stand alone

Create a requirements.txt file and start a virgin docker container

```bash
uv export --no-editable --no-emit-project --no-hashes --no-dev > requirements.txt
docker run --rm -ti -p 8000:8000\
    -v ./cattle_grid:/app/cattle_grid\
    -v ./requirements.txt:/app/requirements.txt \
    --workdir /app\
    helgekr/bovine:python3.13 /bin/sh
```

Once inside the docker container install dependencies

```sh
pip intall -r requirements.txt
```

and run `cattle_grid` via

```sh
uvicorn cattle_grid:create_app --factory --host 0.0.0.0
```

This currently fails.