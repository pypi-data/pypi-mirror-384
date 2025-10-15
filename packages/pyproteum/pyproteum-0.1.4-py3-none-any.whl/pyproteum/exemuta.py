import types, sys, ast, multiprocessing
import sys, csv
import os,io
from pyproteum.models.models import *
import unittest
import pickle
import types
from pyproteum.moperators.myoperator import *
from pyproteum.tcase import change_dir_connect
from pyproteum.tcase import load_module, get_all_test_names, _ensure_module_hierarchy
from pyproteum.utiles import red,green
import timeout_decorator
import inspect


class RegistrandoResultado(unittest.TextTestResult):
	def __init__(self, stream, descriptions, verbosity, number, research):
		super().__init__(stream, descriptions, verbosity)
		self.my_successes = []  # armazena os testes que passaram
		self.timeouts = []
		self.all = []		# todos os testes executados
		self.all_order = {}
		self.order = number
		self.count = 0
		self.research = research

	def startTest(self, test):
		self.all.append(test)
		self.count += 1
		self.all_order[test.id()] = '{}:{}'.format(self.order, self.count)
		super().startTest(test)

	def addSuccess(self, test):
		self.my_successes.append(test)
		super().addSuccess(test)

	def stopTest(self, test):
		super().stopTest(test)
	
	def addFailure(self, test, err):
		etype, evalue, tb = err
		# Marcação explícita de TIMEOUT
		if getattr(etype, "__name__", "") in ("TimeoutError", "TimeoutError_", "TimeoutException"):
			# opcional: anotar em um campo extra
			self.timeouts.append(test)				
		super().addFailure(test, err)
		if not self.research:
			self.stop()

	def addError(self, test, err):
		etype, evalue, tb = err
		# Marcação explícita de TIMEOUT
		if getattr(etype, "__name__", "") in ("TimeoutError", "TimeoutError_", "TimeoutException"):
			# opcional: anotar em um campo extra
			self.timeouts.append(test)		
		super().addError(test, err)
		if not self.research:
			self.stop()


class RegistrandoRunner(unittest.TextTestRunner):

	def __init__(self, *args, number=0, research=False, **kwargs):
		super().__init__(*args, **kwargs)
		self.number = number
		self.research = research

	def _makeResult(self):
		return RegistrandoResultado(self.stream, self.descriptions, self.verbosity, self.number,self.research)




def create_module_from_astx(nome_modulo, arvore_ast):
	modulo = types.ModuleType(nome_modulo)
	code = compile(arvore_ast, filename="<ast>", mode="exec")
	exec(code, modulo.__dict__)
	sys.modules[nome_modulo] = modulo
	return modulo

import types, sys, multiprocessing, os, io
from contextlib import redirect_stdout

def _check_ast_executesx(code_obj, nome, suppress_output):
	# Executa apenas para ver se trava
	modulo = types.ModuleType(nome)

	if suppress_output:
		with open(os.devnull, 'w') as fnull:
			out = sys.stdout
			err = sys.stderr
			sys.stdout = stderr = fnull
			exec(code_obj, modulo.__dict__)
			sys.stdout = out
			sys.stderr = err
	else:
		exec(code_obj, modulo.__dict__)

def create_module_from_astxx(nome_modulo, arvore_ast, timeout=3, suppress_output=True):
	code = compile(arvore_ast, filename="<ast>", mode="exec")

	# Executa o código compilado em um subprocesso apenas para validar
	p = multiprocessing.Process(target=_check_ast_executes, args=(code, nome_modulo, suppress_output))
	p.start()
	p.join(timeout)

	if p.is_alive():
		p.terminate()
		p.join()
		raise TimeoutError(f"O módulo '{nome_modulo}' não respondeu em {timeout} segundos.")

	# Se passou no teste, agora podemos executar de verdade no processo principal
	modulo = types.ModuleType(nome_modulo)

	if suppress_output:
		with open(os.devnull, 'w') as fnull:
			out = sys.stdout
			err = sys.stderr
			sys.stdout = stderr = fnull
			exec(code, modulo.__dict__)
			sys.stdout = out
			sys.stderr = err
	else:
		exec(code, modulo.__dict__)

	sys.modules[nome_modulo] = modulo
	return modulo




