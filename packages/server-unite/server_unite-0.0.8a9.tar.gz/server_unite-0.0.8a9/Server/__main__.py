import argparse

from . application import Application



def parse_args():
	parser = argparse.ArgumentParser(prog="Server", description="Manage server deployment")
	subparsers = parser.add_subparsers(dest="command")

	create_parser = subparsers.add_parser("create", help="Create a new server")
	create_parser.add_argument('repository', help="Repository URL")

	add_parser = subparsers.add_parser("add", help="Add a repository")
	add_parser.add_argument('path', help="Relative path to repository")

	list_parser = subparsers.add_parser("list", help="List repositories")

	update_parser = subparsers.add_parser("update", help="Update server repositories")

	start_parser = subparsers.add_parser("start", help="Start server")
	stop_parser = subparsers.add_parser("stop", help="Stop server")

	process_parser = subparsers.add_parser("process", help="Process event")
	process_parser.add_argument('path', help="Event path")

	args = parser.parse_args()
	if args.command is None:
		parser.print_help()
		return

	return args



def main():
	args = parse_args()
	if args is None:
		return

	Application.Run(args)

if __name__ == '__main__':
	main()
