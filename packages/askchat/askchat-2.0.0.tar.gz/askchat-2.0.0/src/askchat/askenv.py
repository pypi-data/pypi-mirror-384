import click
from askchat import write_config, EnvNameCompletionType
from chattool.const import CHATTOOL_ENV_DIR, CHATTOOL_ENV_FILE
from dotenv import set_key

help_message = """Manage askchat environments.

To enable autocompletion, add the following line to your shell configuration file (e.g., .bashrc, .zshrc):

For zsh users: eval "$(_ASKENV_COMPLETE=zsh_source askenv)"

For bash users: eval "$(_ASKENV_COMPLETE=bash_source askenv)\""""

@click.group(help=help_message)
def cli():
    """askenv CLI for managing askchat environments."""
    if not CHATTOOL_ENV_DIR.exists():
        CHATTOOL_ENV_DIR.mkdir(parents=True)

@cli.command()
def list():
    """List all environment configurations."""
    configs = [env for env in CHATTOOL_ENV_DIR.glob('*.env')]
    if configs:
        click.echo("Available environments:")
        for config in configs:
            click.echo(f"- {config.stem}")
    else:
        click.echo("No environments found in ~/.askchat/envs.")

@cli.command()
@click.argument('name')
@click.option('-a', '--api-key', default=None, help='API key')
@click.option('-b', '--base-url', default=None, help='Base URL of the API (without suffix `/v1`)')
@click.option('--api-base', default=None, help='Base URL of the API (with suffix `/v1`)')
@click.option('-m', '--model', default=None, help='Model name')
@click.option('--interactive', '-i', is_flag=True, default=False, help='Enable interactive mode for inputting options')
def new(name, api_key, base_url, api_base, model, interactive):
    """Create a new environment configuration."""
    config_path = CHATTOOL_ENV_DIR / f'{name}.env'
    if config_path.exists():
        click.echo(f"Warning: Overwriting existing environment '{name}'.")
        click.confirm("Do you want to continue?", abort=True)
    if interactive:
        api_key = click.prompt('API key', default=api_key, hide_input=True)
        base_url = click.prompt('Base URL of the API (without suffix `/v1`)', default=base_url)
        default_api_base = f"{base_url}/v1" if base_url else api_base
        api_base = click.prompt('Base URL of the API (with suffix `/v1`)', default=default_api_base)
        model = click.prompt('Default model name', default=model)
    write_config(config_path, api_key, model, base_url, api_base, overwrite=True)

@cli.command()
@click.argument('name', required=False, type=EnvNameCompletionType())
@click.option('--default', is_flag=True, help='Delete the default environment configuration')
def delete(name, default):
    """Delete an environment configuration."""
    if default:
        default_config_path = CHATTOOL_ENV_DIR / 'default.env'
        if default_config_path.exists():
            default_config_path.unlink()
            click.echo("Default environment configuration deleted.")
        else:
            click.echo("No default environment configuration found.")
    else:
        if not name:
            click.echo("Please specify an environment name or use --default to delete the default configuration.")
            return
        config_path = CHATTOOL_ENV_DIR / f'{name}.env'
        if config_path.exists():
            config_path.unlink()
            click.echo(f"Environment '{name}' deleted.")
        else:
            click.echo(f"Environment '{name}' not found.")

@cli.command()
@click.argument('name', required=False, type=EnvNameCompletionType())
def show(name):
    """Print environment variables. Show default if no name is provided."""
    config_path = CHATTOOL_ENV_DIR / f'{name}.env' if name else CHATTOOL_ENV_FILE
    if config_path.exists():
        with config_path.open() as f:
            click.echo(f.read())
    else:
        if name:
            click.echo(f"Environment '{name}' not found.")
        else:
            click.echo("No active environment. You can use `askenv new` to new one.")

@cli.command()
@click.argument('name')
def save(name):
    """Save the current environment variables to a file."""
    if CHATTOOL_ENV_FILE.exists():
        content = CHATTOOL_ENV_FILE.read_text()
        config_path = CHATTOOL_ENV_DIR / f'{name}.env'
        if config_path.exists():
            click.echo(f"Warning: Overwriting existing environment '{name}'.")
            click.confirm("Do you want to continue?", abort=True)
        config_path.write_text(content)
        click.echo(f"Environment '{name}' saved.")
    else:
        click.echo("No active environment to save.")

@cli.command()
@click.argument('name', type=EnvNameCompletionType())
def use(name):
    """Activate an environment by replacing the .env file."""
    config_path = CHATTOOL_ENV_DIR / f'{name}.env'
    if config_path.exists():
        content = config_path.read_text()
        CHATTOOL_ENV_FILE.write_text(content)
        click.echo(f"Environment '{name}' activated.")
    else:
        click.echo(f"Environment '{name}' not found.")

@cli.command()
@click.option('-a', '--api-key', help='API key')
@click.option('-b', '--base-url', help='Base URL of the API (without suffix `/v1`)')
@click.option('--api-base', help='Base URL of the API (with suffix `/v1`)')
@click.option('-m', '--model', help='Model name')
@click.argument('name', required=False, type=EnvNameCompletionType())
def config(name, api_key, base_url, api_base, model):
    """Update default .env values."""
    if not any([api_key, base_url, api_base, model]):
        click.echo("No updates made. Provide at least one option to update.")
        return
    config_path = CHATTOOL_ENV_DIR / f'{name}.env' if name else CHATTOOL_ENV_FILE
    if not config_path.exists():
        click.echo(f"Environment '{config_path}' not found.\n" +\
                   "Use `askenv new` to create a new environment." )
        return
    write_config(config_path, api_key, model, base_url, api_base)
    click.echo(f"Environment {config_path} updated.")

if __name__ == '__main__':
    cli()
