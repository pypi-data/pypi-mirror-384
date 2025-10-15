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

import argparse
import logging
import os

import kserve

logging.basicConfig(level=kserve.constants.KSERVE_LOGLEVEL)

DEFAULT_TRANSFORMER_NAME = "transformer"


class GroupedAction(argparse.Action):  # pylint:disable=too-few-public-methods
    def __call__(self, theparser, namespace, values, option_string=None):
        group, dest = self.dest.split(".", 2)
        groupspace = getattr(namespace, group, argparse.Namespace())
        setattr(groupspace, dest, values)
        setattr(namespace, group, groupspace)


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    if v.lower() in ("no", "false", "f", "n", "0"):
        return False
    raise argparse.ArgumentTypeError("Boolean value expected.")


def parse_args_transformer(sys_args):
    parser = argparse.ArgumentParser(
        parents=[kserve.model_server.parser], conflict_handler="resolve"
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default=DEFAULT_TRANSFORMER_NAME,
        help="The name of transformer.",
    )
    parser.add_argument(
        "--predictor_host", type=str, help="The host for the predictor", required=True
    )
    parser.add_argument(
        "--explainer_host", type=str, help="The host for the explainer", required=False
    )
    args, _ = parser.parse_known_args(sys_args)
    if "INTERNAL_EXPLAINER" in os.environ and os.environ["INTERNAL_EXPLAINER"] == "True":
        args.explainer_host = args.predictor_host
    else:
        args.explainer_host = args.predictor_host.replace("predictor", "explainer")
    return args
