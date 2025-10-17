import pandas
from .mlmodel import ModelInfo


def predict(df: pandas.DataFrame, model_info: ModelInfo, mapping_table=None):
    """
    Execute a Machine Learning models locally.
    :param df: dataframe to use as input.
    :param model_info: model information handler.
    :param mapping_table: Optional mapping table.
    :return: output dataframe with predicted values.
    """
    if model_info is None or model_info.trained_model is None or model_info.input_columns is None:
        raise ValueError("Please download your model from DS API before using it.")
    old_index = df.index
    df.index = pandas.to_datetime(df.index)
    df_result = pandas.DataFrame(index=df.index)
    features = model_info.input_columns
    if model_info.has_target_feat is True:
        df_result['result'] = model_info.trained_model.detect(df[features]).astype(float)
    else:
        df_result['result'] = model_info.trained_model.predict(df[features]).astype(float)
    if model_info.label_counts != 0:
        df_result[__generate_label_columns(model_info.label_counts)] = \
            model_info.trained_model.predict_proba(df[features]).astype(float)
    df_result = df_result.set_index(old_index)
    return df_result


def __generate_label_columns(label_count):
    """
    Generate a list of columns based on number of desired labels.
    :param label_count: Number of desired labels.
    :return: list of labels generated.
    """
    i = 0
    columns = []
    while i < label_count:
        columns.append("prob_" + str(i) + "_label")
        i = i + 1
    return columns
