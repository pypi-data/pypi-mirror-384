# Copyright © 2024 Pathway

from __future__ import annotations

from typing import Any, Literal

from pathway.internals import api, datasource
from pathway.internals._io_helpers import AwsS3Settings
from pathway.internals.runtime_type_check import check_arg_types
from pathway.internals.schema import Schema
from pathway.internals.table import Table
from pathway.internals.table_io import table_from_datasource
from pathway.internals.trace import trace_user_frame
from pathway.io._utils import (
    CsvParserSettings,
    _get_unique_name,
    construct_schema_and_data_format,
    internal_connector_mode,
    internal_read_method,
)


class DigitalOceanS3Settings:
    """Stores Digital Ocean S3 connection settings.

    Args:
        bucket_name: Name of Digital Ocean S3 bucket.
        access_key: Access key for the bucket.
        secret_access_key: Secret access key for the bucket.
        region: Region of the bucket.
    """

    @trace_user_frame
    def __init__(
        self,
        bucket_name,
        *,
        access_key=None,
        secret_access_key=None,
        region=None,
    ):
        self.bucket_name = bucket_name
        self.access_key = access_key
        self.secret_access_key = secret_access_key
        self.region = region

    def create_aws_settings(self):
        return AwsS3Settings(
            endpoint=None,
            bucket_name=self.bucket_name,
            access_key=self.access_key,
            secret_access_key=self.secret_access_key,
            with_path_style=False,
            region=self.region,
        )


class WasabiS3Settings:
    """Stores Wasabi S3 connection settings.

    Args:
        bucket_name: Name of Wasabi S3 bucket.
        access_key: Access key for the bucket.
        secret_access_key: Secret access key for the bucket.
        region: Region of the bucket.
    """

    @trace_user_frame
    def __init__(
        self,
        bucket_name,
        *,
        access_key=None,
        secret_access_key=None,
        region=None,
    ):
        self.bucket_name = bucket_name
        self.access_key = access_key
        self.secret_access_key = secret_access_key
        self.region = region

    def create_aws_settings(self):
        return AwsS3Settings(
            endpoint=None,
            bucket_name=self.bucket_name,
            access_key=self.access_key,
            secret_access_key=self.secret_access_key,
            with_path_style=False,
            region=f"wa-{self.region}",
        )


