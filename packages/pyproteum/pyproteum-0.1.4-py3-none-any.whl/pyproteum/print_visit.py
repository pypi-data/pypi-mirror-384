import ast,sys
import difflib

class PrintVisit(ast.NodeVisitor):

	def __init__(self, tree, debug=False):
		self.text = []  # lista de linhas do código final
		self.cur_line = 0
		self.cur_col = 0
		self.debug = debug
		self.closed = False
		self.docstrings = set()
		self.tree = tree
		self.pre_visit(tree)

	def go_visit(self):
		self.visit(self.tree)

	def pre_visit(self, tree):
		for node in ast.walk(tree):
			try:
				if ast.get_docstring(node):
					fn = node.body[0]
					self.docstrings.add(id(fn))
			except: 
				continue
		#print(self.docstrings)

	def show_field(self, field):
		print('Type: ', type(field))
		if isinstance(field,ast.AST):
			print('\t\tunparse: ', ast.unparse(field))
		elif isinstance(field, list):
			if field != []:
				self.show_field(field[0])
				self.show_field(field[1:])
		else:
			print('\t\t', field)

	def show_atributes(self, node):
		if not self.debug:
			return
		if hasattr(node, 'lineno'):
			print('\nNo: {} \tlineno: {} \tcol_offset: {}'.format(type(node),node.lineno, node.col_offset))
		else:
			print('\nNo: {} '.format(type(node)))
		
		print('*******************' , self.cur_col)

		for name,field  in ast.iter_fields(node):
			l = None 
			c = None			
			if hasattr(field, 'lineno'):
				l = field.lineno
				c = field.col_offset
			print('\t{} \tlineno: {} \tcol_offset: {}'.format(name, l, c))
			self.show_field(field)

	def add_text(self, text, line, col):
		if len(text) == 0:
			return
		if not isinstance(text, list):
			text = text.split('\n')
		#col += self.cur_col

		while self.cur_line < line:
			self.text.append('')
			self.cur_line += 1
		else:
			if line < 0:
				self.text.append('')
				self.cur_line += 1

		buffer = self.text[-1]
		buffer += (col-len(buffer)) * ' ' + text[0]

		self.text[-1] = buffer
		self.add_text(text[1:], line+1, 0)

	def gen_visit(self, nodes, col):
		if isinstance(nodes, list):
			for node in nodes:
				self.visit(node)
		elif nodes:
			self.visit(nodes)

	def check_line(self, node):
		if self.closed and node.lineno == self.cur_line:
			self.text[-1] += '; '
		
	def close(self):
		self.closed = True

	def open(self):
		self.closed = False

	

########## No: <class 'ast.FunctionDef'> 	lineno: 11 	col_offset: 0
# 	name 	lineno: None 	col_offset: None
# Type:  <class 'str'>
# 		 exemplo_funcao
# 	args 	lineno: None 	col_offset: None
# Type:  <class 'ast.arguments'>
# 		unparse:  a: int, b: str
# 	body 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# Type:  <class 'ast.Return'>
# 		unparse:  return a + b
# Type:  <class 'list'>
# 	decorator_list 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# Type:  <class 'ast.Name'>
# 		unparse:  aaaaa
# Type:  <class 'list'>
# Type:  <class 'ast.Name'>
# 		unparse:  bbbbb
# Type:  <class 'list'>
# 	returns 	lineno: 11 	col_offset: 37
# Type:  <class 'ast.Name'>
# 		unparse:  int
# 	type_comment 	lineno: None 	col_offset: None
# Type:  <class 'NoneType'>
# 		 None
# 	type_params 	lineno: None 	col_offset: None
# Type:  <class 'list'>

	def visit_FunctionDef(self, node):
		self.show_atributes(node)
		self.check_line(node) 
		# decorator list comes before function decl
		for name in node.decorator_list:
			self.add_text(f'@{ast.unparse(name)} ', name.lineno, node.col_offset)

		#function name and arguments and returns
		ret = f' -> {ast.unparse(node.returns)}' if node.returns else ''
		self.add_text(f'def {node.name} ({ast.unparse(node.args)}) {ret}:', node.lineno, node.col_offset)
		self.open()
		self.gen_visit(node.body, node.col_offset)

	def visit_AsyncFunctionDef(self, node):
		self.show_atributes(node)
		self.check_line(node)
		# decorator list comes before function decl
		for name in node.decorator_list:
			self.add_text(f'@{ast.unparse(name)} ', name.lineno, node.col_offset)

		#function name and arguments and returns
		ret = f' -> {ast.unparse(node.returns)}' if node.returns else ''
		self.add_text(f'async def {node.name} ({ast.unparse(node.args)}) {ret}:', node.lineno, node.col_offset)		
		self.open()
		
		self.gen_visit(node.body, node.col_offset)



