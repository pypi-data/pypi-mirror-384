import ast
from pyproteum.moperators.myoperator import *


class Cccr(MyOperator):
	
	def __init__(self, original,filename):
		super().__init__(original, filename)
		self.seq = 1
		self.const_set = list()

	def visit_FunctionDef(self, node):
		old_set = list(self.const_set)
		super().visit_FunctionDef(node)
		self.const_set = old_set
		return node

	def visit_Constant(self, node):
		if not id(node) in self.docstrings:
			old_value = node.value
			if not old_value in self.const_set:
				self.const_set.append(old_value)

			for new_value in self.const_set:
				if new_value == old_value:
					continue
				if type(new_value) != type(old_value):
					continue
				node.value = new_value
				self.salva_muta(node, self.function, self.func_lineno, self.func_end_lineno,seq=self.seq)
				self.seq += 1
				
			node.value = old_value
		self.generic_visit(node)
		return node
		
