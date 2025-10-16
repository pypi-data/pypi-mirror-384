import pytest
import pydantic
import base64
import numpy as np
from blissdata.h5map import InlineRaw, Inline, InlineBase64


@pytest.mark.parametrize(
    "input_value, expected_json",
    [
        pytest.param([], "[]", id="empty list"),
        pytest.param("", '""', id="empty str"),
        pytest.param(["", ""], '["",""]', id="empty str list"),
        pytest.param("hello", '"hello"', id="str"),
        pytest.param(True, "true", id="bool"),
        pytest.param(123, "123", id="int"),
        pytest.param(123.456, "123.456", id="float"),
        pytest.param([[1, 2], [3, 4]], "[[1,2],[3,4]]", id="list"),
        pytest.param([1, 2.3, "4.5"], '["1","2.3","4.5"]', id="coerced list"),
        pytest.param(np.str_("hello"), '"hello"', id="np.str_"),
        pytest.param(np.bool_(True), "true", id="np.bool_"),
        pytest.param(np.uint8(123), "123", id="np.uint8"),
        pytest.param(np.uint16(123), "123", id="np.uint16"),
        pytest.param(np.uint32(123), "123", id="np.uint32"),
        pytest.param(np.uint64(123), "123", id="np.uint64"),
        pytest.param(np.int8(123), "123", id="np.int8"),
        pytest.param(np.int16(123), "123", id="np.int16"),
        pytest.param(np.int32(123), "123", id="np.int32"),
        pytest.param(np.int64(123), "123", id="np.int64"),
        pytest.param(np.float16(1.23), "1.23", id="np.float16"),
        pytest.param(np.float32(1.23), "1.23", id="np.float32"),
        pytest.param(np.float64(1.23), "1.23", id="np.float64"),
        pytest.param(np.float128(1.23), "1.23", id="np.float128"),
        pytest.param(np.array([[1, 2], [3, 4]]), "[[1,2],[3,4]]", id="array"),
        pytest.param(
            np.array([1, 2.3, "4.5"]), '["1","2.3","4.5"]', id="coerced array"
        ),
    ],
)
def test_inline_raw_dump(input_value, expected_json):
    if np.issubdtype(type(input_value), np.floating):
        assert InlineRaw(input_value).model_dump_json().startswith(expected_json)
    else:
        assert InlineRaw(input_value).model_dump_json() == expected_json


@pytest.mark.parametrize(
    "json_input, expected_value",
    [
        pytest.param('"hello"', np.array("hello"), id="str"),
        pytest.param("true", np.array(True), id="bool"),
        pytest.param("123", np.int64(123), id="int"),
        pytest.param("1.23", np.float64(1.23), id="float"),
        pytest.param(
            "[[1,2],[3,4]]", np.array([[1, 2], [3, 4]], dtype=np.int64), id="list"
        ),
        pytest.param(
            '["1","2.3"]', np.array(["1", "2.3"], dtype=np.str_), id="str list"
        ),
    ],
)
def test_inline_raw_load(json_input, expected_value):
    output = InlineRaw.model_validate_json(json_input).model_dump()
    assert np.array_equal(output, expected_value)
    assert output.dtype == expected_value.dtype


@pytest.mark.parametrize(
    "input_value",
    [
        pytest.param(complex(1, 2), id="complex"),
        pytest.param(float("nan"), id="nan"),
        pytest.param(float("inf"), id="inf"),
        pytest.param(np.complex128(1, 2), id="np.complex"),
        pytest.param(np.float64("nan"), id="np.nan"),
        pytest.param(np.float64("inf"), id="np.inf"),
        pytest.param(np.float64([1.0, "nan"]), id="nan in array"),
        pytest.param([1.0, float("nan")], id="nan in list"),
    ],
)
def test_inline_raw_forbidden_value(input_value):
    with pytest.raises(pydantic.ValidationError):
        _ = InlineRaw(input_value)


