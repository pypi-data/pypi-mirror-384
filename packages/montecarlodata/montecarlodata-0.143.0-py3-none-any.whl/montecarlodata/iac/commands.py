import click
import click_config_file

from montecarlodata import settings
from montecarlodata.common import create_mc_client
from montecarlodata.errors import complain_and_abort
from montecarlodata.iac.mc_config_service import MonteCarloConfigService
from montecarlodata.monitors.monitor_service import MonitorService


@click.group(help="Manage monitors.")
def monitors():
    """
    Group for any monitor related subcommands
    """
    pass


@monitors.command(help="Compile monitor configuration.")
@click.option(
    "--project-dir",
    required=False,
    type=click.Path(exists=True),
    help="Base directory of MC project (where montecarlo.yml is located). "
    "By default, this is set to the current working directory",
)
@click.option(
    "--namespace",
    required=False,
    help="Namespace of monitors configuration. This value will be ignored if we find a"
    " namespace in montecarlo.yml",
)
@click.option(
    "--dbt-manifest",
    required=False,
    type=click.Path(exists=True),
    help="Path to dbt manifest used for resolving dbt ref() in monitor config",
)
@click.pass_obj
def compile(ctx, project_dir, namespace, dbt_manifest):
    MonteCarloConfigService(
        config=ctx["config"],
        pycarlo_client=create_mc_client(ctx),
        command_name="monitors compile",
        project_dir=project_dir,
        dbt_manifest_path=dbt_manifest,
    ).compile(namespace)


@monitors.command(help="Compile and apply monitor configuration.")
@click.option(
    "--project-dir",
    required=False,
    type=click.Path(exists=True),
    help="Base directory of MC project (where montecarlo.yml is located). "
    "By default, this is set to the current working directory",
)
@click.option(
    "--namespace",
    required=False,
    help="Namespace of monitors configuration. This value will be ignored if we find a"
    " namespace in montecarlo.yml",
)
@click.option(
    "--dry-run",
    required=False,
    default=False,
    show_default=True,
    is_flag=True,
    help="Dry run (just shows planned changes but doesn't apply them.)",
)
@click.option(
    "--dbt-manifest",
    required=False,
    type=click.Path(exists=True),
    help="Path to dbt manifest used for resolving dbt ref() in monitor config",
)
@click.option(
    "--auto-yes",
    is_flag=True,
    help="Skip any interactive approval.",
    default=False,
    show_default=True,
)
@click.option(
    "--create-non-ingested-tables",
    required=False,
    default=False,
    show_default=True,
    is_flag=True,
    help="force create non-ingested tables if they don't exist.",
)
@click.pass_obj
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def apply(
    ctx,
    project_dir,
    namespace,
    dry_run,
    dbt_manifest,
    auto_yes,
    create_non_ingested_tables,
):
    MonteCarloConfigService(
        config=ctx["config"],
        pycarlo_client=create_mc_client(ctx),
        command_name="monitors apply",
        project_dir=project_dir,
        dbt_manifest_path=dbt_manifest,
    ).apply(
        namespace,
        dry_run=dry_run,
        skip_confirmation=auto_yes,
        create_non_ingested_tables=create_non_ingested_tables,
    )


@monitors.command(help="Delete monitor configuration.")
@click.option(
    "--project-dir",
    required=False,
    type=click.Path(exists=True),
    help="Base directory of MC project (where montecarlo.yml is located). "
    "By default, this is set to the current working directory",
)
@click.option("--namespace", required=True, help="Namespace of monitors configuration.")
@click.option(
    "--dry-run",
    required=False,
    default=False,
    show_default=True,
    is_flag=True,
    help="Dry run (just shows planned changes but doesn't apply them.",
)
@click.pass_obj
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def delete(ctx, project_dir, namespace, dry_run):
    MonteCarloConfigService(
        config=ctx["config"],
        pycarlo_client=create_mc_client(ctx),
        command_name="monitors delete",
        project_dir=project_dir,
    ).delete(namespace, dry_run=dry_run)


