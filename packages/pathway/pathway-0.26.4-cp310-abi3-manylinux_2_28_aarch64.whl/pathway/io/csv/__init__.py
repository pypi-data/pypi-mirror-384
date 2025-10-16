# Copyright © 2024 Pathway

from __future__ import annotations

from os import PathLike
from typing import Iterable, Literal

import pathway as pw
from pathway.internals.expression import ColumnReference
from pathway.internals.runtime_type_check import check_arg_types
from pathway.internals.table import Table
from pathway.internals.trace import trace_user_frame
from pathway.io._utils import CsvParserSettings, check_deprecated_kwargs


@check_arg_types
@trace_user_frame
def read(
    path: str | PathLike,
    *,
    schema: type[pw.Schema] | None = None,
    csv_settings: CsvParserSettings | None = None,
    mode: Literal["streaming", "static"] = "streaming",
    object_pattern: str = "*",
    with_metadata: bool = False,
    autocommit_duration_ms: int | None = 1500,
    name: str | None = None,
    max_backlog_size: int | None = None,
    debug_data=None,
    **kwargs,
) -> Table:
    """Reads a table from one or several files with delimiter-separated values.

    In case the folder is passed to the engine, the order in which files from
    the directory are processed is determined according to the modification time of
    files within this folder: they will be processed by ascending order of
    the modification time.

    Args:
        path: Path to the file or to the folder with files or
            `glob <https://en.wikipedia.org/wiki/Glob_(programming)>`_ pattern for the
            objects to be read. The connector will read the contents of all matching files as well
            as recursively read the contents of all matching folders.
        schema: Schema of the resulting table.
        csv_settings: Settings for the CSV parser.
        mode: Denotes how the engine polls the new data from the source. Currently
            "streaming" and "static" are supported. If set to "streaming" the engine will wait for
            the updates in the specified directory. It will track file additions, deletions, and
            modifications and reflect these events in the state. For example, if a file was deleted,
            "streaming" mode will also remove rows obtained by reading this file from the table. On
            the other hand, the "static" mode will only consider the available data and ingest all
            of it in one commit. The default value is "streaming".
        object_pattern: Unix shell style pattern for filtering only certain files in the
            directory. Ignored in case a path to a single file is specified. This value will be
            deprecated soon, please use glob pattern in ``path`` instead.
        with_metadata: When set to true, the connector will add an additional column
            named ``_metadata`` to the table. This JSON field may contain: (1) created_at - UNIX
            timestamp of file creation; (2) modified_at - UNIX timestamp of last modification;
            (3) seen_at is a UNIX timestamp of when they file was found by the engine;
            (4) owner - Name of the file owner (only for Un); (5) path - Full file path of the
            source row. (6) size - File size in bytes.
        autocommit_duration_ms: the maximum time between two commits. Every
            autocommit_duration_ms milliseconds, the updates received by the connector are
            committed and pushed into Pathway's computation graph.
        name: A unique name for the connector. If provided, this name will be used in
            logs and monitoring dashboards. Additionally, if persistence is enabled, it
            will be used as the name for the snapshot that stores the connector's progress.
        max_backlog_size: Limit on the number of entries read from the input source and kept
            in processing at any moment. Reading pauses when the limit is reached and resumes
            as processing of some entries completes. Useful with large sources that
            emit an initial burst of data to avoid memory spikes.
        debug_data: Static data replacing original one when debug mode is active.

    Returns:
        Table: The table read.

    Example:

    Consider you want to read a dataset, stored in the filesystem in a standard CSV
    format. The dataset contains data about pets and their owners.

    For the sake of demonstration, you can prepare a small dataset by creating a CSV file
    via a unix command line tool:

    .. code-block:: bash

        printf "id,owner,pet\\n1,Alice,dog\\n2,Bob,dog\\n3,Alice,cat\\n4,Bob,dog" > dataset.csv

    In order to read it into Pathway's table, you can first do the import and then
    use the `pw.io.csv.read` method:

    >>> import pathway as pw
    >>> class InputSchema(pw.Schema):
    ...   owner: str
    ...   pet: str
    >>> t = pw.io.csv.read("dataset.csv", schema=InputSchema, mode="static")

    Then, you can output the table in order to check the correctness of the read:

    >>> pw.debug.compute_and_print(t, include_id=False)  # doctest: +SKIP
    owner pet
    Alice dog
      Bob dog
    Alice cat
      Bob dog


    Now let's try something different. Consider you have site access logs stored in a
    separate folder in several files. For the sake of simplicity, a log entry contains
    an access ID, an IP address and the login of the user.

    A dataset, corresponding to the format described above can be generated, thanks to the
    following set of unix commands:

    .. code-block:: bash

        mkdir logs
        printf "id,ip,login\\n1,127.0.0.1,alice\\n2,8.8.8.8,alice" > logs/part_1.csv
        printf "id,ip,login\\n3,8.8.8.8,bob\\n4,127.0.0.1,alice" > logs/part_2.csv

    Now, let's see how you can use the connector in order to read the content of this
    directory into a table:

    >>> class InputSchema(pw.Schema):
    ...   ip: str
    ...   login: str
    >>> t = pw.io.csv.read("logs/", schema=InputSchema, mode="static")

    The only difference is that you specified the name of the directory instead of the
    file name, as opposed to what you had done in the previous example. It's that simple!

    But what if you are working with a real-time system, which generates logs all the time.
    The logs are being written and after a while they get into the log directory (this is
    also called "logs rotation"). Now, consider that there is a need to fetch the new files
    from this logs directory all the time. Would Pathway handle that? Sure!

    The only difference would be in the usage of `mode` flag. So the code
    snippet will look as follows:

    >>> t = pw.io.csv.read("logs/", schema=InputSchema, mode="streaming")

    With this method, you obtain a table updated dynamically. The changes in the logs would incur
    changes in the Business-Intelligence 'BI'-ready data, namely, in the tables you would like to output.
    article.
    """

    check_deprecated_kwargs(
        kwargs,
        ["poll_new_objects"],
    )

    return pw.io.fs.read(
        path,
        schema=schema,
        format="csv",
        mode=mode,
        object_pattern=object_pattern,
        with_metadata=with_metadata,
        csv_settings=csv_settings,
        autocommit_duration_ms=autocommit_duration_ms,
        json_field_paths=None,
        name=name,
        max_backlog_size=max_backlog_size,
        debug_data=debug_data,
        _stacklevel=5,
        **kwargs,
    )


