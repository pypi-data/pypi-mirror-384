# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright The Geneva Authors

from __future__ import annotations

import logging
from types import UnionType
from typing import TYPE_CHECKING, Any, Union, get_args, get_origin, get_type_hints

import attrs
import pyarrow as pa

if TYPE_CHECKING:
    from lancedb import Connection, Table  # type: ignore[attr-defined]

_LOG = logging.getLogger(__name__)

# ---------- Arrow helpers from attrs ----------

_PRIMITIVE_PA: dict[Any, pa.DataType] = {
    str: pa.string(),
    int: pa.int64(),
    float: pa.float64(),
    bool: pa.bool_(),
    bytes: pa.binary(),
}


def _is_optional(ann: Any) -> bool:
    origin = get_origin(ann)
    args = get_args(ann)
    return (origin in (Union, UnionType)) and (type(None) in args)


def _base_of_optional(ann: Any) -> Any:
    if _is_optional(ann):
        return next(t for t in get_args(ann) if t is not type(None))  # noqa: E721
    return ann


def _infer_pa_from_annotation(ann: Any) -> pa.DataType | None:
    ann = _base_of_optional(ann)
    origin = get_origin(ann)
    args = get_args(ann)

    # handle list[T]
    if origin in (list, list):
        if not args:
            return pa.list_(pa.string())
        inner = _infer_pa_from_annotation(args[0])
        if inner is None:
            return None
        return pa.list_(inner)

    # primitives
    if ann in _PRIMITIVE_PA:
        return _PRIMITIVE_PA[ann]

    return None


def _infer_pa_from_value(v: Any) -> pa.DataType | None:
    if v is None:
        return None
    if isinstance(v, dict | set):
        return None
    if isinstance(v, list):
        return None
    if isinstance(v, str | int | float | bool | bytes):
        try:
            return pa.scalar(v).type
        except Exception:
            return None
    return None


def attrs_to_arrow_schema(model: Any) -> pa.Schema:
    if not attrs.has(type(model)):
        raise TypeError("alter_or_create expects an @attrs instance")

    # Resolve annotations (handles 'from __future__ import annotations')
    type_hints = get_type_hints(type(model), include_extras=True)

    fields_pa: list[pa.Field] = []
    for f in attrs.fields(type(model)):
        name = f.name
        meta_pa = f.metadata.get("pa_type") if f.metadata else None
        ann = type_hints.get(name, getattr(f, "type", Any))
        default_val = getattr(model, name)

        pa_type = (
            meta_pa
            or _infer_pa_from_annotation(ann)
            or _infer_pa_from_value(default_val)
        )
        if pa_type is None:
            raise TypeError(
                f"Cannot infer Arrow type for field '{name}'. "
                "Add metadata={'pa_type': ...} or use a supported annotation/value."
            )

        nullable = (default_val is None) or _is_optional(ann)
        fields_pa.append(pa.field(name, pa_type, nullable=nullable))
    return pa.schema(fields_pa)


# ---------- main one-shot API ----------


def alter_or_create_table(
    db: Connection,
    table_name: str,
    model: Any,  # attrs instance
    del_cols: bool = False,  # drop columns not present on the model
) -> Table:
    """
    Ensure `table_name` matches the attrs model schema.
    - If table doesn't exist -> create with model schema.
    - Else:
        - Optionally drop extra columns.
        - Add any missing columns based on pyarrow Field.
        - If the table is empty -> overwrite with full model schema.
    Returns the (opened) lancedb.Table.
    """
    if not attrs.has(type(model)):
        raise TypeError("alter_or_create expects an @attrs instance")

    # Open or create
    try:
        table = db.open_table(table_name)
    except ValueError:
        schema = attrs_to_arrow_schema(model)
        _LOG.info(f"creating table '{table_name}':\n{schema}")
        return db.create_table(table_name, schema=schema)

    # Compute deltas
    cur_cols = set(table.schema.names)
    # model columns, values, and types
    model_fields = attrs.fields(type(model))
    model_vals = {f.name: getattr(model, f.name) for f in model_fields}
    model_cols = set(model_vals.keys())

    # Drop columns not on model
    if del_cols:
        to_drop = [c for c in cur_cols if c not in model_cols]
        if to_drop:
            _LOG.info(f"dropping cols {to_drop} from {table.schema}")
            table.drop_columns(to_drop)
            table = db.open_table(table_name)  # refresh

    # Add new columns
    cur_cols = set(table.schema.names)
    new_cols = [c for c in model_cols if c not in cur_cols]
    if not new_cols:
        _LOG.debug("No new columns; schema up to date")
        return table

    _LOG.info(f"adding columns to table {table_name} schema: {new_cols}")

    # If table is empty: just overwrite schema (fastest & simplest)
    if len(table) == 0:
        schema = attrs_to_arrow_schema(model)
        _LOG.info("table is empty, overwriting with updated schema")
        return db.create_table(table_name, schema=schema, mode="overwrite")

    # Otherwise, add columns using field definitions from the model schema
    # This ensures proper type inference, especially for nullable fields
    model_schema = attrs_to_arrow_schema(model)
    new_fields: list[pa.Field] = [
        field for field in model_schema if field.name in new_cols
    ]

    # When adding columns to existing tables, make them nullable so existing rows
    # can have NULL values (even if the model defines them as non-nullable).
    # This allows for graceful schema evolution.
    new_fields_nullable = [
        pa.field(field.name, field.type, nullable=True, metadata=field.metadata)
        for field in new_fields
    ]

    # Pass the fields directly to add_columns for proper type handling
    # Handle both Geneva Table (has ._ltbl) and LanceDB Table (used directly)
    try:
        lance_table = getattr(table, "_ltbl", table)
        lance_table.add_columns(new_fields_nullable)
    except Exception as e:
        raise RuntimeError(
            f"Failed to add columns {new_cols} to table {table_name}. "
            f"This may indicate incompatible field types. Error: {e}"
        ) from e
    return table