@monitors.command(name="list", help="List monitors ordered by update recency.")
@click.option(
    "--limit",
    required=False,
    default=100,
    type=click.INT,
    show_default=True,
    help="Max number of monitors to list.",
)
@click.option(
    "--monitor-type",
    required=False,
    type=click.Choice(MonitorService.MONITOR_TYPES, case_sensitive=False),
    help="List monitors with monitor_type",
)
@click.option("--namespace", required=False, help="List only monitors in this namespace")
@click.pass_obj
def list_monitors(ctx, monitor_type, limit, namespace):
    monitor_types = None
    namespaces = [namespace] if namespace else None
    if monitor_type:
        if monitor_type == MonitorService.PSEUDO_MONITOR_TYPE_CB_COMPATIBLE:
            monitor_type = MonitorService.MONITOR_TYPE_CUSTOM_SQL
        monitor_types = [monitor_type]
    MonitorService(
        client=create_mc_client(ctx),
        command_name="monitors list_monitors",
    ).list_monitors(limit, namespaces, monitor_types)


@monitors.command(name="namespaces", help="List all namespaces.")
@click.option(
    "--limit",
    required=False,
    default=100,
    type=click.INT,
    show_default=True,
    help="Max number of namespaces to list.",
)
@click.pass_obj
def list_namespaces(ctx, limit):
    MonteCarloConfigService(
        config=ctx["config"],
        pycarlo_client=create_mc_client(ctx),
        command_name="monitors list_namespaces",
    ).list_namespaces(limit)


@monitors.command(help="Generate MC monitor config YAML from dbt tests.")
@click.option(
    "--output-path",
    required=True,
    type=click.Path(),
    help="Path for MC monitor config output YAML",
)
@click.option(
    "--dbt-manifest",
    required=True,
    type=click.Path(exists=True),
    help="Path to dbt manifest containing tests to generate MC monitor config for",
)
@click.option(
    "--test-type",
    required=False,
    multiple=True,
    help="Filter for types of dbt tests to convert. Can pass multiple. Defaults to all."
    " Pass SINGULAR to filter to singular tests without a shared type.",
)
@click.option(
    "--label",
    required=False,
    multiple=True,
    help="Label to apply to all generated MC monitors. Can pass multiple.",
)
@click.pass_obj
def generate_from_dbt_tests(ctx, dbt_manifest, output_path, test_type, label):
    MonteCarloConfigService(
        config=ctx["config"],
        pycarlo_client=create_mc_client(ctx),
        command_name="monitors generate_from_dbt_tests",
        dbt_manifest_path=dbt_manifest,
    ).generate_from_dbt_tests(output_path, test_type, label)


@monitors.command(
    help="Convert monitors from UI to monitors configuration, "
    "exporting the monitors as YAML in the process."
)
@click.option(
    "--namespace",
    required=True,
    type=click.STRING,
    help="Namespace for the exported monitors.",
)
@click.option(
    "--project-dir",
    required=True,
    type=click.Path(),
    help="Path to a directory to export a MC monitor config project to.",
)
@click.option(
    "--monitor-uuids",
    required=False,
    type=click.STRING,
    help="Comma separated list of monitor UUIDs to export.",
)
@click.option(
    "--monitors-file",
    required=False,
    type=click.STRING,
    help="File with monitor UUIDs to convert. One line per monitor.",
)
@click.option(
    "--dry-run",
    required=False,
    default=False,
    show_default=True,
    is_flag=True,
    help="Dry run (only export the monitors as monitors as code, "
    "but do not convert existing ones).",
)
@click.pass_obj
def convert_to_mac(ctx, namespace, dry_run, project_dir, monitor_uuids, monitors_file):
    MonteCarloConfigService(
        config=ctx["config"],
        pycarlo_client=create_mc_client(ctx),
        command_name="monitors convert_to_mac",
    ).convert_to_mac(
        namespace,
        project_dir,
        monitor_uuids.split(",") if monitor_uuids else None,
        monitors_file,
        all_monitors=not monitors_file and not monitor_uuids,
        dry_run=dry_run,
    )