@pytest.mark.parametrize(
    "prefix, suffixes",
    [
        pytest.param("bool", [""], id="bool"),
        pytest.param("uint", ["8", "16", "32", "64"], id="uint"),
        pytest.param("int", ["8", "16", "32", "64"], id="int"),
        pytest.param("float", ["16", "32", "64"], id="float"),
        pytest.param("complex", ["64", "128", "256"], id="complex"),
    ],
)
def test_inline_dtype(prefix, suffixes):
    for suffix in suffixes:
        dtype = prefix + suffix
        Inline(dtype=dtype, value="foo")


@pytest.mark.parametrize(
    "input_value, expected_json",
    [
        pytest.param("hello", '"hello"', id="str"),
        pytest.param(["a", "bc"], '["a","bc"]', id="str list"),
        pytest.param(np.array(["a", "bc"]), '["a","bc"]', id="str array"),
        pytest.param(True, "true", id="bool"),
        pytest.param(123, "123", id="int"),
        pytest.param(1.23, "1.23", id="float"),
        pytest.param(float("nan"), '"nan"', id="nan"),
        pytest.param([float("nan"), 1.23], '["nan",1.23]', id="nan list"),
        pytest.param(np.uint8(123), "123", id="uint8"),
        pytest.param(np.int8(123), "123", id="int8"),
        pytest.param(np.float16(1.0), "1.0", id="float16"),
        pytest.param(np.float16(1.5), "1.5", id="float128"),
        pytest.param(np.float16("nan"), '"nan"', id="nan numpy"),
        pytest.param(np.float16(["nan", 4]), '["nan",4.0]', id="nan array"),
        pytest.param(np.float128(1.23), "1.23", id="float128"),
        pytest.param(np.complex128(1, 23), '"(1+23j)"', id="complex128"),
        pytest.param(np.int64(123), "123", id="int64"),
        pytest.param(np.float64(123), "123.0", id="float64"),
        pytest.param(np.int64([[1], [2]]), "[[1],[2]]", id="singleton lists"),
        pytest.param(
            np.arange(8, dtype=np.float64).reshape(4, 2),
            "[[0.0,1.0],[2.0,3.0],[4.0,5.0],[6.0,7.0]]",
            id="ndarray",
        ),
        pytest.param(
            np.array([[1, 2], [3, 4]], dtype=np.complex64),
            '[["(1+0j)","(2+0j)"],["(3+0j)","(4+0j)"]]',
            id="ndarray complex64",
        ),
        pytest.param(
            [
                [
                    np.uint8(1),
                    np.int64(2),
                ],
                [
                    np.float16("nan"),
                    np.float64(3.45),
                ],
                [
                    np.float32("inf"),
                    np.float64("-inf"),
                ],
                [
                    np.float128(6.78),
                    np.complex128(9, 1.0),
                ],
            ],
            '[[1,2],["nan",3.45],["inf","-inf"],[6.78,"(9+1j)"]]',
            id="ndlist",
        ),
    ],
)
def test_inline_value(input_value, expected_json):
    assert (
        Inline(dtype="bool", value=input_value).value.model_dump_json() == expected_json
    )


@pytest.mark.parametrize(
    "input_value",
    [
        pytest.param(None),
        pytest.param([123, None]),
        pytest.param({"foo": "bar"}),
        pytest.param([123, {"foo": "bar"}]),
    ],
)
def test_inline_forbidden_value(input_value):
    with pytest.raises(pydantic.ValidationError):
        Inline(dtype="int8", value=input_value)


