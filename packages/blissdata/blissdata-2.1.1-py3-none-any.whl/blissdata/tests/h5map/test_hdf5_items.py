from blissdata.h5map import (
    HDF5Item,
    DataItem,
    InlineRaw,
    Inline,
    Dataset,
    Group,
    SoftLink,
    ExternalLink,
    ExternalBinaryDataset,
    VirtualDataset,
)


def test_dataset_inline_raw():
    dataset = Dataset(attributes={"foo": "bar"}, value=123)
    # fmt: off
    expected_json = (
        '{\n'
        '  "type": "dataset",\n'
        '  "attributes": {\n'
        '    "foo": "bar"\n'
        '  },\n'
        '  "value": 123\n'
        '}'
    )
    # fmt: on
    assert dataset.model_dump_json(indent=2) == expected_json

    # with no attributes, only values are dumped
    dataset = Dataset(value=123)
    expected_json = "123"
    assert dataset.model_dump_json() == expected_json

    # The value can be a Dataset or an InlineRaw model depending on what is
    # expected from it (hdf5 or data).
    as_hdf5_item = HDF5Item.validate_json(expected_json)
    as_data_item = DataItem.validate_json(expected_json)
    assert isinstance(as_hdf5_item, Dataset)
    assert isinstance(as_data_item, InlineRaw)


def test_dataset_inline():
    dataset = Dataset(
        attributes={"foo": "bar"}, value=Inline(dtype="uint32", value=123)
    )
    # fmt: off
    json_dataset = (
        '{\n'
        '  "type": "dataset",\n'
        '  "attributes": {\n'
        '    "foo": "bar"\n'
        '  },\n'
        '  "value": {\n'
        '    "type": "inline",\n'
        '    "dtype": "uint32",\n'
        '    "value": 123\n'
        '  }\n'
        '}'
    )
    # fmt: on
    assert dataset.model_dump_json(indent=2) == json_dataset

    # with no attributes, only values are dumped
    dataset = Dataset(value=Inline(dtype="uint32", value=123))
    # fmt: off
    json_dataset = (
        '{\n'
        '  "type": "inline",\n'
        '  "dtype": "uint32",\n'
        '  "value": 123\n'
        '}'
    )
    # fmt: on
    assert dataset.model_dump_json(indent=2) == json_dataset

    # The value can be a Dataset or an Inline model depending on what is
    # expected from it (hdf5 or data).
    as_hdf5_item = HDF5Item.validate_json(json_dataset)
    as_data_item = DataItem.validate_json(json_dataset)
    assert isinstance(as_hdf5_item, Dataset)
    assert isinstance(as_data_item, Inline)
    assert as_hdf5_item == dataset


def test_attributes():
    group = Group(
        attributes={"attr1": [1, 2.3], "attr2": Inline(dtype="float32", value="nan")},
    )
    # fmt: off
    json_group = (
        '{\n'
        '  "type": "group",\n'
        '  "attributes": {\n'
        '    "attr1": [\n'
        '      1.0,\n'
        '      2.3\n'
        '    ],\n'
        '    "attr2": {\n'
        '      "type": "inline",\n'
        '      "dtype": "float32",\n'
        '      "value": "nan"\n'
        '    }\n'
        '  }\n'
        '}'
    )
    # fmt: on
    assert group.model_dump_json(indent=2) == json_group

    # make sure it goes both directions
    group_from_json = HDF5Item.validate_json(json_group)
    assert group_from_json == group


def test_group():
    c1 = Dataset(value=1.23)
    c2 = SoftLink(target_path="local/path")
    c3 = ExternalLink(target_path="local/path", target_file="remote/path")
    c4 = Group()
    group = Group(
        attributes={"myattr": "dummy"},
        children={"child1": c1, "child2": c2, "child3": c3, "child4": c4},
    )
    # fmt: off
    json_group = (
        '{\n'
        '  "type": "group",\n'
        '  "attributes": {\n'
        '    "myattr": "dummy"\n'
        '  },\n'
        '  "children": {\n'
        '    "child1": 1.23,\n'
        '    "child2": {\n'
        '      "type": "soft_link",\n'
        '      "target_path": "local/path"\n'
        '    },\n'
        '    "child3": {\n'
        '      "type": "external_link",\n'
        '      "target_file": "remote/path",\n'
        '      "target_path": "local/path"\n'
        '    },\n'
        '    "child4": {\n'
        '      "type": "group"\n'
        '    }\n'
        '  }\n'
        '}'
    )
    # fmt: on
    assert group.model_dump_json(indent=2) == json_group

    # make sure it goes both directions
    group_from_json = HDF5Item.validate_json(json_group)
    assert group_from_json == group


def test_external_binary_dataset():
    dataset = ExternalBinaryDataset(
        dtype=">u4",
        shape=[4, 128],
        files=[
            {"name": "a.bin", "offset": 0, "size": 1024},
            {"name": "b.bin", "offset": 1024},
        ],
    )

    # fmt: off
    json_dataset = (
        '{\n'
        '  "type": "external_binary_dataset",\n'
        '  "dtype": ">u4",\n'
        '  "shape": [\n'
        '    4,\n'
        '    128\n'
        '  ],\n'
        '  "files": [\n'
        '    {\n'
        '      "name": "a.bin",\n'
        '      "offset": 0,\n'
        '      "size": 1024\n'
        '    },\n'
        '    {\n'
        '      "name": "b.bin",\n'
        '      "offset": 1024\n'
        '    }\n'
        '  ]\n'
        '}'
    )
    # fmt: on
    assert dataset.model_dump_json(indent=2, exclude_none=True) == json_dataset

    # make sure it goes both directions
    dataset_from_json = HDF5Item.validate_json(json_dataset)
    assert dataset_from_json == dataset


def test_virtual_dataset():
    vds = VirtualDataset(
        dtype=">f2",
        shape=[1024, 3],
        virtual_sources=[
            {
                "vspace": {
                    "start": [3, 0],
                    "stride": [1, 1],
                    "count": [1, 1],
                    "block": [3, 1024],
                },
                "src_file": "file.h5",
                "src_dataset": "/data_path_a",
                "src_space": {"start": [0, 0], "count": [1, 1], "block": [1024, 3]},
            },
        ],
    )

    # fmt: off
    json_vds = (
        '{\n'
        '  "type": "virtual_dataset",\n'
        '  "dtype": ">f2",\n'
        '  "shape": [\n'
        '    1024,\n'
        '    3\n'
        '  ],\n'
        '  "virtual_sources": [\n'
        '    {\n'
        '      "vspace": {\n'
        '        "start": [\n'
        '          3,\n'
        '          0\n'
        '        ],\n'
        '        "count": [\n'
        '          1,\n'
        '          1\n'
        '        ],\n'
        '        "block": [\n'
        '          3,\n'
        '          1024\n'
        '        ]\n'
        '      },\n'
        '      "src_file": "file.h5",\n'
        '      "src_dataset": "/data_path_a",\n'
        '      "src_space": {\n'
        '        "start": [\n'
        '          0,\n'
        '          0\n'
        '        ],\n'
        '        "count": [\n'
        '          1,\n'
        '          1\n'
        '        ],\n'
        '        "block": [\n'
        '          1024,\n'
        '          3\n'
        '        ]\n'
        '      }\n'
        '    }\n'
        '  ]\n'
        '}'
    )
    # fmt: on
    assert vds.model_dump_json(indent=2, exclude_none=True) == json_vds

    # make sure it goes both directions
    vds_from_json = HDF5Item.validate_json(json_vds)
    assert vds_from_json == vds
