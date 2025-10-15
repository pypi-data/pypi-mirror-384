import re

import click


class Model:
    def __init__(self, f, out_names):
        self.f = f
        self.out_names = out_names


def convert_to_model(val):
    if isinstance(val, Model):
        return val
    else:
        return Model(val, None)


def convert_to_dict(val):
    dictConv = {}
    for k in val.keys():
        dictConv[k] = val[k]
        dictConv[k]["scores"] = val[k]["scores"].tolist()
    return dictConv


def use_transformer(predictor_host: str):
    return predictor_host.replace("predictor", "transformer")


def use_predictor(predictor_host: str):
    return predictor_host.replace("transformer", "predictor")


def validate_project_name(ctx, param, project_name):
    if re.match(r"\w+$", project_name):
        return project_name
    else:
        raise click.BadParameter("Name can only include alphanumeric characters and underscores")
