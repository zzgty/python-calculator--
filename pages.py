import tkinter as tk
import math
import os
import sys

# ── Capacitor Conversion ────────────────────────────────────────

CAP_UNITS = ["F", "mF", "\u03bcF", "nF", "pF"]
CAP_VALS = [1e0, 1e-3, 1e-6, 1e-9, 1e-12]


class CapPage:
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg="#1e1e1e")
        self._entries = []
        self._build()

    def show(self):
        self.frame.grid()
        self.frame.tkraise()
        self.frame.focus_set()

    def hide(self):
        self.frame.grid_remove()

    def scale_fonts(self, scale):
        fs = max(9, round(11 * scale))

        def rec(w):
            for c in w.winfo_children():
                if isinstance(c, (tk.Label, tk.Entry, tk.Button, tk.Menubutton)):
                    try:
                        c.config(font=("Segoe UI", fs))
                    except Exception:
                        pass
                rec(c)
        rec(self.frame)

    def _build(self):
        top = tk.Frame(self.frame, bg="#1e1e1e")
        top.pack(fill=tk.X, pady=(20, 10))
        tk.Label(top, text="\u7535\u5bb9\u6362\u7b97", bg="#1e1e1e", fg="white",
                 font=("Segoe UI", 14, "bold")).pack()

        row = tk.Frame(self.frame, bg="#1e1e1e")
        row.pack(fill=tk.X, padx=30, pady=10)

        self.src_val = tk.StringVar()
        self.src_unit = tk.StringVar(value="\u03bcF")
        e = tk.Entry(row, textvariable=self.src_val, bg="#2d2d2d", fg="white",
                     font=("Segoe UI", 12), relief=tk.FLAT, bd=6, insertbackground="white")
        e.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        om = tk.OptionMenu(row, self.src_unit, *CAP_UNITS)
        om.config(bg="#3a6ea5", fg="white", font=("Segoe UI", 11), relief=tk.FLAT,
                  activebackground="#4a7eb5", border=0, indicatoron=0)
        om["menu"].config(bg="#2d2d2d", fg="white", font=("Segoe UI", 10))
        om.pack(side=tk.RIGHT)

        calc_btn = tk.Button(self.frame, text="\u8ba1\u7b97", bg="#4caf50", fg="white",
                             font=("Segoe UI", 12, "bold"), relief=tk.FLAT, cursor="hand2",
                             command=self._calc)
        calc_btn.pack(pady=10)

        self.results_frame = tk.Frame(self.frame, bg="#1e1e1e")
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        self._result_labels = []
        for unit in CAP_UNITS:
            r = tk.Frame(self.results_frame, bg="#2d2d2d")
            r.pack(fill=tk.X, pady=2)
            tk.Label(r, text=unit, bg="#2d2d2d", fg="#8a8a8a",
                     font=("Segoe UI", 11), width=6, anchor="w").pack(side=tk.LEFT, padx=8, pady=4)
            lb = tk.Label(r, text="", bg="#2d2d2d", fg="white",
                          font=("Segoe UI", 12, "bold"), anchor="e")
            lb.pack(side=tk.RIGHT, padx=8, pady=4)
            self._result_labels.append(lb)

    def _calc(self):
        try:
            val = float(self.src_val.get())
        except ValueError:
            for lb in self._result_labels:
                lb.config(text="")
            return
        src_idx = CAP_UNITS.index(self.src_unit.get())
        farads = val * CAP_VALS[src_idx]
        for i, lb in enumerate(self._result_labels):
            v = farads / CAP_VALS[i]
            av = abs(v)
            if av >= 10000:
                v = round(v)
            elif av >= 1:
                v = round(v, 6)
            else:
                v = round(v, 12)
            if v == int(v):
                s = str(int(v))
            else:
                s = f"{v:.12f}".rstrip("0").rstrip(".")
                s = "0" if s == "-0" else s
            lb.config(text=s)


# ── RC Filter ───────────────────────────────────────────────────

R_UNITS = ["\u03a9", "k\u03a9", "M\u03a9"]
R_VALS = [1, 1e3, 1e6]
C_UNITS = ["pF", "nF", "\u03bcF", "mF", "F"]
C_VALS = [1e-12, 1e-9, 1e-6, 1e-3, 1]
F_UNITS = ["Hz", "kHz", "MHz"]
F_VALS = [1, 1e3, 1e6]


