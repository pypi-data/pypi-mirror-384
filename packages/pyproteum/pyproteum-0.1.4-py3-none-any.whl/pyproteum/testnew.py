import argparse
import os, sys
from pyproteum.models.models import *
import pickle
import ast
from pyproteum.utiles import red,green

def main():
	parser = argparse.ArgumentParser(description="Create a new test session for a Python program")


	# Flags exclusivas --test ou --research
	group = parser.add_mutually_exclusive_group()
	group.add_argument("--test", action="store_true", help="Create a regular test session (default)")
	group.add_argument("--research", action="store_true", help="Create a research session")

	# Parâmetros opcionais
	parser.add_argument("--S", dest="source_files", action="append", help="Name of a source file; use multiple --S for multiple files")
	parser.add_argument("--D", dest="directory", help="Directory where the session will be created")

	# Nome da sessão de teste (obrigatório e posicional)
	parser.add_argument("session_name", help="Name of the test session")

	args = parser.parse_args()

	# Atribui valores padrão se não fornecidos
	source_files = args.source_files or [args.session_name+'.py']
	if args.directory is None or args.directory == '.':
		directory = os.getcwd()
	else:
		directory = args.directory
		
	session_type = "research" if args.research else "test"

	# Saída (poderia ser substituída pela criação real dos arquivos)
	print(f"Creating a {session_type} test session...")
	print(f"Session name: {args.session_name}")
	print(f"Source files: {', '.join(sf for sf in source_files)}")
	print(f"Directory: {directory}")



	dbname = args.session_name+'.db'
	try: 
		if directory:
			os.chdir(directory)
		if os.path.exists(dbname):
			os.remove(dbname)
		database = SqliteDatabase(dbname)
		db.initialize(database)  # aqui o proxy é vinculado ao banco real
		db.pragma('foreign_keys', 1, permanent=True)
	except Exception as ex:
		print(red(f'Can not find database {dbname}'))
		print(red(ex))
		sys.exit()


	database.drop_tables([Session, TestCase, Mutant,])
	database.create_tables([Session, TestCase, Mutant])
	for srcname in source_files:
		try: 
			f = open(srcname)
			src = f.read().replace('\t', '    ')
			axt = ast.parse(src)
		except FileNotFoundError as ex:
			print(red(f'Can not use source file: {srcname}'))
			print(red(ex))
			sys.exit()			
		except Exception as ex:
			print(red(f'Can not use source file: {srcname}'))
			print(red(ex))
			f.close()
			sys.exit()			
		
		Session.create( filename=srcname,
			type = session_type,
			) 
	

	print("Test session created successfully.")

if __name__ == "__main__":
	main()
