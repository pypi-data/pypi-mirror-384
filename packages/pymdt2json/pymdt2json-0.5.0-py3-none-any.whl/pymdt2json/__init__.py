from .src.parser import MinifyMDT
from .src.cli import create_parser

__version__ = "0.1.0"
__all__ = ["MinfyMDT"]


def main():
    create_parser()
