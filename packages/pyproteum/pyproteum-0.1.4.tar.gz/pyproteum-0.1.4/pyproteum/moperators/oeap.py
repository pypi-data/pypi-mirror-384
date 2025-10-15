import ast
from pyproteum.moperators.myoperator import *
import copy


class Oeap(MyOperator):
	
	def __init__(self, original,filename):
		super().__init__(original, filename)
		self.seq = 1
		ParentSetter().visit(self.original)


	def clone_node(self, new, old):
		new.targets = [old.target]
		new.value = old.value
		ast.copy_location(new,old)

	def visit_AugAssign(self, node):
		p, fld, idx = node.parent, node.parent_field, node.parent_index

		new_node = ast.Assign()
		self.clone_node(new_node, node)
		if idx is not None:
			lst = getattr(p, fld)
			lst[idx] = new_node
		else:
			setattr(p,fld, new_node)
		self.salva_muta(new_node, self.function, self.func_lineno, self.func_end_lineno,seq=self.seq)
		self.seq += 1

		if idx is not None: 
			lst = getattr(p, fld)
			lst[idx] = node
		else:
			setattr(p,fld, node)		

		self.generic_visit(node)
		return node


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

class Oepa(MyOperator):
	
	def __init__(self, original,filename):
		super().__init__(original, filename)
		self.seq = 1
		self.scalar_set = set()
		ParentSetter().visit(self.original)


	def clone_node(self, new, old, op):
		new.target = old.targets[0]
		new.value = old.value
		new.op = op
		ast.copy_location(new,old)

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

	def visit_Assign(self, node):
		p, fld, idx = node.parent, node.parent_field, node.parent_index

		# não é possível mudar a = b = 10
		if len(node.targets) == 1  and isinstance(node.targets[0], (ast.Attribute,ast.Name) ):
			# só faz a mutação se a variável já foi definida
			for op in use:
				new_node = ast.AugAssign()
				self.clone_node(new_node, node, op)
				if idx is not None:
					lst = getattr(p, fld)
					lst[idx] = new_node
				else:
					setattr(p,fld, new_node)
				self.salva_muta(new_node, self.function, self.func_lineno, self.func_end_lineno,seq=self.seq)
				self.seq += 1

			if idx is not None: 
				lst = getattr(p, fld)
				lst[idx] = node
			else:
				setattr(p,fld, node)		

		self.generic_visit(node)
		return node
