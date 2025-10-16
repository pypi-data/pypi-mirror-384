import base64
import os
from typing import List

from databricks.ml_features_common.entities._feature_store_object import (
    _FeatureStoreObject,
)
from databricks.ml_features_common.entities.data_type import DataType
from databricks.ml_features_common.protos.feature_store_serving_pb2 import (
    FeatureFunctionForServing as ProtoFeatureFunctionForServing,
)
from databricks.ml_features_common.protos.feature_store_serving_pb2 import (
    FeatureFunctionParameterInfo as ProtoFeatureFunctionParameterInfo,
)
from databricks.ml_features_common.protos.feature_store_serving_pb2 import (
    FeatureFunctionsForServing as ProtoFeatureFunctionsForServing,
)


class FeatureFunctionParameterInfo(_FeatureStoreObject):
    def __init__(self, type_text: str, type_json: str, name: str, type_name: DataType):
        self._type_text = type_text
        self._type_json = type_json
        self._name = name
        self._type_name = type_name

    @property
    def type_text(self) -> str:
        return self._type_text

    @property
    def type_json(self) -> str:
        return self._type_json

    @property
    def name(self) -> str:
        return self._name

    @property
    def type_name(self) -> DataType:
        return self._type_name

    @classmethod
    def from_proto(cls, the_proto: ProtoFeatureFunctionParameterInfo):
        return cls(
            type_text=the_proto.type_text,
            type_json=the_proto.type_json,
            name=the_proto.name,
            type_name=the_proto.type_name,
        )


class FeatureFunctionForServing(_FeatureStoreObject):
    def __init__(
        self,
        full_name: str,
        input_params: List[FeatureFunctionParameterInfo],
        data_type: DataType,
        full_data_type: str,
        routine_definition: str,
    ):
        self._full_name = full_name
        self._input_params = input_params
        self._data_type = data_type
        self._full_data_type = full_data_type
        self._routine_definition = routine_definition

    @property
    def full_name(self) -> str:
        return self._full_name

    @property
    def input_params(self) -> List[FeatureFunctionParameterInfo]:
        return self._input_params

    @property
    def data_type(self) -> DataType:
        return self._data_type

    @property
    def full_data_type(self) -> str:
        return self._full_data_type

    @property
    def routine_definition(self) -> str:
        return self._routine_definition

    @classmethod
    def from_proto(cls, the_proto: ProtoFeatureFunctionForServing):
        return cls(
            full_name=the_proto.full_name,
            input_params=[
                FeatureFunctionParameterInfo.from_proto(input_param)
                for input_param in the_proto.input_params
            ],
            data_type=the_proto.data_type,
            full_data_type=the_proto.full_data_type,
            routine_definition=the_proto.routine_definition,
        )


class FeatureFunctionsForServing(_FeatureStoreObject):
    DATA_FILE = "feature_functions_for_serving.dat"

    def __init__(self, ff_for_serving: List[FeatureFunctionForServing]):
        self._ff_for_serving = ff_for_serving

    @property
    def ff_for_serving(
        self,
    ) -> List[FeatureFunctionForServing]:
        return self._ff_for_serving

    @classmethod
    def from_proto(cls, the_proto: ProtoFeatureFunctionsForServing):
        ff_for_serving_objs = [
            FeatureFunctionForServing.from_proto(ff_for_serving)
            for ff_for_serving in the_proto.ff_for_serving
        ]
        return cls(ff_for_serving=ff_for_serving_objs)

    @classmethod
    def load(cls, path: str):
        """
        Loads a FeatureFunctionsForServing object from a base64 encoded proto representation.
        """
        proto = ProtoFeatureFunctionsForServing()
        with open(os.path.join(path, cls.DATA_FILE), "rb") as f:
            proto.ParseFromString(base64.b64decode(f.read()))
        return cls.from_proto(proto)
