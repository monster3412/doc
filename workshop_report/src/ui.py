# === ФАЙЛ: src/ui.py ===
"""Главный интерфейс приложения на tkinter — адаптивный визуал + переключатель тем."""

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


# ── Палитры тем ──────────────────────────────────────────────────────────────
THEMES = {
    "light": {
        "bg":            "#f0f4f8",
        "surface":       "#ffffff",
        "surface2":      "#f7f9fc",
        "sidebar_bg":    "#ffffff",
        "card_bg":       "#ffffff",
        "border":        "#e2e8f0",
        "text":          "#1a202c",
        "text_muted":    "#718096",
        "accent":        "#3b5bdb",
        "accent_soft":   "#dbe4ff",
        "green":         "#2f9e44",
        "green_soft":    "#d3f9d8",
        "red":           "#c92a2a",
        "red_soft":      "#ffe3e3",
        "yellow":        "#e67700",
        "yellow_soft":   "#fff3bf",
        "chip_bg":       "#3b5bdb",
        "chip_fg":       "#ffffff",
        "btn_import_bg": "#2f9e44",
        "btn_import_fg": "#ffffff",
        "btn_ghost_bg":  "#f0f4f8",
        "btn_ghost_fg":  "#3b5bdb",
        "entry_bg":      "#f7f9fc",
        "entry_fg":      "#1a202c",
        "toggle_text":   "☀️  Светлая тема",
        "sash":          "#e2e8f0",
    },
    "dark": {
        "bg":            "#0f1117",
        "surface":       "#1a1d27",
        "surface2":      "#22263a",
        "sidebar_bg":    "#0d1b2e",
        "card_bg":       "#111d33",
        "border":        "#2d3250",
        "text":          "#e8eaf6",
        "text_muted":    "#7986cb",
        "accent":        "#748ffc",
        "accent_soft":   "#1c2260",
        "green":         "#69db7c",
        "green_soft":    "#1a3d23",
        "red":           "#ff8787",
        "red_soft":      "#3d1a1a",
        "yellow":        "#ffd43b",
        "yellow_soft":   "#3d3000",
        "chip_bg":       "#3b5bdb",
        "chip_fg":       "#ffffff",
        "btn_import_bg": "#16a34a",
        "btn_import_fg": "#f8fafc",
        "btn_ghost_bg":  "#111827",
        "btn_ghost_fg":  "#dbeafe",
        "entry_bg":      "#111d33",
        "entry_fg":      "#e2e8f0",
        "toggle_text":   "🌙  Тёмная тема",
        "sash":          "#2d3250",
    },
}

FONT_UI   = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_SM   = ("Segoe UI", 9)
FONT_SM_B = ("Segoe UI", 9, "bold")
FONT_XS   = ("Segoe UI", 8)
FONT_NUM  = ("Arial",    28, "bold")
FONT_LOGO = ("Segoe UI", 15, "bold")


def _sep(parent, T):
    """Тонкий горизонтальный разделитель."""
    f = tk.Frame(parent, height=1, bg=T["border"])
    return f


class ScrollableFrame(tk.Frame):
    """Фрейм с вертикальной прокруткой через mousewheel."""

    def __init__(self, parent, bg, **kw):
        outer = tk.Frame(parent, bg=bg)
        outer.pack(fill="both", expand=True)
        self._canvas = tk.Canvas(outer, bg=bg, highlightthickness=0, bd=0)
        self._vsb = ttk.Scrollbar(outer, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._vsb.set)
        self._vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        super().__init__(self._canvas, bg=bg, **kw)
        self._win = self._canvas.create_window((0, 0), window=self, anchor="nw")
        self.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_frame_configure(self, _):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, e):
        self._canvas.itemconfig(self._win, width=e.width)

    def _on_mousewheel(self, e):
        self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def recolor(self, bg):
        self._canvas.configure(bg=bg)
        self.configure(bg=bg)
        self._canvas.master.configure(bg=bg)


