import json
import uuid
import pandas
import time

from .script import Script
from .plot import Plot
from .wizard_function import WizardStep, WizardFunction
from .ds_dataframe import DSDataFrame


class DSAPIEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, Script):
            json_obj = {
                "id": str(obj.script_id),
                "name": str(obj.name),
                "description": str(obj.description),
                "canGeneratePlot": str(obj.canGeneratePlot),
                "canGenerateModel": str(obj.canGenerateModel),
                "canGenerateData": str(obj.canGenerateData),
                "status": str(obj.status),
                "needExactColumnNumbers": str(obj.needExactColumnNumbers),
                "needExactColumnNames": str(obj.needExactColumnNames),
                "inputColumns": list(obj.inputColumns),
                "outputColumns": list(obj.outputColumns)
            }
            return json_obj
        if isinstance(obj, DSDataFrame):
            json_obj = {
                "id": str(obj.df_id)
            }
            if obj.generatedById is not None:
                json_obj["generatedById"] = str(obj.generatedById)
            return json_obj
        if isinstance(obj, Plot):
            return obj.to_json()
        if isinstance(obj, pandas.Timestamp):
            return int(time.mktime(obj.timetuple()) * 1000)
        if isinstance(obj, WizardStep):
            json_obj = {
                "id": obj.step_id,
                "order": obj.order
            }
            return json_obj
        if isinstance(obj, WizardFunction):
            json_obj = {
                "title": obj.title,
                "function": obj.function,
                "is_beta": str(obj.is_beta),
                "steps": obj.steps
            }
            return json_obj
        else:
            type_name = obj.__class__.__name__
            raise TypeError("Unexpected type {0}".format(type_name))