# No: <class 'ast.ClassDef'> 	lineno: 19 	col_offset: 0
# 	name 	lineno: None 	col_offset: None
# Type:  <class 'str'>
# 		 ExemploClasse
# 	bases 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# Type:  <class 'ast.Attribute'>
# 		unparse:  ast.AST
# Type:  <class 'list'>
# 	keywords 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# Type:  <class 'ast.keyword'>
# 		unparse:  metaclass=Meta
# Type:  <class 'list'>
# Type:  <class 'ast.keyword'>
# 		unparse:  abstract=True
# Type:  <class 'list'>
# 	body 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# Type:  <class 'ast.FunctionDef'>
# 		unparse:  def metodo(self):
#	 pass
# Type:  <class 'list'>
# 	decorator_list 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# 	type_params 	lineno: None 	col_offset: None
# Type:  <class 'list'>

	def visit_ClassDef(self, node):
		self.show_atributes(node)

		self.check_line(node)
		# decorator list comes before function decl
		for name in node.decorator_list:
			self.add_text(f'@{ast.unparse(name)}', name.lineno, node.col_offset)

		line = f'class {node.name} '
		if node.bases or node.keywords:
			line += '('
			sep = ''
			for base in node.bases:
				line += sep + ast.unparse(base)
				sep = ','
			for keyword in node.keywords:
				line += sep + ast.unparse(keyword)
				sep = ','
			line += ')'
		line += ':'
		self.add_text(line, node.lineno, node.col_offset)
		self.open()
		self.gen_visit(node.body, node.col_offset)


####### No: <class 'ast.If'> 	lineno: 65 	col_offset: 0
# 	test 	lineno: 65 	col_offset: 3
# Type:  <class 'ast.Compare'>
# 		unparse:  x > 5
# 	body 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# Type:  <class 'ast.Expr'>
# 		unparse:  print('maior que 5')
# Type:  <class 'list'>
# 	orelse 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# Type:  <class 'ast.If'>
# 		unparse:  if x == 5:
#	 print('igual a 5')
# else:
#	 print('menor ou igual a 5')
# Type:  <class 'list'>

	def visit_If(self, node, elif_flag=False):
		self.check_line(node)
		line = 'elif ' if elif_flag else 'if '
		line += ast.unparse(node.test) + ':'
		self.add_text(line, node.lineno, node.col_offset)

		self.show_atributes(node)
		self.open()
		self.gen_visit(node.body, node.col_offset)

		if node.orelse:
			self.open()
			if len(node.orelse) == 1:
				next_if = node.orelse[0]
				# se o comando do else é um só e é um if, então trata-se de um elif
				if isinstance(next_if, ast.If) and next_if.col_offset == node.col_offset:
					self.cur_col = node.col_offset
					self.visit_If(next_if,True)
				else:
					self.add_text('else:', -1, node.col_offset)
					self.visit(next_if)
			else:
				self.add_text('else:', -1, node.col_offset)
				self.gen_visit(node.orelse, node.col_offset)




################# No: <class 'ast.For'> 	lineno: 81 	col_offset: 0
# 	target 	lineno: 81 	col_offset: 4
# Type:  <class 'ast.Tuple'>
# 		unparse:  (i, j, k)
# 	iter 	lineno: 81 	col_offset: 13
# Type:  <class 'ast.Call'>
# 		unparse:  range(2)
# 	body 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# Type:  <class 'ast.Expr'>
# 		unparse:  print('for', i)
# Type:  <class 'list'>
# 	orelse 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# Type:  <class 'ast.Expr'>
# 		unparse:  print('fim do for')
# Type:  <class 'list'>
# 	type_comment 	lineno: None 	col_offset: None
# Type:  <class 'NoneType'>

	def visit_For(self, node):
		self.check_line(node)
		self.show_atributes(node)

		line = f'for {ast.unparse(node.target)} in {ast.unparse(node.iter)}:'
		self.add_text(line, node.lineno, node.col_offset)
		self.open()

		self.gen_visit(node.body, node.col_offset)
		if node.orelse:
			self.add_text('else:', -1, node.col_offset)
			self.open()
			self.gen_visit(node.orelse, node.col_offset)


	def visit_AsyncFor(self, node):
		self.check_line(node)
		self.show_atributes(node)

		line = f'async for {ast.unparse(node.target)} in {ast.unparse(node.iter)}:'
		self.add_text(line, node.lineno, node.col_offset)
		self.open()
		self.gen_visit(node.body, node.col_offset)
		if node.orelse:
			self.add_text('else:', -1, node.col_offset)
			self.open()
			self.gen_visit(node.orelse, node.col_offset)


