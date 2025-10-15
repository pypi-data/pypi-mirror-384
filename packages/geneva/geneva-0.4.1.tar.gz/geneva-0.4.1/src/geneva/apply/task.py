# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright The Geneva Authors

# definition of the read task, which is portion of a fragment

import hashlib
import logging
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any, cast

import attrs
import pyarrow as pa
import pyarrow.compute as pc
from typing_extensions import override

from geneva.db import connect
from geneva.query import ExtractedTransform
from geneva.table import Table, TableReference
from geneva.transformer import BACKFILL_SELECTED, UDF, UDFArgType

_LOG = logging.getLogger(__name__)

DEFAULT_CHECKPOINT_ROWS = 100


class ReadTask(ABC):
    """
    A task to read data that has a defined output location and unique identifier
    """

    @abstractmethod
    def to_batches(
        self, *, batch_size=DEFAULT_CHECKPOINT_ROWS
    ) -> Iterator[pa.RecordBatch]:
        """Return the data to read"""

    @abstractmethod
    def checkpoint_key(self) -> str:
        """Return a unique key for this task"""

    @abstractmethod
    def dest_frag_id(self) -> int:
        """Return the id of the destination fragment"""

    @abstractmethod
    def dest_offset(self) -> int:
        """Return the offset into the destination fragment"""

    @abstractmethod
    def num_rows(self) -> int:
        """Return the number of rows this task will read"""


@attrs.define(order=True)
class ScanTask(ReadTask):
    uri: str
    columns: list[str]
    frag_id: int
    offset: int
    limit: int

    version: int | None = None
    where: str | None = None

    with_row_address: bool = False

    def _get_table(self) -> Table:
        # here's an example: "gs://my-bucket/dir1/dir2/data.lance"
        uri_parts = self.uri.split("/")
        tablename = ".".join(uri_parts[-1].split(".")[:-1])  # "data"
        db_path = "/".join(uri_parts[:-1])  # "gs://my-bucket/dir1/dir2"

        tbl = connect(db_path).open_table(tablename, version=self.version)
        return tbl

    @override
    def to_batches(
        self, *, batch_size=DEFAULT_CHECKPOINT_ROWS
    ) -> Iterator[pa.RecordBatch]:
        _LOG.debug(
            f"Reading {self.uri} with version {self.version} for cols {self.columns}"
            f" offset {self.offset} limit {self.limit} where='{self.where}'"
        )
        tbl = self._get_table()
        query = tbl.search().enable_internal_api()  # type: ignore[attr-defined]

        if self.with_row_address:
            query = query.with_row_address()

        query = query.with_fragments(self.frag_id).offset(self.offset).limit(self.limit)
        query = query.with_where_as_bool_column()

        # works with blobs but not filters
        if self.columns is not None:
            query = query.select(self.columns)
        if self.where is not None:
            query = query.where(self.where)

        # Currently lancedb reports the wrong type for the return value
        # of the to_batches method.  Remove pyright ignore when fixed.
        batches: pa.RecordBatchReader = query.to_batches(batch_size)  # pyright: ignore[reportAssignmentType]

        yield from batches

    @override
    def checkpoint_key(self) -> str:
        hasher = hashlib.md5()
        hasher.update(
            f"{self.uri}:{self.version}:{self.columns}:{self.frag_id}:{self.offset}:{self.limit}:{self.where}".encode(),
        )
        return hasher.hexdigest()

    @override
    def dest_frag_id(self) -> int:
        return self.frag_id

    @override
    def dest_offset(self) -> int:
        return self.offset

    @override
    def num_rows(self) -> int:
        # TODO calculate # rows
        return self.limit


