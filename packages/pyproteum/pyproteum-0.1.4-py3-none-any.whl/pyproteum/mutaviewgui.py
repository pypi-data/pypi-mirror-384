

import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from pyproteum.models.models import Mutant
from pyproteum.print_visit import PrintVisit
import ast
import pickle
from peewee import fn
from pyproteum.moperators.oplist import operator_list,get_descr
import sys, random

# ---------------------- Util ----------------------
def log(msg):
	#print(msg, flush=True)
	pass

def clamp_int(text, default=1):
	try:
		return max(0, int(text))
	except:
		return default

# ---------------------- App ----------------------
class ViewMutantsApp(ttk.Frame):
	def __init__(self, master):
		super().__init__(master, padding=6)
		self.master = master
		self.grid(sticky="nsew")
		self._make_vars()
		self._make_ui()
		self._layout()
		self._bind_events()

	def _make_vars(self):
		self.var_mutant = tk.StringVar(value="1")
		self.var_op_equiv = tk.IntVar(value=0)
		self.var_show_alive = tk.IntVar(value=1)
		self.var_show_dead = tk.IntVar(value=1)
		self.var_show_equiv = tk.IntVar(value=1)
		self.var_status = tk.StringVar()
		self.var_operator = tk.StringVar()
		self.mono = tkfont.Font(family="Courier New", size=10)
		
	def init_fields(self, muta):
		from pyproteum.mutaview import get_source_orig_muta

		try:
			reg_muta = Mutant.get(Mutant.id==muta)
		except:
			return -1
		self.last = muta
		self.var_mutant.set(str(muta))
		self.var_status.set(reg_muta.status)
		self.var_operator.set(f'{reg_muta.operator}: {get_descr(reg_muta.operator)}')
		self.var_op_equiv.set(int(reg_muta.status=='equiv'))
		if reg_muta.status == 'dead':
			self.chk_op_equiv.config(state='disabled')
		else:
			self.chk_op_equiv.config(state='normal')
		self.txt_right.configure(state="normal")
		self.txt_right.delete("1.0", tk.END)
		sample_mutant2, sample_mutant1 = get_source_orig_muta(reg_muta, color=False)
		self.txt_right.insert("1.0", sample_mutant1)
		self.txt_right.configure(state="disabled")

		self.txt_left.configure(state="normal")
		self.txt_left.delete("1.0", tk.END)
		self.txt_left.insert("1.0", sample_mutant2)
		self.txt_left.configure(state="disabled")
		return muta

	def _make_ui(self):
		# Linha 1
		self.lbl_mutant = ttk.Label(self, text="Mutant:")
		self.ent_mutant = ttk.Entry(self, textvariable=self.var_mutant, width=8)
		self.btn_up = ttk.Button(self, text="up", command=self.on_up)
		self.btn_dw = ttk.Button(self, text="down", command=self.on_dw)
		self.chk_op_equiv = ttk.Checkbutton(self, text="Equivalent", variable=self.var_op_equiv, command=self.on_op_equiv)

		self.lbl_type = ttk.Label(self, text="Type to Show:")
		self.frm_types = ttk.Frame(self)

		self.chk_alive = ttk.Checkbutton(self.frm_types, text="Alive", variable=self.var_show_alive, command=self.on_show_alive)
		self.chk_equiv = ttk.Checkbutton(self.frm_types, text="Equivalent", variable=self.var_show_equiv, command=self.on_show_equiv)
		self.chk_dead  = ttk.Checkbutton(self.frm_types, text="Dead", variable=self.var_show_dead, command=self.on_show_dead)
		# Linha 2 (desabilitados)
		self.lbl_status = ttk.Label(self, text="Status:")
		self.ent_status = ttk.Entry(self, textvariable=self.var_status, width=20, state="disabled")
		self.lbl_operator = ttk.Label(self, text="Operator:")
		self.ent_operator = ttk.Entry(self, textvariable=self.var_operator, width=100, state="disabled")

		# Títulos das áreas
		self.lbl_orig_title = ttk.Label(self, text="Original Program", font=("Arial", 11, "bold"))
		self.lbl_mut_title = ttk.Label(self, text="Mutant Program", font=("Arial", 11, "bold"))

		# Textos com rolagem (lado a lado)
		self.frm_left = ttk.Frame(self)
		self.txt_left = tk.Text(self.frm_left, width=70, height=24, font=self.mono, wrap="none")
		self.scrl_left_y = ttk.Scrollbar(self.frm_left, orient="vertical", command=self.txt_left.yview)
		self.scrl_left_x = ttk.Scrollbar(self.frm_left, orient="horizontal", command=self.txt_left.xview)
		self.txt_left.configure(yscrollcommand=self.scrl_left_y.set, xscrollcommand=self.scrl_left_x.set)
		sample_original = ""
		self.txt_left.insert("1.0", sample_original)
		self.txt_left.configure(state="disabled")

		self.frm_right = ttk.Frame(self)
		self.txt_right = tk.Text(self.frm_right, width=70, height=24, font=self.mono, wrap="none")
		self.scrl_right_y = ttk.Scrollbar(self.frm_right, orient="vertical", command=self.txt_right.yview)
		self.scrl_right_x = ttk.Scrollbar(self.frm_right, orient="horizontal", command=self.txt_right.xview)
		self.txt_right.configure(yscrollcommand=self.scrl_right_y.set, xscrollcommand=self.scrl_right_x.set)
		sample_mutant = ""
		self.txt_right.insert("1.0", sample_mutant)
		self.txt_right.configure(state="disabled")

		# Rodapé
		self.btn_ok = ttk.Button(self, text="OK", command=self.master.destroy)

	def _layout(self):
		self.columnconfigure(0, weight=0)
		self.columnconfigure(1, weight=0)
		self.columnconfigure(2, weight=0)
		self.columnconfigure(3, weight=0)
		self.columnconfigure(4, weight=0)
		self.columnconfigure(5, weight=0)

		# Linha 1
		self.lbl_mutant.grid(row=0, column=0, padx=(4,2), pady=(4,2), sticky="w")
		self.ent_mutant.grid(row=0, column=1, padx=(0,6), pady=(4,2), sticky="w")
		self.btn_up.grid(row=0, column=2, padx=(0,2), pady=(4,2), sticky="w")
		self.btn_dw.grid(row=0, column=3, padx=(0,12), pady=(4,2), sticky="w")
		self.chk_op_equiv.grid(row=0, column=4, padx=(0,16), pady=(4,2), sticky="w")

		# o rótulo "Type to Show:"
		self.lbl_type.grid(row=0, column=5, padx=(0,6), pady=(4,2), sticky="w")

		# 🔸 frame que vai conter os 3 checkboxes
		# ele ocupa da coluna 6 até 8, mas como um único widget
		self.frm_types.grid(row=0, column=6, columnspan=3, padx=(0,4), pady=(4,2), sticky="ew")

		# o frame expande
		self.columnconfigure(6, weight=1)
		self.columnconfigure(7, weight=1)
		self.columnconfigure(8, weight=1)

		# 🔸 dentro do frame: 3 colunas iguais
		for c in range(3):
			self.frm_types.columnconfigure(c, weight=1, uniform="types3")

		# cada checkbox em sua coluna, preenchendo horizontalmente
		self.chk_alive.grid(row=0, column=0, sticky="ew", padx=(0,4))
		self.chk_equiv.grid(row=0, column=1, sticky="ew", padx=(0,4))
		self.chk_dead.grid(row=0, column=2, sticky="ew")


		# Linha 2
		self.lbl_status.grid(row=1, column=0, padx=(4,2), pady=(2,6), sticky="w")
		self.ent_status.grid(row=1, column=1, padx=(0,12), pady=(2,6), sticky="w")
		self.lbl_operator.grid(row=1, column=2, padx=(0,2), pady=(2,6), sticky="w")
		self.ent_operator.grid(row=1, column=3, columnspan=4, padx=(0,12), pady=(2,6), sticky="we")

		# Títulos
		self.lbl_orig_title.grid(row=2, column=0, columnspan=5, pady=(2,2), sticky="w")
		self.lbl_mut_title.grid(row=2, column=5, columnspan=6, pady=(2,2), sticky="w")

		# Textos com rolagem
		self.frm_left.grid(row=3, column=0, columnspan=5, sticky="nsew", padx=(0,6), pady=(2,6))
		self.frm_left.rowconfigure(0, weight=1)
		self.frm_left.columnconfigure(0, weight=1)
		self.txt_left.grid(row=0, column=0, sticky="nsew")
		self.scrl_left_y.grid(row=0, column=1, sticky="ns")
		self.scrl_left_x.grid(row=1, column=0, sticky="ew")

		self.frm_right.grid(row=3, column=5, columnspan=6, sticky="nsew", padx=(6,0), pady=(2,6))
		self.frm_right.rowconfigure(0, weight=1)
		self.frm_right.columnconfigure(0, weight=1)
		self.txt_right.grid(row=0, column=0, sticky="nsew")
		self.scrl_right_y.grid(row=0, column=1, sticky="ns")
		self.scrl_right_x.grid(row=1, column=0, sticky="ew")

		# Rodapé
		self.btn_ok.grid(row=4, column=0, columnspan=11, pady=(2,2))

		# Expansão
		self.rowconfigure(3, weight=1)

	def _bind_events(self):
		# Confirma Mutant apenas no Enter
		self.ent_mutant.bind("<Return>", self.on_mutant_enter)

	# ------------------ Handlers ------------------
	def on_mutant_enter(self, event=None):
		text = self.var_mutant.get()
		new_id = clamp_int(text, default=1)
		self.var_mutant.set(str(new_id))
		# mantém o foco no campo após confirmar
		self.ent_mutant.focus_set()
		if self.init_fields(int(self.var_mutant.get())) < 0:
			print('Not set.')
			self.var_mutant.set(str(self.last))

	def on_up(self):
		text = self.var_mutant.get()
		cur = clamp_int(self.var_mutant.get(), default=1) + 1
		while True:
			try:
				reg_muta = Mutant.get(Mutant.id==cur)
			except:
				cur = self.last
				break
			if reg_muta.status == 'live' and bool(self.var_show_alive.get()):
				break
			elif reg_muta.status == 'dead' and bool(self.var_show_dead.get()):
				break
			elif reg_muta.status == 'equiv' and bool(self.var_show_equiv.get()):
				break
			else:
				cur += 1
		self.var_mutant.set(str(cur))
		self.init_fields(cur)
		log(f"[Mutant] up -> {cur}")

	def on_dw(self):
		text = self.var_mutant.get()
		cur = clamp_int(self.var_mutant.get(), default=1) - 1
		while True:
			try:
				reg_muta = Mutant.get(Mutant.id==cur)
			except:
				cur = self.last
				break
			if reg_muta.status == 'live' and bool(self.var_show_alive.get()):
				break
			elif reg_muta.status == 'dead' and bool(self.var_show_dead.get()):
				break
			elif reg_muta.status == 'equiv' and bool(self.var_show_equiv.get()):
				break
			else:
				cur -= 1
		self.var_mutant.set(str(cur))
		self.init_fields(cur)
		log(f"[Mutant] up -> {cur}")


	def on_op_equiv(self):
		log(f"[Operator.Equivalent] {bool(self.var_op_equiv.get())}")
		try:
			reg_muta = Mutant.get(Mutant.id==int(self.var_mutant.get()))
			if bool(self.var_op_equiv.get()):
				reg_muta.status = 'equiv'
			else:
				reg_muta.status = 'live'
			reg_muta.save()
		except:
			pass

	def on_show_alive(self):
		log(f"[Type to Show] Alive -> {bool(self.var_show_alive.get())}")

	def on_show_dead(self):
		log(f"[Type to Show] Dead -> {bool(self.var_show_dead.get())}")

	def on_show_equiv(self):
		log(f"[Type to Show] Equivalent -> {bool(self.var_show_equiv.get())}")


	def on_ok(self):
		log("[OK] clicado")

# ---------------------- Main ----------------------
def mutaview_gui(init_muta):
	root = tk.Tk()
#	style = ttk.Style()
	#print("Tema atual:", style.theme_use())
#	print("Temas disponíveis:", style.theme_names())
#	new_style = style.theme_names()[random.randint(0,len(style.theme_names()))]
#	style.theme_use(new_style)
#	print(new_style)
	root.title("View Mutants")
	# High-DPI / expansão
	root.rowconfigure(0, weight=1)
	root.columnconfigure(0, weight=1)
	app = ViewMutantsApp(root)
	root.minsize(900, 520)
	app.init_fields(init_muta)
	root.mainloop()