class _FilterPageBase:
    def _make_row(self, parent, label, var, unit_var, units, **kw):
        r = tk.Frame(parent, bg="#1e1e1e")
        r.pack(fill=tk.X, pady=4)
        tk.Label(r, text=label, bg="#1e1e1e", fg="#c8c8c8",
                 font=("Segoe UI", 11), width=4, anchor="w").pack(side=tk.LEFT)
        e = tk.Entry(r, textvariable=var, bg="#2d2d2d", fg="white",
                     font=("Segoe UI", 12), relief=tk.FLAT, bd=6, insertbackground="white")
        e.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        om = tk.OptionMenu(r, unit_var, *units)
        om.config(bg="#3a6ea5", fg="white", font=("Segoe UI", 11), relief=tk.FLAT,
                  activebackground="#4a7eb5", border=0, indicatoron=0)
        om["menu"].config(bg="#2d2d2d", fg="white", font=("Segoe UI", 10))
        om.pack(side=tk.RIGHT)
        return r

    def _make_calc_btn(self, parent, cmd):
        return tk.Button(parent, text="\u8ba1\u7b97", bg="#4caf50", fg="white",
                         font=("Segoe UI", 12, "bold"), relief=tk.FLAT, cursor="hand2",
                         command=cmd)

    def _get(self, var, unit_vals, unit_var):
        try:
            v = float(var.get())
        except ValueError:
            return None
        idx = unit_vals.index(unit_var.get())
        return v  # value in the unit the user typed (will be converted later)


def _load_img(path):
    dirs = [os.path.dirname(__file__)]
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        dirs.insert(0, sys._MEIPASS)
    for d in dirs:
        full = os.path.join(d, path)
        if os.path.isfile(full):
            try:
                return tk.PhotoImage(file=full)
            except Exception:
                return None
    return None


