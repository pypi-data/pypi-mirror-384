# functions in this util take a string, do some manipulation of the string, and return it

from typing import Dict, List, Union
from datetime import datetime

import regex

# common regex
# 1: database optional
REGEX_OBJ_IDENTIFIER_1 = r"((?P<database>(\"\w+\")|(\w+))\s*\.)?\s*(?P<schema>(\"\w+\")|(\w+))\s*\.\s*?(?P<name>(\"\w+\")|(\w+)\b)(?!\.)"
# 2: database optional, schema optional
REGEX_OBJ_IDENTIFIER_2 = r"((?P<database>(\"\w+\")|(\w+))\s*\.)?\s*((?P<schema>(\"\w+\")|(\w+))\s*\.)?\s*(?P<name>(\"\w+\")|(\w+)\b)(?!\.)"
# 3: all required, dot after database is part of database name
REGEX_OBJ_IDENTIFIER_3 = r"(?P<database>(\"\w+\"\s*\.)|(\w+)\s*\.)\s*(?P<schema>(\"\w+\")|(\w+))\s*\.\s*(?P<name>(\"\w+\")|(\w+)\b)(?!\.)"

def _replace_with_whitespace(matchobj):
    """
    Replace all characters in regex match object with spaces (preserve linebreaks)
    """
    return regex.sub(r"[^\n]", " ", matchobj.group(0))


def _remove_characters_retain_linebreaks(matchobj):
    """
    Remove all characters in regex match object, but keep line breaks
    """
    return regex.sub(r"[^\n]", "", matchobj.group(0))


def remove_comment(ddl: str, keep_whitespace=False) -> str:
    """
    Remove SQL comments from a string.
    """
    if ddl is None:
        return None
    expression_blockcomment = regex.compile(
        r"('.*?'(*SKIP)(?!))|(\$\$.*?\$\$(*SKIP)(?!))|(\/\*(?:(?!\/\*).)*?\*\/)",
        regex.IGNORECASE | regex.DOTALL,
    )
    expression_linecomment = regex.compile(
        r"('.*?'(*SKIP)(?!))|(\$\$.*?\$\$(*SKIP)(?!))|(--.*?(\n|$))|(\/\/.*?(\n|$))",
        regex.IGNORECASE | regex.DOTALL,
    )

    replace_function = (
        _replace_with_whitespace
        if keep_whitespace
        else _remove_characters_retain_linebreaks
    )
    old_ddl = ddl
    while True:
        cleaned_ddl = expression_blockcomment.sub(replace_function, old_ddl)
        cleaned_ddl = expression_linecomment.sub(replace_function, cleaned_ddl)
        if cleaned_ddl == old_ddl:
            break
        old_ddl = cleaned_ddl

    return cleaned_ddl


def remove_comment_after_statement(ddl: str) -> str:
    """
    Removes any comments after the statement, e.g.
        CREATE VIEW X AS SELECT 1 INT; // will be removed

        CREATE VIEW X AS SELECT 1 INT; -- will be removed

        CREATE VIEW X AS SELECT 1 INT; /* will be removed */

        CREATE VIEW X AS SELECT 1 INT;
        // will be removed

        CREATE VIEW X AS SELECT 1 INT;
        /* will be removed */
    """
    ddl_without_comment = remove_comment(ddl, keep_whitespace=True)
    return ddl[0 : len(ddl_without_comment.rstrip())]


def remove_comment_before_statement(ddl: str) -> str:
    """
    Removes any comments before the statement, e.g.
        // will be removed
        CREATE VIEW X AS SELECT 1 INT;

        -- will be removed
        CREATE VIEW X AS SELECT 1 INT;

        /* will be removed */ CREATE VIEW X AS SELECT 1 INT;

        /* will be removed */
        CREATE VIEW X AS SELECT 1 INT;
    """
    ddl_without_comment = remove_comment(ddl, keep_whitespace=True)
    return ddl[len(ddl) - len(ddl_without_comment.lstrip()) :]


