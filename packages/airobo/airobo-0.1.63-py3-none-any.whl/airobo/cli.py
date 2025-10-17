"""
airobo/cli.py

CLI for the airobo tool.
"""
import argparse
from airobo.api import publish, version
from airobo.utils.env import load_env_from_known_locations

commands = {
    "publish": publish,
    "version": version,
}


#---------------------------------------------------------------------------------------------------------

def main():
    # Load env vars from common locations (won't override pre-set env)
    # This lets users keep C:\airoboEnv or ~/airoboEnv instead of a local .env
    # Load repo and signing env vars from known locations
    load_env_from_known_locations(verbose=False, keys=(
        "gitURL", "gitBranch",
        # Android signing
        "AIROBO_SIGN_STORE_FILE",
        "AIROBO_SIGN_STORE_PASSWORD",
        "AIROBO_SIGN_STORE_TYPE",
        "AIROBO_SIGN_KEY_ALIAS",
        "AIROBO_SIGN_KEY_PASSWORD",
        # common fallbacks
        "STORE_PASSWORD",
        "KEY_PASSWORD",
    ))
    parser = argparse.ArgumentParser(prog='airobo')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create publish subparser with optional platform argument
    publish_parser = subparsers.add_parser('publish', help='Publish app to stores')
    publish_parser.add_argument('platform', nargs='?', choices=['ios', 'android'], 
                               help='Platform to publish to (optional, defaults to both)')
    
    # Create version subparser
    subparsers.add_parser('version', help='Show version')

    args = parser.parse_args()

    # Handle commands
    if args.command == 'publish':
        # Pass the platform argument to publish function
        platform = getattr(args, 'platform', None)
        publish(platform)
    elif args.command == 'version':
        version()
    else:
        parser.print_help()

#---------------------------------------

if __name__ == "__main__":
    main()