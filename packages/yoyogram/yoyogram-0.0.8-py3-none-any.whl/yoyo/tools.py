import os
import sys
from pathlib import Path


def listdir(file: __file__):
	return os.listdir(os.path.dirname(file))

def listpath(file: __file__):
	path = Path(file).resolve()
	parts = list(path.parts)
	if parts[0].endswith("\\"):
		parts[0] = parts[0][:-1]
	return parts

def package(file: __file__):
	project_root = Path(sys.modules['__main__'].__file__).resolve().parent
	current_path = Path(file).resolve()
	relative_path = current_path.relative_to(project_root).parent
	return ".".join(relative_path.with_suffix('').parts)

def basename(file: __file__):
	return file.split(os.sep)[-2]
