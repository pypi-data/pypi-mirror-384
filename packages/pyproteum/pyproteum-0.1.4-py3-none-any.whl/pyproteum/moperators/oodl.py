import ast
from pyproteum.moperators.myoperator import *
import copy


class Oodl(MyOperator):
	
	def __init__(self, original,filename):
		super().__init__(original, filename)
		self.seq = 1
		self.scalar_set = set()
		ParentSetter().visit(self.original)


	def visit_BinOp(self, node):
		p, fld, idx = node.parent, node.parent_field, node.parent_index

		for new_value in [node.left, node.right]:
			if idx is not None:
				lst = getattr(p, fld)
				lst[idx] = new_value
			else:
				setattr(p,fld, new_value)
			self.salva_muta(p, self.function, self.func_lineno, self.func_end_lineno,seq=self.seq)
			self.seq += 1

		if idx is not None: 
			lst = getattr(p, fld)
			lst[idx] = node
		else:
			setattr(p,fld, node)		

		self.generic_visit(node)
		return node

	def visit_UnaryOp(self, node):
		p, fld, idx = node.parent, node.parent_field, node.parent_index

		for new_value in [node.operand]:
			if idx is not None:
				lst = getattr(p, fld)
				lst[idx] = new_value
			else:
				setattr(p,fld, new_value)
			self.salva_muta(p, self.function, self.func_lineno, self.func_end_lineno,seq=self.seq)
			self.seq += 1

		if idx is not None: 
			lst = getattr(p, fld)
			lst[idx] = node
		else:
			setattr(p,fld, node)		

		self.generic_visit(node)
		return node

	def visit_BoolOp(self, node):
		p, fld, idx = node.parent, node.parent_field, node.parent_index

 #  nesse primeiro caso, o nó tem apenas 2 operandos. então retira o nó da árvore
		if len(node.values) == 2:			
			for new_value in node.values:
				if idx is not None:
					lst = getattr(p, fld)
					lst[idx] = new_value
				else:
					setattr(p,fld, new_value)
				self.salva_muta(p, self.function, self.func_lineno, self.func_end_lineno,seq=self.seq)
				self.seq += 1

			if idx is not None: 
				lst = getattr(p, fld)
				lst[idx] = node
			else:
				setattr(p,fld, node)		
		else: # nesse segundo caso, tira apenas um operando da árvore removendo da lista de operandos
			tam = len(node.values)
			for i in range(tam):
				old_node = node.values.pop(i)
				self.salva_muta(node, self.function, self.func_lineno, self.func_end_lineno,seq=self.seq)
				node.values.insert(i, old_node)
				self.seq += 1

		self.generic_visit(node)
		return node