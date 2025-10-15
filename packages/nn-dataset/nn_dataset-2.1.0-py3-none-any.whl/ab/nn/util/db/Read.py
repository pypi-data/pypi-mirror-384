from ab.nn.util.Const import main_columns, main_columns_ext
from ab.nn.util.Util import is_full_config, str_not_none
from ab.nn.util.db.Init import sql_conn, close_conn
from ab.nn.util.db.Write import init_population

init_population()


def query_cursor_cols_rows(*q) -> tuple[list, list]:
    conn, cursor = sql_conn()
    cursor.execute(*q)
    rows = cursor.fetchall()
    # Extract column names from cursor description.
    columns = [col[0] for col in cursor.description]
    close_conn(conn)
    return columns, rows


def query_rows(*q):
    conn, cursor = sql_conn()
    cursor.execute(*q)
    rows = cursor.fetchall()
    close_conn(conn)
    return [tuple([s for s in r]) for r in rows]


def query_cols_rows(q) -> tuple[list, list]:
    rows = query_rows(q)
    # Since each row is a tuple (with one element), you can simply use row[0]
    columns = [row[0] for row in rows]
    return columns, rows

def data(
    only_best_accuracy: bool = False,
    task: str | None = None,
    dataset: str | None = None,
    metric: str | None = None,
    nn: str | None = None,
    epoch: int | None = None,
    max_rows: int | None = None,
    sql: str | None = None,
) -> tuple[
    dict[str, int | float | str | dict[str, int | float | str]], ...
]:
    """
    Get the NN model code and all related statistics from the database.
    
    - If only_best_accuracy == True, then for every unique combination of 
      (task, dataset, metric, nn, epoch) only the row with the highest accuracy is returned.
    - If only_best_accuracy == False, all matching rows are returned.
    - Additionally, if any of the parameters (task, dataset, metric, nn, epoch) is not None,
      the results are filtered accordingly in the SQL query.
      
    Each returned dictionary has the following keys:
      - 'task': str
      - 'dataset': str
      - 'metric': str
      - 'metric_code': str    (source code from the metric table)
      - 'nn': str
      - 'nn_code': str        (source code from the nn table)
      - 'epoch': int
      - 'accuracy': float
      - 'duration': int
      - 'prm': dict           (hyperparameters, reconstructed from the "prm" table)
      - 'transform_code': str (source code from the transform table)
    """

    # Build filtering conditions based on provided parameters.
    params, where_clause = sql_where([task, dataset, metric, nn, epoch])

    # Execute a *single* query for the main stat rows
    conn, cur = sql_conn()
    try:
        if not only_best_accuracy:
            cur.execute(
                f"""WITH all_data AS (
                SELECT s.task, s.dataset, s.metric, m.code AS metric_code, m.id AS metric_id,
                       s.nn, n.code AS nn_code, n.id AS nn_id, s.epoch, s.accuracy, s.duration,
                       s.id   AS stat_id, s.prm  AS stat_prm,
                       t.code AS transform_code, t.id AS transform_id, s.transform
                FROM   stat s
                LEFT JOIN nn      n ON s.nn      = n.name
                LEFT JOIN metric  m ON s.metric  = m.name
                LEFT JOIN transform t ON s.transform = t.name
                {where_clause}
                ORDER BY s.task, s.dataset, s.metric, s.nn, s.epoch
                {str_not_none('LIMIT ', max_rows)})
                {sql if sql else 'SELECT * FROM all_data'}
                """,
                params,
            )
        else:
            cur.execute(
                f"""WITH all_data AS (
                WITH filtered AS (
                    SELECT s.task, s.dataset, s.metric, s.nn, s.transform,
                           s.epoch, s.accuracy, s.duration,
                           s.id AS stat_id, s.prm AS stat_prm
                    FROM   stat s
                    {where_clause}
                ),
                best AS (
                    SELECT task, dataset, metric, nn, epoch,
                           MAX(accuracy) AS max_accuracy
                    FROM   filtered
                    GROUP  BY task, dataset, metric, nn, epoch
                )
                SELECT f.task, f.dataset, f.metric, m.code AS metric_code,  m.id AS metric_id,
                       f.nn, n.code AS nn_code, n.id AS nn_id, f.epoch, f.accuracy, f.duration,
                       f.stat_id, f.stat_prm, t.code AS transform_code, t.id AS transform_id, f.transform
                FROM   filtered  f
                JOIN   best      b ON f.task = b.task
                                   AND f.dataset = b.dataset
                                   AND f.metric  = b.metric
                                   AND f.nn      = b.nn
                                   AND f.epoch   = b.epoch
                                   AND f.accuracy= b.max_accuracy
                LEFT JOIN nn      n ON f.nn      = n.name
                LEFT JOIN metric  m ON f.metric  = m.name
                LEFT JOIN transform t ON f.transform = t.name
                ORDER BY f.task, f.dataset, f.metric, f.nn, f.epoch
                {str_not_none('LIMIT ', max_rows)})
                {sql if sql else 'SELECT * FROM all_data'}""",
                params,
            )

        rows = cur.fetchall()
        columns = [c[0] for c in cur.description]

        if not rows:  # short-circuit for an empty result
            return tuple()

        # Bulk-load *all* hyperparameters for the retrieved stat_ids
        stat_id_idx = columns.index("stat_prm")
        uids = [r[stat_id_idx] for r in rows]

        from collections import defaultdict
        prm_by_uid: dict[str, dict[str, int | float | str]] = defaultdict(dict)

        if uids:
            CHUNK = 900                       # keep well below SQLite’s 999 limit
            for offset in range(0, len(uids), CHUNK):
                chunk = uids[offset : offset + CHUNK]
                placeholders = ",".join("?" * len(chunk))
                cur.execute(
                    f"SELECT uid, name, value FROM prm "
                    f"WHERE uid IN ({placeholders})",
                    chunk,
                )
                for uid, name, value in cur.fetchall():
                    prm_by_uid[uid][name] = value
        # Assemble the final result
        results: list[dict] = []
        for r in rows:
            rec = dict(zip(columns, r))
            uid = rec['stat_prm']
            rec['prm'] = prm_by_uid.get(uid, {})
            rec.pop('stat_id', None)
            rec.pop('transform', None)
            # ensure epoch is int
            try:
                rec['epoch'] = int(rec['epoch'])
            except (ValueError, TypeError):
                pass
            results.append(rec)

        return tuple(results)

    finally:
        close_conn(conn)

