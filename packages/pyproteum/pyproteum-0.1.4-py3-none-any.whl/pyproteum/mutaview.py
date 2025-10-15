
import ast
import pickle
from pyproteum.tcase import change_dir_connect
from pyproteum.models.models import *
from pyproteum.print_visit import PrintVisit
from pyproteum.mutaviewgui import mutaview_gui
import sys
from pyproteum.utiles import red,green



class MutaView(ast.NodeTransformer):
	
	def __init__(self, ast, function):
		self.ast = ast
		self.function = function
		self.source = None


	def go_visit(self):
		self.visit(self.ast) 
	
	
	def visit_FunctionDef(self, node):
		if node.name != self.function:
			self.generic_visit(node)
			return
		self.source = ast.unparse(node)


def get_text_from(text, li, lf):
	lines = text.split('\n')
	func =lines[li-1:lf]
	s = ''
	for r in func:
		s += r + '\n'
	return s

def __view():
	session_name = sys.argv[-1]
	directory = None
	muta_number = None
	list_number = None
	i = 2
	while i < len(sys.argv[:-2]):
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


	if not list_number:
		print('Mutant number not provided')
		sys.exit()

	try: 
		change_dir_connect(directory, session_name)
	except Exception as ex:
		print(red(f'Can not access test session'))
		print(red(ex))
		sys.exit()	
	
	for muta_number in list_number.split():
		try:
			muta_number = int(muta_number)
			reg_muta = Mutant.get(Mutant.id==muta_number)
			print('Mutant: ', reg_muta.id, reg_muta.operator, reg_muta.status)
		except Exception as ex:
			print(red(f'Can not access mutant number {muta_number}'))
			print(red(ex))
			sys.exit()

		try:
			s1,s2 = get_source_orig_muta(reg_muta)
			print(s1)
			print('------------------------')
			print(s2)
		except Exception as ex:
			print(red(f'Can not read mutant {reg_muta.id}'))
			print(red(ex))
			sys.exit()

	
def get_source_orig_muta(reg_muta, color=True):
	if reg_muta.function != '':
		f = open(reg_muta.source.filename)
		text_source = f.read().replace('\t', '    ')
		func_source = get_text_from(text_source, reg_muta.func_lineno, reg_muta.func_end_lineno)

		s1 = pp_format(func_source, -1, -1, reg_muta.func_lineno,color)
		astt = pickle.loads(reg_muta.ast)
		pv = PrintVisit(astt)
		pv.go_visit()
		func_source = get_text_from(str(pv), reg_muta.func_lineno, reg_muta.func_end_lineno)
		s2 = pp_format(func_source, reg_muta.lineno, reg_muta.end_lineno, reg_muta.func_lineno,color)
		f.close()
	else:
		f = open(reg_muta.source.filename)
		text_source = f.read().replace('\t', '    ')
		func_source = get_text_from(text_source, reg_muta.lineno, reg_muta.end_lineno)

		s1 =  pp_format(func_source, -1, -1, reg_muta.lineno,color)
		astt = pickle.loads(reg_muta.ast)
		pv = PrintVisit(astt)
		pv.go_visit()
		func_source = get_text_from(str(pv), reg_muta.lineno, reg_muta.end_lineno)
		s2 = pp_format(func_source, reg_muta.lineno, reg_muta.end_lineno, reg_muta.lineno,color)
		f.close()
	return (s1, s2)

def pp_format(src, begin, end, base,color):
	lines = src.split('\n')
	s = ''
	begin = begin - base
	end = end - base
	for k in range(len(lines)):
		if k >= begin and k <= end:
			if color:
				s +=  green('{:>4d}{}\t'.format(k+base,'-->') + lines[k] + '\n')
			else:
				s +=  '{:>4d}{}\t'.format(k+base,'-->') + lines[k] + '\n'
			
		else:
			s += '{:>4d} \t'.format(k+base) + lines[k] + '\n'
	return s



