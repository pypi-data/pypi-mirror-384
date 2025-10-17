# The MIT License (MIT)
#
# Copyright (c) 2025 FourCIPP Authors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""Test yaml io utils."""

import pytest

from fourcipp.utils.dict_utils import sort_alphabetically
from fourcipp.utils.yaml_io import dict_to_yaml_string, dump_yaml, load_yaml


def test_dump_not_sorted(tmp_path):
    """Test if key order is preserved."""
    data = {"c": 1, "b": 2, "a": 3}
    sorted_file_path = tmp_path / "sorted.yaml"
    dump_yaml(data, path_to_yaml_file=sorted_file_path)
    reloaded_data = load_yaml(sorted_file_path)
    assert reloaded_data == data


def test_dump_sorted_alphabetically(tmp_path):
    """Test if key order is sorted."""
    data = {"c": 1, "b": 2, "a": 3}
    sorted_file_path = tmp_path / "sorted.yaml"
    dump_yaml(
        data, path_to_yaml_file=sorted_file_path, sort_function=sort_alphabetically
    )
    reloaded_data = load_yaml(sorted_file_path)
    assert list(reloaded_data.keys()) == sorted(data.keys())


@pytest.mark.parametrize(
    "use_fourcipp_yaml_style, expected",
    [
        (
            False,
            """SECTION:
  - vector:
      - 1.23
      - 2
      - 3
    nested_vector:
      - - 1
        - 2.0
        - 3
      - - 4.5
        - 5
        - 2.333
  - list_with_bool:
      - 1
      - true
      - 3
    list_with_null:
      - 1
      - null
      - 4
  - list_with_string:
      - 1
      - "abc"
      - 5
    nested_list_with_string:
      - - 1
        - 2.1
      - - 2
        - "def"
""",
        ),
        (
            True,
            """SECTION:
  - vector: [1.23, 2, 3]
    nested_vector: [[1, 2.0, 3], [4.5, 5, 2.333]]
  - list_with_bool:
      - 1
      - true
      - 3
    list_with_null:
      - 1
      - null
      - 4
  - list_with_string:
      - 1
      - "abc"
      - 5
    nested_list_with_string:
      - [1, 2.1]
      - - 2
        - "def"
""",
        ),
    ],
)
def test_yaml_style(use_fourcipp_yaml_style, expected):
    """Test yaml output style."""
    data = {
        "SECTION": [
            {"vector": [1.23, 2, 3], "nested_vector": [[1, 2.0, 3], [4.5, 5, 2.333]]},
            {"list_with_bool": [1, True, 3], "list_with_null": [1, None, 4]},
            {
                "list_with_string": [1, "abc", 5],
                "nested_list_with_string": [[1, 2.1], [2, "def"]],
            },
        ]
    }
    assert (
        dict_to_yaml_string(data, use_fourcipp_yaml_style=use_fourcipp_yaml_style)
        == expected
    )
