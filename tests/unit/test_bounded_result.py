import json
import math
from collections.abc import Iterable, Iterator, Sequence
from typing import cast

import pytest

from data_intel._bounded_result import ResultContentError, build_bounded_result


def test_mixed_cells_have_golden_canonical_bytes_digest_and_immutable_values() -> None:
    result = build_bounded_result(
        ("id", "ratio", "note", "maybe"),
        ((2**53 + 1, 0.1, "snowman ☃", None),),
        1,
    )
    expected = (
        '{"columns":["id","ratio","note","maybe"],"rows":[[{"exact":true,'
        '"type":"integer","value":"9007199254740993"},{"exact":false,"type":"real",'
        '"value":"0.1"},{"type":"text","value":"snowman ☃"},{"type":"null",'
        '"value":null}]]}'
    ).encode()
    assert result.content_bytes == expected
    assert (
        result.content_sha256 == "1288d9f0e2e3e12bbd7f0cc385d4063c4c9861ebe5a5784622b56c924b37f630"
    )
    assert result.row_count == 1
    assert result.rows[0][0].value == "9007199254740993"
    assert result.rows[0][1].value == "0.1"
    attribute = "value"
    with pytest.raises((AttributeError, TypeError)):
        setattr(result.rows[0][0], attribute, "1")


@pytest.mark.parametrize("max_rows", [1, 20])
def test_row_limit_accepts_complete_results(max_rows: int) -> None:
    result = build_bounded_result(("v",), ((value,) for value in range(max_rows)), max_rows)
    assert result.row_count == max_rows
    assert result.rows[-1][0].value == str(max_rows - 1)


@pytest.mark.parametrize("max_rows", [1, 20])
def test_row_overflow_consumes_only_one_extra_row(max_rows: int) -> None:
    seen: list[int] = []

    def source() -> Iterator[tuple[int]]:
        for value in range(max_rows + 5):
            seen.append(value)
            yield (value,)

    with pytest.raises(ResultContentError) as error:
        build_bounded_result(("v",), source(), max_rows)
    assert error.value.code == "result_limit"
    assert seen == list(range(max_rows + 1))


@pytest.mark.parametrize("count", [1, 16])
def test_column_limit_accepts_one_or_sixteen_columns(count: int) -> None:
    labels = tuple(f"c{index}" for index in range(count))
    result = build_bounded_result(labels, (tuple(range(count)),), 1)
    assert result.columns == labels


def test_seventeen_columns_are_refused() -> None:
    with pytest.raises(ResultContentError) as error:
        build_bounded_result(tuple(f"c{index}" for index in range(17)), (), 1)
    assert error.value.code == "result_limit"


@pytest.mark.parametrize("label", ["a" * 64, "é" * 32])
def test_column_label_at_64_utf8_bytes_is_accepted(label: str) -> None:
    assert build_bounded_result((label,), (), 1).columns == (label,)


@pytest.mark.parametrize("label", ["a" * 65, "é" * 33])
def test_column_label_over_64_utf8_bytes_is_refused(label: str) -> None:
    with pytest.raises(ResultContentError) as error:
        build_bounded_result((label,), (), 1)
    assert error.value.code == "result_limit"


@pytest.mark.parametrize("labels", [("same", "same"), ("",), ("bad\ud800",), (1,)])
def test_invalid_column_labels_are_refused_without_echoing_values(
    labels: tuple[object, ...],
) -> None:
    with pytest.raises(ResultContentError) as error:
        build_bounded_result(labels, (), 1)
    assert error.value.code == "invalid_result"
    assert str(error.value) == "invalid_result"


@pytest.mark.parametrize("text", ["x" * 256, "☃" * 85])
def test_text_cell_at_256_utf8_bytes_is_accepted(text: str) -> None:
    assert build_bounded_result(("v",), ((text,),), 1).rows[0][0].value == text


