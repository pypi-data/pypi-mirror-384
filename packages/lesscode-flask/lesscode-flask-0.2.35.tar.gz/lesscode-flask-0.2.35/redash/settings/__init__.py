import os
from importlib import import_module

from redash.settings.helpers import parse_boolean, array_from_string

# from funcy import distinct, remove

# Whether api calls using the json query runner will block private addresses
ENFORCE_PRIVATE_ADDRESS_BLOCK = parse_boolean(os.environ.get("REDASH_ENFORCE_PRIVATE_IP_BLOCK", "true"))
# requests
REQUESTS_ALLOW_REDIRECTS = parse_boolean(os.environ.get("REDASH_REQUESTS_ALLOW_REDIRECTS", "false"))

# Query Runners
default_query_runners = [
    # "redash.query_runner.athena",
    # "redash.query_runner.big_query",
    # "redash.query_runner.google_spreadsheets",
    # "redash.query_runner.graphite",
    # "redash.query_runner.mongodb",
    # "redash.query_runner.couchbase",
    "redash.query_runner.mysql",
    "redash.query_runner.pg",
    "redash.query_runner.kingbase",
    # "redash.query_runner.url",
    # "redash.query_runner.influx_db",
    # "redash.query_runner.influx_db_v2",
    "redash.query_runner.elasticsearch",
    # "redash.query_runner.elasticsearch2",
    # "redash.query_runner.amazon_elasticsearch",
    # "redash.query_runner.trino",
    # "redash.query_runner.presto",
    # "redash.query_runner.pinot",
    # "redash.query_runner.databricks",
    # "redash.query_runner.hive_ds",
    # "redash.query_runner.impala_ds",
    # "redash.query_runner.vertica",
    "redash.query_runner.clickhouse",
    # "redash.query_runner.tinybird",
    # "redash.query_runner.yandex_metrica",
    # "redash.query_runner.yandex_disk",
    # "redash.query_runner.rockset",
    # "redash.query_runner.treasuredata",
    # "redash.query_runner.sqlite",
    # "redash.query_runner.mssql",
    # "redash.query_runner.mssql_odbc",
    # "redash.query_runner.memsql_ds",
    # "redash.query_runner.jql",
    # "redash.query_runner.google_analytics",
    # "redash.query_runner.axibase_tsd",
    # "redash.query_runner.salesforce",
    # "redash.query_runner.query_results",
    # "redash.query_runner.prometheus",
    # "redash.query_runner.db2",
    # "redash.query_runner.druid",
    # "redash.query_runner.kylin",
    # "redash.query_runner.drill",
    # "redash.query_runner.uptycs",
    # "redash.query_runner.snowflake",
    # "redash.query_runner.phoenix",
    # "redash.query_runner.json_ds",
    # "redash.query_runner.cass",
    # "redash.query_runner.dgraph",
    # "redash.query_runner.azure_kusto",
    # "redash.query_runner.exasol",
    # "redash.query_runner.cloudwatch",
    # "redash.query_runner.cloudwatch_insights",
    # "redash.query_runner.corporate_memory",
    # "redash.query_runner.sparql_endpoint",
    # "redash.query_runner.excel",
    # "redash.query_runner.csv",
    # "redash.query_runner.databend",
    # "redash.query_runner.nz",
    # "redash.query_runner.arango",
    # "redash.query_runner.google_analytics4",
    # "redash.query_runner.google_search_console",
    # "redash.query_runner.ignite",
    # "redash.query_runner.oracle",
    # "redash.query_runner.e6data",
    # "redash.query_runner.risingwave",
]

enabled_query_runners = array_from_string(
    os.environ.get("REDASH_ENABLED_QUERY_RUNNERS", ",".join(default_query_runners))
)
additional_query_runners = array_from_string(os.environ.get("REDASH_ADDITIONAL_QUERY_RUNNERS", ""))
disabled_query_runners = array_from_string(os.environ.get("REDASH_DISABLED_QUERY_RUNNERS", ""))

try:
    funcy = import_module("funcy")
except ImportError as e:
    raise Exception(f"funcy is not exist,run:pip install funcy==2.0")

QUERY_RUNNERS = funcy.remove(
    set(disabled_query_runners),
    funcy.distinct(enabled_query_runners + additional_query_runners),
)
