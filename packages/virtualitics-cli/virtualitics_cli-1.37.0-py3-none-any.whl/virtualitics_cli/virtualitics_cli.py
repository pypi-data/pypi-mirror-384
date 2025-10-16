import glob
import importlib.metadata
import json
import os
import string
import subprocess
import sys
from json import JSONDecodeError

import typer

from zipfile import ZipFile
import requests
from pathlib import Path
from art import *
from typing_extensions import Annotated
from typing import Optional
from rich import print
from rich import print_json
from rich.progress import Progress, SpinnerColumn, TextColumn

# TODO recommend installation via pipx to isolate virtualitics-cli from project environments
app = typer.Typer(name="vaip", pretty_exceptions_show_locals=False)
debug_state = {"verbose": False}

APP_NAME = "virtualitics-cli"
CONFIG_FILE_NAME = "virtualitics_config.json"


def get_current_context() -> tuple[str, str, str] | Exception:
    app_dir = typer.get_app_dir(APP_NAME)
    config_path: Path = Path(app_dir) / CONFIG_FILE_NAME
    if not config_path.exists():
        print("No configuration file found. Please run `vaip config` before using this command.")
        raise typer.Exit(code=1)

    with open(config_path, "r+") as f:
        try:
            current_config = json.load(f)
        except JSONDecodeError as e:
            print(":warning: Your configuration file is invalid or `vaip config` has not been run.")
            print(f"Config file location: {config_path}")
            print(e)
            raise typer.Exit(code=1)
        current_context = current_config[current_config["current_context"]]

        return current_context["host"], current_context["token"], current_context["username"]


def app_name_callback(ctx: typer.Context, app_name: str) -> str | None:
    if ctx.resilient_parsing:
        return
    invalid_characters = set(string.punctuation.replace("_", ""))
    invalid_characters.update(string.digits)  # Add numbers (0-9)
    invalid_characters.update(string.whitespace)  # Add whitespace
    if any(char in invalid_characters for char in app_name):
        raise typer.BadParameter("Invalid project name. The only special character allowed is '_'. Numbers, whitespace, and other special characters are not accepted.")
    else:
        return app_name


def context_name_callback(config_name: str):
    if config_name.lower() == "default_config_data":
        raise typer.BadParameter("It is not possible to use default_config_data as a config name.")

    app_dir = typer.get_app_dir(APP_NAME)
    config_path: Path = Path(app_dir) / CONFIG_FILE_NAME
    if config_path.exists():
        with open(config_path, "r") as f:
            try:
                current_config = json.load(f)
            except JSONDecodeError as e:
                print(":warning: Your configuration file is invalid or `vaip config` has not been run.")
                print(f"Config file location: {config_path}")
                print(e)
                raise typer.Exit(code=1)

        if config_name in list(current_config.keys()):
            raise typer.BadParameter(f"The configuration name '{config_name}' is already present.")

    return config_name


def version_callback(value: bool):
    if value:
        tprint("Virtualitics AI Platform", font="cybermedium")
        print(f"{APP_NAME}: {importlib.metadata.version(APP_NAME)}")
        raise typer.Exit()


@app.callback()
def main(version: Annotated[
    Optional[bool], typer.Option("--version", callback=version_callback)
] = False, verbose: bool = False) -> None:
    """
    Used to enable debug logs
    """
    if verbose is True:
        debug_state["verbose"] = True


def get_yes_no(prompt: str) -> bool:
    while True:
        response = typer.prompt(prompt).strip().lower()
        if response in {"y", "yes"}:
            return True
        elif response in {"n", "no"}:
            return False
        else:
            typer.echo("Invalid response. Please enter 'y' or 'n'.")


