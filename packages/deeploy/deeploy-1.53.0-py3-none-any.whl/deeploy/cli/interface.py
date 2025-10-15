# This is derived from Kserve and modified by Deeploy
# Copyright 2021 The KServe Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import logging
import pprint
from collections import ChainMap
from functools import partial

import attr
import numpy as np

logger = logging.getLogger(__name__)


class DeeployPrettyPrinter(pprint.PrettyPrinter):
    """
    Overrides the built in dictionary pretty representation\
          to look more similar to the external
    prettyprinter library.
    """

    _dispatch = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # `sort_dicts` kwarg was only introduced in Python 3.8
        # so we just override it here.
        # Before Python 3.8 the printing was done in insertion order by default.
        self._sort_dicts = False

    def _pprint_dict(self, object, stream, indent, allowance, context, level):
        # Add a few newlines and the appropriate indentation to dictionary printing
        # compare with https://github.com/python/cpython/blob/3.9/Lib/pprint.py
        write = stream.write
        indent += self._indent_per_level
        write("{\n" + " " * (indent + 1))
        if self._indent_per_level > 1:
            write((self._indent_per_level - 1) * " ")
        length = len(object)
        if length:
            if self._sort_dicts:
                items = sorted(object.items(), key=pprint._safe_tuple)
            else:
                items = object.items()
            self._format_dict_items(items, stream, indent, allowance + 1, context, level)
        write("}\n" + " " * (indent - 1))

    _dispatch[dict.__repr__] = _pprint_dict


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(
            obj,
            (
                np.int_,
                np.intc,
                np.intp,
                np.int8,
                np.int16,
                np.int32,
                np.int64,
                np.uint8,
                np.uint16,
                np.uint32,
                np.uint64,
            ),
        ):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


deeploy_pformat = partial(DeeployPrettyPrinter().pformat)


@attr.s
class Explanation:
    """
    Explanation class returned by explainers.
    """

    meta: dict = attr.ib(repr=deeploy_pformat)
    data: dict = attr.ib(repr=deeploy_pformat)

    def __attrs_post_init__(self):
        """
        Expose keys stored in `self.meta` and `self.data` as attributes of the class.
        """
        for key, value in ChainMap(self.meta, self.data).items():
            setattr(self, key, value)

    def to_json(self) -> str:
        """
        Serialize the explanation data and metadata into a `json` format.

        Returns
        -------
        String containing `json` representation of the explanation.
        """
        return json.dumps(attr.asdict(self), cls=NumpyEncoder)

    @classmethod
    def from_json(cls, jsonrepr) -> "Explanation":
        """
        Create an instance of an `Explanation` class using a `json` representation\
              of the `Explanation`.

        Parameters
        ----------
        jsonrepr
            `json` representation of an explanation.

        Returns
        -------
        An Explanation object.
        """
        dictrepr = json.loads(jsonrepr)
        try:
            meta = dictrepr["meta"]
            data = dictrepr["data"]
        except KeyError:
            logger.exception("Invalid explanation representation")
        return cls(meta=meta, data=data)

    def __getitem__(self, item):
        """
        This method is purely for deprecating previous behaviour \
            of accessing explanation
        data via items in the returned dictionary.
        """
        import warnings

        msg = "The Explanation object is not a dictionary anymore \
                  and accessing elements should be done via attribute access. \
                Accessing via item will stop working in a future version."
        warnings.warn(msg, DeprecationWarning, stacklevel=2)
        return getattr(self, item)
