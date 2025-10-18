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
    cleaned_expr = _clean_expr(expr)
    node = ast.parse(cleaned_expr, mode='eval')
    code = compile(node, "<string>", "eval")

    def f(x):
        allowed_math = {name: getattr(math, name) for name in dir(math) if not name.startswith("__")}

        local_scope = {'x': x}
        local_scope.update(allowed_math)

        return eval(code, {"__builtins__": {}}, local_scope)

    return f


class EquationCalculator:
    def __init__(self, root):
        self.root = root
        self.expression = ""
        self.result_function = None

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

        root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):

        self.root.quit()

    def on_button_click(self, char):
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
                self.result_label.config(text="Enter an expression")
                return

            try:
                global a
                a = expr
                global y

                clean = _clean_expr(expr)
                if 'x' in clean:
                    self.result_function = make_function(expr)

                    y = self.result_function
                    self.entry.delete(0, tk.END)
                    self.entry.insert(0, f"y = {expr}")
                    self.result_label.config(text="Created expression y(x)")
                else:
                    val = eval(clean)
                    self.result_function = lambda x=None, v=val: v

                    y = self.result_function
                    self.entry.delete(0, tk.END)
                    self.entry.insert(0, f"y = {val}")
                    self.result_label.config(text="y — const")

                self.root.after(500, self.on_close)

            except Exception as e:
                self.result_label.config(text=f"Error: {e}")
            return

        self.expression += str(char)
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self.expression)
        self.result_label.config(text="")


def run_calculator():
    root = tk.Tk()
    app = EquationCalculator(root)
    root.geometry("380x520")
    root.title("Function input")
    root.mainloop()
    try:
        root.destroy()
    except tk.TclError:
        pass

    return app.result_function