@app.command()
def config(config_name: Annotated[str, typer.Option("--name", "-N",
                                                    help="User-specified friendly name for a given "
                                                         "VAIP instance, i.e. predict-dev",
                                                    callback=context_name_callback,
                                                    prompt=True)],
           backend_host: Annotated[str, typer.Option("--host", "-H",
                                                     help="Backend hostname for a given VAIP instance, "
                                                          "i.e. https://predict-api-dev.virtualitics.com",
                                                     prompt=True)],
           api_token: Annotated[str, typer.Option("--token", "-T",
                                                  help="API token used to verify the user’s access "
                                                       "to the given VAIP instance")] = None,
           vaip_username: Annotated[str, typer.Option("--username", "-U",
                                                      help="Username associated with API token")] = None,
           use_previous: Annotated[str, typer.Option("--use-prev", help="Use the default values for the API token and username.")] = 'n'
           ):
    """
    Used to create or update a configuration file in the default Typer directory within the CLI app.
    Requires a friendly name of a VAIP instance, host of a VAIP instance, and an API token, and a username.
    """

    config_data = {
        "current_context": config_name,
        config_name: {
            "host": backend_host,
            "token": api_token,
            "username": vaip_username
        },
        "default_config_data": {
            "host": None,
            "token": api_token,
            "username": vaip_username
        }
    }

    app_dir = typer.get_app_dir(APP_NAME)
    config_path: Path = Path(app_dir)
    config_file: Path = Path(app_dir) / CONFIG_FILE_NAME
    if not config_path.exists():
        config_path.mkdir(parents=True, exist_ok=False)
    if not config_file.exists():
        config_file.touch(exist_ok=False)

    with open(config_file, "r") as f:
        if os.stat(config_file).st_size == 0:
            current_config = None
        else:
            try:
                current_config = json.load(f)
            except JSONDecodeError as e:
                print(":warning: Your configuration file is invalid.")
                print(f"Config file location: {config_path}")
                print(e)
                raise typer.Exit(code=1)

    if not current_config:
        api_token = typer.prompt("token:")
        vaip_username = typer.prompt("username:")

        config_data[config_name]["token"] = api_token
        config_data[config_name]["username"] = vaip_username
        config_data["default_config_data"]["token"] = api_token
        config_data["default_config_data"]["username"] = vaip_username
    else:
        if "default_config_data" not in current_config:
            api_token = typer.prompt("token")
            vaip_username = typer.prompt("username")

            config_data[config_name]["token"] = api_token
            config_data[config_name]["username"] = vaip_username
            config_data["default_config_data"]["token"] = api_token
            config_data["default_config_data"]["username"] = vaip_username

            current_config[config_name] = config_data[config_name]
            current_config["default_config_data"] = config_data["default_config_data"]
            current_config["current_context"] = config_name
            config_data = current_config
        else:
            api_token = current_config["default_config_data"]["token"]
            vaip_username = current_config["default_config_data"]["username"]

            print("\nDefault config:")
            print(f"Token: * * * {api_token[-5:]}")
            print(f"Username: {vaip_username}")
            use_previous = get_yes_no("Do you want to use the default settings for Token and Username? [y/n]")
            typer.echo(f"You chose: {'Yes' if use_previous else 'No'}")

            if not use_previous:
                api_token = typer.prompt("token")
                vaip_username = typer.prompt("username")

            config_data[config_name]["token"] = api_token
            config_data[config_name]["username"] = vaip_username

            current_config[config_name] = config_data[config_name]
            current_config["current_context"] = config_name
            config_data = current_config

    with open(config_file, "r+") as f:
        print_json(json.dumps(config_data))
        json.dump(config_data, f)

    print(f"Configuration file location: {config_file}")
    print("Configuration file updated. Use `vaip show-context` if you wish to see it.")


@app.command()
def use_context(context_name: Annotated[
    str, typer.Argument(help="The name of a previously configured context referenced in the configuration file.")]):
    """
    Used to set the context referenced for uploading in the config file
    """
    app_dir = typer.get_app_dir(APP_NAME)
    config_path: Path = Path(app_dir) / CONFIG_FILE_NAME
    if not config_path.exists():
        print("Could not successfully switch context. No configuration file found. Please run `vaip config` before using this command.")
        raise typer.Exit(code=1)

    with open(config_path, "r+") as f:
        try:
            current_config = json.load(f)
        except JSONDecodeError as e:
            print(":warning: Could not successfully switch context. Your configuration file is invalid or `vaip config` has not been run.")
            print(f"Config file location: {config_path}")
            print(e)
            raise typer.Exit(code=1)
        if context_name in current_config:
            current_config["current_context"] = context_name
        else:
            print(f":warning: Context: [bold]{context_name}[/bold] given does not exist.")
            raise typer.Exit(code=1)
    with open(config_path, "w") as f:
        json.dump(current_config, f)
        print(f"Now referencing [bold]{context_name}[/bold]")


@app.command()
def show_context():
    """
    Used to display the configuration file
    """
    app_dir = typer.get_app_dir(APP_NAME)
    config_path: Path = Path(app_dir) / CONFIG_FILE_NAME
    if not config_path.exists():
        print("No configuration file found. Please run `vaip config` before using this command.")
        raise typer.Exit(code=1)
    with open(config_path, "r") as f:
        try:
            current_config = json.load(f)
            print_json(data=current_config)
        except JSONDecodeError as e:
            print(":warning: Your configuration file is invalid or `vaip config` has not been run.")
            print(f"Config file location: {config_path}")
            print(e)
            raise typer.Exit(code=1)