@attrs.define(order=True)
class CopyTask(ReadTask):
    src: TableReference
    dst: TableReference
    columns: list[str]
    frag_id: int
    offset: int
    limit: int

    @override
    def to_batches(
        self, *, batch_size=DEFAULT_CHECKPOINT_ROWS
    ) -> Iterator[pa.RecordBatch]:
        dst_tbl = self.dst.open()
        row_ids_batch = (
            dst_tbl.search()
            .select(["__source_row_id"])
            .offset(self.offset)
            .limit(self.limit)
            .to_arrow()
        )
        row_ids = cast("list[int]", row_ids_batch["__source_row_id"].to_pylist())

        # TODO: Add streaming take to lance
        table = self.src.open().to_lance()._take_rows(row_ids, columns=self.columns)

        table = table.add_column(table.num_columns, "_rowaddr", self._get_row_addrs())

        batches = table.to_batches(max_chunksize=batch_size)

        yield from batches

    @override
    def checkpoint_key(self) -> str:
        hasher = hashlib.md5()
        hasher.update(
            f"CopyTask:{self.src.db_uri}:{self.src.table_name}:{self.src.version}:{self.columns}:{self.dst.db_uri}:{self.dst.table_name}:{self.frag_id}:{self.offset}:{self.limit}".encode(),
        )
        return hasher.hexdigest()

    @override
    def dest_frag_id(self) -> int:
        return self.frag_id

    @override
    def dest_offset(self) -> int:
        return self.offset

    def _get_row_addrs(self) -> pa.Array:
        frag_mod = self.frag_id << 32
        addrs = [frag_mod + x for x in range(self.offset, self.offset + self.limit)]
        return cast("pa.Array", pa.array(addrs, pa.uint64()))

    @override
    def num_rows(self) -> int:
        # TODO calculate # rows
        return self.limit


class MapTask(ABC):
    @abstractmethod
    def checkpoint_key(self) -> str:
        """Return a unique name for the task"""

    @abstractmethod
    def name(self) -> str:
        """Return a name to use for progress strings"""

    @abstractmethod
    def apply(self, batch: pa.RecordBatch) -> pa.RecordBatch:
        """Apply the map function to the input batch, returning the output batch"""

    @abstractmethod
    def output_schema(self) -> pa.Schema:
        """Return the output schema"""

    @abstractmethod
    def is_cuda(self) -> bool:
        """Return true if the task requires CUDA

        .. deprecated::
            Use :meth:`num_gpus` instead to get the actual GPU requirement.
        """

    @abstractmethod
    def num_cpus(self) -> float | None:
        """Return the number of CPUs the task should use (None for default)"""

    @abstractmethod
    def num_gpus(self) -> float | None:
        """Return the number of GPUs the task should use (None for default)"""

    @abstractmethod
    def memory(self) -> int | None:
        """Return the amount of RAM the task should use (None for default)"""

    @abstractmethod
    def batch_size(self) -> int:
        """Return the batch size the task should use"""


