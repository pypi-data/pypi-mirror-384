import tkinter as tk
import ast
import math
import re


y = None
a = ''


def _clean_expr(expr: str) -> str:
    expr = expr.replace('^', '**').replace(' ', '')
    # 3x -> 3*x
    expr = re.sub(r'(\d)(x)', r'\1*\2', expr)
    # x2 -> x*2
    expr = re.sub(r'(x)(\d)', r'\1*\2', expr)
    # 2( -> 2*(
    expr = re.sub(r'(\d)\(', r'\1*(', expr)
    # )x -> )*x
    expr = re.sub(r'\)(x)', r')*\1', expr)
    # x( -> x*(
    expr = re.sub(r'(x)\(', r'\1*(', expr)
    return expr


def make_function(expr: str):

    expr = _clean_expr(expr)

    node = ast.parse(expr, mode='eval')

    code = compile(node, "<string>", "eval")

    def f(x):

        allowed = {name: getattr(math, name) for name in dir(math) if not name.startswith("__")}
        allowed['x'] = x

        return eval(code, {"__builtins__": {}}, allowed)

    return f


class EquationCalculator:
    def __init__(self, root):
        self.root = root
        self.expression = ""

        self.entry = tk.Entry(root, font=("Arial", 20), justify="right", bd=6, relief="sunken")
        self.entry.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)

        self.result_label = tk.Label(root, text="", anchor="e", font=("Arial", 14))
        self.result_label.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=5)

        buttons = [
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2), ('/', 2, 3),
            ('4', 3, 0), ('5', 3, 1), ('6', 3, 2), ('*', 3, 3),
            ('1', 4, 0), ('2', 4, 1), ('3', 4, 2), ('-', 4, 3),
            ('.', 5, 0), ('0', 5, 1), ('x', 5, 2), ('+', 5, 3),
            ('^', 6, 0), ('(', 6, 1), (')', 6, 2), ('=', 6, 3),
            ('C', 7, 0), ('⌫', 7, 1)
        ]

        for text, r, c in buttons:
            btn = tk.Button(root, text=text, font=("Arial", 18),
                            command=lambda t=text: self.on_button_click(t))
            btn.grid(row=r, column=c, sticky="nsew", padx=3, pady=3)

        for i in range(8):
            root.rowconfigure(i, weight=1)
        for j in range(4):
            root.columnconfigure(j, weight=1)


        root.protocol("WM_DELETE_WINDOW", root.quit)

    def on_button_click(self, char):
        global y

        if char == 'C':
            self.expression = ""
            self.entry.delete(0, tk.END)
            self.result_label.config(text="")
            return


        if char == '⌫':
            self.expression = self.expression[:-1]
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self.expression)
            return

        if char == '=':
            expr = self.expression.strip()
            if not expr:
                self.result_label.config(text="Введите выражение")
                return

            try:
                global a
                a = expr
                clean = _clean_expr(expr)
                if 'x' in clean:
                    y = make_function(expr)
                    self.entry.delete(0, tk.END)
                    self.entry.insert(0, f"y = {expr}")
                    self.result_label.config(text="Создана функция y(x)")
                else:

                    val = eval(clean.replace('^', '**'))
                    y = lambda x=None, v=val: v
                    self.entry.delete(0, tk.END)
                    self.entry.insert(0, f"y = {val}")
                    self.result_label.config(text="y — константа")


                self.root.quit()
            except Exception as e:

                self.result_label.config(text=f"Ошибка: {e}")
            return


        self.expression += str(char)
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self.expression)
        self.result_label.config(text="")


def run_calculator():
    root = tk.Tk()
    app = EquationCalculator(root)
    root.geometry("380x520")
    root.title("Функциональный калькулятор")
    root.mainloop()
    try:
        root.destroy()
    except:
        pass
    return y