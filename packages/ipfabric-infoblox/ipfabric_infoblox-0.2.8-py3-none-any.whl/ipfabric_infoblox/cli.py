import json
import os
from datetime import datetime
from typing import Annotated
import re

import typer
import yaml
from ipfabric import IPFClient
from pytz import UTC
from rich.console import Console
from invoke import run

from ipfabric_infoblox.config import Configuration
from ipfabric_infoblox.infoblox import NetworkValidation, ManagedIPValidation, Infoblox
from ipfabric_infoblox.sync import Sync

app = typer.Typer()
console = Console()

DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILE = "diff.csv"
GREEN, RED = "bold green", "bold red"


def print_error_and_abort(message: str):
    console.print(f"Error: {message}", style=RED)
    raise typer.Abort()


def load_yaml_config(config_file) -> dict:
    try:
        config_data = yaml.safe_load(config_file)
        return config_data
    except yaml.YAMLError as exc:
        typer.echo(f"Error parsing YAML file: {exc}", err=True)
        raise typer.Exit(code=1)


def common_logic(config_file, logging: bool, ts: str):
    console.print(
        f"Comparing networks in [link={os.environ.get('IPF_URL')}]IP Fabric[/link] and [link={os.environ.get('IB_HOST')}]Infoblox[/link]",
        style=GREEN,
    )

    config = Configuration(**load_yaml_config(config_file))
    sync = Sync(config=config)
    ib = Infoblox(config=config)

    for view in config.network_views:
        if view.name not in ib.views:
            raise ValueError(f"View {view.name} does not exists in IB.")
    for network in sync.network_sync.networks.nets_by_view.get(None, []):
        console.print(f"Error: Network {network.network} failed to validate.", style=RED)

    net_validation = NetworkValidation(
        view_configs=config.network_views,
        ib=ib,
        managed_networks=sync.network_sync.networks,
    )

    managed_ip_validation = ManagedIPValidation(
        validated_ipf_networks=net_validation.validated_ipf_networks(),
        ips=sync.ip_sync,
        view_configs=config.network_views,
    )

    if logging:
        console.print(f"Logging directory set to '{DEFAULT_LOG_DIR}'.", style=GREEN)
        if not os.path.exists(DEFAULT_LOG_DIR):
            os.makedirs(DEFAULT_LOG_DIR)
        net_validation.export_logs_to_csv(os.path.join(DEFAULT_LOG_DIR, f"diff_{ts}.csv"))
        with open(os.path.join(DEFAULT_LOG_DIR, f"diff_{ts}.json"), mode="w") as f:
            json.dump([_.model_dump() for _ in net_validation.logs], f, indent=2)
        console.print(
            f"Logs exported to '{os.path.join(DEFAULT_LOG_DIR, f'diff_{ts}.csv|json')}'.",
            style=GREEN,
        )

    return ib, net_validation, managed_ip_validation


def sync_networks(net_validation, ib, ts: str, logging: bool = False):
    if net_validation.create_networks:
        console.print("Creating Infoblox Network CSV import file.", style=GREEN)
        csv_data = net_validation.create_csv()
        status, result = ib.csv_upload(net_validation.create_csv())
        if not status:
            console.print(f"CSV Import Error Encountered: {result}", style=RED)
        else:
            console.print(
                f"Lines Processed: {result['lines_processed']}\nLines Warning: {result['lines_warning']}"
                f"\nLines Failed: {result['lines_failed']}",
                style=GREEN,
            )
        if logging:
            with open(os.path.join(DEFAULT_LOG_DIR, f"network_import_{ts}.csv"), mode="w") as f:
                f.write(csv_data.getvalue())
            console.print(
                f"Network CSV import logged to '{os.path.join(DEFAULT_LOG_DIR, f'network_import_{ts}.csv')}'.",
                style=GREEN,
            )
        return {"networks": result}
    else:
        console.print("No networks to sync", style=RED)
    return {"networks": None}


def sync_discovery(managed_ip_validation, ib, ts: str, logging: bool = False) -> dict:
    sync_log = dict()
    if managed_ip_validation.validated_ips:
        console.print("Creating Infoblox IP Discovery CSV import files.", style=GREEN)
        discovery_csvs = managed_ip_validation.create_discovery_csvs()
        discovery_log = ""

        for view, ips in discovery_csvs.items():
            console.print(f"Uploading Infoblox IP Discovery Data for Network View: {view}.", style=GREEN)
            status, result = ib.csv_discovery_upload(ips, view)
            sync_log[view] = result
            discovery_log += f"### View: {view}\n{ips.getvalue()}"
            if not status:
                console.print(
                    f"Discovery Import Error Encountered for view '{view}': {result}",
                    style=RED,
                )
            else:
                console.print(result["status"], style=GREEN)

        if logging:
            with open(os.path.join(DEFAULT_LOG_DIR, f"discovery_import_{ts}.csv"), mode="w") as f:
                f.write(discovery_log)
            console.print(
                f"Discovery CSV import files exported to '{os.path.join(DEFAULT_LOG_DIR, f'discovery_import_{ts}.csv')}'.",
                style=GREEN,
            )
    else:
        console.print("No IPs to sync", style="bold red")
    return {"discovery": sync_log}