################### No: <class 'ast.While'> 	lineno: 76 	col_offset: 0
# ******************* 0
# 	test 	lineno: 76 	col_offset: 6
# Type:  <class 'ast.Compare'>
# 		unparse:  i < 3
# 	body 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# Type:  <class 'ast.Expr'>
# 		unparse:  print(i)
# Type:  <class 'list'>
# Type:  <class 'ast.AugAssign'>
# 		unparse:  i += 1
# Type:  <class 'list'>
# 	orelse 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# Type:  <class 'ast.Expr'>
# 		unparse:  print('fim do while')
# Type:  <class 'list'>

	def visit_While(self, node):
		self.check_line(node)
		self.show_atributes(node)

		line = f'while {ast.unparse(node.test)} :'
		self.add_text(line, node.lineno, node.col_offset)
		self.open()
		self.gen_visit(node.body, node.col_offset)
		if node.orelse:
			self.open()
			self.add_text('else:', -1, node.col_offset)
			self.gen_visit(node.orelse, node.col_offset)


# ############No: <class 'ast.With'> 	lineno: 109 	col_offset: 0
# ******************* 0
# 	items 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# Type:  <class 'ast.withitem'>
# 		unparse:  open('exemplo.txt', 'w') as f
# Type:  <class 'list'>
# 	body 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# Type:  <class 'ast.Expr'>
# 		unparse:  f.write('teste')
# Type:  <class 'list'>
# 	type_comment 	lineno: None 	col_offset: None
# Type:  <class 'NoneType'>
# 		 None

	def visit_With(self, node):
		self.show_atributes(node)
		self.check_line(node)
		with_item = ''
		sep = ''
		for item in node.items:
			with_item += f'{sep}{ast.unparse(item)}'
			sep = ','  
		self.add_text(f'with {with_item}:', node.lineno, node.col_offset)
		self.open()
		self.gen_visit(node.body, node.col_offset)


	def visit_AsyncWith(self, node):
		self.show_atributes(node)
		self.check_line(node)
		with_item = ''
		sep = ''
		for item in node.items:
			with_item += f'{sep}{ast.unparse(item)}'
			sep = ','  
		self.add_text(f'async with {with_item}:', node.lineno, node.col_offset)
		self.open()
		self.gen_visit(node.body, node.col_offset)

		

################### No: <class 'ast.Try'> 	lineno: 44 	col_offset: 0
# ******************* 0
# 	body 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# Type:  <class 'ast.Raise'>
# 		unparse:  raise ValueError('Erro')
# Type:  <class 'list'>
# 	handlers 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# Type:  <class 'ast.ExceptHandler'>
# 		unparse:  except ValueError as ex:
#	 pass
# Type:  <class 'list'>
# 	orelse 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# 	finalbody 	lineno: None 	col_offset: None
# Type:  <class 'list'>

	def visit_Try(self, node):
		self.show_atributes(node)
		self.check_line(node)
		self.add_text('try:', node.lineno, node.col_offset)
		self.open()
		self.gen_visit(node.body, node.col_offset)
		if node.handlers:
			self.gen_visit(node.handlers, node.col_offset)
		if node.orelse:
			self.add_text('else:', -1, node.col_offset)
			self.open()
			self.gen_visit(node.orelse, node.col_offset)
		if node.finalbody:
			self.add_text('finally:', -1, node.col_offset)
			self.open()
			self.gen_visit(node.finalbody, node.col_offset)

