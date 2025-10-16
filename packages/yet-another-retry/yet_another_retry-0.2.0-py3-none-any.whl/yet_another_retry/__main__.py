import argparse
from . import __version__
import sys

def main():
    parser = argparse.ArgumentParser(description="Yet Another Retry")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}", help="Prints current installed version")


    if len(sys.argv) == 1:
        parser.print_help()

    args = parser.parse_args()
    

if __name__ == "__main__":
    main()