@attrs.define(order=True)
class BackfillUDFTask(MapTask):
    udfs: dict[str, UDF] = (
        attrs.field()
    )  # TODO: use attrs to enforce stateful udfs are handled here

    # this is needed to differentiate a filtered task's checkpont keys
    # for backfill jobs
    where: str | None = attrs.field(default=None)

    def __get_udf(self) -> tuple[str, UDF]:
        # TODO: Add support for multiple columns to add_columns operation
        if len(self.udfs) != 1:
            raise NotImplementedError("Add columns does not support multiple UDFs")
        col, udf = next(iter(self.udfs.items()))
        if not isinstance(udf, UDF):
            # stateful udf are Callable classes that need to be instantiated.
            udf = udf()
        return col, udf

    @override
    def name(self) -> str:
        name, _ = self.__get_udf()
        return name

    @override
    def checkpoint_key(self) -> str:
        # 'where' is required in key to distinguish different partial backfills jobs
        # hashing it so that it cannot be used as a directory path attack vector
        _, udf = self.__get_udf()
        if self.where:
            hasher = hashlib.md5()
            hasher.update((self.where or "").encode())
            return f"{udf.checkpoint_key}:where={hasher.hexdigest()}"
        return udf.checkpoint_key

    @override
    def apply(self, batch: pa.RecordBatch | list[dict[str, Any]]) -> pa.RecordBatch:
        udf_col_name, udf = self.__get_udf()

        if isinstance(batch, pa.RecordBatch):
            row_addr = batch["_rowaddr"]
            has_carry_forward_col = udf_col_name in batch.schema.names
            has_backfill_selected = BACKFILL_SELECTED in batch.schema.names
        else:
            # might have blob_columns which needs _rowaddr
            row_addr = pa.array([x["_rowaddr"] for x in batch], type=pa.uint64())
            has_carry_forward_col = bool(batch) and (udf_col_name in batch[0])
            has_backfill_selected = bool(batch) and (BACKFILL_SELECTED in batch[0])

        # drop carry_foward cols from what will be UDF arguments.
        if isinstance(batch, pa.RecordBatch):
            if udf_col_name in batch.schema.names:
                # select all the other columns
                col_val_arrays = [
                    batch[col] for col in batch.schema.names if col != udf_col_name
                ]
                col_names = [col for col in batch.schema.names if col != udf_col_name]
                batch_for_udf = pa.RecordBatch.from_arrays(col_val_arrays, col_names)
            else:
                batch_for_udf = batch
        else:
            # list-of-dicts case: just filter out the key
            batch_for_udf = [
                {k: v for k, v in row.items() if k != udf_col_name} for row in batch
            ]

        # execute the udf
        # Optimization: For RecordBatch and Array UDFs with filtering, only process
        # selected rows
        try:
            if (
                has_backfill_selected
                and isinstance(batch, pa.RecordBatch)
                and udf.arg_type in (UDFArgType.RECORD_BATCH, UDFArgType.ARRAY)
            ):
                # Get the selection mask
                mask = batch[BACKFILL_SELECTED]

                # Check if any rows are selected
                if any(mask.to_pylist()):
                    # Filter batch_for_udf to only include selected rows
                    filtered_batch_for_udf = pc.filter(batch_for_udf, mask)  # type: ignore[call-overload,arg-type]
                    _LOG.debug(
                        f"{udf.arg_type.name} UDF optimization: processing "
                        f"{filtered_batch_for_udf.num_rows} rows instead of "  # type: ignore[attr-defined]
                        f"{batch_for_udf.num_rows}"  # type: ignore[attr-defined]
                    )

                    # Execute UDF on filtered batch
                    filtered_new_arr = udf(filtered_batch_for_udf, use_applier=True)

                    # Expand results back to full batch size
                    result_list = [None] * batch.num_rows
                    indices_array = pa.array(range(batch.num_rows))
                    selected_indices = pc.filter(indices_array, mask)

                    # Place filtered results at correct positions
                    for i, filtered_val in enumerate(filtered_new_arr):
                        original_idx = selected_indices[i].as_py()
                        result_list[original_idx] = filtered_val.as_py()

                    new_arr = pa.array(result_list, type=udf.data_type)
                else:
                    # No rows selected, return array of nulls
                    new_arr = pa.array([None] * batch.num_rows, type=udf.data_type)
            else:
                # Original behavior for non-RecordBatch UDFs or when no filtering
                new_arr = udf(batch_for_udf, use_applier=True)
        except KeyError as e:
            # Column not found in batch
            if isinstance(batch_for_udf, pa.RecordBatch):
                available_cols = batch_for_udf.schema.names
            elif batch_for_udf and len(batch_for_udf) > 0:  # list[dict] with elements
                available_cols = list(batch_for_udf[0].keys())
            else:  # empty list
                available_cols = []
            raise KeyError(
                f"UDF '{udf.name}' failed: column {e} not found in batch. "
                f"Available columns: {available_cols}. "
                f"UDF expects input_columns: {udf.input_columns}. "
                f"This typically means the UDF's input_columns don't match "
                f"the table schema."
            ) from e
        except (pa.ArrowInvalid, pa.ArrowTypeError) as e:
            # Type mismatch or serialization error
            batch_schema = (
                batch_for_udf.schema
                if isinstance(batch_for_udf, pa.RecordBatch)
                else None
            )
            raise TypeError(
                f"UDF '{udf.name}' failed with type error: {e}. "
                f"Input batch schema: {batch_schema}. "
                f"UDF expects input_columns: {udf.input_columns}. "
                f"UDF output type: {udf.data_type}. "
                f"This often indicates a type mismatch (e.g., float32 vs float64) "
                f"between the table schema and UDF expectations."
            ) from e

        # now finalize the result.
        if not has_carry_forward_col or not has_backfill_selected:
            schema = pa.schema(
                [
                    pa.field(udf_col_name, udf.data_type, metadata=udf.field_metadata),
                    pa.field("_rowaddr", pa.uint64()),
                ]
            )

            # no carry forward col? return the new
            return pa.record_batch([new_arr, row_addr], schema=schema)

        # handle carry forward of old values
        if isinstance(batch, pa.RecordBatch):
            orig_arr = batch[udf_col_name]
            mask = batch[BACKFILL_SELECTED]
        else:
            # extract py values and wrap into pa array
            orig_vals = [x.get(udf_col_name) for x in batch]
            orig_arr = pa.array(orig_vals, type=new_arr.type)
            mask_vals = [x.get(BACKFILL_SELECTED) for x in batch]
            mask = pa.array(mask_vals, type=pa.bool_())

        merged = pc.if_else(mask, new_arr, orig_arr)
        schema = pa.schema(
            [
                pa.field(udf_col_name, udf.data_type, metadata=udf.field_metadata),
                pa.field("_rowaddr", pa.uint64()),
            ]
        )
        return pa.record_batch([merged, row_addr], schema=schema)

    @override
    def output_schema(self) -> pa.Schema:
        name, udf = self.__get_udf()
        return pa.schema(
            [pa.field(name, udf.data_type), pa.field("_rowaddr", pa.uint64())]
        )

    @override
    def is_cuda(self) -> bool:
        """Deprecated: Use num_gpus() instead."""
        _, udf = self.__get_udf()
        return bool(udf.num_gpus and udf.num_gpus > 0)

    @override
    def num_cpus(self) -> float | None:
        _, udf = self.__get_udf()
        return udf.num_cpus

    @override
    def num_gpus(self) -> float | None:
        _, udf = self.__get_udf()
        return udf.num_gpus

    @override
    def memory(self) -> int | None:
        _, udf = self.__get_udf()
        return udf.memory

    @override
    def batch_size(self) -> int:
        _, udf = self.__get_udf()
        return udf.batch_size or DEFAULT_CHECKPOINT_ROWS


