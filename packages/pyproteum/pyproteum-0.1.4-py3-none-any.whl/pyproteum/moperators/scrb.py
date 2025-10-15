import ast
from pyproteum.moperators.myoperator import *



class Scrb(MyOperator):
	


	def generic_visit(self, node):
		for _, value in ast.iter_fields(node):
			if isinstance(value, list):
				for k, item in enumerate(value):
					if isinstance(item,ast.Continue):
						new_node = ast.Break()
						ast.copy_location(new_node, item)
						value[k] = new_node
						self.salva_muta(new_node, self.function, self.func_lineno, self.func_end_lineno)
						value[k] = item

					self.visit(item)

			elif isinstance(value, ast.AST):
				self.visit(value)
		return node