def _check_ast_executes(code_obj, path_filename, suppress_output):
	module_name, parent, parts = _ensure_module_hierarchy(path_filename)

	modulo = types.ModuleType(module_name)
	if suppress_output:
		with open(os.devnull, 'w') as fnull:
			old_out, old_err = sys.stdout, sys.stderr
			sys.stdout, sys.stderr = fnull, fnull
			try:
				exec(code_obj, modulo.__dict__)
			finally:
				sys.stdout, sys.stderr = old_out, old_err
	else:
		exec(code_obj, modulo.__dict__)

	sys.modules[module_name] = modulo
	if parent is not None:
		setattr(parent, parts[-1], modulo)

def create_module_from_ast(path_filename, arvore_ast, timeout=3, suppress_output=True):
	code = compile(arvore_ast, filename="<ast>", mode="exec")

	# Testa em subprocesso com timeout
	p = multiprocessing.Process(target=_check_ast_executes, args=(code, path_filename, suppress_output))
	p.start()
	p.join(timeout)
	if p.is_alive():
		p.terminate()
		p.join()
		raise TimeoutError(f"O módulo '{path_filename}' não respondeu em {timeout} segundos.")

	# Executa de verdade no processo principal
	module_name, parent, parts = _ensure_module_hierarchy(path_filename)

	modulo = types.ModuleType(module_name)
	if suppress_output:
		with open(os.devnull, 'w') as fnull:
			old_out, old_err = sys.stdout, sys.stderr
			sys.stdout, sys.stderr = fnull, fnull
			try:
				exec(code, modulo.__dict__)
			finally:
				sys.stdout, sys.stderr = old_out, old_err
	else:
		exec(code, modulo.__dict__)

	sys.modules[module_name] = modulo
	if parent is not None:
		setattr(parent, parts[-1], modulo)

	return modulo




def __exec():
	session_name = sys.argv[-1]
	directory = None
	i = 2
	keep = False
	verbose = False
	while i < len(sys.argv[:-1]):
		s = sys.argv[i]
		match s:
			case '--D':
				i += 1
				directory = sys.argv[i]
			case '--keep':
				keep = True
			case '--v':
				verbose = True
			case _:
				usage()
				return
		i += 1
	
	change_dir_connect(directory, session_name)
	session = Session.get(Session.id==1)
	rse = session.type == 'research'

	fields = get_all_test_names()
	Execution = create_exec_db(fields)

	cont_dead = 0
	cont_live = 0
	cont_equiv = 0

	with db.atomic():
		for muta in Mutant:
			reg_muta = Execution.create(mutant=muta)

			if muta.status == 'equiv':
				cont_equiv += 1
				reg_muta.save()
				continue

			if keep and muta.status != 'live' and not rse:
				cont_dead += 1
				reg_muta.save()
				continue

			print('Mutant {} -- {}'.format(muta.id, muta.operator))
			tree = pickle.loads(muta.ast)
			create_module_from_ast(muta.source.filename, tree)

			#print(reg_muta)
			dead = False
			for testfile in TestCase:
				try: 
					nll = open(os.devnull, 'w')
					err = sys.stderr
					out = sys.stdout
					sys.stdout = sys.stderr = nll					
					module_test = load_module(testfile.filename)
					aplicar_timeout_em_tests(module_test)
					suite = unittest.TestLoader().loadTestsFromModule(module_test)
					resultado = RegistrandoRunner(stream=io.StringIO(), research=rse,verbosity=0,number=testfile.id).run(suite)
					sys.stdout = out
					sys.stderr = err
				except Exception as ex:
					sys.stdout = out
					sys.stderr = err					
					print(red(f'Error. Can not run test file {testfile}'))
					print(red(ex))
					sys.exit()
				
				for test in resultado.my_successes:
					t = resultado.all_order[test.id()]
					if verbose:
						print(f'{t} passed.')
					setattr(reg_muta, test.id(), 'live')
					reg_muta.save()
					
				for test,_ in resultado.failures:
					t = resultado.all_order[test.id()]
					if test in resultado.timeouts:
						s = 'timeout'
					else:
						s = 'fail'
					if verbose:
						print(f'{t} {s}.')
					
					setattr(reg_muta, test.id(), s)
					reg_muta.save()				
					dead = True
					

				for test,_ in resultado.errors:
					t = resultado.all_order[test.id()]
					if verbose:
						print(f'{t} error.')
					setattr(reg_muta, test.id(), 'error')
					reg_muta.save()
					dead = True
				if dead and not rse:
					break

					
			if dead:
				muta.status = 'dead'
				print('Dead')
				cont_dead += 1
				muta.save()
			else:
				cont_live += 1
				muta.status = 'live'
				muta.save()
	
	print(green(f'Alive: {cont_live}'))
	print(green(f'Dead: {cont_dead}'))
	print(green(f'Equivalent: {cont_equiv}'))
	if cont_live+cont_dead == 0:
		print(green('Mutation score: {:.2f}'.format(0.0)))
	else:
		print(green('Mutation score: {:.3f}'.format(cont_dead/(cont_live+cont_dead))))

	