@check_arg_types
@trace_user_frame
def read(
    path: str,
    format: Literal["csv", "json", "plaintext", "plaintext_by_object", "binary"],
    *,
    aws_s3_settings: AwsS3Settings | None = None,
    schema: type[Schema] | None = None,
    mode: Literal["streaming", "static"] = "streaming",
    with_metadata: bool = False,
    csv_settings: CsvParserSettings | None = None,
    json_field_paths: dict[str, str] | None = None,
    path_filter: str | None = None,
    downloader_threads_count: int | None = None,
    autocommit_duration_ms: int | None = 1500,
    name: str | None = None,
    max_backlog_size: int | None = None,
    debug_data: Any = None,
    _stacklevel: int = 1,
    **kwargs,
) -> Table:
    """Reads a table from one or several objects in Amazon S3 bucket in the given
    format.

    In case the prefix of S3 path is specified, and there are several objects lying
    under this prefix, their order is determined according to their modification times:
    the smaller the modification time is, the earlier the file will be passed to the
    engine.

    Args:
        path: Path to an object or to a folder of objects in Amazon S3 bucket.
        aws_s3_settings: Connection parameters for the S3 account and the bucket.
        format: Format of data to be read. Currently ``csv``, ``json``, ``plaintext``,
            ``plaintext_by_object`` and ``binary`` formats are supported. The difference
            between ``plaintext`` and ``plaintext_by_object`` is how the input is
            tokenized: if the ``plaintext`` option is chosen, it's split by the newlines.
            Otherwise, the files are split in full and one row will correspond to one
            file. In case the ``binary`` format is specified, the data is read as raw
            bytes without UTF-8 parsing.
        schema: Schema of the resulting table. Not required for ``plaintext_by_object``
            and ``binary`` formats: if they are chosen, the contents of the read objects
            are stored in the column ``data``.
        mode: If set to ``streaming``, the engine waits for the new objects under the
            given path prefix. Set it to ``static``, it only considers the available
            data and ingest all of it. Default value is ``streaming``.
        with_metadata: When set to true, the connector will add an additional column
            named ``_metadata`` to the table. This column will be a JSON field that will
            contain an optional field ``modified_at``. Additionally, the column will also
            have an optional field named ``owner`` containing an ID of the object owner.
            Finally, the column will also contain a field named ``path`` that will show
            the full path to the object within a bucket from where a row was filled.
        csv_settings: Settings for the CSV parser. This parameter is used only in case
            the specified format is ``csv``.
        json_field_paths: If the format is ``json``, this field allows to map field names
            into path in the read json object. For the field which require such mapping,
            it should be given in the format ``<field_name>: <path to be mapped>``,
            where the path to be mapped needs to be a
            `JSON Pointer (RFC 6901) <https://www.rfc-editor.org/rfc/rfc6901>`_.
        path_filter: A wildcard pattern used to match full object paths. Supports ``*``
            (any number of any characters, including none) and ``?`` (any single character).
            If specified, only paths matching this pattern will be included. Applied as an
            additional filter after the initial ``path`` matching.
        downloader_threads_count: The number of threads created to download the contents
            of the bucket under the given path. It defaults to the number of cores
            available on the machine. It is recommended to increase the number of
            threads if your bucket contains many small files.
        autocommit_duration_ms: The maximum time between two commits. Every
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

    Let's consider an object store, which is hosted in Amazon S3. The store contains
    datasets in the respective bucket and is located in the region ``eu-west-3``. The goal
    is to read the dataset, located under the path ``animals/`` in this bucket.

    Let's suppose that the format of the dataset rows is jsonlines.

    Then, the code may look as follows:

    >>> import os
    >>> import pathway as pw
    >>> class InputSchema(pw.Schema):
    ...   owner: str
    ...   pet: str
    >>> t = pw.io.s3.read(
    ...     "animals/",
    ...     aws_s3_settings=pw.io.s3.AwsS3Settings(
    ...         bucket_name="datasets",
    ...         region="eu-west-3",
    ...         access_key=os.environ["S3_ACCESS_KEY"],
    ...         secret_access_key=os.environ["S3_SECRET_ACCESS_KEY"],
    ...     ),
    ...     format="json",
    ...     schema=InputSchema,
    ... )

    In case you are dealing with a public bucket, the parameters ``access_key`` and
    ``secret_access_key`` can be omitted. In this case, the read part will look as
    follows:

    >>> t = pw.io.s3.read(
    ...     "animals/",
    ...     aws_s3_settings=pw.io.s3.AwsS3Settings(
    ...         bucket_name="datasets",
    ...         region="eu-west-3",
    ...     ),
    ...     format="json",
    ...     schema=InputSchema,
    ... )

    It's not obligatory to choose one of the available input tokenizations. You
    can also read the objects in full, thus creating a ``pw.Table`` where each row
    corresponds to a single object read in full. To do that, you need to specify
    ``binary`` as a format:

    >>> t = pw.io.s3.read(
    ...     "animals/",
    ...     aws_s3_settings=pw.io.s3.AwsS3Settings(
    ...         bucket_name="datasets",
    ...         region="eu-west-3",
    ...     ),
    ...     format="binary",
    ... )

    Similarly you can also enable the UTF-8 parsing of the objects read, resulting in
    having a table of plaintext files:

    >>> t = pw.io.s3.read(
    ...     "animals/",
    ...     aws_s3_settings=pw.io.s3.AwsS3Settings(
    ...         bucket_name="datasets",
    ...         region="eu-west-3",
    ...     ),
    ...     format="plaintext_by_object",
    ... )

    Note that it's also possible to infer the bucket name and credentials from the path,
    if it's given in a full form with ``s3://`` prefix. For instance, in the example above
    you can also connect as follows:

    >>> t = pw.io.s3.read("s3://datasets/animals", format="binary")  # doctest: +SKIP

    Note that you need to be logged in S3 for the credentials auto-detection to work.

    Finally, you can also read the data from self-hosted S3 buckets, or generally those
    where the endpoint path differs from the standard AWS paths. To do that, you can make
    use of the ``endpoint`` field of ``pw.io.s3.AwsS3Settings`` class. One of the natural
    examples for that may be the min.io S3 buckets. That is, if you have a min.io S3
    bucket instance, one of the ways to connect to it via this connector would be the
    first to create the settings object with the custom endpoint and path style:

    >>> custom_settings = pw.io.s3.AwsS3Settings(
    ...     endpoint="avv749.stackhero-network.com",
    ...     bucket_name="datasets",
    ...     access_key=os.environ["MINIO_S3_ACCESS_KEY"],
    ...     secret_access_key=os.environ["MINIO_S3_SECRET_ACCESS_KEY"],
    ...     with_path_style=True,
    ...     region="eu-west-3",
    ... )

    And you can connect with the usage of this created custom settings format:

    >>> t = pw.io.s3.read(
    ...     "animals/",
    ...     aws_s3_settings=custom_settings,
    ...     format="binary",
    ... )

    Please note that the min.io connection via generic S3 connector is given only as an
    example: you may use ``pw.io.minio.read`` connector which wouldn't require any custom
    settings object creation from you.
    """
    if aws_s3_settings:
        prepared_aws_settings = aws_s3_settings
    else:
        prepared_aws_settings = AwsS3Settings.new_from_path(path)

    data_storage = api.DataStorage(
        storage_type="s3",
        path=path,
        aws_s3_settings=prepared_aws_settings.settings,
        csv_parser_settings=csv_settings.api_settings if csv_settings else None,
        object_pattern=path_filter or "*",
        mode=internal_connector_mode(mode),
        read_method=internal_read_method(format),
        downloader_threads_count=downloader_threads_count,
    )

    schema, data_format = construct_schema_and_data_format(
        format,
        schema=schema,
        csv_settings=csv_settings,
        json_field_paths=json_field_paths,
        with_metadata=with_metadata,
        _stacklevel=_stacklevel + 4,
    )
    data_source_options = datasource.DataSourceOptions(
        commit_duration_ms=autocommit_duration_ms,
        unique_name=_get_unique_name(name, kwargs, stacklevel=_stacklevel + 5),
        max_backlog_size=max_backlog_size,
    )
    return table_from_datasource(
        datasource.GenericDataSource(
            datastorage=data_storage,
            dataformat=data_format,
            schema=schema,
            data_source_options=data_source_options,
            datasource_name="s3",
        ),
        debug_datasource=datasource.debug_datasource(debug_data),
    )


