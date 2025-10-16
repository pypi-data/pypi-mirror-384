import yaml
import pathlib



class Configuration:

	ROOT = pathlib.Path('~/.config/Server').expanduser().resolve()

	@classmethod
	def Initialize(self):
		self.first_run = not self.ROOT.exists()
		if not self.first_run:
			return

		self.ROOT.mkdir(parents=True, exist_ok=True)

	def __init__(self):
		self.path = self.ROOT / 'configuration.yaml'
		self.changed = False
		if self.first_run:
			self.store = {}
		else:
			self.store = self.Read()

	def __setitem__(self, *args, **kwargs):
		self.changed = True
		return self.store.__setitem__(*args, **kwargs)

	def __getitem__(self, *args, **kwargs):
		return self.store.__setitem__(*args, **kwargs)

	def __delitem__(self, *args, **kwargs):
		self.changed = True
		return self.store.__setitem__(*args, **kwargs)

	def get(self, *args, **kwargs):
		return self.store.get(*args, **kwargs)

	def Read(self):
		if not self.path.exists():
			return {}

		with open(self.path, "r") as f:
			return yaml.load(f, Loader=yaml.CSafeLoader)

	def Write(self):
		if not self.changed:
			return

		with open(self.path, "w") as f:
			yaml.dump(self.store, f, default_flow_style=False, Dumper=yaml.CSafeDumper)
