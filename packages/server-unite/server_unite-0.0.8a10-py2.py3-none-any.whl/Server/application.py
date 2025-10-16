import sys
import click
import socket
import logging
import importlib

from Git import Git, Repositories
from . repository import Repository
from . configuration import Configuration

logging.basicConfig(level=logging.DEBUG)



class Application:

	@classmethod
	def Initialize(self):
		Repository.Initialize()

	@classmethod
	def Run(self, args):
		self.Initialize()
		Configuration.Initialize()
		configuration = Configuration()

		application = self(configuration, args)
		status = application.run()

		if status:
			configuration.Write()

	def __init__(self, configuration, args):
		self.configuration = configuration
		self.command = args.command
		self.args = args

	def run(self):
		function = {
			'create': self.Create,
			'add': self.Add,
			'list': self.List,
			'start': self.Start,
			'stop': self.Stop,
			'update': self.Update,
			'process': self.Process,
		}

		fn = function[self.command]
		return fn()

	def hostname(self):
		return socket.gethostname()

	def Create(self):
		hostname = self.hostname()
		service = self.args.repository

		status = []
		for r in ("webhook", "router", "certbot"):
			repository = Repository(f'server/{hostname}/{r}')
			done = repository.Clone(service, errors=False)
			if not done:
				click.echo("Failed " + click.style(f"{repository.project}", fg="red"))
			status.append(done)

		if any(status):
			self.configuration['repository'] = repository
			return True

		return False

	def Add(self):
		service = self.configuration.get('repository', None)
		if service is None:
			logging.error("No server deployment found")
			return False

		repository = Repository(self.args.path)
		if repository.Exists():
			logging.error(f'Error: {repository.project} exists')
			return False

		status = repository.Clone(service, errors=False)
		if status:
			message = "Cloned " + click.style(f"{repository.project}", fg='green')
		else:
			message = "Could not clone " + click.style(f"{repository.project}", fg='red')

		click.echo(message)
		return status

	def Update(self):
		Git.Initialize(Repository.ROOT)
		for repository in Repositories():
			try:
				repository.pull()
				message = click.style('updated', fg='green')
			except Exception as e:
				message = click.style(f'{e}', fg='red')

			path = repository.path.relative_to(Repository.ROOT)
			click.echo(f'{path} ' + message)

	def List(self):
		Git.Initialize(Repository.ROOT)
		for repository in Repositories():
			path = repository.path.relative_to(Repository.ROOT)
			click.echo(f'{path}')

	def Start(self):
		Git.Initialize(Repository.ROOT, cached=False)

	def Stop(self):
		Git.Initialize(Repository.ROOT)

	def handler(self):
		path = Repository.ROOT / 'webhook'
		if not path.exists():
			return

		if len(sys.path) == 0 or sys.path[0] != path:
			sys.path.insert(0, str(path))

		try:
			return importlib.import_module('Handler')
		except ModuleNotFoundError:
			return

	def Process(self):
		handler = self.handler()
		if handler is None:
			logging.error("Handler could not be imported")
			return

		host = handler.Get()
		if host is None:
			logging.error("No actions registered for this host")
			return

		host = host(self.args.path)

		action = host.Handle()
		if action is None:
			logging.error(f"No actions registered for {self.args.path}")
			return

		print(action)

		self.process(host, action, self.args.path)

	def process(self, host, action, path):
		repository = Repository(path)

		if not self.process_repository_clone(repository, action):
			logging.error("Clone failed")
			return

		if not self.process_repository_update(repository, action):
			logging.error("Update failed")
			return

		# @TODO:
		# Stop > build > start is a bad order of operations.
		# The correct order is build > stop > start
		# (reduced down time, container keeps running if the
		# build fails)
		# But `docker compose down` doesn't work if the
		# image tag changes, so for now, stop comes first.

		if not self.process_repository_stop(repository, action):
			logging.error("Could not stop")
			return

		if not self.process_repository_build(repository, action):
			logging.error("Could not build")
			return

		if not self.process_repository_start(repository, action):
			logging.error("Could not start")
			return

	def process_repository_clone(self, repository, action):
		if repository.Exists():
			logging.info("clone - repository exists")
			return True

		if not action.clone:
			logging.info("clone - action says don't clone")
			return False

		if not self.process_clone(repository):
			return False

		return True

	def process_clone(self, repository):
		service = self.configuration.get('repository', None)
		if service is None:
			logging.error("No server deployment found")
			return False

		return repository.Clone(service, errors=False)

	def process_repository_update(self, repository, action):
		if repository.cloned_now:
			return True

		return repository.Update() == 0

	def process_repository_stop(self, repository, action):
		if action.deploy is False:
			return True

		if action.deploy is True:
			return repository.Stop() == 0

		# @TODO: Allow another
		# repository to manage
		# deployment
		return False

	def process_repository_build(self, repository, action):
		if action.method == 'PULL':
			return repository.Pull() == 0

		if action.method == 'BUILD':
			return repository.Build() == 0

		return False

	def process_repository_start(self, repository, action):
		if action.deploy is False:
			return True

		if action.deploy is True:
			return repository.Start() == 0

		# @TODO: Allow another
		# repository to manage
		# deployment
		return False

	def propagate(repository, host, action):
		pass