def validate_and_sync_infoblox(config, logging: bool = False, sync: bool = False):
    """
    Validate and optionally synchronize networks and managed IPs with Infoblox.

    This function performs network and IP validation using the provided configuration. It can optionally
    synchronize the validated data with Infoblox by generating and uploading CSV files for networks and
    managed IP discovery.

    Args:
        config: The configuration object containing necessary parameters for validation.
        logging (bool): If True, logging will be enabled during the validation process. Default is False.
        sync (bool): If True, synchronizes validated networks and IPs with Infoblox. Default is False.

    Returns:
        tuple: A tuple containing the network validation and managed IP validation results:
            - net_validation: The result of network validation, including details of networks to be created.
            - managed_ip_validation: The result of managed IP validation, including discovered and validated IPs.
            - sync_log: The result of the synchronization process, including the status of the networks and IPs.

    Side Effects:
        - Prints messages to the console indicating the status of validation and synchronization.

    Notes:
        - If `perform_sync` is False, the function will only perform validation and return the results.

    Examples:
        >>> validate_and_sync_infoblox(config, enable_logging=True, perform_sync=True)
        Creating Infoblox Network CSV import CSV file.
        Creating Infoblox IP Discovery CSV import CSV file.
    """
    ts = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H%M%SZ")

    ib, net_validation, managed_ip_validation = common_logic(config, logging, ts)
    if not sync:
        return net_validation, managed_ip_validation
    sync_log = sync_networks(net_validation, ib, ts, logging)
    sync_log.update(sync_discovery(managed_ip_validation, ib, ts, logging))

    if logging:
        with open(os.path.join(DEFAULT_LOG_DIR, f"sync_{ts}.json"), mode="w") as f:
            json.dump(sync_log, f, indent=2)
        console.print(
            f"Import logs exported to '{os.path.join(DEFAULT_LOG_DIR, f'sync_{ts}.log')}'.",
            style=GREEN,
        )

    return net_validation, managed_ip_validation, sync_log


@app.command(name="diff")
def diff_cmd(
    config: Annotated[
        typer.FileText,
        typer.Option(help="YAML file with configuration default = config.yml"),
    ] = "config.yml",
    logging: Annotated[
        bool, typer.Option(help="Creates a Log file with the results of the diff/sync process. Default = False")
    ] = False,
):
    """Diff command to compare configurations."""
    validate_and_sync_infoblox(config, logging)


@app.command(name="sync")
def sync_cmd(
    config: Annotated[
        typer.FileText, typer.Option(help="YAML file with configuration default = config.yml")
    ] = "config.yml",
    logging: Annotated[bool, typer.Option(help="Say hi formally.")] = False,
):
    """Sync command to compare configurations."""
    validate_and_sync_infoblox(config, logging, sync=True)


@app.command(name="install-extension")
def install_extension():
    """Install the extension. Using IP Fabrics Extensions API."""
    try:
        ipf = IPFClient()
        try:
            ipf.extensions.extension_by_name("ipfabric_infoblox")
            console.print("Extension already installed", style=GREEN)
        except ValueError:
            console.print("Installing extension", style=GREEN)
            ipf.extensions.register_from_git_url(
                git_url="https://gitlab.com/ip-fabric/integrations/ipfabric-infoblox",
                name="ipfabric_infoblox",
                slug="ipfabric-infoblox",
                description="Infoblox extension for IP Fabric",
            )
            console.print("Extension installed", style=GREEN)
        ipf_url = re.sub(r"/api/v\d+\.\d+/?$", "/", str(ipf.base_url))
        console.print(f"Extension is available in IP Fabric @ {ipf_url}extensions-apps/ipfabric-infoblox", style=GREEN)
    except Exception as e:
        print_error_and_abort(f"Error installing extension: {e}")
        raise typer.Exit(code=1)


@app.command(name="streamlit")
def streamlit_cmd():
    """Streamlit command to run the streamlit app."""
    command_args = [
        "poetry",
        "run",
        "streamlit",
        "run",
        "ipfabric_infoblox/frontend/frontend.py",
        "--theme.primaryColor=#8C989B",
        "--theme.backgroundColor=#222D32",
        "--theme.secondaryBackgroundColor=#264183",
        "--theme.textColor=#F6F6F6",
        "--theme.font=monospace",
    ]
    run(str(" ").join(command_args))


if __name__ == "__main__":
    app()
