# === ФАЙЛ: src/ui.py ===
"""Главный интерфейс приложения на tkinter."""

from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import tkinter as tk
from typing import Optional

import matplotlib
matplotlib.use("Agg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.calculator import calculate_metrics
from src.charts import build_charts
from src.exporter import _safe_output_name, export_excel, export_html, export_pdf
from src.loader import DATA_DIR, load_facts, load_plans


class ReportApp(tk.Tk):
    """Основное окно отчётности WorkshopReport."""

    def __init__(self) -> None:
        super().__init__()
        self.title("WorkshopReport · Производственный отчёт")
        self.geometry("1100x760")
        self.minsize(1020, 700)
        self.configure(bg="#07111f")

        self.plans_df = None
        self.facts_df = None
        self.metrics_df = None
        self.current_figure = None
        self.canvas = None

        self.default_plans_path = DATA_DIR / "plans.xlsx"
        self.default_facts_path = DATA_DIR / "workshop_production_data.csv"
        self.default_export_dir = Path("exports")

        self.plan_path_var = tk.StringVar(value=str(self.default_plans_path))
        self.fact_path_var = tk.StringVar(value=str(self.default_facts_path))
        self.export_dir_var = tk.StringVar(value=str(self.default_export_dir))

        self._apply_theme()
        self._build_ui()
        self._load_data()

    def _apply_theme(self) -> None:
        """Настраивает современную тему Tkinter/ttk."""
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TLabel", background="#07111f", foreground="#e5eefb", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Accent.TButton", background="#2563eb", foreground="#ffffff", font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#1d4ed8"), ("!disabled", "#2563eb")])
        style.configure("Ghost.TButton", background="#111827", foreground="#dbeafe", font=("Segoe UI", 10, "bold"))
        style.map("Ghost.TButton", background=[("active", "#172554"), ("!disabled", "#111827")])

    def _build_ui(self) -> None:
        """Создаёт интерфейс приложения."""
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        sidebar = tk.Frame(self, bg="#0d1b2e", width=360, padx=16, pady=16)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.columnconfigure(0, weight=1)

        main = tk.Frame(self, bg="#07111f", padx=16, pady=16)
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(4, weight=1)

        tk.Label(sidebar, text="WorkshopReport", fg="#f8fafc", bg="#0b1220", font=("Segoe UI", 18, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(sidebar, text="Импорт и управление отчётами", fg="#bfdbfe", bg="#0b1220", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=(4, 12))

        self.import_btn = tk.Button(
            sidebar,
            text="Импорт документов",
            command=self.import_documents,
            bg="#16a34a",
            fg="#f8fafc",
            bd=0,
            highlightthickness=0,
            padx=12,
            pady=10,
            font=("Segoe UI", 10, "bold"),
            width=22,
            relief="flat",
        )
        self.import_btn.grid(row=2, column=0, sticky="ew")

        tk.Label(sidebar, text="Текущие файлы", fg="#e5eefb", bg="#0b1220", font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky="w", pady=(18, 8))

        self.plan_box = tk.Frame(sidebar, bg="#111d33", bd=0, padx=10, pady=10)
        self.plan_box.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        self.plan_name_label = tk.Label(self.plan_box, text="План (XLSX)", fg="#bfdbfe", bg="#111d33", font=("Segoe UI", 9, "bold"))
        self.plan_name_label.pack(anchor="w")
        self.plan_basename = tk.Label(self.plan_box, textvariable=self.plan_path_var, fg="#e2e8f0", bg="#111d33", justify="left", wraplength=260, font=("Segoe UI", 9))
        self.plan_basename.pack(anchor="w", pady=(4, 0))
        self.plan_status = tk.Label(self.plan_box, text="✗", fg="#f87171", bg="#111d33", font=("Segoe UI", 10, "bold"))
        self.plan_status.pack(anchor="e", pady=(6, 0))
        tk.Button(self.plan_box, text="🗑", command=lambda: self.clear_file("plan"), bg="#111d33", fg="#f8fafc", bd=0, highlightthickness=0, pady=4, relief="flat").place(relx=0.95, rely=0.02, anchor="ne")

        self.fact_box = tk.Frame(sidebar, bg="#111d33", bd=0, padx=10, pady=10)
        self.fact_box.grid(row=5, column=0, sticky="ew")
        self.fact_name_label = tk.Label(self.fact_box, text="Факт (CSV)", fg="#bfdbfe", bg="#111d33", font=("Segoe UI", 9, "bold"))
        self.fact_name_label.pack(anchor="w")
        self.fact_basename = tk.Label(self.fact_box, textvariable=self.fact_path_var, fg="#e2e8f0", bg="#111d33", justify="left", wraplength=260, font=("Segoe UI", 9))
        self.fact_basename.pack(anchor="w", pady=(4, 0))
        self.fact_status = tk.Label(self.fact_box, text="✗", fg="#f87171", bg="#111d33", font=("Segoe UI", 10, "bold"))
        self.fact_status.pack(anchor="e", pady=(6, 0))
        tk.Button(self.fact_box, text="🗑", command=lambda: self.clear_file("fact"), bg="#111d33", fg="#f8fafc", bd=0, highlightthickness=0, pady=4, relief="flat").place(relx=0.95, rely=0.02, anchor="ne")

        tk.Label(sidebar, text="Папка экспорта", fg="#e5eefb", bg="#0d1b2e", font=("Segoe UI", 10, "bold")).grid(row=6, column=0, sticky="w", pady=(14, 4))
        self.export_dir_var = tk.StringVar(value=str(self.default_export_dir))
        tk.Label(sidebar, textvariable=self.export_dir_var, fg="#e2e8f0", bg="#111d33", justify="left", wraplength=280, font=("Segoe UI", 9)).grid(row=7, column=0, sticky="ew", pady=(0, 6))
        tk.Button(sidebar, text="Выбрать папку", command=self.choose_export_dir, bg="#111d33", fg="#f8fafc", bd=0, highlightthickness=0, pady=6, relief="flat").grid(row=8, column=0, sticky="ew")

        tk.Label(sidebar, text="Подсказка: один клик — импорт обоих файлов", fg="#94a3b8", bg="#0b1220", justify="left", wraplength=300, font=("Segoe UI", 9)).grid(row=9, column=0, sticky="w", pady=(12, 0))

        header = tk.Frame(main, bg="#0a1628")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        tk.Label(header, text="Отчёт по цехам", fg="#e2e8f0", bg="#0a1628", font=("Segoe UI", 18, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(header, text="Выберите срез данных и сформируйте отчёт", fg="#94a3b8", bg="#0a1628", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=(4, 0))
        # status pill (canvas for rounded look)
        self.status_canvas = tk.Canvas(header, width=220, height=40, bg="#0a1628", highlightthickness=0)
        self.status_canvas.grid(row=0, column=1, rowspan=2, sticky="e")
        self._render_status_chip("Готов к загрузке", "#14532d", "#bbf7d0")

        filter_card = tk.Frame(main, bg="#0a1628", bd=0, padx=14, pady=14)
        filter_card.grid(row=1, column=0, sticky="ew", pady=(12, 12))
        filter_card.columnconfigure(0, weight=1)

        tk.Label(filter_card, text="Цеха", bg="#0a1628", fg="#e2e8f0", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        # chips selector container
        self.workshop_selector = tk.Frame(filter_card, bg="#0a1628")
        self.workshop_selector.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(self.workshop_selector, textvariable=self.search_var, bg="#111d33", fg="#e2e8f0", insertbackground="#e2e8f0")
        self.search_entry.pack(fill="x")
        self.search_var.trace_add("write", lambda *_: self._filter_workshops())
        self.chips_frame = tk.Frame(self.workshop_selector, bg="#0a1628")
        self.chips_frame.pack(fill="x", pady=(8, 6))
        self.workshop_vars: dict[str, tk.BooleanVar] = {}
        self.workshop_checks_frame = tk.Frame(self.workshop_selector, bg="#0a1628")
        self.workshop_checks_frame.pack(fill="both")

        row2 = tk.Frame(main, bg="#07111f")
        row2.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        row2.columnconfigure(1, weight=1)
        row2.columnconfigure(3, weight=1)

        tk.Label(row2, text="Период с", bg="#07111f", fg="#e5eefb", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.start_var = tk.StringVar(value="2025-01")
        self.start_combo = ttk.Combobox(row2, textvariable=self.start_var, state="readonly", width=12)
        self.start_combo.grid(row=0, column=1, sticky="w", padx=(0, 12))

        tk.Label(row2, text="по", bg="#07111f", fg="#e5eefb", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.end_var = tk.StringVar(value="2025-12")
        self.end_combo = ttk.Combobox(row2, textvariable=self.end_var, state="readonly", width=12)
        self.end_combo.grid(row=0, column=3, sticky="w")

        tk.Label(row2, text="Продукция", bg="#07111f", fg="#e5eefb", font=("Segoe UI", 10, "bold")).grid(row=0, column=4, sticky="w", padx=(12, 8))
        self.product_var = tk.StringVar(value="Все")
        self.product_combo = ttk.Combobox(row2, textvariable=self.product_var, state="readonly", width=18)
        self.product_combo.grid(row=0, column=5, sticky="w", padx=(0, 12))

        self.generate_btn = ttk.Button(row2, text="Сформировать отчёт", command=self.generate_report, style="Accent.TButton", width=20)
        self.generate_btn.grid(row=0, column=6, sticky="e")

        self.kpi_frame = tk.Frame(main, bg="#0a1628")
        self.kpi_frame.grid(row=3, column=0, sticky="ew")
        self.kpi_frame.columnconfigure(0, weight=1)
        self.kpi_frame.columnconfigure(1, weight=1)
        self.kpi_frame.columnconfigure(2, weight=1)
        self.kpi_frame.columnconfigure(3, weight=1)

        self.kpi_cards = {}
        for index, (key, title, hint) in enumerate([
            ("plan", "План всего", "Суммарный объём по выбранному срезу"),
            ("fact", "Факт всего", "Фактически выполненный объём"),
            ("completion", "Выполнение", "Процент выполнения плана"),
            ("deviation", "Отклонение", "Разница факт минус план"),
        ]):
            card = tk.Frame(self.kpi_frame, bg="#111d33", bd=0, padx=12, pady=12)
            card.grid(row=0, column=index, sticky="nsew", padx=(0, 10) if index < 3 else 0)
            tk.Label(card, text=title, fg="#94a3b8", bg="#111d33", font=("Segoe UI", 10, "bold")).pack(anchor="w")
            value = tk.Label(card, text="—", fg="#e2e8f0", bg="#111d33", font=("Arial", 32, "bold"))
            value.pack(anchor="w", pady=(6, 0))
            hint_label = tk.Label(card, text=hint, fg="#94a3b8", bg="#111d33", font=("Segoe UI", 9))
            hint_label.pack(anchor="w")
            self.kpi_cards[key] = {"card": card, "value": value, "hint": hint_label}
            # bind click to open table view
            value.bind("<Button-1>", lambda e, k=key: self._open_kpi_details(k))

        export_panel = tk.Frame(main, bg="#07111f")
        export_panel.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        tk.Label(export_panel, text="Экспорт отчёта", fg="#e5eefb", bg="#07111f", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        self.export_frame = tk.Frame(export_panel, bg="#07111f")
        self.export_frame.grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.excel_btn = ttk.Button(self.export_frame, text="📄 Excel", command=self.export_excel, style="Ghost.TButton", state="disabled", width=14)
        self.excel_btn.pack(side="left", padx=(0, 8))
        self.pdf_btn = ttk.Button(self.export_frame, text="📕 PDF", command=self.export_pdf, style="Ghost.TButton", state="disabled", width=14)
        self.pdf_btn.pack(side="left", padx=(0, 8))
        self.html_btn = ttk.Button(self.export_frame, text="🌐 HTML", command=self.export_html, style="Ghost.TButton", state="disabled", width=14)
        self.html_btn.pack(side="left")

        self.chart_frame = tk.Frame(main, bg="#0a1628", bd=0, padx=14, pady=14)
        self.chart_frame.grid(row=5, column=0, sticky="nsew", pady=(12, 0))
        self.chart_frame.columnconfigure(0, weight=1)
        self.chart_frame.rowconfigure(0, weight=1)
        self.empty_state = tk.Frame(self.chart_frame, bg="#0a1628")
        tk.Label(self.empty_state, text="📊", font=("Segoe UI", 48), fg="#94a3b8", bg="#0a1628").pack(pady=(20, 8))
        tk.Label(self.empty_state, text="Сформируйте отчёт, чтобы увидеть графики и ключевые метрики", fg="#94a3b8", bg="#0a1628", font=("Segoe UI", 11), justify="center").pack()
        self.empty_state.grid(row=0, column=0, sticky="nsew")

    def _load_data(self) -> None:
        """Загружает данные из локальных файлов и заполняет фильтры."""
        try:
            self.plans_df = load_plans(self.default_plans_path)
            self.facts_df = load_facts(self.default_facts_path)
            self._populate_filters()
        except Exception as exc:
            messagebox.showerror("Ошибка загрузки", str(exc))

    def import_documents(self) -> None:
        """Импортирует план и факт через одну зелёную кнопку."""
        paths = filedialog.askopenfilenames(
            title="Выберите файлы плана и факта",
            initialdir=str(self.default_plans_path.parent),
            filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv"), ("Все файлы", "*.*")],
        )
        if not paths:
            return

        plan_path = None
        fact_path = None
        for path in paths:
            suffix = Path(path).suffix.lower()
            if suffix == ".xlsx":
                plan_path = path
            elif suffix == ".csv":
                fact_path = path

        if plan_path is None or fact_path is None:
            messagebox.showwarning("Импорт", "Нужно выбрать оба файла: XLSX для плана и CSV для факта.")
            return

        self.plan_path_var.set(plan_path)
        self.fact_path_var.set(fact_path)
        self.load_selected_data()

    def clear_file(self, kind: str) -> None:
        """Очищает выбранный файл в sidebar."""
        if kind == "plan":
            self.plan_path_var.set("Пока не выбран")
        else:
            self.fact_path_var.set("Пока не выбран")

    def load_selected_data(self) -> None:
        """Загружает выбранные пользователем файлы."""
        try:
            plans_path = Path(self.plan_path_var.get()).expanduser().resolve()
            facts_path = Path(self.fact_path_var.get()).expanduser().resolve()
            if not plans_path.exists() or not facts_path.exists():
                raise FileNotFoundError("Выберите оба файла перед загрузкой.")

            self.plans_df = load_plans(plans_path)
            self.facts_df = load_facts(facts_path)
            self._populate_filters()
            self._render_status_chip("Данные загружены", "#14532d", "#bbf7d0")
        except Exception as exc:
            messagebox.showerror("Ошибка загрузки", str(exc))

    def generate_report(self) -> None:
        """Формирует отчёт, строит графики и активирует экспорт."""
        try:
            workshops = self._get_selected_workshops()
            start = self.start_var.get()
            end = self.end_var.get()
            product = self.product_var.get()

            if start > end:
                raise ValueError("Дата начала не может быть больше даты окончания.")

            self.metrics_df = calculate_metrics(self.plans_df, self.facts_df, workshops, start, end, product)
            if self.metrics_df.empty:
                raise ValueError("Нет данных за выбранный период")

            self._update_kpis(self.metrics_df)
            self.current_figure = build_charts(self.metrics_df)
            if self.canvas is not None:
                self.canvas.get_tk_widget().destroy()
            self.canvas = FigureCanvasTkAgg(self.current_figure, master=self.chart_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
            self.empty_state.grid_forget()

            self.excel_btn.config(state="normal")
            self.pdf_btn.config(state="normal")
            self.html_btn.config(state="normal")
        except Exception as exc:
            messagebox.showerror("Ошибка отчёта", str(exc))
            self._update_kpis(None)
            self.excel_btn.config(state="disabled")
            self.pdf_btn.config(state="disabled")
            self.html_btn.config(state="disabled")

    def _update_kpis(self, metrics_df) -> None:
        """Обновляет KPI-карточки по выбранному отчёту."""
        if metrics_df is None or metrics_df.empty:
            for card in self.kpi_cards.values():
                card["value"].config(text="—", fg="#f8fafc")
                card["hint"].config(text="Нет данных")
            self._render_status_chip("Нет данных", "#7c2d12", "#fed7aa")
            return

        plan_total = int(metrics_df["plan_qty"].sum())
        fact_total = int(metrics_df["fact_qty"].sum())
        deviation_total = int(metrics_df["deviation"].sum())
        completion = 0.0 if plan_total == 0 else round((fact_total / plan_total) * 100, 1)
        def fmt(n: int) -> str:
            return f"{n:,}".replace(",", " ")

        self.kpi_cards["plan"]["value"].config(text=fmt(plan_total), fg="#e2e8f0")
        fact_color = "#34d399" if fact_total >= plan_total else "#fbbf24"
        self.kpi_cards["fact"]["value"].config(text=fmt(fact_total), fg=fact_color)
        self.kpi_cards["completion"]["value"].config(text=f"{completion:.1f}%", fg="#a78bfa")
        dev_color = "#34d399" if deviation_total >= 0 else "#f87171"
        sign = "+" if deviation_total >= 0 else ""
        self.kpi_cards["deviation"]["value"].config(text=f"{sign}{fmt(abs(deviation_total))}", fg=dev_color)

        self.kpi_cards["plan"]["hint"].config(text="Суммарный план")
        self.kpi_cards["fact"]["hint"].config(text="Суммарный факт")
        self.kpi_cards["completion"]["hint"].config(text="% выполнения")
        self.kpi_cards["deviation"]["hint"].config(text="Факт − План")

        if completion >= 100:
            status_text = f"{completion:.1f}% — Выполнение в норме"
            bg_color = "#14532d"
            fg_color = "#bbf7d0"
        elif completion >= 90:
            status_text = f"{completion:.1f}% — Почти в норме"
            bg_color = "#f59e0b"
            fg_color = "#0b1220"
        else:
            status_text = f"{completion:.1f}% — Ниже плана"
            bg_color = "#7f1d1d"
            fg_color = "#fecaca"

        self._render_status_chip(status_text, bg_color, fg_color)

    def export_excel(self) -> None:
        """Экспортирует текущий отчёт в Excel."""
        self._export("xlsx", export_excel)

    def export_pdf(self) -> None:
        """Экспортирует текущий отчёт в PDF."""
        self._export("pdf", export_pdf)

    def export_html(self) -> None:
        """Экспортирует текущий отчёт в HTML."""
        self._export("html", export_html)

    def _export(self, ext: str, handler) -> None:
        """Общий обработчик экспорта."""
        if self.metrics_df is None or self.current_figure is None:
            messagebox.showwarning("Предупреждение", "Сначала сформируйте отчёт.")
            return

        workshop_label = "Все_цеха" if len(self._get_selected_workshops()) == len(self.workshop_vars) else "_".join(self._get_selected_workshops())
        start = self.start_var.get()
        end = self.end_var.get()
        file_name = _safe_output_name(workshop_label, start, end, ext)
        export_dir = Path(self.export_dir_var.get()).expanduser().resolve() if self.export_dir_var.get() else Path("exports")
        output_path = export_dir / file_name
        output_path.parent.mkdir(exist_ok=True)

        try:
            handler(self.metrics_df, self.current_figure, output_path)
            messagebox.showinfo("Экспорт завершён", f"Файл сохранён: {output_path.resolve()}")
        except Exception as exc:
            messagebox.showerror("Ошибка экспорта", str(exc))

    def _populate_filters(self) -> None:
        """Заполняет фильтры по загруженным данным."""
        if self.plans_df is None or self.facts_df is None:
            return

        workshops = sorted(set(self.plans_df["workshop"]).union(set(self.facts_df["workshop"])))
        months = sorted(set(self.plans_df["date"]).union(set(self.facts_df["date"])))
        products = sorted(set(self.plans_df["product"]).union(set(self.facts_df["product"])))

        # build workshop boolean vars and checkboxes
        for w in getattr(self, "workshop_vars", {}):
            # keep any existing vars
            pass
        self.workshop_vars = getattr(self, "workshop_vars", {})
        self.workshop_check_widgets = {}
        for child in self.workshop_checks_frame.winfo_children():
            child.destroy()

        for name in workshops:
            var = self.workshop_vars.get(name, tk.BooleanVar(value=True))
            self.workshop_vars[name] = var
            row = tk.Frame(self.workshop_checks_frame, bg="#0a1628")
            row.pack(fill="x", pady=2)
            cb = tk.Checkbutton(row, text=name, variable=var, onvalue=True, offvalue=False, bg="#0a1628", fg="#e2e8f0", selectcolor="#0a1628", activebackground="#0a1628", activeforeground="#e2e8f0", bd=0, anchor="w")
            cb.pack(side="left", fill="x", expand=True)
            # refresh chips when var changes
            try:
                var.trace_add("write", lambda *_: self._refresh_chips())
            except Exception:
                pass
            # indicator dot based on current data
            pct = self._workshop_completion_pct(name)
            color = "#34d399" if pct >= 100 else ("#fbbf24" if pct >= 90 else "#f87171")
            dot = tk.Canvas(row, width=12, height=12, bg="#0a1628", highlightthickness=0)
            dot.pack(side="right")
            dot.create_oval(2, 2, 10, 10, fill=color, outline=color)
            self.workshop_check_widgets[name] = (cb, dot)

        # refresh chips
        self._refresh_chips()

        self.start_combo["values"] = months
        self.end_combo["values"] = months
        self.product_combo["values"] = ["Все", *products]

        if months:
            self.start_var.set(months[0])
            self.end_var.set(months[-1])

        if products:
            self.product_var.set("Все")

    def _get_selected_workshops(self) -> list[str]:
        """Возвращает выбранные пользователем цеха."""
        selected = [name for name, var in self.workshop_vars.items() if var.get()]
        return selected or list(self.workshop_vars.keys())

    def _filter_workshops(self) -> None:
        """Фильтрует видимые чекбоксы по поисковому полю."""
        q = self.search_var.get().lower().strip()
        for name, (cb, dot) in getattr(self, "workshop_check_widgets", {}).items():
            parent = cb.master
            if q and q not in name.lower():
                parent.pack_forget()
            else:
                parent.pack(fill="x", pady=2)

    def _refresh_chips(self) -> None:
        """Обновляет отображение выбранных chips (плашек)."""
        for child in self.chips_frame.winfo_children():
            child.destroy()
        for name, var in self.workshop_vars.items():
            if var.get():
                chip = tk.Frame(self.chips_frame, bg="#3b82f6", padx=8, pady=4)
                chip.pack(side="left", padx=4)
                lbl = tk.Label(chip, text=name, bg="#3b82f6", fg="#ffffff", font=("Segoe UI", 9))
                lbl.pack(side="left")
                btn = tk.Label(chip, text="✕", bg="#3b82f6", fg="#ffffff")
                btn.pack(side="left", padx=(6, 0))
                btn.bind("<Button-1>", lambda e, n=name: (self.workshop_vars[n].set(False), self._refresh_chips()))

    def _workshop_completion_pct(self, workshop: str) -> float:
        """Возвращает приблизительный процент выполнения для превью-индикатора по цеху."""
        try:
            plan = int(self.plans_df[self.plans_df["workshop"] == workshop]["plan_qty"].sum())
            fact = int(self.facts_df[self.facts_df["workshop"] == workshop]["fact_qty"].sum())
            if plan == 0:
                return 0.0
            return round((fact / plan) * 100, 1)
        except Exception:
            return 0.0

    def _render_status_chip(self, text: str, bg: str, fg: str) -> None:
        """Рисует pill-shaped статус в canvas."""
        self.status_canvas.delete("all")
        w = int(self.status_canvas['width'])
        h = int(self.status_canvas['height'])
        r = 18
        # rounded rectangle via ovals + rect
        self.status_canvas.create_oval(0, 0, r, r, fill=bg, outline=bg)
        self.status_canvas.create_oval(w - r, 0, w, r, fill=bg, outline=bg)
        self.status_canvas.create_rectangle(r/2, 0, w - r/2, h, fill=bg, outline=bg)
        self.status_canvas.create_text(w/2, h/2, text=text, fill=fg, font=("Segoe UI", 10, "bold"))

    def _open_kpi_details(self, key: str) -> None:
        """Открывает дополнительное окно с детализацией KPI по цехам."""
        if self.metrics_df is None or self.metrics_df.empty:
            return
        top = tk.Toplevel(self)
        top.title(f"Детали: {key}")
        cols = ("workshop", "plan_qty", "fact_qty", "completion_pct", "deviation")
        tree = ttk.Treeview(top, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
        agg = self.metrics_df.groupby("workshop").agg({"plan_qty":"sum","fact_qty":"sum","completion_pct":"mean","deviation":"sum"}).reset_index()
        for _, row in agg.iterrows():
            tree.insert("", "end", values=(row["workshop"], int(row["plan_qty"]), int(row["fact_qty"]), f"{row['completion_pct']:.1f}%", int(row["deviation"])))
        tree.pack(fill="both", expand=True)

    def choose_export_dir(self) -> None:
        """Выбирает папку для экспорта."""
        path = filedialog.askdirectory(title="Выберите папку для экспорта", initialdir=str(self.default_export_dir))
        if path:
            self.export_dir_var.set(path)
