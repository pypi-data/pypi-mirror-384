from typing import List, Optional

import click
import click_config_file

import montecarlodata.settings as settings
from montecarlodata.common import create_mc_client
from montecarlodata.common.commands import DISAMBIGUATE_DC_OPTIONS
from montecarlodata.common.resources import CloudResourceService
from montecarlodata.integrations.configure.bi.bi import BiService
from montecarlodata.integrations.info.status import OnboardingStatusService
from montecarlodata.integrations.keys import IntegrationKeyScope, IntegrationKeyService
from montecarlodata.integrations.onboarding.bi.reports import ReportsOnboardingService
from montecarlodata.integrations.onboarding.data_lake.databricks import (
    DatabricksOnboardingService,
)
from montecarlodata.integrations.onboarding.data_lake.events import (
    EventsOnboardingService,
)
from montecarlodata.integrations.onboarding.data_lake.glue_athena import (
    GlueAthenaOnboardingService,
)
from montecarlodata.integrations.onboarding.data_lake.hive import HiveOnboardingService
from montecarlodata.integrations.onboarding.data_lake.presto import (
    PrestoOnboardingService,
)
from montecarlodata.integrations.onboarding.data_lake.spark import (
    SPARK_BINARY_MODE_CONFIG_TYPE,
    SPARK_DATABRICKS_CONFIG_TYPE,
    SPARK_HTTP_MODE_CONFIG_TYPE,
    SparkOnboardingService,
)
from montecarlodata.integrations.onboarding.etl.adf import (
    AzureDataFactoryOnboardingService,
)
from montecarlodata.integrations.onboarding.etl.airflow import AirflowOnboardingService
from montecarlodata.integrations.onboarding.etl.dbt_cloud import (
    DbtCloudOnboardingService,
)
from montecarlodata.integrations.onboarding.etl.fivetran import (
    FivetranOnboardingService,
)
from montecarlodata.integrations.onboarding.etl.informatica import InformaticaOnboardingService
from montecarlodata.integrations.onboarding.fields import (
    AZURE_DEDICATED_SQL_POOL_TYPE,
    AZURE_SQL_DATABASE_TYPE,
    CLICKHOUSE_DATABASE_TYPE,
    CONNECTION_TO_WAREHOUSE_TYPE_MAP,
    DATABRICKS_METASTORE_SQL_WAREHOUSE_CONNECTION_TYPE,
    DATABRICKS_SQL_WAREHOUSE_CONNECTION_TYPE,
    DREMIO_DATABASE_TYPE,
    GLUE_CONNECTION_TYPE,
    GQL_TO_FRIENDLY_CONNECTION_MAP,
    HIVE_MYSQL_CONNECTION_TYPE,
    HIVE_S3_CONNECTION_TYPE,
    MARIADB_DB_TYPE,
    MOTHERDUCK_DATABASE_TYPE,
    MYSQL_DB_TYPE,
    ORACLE_DB_TYPE,
    POSTGRES_DB_TYPE,
    PRESTO_S3_CONNECTION_TYPE,
    SALESFORCE_CRM_DATABASE_TYPE,
    SALESFORCE_DATA_CLOUD_DATABASE_TYPE,
    SAP_HANA_DATABASE_TYPE,
    SECRETS_MANAGER_CREDENTIAL_MECHANISM,
    SELF_HOSTING_MECHANISMS,
    SQL_SERVER_DB_TYPE,
    TERADATA_DB_TYPE,
)
from montecarlodata.integrations.onboarding.operations.connection_ops import (
    ConnectionOperationsService,
)
from montecarlodata.integrations.onboarding.self_hosted_credentials import (
    SelfHostedCredentialOnboardingService,
)
from montecarlodata.integrations.onboarding.streaming.streamings import (
    StreamingOnboardingService,
)
from montecarlodata.integrations.onboarding.transactional import (
    TransactionalOnboardingService,
)
from montecarlodata.integrations.onboarding.vector import (
    VectorDbOnboardingService,
)
from montecarlodata.integrations.onboarding.warehouse.warehouses import (
    WarehouseOnboardingService,
)
from montecarlodata.tools import (
    AdvancedOptions,
    add_common_options,
    convert_empty_str_callback,
    convert_uuid_callback,
    validate_json_callback,
)

# Shared command verbiage
METADATA_VERBIAGE = "For metadata"
QL_VERBIAGE = "For query logs"
SQL_VERBIAGE = "For health queries"
EVENT_VERBIAGE = (
    "For tracking data freshness and volume at scale. "
    "Requires s3 notifications to be configured first"
)
REGION_VERBIAGE = "If not specified the region the collector is deployed in is used"
WAREHOUSE_VERBIAGE = "For metadata, query logs and metrics"
LIGHTWEIGHT_VERBIAGE = "For metadata, and custom SQL monitors"
BI_VERBIAGE = "For reports"
PASSWORD_VERBIAGE = f"If you prefer a prompt (with hidden input) enter {settings.SHOW_PROMPT_VALUE}"
RESOURCE_VERBIAGE = "This can be helpful if the resources are in different accounts"
CONNECTION_ID_VERBIAGE = "ID for the connection."


# Options shared across commands
def role_options(required: bool = True) -> List:
    return [
        click.option(
            "--role",
            help="Assumable role ARN to use for accessing AWS resources.",
            required=required,
        ),
        click.option(
            "--external-id",
            help="An external id, per assumable role conditions.",
            required=False,
        ),
    ]


# Name is used for the creation of a warehouse that will contain the connection.
def warehouse_create_option(required: bool = False, default: Optional[str] = None) -> List:
    return _warehouse_and_connection_name_option(
        help="Friendly name for the created integration (e.g. warehouse). Name must be unique.",
        required=required,
        default=default,
    )


# Name is used to identify an existing warehouse that will contain the connection.
def warehouse_select_option(required: bool = False, default: Optional[str] = None) -> List:
    return _warehouse_and_connection_name_option(
        help="Friendly name of the warehouse which the connection will belong to.",
        required=required,
        default=default,
    )


def _warehouse_and_connection_name_option(
    help: str, required: bool = False, default: Optional[str] = None
) -> List:
    return [
        click.option("--name", help=help, required=required, default=default),
        click.option("--connection-name", help="Friendly name for the connection.", required=False),
    ]


# Name is used to give a distinctive name to the etl connection.
def etl_select_option(required: bool = False, default: Optional[str] = None) -> List:
    return _etl_option(
        help="Friendly name for the etl connection.",
        required=required,
        default=default,
    )


def _etl_option(help: str, required: bool = False, default: Optional[str] = None) -> List:
    return [
        click.option("--name", help=help, required=required, default=default),
        click.option("--connection-name", help="Friendly name for the connection.", required=False),
    ]


def port_create_option(default_port: int) -> List:
    return [
        click.option(
            "--port",
            help="HTTP port.",
            default=default_port,
            type=click.INT,
            show_default=True,
        )
    ]


WAREHOUSE_OPTIONAL_CREATE_OPTIONS = [
    click.option(
        "--create-warehouse",
        help="Create a new warehouse with this connection",
        type=click.BOOL,
        default=True,
        required=False,
    )
]
S3_OPTIONS = [
    click.option("--bucket", help="S3 Bucket where query logs are contained.", required=True),
    click.option("--prefix", help="Path to query logs.", required=True),
    *role_options(required=False),
]

BASIC_DATABASE_OPTIONS = [
    click.option("--host", help="Hostname.", required=True),
    click.option("--user", help="Username with access to the database.", required=True),
    click.option(
        "--password",
        help=f"User's password. {PASSWORD_VERBIAGE}.",
        required=True,
        cls=AdvancedOptions,
        prompt_if_requested=True,
    ),
]

DATABASE_OPTIONS = [
    *BASIC_DATABASE_OPTIONS,
    click.option("--database", help="Name of database/site.", required=True),
]

CONNECTION_OPTIONS = [
    click.option(
        "--connection-id",
        help=CONNECTION_ID_VERBIAGE,
        required=True,
        type=click.UUID,
        callback=convert_uuid_callback,
    )
]

SSL_OPTIONS = [
    click.option(
        "--ssl-ca",
        help="Path to the file that contains a PEM-formatted CA certificate.",
        required=False,
        type=click.Path(dir_okay=False, exists=True),
        cls=AdvancedOptions,
        mutually_exclusive_options=["ssl_disabled"],
    ),
    click.option(
        "--ssl-cert",
        help="Path to the file that contains a PEM-formatted client certificate.",
        required=False,
        type=click.Path(dir_okay=False, exists=True),
        cls=AdvancedOptions,
        mutually_exclusive_options=["ssl_disabled"],
    ),
    click.option(
        "--ssl-key",
        help="Path to the file that contains a PEM-formatted private key for the "
        "client certificate.",
        required=False,
        type=click.Path(dir_okay=False, exists=True),
        cls=AdvancedOptions,
        required_with_options=["ssl_cert"],
        mutually_exclusive_options=["ssl_disabled"],
    ),
    click.option(
        "--ssl-disabled",
        help="A boolean value that disables usage of TLS.",
        required=False,
        type=click.BOOL,
        cls=AdvancedOptions,
        mutually_exclusive_options=["ssl_ca", "ssl_cert", "ssl_key"],
    ),
    click.option(
        "--ssl-key-password",
        help=f"The password for the client certificate private key. {PASSWORD_VERBIAGE}.",
        required=False,
        cls=AdvancedOptions,
        prompt_if_requested=True,
        required_with_options=["ssl_cert"],
    ),
    click.option(
        "--ssl-verify-cert",
        help="Set to true to check the server certificate's validity.",
        required=False,
        type=click.BOOL,
        cls=AdvancedOptions,
        required_with_options=["ssl_cert"],
    ),
    click.option(
        "--ssl-verify-identity",
        help="Set to true to check the server's identity.",
        required=False,
        type=click.BOOL,
        cls=AdvancedOptions,
        required_with_options=["ssl_ca"],
    ),
    click.option(
        "--skip-cert-verification",
        help="Skip SSL certificate verification.",
        required=False,
        is_flag=True,
        cls=AdvancedOptions,
        mutually_exclusive_options=["ssl_verify_cert", "ssl_verify_identity"],
    ),
]

VALIDATION_OPTIONS = [
    click.option(
        "--skip-validation",
        is_flag=True,
        help="Skip all connection tests.",
        cls=AdvancedOptions,
        mutually_exclusive_options=["validate_only"],
    ),
    click.option(
        "--validate-only",
        is_flag=True,
        help="Run connection tests without adding.",
        cls=AdvancedOptions,
        mutually_exclusive_options=["skip_validation"],
    ),
    click.option(
        "--auto-yes",
        is_flag=True,
        help="Skip any interactive approval.",
        default=False,
        show_default=True,
    ),
]

ONBOARDING_CONFIGURATION_OPTIONS = [*DISAMBIGUATE_DC_OPTIONS, *VALIDATION_OPTIONS]

