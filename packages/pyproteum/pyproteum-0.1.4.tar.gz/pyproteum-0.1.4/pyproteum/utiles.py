import unittest
import os
import importlib

RED = '\033[31m'
GREEN = '\033[032m'
RESET = '\033[0m'

def red(s):
	if os.getenv('PYPROTEUMCOLOR') != None :
		return RED + str(s) + RESET
	return s 

def green(s):
	if os.getenv('PYPROTEUMCOLOR') != None :
		return GREEN + str(s) + RESET
	return s 



def get_test_files_with_discover(start_dir, pattern="test*.py"):
	loader = unittest.TestLoader()
	test_files = set()

	try:
		suite = loader.discover(start_dir, pattern=pattern)

	except:
		return test_files

	def _iter_suite(suite):
		for item in suite:
			if isinstance(item, unittest.TestSuite):
				_iter_suite(item)  # recursão direta
			else:
				module_name = item.__class__.__module__
				try:
					module = importlib.import_module(module_name)
					if hasattr(module, "__file__"):
							test_files.add(os.path.join(start_dir, os.path.basename(module.__file__)))  # só o nome curto
				except Exception:
					pass

	_iter_suite(suite)
	return test_files