# report builder

Running 

```bash
docker compose up
```

sets up a similar environment to the CI in this directory, i.e. after running 
`cd resources/report_builder`.

Then

```bash
docker run --rm -ti -v .:/data --workdir /data\
    --env UV_PROJECT_ENVIRONMENT=/tmp/venv\
    --env CATTLE_GRID_MQ=cattle_grid_mq\
    --network test\
    ghcr.io/astral-sh/uv:python3.11-alpine /bin/sh
```

in your checked out cattle grid version