UPDATE_VALIDATION_OPTIONS = [*VALIDATION_OPTIONS, *CONNECTION_OPTIONS]

NETWORK_OPTIONS = [
    click.option(
        "--test-network-only",
        "skip_permission_tests",
        is_flag=True,
        default=False,
        show_default=True,
        cls=AdvancedOptions,
        mutually_exclusive_options=["skip_validation"],
        help="Skip any permission tests. Only validates network connection between the "
        "collector and resource can be established.",
    )
]

BI_OPTIONS = [
    click.option(
        "--verify-ssl/--no-verify-ssl",
        "verify_ssl",
        required=False,
        default=True,
        show_default=True,
        help="Whether to verify the SSL connection (uncheck for self-signed certs).",
    )
]

BASE_DATABRICKS_OPTIONS = [
    click.option("--databricks-workspace-url", help="Databricks workspace URL.", required=True),
    click.option(
        "--databricks-token",
        help=f"Databricks access token. {PASSWORD_VERBIAGE}.",
        required=False,
        cls=AdvancedOptions,
        prompt_if_requested=True,
    ),
]

DATABRICKS_OPTIONS = [
    *BASE_DATABRICKS_OPTIONS,
    click.option("--databricks-workspace-id", help="Databricks workspace ID.", required=True),
    click.option("--databricks-cluster-id", help="Databricks cluster ID.", required=True),
]

DATABRICKS_SQL_WAREHOUSE_OPTIONS = [
    *BASE_DATABRICKS_OPTIONS,
    click.option("--databricks-warehouse-id", help="Databricks warehouse ID.", required=True),
    click.option(
        "--databricks-client-id",
        help="Databricks OAuth Client ID.",
        required=False,
        cls=AdvancedOptions,
        mutually_exclusive_options=["databricks_token"],
        required_with_options=["databricks_client_secret"],
    ),
    click.option(
        "--databricks-client-secret",
        help=f"Databricks OAuth Client Secret. {PASSWORD_VERBIAGE}.",
        required=False,
        cls=AdvancedOptions,
        prompt_if_requested=True,
        mutually_exclusive_options=["databricks_token"],
        required_with_options=["databricks_client_id"],
        at_least_one_set=["databricks_client_id", "databricks_client_secret", "databricks_token"],
    ),
    click.option(
        "--azure-tenant-id",
        help="Azure Tenant ID, needed when using an Entra-ID managed service principal.",
        required=False,
        cls=AdvancedOptions,
        prompt_if_requested=True,
        mutually_exclusive_options=["databricks_token"],
        required_with_options=["azure_workspace_resource_id"],
        at_least_one_set=["databricks_client_id", "databricks_client_secret", "databricks_token"],
    ),
    click.option(
        "--azure-workspace-resource-id",
        help="Azure Workspace Resource, needed when using an Entra-ID managed service principal.",
        required=False,
        cls=AdvancedOptions,
        prompt_if_requested=True,
        mutually_exclusive_options=["databricks_token"],
        required_with_options=["azure_tenant_id"],
        at_least_one_set=["databricks_client_id", "databricks_client_secret", "databricks_token"],
    ),
]

TERADATA_OPTIONS = [
    click.option(
        "--sslmode",
        type=click.Choice(["ALLOW", "PREFER", "REQUIRE", "VERIFY_CA", "VERIFY_FULL"]),
        default=None,
        help="SSL mode for connections to Teradata.",
        required=False,
    ),
    click.option(
        "--logmech",
        type=click.Choice(["TD2", "BROWSER", "JWT", "LDAP", "KRB5", "TDNEGO"]),
        default=None,
        help="Logon mechanism for Teradata connection.",
        required=False,
    ),
    click.option(
        "--ssl-ca-directory",
        type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
        required=False,
        help="Path to directory of PEM files containing CA certs.",
        cls=AdvancedOptions,
        mutually_exclusive_options=["ssl-ca"],
    ),
    click.option(
        "--ssl-ca",
        type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
        required=False,
        help="Path to PEM file containing CA cert(s).",
        cls=AdvancedOptions,
        mutually_exclusive_options=["ssl-ca-directory"],
    ),
    click.option(
        "--ssl-disabled",
        help="A boolean value that disables usage of TLS.",
        required=False,
        type=click.BOOL,
        cls=AdvancedOptions,
    ),
]

S3_BUCKET_OPTIONS = [
    click.option(
        "--bucket",
        "bucket_name",
        required=False,
        help="Name of bucket to enable events for.",
    ),
    click.option(
        "--prefix",
        default=None,
        callback=convert_empty_str_callback,
        required=False,
        help="Limit the notifications to objects starting with a prefix (e.g. 'data/').",
    ),
    click.option(
        "--suffix",
        default=None,
        callback=convert_empty_str_callback,
        required=False,
        help="Limit notifications to objects ending with a suffix (e.g. '.csv').",
    ),
    click.option(
        "--topic-arn",
        default=None,
        callback=convert_empty_str_callback,
        required=False,
        help="Use an existing SNS topic (same region as the bucket). Creates a topic "
        "if one is not specified or "
        "if an MCD topic does not already exist in the region.",
    ),
    click.option(
        "--buckets-filename",
        required=False,
        help="Filename that contains bucket config to enable events for",
        cls=AdvancedOptions,
        mutually_exclusive_options=["bucket_name"],
    ),
]

EVENT_TYPE_OPTIONS = [
    click.option(
        "--event-type",
        required=True,
        default=CloudResourceService.MCD_EVENT_TYPE_MD,
        show_default=True,
        help="Type of event to setup.",
        type=click.Choice(
            list(CloudResourceService.MCD_EVENT_TYPE_FRIENDLY_TO_COLLECTOR_OUTPUT_MAP.keys()),
            case_sensitive=True,
        ),
    ),
]

RESOURCE_PROFILE_OPTIONS = [
    click.option(
        "--resource-aws-profile",
        "bucket_aws_profile",
        required=True,
        help="The AWS profile to use for operations on S3/SNS.",
    )
]

COLLECTOR_PROFILE_OPTIONS = [
    click.option(
        "--collector-aws-profile",
        required=True,
        help="The AWS profile to use for operations on SQS/Collector.",
    )
]

AUTO_YES_OPTIONS = [
    click.option(
        "--auto-yes",
        is_flag=True,
        help="Skip any interactive approval.",
        default=False,
        show_default=True,
    )
]

SELF_HOSTED_STREAMING_AUTH_OPTIONS = [
    click.option(
        "--auth-type",
        type=click.Choice(["NO_AUTH", "BASIC", "BEARER"]),
        required=True,
        help="The type of auth used to connect to the server",
    ),
    click.option(
        "--auth-token",
        required=False,
        help="The auth token used to connect to the server. Used for basic and bearer auth types.",
    ),
]

OAUTH_OPTIONS = [
    click.option(
        "--use-oauth",
        help="Use OAuth for Auth in this integration.",
        required=False,
        is_flag=True,
        default=False,
        show_default=True,
    ),
    click.option(
        "--oauth-client-id",
        help="OAuth Client ID.",
        required=False,
        cls=AdvancedOptions,
        required_with_options=["use_oauth"],
    ),
    click.option(
        "--oauth-client-secret",
        help=f"OAuth Client Secret. {PASSWORD_VERBIAGE}.",
        required=False,
        cls=AdvancedOptions,
        prompt_if_requested=True,
        required_with_options=["use_oauth"],
    ),
    click.option(
        "--oauth-access-token-endpoint",
        help="Endpoint used to acquire access tokens",
        required=False,
        cls=AdvancedOptions,
        required_with_options=["use_oauth"],
    ),
    click.option(
        "--oauth-grant-type",
        help="OAuth Grant type",
        type=click.Choice(["client_credentials", "password"], case_sensitive=True),
        required=False,
        cls=AdvancedOptions,
        required_with_options=["use_oauth"],
    ),
    click.option(
        "--oauth-scope",
        help="OAuth Scope",
        required=False,
        cls=AdvancedOptions,
    ),
    click.option(
        "--oauth-username",
        help="OAuth Username for oauth password grant flow",
        required=False,
        cls=AdvancedOptions,
    ),
    click.option(
        "--oauth-password",
        help=f"OAuth Password for oauth password grant flow. {PASSWORD_VERBIAGE}.",
        required=False,
        cls=AdvancedOptions,
        prompt_if_requested=True,
        required_with_options=["oauth_username"],
    ),
]


@click.group(help="Set up or manage an integration with Monte Carlo.")
def integrations():
    """
    Group for any integration related subcommands
    """
    pass


@integrations.command(help=f"Setup a Hive metastore integration (MySQL). {METADATA_VERBIAGE}.")
@click.pass_obj
@click.option("--port", help="HTTP port.", default=3306, type=click.INT, show_default=True)
@click.option(
    "--use-ssl",
    help="Use SSL to connect (using AWS RDS certificates).",
    required=False,
    is_flag=True,
    default=False,
    show_default=True,
)
@click.option(
    "--catalog",
    help="Presto catalog name. For using multiple hive clusters with Presto. "
    "Uses 'hive' if not specified.",
    required=False,
)
@add_common_options(warehouse_create_option())
@add_common_options(WAREHOUSE_OPTIONAL_CREATE_OPTIONS)
@add_common_options(DATABASE_OPTIONS)
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_hive_metastore(ctx, database, name, **kwargs):
    """
    Onboard a hive metastore connection (MySQL)
    """
    HiveOnboardingService(
        config=ctx["config"],
        command_name="integrations add_hive_metastore",
    ).onboard_hive_mysql(
        dbName=database,
        warehouseName=name,
        **kwargs,
    )


@integrations.command(help=f"Setup a Presto SQL integration. {SQL_VERBIAGE}.")
@click.pass_obj
@click.option("--host", help="Hostname.", required=True)
@click.option("--port", help="HTTP port.", default=8889, type=click.INT, show_default=True)
@click.option("--user", help="Username with access to catalog/schema.", required=False)
@click.option(
    "--password",
    help=f"User's password. {PASSWORD_VERBIAGE}",
    required=False,
    cls=AdvancedOptions,
    prompt_if_requested=True,
)
@click.option("--catalog", help="Mount point to access data source.", required=False)
@click.option("--schema", help="Schema to access.", required=False)
@click.option(
    "--http-scheme",
    help="Scheme for authentication.",
    type=click.Choice(["http", "https"], case_sensitive=True),
    required=True,
)
@click.option(
    "--cert-file",
    help="Local SSL certificate file to upload to collector.",
    required=False,
    type=click.Path(dir_okay=False, exists=True),
    cls=AdvancedOptions,
    mutually_exclusive_options=["cert_s3"],
)
@click.option(
    "--aws-profile",
    help="AWS profile to be used when uploading cert file.",
    required=False,
    cls=AdvancedOptions,
    required_with_options=["cert_file"],
)
@click.option(
    "--aws-region",
    help="AWS region to be used when uploading cert file.",
    required=False,
    cls=AdvancedOptions,
    required_with_options=["cert_file"],
)
@click.option(
    "--cert-s3",
    help="Object path (key) to a certificate already uploaded to the collector.",
    required=False,
    cls=AdvancedOptions,
    mutually_exclusive_options=["cert_file"],
)
@click.option(
    "--skip-cert-verification",
    help="Skip SSL certificate verification.",
    required=False,
    is_flag=True,
)
@add_common_options(warehouse_select_option())
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_presto(ctx, password, name, **kwargs):
    """
    Onboard a presto sql connection
    """
    if not password:
        password = None  # make explicitly null if not set. Prompts can't be None
    PrestoOnboardingService(
        config=ctx["config"],
        command_name="integrations add_presto",
    ).onboard_presto_sql(
        password=password,
        warehouseName=name,
        **kwargs,
    )


