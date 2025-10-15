from typing import List, Iterator
from .api_dto import ApiDto


def get_bool(obj, name: str):
    if isinstance(obj[name], str) and obj[name].lower() == "false":
        return False
    else:
        return bool(obj[name])


class ModelInfo:
    """
    define a pointer to a machine learning model.

    :ivar model_type str: mlflow model flavour
    """

    def __init__(self,
                 key: str,
                 twin_hardware_id: str = None,
                 property_value: str = None,
                 alias: str = None,
                 model_type: str = None,
                 file_format: str = 'pkl',
                 source: str = 'wizata',
                 property_name: str = None
                 ):
        # information identifying a model
        self.key = key
        self.twin_hardware_id = twin_hardware_id
        self.property_value = property_value
        self.alias = alias
        self.file_format = file_format
        self.source = source
        self.model_type = model_type

        # files attached to model when loaded
        self.trained_model = None
        self.scaler = None

        # temporary properties during model generation not generally stored
        self.property_name = property_name
        self.input_columns = None
        self.has_target_feat = False
        self.label_counts = 0


    def identifier(self, include_alias: bool = False) -> str:
        """
        returns the complete string identifier for this model.
        :param include_alias: include the alias pointer or leave it to target the default version.
        :return: complete identifier of a model.
        """
        if self.key is None:
            raise KeyError('please specific a model key')
        identifier = self.key

        if self.twin_hardware_id is not None:
            identifier += f".{self.twin_hardware_id}"

        if self.property_value is not None:
            identifier += f".{self.property_value}"

        if include_alias and self.alias is not None:
            identifier += f"@{self.alias}"

        return identifier

    def to_json(self):
        """
        convert this entity in a dict that can be json serializable
        :return: dict
        """
        obj = {
            "key": self.key,
            "file_format": self.file_format,
            "source": self.source
        }
        if self.twin_hardware_id is not None:
            obj["twin_hardware_id"] = str(self.twin_hardware_id)
        if self.property_value is not None:
            obj["property_value"] = self.property_value
        if self.alias is not None:
            obj["alias"] = self.alias
        if self.model_type is not None:
            obj["model_type"] = self.model_type
        if self.file_format is not None:
            obj["file_format"] = self.file_format
        if self.source is not None:
            obj["source"] = self.source
        if self.property_name is not None:
            obj["property_name"] = self.property_name
        if self.identifier is not None:
            obj["identifier"] = self.identifier(include_alias=True)
        return obj

    def from_json(self, obj):
        """
        load this entity from a dict
        """
        if "key" in obj.keys():
            self.key = obj["key"]
        if "twin_hardware_id" in obj.keys():
            self.twin_hardware_id = obj["twin_hardware_id"]
        if "property_value" in obj.keys():
            self.property_name = obj["property_value"]
        if "alias" in obj.keys():
            self.alias = obj["alias"]
        if "model_type" in obj.keys():
            self.model_type = obj["model_type"]
        if "file_format" in obj.keys():
            self.key = obj["file_format"]
        if "source" in obj.keys():
            self.source = obj["source"]
        if "property_name" in obj.keys():
            self.property_name = obj["property_name"]


class ModelList:
    """
    used to conveniently manipulate a list of models.
    """

    def __init__(self):
        self.models: List[ModelInfo] = []

    def __iter__(self) -> Iterator[ModelInfo]:
        return iter(self.models)

    def __len__(self) -> int:
        return len(self.models)

    def __getitem__(self, index: int) -> ModelInfo:
        return self.models[index]

    def append(self, model: ModelInfo):
        self.models.append(model)


