
import ast
from pyproteum.moperators.myoperator import *


class Crcr(MyOperator):
	
	def __init__(self, original,filename):
		super().__init__(original, filename)
		self.seq = 1
	
	def visit_Constant(self, node):
		old_value = node.value

		if not id(node) in self.docstrings:

			for new_value in self.get_required(node.value):
				if new_value == old_value:
					continue
				node.value = new_value
				self.salva_muta(node, self.function, self.func_lineno, self.func_end_lineno,seq=self.seq)
				self.seq += 1
			node.value = old_value
		return self.generic_visit(node)

	def get_required(self, value):
		if isinstance(value, int):
			return [-1, 0, 1]
		if isinstance(value, float):
			return [-1.0, 0.0, 1.0, 1E-13, 1E+13]
		if isinstance(value, str):
			return ['',' ']		
		if isinstance(value, bytes):
			return [b'',b' ']		
		return []