@integrations.command(help=f"Setup a Hive SQL integration. {SQL_VERBIAGE}.")
@click.pass_obj
@click.option("--host", help="Hostname.", required=True)
@click.option("--database", help="Name of database.", required=False)
@click.option("--port", help="HTTP port.", default=10000, type=click.INT, show_default=True)
@click.option("--user", help="Username with access to hive.", required=True)
@click.option(
    "--auth-mode",
    help="Hive authentication mode.",
    required=False,
    default="SASL",
    type=click.Choice(["SASL", "NOSASL"]),
    show_default=True,
)
@add_common_options(warehouse_select_option())
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_hive(ctx, user, name, **kwargs):
    HiveOnboardingService(
        config=ctx["config"],
        command_name="integrations add_hive",
    ).onboard_hive_sql(
        username=user,
        warehouseName=name,
        **kwargs,
    )


@integrations.command(help=f"Setup a Hive EMR logs integration (S3). {QL_VERBIAGE}.")
@click.pass_obj
@add_common_options(S3_OPTIONS)
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_hive_logs(ctx, role, **kwargs):  # DEPRECATED
    """
    Onboard a hive emr (s3) connection
    """
    HiveOnboardingService(
        config=ctx["config"],
        command_name="integrations add_hive_logs",
    ).onboard_hive_s3(assumable_role=role, **kwargs)


@integrations.command(help=f"Setup a Glue integration. {METADATA_VERBIAGE}.")
@click.pass_obj
@click.option("--region", help=f"Glue catalog region. {REGION_VERBIAGE}.", required=False)
@add_common_options(role_options())
@add_common_options(warehouse_create_option())
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
@click.option(
    "--ssl-ca",
    help="Path to file that contains CA cert bundle to use for SSL connection.",
    required=False,
    type=click.Path(dir_okay=False, exists=True),
    cls=AdvancedOptions,
)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_glue(ctx, role, region, name, **kwargs):
    """
    Onboard a glue connection
    """
    GlueAthenaOnboardingService(
        config=ctx["config"],
        command_name="integrations add_glue",
    ).onboard_glue(
        assumable_role=role,
        aws_region=region,
        warehouseName=name,
        **kwargs,
    )


@integrations.command(help="Setup an Athena integration. For query logs and health queries.")
@click.pass_obj
@click.option(
    "--catalog",
    help="Glue data catalog. If not specified the AwsDataCatalog is used.",
    required=False,
)
@click.option(
    "--workgroup",
    help="Workbook for running queries and retrieving logs. If not specified the primary is used.",
    required=False,
)
@click.option("--region", help=f"Athena cluster region. {REGION_VERBIAGE}.", required=False)
@add_common_options(warehouse_select_option())
@add_common_options(role_options())
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_athena(ctx, role, region, name, **kwargs):
    """
    Onboard an athena connection
    """
    GlueAthenaOnboardingService(
        config=ctx["config"],
        command_name="integrations add_athena",
    ).onboard_athena(
        assumable_role=role,
        aws_region=region,
        warehouseName=name,
        **kwargs,
    )


@integrations.command(help=f"Setup a thrift binary Spark integration. {SQL_VERBIAGE}.")
@click.pass_obj
@click.option("--host", help="Hostname.", required=True)
@click.option("--database", help="Name of database.", required=True)
@click.option("--port", help="Port.", default=10000, type=click.INT, show_default=True)
@click.option("--user", help="Username with access to spark.", required=True)
@click.option(
    "--password",
    help=f"User's password. {PASSWORD_VERBIAGE}.",
    required=True,
    cls=AdvancedOptions,
    prompt_if_requested=True,
)
@add_common_options(warehouse_select_option())
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_spark_binary_mode(ctx, user, name, **kwargs):
    """
    Onboard a spark connection, thrift binary mode
    """
    SparkOnboardingService(
        config=ctx["config"],
        command_name="integrations add_spark_binary_mode",
    ).onboard_spark(
        SPARK_BINARY_MODE_CONFIG_TYPE,
        username=user,
        warehouseName=name,
        **kwargs,
    )


@integrations.command(help=f"Setup a thrift HTTP Spark integration. {SQL_VERBIAGE}.")
@click.pass_obj
@click.option("--url", help="HTTP URL.", required=True)
@click.option("--user", help="Username with access to spark.", required=True)
@click.option(
    "--password",
    help=f"User's password. {PASSWORD_VERBIAGE}.",
    required=True,
    cls=AdvancedOptions,
    prompt_if_requested=True,
)
@add_common_options(warehouse_select_option())
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_spark_http_mode(ctx, user, name, **kwargs):
    """
    Onboard a spark connection, thrift http mode
    """
    SparkOnboardingService(
        config=ctx["config"],
        command_name="integrations add_spark_http_mode",
    ).onboard_spark(
        SPARK_HTTP_MODE_CONFIG_TYPE,
        username=user,
        warehouseName=name,
        **kwargs,
    )


@integrations.command(help=f"Setup a Spark integration for Databricks. {SQL_VERBIAGE}.")
@click.pass_obj
@add_common_options(DATABRICKS_OPTIONS)
@add_common_options(warehouse_select_option())
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_spark_databricks(ctx, name, **kwargs):
    """
    Onboard a spark connection, databricks
    """
    SparkOnboardingService(
        config=ctx["config"],
        command_name="integrations add_spark_databricks",
    ).onboard_spark(
        SPARK_DATABRICKS_CONFIG_TYPE,
        warehouseName=name,
        **kwargs,
    )


@integrations.command(help=f"Setup a Databricks SQL Warehouse integration. {SQL_VERBIAGE}")
@click.pass_obj
@add_common_options(DATABRICKS_SQL_WAREHOUSE_OPTIONS)
@add_common_options(warehouse_select_option())
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_databricks_sql_warehouse(ctx, name, **kwargs):
    """
    Onboard a databricks sql warehouse connection
    """
    DatabricksOnboardingService(
        config=ctx["config"],
        command_name="integrations add_databricks_sql_warehouse",
    ).onboard_databricks_sql_warehouse(
        connection_type=DATABRICKS_SQL_WAREHOUSE_CONNECTION_TYPE,
        warehouseName=name,
        **kwargs,
    )


@integrations.command(help="Setup a Databricks metastore sql warehouse integration. For metadata.")
@click.pass_obj
@add_common_options(warehouse_create_option())
@add_common_options(DATABRICKS_SQL_WAREHOUSE_OPTIONS)
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
@click.option("--databricks-workspace-id", help="Databricks workspace ID.", required=True)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_databricks_metastore_sql_warehouse(ctx, name, **kwargs):
    """
    Onboard a databricks metastore sql warehouse
    """
    DatabricksOnboardingService(
        config=ctx["config"],
        command_name="integrations add_databricks_metastore_sql_warehouse",
    ).onboard_databricks_sql_warehouse(
        connection_type=DATABRICKS_METASTORE_SQL_WAREHOUSE_CONNECTION_TYPE,
        warehouseName=name,
        **kwargs,
    )


@integrations.command(help="Create an integration key for a Databricks webhook")
@click.pass_obj
@click.option(
    "--integration-name",
    help="Name of associated Databricks metastore integration (required if you have more than one)",
)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def create_databricks_webhook_key(ctx, integration_name: Optional[str], **kwargs):
    DatabricksOnboardingService(
        config=ctx["config"],
        command_name="integrations create_databricks_webhook_key",
    ).create_webhook_key(
        warehouse_name=integration_name,
    )


