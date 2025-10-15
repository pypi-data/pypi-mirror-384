# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import warnings
from contextlib import nullcontext
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pytest

from geneva import connect, udf
from geneva.transformer import UDF, UDFArgType


def test_udf_fsl(tmp_path: Path) -> None:
    @udf(data_type=pa.list_(pa.float32(), 4))
    def gen_fsl(b: pa.RecordBatch) -> pa.Array:
        arr = pa.array([b * 1.0 for b in range(8)])
        fsl = pa.FixedSizeListArray.from_arrays(arr, 4)
        return fsl

    assert gen_fsl.data_type == pa.list_(pa.float32(), 4)

    db = connect(tmp_path)
    tbl = pa.table({"a": [1, 2]})
    tbl = db.create_table("t1", tbl)

    # RecordBatch UDFs don't use input_columns - they receive the entire batch
    tbl.add_columns(
        {"embed": gen_fsl},
    )

    tbl = db.open_table("t1")
    assert tbl.schema == pa.schema(
        [
            pa.field("a", pa.int64()),
            pa.field("embed", pa.list_(pa.float32(), 4)),
        ],
    )


def test_udf_data_type_inference() -> None:
    @udf
    def foo(x: int, y: int) -> int:
        return x + y

    assert foo.data_type == pa.int64()
    assert foo.arg_type is UDFArgType.SCALAR

    for np_dtype in [
        np.bool_,
        np.uint8,
        np.uint16,
        np.uint32,
        np.uint64,
        np.int8,
        np.int16,
        np.int32,
        np.int64,
        np.float16,
        np.float32,
        np.float64,
    ]:

        @udf
        def foo_np(x: int, np_dtype=np_dtype) -> np_dtype:
            return np_dtype(x)

        assert foo_np.data_type == pa.from_numpy_dtype(np_dtype)
        assert foo_np.arg_type is UDFArgType.SCALAR

    @udf
    def bool_val(x: int) -> bool:
        return x % 2 == 0

    assert bool_val.data_type == pa.bool_()
    assert bool_val.arg_type is UDFArgType.SCALAR

    @udf
    def foo_str(x: int) -> str:
        return str(x)

    assert foo_str.data_type == pa.string()
    assert foo_str.arg_type is UDFArgType.SCALAR

    @udf
    def np_bool(x: int) -> np.bool_:
        return np.bool_(x % 2 == 0)

    assert np_bool.data_type == pa.bool_()
    assert np_bool.arg_type is UDFArgType.SCALAR


def test_udf_as_regular_functions() -> None:
    @udf
    def add_three_numbers(a: int, b: int, c: int) -> int:
        return a + b + c

    assert add_three_numbers(1, 2, 3) == 6
    assert add_three_numbers(10, 20, 30) == 60
    assert add_three_numbers.arg_type is UDFArgType.SCALAR
    assert add_three_numbers.data_type == pa.int64()

    @udf
    def make_string(x: int, y: str) -> str:
        return f"{y}-{x}"

    assert make_string(42, "answer") == "answer-42"
    assert make_string.arg_type is UDFArgType.SCALAR
    assert make_string.data_type == pa.string()

    @udf(data_type=pa.float32())
    def multi_by_two(batch: pa.RecordBatch) -> pa.Array:
        arr = pc.multiply(batch.column(0), 2)
        return arr

    rb = pa.RecordBatch.from_arrays([pa.array([1, 2, 3])], ["col"])
    assert multi_by_two(rb) == pa.array([2, 4, 6])
    assert multi_by_two.arg_type is UDFArgType.RECORD_BATCH

    # Confirm direct calls with multiple arguments still work as expected
    assert make_string(7, "num") == "num-7"
    assert add_three_numbers(2, 3, 4) == 9


def test_udf_with_batch_mode() -> None:
    """Test using a scalar UDF, but filled with batch model"""

    @udf
    def powers(a: int, b: int) -> int:
        return a**b

    # a RecordBatch with a and b columns
    rb = pa.RecordBatch.from_arrays(
        [pa.array([1, 2, 3]), pa.array([4, 5, 6])],
        ["a", "b"],
    )
    result = powers(rb)
    assert result == pa.array([1, 2**5, 3**6])


def test_stateful_callable() -> None:
    @udf
    class StatefulFn:
        def __init__(self) -> None:
            self.state = 0

        def __call__(self, x: int) -> int:
            self.state += x
            return self.state

    stateful_fn = StatefulFn()
    assert isinstance(stateful_fn, UDF)
    assert stateful_fn(1) == 1
    assert stateful_fn.arg_type is UDFArgType.SCALAR
    assert stateful_fn.data_type == pa.int64()
    assert stateful_fn.input_columns == ["x"]

    @udf(data_type=pa.int64())
    class StatefulBatchFn:
        def __init__(self) -> None:
            self.state = 0

        def __call__(self, batch: pa.RecordBatch) -> pa.Array:
            self.state += sum(batch.column(0).to_pylist())
            return pa.array([self.state] * batch.num_rows)

    stateful_batch_fn = StatefulBatchFn()
    assert isinstance(stateful_batch_fn, UDF)
    assert stateful_batch_fn.arg_type is UDFArgType.RECORD_BATCH
    assert stateful_batch_fn.data_type == pa.int64()


def test_batched_udf_with_explicity_columns() -> None:
    @udf(data_type=pa.int64())
    def add_columns(a: pa.Array, b: pa.Array) -> pa.Array:
        return pc.add(a, b)

    assert add_columns.arg_type is UDFArgType.ARRAY
    assert add_columns.data_type == pa.int64()
    assert add_columns.input_columns == ["a", "b"]

    with pytest.raises(
        ValueError, match="multiple parameters with 'pa.RecordBatch' type"
    ):

        @udf
        def bad_udf(a: pa.RecordBatch, b: pa.RecordBatch) -> pa.Array:
            return pc.add(a.column(0), b.column(0))


