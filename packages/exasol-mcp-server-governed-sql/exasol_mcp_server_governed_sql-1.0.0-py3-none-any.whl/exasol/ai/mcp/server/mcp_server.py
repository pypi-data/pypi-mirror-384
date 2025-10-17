
import re
from functools import cache
from typing import (
    Annotated,
    Any,
)

from fastmcp import FastMCP
from pydantic import Field
from sqlglot import (
    exp,
    parse_one,
)
from sqlglot.errors import ParseError

from exasol.ai.mcp.server.db_connection import DbConnection
from exasol.ai.mcp.server.keyword_search import keyword_filter
from exasol.ai.mcp.server.meta_query import (
    INFO_COLUMN,
    ExasolMetaQuery,
    MetaType,
)
from exasol.ai.mcp.server.parameter_parser import (
    FuncParameterParser,
    ScriptParameterParser,
)
from exasol.ai.mcp.server.parameter_pattern import (
    parameter_list_pattern,
    regex_flags,
)
from exasol.ai.mcp.server.server_settings import (
    ExaDbResult,
    McpServerSettings,
)


## ----- Text-to-SQL -----
## Added for Text-to-SQL option [DirkB @ Exasol: 2025-09-13]
## based on: Exasol MCP Server Version  1.0.0
##

from exasol.ai.mcp.server.text_to_sql_option.utilities.helpers import set_logging_label
from exasol.ai.mcp.server.text_to_sql_option.e_r_diagram import generate_e_r_diagram
from exasol.ai.mcp.server.text_to_sql_option.text_to_sql import t2s_start_process
from exasol.ai.mcp.server.text_to_sql_option.sql_history import text_to_sql_history
from exasol.ai.mcp.server.text_to_sql_option.intro.intro import (
    logger,
    LOGGING,
)

TABLE_USAGE = (
    "In an SQL query, the names of database objects, such as schemas, "
    "tables and columns should be enclosed in double quotes. "
    "A reference to a table should include a reference to its schema. "
    "The SELECT column list cannot have both the * and explicit column names."
)

SCHEMA_NAME_TYPE = Annotated[str, Field(description="name of the database schema")]

OPTIONAL_SCHEMA_NAME_TYPE = Annotated[
    str | None, Field(description="optional name of the database schema", default="")
]

KEYWORDS_TYPE = Annotated[list[str], "list of keywords to filter and order the result"]

TABLE_NAME_TYPE = Annotated[str, "name of the table"]

FUNCTION_NAME_TYPE = Annotated[str, "name of the function"]

SCRIPT_NAME_TYPE = Annotated[str, "name of the script"]


@cache
def _get_emits_pattern() -> re.Pattern:
    pattern = rf"EMITS\s*\({parameter_list_pattern}\)"
    return re.compile(pattern, flags=regex_flags)


def verify_query(query: str) -> bool:
    """
    Verifies that the query is a valid SELECT query.
    Declines any other types of statements including the SELECT INTO.
    """

    # Here is a fix for the SQLGlot deficiency in understanding the syntax of variadic
    # emit UDF. The EMITS clause in the SELECT statement is currently not recognised.
    # To let SQLGlot validate the query, this clause must be pinched away.
    query = _get_emits_pattern().sub("", query)

    try:
        ast = parse_one(query, read="exasol")
        if isinstance(ast, exp.Select):
            return "into" not in ast.args
        return False
    except ParseError:
        return False