@attrs.define(order=True)
class CopyTableTask(MapTask):
    column_udfs: list[ExtractedTransform] = attrs.field()
    view_name: str = attrs.field()
    schema: pa.Schema = attrs.field()

    @override
    def name(self) -> str:
        return self.view_name

    @override
    def checkpoint_key(self) -> str:
        return self.view_name

    @override
    def apply(self, batch: pa.RecordBatch) -> pa.RecordBatch:
        for transform in self.column_udfs:
            new_arr = transform.udf(batch)
            batch = batch.add_column(
                transform.output_index, transform.output_name, new_arr
            )
        return batch

    @override
    def output_schema(self) -> pa.Schema:
        return self.schema

    @override
    def is_cuda(self) -> bool:
        """Deprecated: Use num_gpus() instead."""
        return any(
            column_udf.udf.num_gpus and column_udf.udf.num_gpus > 0
            for column_udf in self.column_udfs
        )

    @override
    def num_cpus(self) -> float | None:
        return max(
            (
                column_udf.udf.num_cpus
                for column_udf in self.column_udfs
                if column_udf.udf.num_cpus is not None
            ),
            default=None,
        )

    @override
    def num_gpus(self) -> float | None:
        return max(
            (
                column_udf.udf.num_gpus
                for column_udf in self.column_udfs
                if column_udf.udf.num_gpus is not None
            ),
            default=None,
        )

    @override
    def memory(self) -> int | None:
        return max(
            (
                column_udf.udf.memory
                for column_udf in self.column_udfs
                if column_udf.udf.memory is not None
            ),
            default=None,
        )

    @override
    def batch_size(self) -> int:
        return min(
            column_udf.udf.batch_size or DEFAULT_CHECKPOINT_ROWS
            for column_udf in self.column_udfs
        )
