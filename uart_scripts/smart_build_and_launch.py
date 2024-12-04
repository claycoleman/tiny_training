import argparse

from utils import smart_build_and_deploy


def main():
    parser = argparse.ArgumentParser(description="Build and deploy STM32 project")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    try:
        smart_build_and_deploy(verbose=args.verbose)

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
