import argparse
import os
from pathlib import Path
import sys

from c2d.core import Converter
from c2d.docker import WarpBase


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        allow_abbrev=True, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "root_dir",
        help="Path to the root of the source code to wrap in a Docker container.",
    )
    parser.add_argument(
        "--config",
        "-c",
        default="./warp_ci.yaml",
        help='Configuration file, with path absolute or relative to the root directory. Default: "./warp_ci.yaml"',
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="dockerfiles",
        help="Path to output generated Dockerfile-s. Default to `dockerfiles`",
    )
    parser.add_argument(
        "--as_text",
        "-t",
        # The below defaults to False (i.e create a physical Dockerfile) Pass flag without value for text output
        action="store_true",
        help="Output physical Dockerfile. Default: True",
    )

    args = parser.parse_args(args)

    conv = Converter()

    dockerfiles = conv.process(args.config, as_text=args.as_text)

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    for idx, df in enumerate(dockerfiles.values()):
        suffix = ""
        # Build the dockerfile if it's an object, otherwise just print out the string to the console (for now)
        if isinstance(df, WarpBase):
            if hasattr(df, "job_name") and len(dockerfiles) > 1:
                suffix = f"_{df.job_name}"
            df.dump(os.path.join(args.output_dir, f"Dockerfile{suffix}"))
        else:
            print(df)


if __name__ == "__main__":
    main()