@app.command()
def delete_context(context_name: Annotated[
    str, typer.Argument(
        help="The name of a previously configured context referenced in the configuration file to delete.")]):
    """
    Used to delete a specific context from the configuration file.
    """
    app_dir = typer.get_app_dir(APP_NAME)
    config_path: Path = Path(app_dir) / CONFIG_FILE_NAME
    if not config_path.exists():
        print("No configuration file found. Please run `vaip config` before using this command.")
        raise typer.Exit(code=1)
    with open(config_path, "r+") as f:
        try:
            current_config = json.load(f)
        except JSONDecodeError as e:
            print(":warning: Your configuration file is invalid or `vaip config` has not been run.")
            print(f"Config file location: {config_path}")
            print(e)
            raise typer.Exit(code=1)
        deleted_context = current_config.pop(context_name, None)
    if deleted_context:
        print(f"Context: [bold]{context_name}[/bold] was deleted. Current configuration file:")
        print_json(data=current_config)
        if current_config["current_context"] == context_name:
            print(f":warning: [bold red] current context is set to the deleted context {context_name}. "
                  f"Please run `vaip use-context [context]` [/bold red].")
        with open(config_path, "w") as f:
            json.dump(current_config, f)
    else:
        print(f"Context: {context_name} could not be found. Current configuration file:")
        print_json(current_config)
        raise typer.Exit(code=1)


@app.command()
def edit_context(context_name: Annotated[
    str, typer.Argument(
        help="The name of a previously configured context referenced in the configuration file to modify.")]):
    """
    Used to modify a specific context from the configuration file.
    """
    app_dir = typer.get_app_dir(APP_NAME)
    config_path: Path = Path(app_dir) / CONFIG_FILE_NAME
    if not config_path.exists():
        print("No configuration file found. Please run `vaip config` before using this command.")
        raise typer.Exit(code=1)
    with open(config_path, "r+") as f:
        try:
            current_config = json.load(f)
        except JSONDecodeError as e:
            print(":warning: Your configuration file is invalid or `vaip config` has not been run.")
            print(f"Config file location: {config_path}")
            print(e)
            raise typer.Exit(code=1)
        modified_context = current_config.pop(context_name, None)
    if not modified_context:
        print(f"Context: {context_name} could not be found. Current configuration file:")
        print_json(current_config)
        raise typer.Exit(code=1)
    else:
        print(f"Host: {modified_context['host']}")
        print(f"Token: * * * {modified_context['token'][-5:]}")
        print(f"Username: {modified_context['username']}")
        key = typer.prompt("Which value do you want to modify? [host/token/username]")

        if key not in modified_context:
            typer.echo("Invalid choice!")
            raise typer.Exit()

        new_value = typer.prompt(f"Enter the new value for {key}", type=str)
        modified_context[key] = new_value
        current_config[context_name] = modified_context

        with open(config_path, "w") as f:
            json.dump(current_config, f)
        print("Configuration file updated. Use `vaip show-context` if you wish to see it.")


# Todo make authors list
@app.command()
def init(project_name: Annotated[
    str, typer.Option("--project-name", "-n", callback=app_name_callback,
                      help="Name for the VAIP App (No spaces, numbers, whitespace or special chars besides '_')", prompt=True)],
         version: Annotated[str, typer.Option("--version", "-v",
                                              help="Version for the VAIP App (0.1.0)", prompt=True)],
         description: Annotated[
             str, typer.Option("--description", "-d", help="Description for the VAIP App",
                               prompt=True)],
         authors: Annotated[str, typer.Option("--authors", "-a", help="Authors for the VAIP App (email)",
                                              prompt=True)],
         licenses: Annotated[
             str, typer.Option("--licenses", "-l", help="Licenses for the VAIP App", prompt=True)]):
    """
    Initializes a VAIP app structure, and a pyproject.toml file that looks like this:
    [project]
    name = "vaip-apps"
    version = "0.1.1"
    description = "vaip example apps"
    authors = [{name = "Virtualitics Engineering", email = "engineering@virtualitics.com"}]
    license = {text = "MIT"}
    requires-python = ">= 3.11"

    [build-system]
    requires = ["setuptools >= 61.0"]
    build-backend = "setuptools.build_meta"

    """
    project_name = project_name.lower()
    if debug_state["verbose"]:
        print(f"Creating {project_name}/__init__.py")
    os.makedirs(f"{project_name}", exist_ok=True)
    with open(f"{project_name}/__init__.py", "w"):
        pass
    if debug_state["verbose"]:
        print(f"Creating {project_name}/blueprint_docs")
    os.makedirs(f"{project_name}/blueprint_docs", exist_ok=True)
    # TODO probably create blueprint doc example here
    if debug_state["verbose"]:
        print(f"Creating __init__.py")
    with open("__init__.py", "w"):
        pass
    if debug_state["verbose"]:
        print(f"Creating pyproject.toml")
    with open("pyproject.toml", "w"):
        pass

    # TODO, what we want is some way to identify that in vaip build, that vaip init was used
    pyproject_content = ["[project]\n", f"name = \"{project_name.replace('_', '-')}\"\n",
                         f"version = \"{version}\"\n",
                         f"description = \"{description}\"\n", f"authors = [{{name = \"{authors}\"}}]\n",
                         f"license = {{text = \"{licenses}\"}}\n",
                         "requires-python = \">= 3.11\"\n\n",
                         "[build-system]\n", "requires = [\"setuptools >= 69.0\"]\n",
                         "build-backend = \"setuptools.build_meta\"\n"]
    with open("pyproject.toml", "w") as f:
        f.writelines(pyproject_content)

    print(f"Initialization of VAIP App {project_name} structure complete.")