@integrations.command(help=f"Setup a Redshift integration. {WAREHOUSE_VERBIAGE}.")
@click.pass_obj
@click.option("--port", help="HTTP port.", default=5439, type=click.INT, show_default=True)
@add_common_options(warehouse_create_option())
@add_common_options(DATABASE_OPTIONS)
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
@add_common_options(NETWORK_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_redshift(ctx, database, name, **kwargs):
    """
    Onboard a redshift connection
    """
    WarehouseOnboardingService(
        config=ctx["config"],
        command_name="integrations add_redshift",
    ).onboard_redshift(
        dbName=database,
        warehouseName=name,
        **kwargs,
    )


@integrations.command(help=f"Setup a Redshift consumer integration. {WAREHOUSE_VERBIAGE}.")
@click.pass_obj
@click.option("--port", help="HTTP port.", default=5439, type=click.INT, show_default=True)
@click.option(
    "--producer-resource-id",
    help="UUID of Producer warehouse",
    required=True,
    type=click.UUID,
    callback=convert_uuid_callback,
)
@click.option(
    "--connection-name", help="Friendly name for the consumer connection.", required=False
)
@add_common_options(DATABASE_OPTIONS)
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
@add_common_options(NETWORK_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_redshift_consumer_connection(ctx, database, **kwargs):
    """
    Onboard a redshift consumer connection
    """
    WarehouseOnboardingService(
        config=ctx["config"],
        command_name="integrations add_redshift_consumer",
    ).onboard_redshift_consumer(
        dbName=database,
        **kwargs,
    )


@integrations.command(help=f"Setup a Snowflake integration. {WAREHOUSE_VERBIAGE}.")
@click.pass_obj
@click.option(
    "--user",
    help="User with access to snowflake.",
    required=True,
    cls=AdvancedOptions,
)
@click.option("--account", help="Snowflake account name.", required=True)
@click.option("--warehouse", help="Name of the warehouse for the user.", required=True)
@click.option(
    "--private-key",
    help="User's private key file for key pair auth.",
    type=click.Path(exists=True),
    required=False,
    cls=AdvancedOptions,
    mutually_exclusive_options=[
        "use_oauth",
    ],
    at_least_one_set=["use_oauth", "private_key"],
)
@click.option(
    "--private-key-passphrase",
    help="User's private key passphrase. This argument is "
    f"only needed when the private key is encrypted. {PASSWORD_VERBIAGE}.",
    required=False,
    cls=AdvancedOptions,
    prompt_if_requested=True,
    required_with_options=["private_key"],
)
@add_common_options(OAUTH_OPTIONS)
@add_common_options(warehouse_create_option())
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_snowflake(ctx, name, **kwargs):
    """
    Onboard a snowflake connection
    """
    WarehouseOnboardingService(
        config=ctx["config"],
        command_name="integrations add_snowflake",
    ).onboard_snowflake(warehouseName=name, **kwargs)


@integrations.command(help=f"Setup a BigQuery integration. {WAREHOUSE_VERBIAGE}.")
@click.pass_obj
@click.option("--key-file", help="JSON Key file.", type=click.Path(exists=True), required=True)
@add_common_options(warehouse_create_option())
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_bigquery(ctx, key_file, name, **kwargs):
    """
    Onboard a BigQuery connection
    """
    WarehouseOnboardingService(
        config=ctx["config"],
        command_name="integrations add_bigquery",
    ).onboard_bq(ServiceFile=key_file, warehouseName=name, **kwargs)


@integrations.command(help="Setup an integration that uses self-hosted credentials.")
@click.pass_obj
@click.option(
    "--connection-type",
    help="Type of connection.",
    required=True,
    type=click.Choice(list(GQL_TO_FRIENDLY_CONNECTION_MAP.keys()), case_sensitive=False),
    cls=AdvancedOptions,
    values_with_required_options=CONNECTION_TO_WAREHOUSE_TYPE_MAP.keys(),
    required_options_for_values=["name"],
)
@click.option(
    "--mechanism",
    help="Credential self-hosting mechanism.",
    required=True,
    type=click.Choice(SELF_HOSTING_MECHANISMS, case_sensitive=False),
    default=SECRETS_MANAGER_CREDENTIAL_MECHANISM,
)
@click.option(
    "--key",
    help="Identifier for credentials within self-hosting mechanism.",
    required=True,
)
@click.option("--name", help="Friendly name for the warehouse.", required=False)
@add_common_options(role_options(required=False))
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_self_hosted_credentials(ctx, mechanism, key, role, name, **kwargs):
    """
    Onboard a connection with self-hosted credentials
    """
    SelfHostedCredentialOnboardingService(
        config=ctx["config"],
        command_name="integrations add_self_hosted_credentials",
    ).onboard_connection(
        self_hosting_mechanism=mechanism,
        self_hosting_key=key,
        assumable_role=role,
        warehouseName=name,
        **kwargs,
    )


@integrations.command(help="Setup an integration that uses self-hosted credentials (v2).")
@click.pass_obj
@click.option(
    "--connection-type",
    help="Connection type to test credentials for (e.g. 'snowflake').",
    required=True,
    type=click.Choice(list(GQL_TO_FRIENDLY_CONNECTION_MAP.keys()), case_sensitive=False),
)
@click.option(
    "--self-hosted-credentials-type",
    help="Self-hosted credentials type (e.g. 'env_var', 'aws_secrets_manager').",
    required=True,
    type=click.Choice(["ENV_VAR", "AWS_SECRETS_MANAGER"], case_sensitive=False),
    cls=AdvancedOptions,
)
@click.option(
    "--decryption-service-type",
    help="Optional type of service used to decrypt environment variable credentials (e.g. 'kms').",
    required=False,
    type=click.Choice(["KMS"], case_sensitive=False),
    cls=AdvancedOptions,
    required_with_options=["env_var_name"],
)
@click.option(
    "--env-var-name",
    help="Name of environment variable containing credentials. Must use prefix 'MCD_'.",
    required=False,
    cls=AdvancedOptions,
    required_with_options=["self_hosted_credentials_type"],
    mutually_exclusive_options=["aws_secret"],
)
@click.option(
    "--kms-key-id",
    help="Optional KMS key id for decrypting environment variable credentials.",
    required=False,
    cls=AdvancedOptions,
    required_with_options=["decryption_service_type"],
)
@click.option(
    "--aws-secret",
    help="ARN or name of AWS Secret Manager secret containing credentials.",
    required=False,
    cls=AdvancedOptions,
    required_with_options=["self_hosted_credentials_type"],
    mutually_exclusive_options=["env_var_name"],
)
@click.option(
    "--aws-region",
    help="Optional AWS region where secret manager secret is stored.",
    required=False,
)
@click.option(
    "--assumable-role",
    help="Optional ARN of AWS role to assume when accessing secret manager secret.",
    required=False,
)
@click.option(
    "--external-id",
    help="Optional external id for AWS role.",
    required=False,
    cls=AdvancedOptions,
    required_with_options=["assumable_role"],
)
@click.option("--name", help="Friendly name for the warehouse.", required=False)
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_self_hosted_credentials_v2(ctx, **kwargs):
    """
    Onboard a connection with self-hosted credentials (v2)
    """
    SelfHostedCredentialOnboardingService(
        config=ctx["config"],
        command_name="integrations add_self_hosted_credentials_v2",
    ).onboard_connection_v2(**kwargs)


@integrations.command(help="Setup an Airflow integration to receive events from Airflow callbacks.")
@click.pass_obj
@click.option("--host", help="Hostname.", required=True)
@add_common_options(etl_select_option())
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_airflow(ctx, host, name, **kwargs):
    """
    Onboard an airflow connection
    """
    etl_name = name or "airflow"
    AirflowOnboardingService(
        config=ctx["config"],
        command_name="integrations add_airflow",
    ).onboard_airflow(
        etl_name=etl_name,
        hostName=host,
        **kwargs,
    )


@integrations.command(help=f"Configure S3 metadata events. {EVENT_VERBIAGE}.")
@click.pass_obj
@click.option(
    "--connection-type",
    help="Type of the integration.",
    cls=AdvancedOptions,
    mutually_exclusive_options=["connection_id"],
    type=click.Choice(
        [
            GLUE_CONNECTION_TYPE,
            HIVE_MYSQL_CONNECTION_TYPE,
        ],
        case_sensitive=False,
    ),
    required=True,
)
@add_common_options(warehouse_create_option(default="s3-metadata-events"))
@add_common_options(DISAMBIGUATE_DC_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def configure_metadata_events(ctx, **kwargs):
    """
    Configure S3 metadata events for a lake
    """
    EventsOnboardingService(
        config=ctx["config"],
        command_name="integrations configure_metadata_events",
    ).configure_metadata_events(**kwargs)


@integrations.command(help=f"Configure S3 query log events. {EVENT_VERBIAGE}.")
@click.pass_obj
@click.option(
    "--connection-type",
    help="Type of the integration.",
    type=click.Choice([HIVE_S3_CONNECTION_TYPE, PRESTO_S3_CONNECTION_TYPE], case_sensitive=True),
    required=True,
)
@add_common_options(warehouse_select_option())
@add_common_options(role_options())
@click.option(
    "--format-type",
    help="Query log format.",
    type=click.Choice(["hive-emr", "hive-native", "custom"], case_sensitive=True),
    required=True,
)
@click.option(
    "--source-format",
    help='Query log file format. Only required when "custom" is used.',
    type=click.Choice(["json", "jsonl"], case_sensitive=True),
    required=False,
)
@click.option(
    "--mapping-file",
    help='Mapping of expected to existing query log fields. Only required if "custom" is used.',
    type=click.Path(exists=True),
    required=False,
)
@click.option(
    "--dc-id",
    help="Collector UUID to enable events on. If not specified, collector"
    " used by the Warehouse will be used.",
    required=False,
)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def configure_query_log_events(ctx, **kwargs):
    """
    Configure S3 query log events for a lake
    """
    EventsOnboardingService(
        config=ctx["config"],
        command_name="integrations configure_query_log_events",
    ).configure_query_log_events(**kwargs)


@integrations.command(help="Disable S3 metadata events.")
@click.pass_obj
@click.option("--name", help="Resource name (only required if more than one exists)")
@click.option(
    "--dc-id",
    help="Collector UUID to enable events on. If not specified, collector "
    "used by the Warehouse will be used.",
    required=False,
)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def disable_metadata_events(ctx, **kwargs):
    """
    Configure S3 metadata events
    """
    EventsOnboardingService(
        config=ctx["config"],
        command_name="integrations disable_metadata_events",
    ).disable_metadata_events(**kwargs)


@integrations.command(help="Disable S3 query log events.")
@click.pass_obj
@click.option("--name", help="Resource name (only required if more than one exists)")
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def disable_query_log_events(ctx, **kwargs):
    """
    Configure S3 query log events
    """
    EventsOnboardingService(
        config=ctx["config"],
        command_name="integrations disable_query_log_events",
    ).disable_query_log_events(**kwargs)


@integrations.command(help=f"Setup a Tableau integration. {BI_VERBIAGE}.")
@click.pass_obj
@click.option(
    "--token-name",
    help="Name for the personal access token.",
    cls=AdvancedOptions,
    mutually_exclusive_options=[
        "password",
        "user",
        "username",
        "client_id",
        "secret_id",
        "secret_value",
    ],
    required_with_options=["token_value"],
    at_least_one_set=[
        "password",
        "user",
        "username",
        "token_name",
        "token_value",
        "client_id",
        "secret_id",
        "secret_value",
    ],
)
@click.option(
    "--token-value",
    help=f"Value for the personal access token. {PASSWORD_VERBIAGE}.",
    cls=AdvancedOptions,
    mutually_exclusive_options=[
        "password",
        "user",
        "username",
        "client_id",
        "secret_id",
        "secret_value",
    ],
    required_with_options=["token_name"],
    prompt_if_requested=True,
)
@click.option(
    "--password",
    help=f"Password for the service account. {PASSWORD_VERBIAGE}.",
    cls=AdvancedOptions,
    mutually_exclusive_options=[
        "token_name",
        "token_value",
        "username",
        "client_id",
        "secret_id",
        "secret_value",
    ],
    required_with_options=["user"],
    prompt_if_requested=True,
)
@click.option(
    "--user",
    help="Username for the service account.",
    cls=AdvancedOptions,
    mutually_exclusive_options=[
        "token_name",
        "token_value",
        "username",
        "client_id",
        "secret_id",
        "secret_value",
    ],
    required_with_options=["password"],
)
@click.option(
    "--username",
    help="Username for the Connected App.",
    cls=AdvancedOptions,
    mutually_exclusive_options=["token_name", "token_value", "user", "password"],
    required_with_options=["client_id", "secret_id", "secret_value"],
)
@click.option(
    "--client-id",
    help="Client ID for the Connected App.",
    cls=AdvancedOptions,
    mutually_exclusive_options=["token_name", "token_value", "user", "password"],
    required_with_options=["username", "secret_id", "secret_value"],
)
@click.option(
    "--secret-id",
    help="Secret ID for the Connected App.",
    cls=AdvancedOptions,
    mutually_exclusive_options=["token_name", "token_value", "user", "password"],
    required_with_options=["username", "client_id", "secret_value"],
)
@click.option(
    "--secret-value",
    help=f"Value of the Connected App secret. {PASSWORD_VERBIAGE}",
    cls=AdvancedOptions,
    mutually_exclusive_options=["token_name", "token_value", "user", "password"],
    required_with_options=["username", "client_id", "secret_id"],
    prompt_if_requested=True,
)
@click.option("--site-name", help="The Tableau site name.", required=True)
@click.option("--server-name", help="The Tableau server name.", required=True)
@click.option("--name", help="Friendly name for the Tableau integration.", required=False)
@click.option("--connection-name", help="Friendly name for Tableau connection.", required=False)
@add_common_options(BI_OPTIONS)
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_tableau(ctx, user, username, **kwargs):
    """
    Onboard a tableau connection
    """
    ReportsOnboardingService(
        config=ctx["config"],
        command_name="integrations add_tableau",
    ).onboard_tableau(
        username=user or username,
        **kwargs,
    )


@integrations.command(help=f"Setup a Looker metadata integration. {BI_VERBIAGE}.")
@click.pass_obj
@click.option("--host-url", "base_url", help="Looker host url.", required=True)
@click.option("--client-id", help="Looker client id.", required=True)
@click.option(
    "--client-secret",
    help=f"Looker client secret (API key). {PASSWORD_VERBIAGE}.",
    required=True,
    cls=AdvancedOptions,
    prompt_if_requested=True,
)
@click.option("--name", help="Friendly name for the Looker integration.", required=False)
@click.option("--connection-name", help="Friendly name for Looker connection.", required=False)
@add_common_options(BI_OPTIONS)
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
def add_looker(ctx, **kwargs):
    """
    Onboard a looker metadata connection
    """
    ReportsOnboardingService(
        config=ctx["config"],
        command_name="integrations add_looker",
    ).onboard_looker_metadata(**kwargs)


@integrations.command(
    help="""
Create or refresh details of BI warehouse sources. Warehouse sources are warehouses connected to a BI container.

If only the bi-container-id parameter is supplied, then the behavior will be the following:
\b
\n
(1) All warehouse sources in the customer's BI system will be matched against warehouses in Monte Carlo.
\b
\n
(2) If all of the customer's BI warehouse sources have a match in Monte Carlo, then the warehouse source details will be
saved.
\b
\n
(3) Otherwise, the response will contain the details of customer's BI warehouse sources and Monte Carlo warehouses. The
caller will then need to manually save the warehouse source details by specifying the warehouse-source-details
parameter.
\b
\n
If the warehouse-source-details parameter is also supplied, then the warehouses will be validated and saved.
"""  # noqa
)
@click.pass_obj
@click.option(
    "--bi-container-id",
    help="ID of the BI container for which to refresh warehouse sources.",
    required=True,
)
@click.option(
    "--warehouse-source-details",
    help="""
              An optional JSON array of warehouse sources. If supplied, these warehouse sources will be created. If an
              entry with the same bi_container_id, warehouse_resource_id and warehouse_resource_type is found, its
              bi_warehouse_id will be updated.

              Each JSON object in this array has the following fields:
              \b
              \n
              bi_warehouse_id: The ID of the warehouse in the customer's ID space.
              \b
              \n
              warehouse_resource_id: The ID of the warehouse Monte Carlo's ID space.
              \b
              \n
              warehouse_resource_type: The type of the warehouse.
              \b
              \n
              E.g. --warehouse-source-details '[{"bi_warehouse_id":"0dd5d40e-8749-71cb-9fa5-2e33b570ff43",
              "warehouse_resource_id": "11b1ad6f-e35c-4532-84d8-2fc88bd53660", "warehouse_resource_type": "snowflake"}]'
              """,  # noqa
    required=False,
    callback=validate_json_callback,
)
def refresh_bi_to_warehouse_connections(ctx, bi_container_id, warehouse_source_details, **kwargs):
    BiService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations refresh_bi_to_warehouse_connections",
    ).refresh_bi_to_warehouse_connections(bi_container_id, warehouse_source_details)


@integrations.command(help=f"Setup a Looker ML (git) integration. {BI_VERBIAGE}.")
@click.pass_obj
@click.option(
    "--ssh-key",
    help="The ssh key for git ssh integrations.",
    required=False,
    type=click.Path(dir_okay=False, exists=True),
    cls=AdvancedOptions,
    mutually_exclusive_options=["token", "username"],
)
@click.option(
    "--repo-url",
    help="Repository URL as ssh://[user@]server/project.git or the shorter "
    "form [user@]server:project.git for ssh. For https, use https://server/project.git.",
    required=True,
)
@click.option(
    "--token",
    help="Git Access Token to be used for Https instead of ssh key.",
    required=False,
    cls=AdvancedOptions,
    mutually_exclusive_options=["ssh-key"],
)
@click.option(
    "--username",
    help="Git username to be used in conjunction with the access token. This is only "
    "required for BitBucket integrations.",
    cls=AdvancedOptions,
    required=False,
    mutually_exclusive_options=["ssh-key"],
)
@click.option("--connection-name", help="Friendly name for Looker Git connection.", required=False)
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
def add_looker_git(ctx, **kwargs):
    """
    Onboard a looker metadata connection
    """
    ReportsOnboardingService(
        config=ctx["config"],
        command_name="integrations add_looker_git",
    ).onboard_looker_git(**kwargs)


@integrations.command(help=f"Setup a Power BI integration. {BI_VERBIAGE}.")
@click.pass_obj
@click.option("--tenant-id", help="The tenant ID from the Azure Active Directory.", required=True)
@click.option(
    "--auth-mode",
    help="Authentication Mode. We support service principal and primary user two auth types",
    required=True,
    type=click.Choice(["SERVICE_PRINCIPAL", "PRIMARY_USER"]),
)
@click.option(
    "--client-id",
    help="App registration application ID for accessing Power BI.",
    required=True,
    cls=AdvancedOptions,
)
@click.option(
    "--client-secret",
    help="Secret for the application to access the Power BI. Set only when auth-mode is "
    "SERVICE_PRINCIPAL",
    required=False,
    cls=AdvancedOptions,
    mutually_exclusive_options=["username", "password"],
    prompt_if_requested=True,
)
@click.option(
    "--username",
    help="Username for accessing the Power BI. Set only when auth-mode is PRIMARY_USER.",
    cls=AdvancedOptions,
    required=False,
    mutually_exclusive_options=["client-secret"],
)
@click.option(
    "--password",
    help="Password for accessing the Power BI. Set only when auth-mode is PRIMARY_USER.",
    cls=AdvancedOptions,
    required=False,
    mutually_exclusive_options=["client-secret"],
    prompt_if_requested=True,
)
@click.option("--name", help="Friendly name for the Power BI integration.", required=False)
@click.option("--connection-name", help="Friendly name for Power BI connection.", required=False)
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
def add_power_bi(ctx, **kwargs):
    """
    Onboard a Power BI connection
    """
    ReportsOnboardingService(
        config=ctx["config"],
        command_name="integrations add_power_bi",
    ).onboard_power_bi(**kwargs)


@integrations.command(help="Setup a dbt Cloud integration.")
@click.pass_obj
@click.option(
    "--dbt-cloud-api-token",
    "dbt_cloud_api_token",
    help=f"dbt Cloud API token. {PASSWORD_VERBIAGE}.",
    required=True,
    cls=AdvancedOptions,
    prompt_if_requested=True,
)
@click.option(
    "--dbt-cloud-account-id",
    "dbt_cloud_account_id",
    help="dbt Cloud Account ID.",
    required=True,
)
@click.option(
    "--dbt-cloud-base-url",
    "dbt_cloud_base_url",
    help="dbt Cloud Base URL.",
    required=False,
)
@click.option(
    "--webhook-hmac-secret",
    "webhook_hmac_secret",
    help="The secret token `hmac_secret` provided by dbt after a webhook "
    "is successfully created in dbt.",
    required=True,
)
@click.option(
    "--webhook-id",
    "webhook_id",
    help="The webhook id provided by dbt after a webhook is successfully created in dbt.",
    required=True,
)
@add_common_options(warehouse_select_option())
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
def add_dbt_cloud(ctx, name, **kwargs):
    """
    Onboard a dbt cloud connection
    """
    DbtCloudOnboardingService(
        config=ctx["config"],
        command_name="integrations add_dbt_cloud",
    ).onboard_dbt_cloud(warehouseName=name, **kwargs)


@integrations.command(help="Setup a Fivetran integration.")
@click.pass_obj
@click.option(
    "--fivetran-api-key",
    "fivetran_api_key",
    help=f"Fivetran API Key. {PASSWORD_VERBIAGE}.",
    required=True,
    cls=AdvancedOptions,
    prompt_if_requested=True,
)
@click.option(
    "--fivetran-api-password",
    "fivetran_api_password",
    help=f"Fivetran API Key. {PASSWORD_VERBIAGE}.",
    required=True,
    cls=AdvancedOptions,
    prompt_if_requested=True,
)
@click.option(
    "--fivetran-base-url",
    "fivetran_base_url",
    help="Fivetran Base URL.",
    required=False,
)
@add_common_options(etl_select_option())
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
def add_fivetran(ctx, name, **kwargs):
    """
    Onboard a Fivetran connection
    """
    FivetranOnboardingService(
        config=ctx["config"],
        command_name="integrations add_fivetran",
    ).onboard_fivetran(etl_name=name, **kwargs)


@integrations.command(help="Setup an Azure Data Factory integration.")
@click.pass_obj
@click.option(
    "--tenant-id",
    help="Azure Tenant ID.",
    required=True,
)
@click.option(
    "--client-id",
    help="Azure Client ID.",
    required=True,
)
@click.option(
    "--client-secret",
    help=f"Azure Client Secret. {PASSWORD_VERBIAGE}.",
    required=True,
    cls=AdvancedOptions,
    prompt_if_requested=True,
)
@click.option(
    "--subscription-id",
    help="Azure Subscription ID.",
    required=True,
)
@click.option(
    "--resource-group-name",
    help="Azure Resource Group Name.",
    required=True,
)
@click.option(
    "--factory-name",
    help="Azure Data Factory Name.",
    required=True,
)
@add_common_options(etl_select_option(required=True))
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
def add_azure_data_factory(ctx, **kwargs):
    """
    Onboard an Azure Data Factory connection
    """
    AzureDataFactoryOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations add_azure_data_factory",
    ).onboard(**kwargs)


@integrations.command(help="Setup an Informatica integration.")
@click.pass_obj
@click.option(
    "--username",
    help=f"Informatica username. {PASSWORD_VERBIAGE}.",
    required=True,
    cls=AdvancedOptions,
    prompt_if_requested=True,
)
@click.option(
    "--password",
    help=f"Informatica password. {PASSWORD_VERBIAGE}.",
    required=True,
    cls=AdvancedOptions,
    prompt_if_requested=True,
)
@add_common_options(etl_select_option(required=True))
@add_common_options(ONBOARDING_CONFIGURATION_OPTIONS)
def add_informatica(ctx, **kwargs):
    """
    Onboard an Informatica connection
    """
    InformaticaOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations add_informatica",
    ).onboard(**kwargs)