def sql_where(value_list):
    filters = []
    params = []
    for nm, v in zip(main_columns_ext, value_list):
        if v is not None:
            filters.append(f"s.{nm} = ?")
            params.append(v)
    return params, ' WHERE ' + ' AND '.join(filters) if filters else ''


def remaining_trials(config_ext, n_optuna_trials) -> tuple[int, int]:
    """
    Calculate the number of remaining Optuna trials for a given model configuration by querying the database.
    
    Instead of reading trial counts from a file, we query the database to count all trial records
    for the specified model (identified by model_name). The trial_file parameter is retained for
    interface compatibility but is not used.
    
    If n_optuna_trials is negative, its absolute value is taken as the required number of additional trials.
    Otherwise, the function computes:
    
        remaining_trials = max(0, n_optuna_trials - n_passed_trials)
    
    :param config_ext: Tuple of names (Task, Dataset, Metric, Model, Epoch).
    :param n_optuna_trials: Target number of trials. If negative, its absolute value specifies the additional trials required.
    :return: A tuple (n_remaining_trials, n_passed_trials) where:
             - n_remaining_trials is the number of new trials to run (or 0 if none remain).
             - n_passed_trials is the number of trials already recorded in the database for this model.
    """

    conn, cursor = sql_conn()
    params, where_clause = sql_where(config_ext)
    cursor.execute('SELECT COUNT(*) AS trial_count FROM stat s' + where_clause, params)
    row = cursor.fetchone()
    if row:
        # Convert the tuple row to a dict
        columns = [col[0] for col in cursor.description]
        row_dict = dict(zip(columns, row))
        n_passed_trials = row_dict.get("trial_count", 0)
    else:
        n_passed_trials = 0

    if n_optuna_trials < 0:
        n_remaining_trials = abs(n_optuna_trials)
    else:
        n_remaining_trials = max(0, n_optuna_trials - n_passed_trials)

    if n_passed_trials > 0:
        print(f"Model '{config_ext[-2]}' has {n_passed_trials} recorded trial(s), {n_remaining_trials} remaining.")

    close_conn(conn)
    return n_remaining_trials, n_passed_trials


def supported_transformers() -> list[str]:
    """
    Returns a list of all transformer names available in the database.
    
    The function queries the 'transform' table for all records and extracts the 'name'
    field from each row.
    """
    return query_cols_rows("SELECT name FROM transform")[0]


def unique_configs(patterns: list[tuple[str, ...]]) -> list[list[str]]:
    """
    Returns a list of unique configuration strings from the database that match at least one of the input patterns.
    
    A configuration string is constructed by concatenating the 'task', 'dataset', 'metric', and 'nn'
    fields from the 'stat' table using the configuration splitter defined in your constants.
    
    :param patterns: A tuple of configuration prefix patterns.
    :return: A list of unique configuration strings that start with any of the provided patterns.
    """
    matched_configs = []
    for pattern in patterns:
        pattern = list(filter(None, pattern))
        params, where_clause = sql_where(pattern)
        # params = params if not params else params[:-1] + [params[-1] + '*']
        rows = query_rows(f"SELECT DISTINCT {', '.join(main_columns)} FROM stat s" + where_clause, params)
        if not rows and is_full_config(pattern):
            rows = [tuple(pattern)]
        matched_configs = matched_configs + rows
    return list(set(matched_configs))