class RCPage(_FilterPageBase):
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg="#1e1e1e")
        self.R_var = tk.StringVar()
        self.C_var = tk.StringVar()
        self.f_var = tk.StringVar()
        self.R_unit = tk.StringVar(value="k\u03a9")
        self.C_unit = tk.StringVar(value="\u03bcF")
        self.f_unit = tk.StringVar(value="Hz")
        self._build()

    def show(self):
        self.frame.grid()
        self.frame.tkraise()
        self.frame.focus_set()

    def hide(self):
        self.frame.grid_remove()

    def scale_fonts(self, scale):
        fs = max(9, round(11 * scale))
        for w in self.frame.winfo_children():
            if isinstance(w, tk.Frame):
                for c in w.winfo_children():
                    if isinstance(c, (tk.Label, tk.Entry, tk.Button, tk.Frame)):
                        self._scale_recursive(c, fs)

    def _scale_recursive(self, w, fs):
        if isinstance(w, (tk.Label, tk.Entry, tk.Button)):
            try:
                w.config(font=("Segoe UI", fs))
            except Exception:
                pass
        if hasattr(w, "winfo_children"):
            for c in w.winfo_children():
                self._scale_recursive(c, fs)

    def _build(self):
        tk.Label(self.frame, text="RC \u4f4e\u901a\u6ee4\u6ce2\u5668", bg="#1e1e1e",
                 fg="white", font=("Segoe UI", 14, "bold")).pack(pady=(20, 5))
        tk.Label(self.frame, text="f\u2093 = 1 / (2\u03c0RC)", bg="#1e1e1e", fg="#8a8a8a",
                 font=("Segoe UI", 10)).pack()

        mid = tk.Frame(self.frame, bg="#1e1e1e")
        mid.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        self.rc_img = _load_img("rc\u6ee4\u6ce2-20606.png")
        if self.rc_img:
            img_label = tk.Label(mid, image=self.rc_img, bg="#1e1e1e")
            img_label.pack(side=tk.LEFT, padx=(0, 10))

        form = tk.Frame(mid, bg="#1e1e1e")
        form.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        self._make_row(form, "R:", self.R_var, self.R_unit, R_UNITS)
        self._make_row(form, "C:", self.C_var, self.C_unit, C_UNITS)
        self._make_row(form, "f:", self.f_var, self.f_unit, F_UNITS)

        btn = self._make_calc_btn(self.frame, self._calc)
        btn.pack(pady=6)

        self.result_var = tk.StringVar()
        tk.Label(self.frame, textvariable=self.result_var, bg="#1e1e1e", fg="#4caf50",
                 font=("Segoe UI", 14, "bold"), wraplength=400).pack(pady=6)
        tk.Label(self.frame, text="\u8f93\u5165\u4efb\u610f\u4e24\u4e2a\u503c\u8ba1\u7b97\u7b2c\u4e09\u4e2a",
                 bg="#1e1e1e", fg="#6a6a6a", font=("Segoe UI", 9)).pack()

    def _calc(self):
        R_idx = R_UNITS.index(self.R_unit.get())
        C_idx = C_UNITS.index(self.C_unit.get())
        f_idx = F_UNITS.index(self.f_unit.get())

        try:
            R_val = float(self.R_var.get()) * R_VALS[R_idx] if self.R_var.get() else None
        except ValueError:
            R_val = None
        try:
            C_val = float(self.C_var.get()) * C_VALS[C_idx] if self.C_var.get() else None
        except ValueError:
            C_val = None
        try:
            f_val = float(self.f_var.get()) * F_VALS[f_idx] if self.f_var.get() else None
        except ValueError:
            f_val = None

        filled = sum(1 for v in (R_val, C_val, f_val) if v is not None)
        if filled < 2:
            self.result_var.set("\u8bf7\u8f93\u5165\u81f3\u5c11\u4e24\u4e2a\u503c")
            return

        try:
            if R_val is not None and C_val is not None:
                result_f = 1 / (2 * math.pi * R_val * C_val)
                self.f_var.set(f"{result_f / F_VALS[f_idx]:.4g}")
                self.result_var.set(f"f\u2093 = {result_f / F_VALS[f_idx]:.4g} {self.f_unit.get()}")
            elif R_val is not None and f_val is not None:
                result_c = 1 / (2 * math.pi * R_val * f_val)
                self.C_var.set(f"{result_c / C_VALS[C_idx]:.4g}")
                self.result_var.set(f"C = {result_c / C_VALS[C_idx]:.4g} {self.C_unit.get()}")
            elif C_val is not None and f_val is not None:
                result_r = 1 / (2 * math.pi * C_val * f_val)
                self.R_var.set(f"{result_r / R_VALS[R_idx]:.4g}")
                self.result_var.set(f"R = {result_r / R_VALS[R_idx]:.4g} {self.R_unit.get()}")
        except Exception:
            self.result_var.set("\u8ba1\u7b97\u51fa\u9519")


# ── LC Filter ───────────────────────────────────────────────────

L_UNITS = ["\u03bcH", "mH", "H"]
L_VALS = [1e-6, 1e-3, 1]