def test_default_no_cuda_no_num_gpus_uses_0_no_warning() -> None:
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")

        @udf
        def f(x: int) -> int:
            return x

        assert isinstance(f, UDF)
        assert f.num_gpus == 0.0
        # No deprecation warning since caller didn't provide cuda
        assert not [w for w in rec if issubclass(w.category, DeprecationWarning)]


@pytest.mark.parametrize(
    ("cuda", "num_gpus", "expected"),
    [
        (True, None, 1.0),  # deprecated behavior
        (False, None, 0.0),  # deprecated behavior
        (False, 1.0, 1.0),  # respect num_gpus over cuda
        (True, 0.0, 0.0),  # respect num_gpus over cuda
        (None, None, 0.0),  # default
        (None, 2.5, 2.5),  # new behavior
        (None, 3, 3.0),  # int to float conversion
    ],
)
def test_fallback_to_cuda_when_num_gpus_none(cuda, num_gpus, expected) -> None:
    ctx = (
        pytest.warns(DeprecationWarning, match=r".*'cuda'.*deprecated.*")
        if cuda
        else nullcontext()
    )
    with ctx:

        @udf(cuda=cuda, num_gpus=num_gpus)
        def f(x: int) -> int:
            return x

    assert f.num_gpus == expected


GE_ZERO_RE = r".*>=\s*0(\.0)?"


def test_negative_num_gpus_rejected_on_init() -> None:
    with pytest.raises(ValueError, match=GE_ZERO_RE):

        @udf(num_gpus=-1)
        def f(x: int) -> int:
            return x


def test_set_time_validation_rejects_negative() -> None:
    @udf(num_gpus=0.0)
    def f(x: int) -> int:
        return x

    with pytest.raises(ValueError, match=GE_ZERO_RE):
        f.num_gpus = -0.1  # on_setattr=attrs.setters.validate should enforce validator


def test_cloudpickle_preserves_num_gpus() -> None:
    """Test that num_gpus is preserved through cloudpickle serialization."""
    import geneva.cloudpickle as cloudpickle

    @udf(num_gpus=2.5)
    def gpu_func(x: int) -> int:
        return x * 2

    # Serialize and deserialize
    pickled = cloudpickle.dumps(gpu_func)
    restored = cloudpickle.loads(pickled)

    # Verify all GPU-related attributes are preserved
    assert restored.num_gpus == 2.5
    assert restored.num_cpus == 1.0
    assert restored.cuda is False


def test_cloudpickle_preserves_cuda_deprecated() -> None:
    """Test that cuda=True (deprecated) is preserved through cloudpickle."""
    import geneva.cloudpickle as cloudpickle

    with pytest.warns(DeprecationWarning, match=r".*'cuda'.*deprecated.*"):

        @udf(cuda=True)
        def cuda_func(x: int) -> int:
            return x * 2

    # Serialize and deserialize
    pickled = cloudpickle.dumps(cuda_func)
    restored = cloudpickle.loads(pickled)

    # cuda=True sets num_gpus=1.0
    assert restored.num_gpus == 1.0
    assert restored.cuda is True


def test_cloudpickle_preserves_cpu_only() -> None:
    """Test that CPU-only UDFs (num_gpus=0) are preserved."""
    import geneva.cloudpickle as cloudpickle

    @udf(num_gpus=0.0)
    def cpu_func(x: int) -> int:
        return x * 2

    pickled = cloudpickle.dumps(cpu_func)
    restored = cloudpickle.loads(pickled)

    assert restored.num_gpus == 0.0
    assert restored.cuda is False


@pytest.mark.parametrize(
    ("num_gpus", "num_cpus"),
    [
        (0.0, 1.0),
        (1.0, 2.0),
        (2.5, 4.0),
        (None, None),  # None means use defaults
    ],
)
def test_packager_preserves_gpu_cpu_settings(num_gpus, num_cpus) -> None:
    """Test that UDFPackager marshal/unmarshal preserves GPU/CPU settings."""
    from geneva.packager import DockerUDFPackager

    kwargs = {}
    if num_gpus is not None:
        kwargs["num_gpus"] = num_gpus
    if num_cpus is not None:
        kwargs["num_cpus"] = num_cpus

    @udf(**kwargs)
    def compute_func(x: int) -> int:
        return x * 3

    expected_num_gpus = num_gpus if num_gpus is not None else 0.0
    expected_num_cpus = num_cpus if num_cpus is not None else 1.0

    # Create packager without workspace (no workspace zip needed for this test)
    packager = DockerUDFPackager(prebuilt_docker_img="test:latest")

    # Marshal and unmarshal
    spec = packager.marshal(compute_func)
    restored = packager.unmarshal(spec)

    # Verify GPU/CPU settings are preserved
    assert restored.num_gpus == expected_num_gpus
    assert restored.num_cpus == expected_num_cpus
    assert restored.name == compute_func.name


def test_packager_preserves_cuda_deprecated() -> None:
    """Test that packager preserves cuda=True through marshal/unmarshal."""
    from geneva.packager import DockerUDFPackager

    with pytest.warns(DeprecationWarning, match=r".*'cuda'.*deprecated.*"):

        @udf(cuda=True, num_cpus=2.0)
        def cuda_compute(x: int) -> int:
            return x * 4

    packager = DockerUDFPackager(prebuilt_docker_img="test:latest")

    spec = packager.marshal(cuda_compute)
    restored = packager.unmarshal(spec)

    # cuda=True sets num_gpus=1.0
    assert restored.num_gpus == 1.0
    assert restored.cuda is True
    assert restored.num_cpus == 2.0
