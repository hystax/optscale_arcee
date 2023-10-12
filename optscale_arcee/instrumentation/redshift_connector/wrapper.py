from typing import List

from optscale_arcee.instrumentation.redshift_connector.stats import (
    count_queries,
)

SERVICE_PREFIX = "/* requestor: Optscale */"


def add_query_prefix(query_text: str) -> str:
    # add specific prefix to mark our service queries
    return f"{SERVICE_PREFIX} {query_text}"


def get_connection_info(cursor) -> tuple[int, int, str]:
    connection_info_query = """
    select
      pg_backend_pid() as session_id,
      current_user_id as user_id,
      current_database() as database"""
    cursor.execute(add_query_prefix(connection_info_query))
    result = cursor.fetchone()
    session_id, user_id, database = result
    return session_id, user_id, database


def get_queries_info(
    cursor, database: str, user_id: int, session_id: int
) -> List[dict]:
    # collect executed queries info in current session scope
    # excluding service queries
    query_string = """
    select
      database_name,
      start_time,
      end_time,
      trim(status) as status,
      trim(query_text) as query,
      elapsed_time,
      returned_rows,
      returned_bytes
    from
      sys_query_history
    where
      session_id = {session_id}
      and database_name = '{database}'
      and user_id = {user_id}
      and substring(query, 1, {prefix_len}) != '{prefix}'
    order by
      start_time asc
    """.format(
        database=database,
        session_id=session_id,
        user_id=user_id,
        prefix_len=len(SERVICE_PREFIX),
        prefix=SERVICE_PREFIX,
    )
    cursor.execute(add_query_prefix(query_string))

    # props in query order to map them to query result
    props = [
        "database",
        "start_time",
        "end_time",
        "status",
        "query",
        "duration",
        "returned_rows",
        "returned_bytes",
    ]

    def format_res(row: List) -> dict:
        res = dict(zip(props, row))
        res["start_time"] = res["start_time"].timestamp()
        if res.get("end_time"):
            res["end_time"] = res["end_time"].timestamp()
        return res

    return list(map(lambda r: format_res(r), cursor.fetchall()))


def close_wrapper(original, self):
    with self.cursor() as cursor:
        session_id, user_id, database = get_connection_info(cursor)
        queries_info = get_queries_info(
            cursor, user_id=user_id, database=database, session_id=session_id
        )
        count_queries(queries=queries_info)
    return original(self)