@check_arg_types
@trace_user_frame
def write(
    table: Table,
    filename: str | PathLike,
    *,
    name: str | None = None,
    sort_by: Iterable[ColumnReference] | None = None,
) -> None:
    """Writes `table`'s stream of updates to a file in delimiter-separated values format.

    Args:
        table: Table to be written.
        filename: Path to the target output file.
        name: A unique name for the connector. If provided, this name will be used in
            logs and monitoring dashboards.
        sort_by: If specified, the output will be sorted in ascending order based on the
            values of the given columns within each minibatch. When multiple columns are provided,
            the corresponding value tuples will be compared lexicographically.

    Returns:
        None

    Example:

    In this simple example you can see how table output works.
    First, import Pathway and create a table:

    >>> import pathway as pw
    >>> t = pw.debug.table_from_markdown("age owner pet \\n 1 10 Alice dog \\n 2 9 Bob cat \\n 3 8 Alice cat")

    Consider you would want to output the stream of changes of this table. In order to do that
    you simply do:

    >>> pw.io.csv.write(t, "table.csv")

    Now, let's see what you have on the output:

    .. code-block:: bash

        cat table.csv

    .. code-block:: csv

        age,owner,pet,time,diff
        10,"Alice","dog",0,1
        9,"Bob","cat",0,1
        8,"Alice","cat",0,1

    The first three columns clearly represent the data columns you have. The column time
    represents the number of operations minibatch, in which each of the rows was read. In
    this example, since the data is static: you have 0. The diff is another
    element of this stream of updates. In this context, it is 1 because all three rows were read from
    the input. All in all, the extra information in ``time`` and ``diff`` columns - in this case -
    shows us that in the initial minibatch (``time = 0``), you have read three rows and all of
    them were added to the collection (``diff = 1``).
    """

    pw.io.fs.write(
        table,
        filename=filename,
        format="csv",
        name=name,
        sort_by=sort_by,
    )
