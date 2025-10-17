import logging

import select

try:
    import pg8000

    enabled = True
except ImportError:
    enabled = False
    logging.error(f"pg8000 is not exist,run:pip install pg8000==1.31.2")

from redash.query_runner import (
    TYPE_BOOLEAN,
    TYPE_DATE,
    TYPE_DATETIME,
    TYPE_FLOAT,
    TYPE_INTEGER,
    TYPE_STRING,
    BaseSQLQueryRunner,
    InterruptException,
    # JobTimeoutException,
    register, QueryExecutionError,
)

logger = logging.getLogger(__name__)

# try:
#     import boto3
#
#     IAM_ENABLED = True
# except ImportError:
#     IAM_ENABLED = False

types_map = {
    20: TYPE_INTEGER,
    21: TYPE_INTEGER,
    23: TYPE_INTEGER,
    700: TYPE_FLOAT,
    1700: TYPE_FLOAT,
    701: TYPE_FLOAT,
    16: TYPE_BOOLEAN,
    1082: TYPE_DATE,
    1182: TYPE_DATE,
    1114: TYPE_DATETIME,
    1184: TYPE_DATETIME,
    1115: TYPE_DATETIME,
    1185: TYPE_DATETIME,
    1014: TYPE_STRING,
    1015: TYPE_STRING,
    1008: TYPE_STRING,
    1009: TYPE_STRING,
    2951: TYPE_STRING,
    1043: TYPE_STRING,
    1002: TYPE_STRING,
    1003: TYPE_STRING,
}


def full_table_name(schema, name):
    if "." in name:
        name = '"{}"'.format(name)

    return "{}.{}".format(schema, name)


def build_schema(query_result, schema):
    # By default we omit the public schema name from the table name. But there are
    # edge cases, where this might cause conflicts. For example:
    # * We have a schema named "main" with table "users".
    # * We have a table named "main.users" in the public schema.
    # (while this feels unlikely, this actually happened)
    # In this case if we omit the schema name for the public table, we will have
    # a conflict.
    table_names = set(
        map(
            lambda r: full_table_name(r["table_schema"], r["table_name"]),
            query_result["rows"],
        )
    )

    for row in query_result["rows"]:
        if row["table_schema"] != "public":
            table_name = full_table_name(row["table_schema"], row["table_name"])
        else:
            if row["table_name"] in table_names:
                table_name = full_table_name(row["table_schema"], row["table_name"])
            else:
                table_name = row["table_name"]

        if table_name not in schema:
            schema[table_name] = {"name": table_name, "columns": []}

        column = row["column_name"]
        if row.get("data_type") is not None:
            column = {"name": row["column_name"], "type": row["data_type"]}

        schema[table_name]["columns"].append(column)


class KingBase(BaseSQLQueryRunner):
    noop_query = "SELECT 1"

    @classmethod
    def configuration_schema(cls):
        return {
            "type": "object",
            "properties": {
                "user": {"type": "string"},
                "passwd": {"type": "string"},
                "host": {"type": "string", "default": "127.0.0.1"},
                "port": {"type": "number", "default": 5432},
                "db": {"type": "string", "title": "Database Name"}
            },
            "order": ["host", "port", "user", "password"],
            "required": ["dbname"],
            "secret": ["password"]
        }

    def create_options(self, configuration):
        options = {
            "user": configuration.get("username"),
            "passwd": configuration.get("password"),
            "host": configuration.get("host"),
            "port": configuration.get("port"),
            "db": configuration.get("dbname"),
        }
        return options

    def get_password_field(self):
        return "passwd"

    @classmethod
    def type(cls):
        return "kingbase"

    def _get_definitions(self, schema, query):
        results, error = self.run_query(query, None)

        if error is not None:
            self._handle_run_query_error(error)

        build_schema(results, schema)

    def _get_tables(self, schema):
        """
        relkind constants per https://www.postgresql.org/docs/10/static/catalog-pg-class.html
        r = regular table
        v = view
        m = materialized view
        f = foreign table
        p = partitioned table (new in 10)
        ---
        i = index
        S = sequence
        t = TOAST table
        c = composite type
        """

        query = """
        SELECT s.nspname as table_schema,
               c.relname as table_name,
               a.attname as column_name,
               null as data_type
        FROM pg_class c
        JOIN pg_namespace s
        ON c.relnamespace = s.oid
        AND s.nspname NOT IN ('pg_catalog', 'information_schema')
        JOIN pg_attribute a
        ON a.attrelid = c.oid
        AND a.attnum > 0
        AND NOT a.attisdropped
        WHERE c.relkind IN ('m', 'f', 'p')
        AND has_table_privilege(s.nspname || '.' || c.relname, 'select')
        AND has_schema_privilege(s.nspname, 'usage')

        UNION

        SELECT table_schema,
               table_name,
               column_name,
               data_type
        FROM information_schema.columns
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        """

        self._get_definitions(schema, query)

        return list(schema.values())

    def _get_connection(self):
        params = dict(
            host=self.configuration.get("host", ""),
            user=self.configuration.get("user", ""),
            password=self.configuration.get("passwd", ""),
            database=self.configuration["db"],
            port=self.configuration.get("port", 54321),
        )

        connection = pg8000.connect(**params)

        return connection

    @classmethod
    def enabled(cls):
        return enabled

    def run_query(self, query, user):
        logger.debug("KingBase is about to execute query: %s", query)
        connection = self._get_connection()

        cursor = connection.cursor()

        try:
            cursor.execute(query)
            #    _wait(connection)
            connection.commit()
            if cursor.description is not None:
                columns = self.fetch_columns([(i[0], types_map.get(i[1], None)) for i in cursor.description])
                rows = [dict(zip((column["name"] for column in columns), row)) for row in cursor]

                data = {"columns": columns, "rows": rows}
                error = None
            elif isinstance(cursor.rowcount, int) and cursor.rowcount >= 0:
                data = cursor.rowcount
                error = None
            else:
                error = QueryExecutionError("Query completed but it returned no data.")
                data = None
        except (select.error, OSError):
            error = QueryExecutionError("Query interrupted. Please retry.")
            data = None
        except pg8000.DatabaseError as e:
            error = e
            data = None
        # except (KeyboardInterrupt, InterruptException, JobTimeoutException):
        except (KeyboardInterrupt, InterruptException):
            connection.cancel()
            error = QueryExecutionError("Query interrupted. Please retry.")
            data = None
        except Exception as e:
            error = e
            data = None
        finally:
            connection.close()

        return data, error

    def exec(self, query, user):
        logger.debug("KingBase is about to execute query: %s", query)
        connection = self._get_connection()

        cursor = connection.cursor()

        cursor.execute(query)
        #    _wait(connection)
        connection.commit()

        return True, None


register(KingBase)
