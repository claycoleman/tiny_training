import argparse
from utils import clean_project, build_project, deploy_binary


def main():
    parser = argparse.ArgumentParser(description="Build and deploy STM32 project")
    parser.add_argument("--clean", action="store_true", help="Clean before building")
    parser.add_argument(
        "--build-only", action="store_true", help="Only build, don't deploy"
    )
    parser.add_argument(
        "--deploy-only", action="store_true", help="Only deploy, don't build"
    )
    args = parser.parse_args()

    try:
        if args.deploy_only:
            deploy_binary()
            return

        if args.clean:
            clean_project()

        if not args.deploy_only:
            build_project()

        if not args.build_only:
            deploy_binary()

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