class LCPage(_FilterPageBase):
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg="#1e1e1e")
        self.L_var = tk.StringVar()
        self.C_var = tk.StringVar()
        self.f_var = tk.StringVar()
        self.L_unit = tk.StringVar(value="\u03bcH")
        self.C_unit = tk.StringVar(value="\u03bcF")
        self.f_unit = tk.StringVar(value="Hz")
        self._build()

    def show(self):
        self.frame.grid()
        self.frame.tkraise()
        self.frame.focus_set()

    def hide(self):
        self.frame.grid_remove()

    def scale_fonts(self, scale):
        fs = max(9, round(11 * scale))
        for w in self.frame.winfo_children():
            if isinstance(w, tk.Frame):
                for c in w.winfo_children():
                    self._scale_recursive(c, fs)

    def _scale_recursive(self, w, fs):
        if isinstance(w, (tk.Label, tk.Entry, tk.Button)):
            try:
                w.config(font=("Segoe UI", fs))
            except Exception:
                pass
        if hasattr(w, "winfo_children"):
            for c in w.winfo_children():
                self._scale_recursive(c, fs)

    def _build(self):
        tk.Label(self.frame, text="LC \u4f4e\u901a\u6ee4\u6ce2\u5668", bg="#1e1e1e",
                 fg="white", font=("Segoe UI", 14, "bold")).pack(pady=(20, 5))
        tk.Label(self.frame, text="f\u2093 = 1 / (2\u03c0\u221a(LC))", bg="#1e1e1e",
                 fg="#8a8a8a", font=("Segoe UI", 10)).pack()

        mid = tk.Frame(self.frame, bg="#1e1e1e")
        mid.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        self.lc_img = _load_img("lc\u6ee4\u6ce2-202606.png")
        if self.lc_img:
            img_label = tk.Label(mid, image=self.lc_img, bg="#1e1e1e")
            img_label.pack(side=tk.LEFT, padx=(0, 10))

        form = tk.Frame(mid, bg="#1e1e1e")
        form.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        self._make_row(form, "L:", self.L_var, self.L_unit, L_UNITS)
        self._make_row(form, "C:", self.C_var, self.C_unit, C_UNITS)
        self._make_row(form, "f:", self.f_var, self.f_unit, F_UNITS)

        btn = self._make_calc_btn(self.frame, self._calc)
        btn.pack(pady=6)

        self.result_var = tk.StringVar()
        tk.Label(self.frame, textvariable=self.result_var, bg="#1e1e1e", fg="#4caf50",
                 font=("Segoe UI", 14, "bold"), wraplength=400).pack(pady=6)
        tk.Label(self.frame, text="\u8f93\u5165\u4efb\u610f\u4e24\u4e2a\u503c\u8ba1\u7b97\u7b2c\u4e09\u4e2a",
                 bg="#1e1e1e", fg="#6a6a6a", font=("Segoe UI", 9)).pack()

    def _calc(self):
        L_idx = L_UNITS.index(self.L_unit.get())
        C_idx = C_UNITS.index(self.C_unit.get())
        f_idx = F_UNITS.index(self.f_unit.get())

        try:
            L_val = float(self.L_var.get()) * L_VALS[L_idx] if self.L_var.get() else None
        except ValueError:
            L_val = None
        try:
            C_val = float(self.C_var.get()) * C_VALS[C_idx] if self.C_var.get() else None
        except ValueError:
            C_val = None
        try:
            f_val = float(self.f_var.get()) * F_VALS[f_idx] if self.f_var.get() else None
        except ValueError:
            f_val = None

        filled = sum(1 for v in (L_val, C_val, f_val) if v is not None)
        if filled < 2:
            self.result_var.set("\u8bf7\u8f93\u5165\u81f3\u5c11\u4e24\u4e2a\u503c")
            return

        try:
            if L_val is not None and C_val is not None:
                result_f = 1 / (2 * math.pi * math.sqrt(L_val * C_val))
                self.f_var.set(f"{result_f / F_VALS[f_idx]:.4g}")
                self.result_var.set(f"f\u2093 = {result_f / F_VALS[f_idx]:.4g} {self.f_unit.get()}")
            elif L_val is not None and f_val is not None:
                result_c = 1 / (4 * math.pi ** 2 * L_val * f_val ** 2)
                self.C_var.set(f"{result_c / C_VALS[C_idx]:.4g}")
                self.result_var.set(f"C = {result_c / C_VALS[C_idx]:.4g} {self.C_unit.get()}")
            elif C_val is not None and f_val is not None:
                result_l = 1 / (4 * math.pi ** 2 * C_val * f_val ** 2)
                self.L_var.set(f"{result_l / L_VALS[L_idx]:.4g}")
                self.result_var.set(f"L = {result_l / L_VALS[L_idx]:.4g} {self.L_unit.get()}")
        except Exception:
            self.result_var.set("\u8ba1\u7b97\u51fa\u9519")


# ── Voltage Divider ─────────────────────────────────────────────

V_UNITS = ["V", "mV"]
V_VALS = [1, 1e-3]
R_UNITS_DIV = ["\u03a9", "k\u03a9", "M\u03a9"]
R_VALS_DIV = [1, 1e3, 1e6]


