import ast
from pyproteum.moperators.myoperator import *

f = lambda x: str(x)

no_use = [ast.In(), ast.NotIn(), ast.Is(), ast.IsNot()]

use = [ast.Eq(), ast.NotEq(), ast.Lt(), ast.LtE(), ast.Gt(), ast.GtE()]

class Orrn(MyOperator):
	
	def __init__(self, original,filename):
		super().__init__(original, filename)
		self.use = sorted(use, key=f)
		self.seq = 1
	
	def visit_Compare(self, node):
		for i,op in enumerate(node.ops):
			if self.check_in(op,no_use):
				#print('continue')
				continue

			self.ckeck_remove(op,self.use)
			
			for new_op in self.use:
				node.ops[i] = new_op
				#desloc = self.compute_len(op, new_op)
				self.salva_muta(node, self.function, self.func_lineno, self.func_end_lineno,seq=self.seq)
				self.seq += 1
			self.use = sorted(use, key=f)
			node.ops[i] = op
		
		return self.generic_visit(node)

	def check_in(self, op, use):
		op_class = type(op)
		it = list(filter(lambda x: isinstance(x,op_class), use))
		return len(it) > 0
		
	def ckeck_remove(self, op, use):
		for use_op in use:
			if type(op) is type(use_op):
				use.remove(use_op)
				return use_op
		return None

	def compute_len(self, op, new_op):
		r = 0
		if self.check_in(op, [ast.Eq(), ast.NotEq(), ast.LtE(), ast.GtE()]):
			if self.check_in(new_op, [ast.Lt(), ast.Gt()]):
				r = -1
		else:
			if self.check_in(new_op, [ast.Eq(), ast.NotEq(), ast.LtE(), ast.GtE()]):
				r = 1
		return r