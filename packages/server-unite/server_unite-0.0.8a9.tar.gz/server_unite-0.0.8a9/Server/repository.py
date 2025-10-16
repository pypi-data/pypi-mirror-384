import logging
import pathlib

from Git import Repository as GitRepository
from . shell import Run



def command(name):
	path = pathlib.Path(__file__).parent / f'script/{name}'
	path = path.resolve().absolute()

	return [f"{path}"]



class Repository:

	ROOT = pathlib.Path('~/source').expanduser().resolve()

	@classmethod
	def Initialize(self):
		if self.ROOT.exists():
			return

		self.ROOT.mkdir(parents=True, exist_ok=True)

	def __init__(self, path):
		self.project = path
		self.path = self.ROOT / path
		self.cloned_now = False

	def Exists(self):
		return self.path.exists()

	def Clone(self, service, errors=True):
		link = f'{service}/{self.project}.git'
		logging.info(f"Cloning {link} at {self.path}")

		try:
			GitRepository.Clone(link, self.path)
			self.cloned_now = True
			return True

		except Exception:
			if errors:
				raise
			return False

	def Build(self):
		return Run(command('build.sh'), self.path)

	def Pull(self):
		return Run(command('pull.sh'), self.path)

	def Update(self):
		return Run(command('update.sh'), self.path)

	def Restart(self):
		return Run(command('restart.sh'), self.path)

	def Start(self):
		script_override = self.path / 'control/container/start'
		if script_override.exists():
			script = [f'{script_override}']
		else:
			script = command('start.sh')

		return Run(script, self.path)

	def Stop(self):
		script_override = self.path / 'control/container/stop'
		if script_override.exists():
			script = [f'{script_override}']
		else:
			script = command('stop.sh')

		return Run(script, self.path)