@integrations.command(help=f"Setup a SQL Server integration. {LIGHTWEIGHT_VERBIAGE}.")
@click.pass_obj
@add_common_options(
    warehouse_create_option(required=True)
    + port_create_option(default_port=1433)
    + BASIC_DATABASE_OPTIONS
    + ONBOARDING_CONFIGURATION_OPTIONS
)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_sql_server(ctx, name, **kwargs):
    """
    Onboard a SQL Server connection
    """
    TransactionalOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations add_sql_server",
    ).onboard_transactional_db(warehouseName=name, dbType=SQL_SERVER_DB_TYPE, **kwargs)


@integrations.command(help=f"Setup a Postgres integration. {LIGHTWEIGHT_VERBIAGE}.")
@click.pass_obj
@add_common_options(
    warehouse_create_option(required=True)
    + port_create_option(default_port=5432)
    + DATABASE_OPTIONS
    + ONBOARDING_CONFIGURATION_OPTIONS
)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
@click.option(
    "--rds-proxy",
    is_flag=True,
    help="Use if connecting to Postgres through a RDS proxy.",
    required=False,
)
def add_postgres(ctx, database, name, rds_proxy, **kwargs):
    """
    Onboard a Postgres connection
    """
    kwargs["connection_settings"] = {"rds_proxy": rds_proxy}
    TransactionalOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations add_postgres",
    ).onboard_transactional_db(
        warehouseName=name, dbName=database, dbType=POSTGRES_DB_TYPE, **kwargs
    )


