from setuptools import setup, find_packages

setup(
	name='pyproteum',
	version='0.1',
	packages=find_packages(),
	install_requires=[
		'timeout-decorator',
		'peewee'
	],
	author='Delamaro',
	description='A tool for mutation testing in Python. Implemented as a Python module.',
	python_requires='>=3.10',
	# Note: 'pickle' is part of the Python standard library and should not be listed in install_requires.
)