class ReportApp(tk.Tk):
    """Основное окно отчётности WorkshopReport."""

    _last_status = ("Готов к загрузке", "#2f9e44", "#d3f9d8")

    # ── Init ─────────────────────────────────────────────────────────────────
    def __init__(self) -> None:
        super().__init__()
        self.title("WorkshopReport · Производственный отчёт")
        self.geometry("1160x780")
        self.minsize(820, 600)

        self.plans_df       = None
        self.facts_df       = None
        self.metrics_df     = None
        self.current_figure = None
        self.canvas         = None

        self._theme_name = "light"
        self._T          = THEMES["light"]

        self.default_plans_path = DATA_DIR / "plans.xlsx"
        self.default_facts_path = DATA_DIR / "workshop_production_data.csv"
        self.default_export_dir = Path("exports")

        self.plan_path_var  = tk.StringVar(value=str(self.default_plans_path))
        self.fact_path_var  = tk.StringVar(value=str(self.default_facts_path))
        self.export_dir_var = tk.StringVar(value=str(self.default_export_dir))

        self.workshop_vars: dict[str, tk.BooleanVar] = {}
        self.workshop_check_widgets: dict = {}

        self._apply_ttk_theme()
        self._build_ui()
        self._repaint()
        self._load_data()

    # ── TTK стили ────────────────────────────────────────────────────────────
    def _apply_ttk_theme(self) -> None:
        T = self._T
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        s.configure("TLabel",         background=T["bg"],          foreground=T["text"],         font=FONT_UI)
        s.configure("TCombobox",      fieldbackground=T["entry_bg"], foreground=T["entry_fg"],   font=FONT_UI)
        s.configure("Accent.TButton", background=T["accent"],       foreground="#ffffff",         font=FONT_BOLD)
        s.map("Accent.TButton",       background=[("active", T["accent_soft"]), ("!disabled", T["accent"])])
        s.configure("Ghost.TButton",  background=T["btn_ghost_bg"], foreground=T["btn_ghost_fg"], font=FONT_SM_B)
        s.map("Ghost.TButton",        background=[("active", T["accent_soft"]), ("!disabled", T["btn_ghost_bg"])])
        s.configure("TPanedwindow",   background=T["sash"])
        s.configure("Sash",           sashthickness=5,              sashpad=2,                    background=T["sash"])

    # ── Build UI ─────────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        T = self._T
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # PanedWindow — перетаскиваемый разделитель между сайдбаром и главным контентом
        self.paned = tk.PanedWindow(self, orient="horizontal", sashwidth=6,
                                    sashrelief="flat", bd=0, bg=T["sash"])
        self.paned.grid(row=0, column=0, sticky="nsew")

        # ── Sidebar ──────────────────────────────────────────────────────────
        self._sb_outer = tk.Frame(self.paned, width=280)
        self.paned.add(self._sb_outer, minsize=200, sticky="nsew")
        self._sb_outer.rowconfigure(0, weight=1)
        self._sb_outer.columnconfigure(0, weight=1)

        self._sb_scroll = ScrollableFrame(self._sb_outer, bg=T["sidebar_bg"], padx=14, pady=14)
        self._sb_scroll.columnconfigure(0, weight=1)
        sidebar = self._sb_scroll   # alias

        # Logo
        self.lbl_logo = tk.Label(sidebar, text="WorkshopReport", font=FONT_LOGO)
        self.lbl_logo.grid(row=0, column=0, sticky="w")
        self.lbl_sub = tk.Label(sidebar, text="Производственный отчёт", font=FONT_XS)
        self.lbl_sub.grid(row=1, column=0, sticky="w", pady=(2, 10))

        # Theme toggle
        self.theme_btn = tk.Button(sidebar, command=self._toggle_theme,
                                   bd=0, highlightthickness=0, padx=10, pady=6,
                                   font=FONT_SM_B, relief="flat", cursor="hand2")
        self.theme_btn.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        # Import button
        self.import_btn = tk.Button(sidebar, text="⬆  Импортировать документы",
                                    command=self.import_documents,
                                    bd=0, highlightthickness=0, padx=12, pady=9,
                                    font=FONT_BOLD, relief="flat", cursor="hand2")
        self.import_btn.grid(row=3, column=0, sticky="ew")

        # File cards label
        self.lbl_files = tk.Label(sidebar, text="Текущие файлы", font=FONT_BOLD)
        self.lbl_files.grid(row=4, column=0, sticky="w", pady=(16, 6))

        # Plan card
        self.plan_box = tk.Frame(sidebar, bd=0, padx=10, pady=10)
        self.plan_box.grid(row=5, column=0, sticky="ew", pady=(0, 8))
        self.plan_box.columnconfigure(0, weight=1)
        header_row = tk.Frame(self.plan_box)
        header_row.grid(row=0, column=0, sticky="ew")
        header_row.columnconfigure(0, weight=1)
        self.plan_name_label = tk.Label(header_row, text="📊  План (XLSX)", font=FONT_SM_B)
        self.plan_name_label.grid(row=0, column=0, sticky="w")
        self._plan_clear_btn = tk.Button(header_row, text="✕",
                                         command=lambda: self.clear_file("plan"),
                                         bd=0, highlightthickness=0, relief="flat",
                                         cursor="hand2", font=FONT_SM, padx=4)
        self._plan_clear_btn.grid(row=0, column=1, sticky="e")
        self.plan_basename = tk.Label(self.plan_box, textvariable=self.plan_path_var,
                                      justify="left", wraplength=230, font=FONT_XS)
        self.plan_basename.grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.plan_status = tk.Label(self.plan_box, text="✗", font=FONT_SM_B)
        self.plan_status.grid(row=2, column=0, sticky="e", pady=(4, 0))

        # Fact card
        self.fact_box = tk.Frame(sidebar, bd=0, padx=10, pady=10)
        self.fact_box.grid(row=6, column=0, sticky="ew")
        self.fact_box.columnconfigure(0, weight=1)
        header_row2 = tk.Frame(self.fact_box)
        header_row2.grid(row=0, column=0, sticky="ew")
        header_row2.columnconfigure(0, weight=1)
        self.fact_name_label = tk.Label(header_row2, text="📋  Факт (CSV)", font=FONT_SM_B)
        self.fact_name_label.grid(row=0, column=0, sticky="w")
        self._fact_clear_btn = tk.Button(header_row2, text="✕",
                                         command=lambda: self.clear_file("fact"),
                                         bd=0, highlightthickness=0, relief="flat",
                                         cursor="hand2", font=FONT_SM, padx=4)
        self._fact_clear_btn.grid(row=0, column=1, sticky="e")
        self.fact_basename = tk.Label(self.fact_box, textvariable=self.fact_path_var,
                                      justify="left", wraplength=230, font=FONT_XS)
        self.fact_basename.grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.fact_status = tk.Label(self.fact_box, text="✗", font=FONT_SM_B)
        self.fact_status.grid(row=2, column=0, sticky="e", pady=(4, 0))

        # Export dir
        self.lbl_export_dir = tk.Label(sidebar, text="Папка экспорта", font=FONT_BOLD)
        self.lbl_export_dir.grid(row=7, column=0, sticky="w", pady=(16, 4))
        self.lbl_export_path = tk.Label(sidebar, textvariable=self.export_dir_var,
                                        justify="left", wraplength=240, font=FONT_XS)
        self.lbl_export_path.grid(row=8, column=0, sticky="w")
        self.choose_dir_btn = tk.Button(sidebar, text="📁  Выбрать папку",
                                        command=self.choose_export_dir,
                                        bd=0, highlightthickness=0, pady=6, relief="flat",
                                        cursor="hand2", font=FONT_SM)
        self.choose_dir_btn.grid(row=9, column=0, sticky="ew", pady=(4, 0))

        self.lbl_hint = tk.Label(sidebar, text="Один клик — импорт обоих файлов.",
                                 justify="left", wraplength=240, font=FONT_XS)
        self.lbl_hint.grid(row=10, column=0, sticky="w", pady=(12, 0))

        # ── Main area ────────────────────────────────────────────────────────
        self._main_outer = tk.Frame(self.paned)
        self.paned.add(self._main_outer, minsize=500, sticky="nsew")
        self._main_outer.rowconfigure(0, weight=1)
        self._main_outer.columnconfigure(0, weight=1)

        # Scrollable main canvas
        self._main_canvas = tk.Canvas(self._main_outer, highlightthickness=0, bd=0)
        self._main_vsb = ttk.Scrollbar(self._main_outer, orient="vertical",
                                        command=self._main_canvas.yview)
        self._main_canvas.configure(yscrollcommand=self._main_vsb.set)
        self._main_vsb.grid(row=0, column=1, sticky="ns")
        self._main_canvas.grid(row=0, column=0, sticky="nsew")
        self._main_outer.rowconfigure(0, weight=1)
        self._main_outer.columnconfigure(0, weight=1)

        main = tk.Frame(self._main_canvas, padx=18, pady=16)
        main.columnconfigure(0, weight=1)
        self._main_frame = main
        self._main_win = self._main_canvas.create_window((0, 0), window=main, anchor="nw")

        main.bind("<Configure>", self._on_main_configure)
        self._main_canvas.bind("<Configure>", self._on_main_canvas_configure)
        self._main_canvas.bind_all("<MouseWheel>", self._on_main_mousewheel)

        # Header
        self.header_frame = tk.Frame(main, padx=14, pady=12)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.columnconfigure(0, weight=1)
        self.lbl_title = tk.Label(self.header_frame, text="Отчёт по цехам", font=("Segoe UI", 18, "bold"))
        self.lbl_title.grid(row=0, column=0, sticky="w")
        self.lbl_subtitle = tk.Label(self.header_frame, text="Выберите срез данных и сформируйте отчёт", font=FONT_SM)
        self.lbl_subtitle.grid(row=1, column=0, sticky="w", pady=(2, 0))
        self.status_canvas = tk.Canvas(self.header_frame, width=220, height=36, highlightthickness=0)
        self.status_canvas.grid(row=0, column=1, rowspan=2, sticky="e", padx=(10, 0))

        # Sep
        self._sep1 = tk.Frame(main, height=1)
        self._sep1.grid(row=1, column=0, sticky="ew", pady=(2, 10))

        # ── Filter card ──────────────────────────────────────────────────────
        self.filter_card = tk.Frame(main, padx=14, pady=12)
        self.filter_card.grid(row=2, column=0, sticky="ew")
        self.filter_card.columnconfigure(0, weight=1)

        self.lbl_workshops = tk.Label(self.filter_card, text="Цеха", font=FONT_BOLD)
        self.lbl_workshops.grid(row=0, column=0, sticky="w")

        self.workshop_selector = tk.Frame(self.filter_card)
        self.workshop_selector.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self.workshop_selector.columnconfigure(0, weight=1)

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(self.workshop_selector, textvariable=self.search_var,
                                     font=FONT_UI, bd=0, highlightthickness=1, relief="flat")
        self.search_entry.grid(row=0, column=0, sticky="ew", ipady=5, padx=1)
        self.search_var.trace_add("write", lambda *_: self._filter_workshops())

        # Chips row — wrap-friendly via pack inside a frame
        self.chips_frame = tk.Frame(self.workshop_selector)
        self.chips_frame.grid(row=1, column=0, sticky="ew", pady=(8, 4))

        # Checkboxes in a 2-column grid for space efficiency
        self.workshop_checks_frame = tk.Frame(self.workshop_selector)
        self.workshop_checks_frame.grid(row=2, column=0, sticky="ew")
        self.workshop_checks_frame.columnconfigure(0, weight=1)
        self.workshop_checks_frame.columnconfigure(1, weight=1)

        # ── Period + generate row (wraps on resize) ──────────────────────────
        self._sep_f = tk.Frame(main, height=1)
        self._sep_f.grid(row=3, column=0, sticky="ew", pady=(10, 10))

        self.controls_frame = tk.Frame(main)
        self.controls_frame.grid(row=4, column=0, sticky="ew")
        self.controls_frame.columnconfigure(1, weight=0)
        self.controls_frame.columnconfigure(3, weight=0)
        self.controls_frame.columnconfigure(5, weight=0)
        self.controls_frame.columnconfigure(6, weight=1)

        self.lbl_from = tk.Label(self.controls_frame, text="С", font=FONT_BOLD)
        self.lbl_from.grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.start_var = tk.StringVar(value="2025-01")
        self.start_combo = ttk.Combobox(self.controls_frame, textvariable=self.start_var,
                                        state="readonly", width=10, font=FONT_UI)
        self.start_combo.grid(row=0, column=1, sticky="w", padx=(0, 8))

        self.lbl_to = tk.Label(self.controls_frame, text="по", font=FONT_BOLD)
        self.lbl_to.grid(row=0, column=2, sticky="w", padx=(0, 6))
        self.end_var = tk.StringVar(value="2025-12")
        self.end_combo = ttk.Combobox(self.controls_frame, textvariable=self.end_var,
                                      state="readonly", width=10, font=FONT_UI)
        self.end_combo.grid(row=0, column=3, sticky="w", padx=(0, 8))

        self.lbl_product = tk.Label(self.controls_frame, text="Продукция", font=FONT_BOLD)
        self.lbl_product.grid(row=0, column=4, sticky="w", padx=(0, 6))
        self.product_var = tk.StringVar(value="Все")
        self.product_combo = ttk.Combobox(self.controls_frame, textvariable=self.product_var,
                                          state="readonly", width=16, font=FONT_UI)
        self.product_combo.grid(row=0, column=5, sticky="w", padx=(0, 10))

        self.generate_btn = ttk.Button(self.controls_frame, text="▶  Сформировать отчёт",
                                       command=self.generate_report,
                                       style="Accent.TButton", width=22)
        self.generate_btn.grid(row=0, column=6, sticky="e")

        # ── Sep ──────────────────────────────────────────────────────────────
        self._sep2 = tk.Frame(main, height=1)
        self._sep2.grid(row=5, column=0, sticky="ew", pady=(12, 10))

        # ── KPI cards — adaptive grid ─────────────────────────────────────────
        self.kpi_frame = tk.Frame(main)
        self.kpi_frame.grid(row=6, column=0, sticky="ew")
        for i in range(4):
            self.kpi_frame.columnconfigure(i, weight=1)

        self.kpi_cards: dict = {}
        kpi_defs = [
            ("plan",       "📦  План",      "Суммарный план"),
            ("fact",       "✅  Факт",       "Суммарный факт"),
            ("completion", "📈  Выполнение", "% выполнения"),
            ("deviation",  "↔  Отклонение", "Факт − план"),
        ]
        for idx, (key, title, hint) in enumerate(kpi_defs):
            pad_r = (0, 8) if idx < 3 else (0, 0)
            card = tk.Frame(self.kpi_frame, bd=0, padx=12, pady=10)
            card.grid(row=0, column=idx, sticky="nsew", padx=pad_r)
            lbl_t = tk.Label(card, text=title, font=FONT_SM_B)
            lbl_t.pack(anchor="w")
            value = tk.Label(card, text="—", font=FONT_NUM)
            value.pack(anchor="w", pady=(4, 0))
            hint_lbl = tk.Label(card, text=hint, font=FONT_XS)
            hint_lbl.pack(anchor="w", pady=(2, 0))
            value.bind("<Button-1>", lambda e, k=key: self._open_kpi_details(k))
            value.config(cursor="hand2")
            self.kpi_cards[key] = {"card": card, "value": value, "hint": hint_lbl, "title_lbl": lbl_t}

        # ── Export panel ──────────────────────────────────────────────────────
        self._sep3 = tk.Frame(main, height=1)
        self._sep3.grid(row=7, column=0, sticky="ew", pady=(12, 10))

        export_panel = tk.Frame(main)
        export_panel.grid(row=8, column=0, sticky="ew")
        self.lbl_export = tk.Label(export_panel, text="Экспорт отчёта", font=FONT_BOLD)
        self.lbl_export.pack(anchor="w")
        self.export_frame = tk.Frame(export_panel)
        self.export_frame.pack(anchor="w", pady=(6, 0))
        self.excel_btn = ttk.Button(self.export_frame, text="📄  Excel", command=self.export_excel,
                                    style="Ghost.TButton", state="disabled", width=12)
        self.excel_btn.pack(side="left", padx=(0, 8))
        self.pdf_btn = ttk.Button(self.export_frame, text="📕  PDF", command=self.export_pdf,
                                   style="Ghost.TButton", state="disabled", width=12)
        self.pdf_btn.pack(side="left", padx=(0, 8))
        self.html_btn = ttk.Button(self.export_frame, text="🌐  HTML", command=self.export_html,
                                    style="Ghost.TButton", state="disabled", width=12)
        self.html_btn.pack(side="left")

        # ── Chart frame ───────────────────────────────────────────────────────
        self.chart_frame = tk.Frame(main, bd=0, padx=12, pady=12)
        self.chart_frame.grid(row=9, column=0, sticky="nsew", pady=(12, 0))
        self.chart_frame.columnconfigure(0, weight=1)
        self.chart_frame.rowconfigure(0, weight=1)
        main.rowconfigure(9, weight=1)

        self.empty_state = tk.Frame(self.chart_frame)
        self.empty_state.grid(row=0, column=0, sticky="nsew")
        tk.Label(self.empty_state, text="📊", font=("Segoe UI", 40)).pack(pady=(28, 8))
        tk.Label(self.empty_state, text="Сформируйте отчёт,\nчтобы увидеть графики и метрики",
                 font=FONT_UI, justify="center").pack()

    # ── Responsive canvas callbacks ───────────────────────────────────────────
    def _on_main_configure(self, _):
        self._main_canvas.configure(scrollregion=self._main_canvas.bbox("all"))

    def _on_main_canvas_configure(self, e):
        self._main_canvas.itemconfig(self._main_win, width=e.width)

    def _on_main_mousewheel(self, e):
        self._main_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    # ── Repaint ───────────────────────────────────────────────────────────────
    def _repaint(self) -> None:
        T = self._T
        self.configure(bg=T["bg"])
        self.paned.configure(bg=T["sash"])
        self._sb_outer.configure(bg=T["sidebar_bg"])
        self._sb_scroll.recolor(T["sidebar_bg"])

        # Sidebar widgets
        for w in (self.lbl_logo, self.lbl_sub, self.lbl_files, self.lbl_hint,
                  self.lbl_export_dir, self.lbl_export_path):
            w.configure(bg=T["sidebar_bg"])
        self.lbl_logo.configure(fg=T["text"])
        self.lbl_sub.configure(fg=T["text_muted"])
        self.lbl_files.configure(fg=T["text"])
        self.lbl_hint.configure(fg=T["text_muted"])
        self.lbl_export_dir.configure(fg=T["text"])
        self.lbl_export_path.configure(fg=T["text_muted"])

        self.theme_btn.configure(
            bg=T["btn_ghost_bg"], fg=T["accent"],
            text=T["toggle_text"],
            activebackground=T["accent_soft"],
        )
        self.import_btn.configure(
            bg=T["btn_import_bg"], fg=T["btn_import_fg"],
            activebackground=T["green"],
        )
        self.choose_dir_btn.configure(bg=T["surface2"] if T == THEMES["light"] else T["card_bg"],
                                      fg=T["text_muted"],
                                      activebackground=T["border"])

        # File cards
        for box, nl, bl, st, cb in (
            (self.plan_box, self.plan_name_label, self.plan_basename, self.plan_status, self._plan_clear_btn),
            (self.fact_box, self.fact_name_label, self.fact_basename, self.fact_status, self._fact_clear_btn),
        ):
            box.configure(bg=T["card_bg"])
            for child in box.winfo_children():
                try:
                    child.configure(bg=T["card_bg"])
                except Exception:
                    pass
            nl.configure(bg=T["card_bg"], fg=T["accent"])
            bl.configure(bg=T["card_bg"], fg=T["text_muted"])
            st.configure(bg=T["card_bg"], fg=T["red"])
            cb.configure(bg=T["card_bg"], fg=T["text_muted"], activebackground=T["card_bg"])
            # header row inside card
            cb.master.configure(bg=T["card_bg"])

        # Main scroll area
        self._main_canvas.configure(bg=T["bg"])
        self._main_frame.configure(bg=T["bg"])

        self.header_frame.configure(bg=T["surface"])
        self.status_canvas.configure(bg=T["surface"])
        self.lbl_title.configure(bg=T["surface"], fg=T["text"])
        self.lbl_subtitle.configure(bg=T["surface"], fg=T["text_muted"])

        for sep in (self._sep1, self._sep_f, self._sep2, self._sep3):
            sep.configure(bg=T["border"])

        self.filter_card.configure(bg=T["surface"])
        self.lbl_workshops.configure(bg=T["surface"], fg=T["text"])
        self.workshop_selector.configure(bg=T["surface"])
        self.chips_frame.configure(bg=T["surface"])
        self.workshop_checks_frame.configure(bg=T["surface"])
        self.search_entry.configure(
            bg=T["entry_bg"], fg=T["entry_fg"],
            insertbackground=T["entry_fg"],
            highlightcolor=T["accent"], highlightbackground=T["border"],
        )

        cf = self.controls_frame
        cf.configure(bg=T["bg"])
        for lbl in (self.lbl_from, self.lbl_to, self.lbl_product):
            lbl.configure(bg=T["bg"], fg=T["text"])

        self.kpi_frame.configure(bg=T["bg"])
        for d in self.kpi_cards.values():
            d["card"].configure(bg=T["card_bg"])
            d["title_lbl"].configure(bg=T["card_bg"], fg=T["text_muted"])
            d["value"].configure(bg=T["card_bg"])
            d["hint"].configure(bg=T["card_bg"], fg=T["text_muted"])

        ep = self.lbl_export.master
        ep.configure(bg=T["bg"])
        self.export_frame.configure(bg=T["bg"])
        self.lbl_export.configure(bg=T["bg"], fg=T["text"])

        for sep in (self._sep3,):
            sep.configure(bg=T["border"])

        self.chart_frame.configure(bg=T["surface"])
        self.empty_state.configure(bg=T["surface"])
        for child in self.empty_state.winfo_children():
            try:
                child.configure(bg=T["surface"], fg=T["text_muted"])
            except Exception:
                pass

        # Workshop checkboxes
        for name, (cb, dot) in self.workshop_check_widgets.items():
            cb.configure(bg=T["surface"], fg=T["text"],
                         selectcolor=T["surface"],
                         activebackground=T["surface"], activeforeground=T["text"])
            cb.master.configure(bg=T["surface"])
            dot.configure(bg=T["surface"])

        self._refresh_chips()
        self._render_status_chip(*self._last_status)
        self._apply_ttk_theme()

    # ── Theme toggle ──────────────────────────────────────────────────────────
    def _toggle_theme(self) -> None:
        self._theme_name = "dark" if self._theme_name == "light" else "light"
        self._T = THEMES[self._theme_name]
        self._repaint()

    # ── Status chip ───────────────────────────────────────────────────────────
    def _render_status_chip(self, text: str, bg: str, fg: str) -> None:
        self._last_status = (text, bg, fg)
        c = self.status_canvas
        c.delete("all")
        w, h, r = int(c["width"]), int(c["height"]), 14
        c.create_oval(0, 0, r*2, h, fill=bg, outline=bg)
        c.create_oval(w-r*2, 0, w, h, fill=bg, outline=bg)
        c.create_rectangle(r, 0, w-r, h, fill=bg, outline=bg)
        c.create_text(w/2, h/2, text=text, fill=fg, font=FONT_SM_B)

    # ── Data loading ──────────────────────────────────────────────────────────
    def _load_data(self) -> None:
        try:
            self.plans_df = load_plans(self.default_plans_path)
            self.facts_df = load_facts(self.default_facts_path)
            self._populate_filters()
        except Exception as exc:
            messagebox.showerror("Ошибка загрузки", str(exc))

    def import_documents(self) -> None:
        plan_path = filedialog.askopenfilename(
            title="Выберите файл плана (.xlsx)",
            initialdir=str(self.default_plans_path.parent),
            filetypes=[("Excel", "*.xlsx"), ("Все файлы", "*.*")],
        )
        if not plan_path:
            return
        fact_path = filedialog.askopenfilename(
            title="Выберите файл факта (.csv)",
            initialdir=str(self.default_facts_path.parent),
            filetypes=[("CSV", "*.csv"), ("Все файлы", "*.*")],
        )
        if not fact_path:
            return
        self.plan_path_var.set(plan_path)
        self.fact_path_var.set(fact_path)
        self.load_selected_data()

    def clear_file(self, kind: str) -> None:
        if kind == "plan":
            self.plan_path_var.set("")
        else:
            self.fact_path_var.set("")
        self._render_status_chip("Файлы не выбраны", "#c92a2a", "#ffe3e3")
        self.plans_df = self.facts_df = self.metrics_df = self.current_figure = None
        self._update_kpis(None)
        for btn in (self.excel_btn, self.pdf_btn, self.html_btn):
            btn.config(state="disabled")
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        self.empty_state.grid(row=0, column=0, sticky="nsew")

    def load_selected_data(self) -> None:
        try:
            plans_path = Path(self.plan_path_var.get()).expanduser().resolve()
            facts_path = Path(self.fact_path_var.get()).expanduser().resolve()
            if not plans_path.exists() or not facts_path.exists():
                raise FileNotFoundError("Выберите оба файла перед загрузкой.")
            self.plans_df = load_plans(plans_path)
            self.facts_df = load_facts(facts_path)
            self._populate_filters()
            self._render_status_chip("Данные загружены ✓", "#2f9e44", "#d3f9d8")
            self.plan_status.configure(text="✓", fg=self._T["green"])
            self.fact_status.configure(text="✓", fg=self._T["green"])
        except Exception as exc:
            messagebox.showerror("Ошибка загрузки", str(exc))

    # ── Generate report ───────────────────────────────────────────────────────
    def generate_report(self) -> None:
        try:
            workshops = self._get_selected_workshops()
            start, end = self.start_var.get(), self.end_var.get()
            product   = self.product_var.get()
            if start > end:
                raise ValueError("Дата начала не может быть позже даты окончания.")
            self.metrics_df = calculate_metrics(self.plans_df, self.facts_df, workshops, start, end, product)
            if self.metrics_df.empty:
                raise ValueError("Нет данных за выбранный период.")
            self._update_kpis(self.metrics_df)
            self.current_figure = build_charts(self.metrics_df)
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
            self.canvas = FigureCanvasTkAgg(self.current_figure, master=self.chart_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
            self.empty_state.grid_forget()
            for btn in (self.excel_btn, self.pdf_btn, self.html_btn):
                btn.config(state="normal")
        except Exception as exc:
            messagebox.showerror("Ошибка отчёта", str(exc))
            self._update_kpis(None)
            for btn in (self.excel_btn, self.pdf_btn, self.html_btn):
                btn.config(state="disabled")

    # ── KPI ───────────────────────────────────────────────────────────────────
    def _update_kpis(self, metrics_df) -> None:
        T = self._T
        if metrics_df is None or metrics_df.empty:
            for card in self.kpi_cards.values():
                card["value"].config(text="—", fg=T["text"])
                card["hint"].config(text="Нет данных")
            self._render_status_chip("Нет данных", "#c92a2a", "#ffe3e3")
            return

        plan_total = int(metrics_df["plan_qty"].sum())
        fact_total = int(metrics_df["fact_qty"].sum())
        dev_total  = int(metrics_df["deviation"].sum())
        completion = 0.0 if plan_total == 0 else round(fact_total / plan_total * 100, 1)

        def fmt(n: int) -> str:
            return f"{n:,}".replace(",", "\u2009")

        self.kpi_cards["plan"]["value"].config(text=fmt(plan_total), fg=T["accent"])
        fact_col = T["green"] if fact_total >= plan_total else T["yellow"]
        self.kpi_cards["fact"]["value"].config(text=fmt(fact_total), fg=fact_col)
        pct_col = T["green"] if completion >= 100 else (T["yellow"] if completion >= 90 else T["red"])
        self.kpi_cards["completion"]["value"].config(text=f"{completion:.1f}%", fg=pct_col)
        dev_col = T["green"] if dev_total >= 0 else T["red"]
        sign = "+" if dev_total >= 0 else ""
        self.kpi_cards["deviation"]["value"].config(text=f"{sign}{fmt(abs(dev_total))}", fg=dev_col)
        for key in ("plan", "fact", "completion", "deviation"):
            self.kpi_cards[key]["hint"].config(text={
                "plan": "Суммарный план", "fact": "Суммарный факт",
                "completion": "% выполнения", "deviation": "Факт − план",
            }[key])

        if completion >= 100:
            self._render_status_chip(f"{completion:.1f}% — план выполнен", "#2f9e44", "#d3f9d8")
        elif completion >= 90:
            self._render_status_chip(f"{completion:.1f}% — почти выполнен", "#e67700", "#fff3bf")
        else:
            self._render_status_chip(f"{completion:.1f}% — ниже плана", "#c92a2a", "#ffe3e3")

    # ── Export ────────────────────────────────────────────────────────────────
    def export_excel(self) -> None:
        self._export("xlsx", export_excel)

    def export_pdf(self) -> None:
        self._export("pdf", export_pdf)

    def export_html(self) -> None:
        self._export("html", export_html)

    def _export(self, ext: str, handler) -> None:
        if self.metrics_df is None or self.current_figure is None:
            messagebox.showwarning("Предупреждение", "Сначала сформируйте отчёт.")
            return
        ws_label = ("Все_цеха" if len(self._get_selected_workshops()) == len(self.workshop_vars)
                    else "_".join(self._get_selected_workshops()))
        file_name   = _safe_output_name(ws_label, self.start_var.get(), self.end_var.get(), ext)
        export_dir  = Path(self.export_dir_var.get() or "exports").expanduser().resolve()
        output_path = export_dir / file_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            handler(self.metrics_df, self.current_figure, output_path)
            messagebox.showinfo("Экспорт завершён", f"Файл сохранён:\n{output_path.resolve()}")
        except Exception as exc:
            messagebox.showerror("Ошибка экспорта", str(exc))

    # ── Filters ───────────────────────────────────────────────────────────────
    def _populate_filters(self) -> None:
        if self.plans_df is None or self.facts_df is None:
            return
        T = self._T
        workshops = sorted(set(self.plans_df["workshop"]).union(self.facts_df["workshop"]))
        months    = sorted(set(self.plans_df["date"]).union(self.facts_df["date"]))
        products  = sorted(set(self.plans_df["product"]).union(self.facts_df["product"]))

        self.workshop_check_widgets = {}
        for child in self.workshop_checks_frame.winfo_children():
            child.destroy()

        # 2-column grid for checkboxes
        for idx, name in enumerate(workshops):
            var = self.workshop_vars.get(name, tk.BooleanVar(value=True))
            self.workshop_vars[name] = var
            col = idx % 2
            row_idx = idx // 2
            row_f = tk.Frame(self.workshop_checks_frame, bg=T["surface"])
            row_f.grid(row=row_idx, column=col, sticky="ew", padx=(0, 4) if col == 0 else 0, pady=2)
            cb = tk.Checkbutton(row_f, text=name, variable=var, onvalue=True, offvalue=False,
                                bg=T["surface"], fg=T["text"], selectcolor=T["surface"],
                                activebackground=T["surface"], activeforeground=T["text"],
                                bd=0, anchor="w", font=FONT_SM)
            cb.pack(side="left", fill="x", expand=True)
            try:
                var.trace_add("write", lambda *_: self._refresh_chips())
            except Exception:
                pass
            pct   = self._workshop_completion_pct(name)
            color = T["green"] if pct >= 100 else (T["yellow"] if pct >= 90 else T["red"])
            dot = tk.Canvas(row_f, width=10, height=10, bg=T["surface"], highlightthickness=0)
            dot.pack(side="right", padx=4)
            dot.create_oval(1, 1, 9, 9, fill=color, outline=color)
            self.workshop_check_widgets[name] = (cb, dot)

        self._refresh_chips()

        self.start_combo["values"] = months
        self.end_combo["values"]   = months
        self.product_combo["values"] = ["Все", *products]
        if months:
            self.start_var.set(months[0])
            self.end_var.set(months[-1])
        self.product_var.set("Все")

    def _get_selected_workshops(self) -> list[str]:
        selected = [n for n, v in self.workshop_vars.items() if v.get()]
        return selected or list(self.workshop_vars.keys())

    def _filter_workshops(self) -> None:
        q = self.search_var.get().lower().strip()
        for name, (cb, dot) in self.workshop_check_widgets.items():
            parent = cb.master
            if q and q not in name.lower():
                parent.grid_remove()
            else:
                parent.grid()

    def _refresh_chips(self) -> None:
        T = self._T
        for child in self.chips_frame.winfo_children():
            child.destroy()
        self.chips_frame.configure(bg=T["surface"])
        for name, var in self.workshop_vars.items():
            if var.get():
                chip = tk.Frame(self.chips_frame, bg=T["chip_bg"], padx=6, pady=3)
                chip.pack(side="left", padx=(0, 5), pady=2)
                tk.Label(chip, text=name, bg=T["chip_bg"], fg=T["chip_fg"], font=FONT_SM_B).pack(side="left")
                x = tk.Label(chip, text=" ✕", bg=T["chip_bg"], fg=T["chip_fg"], font=FONT_SM, cursor="hand2")
                x.pack(side="left")
                x.bind("<Button-1>", lambda e, n=name: (self.workshop_vars[n].set(False), self._refresh_chips()))

    def _workshop_completion_pct(self, workshop: str) -> float:
        try:
            plan = int(self.plans_df[self.plans_df["workshop"] == workshop]["plan_qty"].sum())
            fact = int(self.facts_df[self.facts_df["workshop"] == workshop]["fact_qty"].sum())
            return 0.0 if plan == 0 else round(fact / plan * 100, 1)
        except Exception:
            return 0.0

    def _open_kpi_details(self, key: str) -> None:
        if self.metrics_df is None or self.metrics_df.empty:
            return
        T = self._T
        top = tk.Toplevel(self)
        top.title(f"Детали — {key}")
        top.configure(bg=T["bg"])
        top.geometry("560x360")
        top.minsize(400, 260)
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)

        style = ttk.Style(top)
        style.configure("Details.Treeview",
                         background=T["surface"], foreground=T["text"],
                         fieldbackground=T["surface"], rowheight=26, font=FONT_SM)
        style.configure("Details.Treeview.Heading",
                         background=T["surface2"] if self._theme_name == "light" else T["card_bg"],
                         foreground=T["text_muted"], font=FONT_SM_B)

        frame = tk.Frame(top, bg=T["bg"])
        frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        cols = ("workshop", "plan_qty", "fact_qty", "completion_pct", "deviation")
        heads = {"workshop": "Цех", "plan_qty": "План", "fact_qty": "Факт",
                 "completion_pct": "Выполнение", "deviation": "Отклонение"}
        tree = ttk.Treeview(frame, columns=cols, show="headings", style="Details.Treeview")
        for c in cols:
            tree.heading(c, text=heads[c])
            tree.column(c, width=100, anchor="center", stretch=True)
        tree.column("workshop", width=130, anchor="w", stretch=True)

        agg = (self.metrics_df.groupby("workshop")
               .agg({"plan_qty": "sum", "fact_qty": "sum",
                     "completion_pct": "mean", "deviation": "sum"})
               .reset_index())
        for _, row in agg.iterrows():
            tree.insert("", "end", values=(
                row["workshop"], int(row["plan_qty"]), int(row["fact_qty"]),
                f"{row['completion_pct']:.1f}%", int(row["deviation"]),
            ))

        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

    def choose_export_dir(self) -> None:
        path = filedialog.askdirectory(title="Выберите папку для экспорта",
                                       initialdir=str(self.default_export_dir))
        if path:
            self.export_dir_var.set(path)