@check_arg_types
@trace_user_frame
def read_from_digital_ocean(
    path: str,
    do_s3_settings: DigitalOceanS3Settings,
    format: Literal["csv", "json", "plaintext", "plaintext_by_object", "binary"],
    *,
    schema: type[Schema] | None = None,
    mode: Literal["streaming", "static"] = "streaming",
    with_metadata: bool = False,
    csv_settings: CsvParserSettings | None = None,
    json_field_paths: dict[str, str] | None = None,
    downloader_threads_count: int | None = None,
    autocommit_duration_ms: int | None = 1500,
    name: str | None = None,
    max_backlog_size: int | None = None,
    debug_data: Any = None,
    **kwargs,
) -> Table:
    """Reads a table from one or several objects in Digital Ocean S3 bucket.

    In case the prefix of S3 path is specified, and there are several objects lying
    under this prefix, their order is determined according to their modification times:
    the smaller the modification time is, the earlier the file will be passed to the
    engine.

    Args:
        path: Path to an object or to a folder of objects in S3 bucket.
        do_s3_settings: Connection parameters for the account and the bucket.
        format: Format of data to be read. Currently ``csv``, ``json``, ``plaintext``,
            ``plaintext_by_object`` and ``binary`` formats are supported. The difference
            between ``plaintext`` and ``plaintext_by_object`` is how the input is
            tokenized: if the ``plaintext`` option is chosen, it's split by the newlines.
            Otherwise, the files are split in full and one row will correspond to one
            file. In case the ``binary`` format is specified, the data is read as raw
            bytes without UTF-8 parsing.
        schema: Schema of the resulting table. Not required for ``plaintext_by_object``
            and ``binary`` formats: if they are chosen, the contents of the read objects
            are stored in the column ``data``.
        mode: If set to ``streaming``, the engine waits for the new objects under the
            given path prefix. Set it to ``static``, it only considers the available
            data and ingest all of it. Default value is ``streaming``.
        with_metadata: When set to true, the connector will add an additional column
            named ``_metadata`` to the table. This column will be a JSON field that will
            contain an optional field ``modified_at``. Additionally, the column will also
            have an optional field named ``owner`` containing an ID of the object owner.
            Finally, the column will also contain a field named ``path`` that will show
            the full path to the object within a bucket from where a row was filled.
        csv_settings: Settings for the CSV parser. This parameter is used only in case
            the specified format is "csv".
        json_field_paths: If the format is "json", this field allows to map field names
            into path in the read json object. For the field which require such mapping,
            it should be given in the format ``<field_name>: <path to be mapped>``,
            where the path to be mapped needs to be a
            `JSON Pointer (RFC 6901) <https://www.rfc-editor.org/rfc/rfc6901>`_.
        downloader_threads_count: The number of threads created to download the contents
            of the bucket under the given path. It defaults to the number of cores
            available on the machine. It is recommended to increase the number of
            threads if your bucket contains many small files.
        autocommit_duration_ms: The maximum time between two commits. Every
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

    Let's consider an object store, which is hosted in Digital Ocean S3. The store
    contains CSV datasets in the respective bucket and is located in the region ams3.
    The goal is to read the dataset, located under the path ``animals/`` in this bucket.

    Then, the code may look as follows:

    >>> import os
    >>> import pathway as pw
    >>> class InputSchema(pw.Schema):
    ...   owner: str
    ...   pet: str
    >>> t = pw.io.s3.read_from_digital_ocean(
    ...     "animals/",
    ...     do_s3_settings=pw.io.s3.DigitalOceanS3Settings(
    ...         bucket_name="datasets",
    ...         region="ams3",
    ...         access_key=os.environ["DO_S3_ACCESS_KEY"],
    ...         secret_access_key=os.environ["DO_S3_SECRET_ACCESS_KEY"],
    ...     ),
    ...     format="csv",
    ...     schema=InputSchema,
    ... )

    Please note that this connector is **interoperable** with the **AWS S3** connector,
    therefore all examples concerning different data formats in ``pw.io.s3.read`` also
    work with Digital Ocean version.
    """
    prepared_s3_settings = do_s3_settings.create_aws_settings()
    data_storage = api.DataStorage(
        storage_type="s3",
        path=path,
        aws_s3_settings=prepared_s3_settings.settings,
        csv_parser_settings=csv_settings.api_settings if csv_settings else None,
        mode=internal_connector_mode(mode),
        read_method=internal_read_method(format),
        downloader_threads_count=downloader_threads_count,
    )

    schema, data_format = construct_schema_and_data_format(
        format,
        schema=schema,
        csv_settings=csv_settings,
        json_field_paths=json_field_paths,
        with_metadata=with_metadata,
        _stacklevel=5,
    )
    datasource_options = datasource.DataSourceOptions(
        commit_duration_ms=autocommit_duration_ms,
        unique_name=_get_unique_name(name, kwargs),
        max_backlog_size=max_backlog_size,
    )
    return table_from_datasource(
        datasource.GenericDataSource(
            datastorage=data_storage,
            dataformat=data_format,
            data_source_options=datasource_options,
            schema=schema,
            datasource_name="s3-digital-ocean",
        ),
        debug_datasource=datasource.debug_datasource(debug_data),
    )