@pytest.mark.parametrize("text", ["x" * 257, "☃" * 86])
def test_text_cell_over_256_utf8_bytes_is_refused(text: str) -> None:
    with pytest.raises(ResultContentError) as error:
        build_bounded_result(("v",), ((text,),), 1)
    assert error.value.code == "result_limit"


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        b"blob",
        bytearray(b"blob"),
        memoryview(b"blob"),
        math.nan,
        math.inf,
        -math.inf,
        object(),
    ],
    ids=[
        "bool",
        "false",
        "bytes",
        "bytearray",
        "memoryview",
        "nan",
        "infinity",
        "negative-infinity",
        "object",
    ],
)
def test_unsupported_scalar_values_are_refused(value: object) -> None:
    with pytest.raises(ResultContentError) as error:
        build_bounded_result(("v",), ((value,),), 1)
    assert error.value.code == "invalid_result"
    assert str(error.value) == "invalid_result"


@pytest.mark.parametrize("value", [-(2**63), 2**63 - 1, 2**53 + 1])
def test_sqlite_integer_values_keep_exact_signed_decimal(value: int) -> None:
    result = build_bounded_result(("v",), ((value,),), 1)
    assert result.rows[0][0].value == str(value)


@pytest.mark.parametrize("value", [-(2**63) - 1, 2**63])
def test_integer_outside_sqlite_signed_range_is_refused(value: int) -> None:
    with pytest.raises(ResultContentError) as error:
        build_bounded_result(("v",), ((value,),), 1)
    assert error.value.code == "invalid_result"


@pytest.mark.parametrize("row", [(), (1, 2), "1", b"1", 1])
def test_mismatched_or_nonrow_values_are_refused(row: object) -> None:
    with pytest.raises(ResultContentError) as error:
        build_bounded_result(("v",), (cast(Sequence[object], row),), 1)
    assert error.value.code == "invalid_result"


@pytest.mark.parametrize("max_rows", [0, 21, True, 1.0])
def test_max_rows_must_be_strict_integer_from_one_through_twenty(max_rows: object) -> None:
    with pytest.raises(ResultContentError) as error:
        build_bounded_result(("v",), (), cast(int, max_rows))
    assert error.value.code == "invalid_input"


def _sized_text_rows(target_bytes: int) -> tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]:
    labels = tuple(f"c{index}" for index in range(16))
    rows = [[""] * 16 for _ in range(20)]
    base_size = len(_reference_bytes(labels, rows))
    padding = target_bytes - base_size
    for row_index in range(20):
        for column_index in range(16):
            size = min(256, padding)
            rows[row_index][column_index] = "x" * size
            padding -= size
            if padding == 0:
                return labels, tuple(tuple(row) for row in rows)
    raise AssertionError("fixture capacity was insufficient")


def _reference_bytes(labels: tuple[str, ...], rows: list[list[str]]) -> bytes:
    wire_rows: list[list[dict[str, str]]] = []
    for row in rows:
        wire_rows.append([{"type": "text", "value": value} for value in row])
    content: dict[str, object] = {"columns": labels, "rows": wire_rows}
    return json.dumps(
        content, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


@pytest.mark.parametrize("size", [16_384, 16_385])
def test_complete_serialized_content_byte_limit(size: int) -> None:
    labels, rows = _sized_text_rows(size)
    expected = _reference_bytes(labels, [list(row) for row in rows])
    assert len(expected) == size
    if size == 16_384:
        assert build_bounded_result(labels, rows, 20).content_bytes == expected
    else:
        with pytest.raises(ResultContentError) as error:
            build_bounded_result(labels, rows, 20)
        assert error.value.code == "result_limit"


def test_unexpected_row_iterator_failure_remains_for_engine_classification() -> None:
    def broken_rows() -> Iterator[tuple[int]]:
        yield (1,)
        raise RuntimeError("query interrupted")

    with pytest.raises(RuntimeError, match="query interrupted"):
        build_bounded_result(("v",), broken_rows(), 2)


def test_noniterable_rows_are_classified_as_invalid_result() -> None:
    with pytest.raises(ResultContentError) as error:
        build_bounded_result(("v",), cast(Iterable[Sequence[object]], 1), 1)
    assert error.value.code == "invalid_result"


def test_text_that_is_not_strict_utf8_is_refused() -> None:
    with pytest.raises(ResultContentError) as error:
        build_bounded_result(("v",), (("bad\ud800",),), 1)
    assert error.value.code == "invalid_result"