def remove_text_in_quotes(statement: str) -> str:
    """
        Removes everything in single quotes ('remove') and double dollars ($$remove$$)
    Args:
        statement: str - the whole statement (multiple lines)
    Returns:
        str - the statement with any text in single quotes removed
    """
    pattern_quotes = regex.compile(
        r"(?<!\\)'[^\\\']*(?:\\.[^\\\']*)*[^\\]??'", regex.IGNORECASE | regex.DOTALL
    )
    pattern_dollars = regex.compile(
        r"(?<!\\)\$\$.*?[^\\]??\$\$", regex.IGNORECASE | regex.DOTALL
    )

    statement = pattern_quotes.sub("''", statement)
    statement = pattern_dollars.sub(r"$$$$", statement)

    return statement


def split_parameters_string(parameter_string: str) -> List[str]:
    """
    Take a list of parameters and return theses parameters as a list.
    Example: '(VARCHAR(20), INTEGER, NUMBER(38,0))' returns ['VARCHAR(20)', 'INTEGER', 'NUMBER(38,0)']
    """
    if parameter_string.startswith("(") and parameter_string.endswith(")"):
        parameter_string = parameter_string[1:-1]

    if parameter_string == "":
        return []

    new_delimiter = "@@@"
    parameter_string_replaced_commas = regex.sub(
        r",(?=[^\)]*(?:\(|$))", new_delimiter, parameter_string
    )

    split_parameters = parameter_string_replaced_commas.split(new_delimiter)
    return [s.strip() for s in split_parameters]


def add_create_or_replace(ddl: str) -> str:
    """
    Given a ddl statement, add 'OR REPLACE' if not already in the ddl statement.

    Return error if CREATE could not be found.
    """
    ddl_clean = remove_comment_before_statement(ddl).strip()
    ddl_result, count = regex.subn(
        r"^CREATE\s+(OR\s+REPLACE\s+)?",
        "CREATE OR REPLACE ",
        ddl_clean,
        count=1,
        flags=regex.IGNORECASE,
    )
    if count == 0:
        raise ValueError(
            f"FAILED to find CREATE in DDL. Is this a valid DDL statement?\n{ddl}"
        )
    return ddl_result


def remove_create_or_replace(ddl: str) -> str:
    """
    Given a ddl statement, remove 'OR REPLACE' if it appears in the ddl statement.

    Return error if CREATE could not be found.
    """
    ddl_clean = remove_comment_before_statement(ddl).strip()
    ddl_result, count = regex.subn(
        r"^CREATE\s+(OR\s+REPLACE\s+)?",
        "CREATE ",
        ddl_clean,
        count=1,
        flags=regex.IGNORECASE,
    )
    if count == 0:
        raise ValueError(
            f"FAILED to find CREATE in DDL. Is this a valid DDL statement?\n{ddl}"
        )
    return ddl_result


def remove_prefix(s, prefix):
    """
    If a string s starts with prefix, remove that prefix. Else, return the string s.

    Based on https://stackoverflow.com/a/16891418
    TODO: In Python 3.9, there is a native function for this
    """
    if s.startswith(prefix):
        return s[len(prefix) :]
    return s


def string_replace_by_dict(s: str, string_replace_dict: Dict[str, str]):
    """
    Given a string s, replace all occurences of the given keys in the dict with the values.

    Example: s = 'Acedeploy is %%var%%.', string_replace_dict = {'var': 'cool'} will return 'Acedeploy is cool.'
    """
    for k, v in string_replace_dict.items():
        s = s.replace(f"%%{k}%%", v)
    return s


def convert_python_variable_to_snowflake_value(v: Union[str, int, bool, list]) -> str:
    """
    Given a variable v, return the representation for Snowflake.

    Examples:
        v: str = "hello world" --> "'hello world'"
        v: int = 12 --> "12"
        v: bool = True --> "TRUE"
    """
    if isinstance(v, type(None)):
        return "NONE"
    if isinstance(v, str):
        return f"'{escape_string_for_snowflake(v.encode('unicode_escape').decode('utf-8'))}'"  # encode and decode to preserve, e.g. \n
    if isinstance(v, bool):
        return str(v).upper()
    if isinstance(v, int):  # order matters: True is both of type bool and int
        return str(v)
    if isinstance(v, list):
        return f"({', '.join([convert_python_variable_to_snowflake_value(vv) for vv in v])})"
    raise ValueError(
        f"The type of [ '{v}' ] is [ '{type(v)}' ] which can not be converted to a Snowflake representation."
    )