def remove_info_column(result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Removes the column with extra information, collected for data filtering.
    """
    for row in result:
        if INFO_COLUMN in row:
            row.pop(INFO_COLUMN)
    return result


class ExasolMCPServer(FastMCP):
    """
    An Exasol MCP server based on FastMCP.

    Args:
        connection:
            pyexasol connection wrapper.
        config:
            The server configuration.
    """

    def __init__(self, connection: DbConnection, config: McpServerSettings) -> None:
        super().__init__(name="exasol-mcp")
        self.connection = connection
        self.meta_query = ExasolMetaQuery(config)

    @property
    def config(self) -> McpServerSettings:
        return self.meta_query.config

    def _execute_meta_query(
        self, query: str, keywords: list[str] | None = None
    ) -> ExaDbResult:
        """
        Executes a metadata query and returns the result as a list of dictionaries.
        Applies the keyword fitter if provided.
        Removes the column with extra information that could be added to the result
        to assist filtering. This is necessary to avoid polluting the LLM's context
        with data it doesn't need at the current stage.
        """
        result = self.connection.execute_query(query).fetchall()
        if keywords:
            result = keyword_filter(result, keywords, language=self.config.language)
        return ExaDbResult(remove_info_column(result))

    def list_schemas(self) -> ExaDbResult:
        if not self.config.schemas.enable:
            raise RuntimeError("The schema listing is disabled.")

        query = self.meta_query.get_metadata(MetaType.SCHEMA)
        return self._execute_meta_query(query)

    def find_schemas(self, keywords: KEYWORDS_TYPE) -> ExaDbResult:
        if not self.config.schemas.enable:
            raise RuntimeError("The schema listing is disabled.")

        query = self.meta_query.find_schemas()
        return self._execute_meta_query(query, keywords)

    def list_tables(self, schema_name: SCHEMA_NAME_TYPE) -> ExaDbResult:
        table_conf = self.config.tables
        view_conf = self.config.views
        if (not table_conf.enable) and (not view_conf.enable):
            raise RuntimeError("Both the table and the view listings are disabled.")

        query = "\nUNION\n".join(
            self.meta_query.get_metadata(meta_type, schema_name)
            for meta_type, conf in zip(
                [MetaType.TABLE, MetaType.VIEW], [table_conf, view_conf]
            )
            if conf.enable
        )
        return self._execute_meta_query(query)

    def find_tables(
        self, keywords: KEYWORDS_TYPE, schema_name: OPTIONAL_SCHEMA_NAME_TYPE
    ) -> ExaDbResult:
        if (not self.config.tables.enable) and (not self.config.views.enable):
            raise RuntimeError("Both the table and the view listings are disabled.")

        query = self.meta_query.find_tables(schema_name)
        return self._execute_meta_query(query, keywords)

    def list_functions(self, schema_name: SCHEMA_NAME_TYPE) -> ExaDbResult:
        if not self.config.functions.enable:
            raise RuntimeError("The function listing is disabled.")

        query = self.meta_query.get_metadata(MetaType.FUNCTION, schema_name)
        return self._execute_meta_query(query)

    def find_functions(
        self, keywords: KEYWORDS_TYPE, schema_name: OPTIONAL_SCHEMA_NAME_TYPE
    ) -> ExaDbResult:
        if not self.config.functions.enable:
            raise RuntimeError("The function listing is disabled.")

        query = self.meta_query.get_metadata(MetaType.FUNCTION, schema_name)
        return self._execute_meta_query(query, keywords)

    def list_scripts(self, schema_name: SCHEMA_NAME_TYPE) -> ExaDbResult:
        if not self.config.scripts.enable:
            raise RuntimeError("The script listing is disabled.")

        query = self.meta_query.get_metadata(MetaType.SCRIPT, schema_name)
        return self._execute_meta_query(query)

    def find_scripts(
        self, keywords: KEYWORDS_TYPE, schema_name: OPTIONAL_SCHEMA_NAME_TYPE
    ) -> ExaDbResult:
        if not self.config.scripts.enable:
            raise RuntimeError("The script listing is disabled.")

        query = self.meta_query.get_metadata(MetaType.SCRIPT, schema_name)
        return self._execute_meta_query(query, keywords)

    def describe_columns(
        self, schema_name: SCHEMA_NAME_TYPE, table_name: TABLE_NAME_TYPE
    ) -> ExaDbResult:
        """
        Returns the list of columns in the given table. Currently, this is a part of
        the `describe_table` tool, but it can be used independently in the future.
        """
        if not self.config.columns.enable:
            raise RuntimeError("The column listing is disabled.")

        query = self.meta_query.describe_columns(schema_name, table_name)
        return self._execute_meta_query(query)

    def describe_constraints(
        self, schema_name: SCHEMA_NAME_TYPE, table_name: TABLE_NAME_TYPE
    ) -> ExaDbResult:
        """
        Returns the list of constraints in the given table. Currently, this is a part
        of the `describe_table` tool, but it can be used independently in the future.
        """
        if not self.config.columns.enable:
            raise RuntimeError("The constraint listing is disabled.")

        query = self.meta_query.describe_constraints(schema_name, table_name)
        return self._execute_meta_query(query)

    def get_table_comment(self, schema_name: str, table_name: str) -> str | None:
        query = self.meta_query.get_table_comment(schema_name, table_name)
        comment_row = self.connection.execute_query(query).fetchone()
        if comment_row is None:
            return None
        table_comment = next(iter(comment_row.values()))
        if table_comment is None:
            return None
        return str(table_comment)

    def describe_table(
        self, schema_name: SCHEMA_NAME_TYPE, table_name: TABLE_NAME_TYPE
    ) -> dict[str, Any]:

        conf = self.config.columns
        columns = self.describe_columns(schema_name, table_name)
        constraints = self.describe_constraints(schema_name, table_name)
        table_comment = self.get_table_comment(schema_name, table_name)

        return {
            conf.columns_field: columns.result,
            conf.constraints_field: constraints.result,
            conf.table_comment_field: table_comment,
            conf.usage_field: TABLE_USAGE,
        }

    def describe_function(
        self, schema_name: SCHEMA_NAME_TYPE, func_name: FUNCTION_NAME_TYPE
    ) -> dict[str, Any]:
        parser = FuncParameterParser(connection=self.connection, settings=self.config)
        return parser.describe(schema_name, func_name)

    def describe_script(
        self, schema_name: SCHEMA_NAME_TYPE, script_name: SCRIPT_NAME_TYPE
    ) -> dict[str, Any]:
        parser = ScriptParameterParser(connection=self.connection, settings=self.config)
        return parser.describe(schema_name, script_name)

    def execute_query(
        self, query: Annotated[str, Field(description="select query")]
    ) -> ExaDbResult:
        if not self.config.enable_read_query:
            raise RuntimeError("Query execution is disabled.")
        if verify_query(query):
            result = self.connection.execute_query(query, snapshot=False).fetchall()
            return ExaDbResult(result)
        raise ValueError("The query is invalid or not a SELECT statement.")


    ## ----- Text-to-SQL -----
    ## Added for Text-to-SQL option [DirkB @ Exasol: 2025-09-12]
    ## based on: Exasol MCP Server Version  1.0.0
    ##

    def text_to_sql(self,
                    question: Annotated[str, Field(description="question")],
                    db_schema: Annotated[str, Field(description="Name of Database Schema")],
                    state):

        if not self.config.enable_text_to_sql:
            raise RuntimeError("Text-to-SQL option is disabled")

        """
        Starts the transformation process...
        """
        set_logging_label(logging=LOGGING, logger=logger, label="##### Starting Text-to-SQL")
        set_logging_label(logging=LOGGING, logger=logger, label=f"### Database schema: {db_schema}")
        set_logging_label(logging=LOGGING, logger=logger, label=f"### Question: {question}")

        state['question'] = question
        state['db_schema'] = db_schema

        state = t2s_start_process(state)

        return state

    def text_to_sql_history(self,
                            search_text: Annotated[str, Field(description="Search Text in question metadata field'", default="*")],
                            db_schema: Annotated[str, Field(description="Name of Database Schema", default="*")],
                            number_results: Annotated[int, Field(description="Number of records returned", default=5)],
                            ):

        result = text_to_sql_history(search_text=search_text, db_schema=db_schema, number_results=number_results)

        return result

    def text_to_sql_e_r_diagram(self,
                                db_schema: Annotated[str, Field(description="Name of Database Schema")]) -> str:

        result = generate_e_r_diagram(db_schema=db_schema)

        return result