def __build():
	session_name = sys.argv[-1]
	directory = None
	muta_number = None
	i = 2
	list_number = None
	while i < len(sys.argv[:-2]):
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

	if not list_number:
		print('Mutant number not provided')
		sys.exit()

	try: 
		change_dir_connect(directory, session_name)
	except Exception as ex:
		print(red(f'Can not access test session'))
		print(red(ex))
		sys.exit()	
	
	for muta_number in list_number.split():
		try:
			muta_number = int(muta_number)
			reg_muta = Mutant.get(Mutant.id==muta_number)
			print('Mutant: ', reg_muta.id)
		except Exception as ex:
			print(red(f'Can not access mutant number {muta_number}'))
			print(red(ex))
			sys.exit()	
		
		muta_filename = '{}_muta{:04d}.py'.format(session_name,muta_number)
		astt = pickle.loads(reg_muta.ast)
		unv = PrintVisit(astt)
		unv.go_visit()
		try:
			f = open(muta_filename, 'w')
		#	tree = ast.parse(str(unv)) # verifica se código é válido.
			f.write(str(unv))
			print(f'File {muta_filename} succesfully created')
		except Exception as ex:
			print(red(f'Cannot create file {muta_filename}')	)
			print(red(ex))
		finally:
			f.close()

def __list():
	session_name = sys.argv[-1]
	directory = None
	i = 2
	while i < len(sys.argv[:-1]):
		s = sys.argv[i]
		match s:
			case '--D':
				i += 1
				directory = sys.argv[i]
			case _:
				usage()
				return
		i += 1

	cont_dead = 0
	cont_live = 0
	cont_equiv = 0	
	try:
		change_dir_connect(directory, session_name)
		for muta in Mutant:
			print('{:04d} \t{}\t{}'.format(muta.id, muta.operator,muta.status))
			if muta.status == 'live':
				cont_live += 1
			elif muta.status == 'dead':
				cont_dead += 1
			else:
				cont_equiv += 1
	except Exception as ex:
		print(red(f'Can not access mutants'))
		print(red(ex))
		sys.exit()	
	print(green(f'Alive: {cont_live}'))
	print(green(f'Dead: {cont_dead}'))
	print(green(f'Equivalent: {cont_equiv}'))
	if cont_live+cont_dead == 0:
		print(green('Mutation score: {:.2f}'.format(0.0)))
	else:
		print(green('Mutation score: {:.3f}'.format(cont_dead/(cont_live+cont_dead))))	

def __gui():
	session_name = sys.argv[-1]
	directory = None
	muta_number = None
	i = 2
	list_number = None
	while i < len(sys.argv[:-2]):
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

	if not list_number:
		list_number = 1

	try: 
		change_dir_connect(directory, session_name)
	except Exception as ex:
		print(red(f'Can not access test session'))
		print(red(ex))
		sys.exit()	

	try:
		muta_number = int(list_number)
		reg_muta = Mutant.get(Mutant.id==muta_number)
	except Exception as ex:
		print(red(f'Can not access mutant number {muta_number}'))
		print(red(ex))
		sys.exit()	
	mutaview_gui(muta_number)

def main():
	n = len(sys.argv)-2
	if n < 1:
		usage()
	
	if sys.argv[1] == '--view':
		__view()
		return
	if sys.argv[1] == '--build':
		__build()
		return		
	if sys.argv[1] == '--list':
		__list()
		return	
	if sys.argv[1] == '--gui':
		__gui()
		return		
	else:
		usage()


def usage():
	print('Usage:')
	print('mutaview --view [--D <directory> ] --x <mutant number>  <session name>')
	print('\tShows original code and mutant code\n')
	print('mutaview --build [--D <directory> ] --x <mutant number>  <session name>')
	print('\tCreates a mutaNNNN.py file with the mutant code\n')
	print('mutaview --gui [--D <directory> ] [--x <mutant number>]  <session name>')
	print('\tShows original code and mutant code in a GUI. Allows to browser through all mutants\n')
	sys.exit()

if __name__ == '__main__' :
	main()
