# Monte Carlo CLI

Monte Carlo's Alpha CLI!

## Installation

Requires Python 3.9 or greater. Normally you can install and update using `pip`. For instance:

```shell
pip install virtualenv
virtualenv venv
. venv/bin/activate

pip install -U montecarlodata
```

Developers of the CLI can use:

```shell
pip install virtualenv
make install
. venv/bin/activate
pre-commit install
```

Either way confirm the installation by running:

```shell
montecarlo --version
```

If the Python requirement does not work for you please reach out to `support@montecarlodata.com`. Docker is an option.

## Quick start

First time users can configure the tool by following the onscreen prompts:

```shell
montecarlo configure
```

MCD tokens can be generated from the [dashboard](https://getmontecarlo.com/get-token).

Use the `--help` flag for details on any advanced options (e.g. creating multiple montecarlo profiles) or
see docs [here][cli-docs].

That's it! You can always validate your connection with:

```shell
montecarlo validate
```

## User settings

Any configuration set by `montecarlo configure` can be found in `~/.mcd/` by default.

The MCD ID and Token can be overwritten, or even set, by the environment:

- `MCD_DEFAULT_API_ID`
- `MCD_DEFAULT_API_TOKEN`

These two are required either as part of `configure` or as environment variables.

The following values can also be set by the environment:

- `MCD_API_ENDPOINT` - Overwrite the default API endpoint
- `MCD_VERBOSE_ERRORS` - Enable verbose logging on errors (default=false)

## Help

Documentation for commands, options, and arguments can be found [here][cli-docs].

You can also use `montecarlo help` to echo all help text or use the `--help` flag on any command.

## Examples

### Using Docker from a local installation

```shell
docker build -t montecarlo .
docker run -e MCD_DEFAULT_API_ID='<ID>' -e MCD_DEFAULT_API_TOKEN='<TOKEN>' montecarlo --version
```

Replace `--version` with any sub-commands or options. If interacting with files those directories will probably need to be mounted too.

### Configure a named profile with custom config-path

```shell
$ montecarlo configure --profile-name zeus --config-path .
Key ID: 1234
Secret:

$ cat ./profiles.ini
[zeus]
mcd_id = 1234
mcd_token = 5678
```

### List active integrations

```shell
$ montecarlo integrations list
╒══════════════════╤══════════════════════════════════════╤══════════════════════════════════╕
│ Integration      │ ID                                   │ Created on (UTC)                 │
╞══════════════════╪══════════════════════════════════════╪══════════════════════════════════╡
│ Odin             │ 58005657-2914-4701-9a11-260ac425b14e │ 2021-01-02T01:30:52.806602+00:00 │
├──────────────────┼──────────────────────────────────────┼──────────────────────────────────┤
│ Thor             │ 926816bd-ab17-4f95-a953-fa14482c59de │ 2021-01-02T01:31:19.892205+00:00 │
├──────────────────┼──────────────────────────────────────┼──────────────────────────────────┤
│ Loki             │ 1cf1dc0d-d8ec-4c85-8e64-57ab2ad8e023 │ 2021-01-02T01:32:37.709747+00:00 │
╘══════════════════╧══════════════════════════════════════╧══════════════════════════════════╛
```

### Apply monitors configuration

```shell
$ montecarlo monitors apply --namespace my-monitors

Gathering monitor configuration files.
- models/customer_success/schema.yml - Embedded monitor configuration found.
- models/customer_success/schema.yml - Monitor configuration found.
- models/lineage/schema.yml - Embedded monitor configuration found.

Modifications:
- ResourceModificationType.UPDATE - Monitor: type=stats, table=analytics:prod.customer_360
- ResourceModificationType.UPDATE - Monitor: type=categories, table=analytics:prod.customer_360
- ResourceModificationType.UPDATE - Monitor: type=stats, table=analytics:prod_lineage.lineage_nodes
- ResourceModificationType.UPDATE - Freshness SLI: table=analytics:prod.customer_360, freshness_threshold=30
```

### Import DBT manifest

```shell
$ montecarlo import dbt-manifest --dbt-manifest-file target/manifest.json

Importing DBT objects into Monte Carlo catalog. please wait...

Imported a total of 51 DBT objects into Monte Carlo catalog.
```

## Tests and Releases

Locally `make test` will run all tests. CircleCI manages all testing for deployment.

To publish a new release, navigate to [Releases](https://github.com/monte-carlo-data/cli/releases) in the GitHub repo and then:

- Click "Draft a new release"
- In the "Choose a tag" dropdown, type the new version number, for example `v1.2.3` and click "Create a new tag"
- Follow the format from previous releases for the description
- Leave "Set as the latest release" checked
- Click "Publish release"
- CircleCI will take care of publishing a new package to [PyPI](https://pypi.org/project/montecarlodata/) and generating documentation.

## License

Apache 2.0 - See the [LICENSE](http://www.apache.org/licenses/LICENSE-2.0) for more information.

[cli-docs]: https://clidocs.getmontecarlo.com/