@integrations.command(help=f"Setup a MySQL integration. {LIGHTWEIGHT_VERBIAGE}.")
@click.pass_obj
@add_common_options(
    warehouse_create_option(required=True)
    + port_create_option(default_port=3306)
    + BASIC_DATABASE_OPTIONS
    + ONBOARDING_CONFIGURATION_OPTIONS
    + SSL_OPTIONS
)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_mysql(ctx, name, **kwargs):
    """
    Onboard a MySQL connection
    """
    TransactionalOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations add_mysql",
    ).onboard_transactional_db(warehouseName=name, dbType=MYSQL_DB_TYPE, **kwargs)


@integrations.command(help=f"Setup an Oracle integration. {LIGHTWEIGHT_VERBIAGE}.")
@click.pass_obj
@add_common_options(
    warehouse_create_option(required=True)
    + port_create_option(default_port=1521)
    + DATABASE_OPTIONS
    + ONBOARDING_CONFIGURATION_OPTIONS
)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_oracle(ctx, database, name, **kwargs):
    """
    Onboard an Oracle connection
    """
    TransactionalOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations add_oracle",
    ).onboard_transactional_db(warehouseName=name, dbName=database, dbType=ORACLE_DB_TYPE, **kwargs)


@integrations.command(help=f"Setup an MariaDB integration. {LIGHTWEIGHT_VERBIAGE}.")
@click.pass_obj
@add_common_options(
    warehouse_create_option(required=True)
    + port_create_option(default_port=3306)
    + BASIC_DATABASE_OPTIONS
    + ONBOARDING_CONFIGURATION_OPTIONS
)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_mariadb(ctx, name, **kwargs):
    """
    Onboard an MariaDB connection
    """
    TransactionalOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations add_mariadb",
    ).onboard_transactional_db(warehouseName=name, dbType=MARIADB_DB_TYPE, **kwargs)


@integrations.command(help=f"Setup a Teradata integration. {LIGHTWEIGHT_VERBIAGE}.")
@click.pass_obj
@add_common_options(
    warehouse_create_option(required=True)
    + port_create_option(default_port=1025)
    + BASIC_DATABASE_OPTIONS
    + ONBOARDING_CONFIGURATION_OPTIONS
)
@add_common_options(TERADATA_OPTIONS)
def add_teradata(ctx, name, sslmode, logmech, **kwargs):
    """
    Onboard a Teradata connection
    """
    kwargs["connection_settings"] = {
        key: value
        for key, value in [("td_sslmode", sslmode), ("td_logmech", logmech)]
        if value is not None
    }

    TransactionalOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations add_teradata",
    ).onboard_transactional_db(warehouseName=name, dbType=TERADATA_DB_TYPE, **kwargs)


@integrations.command(help=f"Update a Teradata integration. {LIGHTWEIGHT_VERBIAGE}.")
@click.pass_obj
@click.option("--host", help="Hostname.", required=False)
@click.option("--port", help="Port to use for connection.", required=False)
@click.option("--user", help="Username with access to the database.", required=False)
@click.option(
    "--password",
    help=f"User's password. {PASSWORD_VERBIAGE}.",
    required=False,
    cls=AdvancedOptions,
    prompt_if_requested=True,
)
@add_common_options(TERADATA_OPTIONS)
@add_common_options(UPDATE_VALIDATION_OPTIONS)
def update_teradata(ctx, sslmode, logmech, connection_id, **kwargs):
    """
    Update a Teradata connection
    """
    kwargs["connection_settings"] = {
        key: value
        for key, value in [("td_sslmode", sslmode), ("td_logmech", logmech)]
        if value is not None
    }

    TransactionalOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations update_teradata",
    ).update_transactional_db(connection_id=connection_id, connection_type="teradata", **kwargs)


@integrations.command(
    help=f"Setup an Azure Dedicated SQL Pool integration. {LIGHTWEIGHT_VERBIAGE}."
)
@click.pass_obj
@add_common_options(
    warehouse_create_option(required=True)
    + port_create_option(default_port=1433)
    + DATABASE_OPTIONS
    + ONBOARDING_CONFIGURATION_OPTIONS
)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_azure_dedicated_sql_pool(ctx, database, name, **kwargs):
    """
    Onboard an Azure Dedicated SQL Pool connection
    """
    TransactionalOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations add_azure_dedicated_sql_pool",
    ).onboard_transactional_db(
        warehouseName=name,
        dbName=database,
        dbType=AZURE_DEDICATED_SQL_POOL_TYPE,
        **kwargs,
    )


@integrations.command(help=f"Setup an Azure SQL Database integration. {LIGHTWEIGHT_VERBIAGE}.")
@click.pass_obj
@add_common_options(
    warehouse_create_option(required=True)
    + port_create_option(default_port=1433)
    + DATABASE_OPTIONS
    + ONBOARDING_CONFIGURATION_OPTIONS
)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_azure_sql_database(ctx, database, name, **kwargs):
    """
    Onboard an Azure SQL Database connection
    """
    TransactionalOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations add_azure_sql_database",
    ).onboard_transactional_db(
        warehouseName=name,
        dbName=database,
        dbType=AZURE_SQL_DATABASE_TYPE,
        **kwargs,
    )


@integrations.command(help=f"Setup a SAP HANA integration. {LIGHTWEIGHT_VERBIAGE}.")
@click.pass_obj
@add_common_options(
    warehouse_create_option(required=True)
    + port_create_option(default_port=39015)
    + DATABASE_OPTIONS
    + ONBOARDING_CONFIGURATION_OPTIONS
)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_sap_hana_database(ctx, database, name, **kwargs):
    """
    Onboard a SAP HANA Database connection
    """
    TransactionalOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations add_sap_hana_database",
    ).onboard_transactional_db(
        warehouseName=name,
        dbName=database,
        dbType=SAP_HANA_DATABASE_TYPE,
        **kwargs,
    )


@integrations.command(help=f"Setup a Motherduck integration. {LIGHTWEIGHT_VERBIAGE}.")
@click.pass_obj
@add_common_options(
    warehouse_create_option(required=True)
    + [
        click.option("--token", help="Token for authentication", required=True),
        click.option("--database", help="Name of default database.", required=True),
    ]
    + ONBOARDING_CONFIGURATION_OPTIONS
)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_motherduck_database(ctx, database, name, **kwargs):
    """
    Onboard a Motherduck connection
    """
    TransactionalOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations add_motherduck_database",
    ).onboard_transactional_db(
        warehouseName=name,
        dbName=database,
        dbType=MOTHERDUCK_DATABASE_TYPE,
        **kwargs,
    )


@integrations.command(help=f"Setup a Dremio integration. {LIGHTWEIGHT_VERBIAGE}.")
@click.pass_obj
@add_common_options(
    warehouse_create_option(required=True)
    + [
        click.option("--token", help="Token for authentication", required=True),
        click.option(
            "--host",
            help="Hostname of coordinator node or data.dremio.cloud if using Dremio cloud.",
            required=True,
        ),
        click.option(
            "--port",
            help="Dremio's Arrow Flight server port. 443 if using Dremio Cloud",
            required=True,
        ),
    ]
    + ONBOARDING_CONFIGURATION_OPTIONS
)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
@click.option(
    "--tls",
    is_flag=True,
    help="Use TLS for connection. Required for Dremio cloud.",
    required=False,
)
def add_dremio(ctx, name, tls, **kwargs):
    """
    Onboard a Dremio connection
    """
    if tls:
        kwargs["connection_settings"] = {"tls": True}

    TransactionalOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations add_dremio",
    ).onboard_transactional_db(
        warehouseName=name,
        dbType=DREMIO_DATABASE_TYPE,
        **kwargs,
    )


@integrations.command(help=f"Setup a Salesforce CRM integration. {LIGHTWEIGHT_VERBIAGE}.")
@click.pass_obj
@click.option(
    "--token",
    help="Salesforce CRM token for authentication",
    required=False,
    cls=AdvancedOptions,
    required_with_options=["user", "password"],
    mutually_exclusive_options=["consumer_key"],
)
@click.option(
    "--user",
    help="Salesforce CRM username for authentication.",
    required=False,
    cls=AdvancedOptions,
    required_with_options=["token", "password"],
)
@click.option(
    "--password",
    help="Salesforce CRM password for authentication.",
    required=False,
    cls=AdvancedOptions,
    required_with_options=["token", "user"],
    prompt_if_requested=True,
)
@click.option(
    "--consumer-key",
    "consumer_key",
    help="Salesforce CRM consumer key for OAuth 2.0 client credentials.",
    required=False,
    cls=AdvancedOptions,
    required_with_options=["consumer_secret", "domain"],
    mutually_exclusive_options=["token"],
)
@click.option(
    "--consumer-secret",
    "consumer_secret",
    help="Salesforce CRM consumer secret for OAuth 2.0 client credentials.",
    required=False,
    cls=AdvancedOptions,
    required_with_options=["consumer_key", "domain"],
    prompt_if_requested=True,
)
@click.option(
    "--domain",
    help='Salesforce "My Domain URL" for your organization.',
    required=False,
    cls=AdvancedOptions,
    required_with_options=["consumer_key", "consumer_secret"],
)
@add_common_options(warehouse_create_option(required=True) + ONBOARDING_CONFIGURATION_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_salesforce_crm(ctx, name, **kwargs):
    """
    Onboard a Salesforce CRM connection
    """
    TransactionalOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations add_salesforce_crm",
    ).onboard_transactional_db(
        warehouseName=name,
        dbType=SALESFORCE_CRM_DATABASE_TYPE,
        **kwargs,
    )