class DivPage(_FilterPageBase):
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg="#1e1e1e")
        self.Vin_var = tk.StringVar()
        self.Vout_var = tk.StringVar()
        self.R1_var = tk.StringVar()
        self.R2_var = tk.StringVar()
        self.Vin_unit = tk.StringVar(value="V")
        self.Vout_unit = tk.StringVar(value="V")
        self.R1_unit = tk.StringVar(value="k\u03a9")
        self.R2_unit = tk.StringVar(value="k\u03a9")
        self._build()

    def show(self):
        self.frame.grid()
        self.frame.tkraise()
        self.frame.focus_set()

    def hide(self):
        self.frame.grid_remove()

    def scale_fonts(self, scale):
        fs = max(9, round(11 * scale))
        for w in self.frame.winfo_children():
            if isinstance(w, tk.Frame):
                for c in w.winfo_children():
                    self._scale_recursive(c, fs)

    def _scale_recursive(self, w, fs):
        if isinstance(w, (tk.Label, tk.Entry, tk.Button)):
            try:
                w.config(font=("Segoe UI", fs))
            except Exception:
                pass
        if hasattr(w, "winfo_children"):
            for c in w.winfo_children():
                self._scale_recursive(c, fs)

    def _build(self):
        tk.Label(self.frame, text="\u7535\u963b\u5206\u538b\u8ba1\u7b97", bg="#1e1e1e",
                 fg="white", font=("Segoe UI", 14, "bold")).pack(pady=(20, 5))
        tk.Label(self.frame, text="V\u2092\u1d62\u2099 \u00d7 R\u2082 / (R\u2081 + R\u2082)",
                 bg="#1e1e1e", fg="#8a8a8a", font=("Segoe UI", 10)).pack()

        mid = tk.Frame(self.frame, bg="#1e1e1e")
        mid.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        self.div_img = _load_img("\u7535\u963b\u5206\u538b\u914d\u56fe-202606.png")
        if self.div_img:
            img_label = tk.Label(mid, image=self.div_img, bg="#1e1e1e")
            img_label.pack(side=tk.LEFT, padx=(0, 10))

        form = tk.Frame(mid, bg="#1e1e1e")
        form.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        self._make_row(form, "Vi:", self.Vin_var, self.Vin_unit, V_UNITS)
        self._make_row(form, "Vo:", self.Vout_var, self.Vout_unit, V_UNITS)
        self._make_row(form, "Ra:", self.R1_var, self.R1_unit, R_UNITS_DIV)
        self._make_row(form, "Rb:", self.R2_var, self.R2_unit, R_UNITS_DIV)

        btn = self._make_calc_btn(self.frame, self._calc)
        btn.pack(pady=6)

        self.result_var = tk.StringVar()
        tk.Label(self.frame, textvariable=self.result_var, bg="#1e1e1e", fg="#4caf50",
                 font=("Segoe UI", 14, "bold"), wraplength=400).pack(pady=6)
        tk.Label(self.frame, text="\u8f93\u5165\u4efb\u610f\u4e09\u4e2a\u503c\u8ba1\u7b97\u7b2c\u56db\u4e2a",
                 bg="#1e1e1e", fg="#6a6a6a", font=("Segoe UI", 9)).pack()

    def _calc(self):
        Vi_idx = V_UNITS.index(self.Vin_unit.get())
        Vo_idx = V_UNITS.index(self.Vout_unit.get())
        R1_idx = R_UNITS_DIV.index(self.R1_unit.get())
        R2_idx = R_UNITS_DIV.index(self.R2_unit.get())

        def get_val(var, vals, idx):
            if not var.get():
                return None
            try:
                return float(var.get()) * vals[idx]
            except ValueError:
                return None

        Vin = get_val(self.Vin_var, V_VALS, Vi_idx)
        Vout = get_val(self.Vout_var, V_VALS, Vo_idx)
        R1 = get_val(self.R1_var, R_VALS_DIV, R1_idx)
        R2 = get_val(self.R2_var, R_VALS_DIV, R2_idx)

        filled = sum(1 for v in (Vin, Vout, R1, R2) if v is not None)
        if filled < 3:
            self.result_var.set("\u8bf7\u8f93\u5165\u81f3\u5c11\u4e09\u4e2a\u503c")
            return

        try:
            if Vin is not None and R1 is not None and R2 is not None:
                result = Vin * R2 / (R1 + R2)
                self.Vout_var.set(f"{result / V_VALS[Vo_idx]:.4g}")
                self.result_var.set(f"V\u2092\u1d62\u2099 = {result / V_VALS[Vo_idx]:.4g} {self.Vout_unit.get()}")
            elif Vin is not None and Vout is not None and R1 is not None:
                result_r2 = R1 * Vout / (Vin - Vout)
                self.R2_var.set(f"{result_r2 / R_VALS_DIV[R2_idx]:.4g}")
                self.result_var.set(f"R\u2082 = {result_r2 / R_VALS_DIV[R2_idx]:.4g} {self.R2_unit.get()}")
            elif Vin is not None and Vout is not None and R2 is not None:
                result_r1 = R2 * (Vin - Vout) / Vout
                self.R1_var.set(f"{result_r1 / R_VALS_DIV[R1_idx]:.4g}")
                self.result_var.set(f"R\u2081 = {result_r1 / R_VALS_DIV[R1_idx]:.4g} {self.R1_unit.get()}")
            elif Vout is not None and R1 is not None and R2 is not None:
                result_vin = Vout * (R1 + R2) / R2
                self.Vin_var.set(f"{result_vin / V_VALS[Vi_idx]:.4g}")
                self.result_var.set(f"V\u2096\u2099 = {result_vin / V_VALS[Vi_idx]:.4g} {self.Vin_unit.get()}")
        except (ZeroDivisionError, Exception):
            self.result_var.set("\u8ba1\u7b97\u51fa\u9519")