# TODO might want this https://pypi.org/project/setuptools-scm/
@app.command()
def build(confirm_build: Annotated[bool, typer.Option("--yes", "-y",
                                                      help="Build a wheel using pyproject.toml in current directory?",
                                                      prompt=True)]):
    """
    Builds a VAIP App Python wheel file
    """
    if not confirm_build:
        print("Did not confirm build.")
        raise typer.Exit(code=1)
    try:
        subprocess.check_call([sys.executable, '-m', 'build'])
        print("Successfully built VAIP App, check your /dist directory.")
    except subprocess.CalledProcessError as e:
        print(f"There was an error during build: {e}")
        print("Try running `python -m build` if you are having issues.")


# TODO, what we want is some way to identify that in vaip build, that vaip init was used
@app.command()
# https://typer.tiangolo.com/tutorial/parameter-types/path/
def deploy(file: Annotated[str, typer.Option("--file", "-f",
                                             help="Absolute path to the wheel file "
                                                  "if not in current project /dist")] = ""):
    """
    Deploys the VAIP App to a VAIP Instance
    """
    host, token, username = get_current_context()

    # else assume default dir ./dist/*.whl'
    if not file:
        try:
            file = glob.glob("./dist/*.whl")[0]
        except IndexError:
            print(
                f"Unable to locate a suitable wheel file. Perhaps try running vaip build, "
                f"or providing an absolute path with --file")
    if file.split(".")[-1] != "whl":
        print(f"File {file} does not appear to be a wheel file.")
        raise typer.Exit(code=1)
    files = {'file': open(file, 'rb')}
    if debug_state["verbose"]:
        print(f"Attempting to send files: {files}\n")
        names = ZipFile(file).namelist()
        print(f'Unzipped file contents: {names}\n')
    print(f"Using:\n username {username} \n token: ...{token[-4:]} \n host: {host} \n ")
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        try:
            progress.add_task(description="Uploading...", total=None)
            r = requests.post(f"{host}/cli/deploy/",
                              data={"username": username},
                              headers={"Authorization": f"Bearer {token}"},
                              files=files)
        except requests.exceptions.ConnectionError as e:
            print(f"Error: Unable to connect to {host}. Please check your connections and try again.")
            raise typer.Exit(code=1)
    if r.status_code == 404:
        print("Error: It looks like your VAIP instance is not configured for CLI App uploads.")
        raise typer.Exit(code=1)
    else:
        print_json(r.text)
        raise typer.Exit()


@app.command()
def destroy(
        project_name: Annotated[
            str, typer.Option("--project-name", "-n",
                              help="Project name to delete (ie, name in pyproject.toml)", prompt=True)],
        confirm_delete: Annotated[bool, typer.Option("--yes", "-y", prompt=True)]):
    """
    Deletes a VAIP module, and all the apps of that module.
    """
    # TODO project name has to be underscore, which user won't know if they copy from pyproject.toml
    host, token, username = get_current_context()
    if not confirm_delete:
        print("Did not confirm delete.")
        raise typer.Exit(code=1)
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        try:
            progress.add_task(description="Deleting...", total=None)
            r = requests.post(f"{host}/cli/delete/",
                              data={"username": username, "project_name": project_name},
                              headers={"Authorization": f"Bearer {token}"})
        except requests.exceptions.ConnectionError:
            print(f"Error: Unable to connect to {host}. Please check your connections and try again.")
            raise typer.Exit(code=1)
    # TODO, if invalid project name it just 404s from Predict
    if r.status_code == 404:
        print("Error: It looks like your VAIP instance is not configured for CLI App uploads.")
        raise typer.Exit(code=1)
    else:
        print_json(r.text)
        raise typer.Exit()


@app.command()
def publish():
    """
    Publishes a VAIP App to other users in your group
    """
    host, token, username = get_current_context()

    r = requests.post(f"{host}/cli/publish/",
                      data={"username": username},
                      headers={"Authorization": f"Bearer {token}"})

    print_json(r.text)
    print("Makes the current VAIP App available to other users in your group")
