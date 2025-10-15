import ast
from pyproteum.moperators.myoperator import *



class Ssdl(MyOperator):
	

	def __init__(self, original,filename):
		super().__init__(original, filename)
		self.seq = 1

	def generic_visit(self, node):		
		for campo, value in ast.iter_fields(node):
			if isinstance(value, list):
				for k, item in enumerate(value):
					if id(item) in self.docstrings:
						self.visit(item)								
					elif isinstance(item, ast.If): #trata o caso especial do elif
						pass_node = ast.Pass()
						if campo == 'orelse' and len(value) == 1 and item.col_offset == node.col_offset:
							firstc = item.body[0]
							ast.copy_location(pass_node, firstc)
						else:
							ast.copy_location(pass_node, item)
						value[k] = pass_node
						# self.show_node(pass_node)
						# self.show_node(item)
						self.salva_muta(pass_node, self.function, self.func_lineno, self.func_end_lineno, self.seq)
						value[k] = item				
					elif self._is_command(item):
						pass_node = ast.Pass()
						ast.copy_location(pass_node, item)
						value[k] = pass_node
						# self.show_node(pass_node)
						# self.show_node(item)
						self.salva_muta(pass_node, self.function, self.func_lineno, self.func_end_lineno, self.seq)
						value[k] = item
					self.seq += 1
					self.visit(item)


			elif isinstance(value, ast.AST):
				self.visit(value)
		return node

	def _is_command(self, node):
		return isinstance(node, (
			ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.Try,
			ast.Assign, ast.AugAssign, ast.Expr, ast.AsyncWith,
			ast.Return, ast.Raise, ast.Assert, ast.Delete, ast.Nonlocal,
			ast.Break, ast.Continue, ast.Match, ast.AnnAssign, ast.Global
		))