@integrations.command(help=f"Setup a Salesforce Data Cloud integration. {LIGHTWEIGHT_VERBIAGE}.")
@click.pass_obj
@click.option(
    "--consumer-key",
    "consumer_key",
    help="Salesforce Connected App Consumer Key.",
    required=True,
    cls=AdvancedOptions,
)
@click.option(
    "--consumer-secret",
    "consumer_secret",
    help="Salesforce Connected App Consumer Secret.",
    required=True,
    cls=AdvancedOptions,
    prompt_if_requested=True,
)
@click.option(
    "--domain",
    help='Salesforce "My Domain URL" for your organization.',
    required=True,
    cls=AdvancedOptions,
)
@add_common_options(warehouse_create_option(required=True) + ONBOARDING_CONFIGURATION_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_salesforce_data_cloud(ctx, name, **kwargs):
    """
    Onboard a Salesforce Data Cloud connection
    """
    TransactionalOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations add_salesforce_data_cloud",
    ).onboard_transactional_db(
        warehouseName=name,
        dbType=SALESFORCE_DATA_CLOUD_DATABASE_TYPE,
        **kwargs,
    )


@integrations.command(help=f"Setup a Clickhouse integration. {LIGHTWEIGHT_VERBIAGE}.")
@click.pass_obj
@add_common_options(
    warehouse_create_option(required=True)
    + port_create_option(default_port=8123)
    + DATABASE_OPTIONS
    + ONBOARDING_CONFIGURATION_OPTIONS
)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_clickhouse(ctx, database, name, **kwargs):
    """
    Onboard a Clickhouse connection
    """
    TransactionalOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations add_clickhouse",
    ).onboard_transactional_db(
        warehouseName=name,
        dbName=database,
        dbType=CLICKHOUSE_DATABASE_TYPE,
        **kwargs,
    )


@integrations.command(help="List all active connections.", name="list")
@click.pass_obj
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def display_integrations(ctx):
    """
    Display active integrations
    """
    OnboardingStatusService(
        config=ctx["config"],
        command_name="integrations display_integrations",
    ).display_integrations()


@integrations.command(
    help="Create an IAM role from a policy FILE. "
    "The returned role ARN and external id should be used for adding lake assets."
)
@click.pass_obj
@click.argument("file", type=click.Path(dir_okay=False, exists=True))
@click.option(
    "--aws-profile",
    required=True,
    help="The AWS profile indicating where the role is created.",
)
@add_common_options(DISAMBIGUATE_DC_OPTIONS)
def create_role(ctx, file, aws_profile, dc_id, agent_id):
    """
    Create a collector compatible role from the provided policy
    """
    CloudResourceService(
        config=ctx["config"],
        aws_profile_override=aws_profile,
        command_name="integrations create_role",
    ).create_role(path_to_policy_doc=file, dc_id=dc_id, agent_id=agent_id)


@integrations.command(
    help="Update credentials for a connection. Only replaces/inserts the "
    "keys in changes by default.",
    name="update",
)
@click.pass_obj
@add_common_options(CONNECTION_OPTIONS)
@click.option(
    "--changes",
    help="""
              Credential key,value pairs as JSON.
              \b
              \n
              E.g. --changes '{"user":"Apollo"}'
              """,
    required=False,
    cls=AdvancedOptions,
    at_least_one_set=["ssl_ca", "changes", "remove_ssl_ca"],
    callback=validate_json_callback,
)
@click.option(
    "--ssl-ca",
    help="For integrations that support client certs, update the cert used.",
    required=False,
    cls=AdvancedOptions,
    at_least_one_set=["ssl_ca", "changes", "remove_ssl_ca"],
    mutually_exclusive_options=["remove_ssl_ca"],
    type=click.Path(dir_okay=False, exists=True),
)
@click.option(
    "--remove-ssl-ca",
    help="Remove the SSL CA cert from credentials.",
    is_flag=True,
    default=False,
    cls=AdvancedOptions,
    at_least_one_set=["ssl_ca", "changes", "remove_ssl_ca"],
    mutually_exclusive_options=["ssl_ca"],
)
@click.option(
    "--skip-validation",
    help="Skip validating credentials.",
    default=False,
    show_default=True,
    is_flag=True,
)
@click.option(
    "--replace-all",
    help="Replace all credentials rather than just inserting/updating the keys in changes.",
    default=False,
    show_default=True,
    is_flag=True,
)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def update_credentials(
    ctx, connection_id, changes, ssl_ca, remove_ssl_ca, skip_validation, replace_all
):
    """
    Update credentials for a connection
    """
    ConnectionOperationsService(
        config=ctx["config"],
        command_name="integrations update_credentials",
    ).update_credentials(
        connection_id=connection_id,
        changes=changes,
        ssl_ca=ssl_ca,
        remove_ssl_ca=remove_ssl_ca,
        should_validate=not skip_validation,
        should_replace=replace_all,
    )


@integrations.command(
    help="Remove an existing connection. Deletes any associated jobs, monitors, etc.",
    name="remove",
)
@click.pass_obj
@add_common_options(CONNECTION_OPTIONS)
@click.option(
    "--no-prompt",
    help="Don't ask for confirmation.",
    default=False,
    show_default=True,
    is_flag=True,
)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def remove_connection(ctx, **kwargs):
    """
    Remove connection by ID
    """
    ConnectionOperationsService(
        config=ctx["config"],
        command_name="integrations remove_connection",
    ).remove_connection(**kwargs)


@integrations.command(help="Retest an existing connection.", name="test")
@click.pass_obj
@add_common_options(CONNECTION_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def echo_test_existing(ctx, **kwargs):
    """
    Tests an existing connection and echos results in pretty JSON.
    """
    ConnectionOperationsService(
        config=ctx["config"],
        command_name="integrations echo_test_existing",
    ).echo_test_existing(**kwargs)


@integrations.command(help="Setup complete S3 event notifications for a lake.")
@click.pass_obj
@add_common_options(S3_BUCKET_OPTIONS)
@add_common_options(EVENT_TYPE_OPTIONS)
@add_common_options(COLLECTOR_PROFILE_OPTIONS)
@add_common_options(RESOURCE_PROFILE_OPTIONS)
@add_common_options(AUTO_YES_OPTIONS)
@add_common_options(DISAMBIGUATE_DC_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_events(ctx, **kwargs):
    CloudResourceService(
        config=ctx["config"],
        aws_wrapper=None,
        command_name="integrations add_events",
    ).add_events(**kwargs)


@integrations.command(help="Setup Event Topic for S3 event notifications in a lake.")
@click.pass_obj
@add_common_options(S3_BUCKET_OPTIONS)
@add_common_options(EVENT_TYPE_OPTIONS)
@add_common_options(RESOURCE_PROFILE_OPTIONS)
@add_common_options(AUTO_YES_OPTIONS)
@add_common_options(DISAMBIGUATE_DC_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def create_event_topic(ctx, **kwargs):
    CloudResourceService(
        config=ctx["config"],
        aws_wrapper=None,
        command_name="integrations create_event_topic",
    ).create_event_topic(**kwargs)


@integrations.command(help="Setup Bucket Side S3 event infrastructure for a lake.")
@click.pass_obj
@add_common_options(S3_BUCKET_OPTIONS)
@add_common_options(EVENT_TYPE_OPTIONS)
@add_common_options(RESOURCE_PROFILE_OPTIONS)
@add_common_options(AUTO_YES_OPTIONS)
@add_common_options(DISAMBIGUATE_DC_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def create_bucket_side_event_infrastructure(ctx, **kwargs):
    CloudResourceService(
        config=ctx["config"],
        aws_wrapper=None,
        command_name="integrations create_bucket_side_event_infrastructure",
    ).create_bucket_side_event_infrastructure(**kwargs)


@integrations.command(
    help="Create an integration key. The resulting key id and secret will "
    "be printed to the console."
)
@click.pass_obj
@click.option("--description", required=True, help="Key description.")
@click.option(
    "--scope",
    required=True,
    type=click.Choice(IntegrationKeyScope.values(), case_sensitive=False),
    help="Key scope (integration the key can be used for).",
)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def create_key(ctx, **kwargs):
    IntegrationKeyService(
        config=ctx["config"],
        command_name="integrations create_key",
    ).create(**kwargs)


@integrations.command(help="Delete an integration key.")
@click.pass_obj
@click.option("--key-id", required=True, help="Integration key id.")
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def delete_key(ctx, **kwargs):
    IntegrationKeyService(
        config=ctx["config"],
        command_name="integrations delete_key",
    ).delete(**kwargs)


@integrations.command(help="List all integration keys.")
@click.pass_obj
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def list_keys(ctx):
    IntegrationKeyService(
        config=ctx["config"],
        command_name="integrations list_keys",
    ).get_all()


@integrations.command(help="Set the name of a Warehouse.")
@click.pass_obj
@click.option("--current-name", required=True, help="Current Name of the Warehouse")
@click.option("--new-name", required=True, help="Name to give the Warehouse")
def set_warehouse_name(ctx, **kwargs):
    ConnectionOperationsService(
        config=ctx["config"],
        command_name="integrations set_warehouse_name",
    ).set_warehouse_name(**kwargs)


@integrations.command(help="Set the name of a BI Connection.")
@click.pass_obj
@click.option("--bi-connection-id", required=True, help="UUID of the existing BI Connection")
@click.option("--new-name", required=True, help="Name to give the BI Connection")
def set_bi_connection_name(ctx, **kwargs):
    ConnectionOperationsService(
        config=ctx["config"],
        command_name="integrations set_bi_connection_name",
    ).set_bi_connection_name(**kwargs)


@integrations.command(help="Setup a streaming system.")
@click.pass_obj
@click.option(
    "--streaming-system-type",
    required=True,
    type=click.Choice(["confluent-cloud", "msk", "self-hosted"]),
    help="Streaming System type. Currently we only support confluent-cloud and self-hosted.",
)
@click.option(
    "--streaming-system-name",
    required=True,
    help="Name that helps you identify the streaming system in MC.",
)
@click.option(
    "--dc-id",
    help="The data collector UUID that you'd like to run jobs of this system in. "
    "This is needed when you have more than one active data collector.",
    required=False,
    cls=AdvancedOptions,
)
def add_streaming_system(ctx, **kwargs):
    StreamingOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations add_streaming_system",
    ).create_streaming_system(**kwargs)


@integrations.command(help="Test and generate credential key for Confluent Kafka Connection.")
@click.pass_obj
@click.option(
    "--cluster",
    required=True,
    help="Cluster ID in Confluent Cloud.",
)
@click.option(
    "--api-key",
    required=True,
    help="API Key.",
)
@click.option(
    "--secret",
    help="Secret of the API Key.",
    required=True,
)
@click.option(
    "--url",
    help="URL for accessing the Kafka Cluster in Confluent Cloud.",
    required=True,
)
@click.option(
    "--dc-id",
    help="Data Collector UUID, if we'd like to test the credentials against the "
    "specific dc, or you have multiple DC.",
    required=False,
)
def test_confluent_kafka_credentials(ctx, **kwargs):
    StreamingOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations test_confluent_kafka_credentials",
    ).test_new_confluent_kafka_credentials(**kwargs)


@integrations.command(
    help="Test and generate credential key for Confluent Cloud accessing Kafka Connect."
)
@click.pass_obj
@click.option(
    "--confluent-env",
    required=True,
    help="Environment ID in Confluent Cloud.",
)
@click.option(
    "--cluster",
    required=True,
    help="Cluster ID of the Kafka Connect in Confluent Cloud.",
)
@click.option(
    "--api-key",
    required=True,
    help="API Key.",
)
@click.option(
    "--secret",
    help="Secret of the API Key.",
    required=True,
)
@click.option(
    "--url",
    help="Special URL for accessing Kafka Connect API in Confluent Cloud. By default, "
    "we use the cloud API URL.",
    required=False,
)
@click.option(
    "--dc-id",
    help="Data Collector UUID, if we'd like to test the credentials against the specific dc, "
    "or you have multiple DC.",
    required=False,
)
def test_confluent_kafka_connect_credentials(ctx, **kwargs):
    StreamingOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations test_confluent_kafka_connect_credentials",
    ).test_new_confluent_kafka_connect_credentials(**kwargs)


@integrations.command(
    help="Test and generate credential key for a MSK Kafka Connection (via REST proxy)."
)
@click.pass_obj
@click.option(
    "--cluster",
    required=True,
    help="Cluster ID",
)
@click.option(
    "--url",
    help="URL for accessing the REST Proxy.",
    required=True,
)
@add_common_options(SELF_HOSTED_STREAMING_AUTH_OPTIONS)
@click.option(
    "--dc-id",
    help="Data Collector UUID, if we'd like to test the credentials against the specific dc, "
    "or you have multiple DC.",
    required=False,
)
def test_msk_kafka_credentials(ctx, **kwargs):
    StreamingOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations test_msk_kafka_credentials",
    ).test_new_msk_kafka_credentials(**kwargs)


