import logging
import subprocess
import sys
import textwrap
import click

from .utils import (
    setup_logging,
    write_success,
    WRANGLER_COMMAND,
    WRANGLER_CREATE_COMMAND,
)

setup_logging()
logger = logging.getLogger("pywrangler")


class ProxyToWranglerGroup(click.Group):
    def get_help(self, ctx):
        """Override to add custom help content."""
        # Get the default help text
        help_text = super().get_help(ctx)

        # Get wrangler help and append it
        try:
            result = subprocess.run(
                WRANGLER_COMMAND + ["--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                wrangler_help = result.stdout
                # Replace 'wrangler' with 'pywrangler' in the help text
                wrangler_help = wrangler_help.replace("wrangler ", "pywrangler ")
                # Indent each line of the wrangler help
                indented_help = textwrap.indent(wrangler_help, "  ")
                help_text += "\n\nWrangler Commands (proxied):\n"
                help_text += indented_help
        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            subprocess.SubprocessError,
        ):
            # Fallback if wrangler is not available
            help_text += f"\n\nNote: Run '{' '.join(WRANGLER_COMMAND)} --help' for additional wrangler commands."

        return help_text

    def get_command(self, ctx, cmd_name):
        command = super().get_command(ctx, cmd_name)

        if command is None:
            try:
                cmd_index = sys.argv.index(cmd_name)
                remaining_args = sys.argv[cmd_index + 1 :]
            except ValueError:
                remaining_args = []

            if cmd_name in ["dev", "publish", "deploy", "versions"]:
                ctx.invoke(sync_command, force=False, directly_requested=False)

            if cmd_name == "dev":
                from .sync import check_wrangler_version

                check_wrangler_version()

            if cmd_name == "init":
                # explicitly call `create-cloudflare` so we can instruct it to only show Python templates
                _proxy_to_create_cloudflare(
                    ["--lang=python", "--no-deploy"] + remaining_args
                )
                sys.exit(0)

            _proxy_to_wrangler(cmd_name, remaining_args)
            sys.exit(0)

        return command


def get_version():
    """Get the version of pywrangler."""
    try:
        from importlib.metadata import version

        return version("workers-py")
    except Exception:
        return "unknown"


@click.group(cls=ProxyToWranglerGroup)
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.version_option(version=get_version(), prog_name="pywrangler")
@click.pass_context
def app(ctx, debug=False):
    """
    A CLI tool for Cloudflare Workers.
    Use 'sync' command for Python package setup.
    All other commands are proxied to 'wrangler', with `dev` and `deploy`
    automatically running `sync` first before proxying.
    """

    # Set the logging level to DEBUG if the debug flag is provided
    if debug:
        logger.setLevel(logging.DEBUG)


@app.command("types")
@click.option(
    "-o",
    "--outdir",
    type=click.Path(writable=True),
    help="The output directory to write the generated types. Default: ./src",
)
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to Wrangler configuration file",
)
def types_command(outdir=None, config=None):
    from .types import wrangler_types

    wrangler_types(outdir, config)
    raise click.exceptions.Exit(code=0)


@app.command("sync")
@click.option("--force", is_flag=True, help="Force sync even if no changes detected")
def sync_command(force=False, directly_requested=True):
    """
    Installs Python packages from pyproject.toml into src/vendor.

    Also creates a virtual env for Workers that you can use for testing.
    """
    # This module is imported locally because it searches for pyproject.toml at the top-level.
    from .sync import (
        check_requirements_txt,
        check_wrangler_config,
        is_sync_needed,
        create_pyodide_venv,
        create_workers_venv,
        parse_requirements,
        install_requirements,
    )

    # Check if requirements.txt does not exist.
    check_requirements_txt()

    # Check if sync is needed based on file timestamps
    sync_needed = force or is_sync_needed()
    if not sync_needed:
        if directly_requested:
            logger.warning(
                "pyproject.toml hasn't changed since last sync, use --force to ignore timestamp check"
            )
        return

    # Check to make sure a wrangler config file exists.
    check_wrangler_config()

    # Create .venv-workers if it doesn't exist
    create_workers_venv()

    # Set up Pyodide virtual env
    create_pyodide_venv()

    # Generate requirements.txt from pyproject.toml by directly parsing the TOML file then install into vendor folder.
    requirements = parse_requirements()
    if not requirements:
        logger.warning(
            "No dependencies found in [project.dependencies] section of pyproject.toml."
        )
    install_requirements(requirements)

    write_success("Sync process completed successfully.")


def _proxy_to_wrangler(command_name, args_list):
    command_to_run = WRANGLER_COMMAND + [command_name] + args_list
    logger.info(f"Passing command to npx wrangler: {' '.join(command_to_run)}")
    try:
        process = subprocess.run(command_to_run, check=False, cwd=".")
        click.get_current_context().exit(process.returncode)
    except FileNotFoundError as e:
        logger.error(
            f"Wrangler not found. Ensure Node.js and Wrangler are installed and in your PATH. Error was: {str(e)}"
        )
        click.get_current_context().exit(1)


def _proxy_to_create_cloudflare(args_list):
    command_to_run = WRANGLER_CREATE_COMMAND + args_list
    logger.info(f"Passing command to npx create-cloudflare: {' '.join(command_to_run)}")
    try:
        process = subprocess.run(command_to_run, check=False, cwd=".")
        click.get_current_context().exit(process.returncode)
    except FileNotFoundError as e:
        logger.error(
            f"Create-cloudflare not found. Ensure Node.js and create-cloudflare are installed and in your PATH. Error was: {str(e)}"
        )
        click.get_current_context().exit(1)