def create_exec_db(fields):
	model_dict = { 'mutant' : ForeignKeyField(Mutant, backref='executed')}
	fields = sorted(fields)
	for r in fields:
		model_dict[r] = TextField(default='No Exec')	
	Execution = criar_modelo('Execution', model_dict)
	db.drop_tables([Execution])
	db.create_tables([Execution])
	return Execution

TIMEOUT_SEGUNDOS = 2

def aplicar_timeout_em_tests(modulo):
	for nome, obj in inspect.getmembers(modulo):
		if inspect.isclass(obj) and issubclass(obj, unittest.TestCase):
			for metodo_nome, metodo in inspect.getmembers(obj, inspect.isfunction):
				if metodo_nome.startswith("test_"):
					setattr(obj, metodo_nome, timeout_decorator.timeout(TIMEOUT_SEGUNDOS, use_signals=False)(metodo))
	
def __csv():
	session_name = sys.argv.pop()
	directory = None
	outname = None
	i = 2
	while i < len(sys.argv[:-1]):
		s = sys.argv[i]
		match s:
			case '--D':
				i += 1
				directory = sys.argv[i]
			case '--O':
				i += 1
				outname = sys.argv[i]
			case _:
				usage()
				return
		i += 1

	change_dir_connect(directory, session_name)

	if outname is None:
		outname = session_name+'.csv'

	try:
		Execution = get_table_model('Execution')
	except Exception as ex:
		print(red('Previous execution not found. Try "exemuta.py --exec" before exporting'))
		print(red(ex))
		sys.exit()

	try:
		with open(outname, 'w') as out:
			writer = csv.writer(out)
			campos = [field.name for field in Execution._meta.sorted_fields]
			campos.remove('id')
			writer.writerow(campos)
			for registro in Execution.select():
				writer.writerow([getattr(registro, campo) for campo in campos])
		print(f'{outname} successfully generated')
	except Exception as ex:
		print(red(f'Could not generate {outname}'))
		print(red(ex))
		sys.exit()


def __equiv():
	session_name = sys.argv[-1]
	directory = None
	list_number = None
	i = 2
	while i < len(sys.argv[:-1]):
		s = sys.argv[i]
		match s:
			case '--D':
				i += 1
				directory = sys.argv[i]
			case '--x':
				i += 1
				list_number = sys.argv[i]
			case _:
				usage()
				return
		i += 1


	try: 
		change_dir_connect(directory, session_name)
	except Exception as ex:
		print(red(f'Can not access test session'))
		print(red(ex))
		sys.exit()	

	# se os número não foram fornecidos, marca todos os vivos
	if  list_number is None:
		list_number = [] 
		for numero in Mutant.select().where(Mutant.status == "live"):
			list_number.append(numero.id)
	else:
		list_number = list_number.split()

	with db.atomic():
		for muta_number in list_number:
			try:
				muta_number = int(muta_number)
				reg_muta = Mutant.get(Mutant.id==muta_number)
				print('Mutant: ', reg_muta.id)
				if not reg_muta.status in ['live','equiv']:
					print(f'Warning: mutant {reg_muta.id} is not alive. It is {reg_muta.status}')
				else:
					reg_muta.status = 'equiv'
					reg_muta.save()
			except Exception as ex:
				print(red(f'Can not access mutant number {muta_number}'))
				print(red(ex))
				#sys.exit()

def main():
	n = len(sys.argv)-2
	if n < 1:
		usage()
	
	if sys.argv[1] == '--exec':
		__exec()
		return
	elif sys.argv[1] == '--csv':
		__csv()
		return
	elif sys.argv[1] == '--equiv':
		__equiv()
		return
	else:
		usage()


def usage():
	print('Usage:')
	print('exemuta --exec [--keep] [--D <directory> ]  <session name>')
	print('\tExecute the mutants with the test cases in the session')
	print('\t--keep: execute only the live mutants')
	print('exemuta --csv [--D <directory> ]  <session name>')
	print('\tExports the last execution to a csv file')
	print('exemuta --equiv --x <list of numbers> [--D <directory> ]  <session name>')
	print('\tMarks mutants as equivalents') 
	sys.exit()

if __name__ == '__main__' :
	main()