def escape_string_for_snowflake(s: str) -> str:
    """
    Escape a string so that it can be used in as a snowflake string.

    Example: s = "hello 'world'" --> "hello ''world''"
             allows use in, e.g., ...SET COMMENT = 'hello ''world''';
    """
    return s.replace("'", "''")

def compare_strings_ignore_whitespace_and_case(str1: str, str2: str) -> bool:
    """
    Compare two strings and ignore new-lines and whitespaces.
    Return True if the strings are equal.
    """
    
    lines1 = [line.strip() for line in str1.split('\n')]
    lines2 = [line.strip() for line in str2.split('\n')]
    str1 = ''.join(lines1)
    str2 = ''.join(lines2)

    str1 = str1.replace(" ", "").replace("\n", "").lower()
    str2 = str2.replace(" ", "").replace("\n", "").lower()
    
    return str1 == str2


def add_copy_grants(view_ddl: str) -> str:
    """
    Given a ddl statement of a view, add 'COPY GRANTS'.
    Removes SQL comments from the view ddl.
    """
    ddl_clean = remove_comment(view_ddl).strip()

    # check if COPY GRANTS was already added
    regex_copy_grants = fr"\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:SECURE\s+)?(?:RECURSIVE\s+)?VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?{REGEX_OBJ_IDENTIFIER_1}\s+(?:COPY\s+GRANTS\s+)"
    match_copy_grants = regex.match(regex_copy_grants, ddl_clean, flags=regex.IGNORECASE)

    if match_copy_grants:
        return ddl_clean
    else:
        # add COPY GRANTS
        regex_view = fr"\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:SECURE\s+)?(?:RECURSIVE\s+)?VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?{REGEX_OBJ_IDENTIFIER_1}"
        match = regex.match(regex_view, ddl_clean, flags=regex.IGNORECASE)
        if match:
            view_signature = match[0]
        else:
            raise ValueError(
                f"FAILED to identify view signature in DDL. Is this a valid DDL statement?\n{view_ddl}"
            )
        added_copy_grants = f"{view_signature} COPY GRANTS "
        view_ddl_result, count = regex.subn(
            regex_view,
            added_copy_grants,
            ddl_clean,
            count=1,
            flags=regex.IGNORECASE,
        )

        if count == 0:
            raise ValueError(
                f"FAILED to identify view signature in DDL. Is this a valid DDL statement?\n{view_ddl}"
            )
        return view_ddl_result
    
def fix_view_definition(view_definition: str) -> str:
    """
    This temporarily fixes a Snowflake Bug when retrieving the VIEW_DEFINITION from the INFORMATION_SCHEMA.VIEWS after cloning the schema that contains the view.
    Removes SQL comments from the view definition.
    """

    ddl_clean = remove_comment(view_definition).strip()
       
    regex_view = r'\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:SECURE\s+)?(?:RECURSIVE\s+)?VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<identifier>\"\w+.\w+.\w+\")(?!\s*\.)'

    match = regex.match(regex_view, ddl_clean, flags=regex.IGNORECASE)

    if match:

        fixed_match = match[0].replace(match["identifier"], match["identifier"][1:-1])

        fixed_view_definition = ddl_clean.replace(match[0], fixed_match)

    else:
        fixed_view_definition = view_definition

    return fixed_view_definition

def sub_object_name(object_type: str, file_content: str, old_name: str, new_name: str) -> str:
    """
    Given a ddl, replace the object name with a new name.
    """
    return regex.sub(
        f"{object_type}\\s+{regex.escape(old_name)}",
        f"{object_type} {new_name}",
        file_content,
        count=1,
        flags=regex.IGNORECASE
    )


def get_now_string(format: str="%Y%m%d_%H%M%S_%f"):
    return datetime.now().strftime(format)
