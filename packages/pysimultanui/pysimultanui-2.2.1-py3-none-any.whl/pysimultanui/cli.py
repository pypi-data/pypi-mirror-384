import os
import argparse
from .main_ui import run_ui as run_web_ui

parser = argparse.ArgumentParser(
    prog='PySimultanUI',
    description='Run PySimultanUI',
    epilog='')


parser.add_argument("--title", required=False, default='PySimultan Web UI', type=str)
parser.add_argument("--dark", required=False, default=False, type=bool)
parser.add_argument("--reload", required=False, default=False, type=bool)
parser.add_argument("--port", required=False, default=8080, type=int)
parser.add_argument("--uvicorn_logging_level", required=False)
parser.add_argument("--endpoint_documentation", required=False)
parser.add_argument("--storage_secret", required=False)


def run_ui():

    args = parser.parse_args()

    run_web_ui(title=args.title,
               dark=args.dark,
               reload=args.reload,
               port=args.port,
               uvicorn_logging_level=args.uvicorn_logging_level,
               endpoint_documentation=args.endpoint_documentation,
               storage_secret=args.storage_secret if args.storage_secret is not None else
               os.environ.get('STORAGE_SECRET', 'my_secret6849')
               )