################# No: <class 'ast.ExceptHandler'> 	lineno: 99 	col_offset: 0
# ******************* 0
# 	type 	lineno: 99 	col_offset: 7
# Type:  <class 'ast.Name'>
# 		unparse:  ZeroDivisionError
# 	name 	lineno: None 	col_offset: None
# Type:  <class 'NoneType'>
# 		 None
# 	body 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# Type:  <class 'ast.Assign'>
# 		unparse:  x = 0
# Type:  <class 'list'>

	def visit_ExceptHandler(self,  node):
		self.show_atributes(node)
		self.check_line(node)
		name = f'as {node.name}' if node.name else '' 
		tipo = ast.unparse(node.type) if node.type else ''
		self.add_text(f'except {tipo} {name}:', node.lineno, node.col_offset)
		self.open()
		self.gen_visit(node.body, node.col_offset)		

######### No: <class 'ast.Assign'> 	lineno: 28 	col_offset: 0
# ******************* 0
# 	targets 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# Type:  <class 'ast.Name'>
# 		unparse:  a
# Type:  <class 'list'>
# 	value 	lineno: 28 	col_offset: 4
# Type:  <class 'ast.List'>
# 		unparse:  [1, 2, 3]
# 	type_comment 	lineno: None 	col_offset: None
# Type:  <class 'NoneType'>
# 		 None

	def visit_Assign(self, node):
		self.check_line(node)
		self.show_atributes(node)
		self.add_text(f'{ast.unparse(node)}', node.lineno, node.col_offset)
		self.close()

############### No: <class 'ast.AugAssign'> 	lineno: 35 	col_offset: 0
# ******************* 0
# 	target 	lineno: 35 	col_offset: 0
# Type:  <class 'ast.Name'>
# 		unparse:  x
# 	op 	lineno: None 	col_offset: None
# Type:  <class 'ast.Add'>
# 		unparse:  
# 	value 	lineno: 35 	col_offset: 5
# Type:  <class 'ast.Constant'>
# 		unparse:  5

	def visit_AugAssign(self, node):
		self.show_atributes(node)
		self.check_line(node)
		self.add_text(f'{ast.unparse(node)}', node.lineno, node.col_offset)
		self.close()
		
	def visit_AnnAssign(self, node):
		self.show_atributes(node)
		self.check_line(node)
		self.add_text(f'{ast.unparse(node)}', node.lineno, node.col_offset)
		self.close()

##### No: <class 'ast.Expr'> 	lineno: 16 	col_offset: 4
# ******************* 0
# 	value 	lineno: 16 	col_offset: 4
# Type:  <class 'ast.Await'>
# 		unparse:  await exemplo_corrotina()

	def visit_Expr(self, node):
		self.show_atributes(node)
		if id(node) in self.docstrings:
			self.visit_docstring(node)
		else:
			self.check_line(node)
			self.add_text(f'{ast.unparse(node)}', node.lineno, node.col_offset)
		self.close()

	def visit_docstring(self, node):
		#print('Docstring: ', node.value.value, len(node.value.value))
		self.add_text(f"'''{node.value.value}'''", node.lineno, node.col_offset)

	def visit_Return(self, node):
		self.show_atributes(node)
		self.check_line(node)
		self.add_text(f'{ast.unparse(node)}', node.lineno, node.col_offset)
		self.close()

	def visit_Raise(self, node):
		self.show_atributes(node)
		self.check_line(node)
		self.add_text(f'{ast.unparse(node)}', node.lineno, node.col_offset)
		self.close()

	def visit_Assert(self, node):
		self.show_atributes(node)
		self.check_line(node)
		self.add_text(f'{ast.unparse(node)}', node.lineno, node.col_offset)
		self.close()

	def visit_Delete(self, node):
		self.show_atributes(node)
		self.check_line(node)
		self.add_text(f'{ast.unparse(node)}', node.lineno, node.col_offset)
		self.close()


	def visit_Global(self, node):
		self.show_atributes(node)
		self.check_line(node)
		self.add_text(f'{ast.unparse(node)}', node.lineno, node.col_offset)
		self.close()

	def visit_Nonlocal(self, node):
		self.show_atributes(node)
		self.check_line(node)
		self.add_text(f'{ast.unparse(node)}', node.lineno, node.col_offset)
		self.close()

	def visit_Break(self, node):
		self.show_atributes(node)
		self.check_line(node)
		self.add_text(f'{ast.unparse(node)}', node.lineno, node.col_offset)
		self.close()

	def visit_Continue(self, node):
		self.show_atributes(node)
		self.check_line(node)
		self.add_text(f'{ast.unparse(node)}', node.lineno, node.col_offset)
		self.close()

	def visit_Pass(self, node):
		self.show_atributes(node)
		self.check_line(node)
		self.add_text(f'{ast.unparse(node)}', node.lineno, node.col_offset)
		self.close()


