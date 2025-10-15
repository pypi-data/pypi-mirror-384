import ast
from pyproteum.moperators.myoperator import *
import copy


class Ccsr(MyOperator):
	
	def __init__(self, original,filename):
		super().__init__(original, filename)
		self.seq = 1
		self.scalar_set = set()
		ParentSetter().visit(self.original)



	def visit_FunctionDef(self, node):
		old_set = set(self.scalar_set)
		super().visit_FunctionDef(node)
		self.scalar_set = old_set
		return node

	def visit_Name(self, node):
		if isinstance(node.ctx, ast.Store) :
			self.scalar_set.add(node.id)
		self.generic_visit(node)
		return node

	def visit_arg(self, node):
		if node.arg != 'self':
			self.scalar_set.add(node.arg)
		self.generic_visit(node)
		return node

	def visit_Constant(self, node):
		p, fld, idx = node.parent, node.parent_field, node.parent_index

		if not id(node) in self.docstrings:
			for nv in sorted(list(self.scalar_set)):
				new_value = ast.Name(id=nv, ctx=ast.Load())
				ast.copy_location(new_value, node)
				if idx is not None:
					lst = getattr(p, fld)
					lst[idx] = new_value
				else:
					setattr(p,fld, new_value)
				self.salva_muta(new_value, self.function, self.func_lineno, self.func_end_lineno,seq=self.seq)
				self.seq += 1

			if idx is not None: 
				lst = getattr(p, fld)
				lst[idx] = node
			else:
				setattr(p,fld, node)		

		self.generic_visit(node)
		return node
		