@monitors.command(help="Convert monitors from a monitors as code namespace to UI monitors.")
@click.option(
    "--namespace",
    required=True,
    type=click.STRING,
    help="Namespace to convert.",
)
@click.option(
    "--dry-run",
    required=False,
    default=False,
    show_default=True,
    is_flag=True,
    help="Dry run (just shows planned changes but doesn't apply them.)",
)
@click.pass_obj
def convert_to_ui(ctx, namespace, dry_run):
    MonteCarloConfigService(
        config=ctx["config"],
        pycarlo_client=create_mc_client(ctx),
        command_name="monitors convert_to_ui",
    ).convert_to_ui(namespace, dry_run=dry_run)


@monitors.command(
    help="Export monitors in a monitor as code namespace upgraded to the latest "
    "version of monitors of monitors as code. Will only export monitors that "
    "can be upgraded."
)
@click.option(
    "--namespace",
    required=True,
    type=click.STRING,
    help="Namespace to export as latest.",
)
@click.option(
    "--monitors-file",
    required=False,
    type=click.STRING,
    help="File with monitor UUIDs to export as latest. One line per monitor.",
)
@click.pass_obj
def export_as_latest(ctx, namespace, monitors_file):
    MonteCarloConfigService(
        config=ctx["config"],
        pycarlo_client=create_mc_client(ctx),
        command_name="monitors export_as_latest",
    ).export_as_latest(namespace, monitors_file=monitors_file)


@monitors.command(help="Export monitors as monitor as code.")
@click.option(
    "--monitor-uuids",
    required=False,
    type=click.STRING,
    help="Comma separated list of monitor UUIDs to export.",
)
@click.option(
    "--monitors-file",
    required=False,
    type=click.STRING,
    help="File with monitor UUIDs to export. One line per monitor.",
)
@click.option(
    "--export-name",
    required=False,
    type=click.BOOL,
    default=True,
    show_default=True,
    help="Export the monitor name in the output.",
)
@click.pass_obj
def export(ctx, monitor_uuids, monitors_file, export_name):
    if monitors_file and monitor_uuids:
        complain_and_abort("Cannot use both --monitor-uuids and --monitors-file")
    if not monitor_uuids and not monitors_file:
        complain_and_abort("You must provide either --monitor-uuids or --monitors-file")
    MonteCarloConfigService(
        config=ctx["config"],
        pycarlo_client=create_mc_client(ctx),
        command_name="monitors export",
    ).export(
        monitor_uuids.split(",") if monitor_uuids else None,
        monitors_file=monitors_file,
        export_name=export_name,
    )


@monitors.command(help="Get the monitors configuration for a given namespace.")
@click.option(
    "--namespace",
    required=True,
    type=click.STRING,
    help="Namespace for the exported monitors.",
)
@click.option(
    "--project-dir",
    required=True,
    type=click.Path(),
    help="Path to a directory to export a the template to.",
)
@click.pass_obj
def get_template(ctx, namespace, project_dir):
    MonteCarloConfigService(
        config=ctx["config"],
        pycarlo_client=create_mc_client(ctx),
        command_name="monitors get_template",
    ).get_template(namespace, project_dir)


@monitors.command(
    help=(
        "Export monitors as code configuration for a given namespace. "
        "Only generates configuration for system migrated Dimension Tracking monitors."
    )
)
@click.option(
    "--project-dir",
    required=False,
    type=click.Path(exists=True),
    help=(
        "Base directory of MC project (where montecarlo.yml is located). "
        "By default, this is set to the current working directory"
    ),
)
@click.option(
    "--namespace",
    required=False,
    help=(
        "Namespace of monitors to be exported. "
        "This value will be ignored if we find a namespace in montecarlo.yml"
    ),
)
@click.pass_obj
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def export_migrated_dt(ctx, project_dir, namespace):
    MonteCarloConfigService(
        config=ctx["config"],
        pycarlo_client=create_mc_client(ctx),
        command_name="monitors export_migrated_dt",
        project_dir=project_dir,
    ).export_migrated_dt(namespace)
