import argparse
import logging
from pathlib import Path

from .config import Config
from .server import App


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="/etc/raphson-music-headless.json", help="path to configuration file")
    parser.add_argument("-q", "--quiet", action="store_true", help="reduce logging output")
    args = parser.parse_args()

    if not args.quiet:
        logging.basicConfig(level=logging.INFO)

    config = Config.load(Path(args.config))
    app = App(config)
    app.start(config)


if __name__ == '__main__':
    main()
