import click
import json
import uvicorn
import logging

from cattle_grid.extensions.load import load_extension

from .helper import (
    async_schema_for_extension,
    openapi_schema_for_extension,
    fastapi_for_extension,
)

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def run_app(module, port, host, no_broker):
    extension = load_extension({"module": module})

    if extension.transformer:
        logger.warning("The transformer associated with the extension will not be run")
        logger.warning(
            "For this to work, the extension needs to be loaded by cattle_grid"
        )

    if extension.lookup_method:
        logger.warning("The lookup included in this extension will not be included")
        logger.warning(
            "For this to work, the extension needs to be loaded by cattle_grid"
        )

    app = fastapi_for_extension(extension, include_broker=not no_broker)

    uvicorn.run(app, port=port, host=host)


def build_filename(filename: str | None, api_type: str, name: str) -> str:
    """
    ```
    >>> build_filename("file.txt", "openapi", "some name")
    'file.txt'

    >>> build_filename(None, "openapi", "simple html display")
    './docs/assets/schemas/openapi_simple_html_display.json'

    ```
    """
    if filename:
        return filename

    name = name.replace(" ", "_")
    return f"./docs/assets/schemas/{api_type}_{name}.json"


def add_extension_commands(main):
    @main.command("load")
    @click.argument("module")
    def load_extension_command(module):
        """Loads an extension"""
        load_extension({"module": module})

        # FIXME config parameters

    @main.command("async-api")
    @click.argument("module")
    @click.option("--filename", default=None, help="Filename to write to")
    def async_api(module, filename):
        """Generates the async api schema for the extension"""
        extension = load_extension({"module": module})
        schema = async_schema_for_extension(extension).to_json()
        filename = build_filename(filename, "asyncapi", extension.name)

        with open(filename, "w") as fp:
            fp.write(schema)

        click.echo(f"Wrote async api schema to {filename}")

    @main.command("openapi")
    @click.argument("module")
    @click.option("--filename", default=None, help="Filename to write to")
    def openapi(module, filename):
        """Generates the openapi schema for the extension"""
        extension = load_extension({"module": module})
        schema = openapi_schema_for_extension(extension)
        filename = build_filename(filename, "openapi", extension.name)

        with open(filename, "w") as fp:
            json.dump(schema, fp)

        click.echo(f"Wrote openapi schema to {filename}")

    @main.command("run")
    @click.argument("module")
    @click.option("--host", default="0.0.0.0", help="Host to run on")
    @click.option("--port", default=80, help="Port to run on")
    @click.option("--reload_dir", default=None, help="Reload on changes in directory")
    @click.option(
        "--no_broker",
        is_flag=True,
        default=False,
        help="Set to run without included broker",
    )
    def run_server(module, host, port, reload_dir, no_broker):
        """Runs the extension as an independent server process.
        The configuration is taken from the same files as cattle_grid.
        Thus these must be present."""

        if reload_dir:
            import watchfiles

            logger.info("Watching for changes in %s", reload_dir)

            watchfiles.run_process(
                reload_dir, target=run_app, args=(module, port, host, no_broker)
            )
        else:
            run_app(module, port, host, no_broker)


def add_extension_commands_as_group(main):
    @main.group("extensions")
    def extensions():
        """Commands for managing extensions"""

    add_extension_commands(extensions)