# ── Calculator Page ─────────────────────────────────────────────

class CalculatorPage:
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg="#1e1e1e")

        self.expression = ""
        self.result_var = tk.StringVar(value="0")
        self.expression_var = tk.StringVar(value="")
        self.history = []
        self.radian = True
        self.new_input = False
        self._all_btns = []
        self._sci_btns = []

        self._create_display()
        self._create_body()
        self._bind_keys()

    def show(self):
        self.frame.grid()
        self.frame.tkraise()
        self.frame.focus_set()

    def hide(self):
        self.frame.grid_remove()

    def scale_fonts(self, scale):
        expr_font = ("Segoe UI", max(8, round(10 * scale)))
        result_font = ("Segoe UI", max(14, round(26 * scale)), "bold")
        hist_font = ("Consolas", max(6, round(8 * scale)))
        num_font = ("Segoe UI", max(9, round(12 * scale)))
        sci_font = ("Segoe UI", max(8, round(11 * scale)))
        eq_font = ("Segoe UI", max(10, round(14 * scale)), "bold")

        self.expr_label.config(font=expr_font)
        self.result_label.config(font=result_font)
        self.history_box.config(font=hist_font)
        for b in self._all_btns:
            b.config(font=num_font)
        for b in self._sci_btns:
            b.config(font=sci_font)
        if self._all_btns:
            self._all_btns[-1].config(font=eq_font)

    # ── Display ──────────────────────────────────────────────

    def _create_display(self):
        display = tk.Frame(self.frame, bg="#1e1e1e")
        display.pack(fill=tk.X, padx=8, pady=(4, 2))

        self.expr_label = tk.Label(display, textvariable=self.expression_var,
                                   anchor="e", bg="#2d2d2d", fg="#8a8a8a",
                                   font=("Segoe UI", 10), padx=12, pady=4)
        self.expr_label.pack(fill=tk.X)

        self.result_label = tk.Label(display, textvariable=self.result_var,
                                     anchor="e", bg="#2d2d2d", fg="white",
                                     font=("Segoe UI", 26, "bold"), padx=12, pady=6)
        self.result_label.pack(fill=tk.X)

    # ── Body ─────────────────────────────────────────────────

    def _create_body(self):
        main = tk.Frame(self.frame, bg="#1e1e1e")
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self._create_sci_pad(main)
        self._create_num_pad(main)
        self._create_history(main)

        main.columnconfigure(0, weight=2)
        main.columnconfigure(1, weight=3)
        main.rowconfigure(0, weight=1)
        main.rowconfigure(1, weight=0)

    def _lighten(self, color):
        try:
            r = min(255, int(color[1:3], 16) + 30)
            g = min(255, int(color[3:5], 16) + 30)
            b = min(255, int(color[5:7], 16) + 30)
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return color

    def _sci_btn(self, parent, text, color, row, col):
        b = tk.Button(parent, text=text, bg=color, fg="white",
                      activebackground=self._lighten(color),
                      font=("Segoe UI", 10), relief=tk.FLAT, cursor="hand2",
                      command=lambda t=text: self._on_sci(t))
        b.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
        self._sci_btns.append(b)

    def _create_sci_pad(self, parent):
        frame = tk.Frame(parent, bg="#1e1e1e")
        frame.grid(row=0, column=0, sticky="nsew")

        sci_btns = [
            ("sin", "#3a6ea5"), ("cos", "#3a6ea5"), ("tan", "#3a6ea5"),
            ("log", "#3a6ea5"), ("ln", "#3a6ea5"), ("\u221a", "#3a6ea5"),
            ("x\u00b2", "#5a5a8a"), ("x\u00b3", "#5a5a8a"), ("x\u207f", "#5a5a8a"),
            ("1/x", "#5a5a8a"), ("n!", "#5a5a8a"), ("\u03c0", "#5a5a8a"),
            ("e", "#5a5a8a"), ("EXP", "#5a5a8a"), ("Rad", "#8a6a3a"),
        ]

        for i, (txt, clr) in enumerate(sci_btns):
            self._sci_btn(frame, txt, clr, *divmod(i, 3))

        for i in range(5):
            frame.rowconfigure(i, weight=1)
        for i in range(3):
            frame.columnconfigure(i, weight=1)

    def _num_btn(self, parent, text, color, row, col, span=1):
        b = tk.Button(parent, text=text, bg=color, fg="white",
                      activebackground=self._lighten(color),
                      font=("Segoe UI", 11), relief=tk.FLAT, cursor="hand2",
                      command=lambda t=text: self._on_click(t))
        b.grid(row=row, column=col, columnspan=span, sticky="nsew", padx=2, pady=2)
        self._all_btns.append(b)

    def _create_num_pad(self, parent):
        frame = tk.Frame(parent, bg="#1e1e1e")
        frame.grid(row=0, column=1, sticky="nsew")

        grey = "#3c3c3c"
        dgrey = "#2a2a2a"
        orange = "#d47c2a"

        layout = [
            ("(", grey, 0, 0), (")", grey, 0, 1), ("\u232b", "#a04040", 0, 2), ("C", "#a04040", 0, 3),
            ("7", dgrey, 1, 0), ("8", dgrey, 1, 1), ("9", dgrey, 1, 2), ("\u00f7", orange, 1, 3),
            ("4", dgrey, 2, 0), ("5", dgrey, 2, 1), ("6", dgrey, 2, 2), ("\u00d7", orange, 2, 3),
            ("1", dgrey, 3, 0), ("2", dgrey, 3, 1), ("3", dgrey, 3, 2), ("-", orange, 3, 3),
            ("\u00b1", grey, 4, 0), ("0", dgrey, 4, 1), (".", dgrey, 4, 2), ("+", orange, 4, 3),
        ]

        for args in layout:
            self._num_btn(frame, *args)

        eq = tk.Button(frame, text="=", bg="#4caf50", fg="white",
                       activebackground="#66bb6a",
                       font=("Segoe UI", 13, "bold"), relief=tk.FLAT, cursor="hand2",
                       command=lambda: self._on_click("="))
        eq.grid(row=5, column=0, columnspan=4, sticky="nsew", padx=2, pady=2)
        self._all_btns.append(eq)

        for i in range(6):
            frame.rowconfigure(i, weight=1)
        for i in range(4):
            frame.columnconfigure(i, weight=1)

    def _create_history(self, parent):
        frame = tk.LabelFrame(parent, text=" \u5386\u53f2\u8bb0\u5f55 ", fg="#8a8a8a",
                              bg="#1e1e1e", font=("Segoe UI", 9), labelanchor="nw")
        frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(6, 0))

        btn_frame = tk.Frame(frame, bg="#1e1e1e")
        btn_frame.pack(fill=tk.X, padx=2, pady=(2, 0))
        tk.Button(btn_frame, text="\u6e05\u7a7a", bg="#3c3c3c", fg="white",
                  relief=tk.FLAT, cursor="hand2",
                  command=self._clear_history).pack(side=tk.RIGHT)

        self.history_box = tk.Listbox(frame, height=4, bg="#2d2d2d", fg="#c8c8c8",
                                      selectbackground="#3a6ea5", border=0,
                                      font=("Consolas", 9), activestyle="none")
        self.history_box.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.history_box.bind("<ButtonRelease-1>", self._on_history_click)

    # ── Input Handling ──────────────────────────────────────

    def _on_click(self, text):
        if text == "C":
            self.expression = ""
            self.result_var.set("0")
            self.expression_var.set("")
            self.new_input = False
        elif text == "\u232b":
            if self.new_input:
                self.expression = ""
                self.new_input = False
            self.expression = self.expression[:-1]
            self.result_var.set(self.expression or "0")
        elif text == "\u00b1":
            if self.new_input:
                self.new_input = False
            if self.expression.startswith("-"):
                self.expression = self.expression[1:]
            else:
                self.expression = "-" + self.expression
            self.result_var.set(self.expression or "0")
        elif text == "=":
            self._calculate()
        else:
            if self.new_input:
                self.expression = ""
                self.new_input = False
            self.expression += text
            self.result_var.set(self.expression)

    def _on_sci(self, text):
        if text == "Rad":
            self.radian = not self.radian
            for b in self._sci_btns:
                if b.cget("text") == "Rad":
                    b.config(text="Deg")
                elif b.cget("text") == "Deg":
                    b.config(text="Rad")
        elif text == "\u03c0":
            self._insert_value("\u03c0")
        elif text == "e":
            self._insert_value("e")
        elif text == "\u221a":
            self._wrap_func("sqrt")
        elif text == "x\u00b2":
            self._wrap_func("sq")
        elif text == "x\u00b3":
            self._wrap_func("cb")
        elif text == "x\u207f":
            if self.new_input:
                self.expression = ""
                self.new_input = False
            self.expression = f"({self.expression})^"
            self.result_var.set(self.expression)
        elif text == "1/x":
            self._wrap_func("inv")
        elif text == "n!":
            self._wrap_func("factorial")
        elif text == "EXP":
            self._wrap_func("exp")
        else:
            self._wrap_func(text)

    def _insert_value(self, val):
        if self.new_input:
            self.expression = ""
            self.new_input = False
        self.expression += val
        self.result_var.set(self.expression)

    def _wrap_func(self, func):
        if self.new_input:
            self.expression = ""
            self.new_input = False
        self.expression = f"{func}({self.expression})"
        self.result_var.set(self.expression)

    # ── Calculation ──────────────────────────────────────────

    def _calculate(self):
        try:
            expr = self.expression.replace("\u00d7", "*").replace("\u00f7", "/")
            expr = expr.replace("^", "**")
            expr = expr.replace("\u03c0", str(math.pi)).replace("e", str(math.e))

            safe = {
                "sin": (lambda x: math.sin(x if self.radian else math.radians(x))),
                "cos": (lambda x: math.cos(x if self.radian else math.radians(x))),
                "tan": (lambda x: math.tan(x if self.radian else math.radians(x))),
                "log": math.log10, "ln": math.log, "sqrt": math.sqrt,
                "factorial": math.factorial, "exp": math.exp,
                "sq": lambda x: x ** 2, "cb": lambda x: x ** 3,
                "inv": lambda x: 1 / x,
            }

            result = eval(expr, {"__builtins__": {}}, safe)

            if isinstance(result, float):
                result_str = str(int(result)) if result.is_integer() else f"{result:.10g}"
            else:
                result_str = str(result)

            entry = f"{self.expression} = {result_str}"
            self.history.insert(0, entry)
            self.history_box.insert(0, entry)

            self.expression_var.set(self.expression)
            self.expression = result_str
            self.result_var.set(result_str)
            self.new_input = True

        except Exception:
            self.result_var.set("\u9519\u8bef")

    def _on_history_click(self, event):
        sel = self.history_box.curselection()
        if not sel:
            return
        entry = self.history_box.get(sel[0])
        if " = " in entry:
            result = entry.split(" = ", 1)[1]
            self.expression = result
            self.result_var.set(result)
            self.new_input = True

    def _clear_history(self):
        self.history.clear()
        self.history_box.delete(0, tk.END)

    def _bind_keys(self):
        for k in "0123456789.+-*/%()":
            self.frame.bind(f"<Key-{k}>", lambda e, t=k: self._on_click(
                {"*": "\u00d7", "/": "\u00f7"}.get(t, t)))
        self.frame.bind("<Return>", lambda e: self._on_click("="))
        self.frame.bind("<BackSpace>", lambda e: self._on_click("\u232b"))
        self.frame.bind("<Escape>", lambda e: self._on_click("C"))