@check_arg_types
@trace_user_frame
def read_from_wasabi(
    path: str,
    wasabi_s3_settings: WasabiS3Settings,
    format: Literal["csv", "json", "plaintext", "plaintext_by_object", "binary"],
    *,
    schema: type[Schema] | None = None,
    mode: Literal["streaming", "static"] = "streaming",
    with_metadata: bool = False,
    csv_settings: CsvParserSettings | None = None,
    json_field_paths: dict[str, str] | None = None,
    downloader_threads_count: int | None = None,
    autocommit_duration_ms: int | None = 1500,
    name: str | None = None,
    max_backlog_size: int | None = None,
    debug_data: Any = None,
    **kwargs,
) -> Table:
    """Reads a table from one or several objects in Wasabi S3 bucket.

    In case the prefix of S3 path is specified, and there are several objects lying under
    this prefix, their order is determined according to their modification times: the
    smaller the modification time is, the earlier the file will be passed to the engine.

    Args:
        path: Path to an object or to a folder of objects in S3 bucket.
        wasabi_s3_settings: Connection parameters for the account and the bucket.
        format: Format of data to be read. Currently ``csv``, ``json``, ``plaintext``,
            ``plaintext_by_object`` and ``binary`` formats are supported. The difference
            between ``plaintext`` and ``plaintext_by_object`` is how the input is
            tokenized: if the ``plaintext`` option is chosen, it's split by the newlines.
            Otherwise, the files are split in full and one row will correspond to one
            file. In case the ``binary`` format is specified, the data is read as raw
            bytes without UTF-8 parsing.
        schema: Schema of the resulting table. Not required for ``plaintext_by_object``
            and ``binary`` formats: if they are chosen, the contents of the read objects
            are stored in the column ``data``.
        mode: If set to ``streaming``, the engine waits for the new objects under the
            given path prefix. Set it to ``static``, it only considers the available
            data and ingest all of it. Default value is ``streaming``.
        with_metadata: When set to true, the connector will add an additional column
            named ``_metadata`` to the table. This column will be a JSON field that will
            contain an optional field ``modified_at``. Additionally, the column will also
            have an optional field named ``owner`` containing an ID of the object owner.
            Finally, the column will also contain a field named ``path`` that will show
            the full path to the object within a bucket from where a row was filled.
        csv_settings: Settings for the CSV parser. This parameter is used only in case
            the specified format is "csv".
        json_field_paths: If the format is "json", this field allows to map field names
            into path in the read json object. For the field which require such mapping,
            it should be given in the format ``<field_name>: <path to be mapped>``,
            where the path to be mapped needs to be a
            `JSON Pointer (RFC 6901) <https://www.rfc-editor.org/rfc/rfc6901>`_.
        downloader_threads_count: The number of threads created to download the contents
            of the bucket under the given path. It defaults to the number of cores
            available on the machine. It is recommended to increase the number of
            threads if your bucket contains many small files.
        autocommit_duration_ms: The maximum time between two commits. Every
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

    Let's consider an object store, which is hosted in Wasabi S3. The store
    contains CSV datasets in the respective bucket and is located in the region ``us-west-1``.
    The goal is to read the dataset, located under the path ``animals/`` in this bucket.

    Then, the code may look as follows:

    >>> import os
    >>> import pathway as pw
    >>> class InputSchema(pw.Schema):
    ...   owner: str
    ...   pet: str
    >>> t = pw.io.s3.read_from_wasabi(
    ...     "animals/",
    ...     wasabi_s3_settings=pw.io.s3.WasabiS3Settings(
    ...         bucket_name="datasets",
    ...         region="us-west-1",
    ...         access_key=os.environ["WASABI_S3_ACCESS_KEY"],
    ...         secret_access_key=os.environ["WASABI_S3_SECRET_ACCESS_KEY"],
    ...     ),
    ...     format="csv",
    ...     schema=InputSchema,
    ... )

    Please note that this connector is **interoperable** with the **AWS S3** connector,
    therefore all examples concerning different data formats in ``pw.io.s3.read`` also
    work with Wasabi version.
    """
    prepared_s3_settings = wasabi_s3_settings.create_aws_settings()
    data_storage = api.DataStorage(
        storage_type="s3",
        path=path,
        aws_s3_settings=prepared_s3_settings.settings,
        csv_parser_settings=csv_settings.api_settings if csv_settings else None,
        mode=internal_connector_mode(mode),
        read_method=internal_read_method(format),
        downloader_threads_count=downloader_threads_count,
    )

    schema, data_format = construct_schema_and_data_format(
        format,
        schema=schema,
        csv_settings=csv_settings,
        json_field_paths=json_field_paths,
        with_metadata=with_metadata,
        _stacklevel=5,
    )
    datasource_options = datasource.DataSourceOptions(
        commit_duration_ms=autocommit_duration_ms,
        unique_name=_get_unique_name(name, kwargs),
        max_backlog_size=max_backlog_size,
    )
    return table_from_datasource(
        datasource.GenericDataSource(
            datastorage=data_storage,
            dataformat=data_format,
            data_source_options=datasource_options,
            schema=schema,
            datasource_name="s3-wasabi",
        ),
        debug_datasource=datasource.debug_datasource(debug_data),
    )


# This is made to force AwsS3Settings documentation
__all__ = [
    "AwsS3Settings",
    "DigitalOceanS3Settings",
    "WasabiS3Settings",
    "read",
    "read_from_digital_ocean",
    "read_from_wasabi",
]