@integrations.command(help="Test and generate credential key for a MSK Kafka Connect Connection.")
@click.pass_obj
@click.option(
    "--cluster-arn",
    help="ARN of the MSK cluster the connectors are running against.",
    required=True,
)
@click.option(
    "--iam-role-arn",
    help="ARN of an assumable IAM role that will be used for collection.",
    required=True,
)
@click.option(
    "--external-id",
    help="Optional external id, if required to assume IAM role for collection.",
    required=True,
)
@click.option(
    "--dc-id",
    help="Data Collector UUID, if we'd like to test the credentials against the specific dc, "
    "or you have multiple DC.",
    required=False,
)
def test_msk_kafka_connect_credentials(ctx, **kwargs):
    StreamingOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations test_msk_kafka_connect_credentials",
    ).test_new_msk_kafka_connect_credentials(**kwargs)


@integrations.command(help="Test and generate credential key for a Self Hosted Kafka Connection.")
@click.pass_obj
@click.option(
    "--cluster",
    required=True,
    help="Cluster ID",
)
@click.option(
    "--url",
    help="URL for accessing the self hosted Kafka Rest Proxy.",
    required=True,
)
@add_common_options(SELF_HOSTED_STREAMING_AUTH_OPTIONS)
@click.option(
    "--dc-id",
    help="Data Collector UUID, if we'd like to test the credentials against the specific dc, "
    "or you have multiple DC.",
    required=False,
)
def test_self_hosted_kafka_credentials(ctx, **kwargs):
    StreamingOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations test_self_hosted_kafka_credentials",
    ).test_new_self_hosted_kafka_credentials(**kwargs)


@integrations.command(help="Test and generate credential key for a Self Hosted Kafka Connect.")
@click.pass_obj
@click.option(
    "--cluster",
    required=True,
    help="Cluster ID of the Kafka Connect.",
)
@click.option(
    "--url",
    help="URL for accessing the self hosted Kafka Connect Rest Server.",
    required=True,
)
@add_common_options(SELF_HOSTED_STREAMING_AUTH_OPTIONS)
@click.option(
    "--dc-id",
    help="Data Collector UUID, if we'd like to test the credentials against the specific dc, "
    "or you have multiple DC.",
    required=False,
)
def test_self_hosted_kafka_connect_credentials(ctx, **kwargs):
    StreamingOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations test_self_hosted_kafka_connect_credentials",
    ).test_new_self_hosted_kafka_connect_credentials(**kwargs)


@integrations.command(help=".")
@click.pass_obj
@click.option(
    "--connection-type",
    help="Streaming Connection Type to create. Right now only support "
    "['confluent-kafka', 'confluent-kafka-connect', "
    "'msk-kafka', 'msk-kafka-connect', 'self-hosted-kafka', 'self-hosted-kafka-connect']",
    type=click.Choice(
        [
            "confluent-kafka",
            "confluent-kafka-connect",
            "msk-kafka",
            "msk-kafka-connect",
            "self-hosted-kafka",
            "self-hosted-kafka-connect",
        ]
    ),
    required=True,
)
@click.option(
    "--key",
    help="Credentials key."
    "You can obtain it by calling test-confluent-kafka-credentials for connection type "
    "confluent-kafka; Or calling test-confluent-kafka-connect-credentials for connection type "
    "confluent-kafka-connect. It's ok to leave it blank, but fill [url, api-key, secret] field "
    "for confluent-kafka connection in this all; Or fill [api-key, secret, confluent-env] field "
    "for confluent-kafka-connect connection.",
    required=False,
    cls=AdvancedOptions,
    mutually_exclusive_options=["url", "confluent_env", "api_key", "secret"],
)
@click.option(
    "--url",
    help="This is required only when the key is not specified and the connection "
    "type is confluent-kafka.",
    required=False,
    cls=AdvancedOptions,
    mutually_exclusive_options=["key"],
)
@click.option(
    "--confluent-env",
    help="This is required only when the key is not specified and the connection "
    "type is confluent-kafka-connect.",
    required=False,
    cls=AdvancedOptions,
    mutually_exclusive_options=["key"],
)
@click.option(
    "--api-key",
    help="API for accessing the  This is required only when the credential key is not specified.",
    required=False,
    cls=AdvancedOptions,
    mutually_exclusive_options=["key"],
)
@click.option(
    "--secret",
    help="This is required only when the key is not specified.",
    required=False,
    cls=AdvancedOptions,
    mutually_exclusive_options=["key"],
    prompt_if_requested=True,
)
@click.option(
    "--auth-type",
    type=click.Choice(["NO_AUTH", "BASIC", "BEARER"]),
    required=False,
    help="This is required only when the key is not specified and the cluster is self-hosted.",
    cls=AdvancedOptions,
    mutually_exclusive_options=["key"],
)
@click.option(
    "--auth-token",
    required=False,
    help="This is required only when the key is not specified and the cluster is self-hosted.",
    cls=AdvancedOptions,
    mutually_exclusive_options=["key"],
    prompt_if_requested=True,
)
@click.option(
    "--cluster-arn",
    required=False,
    help="This is required only when the key is not specified and the cluster type is MSK Connect.",
    cls=AdvancedOptions,
    mutually_exclusive_options=["key"],
    prompt_if_requested=True,
)
@click.option(
    "--iam-role-arn",
    required=False,
    help="This is required only when the key is not specified and the cluster type is MSK Connect.",
    cls=AdvancedOptions,
    mutually_exclusive_options=["key"],
    prompt_if_requested=True,
)
@click.option(
    "--external-id",
    required=False,
    help="This is required only when the key is not specified and the cluster type is MSK Connect.",
    cls=AdvancedOptions,
    mutually_exclusive_options=["key"],
    prompt_if_requested=True,
)
@click.option(
    "--streaming-system-id",
    help=(
        "Streaming system UUID. If we are adding a cluster to an existing streaming system, we "
        "should use the UUID here. When this is given, please leave new_streaming_system_name, "
        "new_streaming_system_type, dc_id empty."
    ),
    required=False,
    cls=AdvancedOptions,
    mutually_exclusive_options=[
        "new_streaming_system_name",
        "new_streaming_system_type",
        "dc_id",
    ],
)
@click.option(
    "--new-streaming-system-name",
    help="Streaming System Name, if we are creating a new streaming system along the "
    "new cluster connection.",
    required=False,
    cls=AdvancedOptions,
    mutually_exclusive_options=["streaming_system_id"],
)
@click.option(
    "--new-streaming-system-type",
    help="Streaming System Type, if we are creating a new streaming system along the "
    "new cluster connection.",
    required=False,
    type=click.Choice(["confluent-cloud", "msk", "self-hosted"]),
    cls=AdvancedOptions,
    mutually_exclusive_options=["streaming_system_id"],
)
@click.option(
    "--dc-id",
    help="Data Collector UUID. Only specify when there are more than one data collector "
    "in the system, and you are "
    "trying to create a new streaming system for the cluster connection.",
    required=False,
    cls=AdvancedOptions,
    mutually_exclusive_options=["streaming_system_id"],
)
@click.option(
    "--mc-cluster-id",
    help="Existing Streaming Cluster MC UUID. If we are only adding a connection "
    "to a specific cluster, we set this.",
    required=False,
    cls=AdvancedOptions,
    mutually_exclusive_options=[
        "new_cluster_id",
        "new_cluster_name",
        "new_cluster_type",
    ],
)
@click.option(
    "--new-cluster-id",
    help="Streaming cluster id in your streaming system, required when creating a new cluster",
    required=False,
    cls=AdvancedOptions,
    mutually_exclusive_options=["mc_cluster_id"],
)
@click.option(
    "--new-cluster-name",
    help="New streaming cluster name at MC side. If not specified, will use "
    "cluster ID as the cluster name when creating a new cluster.",
    required=False,
    cls=AdvancedOptions,
    mutually_exclusive_options=["mc_cluster_id"],
)
def add_streaming_cluster_connection(ctx, **kwargs):
    StreamingOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations add_streaming_cluster_connection",
    ).onboard_streaming_cluster_connection(**kwargs)


@integrations.command(help="Setup a Pinecone integration.")
@click.pass_obj
@click.option("--environment", help="Pinecone environment (e.g. us-east-1-aws).", required=True)
@click.option("--project-id", help="Pinecone project id.", required=True)
@click.option("--api-key", help="API key for Pinecone project.", required=True)
@click.option(
    "--name",
    help="Friendly name for the integration (defaults to environment:project-id).",
    required=False,
)
@add_common_options(DISAMBIGUATE_DC_OPTIONS)
@click_config_file.configuration_option(settings.OPTION_FILE_FLAG)
def add_pinecone(ctx, **kwargs):
    VectorDbOnboardingService(
        config=ctx["config"],
        mc_client=create_mc_client(ctx),
        command_name="integrations add_pinecone",
    ).onboard_pinecone(**kwargs)
