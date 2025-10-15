import ast
from pyproteum.moperators.myoperator import *
from pyproteum.moperators.oaan import use

f = lambda x: str(x)


use = [ast.Add(),
ast.Sub(),
ast.Mult(),
ast.Div(),
ast.FloorDiv(),
ast.Mod(),
ast.Pow(),
ast.LShift(),
ast.RShift(),
ast.BitOr(),
ast.BitXor(),
ast.BitAnd(),
]

class Oaaa(MyOperator):
	
	def __init__(self, original,filename):
		super().__init__(original, filename)
		self.use = sorted(use, key=f)
		self.seq = 1
	
	def visit_AugAssign(self, node):
		for i,op in enumerate(use):
			if type(op) == type(node.op):
				continue

			old_op = node.op
			node.op = op
			

			self.salva_muta(node, self.function, self.func_lineno, self.func_end_lineno,seq=self.seq)
			node.op = old_op
			self.seq += 1
		
		return self.generic_visit(node)