class MLModelConfig(ApiDto):
    """
    a model config defines execution properties within a pipeline.
    usually to define how a pipeline should train and predict with your model.

    :ivar format: by default 'pkl' for pickle, accept 'pt' for PyTorch model using tensors (none = 'pkl')
    :ivar bool by_twin: define if pipeline need to train and use different model by twin item.
    :ivar bool by_property: define if pipeline need to train and use different model based on 'property_name'.
    :ivar list features: datapoint list to refine columns if necessary.
    :ivar str function: name of the function used instead of 'predict' on model inference.
    :ivar str model_key: key of the model to store (or use story property if dynamic).
    :ivar str model_type: reserved for 'mlflow' defines model flavor such as 'sklearn' or 'pyfunc'.
    :ivar str model_alias: reserved for 'mlflow' set the alias to target and use inside a pipeline.
    :ivar str model_format: type of model (by default 'pkl') accept also 'pt' for PyTorch model using tensors (none = 'pkl')
    :ivar dict properties_mapping: dict to map properties expected by the script with the properties from the context.
    :ivar str property_name: define which property is looked for when using 'by_property'.
    :ivar str source: define name of model storage to use 'wizata'.
    :ivar str|list target_feat: target feature name(s) to remove from df in 'predict' mode.
    :ivar str train_script: name of function referencing the script to train the model.
    :ivar float train_test_split_pct: percentage repartition to split the data for training and scoring.
    :ivar str train_test_split_type: type of splitting desired to split the train dataframe.
    :ivar bool output_append: true - default - append output to input dataframe. false to retrieve only 'predict' column(s).
    :ivar list output_columns_names: name list to rename columns inside output dataframe.
    :ivar str output_prefix: set a prefix to put before output column names (default or custom).
    """

    def __init__(self,
                 train_script=None,
                 train_test_split_pct: float = 1.0,
                 train_test_split_type: str = "ignore",
                 function: str = "predict",
                 properties_mapping=None,
                 target_feat=None,
                 output_append: bool = True,
                 output_columns_names: list = None,
                 output_prefix: str = None,
                 features: list = None,
                 model_key: str = None,
                 model_type: str = None,
                 model_alias: str = None,
                 model_format: str = 'pkl',
                 by_twin: bool = False,
                 by_property: bool = False,
                 property_name: str = None,
                 source: str = "wizata"
                 ):

        # training
        self.train_script = train_script
        self.train_test_split_pct = train_test_split_pct
        self.train_test_split_type = train_test_split_type
        self.function = function
        self.properties_mapping = properties_mapping

        # features management
        self.target_feat = target_feat
        self.features = features
        self.output_columns_names = output_columns_names
        self.output_append = output_append
        self.output_prefix = output_prefix

        # key and identification
        self.model_key = model_key
        self.by_twin = by_twin
        self.by_property = by_property
        self.property_name = property_name
        self.model_format = model_format

        # source
        self.source = source
        self.model_type = model_type
        self.model_alias = model_alias

    def create_model_info(self,
                          hardware_id: str = None,
                          property_value: str = None) -> ModelInfo:
        """
        create model info corresponding to the configuration.
        :param hardware_id: provide a hardware id for this model if by_twin.
        :param property_value: provide a value for this model if by_property.
        :return:
        """
        if self.by_twin and hardware_id is None:
            raise ValueError('hardware_id is required if by_twin to create a model info')
        if self.by_property and property_value is None:
            raise ValueError('property_value is required if by_property to create a model info')
        model_info = ModelInfo(
            key=self.model_key,
            twin_hardware_id=hardware_id,
            property_value=property_value,
            source=self.source,
            alias=self.model_alias,
            file_format=self.model_format,
            model_type=self.model_type,
            property_name=self.property_name
        )
        return model_info

    def from_json(self, obj):

        # Managed deprecated fields
        if "model_key_type" in obj.keys() and obj["model_key_type"] is not None:
            if obj["model_key_type"] == "template":
                self.by_twin = True
            elif obj["model_key_type"] == "variable":
                self.by_property = True
                if "model_key" not in obj.keys() or obj["model_key"] is None:
                    raise KeyError('model_key must be declared in the config.')
                self.property_name = obj["model_key"]

        # training info
        if "train_script" in obj.keys() and obj["train_script"] is not None:
            self.train_script = obj["train_script"]
        if "train_test_split_pct" in obj.keys() and obj["train_test_split_pct"] is not None:
            self.train_test_split_pct = float(obj["train_test_split_pct"])
        if "train_test_split_type" in obj.keys() and obj["train_test_split_type"] is not None:
            self.train_test_split_type = obj["train_test_split_type"]
        if "function" in obj.keys() and obj["function"] is not None:
            self.function = obj["function"]
        if "properties_mapping" in obj:
            self.properties_mapping = obj["properties_mapping"]

        # features info
        if "target_feat" in obj.keys() and obj["target_feat"] is not None:
            if isinstance(obj["target_feat"], str) or isinstance(obj["target_feat"], list):
                self.target_feat = obj["target_feat"]
            else:
                raise ValueError(f'target_feat should be a str or a list with columns name to remove.')

        if "features" in obj.keys() and obj["features"] is not None:
            self.features = obj["features"]

        # output management
        if "output_append" in obj.keys():
            self.output_append = get_bool(obj, name="output_append")

        if "output_prefix" in obj.keys() and obj["output_prefix"] is not None:
            self.output_prefix = obj["output_prefix"]
        if "output_columns_names" in obj.keys() and obj["output_columns_names"] is not None:
            if isinstance(obj["output_columns_names"], str):
                self.output_columns_names = [obj["output_columns_names"]]
            elif isinstance(obj["output_columns_names"], list):
                self.output_columns_names = obj["output_columns_names"]
            else:
                raise ValueError(f'output_property or output_columns_names should be a list or a string')
        elif "output_property" in obj.keys() and obj["output_property"] is not None \
                and obj["output_property"] != "result":
            if isinstance(obj["output_property"], str):
                self.output_columns_names = [obj["output_property"]]
            elif isinstance(obj["output_property"], list):
                self.output_columns_names = obj["output_property"]
            else:
                raise ValueError(f'output_property or output_columns_names should be a list or a string')

        # source
        if "source" in obj.keys() and obj["source"] is not None:
            self.source = obj["source"]
            if self.source not in ["wizata", "mlflow"]:
                raise ValueError("source must be wizata or mlflow")

        # key and target
        if "model_key" not in obj.keys() or obj["model_key"] is None:
            raise KeyError('model_key must be declared in the config.')
        self.model_key = obj["model_key"]
        if "by_twin" in obj.keys():
            self.by_twin = get_bool(obj, name="by_twin")
        if "by_property" in obj.keys():
            self.by_property = get_bool(obj, name="by_property")
        if "property_name" in obj.keys() and obj["property_name"] is not None:
            self.property_name = obj["property_name"]
        if "model_type" in obj.keys() and obj["model_type"] is not None:
            self.model_type = obj["model_type"]
        if "model_alias" in obj.keys() and obj["model_alias"] is not None:
            self.model_alias = obj["model_alias"]
        if "model_format" in obj.keys() and obj["model_format"] is not None:
            self.model_format = obj["model_format"]

    def to_json(self, target: str = None):
        obj = {
            "source": self.source
        }

        # training info
        if self.train_script is not None:
            obj["train_script"] = str(self.train_script)
        if self.train_test_split_pct is not None:
            obj["train_test_split_pct"] = float(self.train_test_split_pct)
        if self.train_test_split_type is not None:
            obj["train_test_split_type"] = str(self.train_test_split_type)
        if self.features is not None:
            obj["features"] = self.features
        if self.properties_mapping is not None and isinstance(self.properties_mapping, dict):
            obj["properties_mapping"] = self.properties_mapping

        # features info
        if self.target_feat is not None:
            obj["target_feat"] = self.target_feat
        if self.output_append is not None:
            obj["output_append"] = str(self.output_append)
        if self.output_columns_names is not None:
            obj["output_columns_names"] = self.output_columns_names
        if self.output_prefix is not None:
            obj["output_prefix"] = self.output_prefix
        if self.function is not None:
            obj["function"] = self.function

        # key and target
        if self.model_key is not None:
            obj["model_key"] = self.model_key
        if self.model_type is not None:
            obj["model_type"] = self.model_type
        if self.model_alias is not None:
            obj["model_alias"] = self.model_alias
        if self.by_twin is not None:
            obj["by_twin"] = str(self.by_twin)
        if self.by_property is not None:
            obj["by_property"] = str(self.by_property)
        if self.property_name is not None:
            obj["property_name"] = self.property_name
        if self.model_format  is not None:
            obj["model_format"] = self.model_format

        return obj

    def has_target_feat(self) -> bool:
        """
        determine if configuration possess a target feature
        """
        if self.target_feat is None:
            return False

        if isinstance(self.target_feat, str):
            return True
        elif isinstance(self.target_feat, list):
            if len(self.target_feat) == 0:
                return False
            else:
                return True
        else:
            raise TypeError(f'unsupported target_feat type {self.target_feat.__class__.__name__}')

