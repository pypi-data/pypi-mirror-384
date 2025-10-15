import argparse

from kserve import model_server

DEFAULT_MODEL_NAME = "default"
DEFAULT_NTHREAD = "1"


def parse_args_model(system_args):
    parser = argparse.ArgumentParser(parents=[model_server.parser])
    parser.add_argument("--model_dir", help="A URI pointer to the model directory")
    parser.add_argument(
        "--nthread",
        default=DEFAULT_NTHREAD,
        help="Number of threads to use by the custom model.",
    )
    args, _ = parser.parse_known_args(system_args)
    return args
