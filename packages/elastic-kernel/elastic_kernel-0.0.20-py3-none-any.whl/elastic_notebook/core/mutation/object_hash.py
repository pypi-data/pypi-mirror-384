import copy
import io
import logging
from inspect import isclass
from types import FunctionType, ModuleType

import lightgbm
import networkx as nx
import numpy as np
import pandas as pd
import scipy
import torch
import xxhash

BASE_TYPES = [type(None), FunctionType]

logger = logging.getLogger("ElasticNotebookLogger")


class ImmutableObj:
    def __init__(self):
        pass

    def __eq__(self, other):
        if isinstance(other, ImmutableObj):
            return True
        return False


# Object representing none.
class NoneObj:
    def __init__(self):
        pass

    def __eq__(self, other):
        if isinstance(other, NoneObj):
            return True
        return False


# Object representing a dataframe.
class DataframeObj:
    def __init__(self):
        pass

    def __eq__(self, other):
        if isinstance(other, DataframeObj):
            return True
        return False


class NxGraphObj:
    def __init__(self, graph):
        self.graph = graph

    def __eq__(self, other):
        if isinstance(other, NxGraphObj):
            return nx.graphs_equal(self.graph, other.graph)
        return False


class NpArrayObj:
    def __init__(self, arraystr):
        self.arraystr = arraystr
        pass

    def __eq__(self, other):
        if isinstance(other, NpArrayObj):
            return self.arraystr == other.arraystr
        return False


class ScipyArrayObj:
    def __init__(self, arraystr):
        self.arraystr = arraystr
        pass

    def __eq__(self, other):
        if isinstance(other, ScipyArrayObj):
            return self.arraystr == other.arraystr
        return False


class TorchTensorObj:
    def __init__(self, arraystr):
        self.arraystr = arraystr
        pass

    def __eq__(self, other):
        if isinstance(other, TorchTensorObj):
            return self.arraystr == other.arraystr
        return False


class ModuleObj:
    def __init__(self):
        pass

    def __eq__(self, other):
        if isinstance(other, ModuleObj):
            return True
        return False


# Object representing general unserializable class.
class UnserializableObj:
    def __init__(self):
        pass

    def __eq__(self, other):
        if isinstance(other, UnserializableObj):
            return True
        return False


class UncomparableObj:
    def __init__(self):
        pass

    def __eq__(self, other):
        if isinstance(other, UncomparableObj):
            return True
        return False


def construct_object_hash(obj, deepcopy=False):
    """
    Construct an object hash for the object. Uses deep-copy as a fallback.
    """

    if type(obj) in BASE_TYPES:
        return ImmutableObj()

    if isclass(obj):
        return type(obj)

    # Flag hack for Pandas dataframes: each dataframe column is a numpy array.
    # All the writeable flags of these arrays are set to false; if after cell execution, any of these flags are
    # reset to True, we assume that the dataframe has been modified.
    if isinstance(obj, pd.DataFrame):
        for _, col in obj.items():
            col.__array__().flags.writeable = False
        return DataframeObj()

    if isinstance(obj, pd.Series):
        obj.__array__().flags.writeable = False
        return DataframeObj()

    attr_str = getattr(obj, "__module__", None)
    if attr_str and (
        "matplotlib" in attr_str
        or "transformers" in attr_str
        or "networkx" in attr_str
        or "keras" in attr_str
        or "tensorflow" in attr_str
    ):
        return UncomparableObj()

    # Object is file handle
    if isinstance(obj, io.IOBase):
        return UncomparableObj()

    if isinstance(obj, np.ndarray):
        h = xxhash.xxh3_128()
        h.update(np.ascontiguousarray(obj.data))
        str1 = h.intdigest()
        return NpArrayObj(str1)

    if isinstance(obj, scipy.sparse.csr_matrix):
        h = xxhash.xxh3_128()
        h.update(np.ascontiguousarray(obj))
        str1 = h.intdigest()
        return ScipyArrayObj(str1)

    if isinstance(obj, torch.Tensor):
        h = xxhash.xxh3_128()
        h.update(np.ascontiguousarray(obj))
        str1 = h.intdigest()
        return TorchTensorObj(str1)

    if isinstance(obj, ModuleType) or isclass(obj):
        return ModuleObj()

    # Polars dataframes are immutable.
    # if isinstance(obj, pl.DataFrame):
    #    return type(obj)

    # LightGBM dataframes are immutable.
    if isinstance(obj, lightgbm.Dataset):
        return type(obj)

    # Try to hash the object; if the object is unhashable, use deepcopy as fallback.
    try:
        h = xxhash.xxh3_128()
        if hasattr(obj, "__bytes__"):
            # Use object's __bytes__ method if available
            obj_bytes = bytes(obj)
        elif hasattr(obj, "tobytes"):
            # For numpy-like objects with tobytes method
            obj_bytes = obj.tobytes()
        else:
            # Fallback to string representation
            obj_bytes = str(obj).encode("utf-8")

        h.update(obj_bytes)
        return h.intdigest()
    except Exception as e:
        logger.error(f"Error hashing object: {obj}")
        logger.error(f"Error: {e}")
        try:
            if deepcopy:
                return copy.deepcopy(obj)
            else:
                return obj
        except Exception:
            # If object is not even deepcopy-able, mark it as unserializable and assume modified-on-write.
            return UnserializableObj()
