# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

import argparse
import os
import shutil

try:
    from importlib.resources import files
except ImportError:
    # Fallback for Python < 3.9
    from importlib_resources import files


def main():
    parser = argparse.ArgumentParser(description="Extract Project Aria Client Samples.")
    parser.add_argument(
        "--output", "-o", dest="output", help="Output directory", default=os.getcwd()
    )
    args = parser.parse_args()

    # Location in package install
    samples_gen1 = str(files("aria").joinpath("samples"))
    samples_gen2 = str(files("aria").joinpath("gen2_samples"))

    # Destination directory
    output_gen1 = os.path.join(args.output, "projectaria_client_sdk_samples")
    output_gen2 = os.path.join(args.output, "projectaria_client_sdk_samples_gen2")

    if os.path.exists(output_gen1):
        prompt = f"Directory {output_gen1} already exists, would you like to replace it? [y/N]: "
        if input(prompt).lower().strip() == "y":
            print(f"Removing existing directory {output_gen1}")
            shutil.rmtree(output_gen1)
        else:
            print(f" Not replacing directory, please extract to a different directory")
            exit(1)

    if os.path.exists(output_gen2):
        prompt = f"Directory {output_gen2} already exists, would you like to replace it? [y/N]: "
        if input(prompt).lower().strip() == "y":
            print(f"Removing existing directory {output_gen2}")
            shutil.rmtree(output_gen2)
        else:
            print(f" Not replacing directory, please extract to a different directory")
            exit(1)

    # Copy samples to output directory
    print(f"Extracting gen1 samples to {output_gen1}")
    shutil.copytree(samples_gen1, output_gen1)

    print(f"Extracting gen2 samples to {output_gen2}")
    shutil.copytree(samples_gen2, output_gen2)


if __name__ == "__main__":
    main()