################# No: <class 'ast.Match'> 	lineno: 97 	col_offset: 0
# ******************* 0
# 	subject 	lineno: 97 	col_offset: 6
# Type:  <class 'ast.Name'>
# 		unparse:  x
# 	cases 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# Type:  <class 'ast.match_case'>
# 		unparse:  case 1 if j > 10:
#     pass
# Type:  <class 'list'>
# Type:  <class 'ast.match_case'>
# 		unparse:  case _:
#     pass
# Type:  <class 'list'>

################# No: <class 'ast.match_case'> 
# ******************* 0
# 	pattern 	lineno: 98 	col_offset: 6
# Type:  <class 'ast.MatchValue'>
# 		unparse:  1
# 	guard 	lineno: 98 	col_offset: 11
# Type:  <class 'ast.Compare'>
# 		unparse:  j > 10
# 	body 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# Type:  <class 'ast.Pass'>
# 		unparse:  pass
# Type:  <class 'list'>

	def visit_Match(self, node):
		self.show_atributes(node)
		self.add_text(f'match {ast.unparse(node.subject)}:', node.lineno, node.col_offset)
		for cs in node.cases: 
			gd = ''
			if cs.guard:
				gd = f'if {ast.unparse(cs.guard)}'
			self.add_text(f'\ncase {ast.unparse(cs.pattern)} {gd}:',-1 ,node.col_offset+4)
			self.open()
			self.gen_visit(cs.body, node.col_offset+4)
		

	def visit_match_case(self, node):
		self.show_atributes(node)
		self.generic_visit(node)	

############### No: <class 'ast.Import'> 	lineno: 111 	col_offset: 0
# ******************* 0
# 	names 	lineno: None 	col_offset: None
# Type:  <class 'list'>
# Type:  <class 'ast.alias'>
# 		unparse:  asyncio
# Type:  <class 'list'>

	def visit_Import(self, node):
		self.check_line(node)
		self.show_atributes(node)
		self.add_text(f'{ast.unparse(node)}', node.lineno, node.col_offset)
		self.close()

	def visit_ImportFrom(self, node):
		self.check_line(node)
		self.show_atributes(node)
		self.add_text(f'{ast.unparse(node)}', node.lineno, node.col_offset)
		self.close()

	def __str__(self):
		s = ''
		for r in self.text:
			s += r+'\n'
		return s


def compare_ast(node1, node2, path="root"):
	if isinstance(node1, ast.AST):
		print(path, ast.unparse(node1), ast.unparse(node2))
	if type(node1) != type(node2):
		print(f"Tipo diferente em {path}: {type(node1).__name__} vs {type(node2).__name__}")
		print(node1, node2)		
		return

	if isinstance(node1, ast.AST):
		for field in node1._fields:
			val1 = getattr(node1, field, None)
			val2 = getattr(node2, field, None)
			compare_ast(val1, val2, path + f".{field}")
	elif isinstance(node1, list):
		if len(node1) != len(node2):
			print(f"Listas de tamanhos diferentes em {path}: {len(node1)} vs {len(node2)}")
			print(node1)
			print(node2)
			
		for i, (item1, item2) in enumerate(zip(node1, node2)):
			compare_ast(item1, item2, path + f"[{i}]")
	else:
		if node1 != node2:
			print(f"Diferença em {path}: {node1!r} vs {node2!r}")
			if node1.lineno:
				print(node1.lineno)

if __name__ == "__main__":
	source = open(sys.argv[1]).read()
	tree = ast.parse(source)
	#print(ast.dump(tree))
	pv = PrintVisit(tree, debug=True)
	pv.go_visit()
	print(pv)

	tree2 = ast.parse(str(pv))

	d1 = ast.dump(tree)
	d2 = ast.dump(tree2)

	if d1 == d2:
		print('iguais')
	else:
		compare_ast(tree, tree2)
		with open('../erro.py', 'w') as f:
			f.write(str(pv))