@pytest.mark.parametrize(
    "json_input, expected_value",
    [
        pytest.param('{"type":"inline","dtype":"int8","value":-123}', np.int8(-123)),
        pytest.param(
            '{"type":"inline","dtype":"int16","value":[1,2,3]}', np.int16([1, 2, 3])
        ),
        pytest.param(
            '{"type":"inline","dtype":"float32","value":"nan"}',
            np.float32("nan"),
        ),
        pytest.param(
            '{"type":"inline","dtype":"float32","value":["nan","-inf", "inf", 1.23]}',
            np.float32(["nan", "-inf", "inf", 1.23]),
        ),
        pytest.param(
            '{"type":"inline","dtype":"complex64","value":"(nan+4.56j)"}',
            np.complex64(float("nan"), 4.56),
        ),
        pytest.param(
            '{"type":"inline","dtype":"complex128","value":["(1+2j)", "(3+4j)"]}',
            np.array([np.complex128(1, 2), np.complex128(3, 4)]),
        ),
        pytest.param(
            '{"type":"inline","dtype":"complex128","value":[123,1.23,"nan","(1+23j)"]}',
            np.complex128([123, 1.23, "nan", "(1+23j)"]),
        ),
    ],
)
def test_inline_load(json_input, expected_value):
    output = Inline.model_validate_json(json_input).decode()
    assert np.array_equal(output, expected_value, equal_nan=True)
    assert output.dtype == expected_value.dtype


@pytest.mark.parametrize(
    "json_input, expected_value",
    [
        pytest.param(
            '{"type":"inline_b64","shape":[],"dtype":"|i1","value":"hQ=="}',
            np.int8(-123),
        ),
        pytest.param(
            '{"type":"inline_b64","shape":[3],"dtype":"<i2","value":"AQACAAMA"}',
            np.int16([1, 2, 3]),
        ),
        pytest.param(
            '{"type":"inline_b64","shape":[],"dtype":"<f4","value":"AADAfw=="}',
            np.float32("nan"),
        ),
        pytest.param(
            '{"type":"inline_b64","shape":[4],"dtype":"<f4","value":"AADAfwAAgP8AAIB/pHCdPw=="}',
            np.float32(["nan", "-inf", "inf", 1.23]),
        ),
        pytest.param(
            '{"type":"inline_b64","shape":[],"dtype":"<c8","value":"AADAf4XrkUA="}',
            np.complex64(float("nan"), 4.56),
        ),
        pytest.param(
            '{"type":"inline_b64","shape":[2],"dtype":"<c16","value":"AAAAAAAA8D8AAAAAAAAAQAAAAAAAAAhAAAAAAAAAEEA="}',
            np.array([np.complex128(1, 2), np.complex128(3, 4)]),
        ),
        pytest.param(
            '{"type":"inline_b64","shape":[4],"dtype":"<c16","value":"AAAAAADAXkAAAAAAAAAAAK5H4XoUrvM/AAAAAAAAAAAAAAAAAAD4fwAAAAAAAAAAAAAAAAAA8D8AAAAAAAA3QA=="}',
            np.complex128([123, 1.23, "nan", "(1+23j)"]),
        ),
    ],
)
def test_inline_base64_load(json_input, expected_value):
    output = InlineBase64.model_validate_json(json_input).decode()
    assert np.array_equal(output, expected_value, equal_nan=True)
    assert output.dtype == expected_value.dtype
    assert output.shape == expected_value.shape


@pytest.mark.parametrize(
    "input_value",
    [
        pytest.param(123456),
        pytest.param(1.23456),
        pytest.param([1, 2, 3, 4]),
        pytest.param(np.array([1.0, 2.3], dtype="<f4")),
        pytest.param(np.array([1.0, 2.3], dtype=">f4")),
        pytest.param(
            np.float32("nan"),
        ),
        pytest.param(
            np.float128(["nan", "-inf", "inf", 1.23]),
        ),
        pytest.param(
            np.complex64(float("nan"), 4.56),
        ),
        pytest.param(
            np.array([np.complex128(1, 2), np.complex128(3, 4)]),
        ),
        pytest.param(
            np.complex128([123, 1.23, "nan", "(1+23j)"]),
        ),
    ],
)
def test_inline_base64_dump(input_value):
    in_array = np.asarray(input_value)

    shape = in_array.shape
    dtype = in_array.dtype.str
    value = base64.b64encode(in_array.tobytes())

    model = InlineBase64(dtype=dtype, shape=shape, value=value)
    json_value = model.model_dump_json()
    model_clone = InlineBase64.model_validate_json(json_value)
    output = model_clone.decode()
    assert np.array_equal(output, in_array, equal_nan=True)
    assert output.dtype == in_array.dtype
    assert output.shape == in_array.shape
