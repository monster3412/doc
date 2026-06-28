# === ФАЙЛ: src/ui.py ===
"""
WorkshopReport 
"""

import csv
import io
import json
import os
import re
import webbrowser
import tempfile
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import tkinter as tk
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.gridspec as gridspec

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


# ══════════════════════════════════════════════════════════════════════════════
#  ЦВЕТА / ТЕМЫ
# ══════════════════════════════════════════════════════════════════════════════

THEMES = {
    "light": {
        "bg":           "#f0f4f8",
        "surface":      "#ffffff",
        "surface2":     "#f7f9fc",
        "sidebar_bg":   "#ffffff",
        "card_bg":      "#ffffff",
        "border":       "#e2e8f0",
        "text":         "#1a202c",
        "muted":        "#718096",
        "accent":       "#3b5bdb",
        "accent_soft":  "#dbe4ff",
        "green":        "#2f9e44",
        "green_soft":   "#d3f9d8",
        "red":          "#c92a2a",
        "red_soft":     "#ffe3e3",
        "yellow":       "#e67700",
        "yellow_soft":  "#fff3bf",
        "chip_bg":      "#3b5bdb",
        "chip_fg":      "#ffffff",
        "import_bg":    "#2f9e44",
        "import_fg":    "#ffffff",
        "ghost_bg":     "#f0f4f8",
        "ghost_fg":     "#3b5bdb",
        "entry_bg":     "#f7f9fc",
        "entry_fg":     "#1a202c",
        "sash":         "#e2e8f0",
        "toggle_text":  "☀️  Светлая тема",
        # matplotlib
        "mpl_bg":       "#ffffff",
        "mpl_axes":     "#f7f9fc",
        "mpl_grid":     "#e2e8f0",
        "mpl_text":     "#1a202c",
        "mpl_tick":     "#718096",
    },
    "dark": {
        "bg":           "#0f1117",
        "surface":      "#1a1d27",
        "surface2":     "#22263a",
        "sidebar_bg":   "#0d1b2e",
        "card_bg":      "#111d33",
        "border":       "#2d3250",
        "text":         "#e8eaf6",
        "muted":        "#7986cb",
        "accent":       "#748ffc",
        "accent_soft":  "#1c2260",
        "green":        "#69db7c",
        "green_soft":   "#1a3d23",
        "red":          "#ff8787",
        "red_soft":     "#3d1a1a",
        "yellow":       "#ffd43b",
        "yellow_soft":  "#3d3000",
        "chip_bg":      "#3b5bdb",
        "chip_fg":      "#ffffff",
        "import_bg":    "#16a34a",
        "import_fg":    "#f8fafc",
        "ghost_bg":     "#111827",
        "ghost_fg":     "#dbeafe",
        "entry_bg":     "#111d33",
        "entry_fg":     "#e2e8f0",
        "sash":         "#2d3250",
        "toggle_text":  "🌙  Тёмная тема",
        "mpl_bg":       "#1a1d27",
        "mpl_axes":     "#22263a",
        "mpl_grid":     "#2d3250",
        "mpl_text":     "#e8eaf6",
        "mpl_tick":     "#7986cb",
    },
}

PALETTE = ["#3b5bdb","#2f9e44","#e67700","#c92a2a","#7950f2",
           "#1098ad","#f59f00","#d6336c","#099268","#c92a2a"]

FONT_LOGO = ("Segoe UI", 15, "bold")
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_UI   = ("Segoe UI", 10)
FONT_SM   = ("Segoe UI", 9)
FONT_SM_B = ("Segoe UI", 9, "bold")
FONT_XS   = ("Segoe UI", 8)
FONT_NUM  = ("Arial",    26, "bold")


# ══════════════════════════════════════════════════════════════════════════════
#  ВСТРОЕННЫЙ ДАТАСЕТ
# ══════════════════════════════════════════════════════════════════════════════

BUILTIN: list[list] = [
    ["Цех 1","2025-01","Деталь А",103,111,51.5,55.5,5.15,5.55],
    ["Цех 1","2025-01","Узел Б",93,118,46.5,59.0,4.65,5.9],
    ["Цех 1","2025-01","Корпус В",105,105,52.5,52.5,5.25,5.25],
    ["Цех 1","2025-02","Деталь А",97,80,48.5,40.0,4.85,4.0],
    ["Цех 1","2025-02","Узел Б",92,121,46.0,60.5,4.6,6.05],
    ["Цех 1","2025-02","Корпус В",105,87,52.5,43.5,5.25,4.35],
    ["Цех 1","2025-03","Деталь А",112,82,56.0,41.0,5.6,4.1],
    ["Цех 1","2025-03","Узел Б",89,107,44.5,53.5,4.45,5.35],
    ["Цех 1","2025-03","Корпус В",86,106,43.0,53.0,4.3,5.3],
    ["Цех 1","2025-04","Деталь А",104,114,52.0,57.0,5.2,5.7],
    ["Цех 1","2025-04","Узел Б",81,106,40.5,53.0,4.05,5.3],
    ["Цех 1","2025-04","Корпус В",114,101,57.0,50.5,5.7,5.05],
    ["Цех 1","2025-05","Деталь А",90,86,45.0,43.0,4.5,4.3],
    ["Цех 1","2025-05","Узел Б",94,87,47.0,43.5,4.7,4.35],
    ["Цех 1","2025-05","Корпус В",117,98,58.5,49.0,5.85,4.9],
    ["Цех 1","2025-06","Деталь А",109,96,54.5,48.0,5.45,4.8],
    ["Цех 1","2025-06","Узел Б",119,77,59.5,38.5,5.95,3.85],
    ["Цех 1","2025-06","Корпус В",91,105,45.5,52.5,4.55,5.25],
    ["Цех 1","2025-07","Деталь А",107,111,53.5,55.5,5.35,5.55],
    ["Цех 1","2025-07","Узел Б",98,89,49.0,44.5,4.9,4.45],
    ["Цех 1","2025-07","Корпус В",111,0,55.5,0.0,5.55,0.0],
    ["Цех 1","2025-08","Деталь А",83,91,41.5,45.5,4.15,4.55],
    ["Цех 1","2025-08","Узел Б",86,86,43.0,43.0,4.3,4.3],
    ["Цех 1","2025-08","Корпус В",117,85,58.5,42.5,5.85,4.25],
    ["Цех 1","2025-09","Деталь А",86,105,43.0,52.5,4.3,5.25],
    ["Цех 1","2025-09","Узел Б",80,128,40.0,64.0,4.0,6.4],
    ["Цех 1","2025-09","Корпус В",118,113,59.0,56.5,5.9,5.65],
    ["Цех 1","2025-10","Деталь А",102,97,51.0,48.5,5.1,4.85],
    ["Цех 1","2025-10","Узел Б",105,100,52.5,50.0,5.25,5.0],
    ["Цех 1","2025-10","Корпус В",93,107,46.5,53.5,4.65,5.35],
    ["Цех 1","2025-11","Деталь А",89,92,44.5,46.0,4.45,4.6],
    ["Цех 1","2025-11","Узел Б",109,95,54.5,47.5,5.45,4.75],
    ["Цех 1","2025-11","Корпус В",118,116,59.0,58.0,5.9,5.8],
    ["Цех 1","2025-12","Деталь А",103,107,51.5,53.5,5.15,5.35],
    ["Цех 1","2025-12","Узел Б",110,91,55.0,45.5,5.5,4.55],
    ["Цех 1","2025-12","Корпус В",111,110,55.5,55.0,5.55,5.5],
    ["Цех 2","2025-01","Деталь А",95,92,47.5,46.0,4.75,4.6],
    ["Цех 2","2025-01","Узел Б",90,0,45.0,0.0,4.5,0.0],
    ["Цех 2","2025-01","Корпус В",82,89,41.0,44.5,4.1,4.45],
    ["Цех 2","2025-02","Деталь А",86,82,43.0,41.0,4.3,4.1],
    ["Цех 2","2025-02","Узел Б",104,77,52.0,38.5,5.2,3.85],
    ["Цех 2","2025-02","Корпус В",105,0,52.5,0.0,5.25,0.0],
    ["Цех 2","2025-03","Деталь А",89,85,44.5,42.5,4.45,4.25],
    ["Цех 2","2025-03","Узел Б",84,87,42.0,43.5,4.2,4.35],
    ["Цех 2","2025-03","Корпус В",108,111,54.0,55.5,5.4,5.55],
    ["Цех 2","2025-04","Деталь А",98,0,49.0,0.0,4.9,0.0],
    ["Цех 2","2025-04","Узел Б",81,89,40.5,44.5,4.05,4.45],
    ["Цех 2","2025-04","Корпус В",99,109,49.5,54.5,4.95,5.45],
    ["Цех 2","2025-05","Деталь А",106,87,53.0,43.5,5.3,4.35],
    ["Цех 2","2025-05","Узел Б",92,116,46.0,58.0,4.6,5.8],
    ["Цех 2","2025-05","Корпус В",82,104,41.0,52.0,4.1,5.2],
    ["Цех 2","2025-06","Деталь А",102,105,51.0,52.5,5.1,5.25],
    ["Цех 2","2025-06","Узел Б",113,88,56.5,44.0,5.65,4.4],
    ["Цех 2","2025-06","Корпус В",85,94,42.5,47.0,4.25,4.7],
    ["Цех 2","2025-07","Деталь А",117,0,58.5,0.0,5.85,0.0],
    ["Цех 2","2025-07","Узел Б",111,134,55.5,67.0,5.55,6.7],
    ["Цех 2","2025-07","Корпус В",93,119,46.5,59.5,4.65,5.95],
    ["Цех 2","2025-08","Деталь А",82,124,41.0,62.0,4.1,6.2],
    ["Цех 2","2025-08","Узел Б",103,123,51.5,61.5,5.15,6.15],
    ["Цех 2","2025-08","Корпус В",83,70,41.5,35.0,4.15,3.5],
    ["Цех 2","2025-09","Деталь А",112,93,56.0,46.5,5.6,4.65],
    ["Цех 2","2025-09","Узел Б",89,114,44.5,57.0,4.45,5.7],
    ["Цех 2","2025-09","Корпус В",96,89,48.0,44.5,4.8,4.45],
    ["Цех 2","2025-10","Деталь А",100,114,50.0,57.0,5.0,5.7],
    ["Цех 2","2025-10","Узел Б",98,70,49.0,35.0,4.9,3.5],
    ["Цех 2","2025-10","Корпус В",109,98,54.5,49.0,5.45,4.9],
    ["Цех 2","2025-11","Деталь А",116,98,58.0,49.0,5.8,4.9],
    ["Цех 2","2025-11","Узел Б",100,99,50.0,49.5,5.0,4.95],
    ["Цех 2","2025-11","Корпус В",110,105,55.0,52.5,5.5,5.25],
    ["Цех 2","2025-12","Деталь А",92,103,46.0,51.5,4.6,5.15],
    ["Цех 2","2025-12","Узел Б",95,90,47.5,45.0,4.75,4.5],
    ["Цех 2","2025-12","Корпус В",110,86,55.0,43.0,5.5,4.3],
    ["Цех 3","2025-01","Деталь А",83,102,41.5,51.0,4.15,5.1],
    ["Цех 3","2025-01","Узел Б",98,88,49.0,44.0,4.9,4.4],
    ["Цех 3","2025-01","Корпус В",102,125,51.0,62.5,5.1,6.25],
    ["Цех 3","2025-02","Деталь А",86,0,43.0,0.0,4.3,0.0],
    ["Цех 3","2025-02","Узел Б",91,89,45.5,44.5,4.55,4.45],
    ["Цех 3","2025-02","Корпус В",113,99,56.5,49.5,5.65,4.95],
    ["Цех 3","2025-03","Деталь А",109,82,54.5,41.0,5.45,4.1],
    ["Цех 3","2025-03","Узел Б",86,93,43.0,46.5,4.3,4.65],
    ["Цех 3","2025-03","Корпус В",113,0,56.5,0.0,5.65,0.0],
    ["Цех 3","2025-04","Деталь А",92,119,46.0,59.5,4.6,5.95],
    ["Цех 3","2025-04","Узел Б",117,0,58.5,0.0,5.85,0.0],
    ["Цех 3","2025-04","Корпус В",114,93,57.0,46.5,5.7,4.65],
    ["Цех 3","2025-05","Деталь А",107,84,53.5,42.0,5.35,4.2],
    ["Цех 3","2025-05","Узел Б",115,100,57.5,50.0,5.75,5.0],
    ["Цех 3","2025-05","Корпус В",94,95,47.0,47.5,4.7,4.75],
    ["Цех 3","2025-06","Деталь А",98,95,49.0,47.5,4.9,4.75],
    ["Цех 3","2025-06","Узел Б",91,97,45.5,48.5,4.55,4.85],
    ["Цех 3","2025-06","Корпус В",99,113,49.5,56.5,4.95,5.65],
    ["Цех 3","2025-07","Деталь А",115,110,57.5,55.0,5.75,5.5],
    ["Цех 3","2025-07","Узел Б",110,110,55.0,55.0,5.5,5.5],
    ["Цех 3","2025-07","Корпус В",111,0,55.5,0.0,5.55,0.0],
    ["Цех 3","2025-08","Деталь А",118,92,59.0,46.0,5.9,4.6],
    ["Цех 3","2025-08","Узел Б",98,78,49.0,39.0,4.9,3.9],
    ["Цех 3","2025-08","Корпус В",90,116,45.0,58.0,4.5,5.8],
    ["Цех 3","2025-09","Деталь А",114,82,57.0,41.0,5.7,4.1],
    ["Цех 3","2025-09","Узел Б",111,82,55.5,41.0,5.55,4.1],
    ["Цех 3","2025-09","Корпус В",106,110,53.0,55.0,5.3,5.5],
    ["Цех 3","2025-10","Деталь А",109,109,54.5,54.5,5.45,5.45],
    ["Цех 3","2025-10","Узел Б",94,96,47.0,48.0,4.7,4.8],
    ["Цех 3","2025-10","Корпус В",118,110,59.0,55.0,5.9,5.5],
    ["Цех 3","2025-11","Деталь А",89,131,44.5,65.5,4.45,6.55],
    ["Цех 3","2025-11","Узел Б",103,112,51.5,56.0,5.15,5.6],
    ["Цех 3","2025-11","Корпус В",115,90,57.5,45.0,5.75,4.5],
    ["Цех 3","2025-12","Деталь А",100,84,50.0,42.0,5.0,4.2],
    ["Цех 3","2025-12","Узел Б",96,97,48.0,48.5,4.8,4.85],
    ["Цех 3","2025-12","Корпус В",86,104,43.0,52.0,4.3,5.2],
    ["Цех 4","2025-01","Деталь А",96,89,48.0,44.5,4.8,4.45],
    ["Цех 4","2025-01","Узел Б",83,92,41.5,46.0,4.15,4.6],
    ["Цех 4","2025-01","Корпус В",115,99,57.5,49.5,5.75,4.95],
    ["Цех 4","2025-02","Деталь А",87,90,43.5,45.0,4.35,4.5],
    ["Цех 4","2025-02","Узел Б",115,109,57.5,54.5,5.75,5.45],
    ["Цех 4","2025-02","Корпус В",85,98,42.5,49.0,4.25,4.9],
    ["Цех 4","2025-03","Деталь А",83,100,41.5,50.0,4.15,5.0],
    ["Цех 4","2025-03","Узел Б",96,117,48.0,58.5,4.8,5.85],
    ["Цех 4","2025-03","Корпус В",113,82,56.5,41.0,5.65,4.1],
    ["Цех 4","2025-04","Деталь А",93,89,46.5,44.5,4.65,4.45],
    ["Цех 4","2025-04","Узел Б",106,104,53.0,52.0,5.3,5.2],
    ["Цех 4","2025-04","Корпус В",106,70,53.0,35.0,5.3,3.5],
    ["Цех 4","2025-05","Деталь А",114,117,57.0,58.5,5.7,5.85],
    ["Цех 4","2025-05","Узел Б",113,121,56.5,60.5,5.65,6.05],
    ["Цех 4","2025-05","Корпус В",90,84,45.0,42.0,4.5,4.2],
    ["Цех 4","2025-06","Деталь А",118,92,59.0,46.0,5.9,4.6],
    ["Цех 4","2025-06","Узел Б",89,88,44.5,44.0,4.45,4.4],
    ["Цех 4","2025-06","Корпус В",105,104,52.5,52.0,5.25,5.2],
    ["Цех 4","2025-07","Деталь А",104,114,52.0,57.0,5.2,5.7],
    ["Цех 4","2025-07","Узел Б",90,124,45.0,62.0,4.5,6.2],
    ["Цех 4","2025-07","Корпус В",91,107,45.5,53.5,4.55,5.35],
    ["Цех 4","2025-08","Деталь А",84,69,42.0,34.5,4.2,3.45],
    ["Цех 4","2025-08","Узел Б",83,95,41.5,47.5,4.15,4.75],
    ["Цех 4","2025-08","Корпус В",93,89,46.5,44.5,4.65,4.45],
    ["Цех 4","2025-09","Деталь А",101,109,50.5,54.5,5.05,5.45],
    ["Цех 4","2025-09","Узел Б",112,100,56.0,50.0,5.6,5.0],
    ["Цех 4","2025-09","Корпус В",116,87,58.0,43.5,5.8,4.35],
    ["Цех 4","2025-10","Деталь А",114,86,57.0,43.0,5.7,4.3],
    ["Цех 4","2025-10","Узел Б",80,75,40.0,37.5,4.0,3.75],
    ["Цех 4","2025-10","Корпус В",119,118,59.5,59.0,5.95,5.9],
    ["Цех 4","2025-11","Деталь А",93,90,46.5,45.0,4.65,4.5],
    ["Цех 4","2025-11","Узел Б",89,115,44.5,57.5,4.45,5.75],
    ["Цех 4","2025-11","Корпус В",85,90,42.5,45.0,4.25,4.5],
    ["Цех 4","2025-12","Деталь А",87,112,43.5,56.0,4.35,5.6],
    ["Цех 4","2025-12","Узел Б",85,86,42.5,43.0,4.25,4.3],
    ["Цех 4","2025-12","Корпус В",82,119,41.0,59.5,4.1,5.95],
    ["Цех 5","2025-01","Деталь А",114,107,57.0,53.5,5.7,5.35],
    ["Цех 5","2025-01","Узел Б",99,133,49.5,66.5,4.95,6.65],
    ["Цех 5","2025-01","Корпус В",97,99,48.5,49.5,4.85,4.95],
    ["Цех 5","2025-02","Деталь А",100,129,50.0,64.5,5.0,6.45],
    ["Цех 5","2025-02","Узел Б",114,108,57.0,54.0,5.7,5.4],
    ["Цех 5","2025-02","Корпус В",95,91,47.5,45.5,4.75,4.55],
    ["Цех 5","2025-03","Деталь А",113,0,56.5,0.0,5.65,0.0],
    ["Цех 5","2025-03","Узел Б",116,73,58.0,36.5,5.8,3.65],
    ["Цех 5","2025-03","Корпус В",108,115,54.0,57.5,5.4,5.75],
    ["Цех 5","2025-04","Деталь А",107,93,53.5,46.5,5.35,4.65],
    ["Цех 5","2025-04","Узел Б",104,92,52.0,46.0,5.2,4.6],
    ["Цех 5","2025-04","Корпус В",115,109,57.5,54.5,5.75,5.45],
    ["Цех 5","2025-05","Деталь А",82,94,41.0,47.0,4.1,4.7],
    ["Цех 5","2025-05","Узел Б",81,91,40.5,45.5,4.05,4.55],
    ["Цех 5","2025-05","Корпус В",98,87,49.0,43.5,4.9,4.35],
    ["Цех 5","2025-06","Деталь А",119,104,59.5,52.0,5.95,5.2],
    ["Цех 5","2025-06","Узел Б",80,0,40.0,0.0,4.0,0.0],
    ["Цех 5","2025-06","Корпус В",115,123,57.5,61.5,5.75,6.15],
    ["Цех 5","2025-07","Деталь А",104,81,52.0,40.5,5.2,4.05],
    ["Цех 5","2025-07","Узел Б",118,119,59.0,59.5,5.9,5.95],
    ["Цех 5","2025-07","Корпус В",87,115,43.5,57.5,4.35,5.75],
    ["Цех 5","2025-08","Деталь А",85,105,42.5,52.5,4.25,5.25],
    ["Цех 5","2025-08","Узел Б",86,102,43.0,51.0,4.3,5.1],
    ["Цех 5","2025-08","Корпус В",88,92,44.0,46.0,4.4,4.6],
    ["Цех 5","2025-09","Деталь А",85,104,42.5,52.0,4.25,5.2],
    ["Цех 5","2025-09","Узел Б",114,93,57.0,46.5,5.7,4.65],
    ["Цех 5","2025-09","Корпус В",96,90,48.0,45.0,4.8,4.5],
    ["Цех 5","2025-10","Деталь А",103,99,51.5,49.5,5.15,4.95],
    ["Цех 5","2025-10","Узел Б",111,119,55.5,59.5,5.55,5.95],
    ["Цех 5","2025-10","Корпус В",97,85,48.5,42.5,4.85,4.25],
    ["Цех 5","2025-11","Деталь А",117,76,58.5,38.0,5.85,3.8],
    ["Цех 5","2025-11","Узел Б",84,90,42.0,45.0,4.2,4.5],
    ["Цех 5","2025-11","Корпус В",119,90,59.5,45.0,5.95,4.5],
    ["Цех 5","2025-12","Деталь А",115,122,57.5,61.0,5.75,6.1],
    ["Цех 5","2025-12","Узел Б",80,83,40.0,41.5,4.0,4.15],
    ["Цех 5","2025-12","Корпус В",103,79,51.5,39.5,5.15,3.95],
]

def _enrich(rows: list[list]) -> list[list]:
    """Схлопывает строки по ключам и добавляет столбцы: отклонение и % выполнения."""
    def _coerce_number(value) -> float:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip().replace(" ", "").replace("\u00A0", "")
        if not text:
            return 0.0
        if "." in text and "," in text:
            if text.rfind(",") > text.rfind("."):
                text = text.replace(".", "").replace(",", ".")
            else:
                text = text.replace(",", "")
        elif "," in text:
            parts = text.split(",")
            if len(parts[-1]) in (1, 2):
                text = text.replace(",", ".")
            else:
                text = "".join(parts)
        text = re.sub(r"[^0-9\.-]", "", text)
        if text in ("", ".", "-", "-."):
            return 0.0
        try:
            return float(text)
        except ValueError:
            return 0.0

    grouped: dict[tuple[str, str, str], dict[str, float]] = {}
    for r in rows:
        ws = str(r[0] or "").strip()
        dt = str(r[1] or "").strip()
        pr = str(r[2] or "").strip()
        plan = _coerce_number(r[3]) if len(r) > 3 else 0.0
        fact = _coerce_number(r[4]) if len(r) > 4 else 0.0
        plan_energy = _coerce_number(r[5]) if len(r) > 5 else 0.0
        fact_energy = _coerce_number(r[6]) if len(r) > 6 else 0.0
        plan_time = _coerce_number(r[7]) if len(r) > 7 else 0.0
        fact_time = _coerce_number(r[8]) if len(r) > 8 else 0.0
        key = (ws, dt, pr)
        if key not in grouped:
            grouped[key] = {
                "plan": 0.0,
                "fact": 0.0,
                "plan_energy": 0.0,
                "fact_energy": 0.0,
                "plan_time": 0.0,
                "fact_time": 0.0,
            }
        grouped[key]["plan"] += plan
        grouped[key]["fact"] += fact
        grouped[key]["plan_energy"] += plan_energy
        grouped[key]["fact_energy"] += fact_energy
        grouped[key]["plan_time"] += plan_time
        grouped[key]["fact_time"] += fact_time

    out = []
    for (ws, dt, pr), values in sorted(grouped.items()):
        plan = int(values["plan"])
        fact = int(values["fact"])
        dev = fact - plan
        if plan:
            pct = round((fact / plan * 100), 1)
        elif fact == 0:
            pct = 0.0
        else:
            pct = None

        energy_intensity = (float(values["fact_energy"]) / float(values["fact"])) if values["fact"] else 0.0
        time_intensity = (float(values["fact_time"]) / float(values["fact"])) if values["fact"] else 0.0
        time_utilization = (float(values["plan_time"]) / float(values["fact_time"]) * 100.0) if values["fact_time"] else 0.0

        out.append([
            ws, dt, pr, plan, fact, dev, pct,
            float(values["plan_energy"]), float(values["fact_energy"]),
            float(values["plan_time"]), float(values["fact_time"]),
            energy_intensity, time_intensity, time_utilization,
        ])
    return out


class ScrollableFrame(tk.Frame):
    """Фрейм с вертикальной прокруткой."""

    def __init__(self, parent, bg: str, **kw):
        outer = tk.Frame(parent, bg=bg)
        # use grid instead of pack to avoid mixing geometry managers
        padx = kw.pop("padx", 0)
        pady = kw.pop("pady", 0)
        outer.grid(sticky="nsew", padx=padx, pady=pady)
        self._c = tk.Canvas(outer, bg=bg, highlightthickness=0, bd=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=self._c.yview)
        self._c.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._c.pack(side="left", fill="both", expand=True)
        super().__init__(self._c, bg=bg, **kw)
        self._win = self._c.create_window((0, 0), window=self, anchor="nw")
        self.bind("<Configure>", lambda _: self._c.configure(scrollregion=self._c.bbox("all")))
        self._c.bind("<Configure>", lambda e: self._c.itemconfig(self._win, width=e.width))

        def _on_wheel(ev):
            self._c.yview_scroll(int(-ev.delta / 120), "units")
            return "break"

        self._c.bind("<Enter>", lambda e: self._c.bind_all("<MouseWheel>", _on_wheel))
        self._c.bind("<Leave>", lambda e: self._c.unbind_all("<MouseWheel>"))

    def recolor(self, bg: str):
        self._c.configure(bg=bg)
        self.configure(bg=bg)
        self._c.master.configure(bg=bg)


# ══════════════════════════════════════════════════════════════════════════════
#  ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ══════════════════════════════════════════════════════════════════════════════

class ReportApp(tk.Tk):

    _last_status = ("Встроенный датасет загружен", "#2f9e44", "#d3f9d8")

    def __init__(self):
        super().__init__()
        self.title("WorkshopReport — Производственный отчёт")
        self.geometry("1200x800")
        self.minsize(860, 620)
        # Не вызывать очистку экспортов автоматически — опционально через метод
        self._prompt_cleanup_exports = False

        # ── данные ────────────────────────────────────────────────────────────
        self._all_data: list[list] = []                  # обогащённые строки для отчёта
        self._view_data: list[list] = []                 # после фильтрации
        self._loaded_files: list[dict] = []              # [{name, rows, ok}]
        self._imported_rows: list[list] = []            # сырые строки из пользовательских файлов
        self._ws_vars: dict[str, tk.BooleanVar] = {}
        self._ws_check_widgets: dict = {}

        # ── сортировка таблицы ────────────────────────────────────────────────
        self._sort_col = 1
        self._sort_dir = 1

        # ── вкладки ───────────────────────────────────────────────────────────
        self._active_tab = "table"      # "table" | "charts"
        self._chart_type = "bar"        # "bar" | "line" | "pct"
        self._chart_canvas: Optional[FigureCanvasTkAgg] = None
        self._current_figure: Optional[plt.Figure] = None

        # ── тема ──────────────────────────────────────────────────────────────
        self._theme_name = "light"
        self._T = THEMES["light"]

        self._apply_ttk_style()
        self._build_ui()
        self._repaint()
        self._rebuild_controls()
        self._render_status_chip("Импортируйте файл(ы) и нажмите «Сформировать»",
                                 self._T["yellow"], "#1a202c")

    # ══════════════════════════════════════════════════════════════════════════
    #  TTK стили
    # ══════════════════════════════════════════════════════════════════════════

    def _apply_ttk_style(self):
        T = self._T
        s = ttk.Style(self)
        try: s.theme_use("clam")
        except tk.TclError: pass
        s.configure("TLabel",         background=T["bg"],       foreground=T["text"], font=FONT_UI)
        s.configure("Treeview",       background=T["surface"],  foreground=T["text"],
                    fieldbackground=T["surface"], rowheight=26, font=FONT_SM)
        s.configure("Treeview.Heading", background=T["surface2"], foreground=T["muted"], font=FONT_SM_B)
        s.map("Treeview",             background=[("selected", T["accent"])],
                                      foreground=[("selected", "#ffffff")])
        s.configure("Accent.TButton", background=T["accent"],   foreground="#ffffff", font=FONT_BOLD)
        s.map("Accent.TButton",       background=[("active", T["accent_soft"]), ("!disabled", T["accent"])])
        s.configure("Ghost.TButton",  background=T["ghost_bg"], foreground=T["ghost_fg"], font=FONT_SM_B)
        s.map("Ghost.TButton",        background=[("active", T["accent_soft"]), ("!disabled", T["ghost_bg"])])

    # ══════════════════════════════════════════════════════════════════════════
    #  ПОСТРОЕНИЕ UI
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        T = self._T
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # PanedWindow — двигаемый разделитель сайдбар/контент
        self.paned = tk.PanedWindow(self, orient="horizontal",
                                    sashwidth=5, sashrelief="flat",
                                    bg=T["sash"], bd=0)
        self.paned.grid(row=0, column=0, sticky="nsew")

        # ── SIDEBAR ───────────────────────────────────────────────────────────
        self._sb_outer = tk.Frame(self.paned, width=290)
        self.paned.add(self._sb_outer, minsize=210, sticky="nsew")
        self._sb_outer.rowconfigure(0, weight=1)
        self._sb_outer.columnconfigure(0, weight=1)

        sb = ScrollableFrame(self._sb_outer, bg=T["sidebar_bg"], padx=14, pady=14)
        sb.columnconfigure(0, weight=1)
        self._sb = sb

        # Лого
        self.lbl_logo = tk.Label(sb, text="WorkshopReport", font=FONT_LOGO)
        self.lbl_logo.grid(row=0, column=0, sticky="w")
        self.lbl_sub  = tk.Label(sb, text="Производственный отчёт", font=FONT_XS)
        self.lbl_sub.grid(row=1, column=0, sticky="w", pady=(1, 10))

        # Кнопка темы
        self.theme_btn = tk.Button(sb, command=self._toggle_theme,
                                   bd=0, highlightthickness=0,
                                   padx=10, pady=7, relief="flat", cursor="hand2",
                                   font=FONT_SM_B)
        self.theme_btn.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        # Импорт файлов
        self._sep_sb(sb, 3)
        self.lbl_import = tk.Label(sb, text="ЗАГРУЗКА ДАННЫХ", font=FONT_XS)
        self.lbl_import.grid(row=4, column=0, sticky="w", pady=(6, 6))

        self.import_btn = tk.Button(sb, text="📂  Загрузить CSV / JSON / XLSX",
                                    command=self._import_files,
                                    bd=0, highlightthickness=0,
                                    padx=10, pady=9, relief="flat", cursor="hand2",
                                    font=FONT_SM_B)
        self.import_btn.grid(row=5, column=0, sticky="ew")

        self.clear_data_btn = tk.Button(sb, text="🗑  Очистить загруженные данные",
                        command=self._clear_loaded_data,
                        bd=0, highlightthickness=0,
                        padx=10, pady=7, relief="flat", cursor="hand2",
                        font=FONT_SM_B)
        self.clear_data_btn.grid(row=6, column=0, sticky="ew", pady=(8, 6))

        self.files_frame = tk.Frame(sb)
        self.files_frame.grid(row=7, column=0, sticky="ew", pady=(8, 0))
        self.files_frame.columnconfigure(0, weight=1)

        # Фильтр цехов
        self._sep_sb(sb, 7)
        self.lbl_ws = tk.Label(sb, text="ЦЕХА", font=FONT_XS)
        self.lbl_ws.grid(row=8, column=0, sticky="w", pady=(6, 4))

        self.ws_search_var = tk.StringVar()
        self.ws_search = tk.Entry(sb, textvariable=self.ws_search_var,
                                  font=FONT_SM, bd=0, highlightthickness=1,
                                  relief="flat")
        self.ws_search.grid(row=9, column=0, sticky="ew", ipady=5, padx=1)
        self.ws_search_var.trace_add("write", lambda *_: self._filter_ws_list())

        self.ws_frame = tk.Frame(sb)
        self.ws_frame.grid(row=10, column=0, sticky="ew", pady=(6, 0))
        self.ws_frame.columnconfigure(0, weight=1)
        self.ws_frame.columnconfigure(1, weight=1)

        # Chips выбранных цехов
        self.chips_frame = tk.Frame(sb)
        self.chips_frame.grid(row=11, column=0, sticky="ew", pady=(6, 0))

        # Период
        self._sep_sb(sb, 12)
        self.lbl_period = tk.Label(sb, text="ПЕРИОД", font=FONT_XS)
        self.lbl_period.grid(row=13, column=0, sticky="w", pady=(6, 4))

        period_row = tk.Frame(sb)
        period_row.grid(row=14, column=0, sticky="ew")
        period_row.columnconfigure(1, weight=1)
        period_row.columnconfigure(3, weight=1)
        self.lbl_from = tk.Label(period_row, text="С", font=FONT_SM_B)
        self.lbl_from.grid(row=0, column=0, padx=(0, 4))
        self.start_var = tk.StringVar()
        self.start_combo = ttk.Combobox(period_row, textvariable=self.start_var,
                                        state="readonly", width=10, font=FONT_SM)
        self.start_combo.grid(row=0, column=1, sticky="ew", padx=(0, 6))
        self.lbl_to = tk.Label(period_row, text="по", font=FONT_SM_B)
        self.lbl_to.grid(row=0, column=2, padx=(0, 4))
        self.end_var = tk.StringVar()
        self.end_combo = ttk.Combobox(period_row, textvariable=self.end_var,
                                      state="readonly", width=10, font=FONT_SM)
        self.end_combo.grid(row=0, column=3, sticky="ew")

        # Продукция
        self.lbl_product = tk.Label(sb, text="ПРОДУКЦИЯ", font=FONT_XS)
        self.lbl_product.grid(row=15, column=0, sticky="w", pady=(10, 4))
        self.product_var = tk.StringVar()
        self.product_combo = ttk.Combobox(sb, textvariable=self.product_var,
                                          state="readonly", font=FONT_SM)
        self.product_combo.grid(row=16, column=0, sticky="ew")

        # Кнопка генерации
        self.gen_btn = tk.Button(sb, text="▶  Сформировать отчёт",
                                 command=self._generate_report,
                                 bd=0, highlightthickness=0,
                                 padx=12, pady=10, relief="flat", cursor="hand2",
                                 font=FONT_BOLD)
        self.gen_btn.grid(row=17, column=0, sticky="ew", pady=(14, 0))

        # Экспорт
        self._sep_sb(sb, 18)
        self.lbl_export_hdr = tk.Label(sb, text="ЭКСПОРТ", font=FONT_XS)
        self.lbl_export_hdr.grid(row=19, column=0, sticky="w", pady=(6, 6))

        self.exp_csv_btn  = tk.Button(sb, text="📄  Скачать CSV",
                                      command=self._export_csv,
                                      bd=0, highlightthickness=0,
                                      padx=10, pady=7, relief="flat", cursor="hand2",
                                      font=FONT_SM_B, state="disabled")
        self.exp_csv_btn.grid(row=20, column=0, sticky="ew", pady=(0, 4))
        self.exp_json_btn = tk.Button(sb, text="🗂  Скачать JSON",
                                      command=self._export_json,
                                      bd=0, highlightthickness=0,
                                      padx=10, pady=7, relief="flat", cursor="hand2",
                                      font=FONT_SM_B, state="disabled")
        self.exp_json_btn.grid(row=21, column=0, sticky="ew", pady=(0, 4))
        self.exp_html_btn = tk.Button(sb, text="🌐  Сохранить HTML",
                                      command=self._export_html,
                                      bd=0, highlightthickness=0,
                                      padx=10, pady=7, relief="flat", cursor="hand2",
                                      font=FONT_SM_B, state="disabled")
        self.exp_html_btn.grid(row=22, column=0, sticky="ew")

        # ── MAIN AREA ─────────────────────────────────────────────────────────
        self._main_outer = tk.Frame(self.paned)
        self.paned.add(self._main_outer, minsize=540, sticky="nsew")
        self._main_outer.rowconfigure(0, weight=1)
        self._main_outer.columnconfigure(0, weight=1)

        # Прокручиваемый холст для основного контента
        self._mc = tk.Canvas(self._main_outer, highlightthickness=0, bd=0)
        self._mvsb = ttk.Scrollbar(self._main_outer, orient="vertical", command=self._mc.yview)
        self._mc.configure(yscrollcommand=self._mvsb.set)
        self._mvsb.grid(row=0, column=1, sticky="ns")
        self._mc.grid(row=0, column=0, sticky="nsew")
        self._main_outer.rowconfigure(0, weight=1)
        self._main_outer.columnconfigure(0, weight=1)

        main = tk.Frame(self._mc, padx=20, pady=16)
        main.columnconfigure(0, weight=1)
        self._main = main
        self._mwin = self._mc.create_window((0, 0), window=main, anchor="nw")
        main.bind("<Configure>", lambda _: self._mc.configure(scrollregion=self._mc.bbox("all")))
        self._mc.bind("<Configure>", lambda e: self._mc.itemconfig(self._mwin, width=e.width))

        def _ignore_wheel(ev):
            return "break"

        self._mc.bind("<MouseWheel>", _ignore_wheel)
        main.bind("<MouseWheel>", _ignore_wheel)
        self.after_idle(lambda: self._mc.yview_moveto(0))

        # Заголовок страницы
        self.header_frame = tk.Frame(main, padx=16, pady=14)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.columnconfigure(0, weight=1)
        self.lbl_title    = tk.Label(self.header_frame, text="Отчёт по цехам", font=("Segoe UI", 20, "bold"))
        self.lbl_title.grid(row=0, column=0, sticky="w")
        self.lbl_subtitle = tk.Label(self.header_frame, text="Загрузите данные или используйте встроенный датасет", font=FONT_SM)
        self.lbl_subtitle.grid(row=1, column=0, sticky="w", pady=(2, 0))
        self.status_canvas = tk.Canvas(self.header_frame, width=380, height=38, highlightthickness=0)
        self.status_canvas.grid(row=0, column=1, rowspan=2, sticky="e", padx=(12, 0))

        self._hsep(main, 1)

        # KPI карточки
        self.kpi_frame = tk.Frame(main)
        self.kpi_frame.grid(row=2, column=0, sticky="ew", pady=(0, 4))
        for i in range(6): self.kpi_frame.columnconfigure(i, weight=1)

        self.kpi_cards: dict = {}
        kpi_defs = [
            ("plan",       "📦 План",         "Суммарный план"),
            ("fact",       "✅ Факт",           "Суммарный факт"),
            ("pct",        "📈 Выполнение",    "Средний %"),
            ("dev",        "↔ Отклонение",    "Факт − план"),
            ("over",       "▲ Перевыполнено", "позиций"),
            ("under",      "▼ Недовыполнено", "позиций"),
        ]
        for idx, (key, title, hint) in enumerate(kpi_defs):
            card = tk.Frame(self.kpi_frame, bd=0, padx=10, pady=10)
            card.grid(row=0, column=idx, sticky="nsew", padx=(0, 6) if idx < 5 else 0)
            lbl_t = tk.Label(card, text=title, font=FONT_XS)
            lbl_t.pack(anchor="w")
            val   = tk.Label(card, text="—", font=FONT_NUM)
            val.pack(anchor="w", pady=(3, 0))
            lbl_h = tk.Label(card, text=hint, font=FONT_XS)
            lbl_h.pack(anchor="w", pady=(1, 0))
            self.kpi_cards[key] = {"card": card, "val": val, "title": lbl_t, "hint": lbl_h}

        self.efficiency_frame = tk.Frame(main)
        self.efficiency_frame.grid(row=3, column=0, sticky="ew", pady=(0, 4))
        self.efficiency_frame.rowconfigure(0, weight=1)
        for col in range(6):
            self.efficiency_frame.columnconfigure(col, weight=1)
        self.efficiency_labels: dict[str, tk.Label] = {}
        self.efficiency_cards: dict[str, dict[str, tk.Widget]] = {}
        efficiency_defs = [
            ("energy_intensity", "Энергоёмкость (кВт·ч/ед)"),
            ("time_intensity", "Трудоёмкость (ч/ед)"),
            ("time_utilization", "Использование времени (%)"),
        ]
        for idx, (_, title) in enumerate(efficiency_defs):
            frame = tk.Frame(self.efficiency_frame, bd=0, padx=10, pady=10)
            frame.grid(row=0, column=idx*2, columnspan=2, sticky="nsew", padx=(0, 6) if idx < 2 else 0)
            lbl_title = tk.Label(frame, text=title, font=FONT_XS)
            lbl_title.pack(anchor="w")
            val = tk.Label(frame, text="—", font=FONT_NUM)
            val.pack(anchor="w", pady=(3, 0))
            self.efficiency_labels[title] = val
            self.efficiency_cards[title] = {"frame": frame, "title": lbl_title, "val": val}

        # Убираем лишнюю линию разделителя и сохраняем ровный отступ до вкладок

        # Вкладки Таблица / Графики
        tab_row = tk.Frame(main)
        tab_row.grid(row=4, column=0, sticky="ew")
        tab_row.columnconfigure(0, weight=1)

        self.tab_bar = tk.Frame(tab_row)
        self.tab_bar.grid(row=0, column=0, sticky="w")
        self.tab_btns: dict[str, tk.Button] = {}
        for tab_id, tab_label in [("table", "📋  Таблица"), ("charts", "📊  Графики")]:
            b = tk.Button(self.tab_bar, text=tab_label,
                          command=lambda t=tab_id: self._switch_tab(t),
                          bd=0, highlightthickness=0, padx=16, pady=8,
                          relief="flat", cursor="hand2", font=FONT_SM_B)
            b.pack(side="left", padx=(0, 2))
            self.tab_btns[tab_id] = b

        self._tab_sep = tk.Frame(main, height=2)
        self._tab_sep.grid(row=5, column=0, sticky="ew")

        # ── Панель таблицы ────────────────────────────────────────────────────
        self.table_panel = tk.Frame(main)
        self.table_panel.grid(row=6, column=0, sticky="nsew")
        self.table_panel.columnconfigure(0, weight=1)
        main.rowconfigure(6, weight=1)

        # Строка быстрых фильтров по цехам
        self.filter_bar = tk.Frame(self.table_panel)
        self.filter_bar.grid(row=0, column=0, sticky="ew", pady=(10, 8))
        self.filter_bar.columnconfigure(1, weight=1)
        self.lbl_filter = tk.Label(self.filter_bar, text="Цех:", font=FONT_SM_B)
        self.lbl_filter.grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.filter_chips = tk.Frame(self.filter_bar)
        self.filter_chips.grid(row=0, column=1, sticky="w")
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(self.filter_bar, textvariable=self.search_var,
                                     font=FONT_SM, bd=0, highlightthickness=1,
                                     relief="flat", width=20)
        self.search_entry.grid(row=0, column=2, sticky="e", ipady=4, padx=1)
        self.search_var.trace_add("write", lambda *_: self._render_table())

        # Treeview (таблица)
        tree_frame = tk.Frame(self.table_panel)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        self.table_panel.rowconfigure(1, weight=1)

        cols = ("workshop", "date", "product", "plan", "fact", "deviation", "pct",
                "energy_intensity", "time_intensity", "time_utilization")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        heads = {"workshop":"Цех","date":"Период","product":"Продукт",
                 "plan":"План","fact":"Факт","deviation":"Отклонение","pct":"Выполнение %",
                 "energy_intensity":"Энергоёмкость","time_intensity":"Трудоёмкость",
                 "time_utilization":"Использование времени"}
        widths = {"workshop":90,"date":80,"product":100,"plan":70,"fact":70,"deviation":90,
                  "pct":110,"energy_intensity":110,"time_intensity":110,"time_utilization":140}
        for c in cols:
            self.tree.heading(c, text=heads[c],
                              command=lambda col=c: self._sort_by(col))
            self.tree.column(c, width=widths[c], anchor="w" if c in ("workshop","product") else "e",
                             stretch=True)
        tsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        tsb.grid(row=0, column=1, sticky="ns")

        def _tree_wheel(ev):
            self.tree.yview_scroll(int(-ev.delta / 120), "units")
            return "break"

        self.tree.bind("<MouseWheel>", _tree_wheel)

        # Строка статуса таблицы
        self.tree_footer = tk.Frame(self.table_panel)
        self.tree_footer.grid(row=2, column=0, sticky="ew")
        self.tree_footer.columnconfigure(1, weight=1)
        self.lbl_row_count = tk.Label(self.tree_footer, text="Записей: 0", font=FONT_XS)
        self.lbl_row_count.grid(row=0, column=0, sticky="w", padx=4, pady=4)

        # ── Панель графиков ───────────────────────────────────────────────────
        self.chart_panel = tk.Frame(main)
        # (скрыта по умолчанию — показывается через _switch_tab)

        chart_ctrl = tk.Frame(self.chart_panel)
        chart_ctrl.pack(fill="x", pady=(10, 8))
        self.lbl_chart_type = tk.Label(chart_ctrl, text="Тип:", font=FONT_SM_B)
        self.lbl_chart_type.pack(side="left", padx=(0, 8))
        self.chart_type_btns: dict[str, tk.Button] = {}
        for ct_id, ct_label in [("bar","Столбцы"), ("line","Линия"), ("pct","% выполнения"),
                                  ("energy_ws","Энергоёмкость"), ("time_ws","Трудоёмкость"),
                                  ("utilization_ws","Использование времени")]:
            b = tk.Button(chart_ctrl, text=ct_label,
                          command=lambda t=ct_id: self._set_chart_type(t),
                          bd=0, highlightthickness=0, padx=12, pady=5,
                          relief="flat", cursor="hand2", font=FONT_SM)
            b.pack(side="left", padx=(0, 4))
            self.chart_type_btns[ct_id] = b

        self.chart_area = tk.Frame(self.chart_panel, height=340)
        self.chart_area.pack(fill="both", expand=True)
        self.chart_area.columnconfigure(0, weight=1)
        self.chart_area.rowconfigure(0, weight=1)

        self.chart_empty = tk.Frame(self.chart_area)
        self.chart_empty.grid(row=0, column=0, sticky="nsew")
        tk.Label(self.chart_empty, text="📊", font=("Segoe UI", 42)).pack(pady=(36, 8))
        tk.Label(self.chart_empty, text="Сформируйте отчёт, чтобы увидеть графики",
                 font=FONT_UI, justify="center").pack()

        # Активируем вкладку таблицы по умолчанию
        self._switch_tab("table", init=True)

    def _sep_sb(self, parent, row):
        """Тонкий разделитель в сайдбаре."""
        f = tk.Frame(parent, height=1)
        f.grid(row=row, column=0, sticky="ew", pady=(8, 0))
        self._sb_seps = getattr(self, "_sb_seps", [])
        self._sb_seps.append(f)

    def _hsep(self, parent, row):
        """Горизонтальный разделитель в основной панели."""
        f = tk.Frame(parent, height=1)
        f.grid(row=row, column=0, sticky="ew", pady=(4, 4))
        self._hseps = getattr(self, "_hseps", [])
        self._hseps.append(f)

    # ══════════════════════════════════════════════════════════════════════════
    #  ПОКРАСКА (repaint)
    # ══════════════════════════════════════════════════════════════════════════

    def _repaint(self):
        T = self._T
        self.configure(bg=T["bg"])
        self.paned.configure(bg=T["sash"])
        self._sb_outer.configure(bg=T["sidebar_bg"])
        self._sb.recolor(T["sidebar_bg"])

        # Sidebar labels
        for w in (self.lbl_logo, self.lbl_sub, self.lbl_import, self.lbl_ws,
                  self.lbl_period, self.lbl_product, self.lbl_export_hdr):
            try:
                w.configure(bg=T["sidebar_bg"])
            except Exception: pass
        self.lbl_logo.configure(fg=T["text"])
        self.lbl_sub.configure(fg=T["muted"])
        for lbl in (self.lbl_import, self.lbl_ws, self.lbl_period,
                    self.lbl_product, self.lbl_export_hdr):
            lbl.configure(fg=T["muted"])

        self.theme_btn.configure(bg=T["surface2"], fg=T["accent"],
                                 text=T["toggle_text"],
                                 activebackground=T["accent_soft"])
        self.import_btn.configure(bg=T["import_bg"], fg=T["import_fg"],
                                  activebackground=T["green"])
        self.gen_btn.configure(bg=T["accent"], fg="#ffffff",
                               activebackground=T["accent_soft"])

        # Export buttons
        for btn, ena in ((self.exp_csv_btn, self._view_data),
                         (self.exp_json_btn, self._view_data),
                         (self.exp_html_btn, self._view_data)):
            btn.configure(bg=T["ghost_bg"], fg=T["ghost_fg"],
                          activebackground=T["accent_soft"],
                          disabledforeground=T["muted"])

        # Files frame
        self.files_frame.configure(bg=T["sidebar_bg"])
        self._repaint_file_pills()

        # WS widgets
        self.ws_search.configure(bg=T["entry_bg"], fg=T["entry_fg"],
                                 insertbackground=T["entry_fg"],
                                 highlightcolor=T["accent"], highlightbackground=T["border"])
        self.ws_frame.configure(bg=T["sidebar_bg"])
        self.chips_frame.configure(bg=T["sidebar_bg"])
        for name, (cb, dot) in self._ws_check_widgets.items():
            cb.configure(bg=T["sidebar_bg"], fg=T["text"],
                         selectcolor=T["sidebar_bg"],
                         activebackground=T["sidebar_bg"])
            cb.master.configure(bg=T["sidebar_bg"])
            dot.configure(bg=T["sidebar_bg"])

        # Period
        for lbl in (self.lbl_from, self.lbl_to):
            lbl.configure(bg=T["sidebar_bg"], fg=T["text"])
        self.lbl_from.master.configure(bg=T["sidebar_bg"])

        # Separators
        for f in getattr(self, "_sb_seps", []):
            f.configure(bg=T["border"])
        for f in getattr(self, "_hseps", []):
            f.configure(bg=T["border"])
        self._tab_sep.configure(bg=T["accent"])

        # Main canvas
        self._mc.configure(bg=T["bg"])
        self._main.configure(bg=T["bg"])

        # Header
        self.header_frame.configure(bg=T["surface"])
        self.status_canvas.configure(bg=T["surface"])
        self.lbl_title.configure(bg=T["surface"], fg=T["text"])
        self.lbl_subtitle.configure(bg=T["surface"], fg=T["muted"])

        # KPI
        self.kpi_frame.configure(bg=T["bg"])
        for d in self.kpi_cards.values():
            d["card"].configure(bg=T["card_bg"])
            d["title"].configure(bg=T["card_bg"], fg=T["muted"])
            d["val"].configure(bg=T["card_bg"])
            d["hint"].configure(bg=T["card_bg"], fg=T["muted"])

        # Efficiency cards
        self.efficiency_frame.configure(bg=T["bg"])
        for d in self.efficiency_cards.values():
            d["frame"].configure(bg=T["card_bg"])
            d["title"].configure(bg=T["card_bg"], fg=T["muted"])
            d["val"].configure(bg=T["card_bg"])

        # Tab buttons
        tab_bar = self.tab_bar
        tab_bar.configure(bg=T["bg"])
        for tid, btn in self.tab_btns.items():
            active = tid == self._active_tab
            btn.configure(bg=T["bg"] if not active else T["accent_soft"],
                          fg=T["accent"] if active else T["muted"],
                          activebackground=T["accent_soft"])

        # Table panel
        self.table_panel.configure(bg=T["bg"])
        self.filter_bar.configure(bg=T["bg"])
        self.lbl_filter.configure(bg=T["bg"], fg=T["text"])
        self.filter_chips.configure(bg=T["bg"])
        self.search_entry.configure(bg=T["entry_bg"], fg=T["entry_fg"],
                                    insertbackground=T["entry_fg"],
                                    highlightcolor=T["accent"], highlightbackground=T["border"])
        self.tree_footer.configure(bg=T["surface2"])
        self.lbl_row_count.configure(bg=T["surface2"], fg=T["muted"])
        self._repaint_filter_chips()

        # Chart panel
        self.chart_panel.configure(bg=T["bg"])
        self.chart_area.configure(bg=T["surface"])
        self.chart_empty.configure(bg=T["surface"])
        for c in self.chart_empty.winfo_children():
            try: c.configure(bg=T["surface"], fg=T["muted"])
            except Exception: pass
        ctrl = self.lbl_chart_type.master
        ctrl.configure(bg=T["bg"])
        self.lbl_chart_type.configure(bg=T["bg"], fg=T["text"])
        self._repaint_chart_type_btns()

        # TTK
        self._apply_ttk_style()
        self._render_status_chip(*self._last_status)
        self._refresh_ws_chips()

    def _repaint_file_pills(self):
        T = self._T
        for child in self.files_frame.winfo_children():
            child.destroy()
        for f in self._loaded_files:
            pill = tk.Frame(self.files_frame, bg=T["card_bg"], padx=8, pady=6)
            pill.pack(fill="x", pady=(0, 4))
            pill.columnconfigure(1, weight=1)
            icon = "📄" if f["ok"] else "⚠️"
            tk.Label(pill, text=icon, bg=T["card_bg"], font=("Segoe UI", 14)).grid(row=0, column=0, rowspan=2, padx=(0, 8))
            tk.Label(pill, text=f["name"], bg=T["card_bg"], fg=T["text"],
                     font=FONT_SM_B, anchor="w").grid(row=0, column=1, sticky="w")
            meta = f"{f['rows']} строк" if f["ok"] else f.get("err", "Ошибка")
            tk.Label(pill, text=meta, bg=T["card_bg"], fg=T["muted"],
                     font=FONT_XS, anchor="w").grid(row=1, column=1, sticky="w")
            status = "✓" if f["ok"] else "✗"
            tk.Label(pill, text=status, bg=T["card_bg"],
                     fg=T["green"] if f["ok"] else T["red"],
                     font=FONT_SM_B).grid(row=0, column=2, rowspan=2, padx=(6, 2))

    def _repaint_chart_type_btns(self):
        T = self._T
        for ct_id, btn in self.chart_type_btns.items():
            active = ct_id == self._chart_type
            btn.configure(bg=T["accent_soft"] if active else T["surface2"],
                          fg=T["accent"] if active else T["muted"],
                          activebackground=T["accent_soft"])

    def _repaint_filter_chips(self):
        T = self._T
        ws_set = sorted({r[0] for r in self._all_data})
        for child in self.filter_chips.winfo_children():
            child.destroy()
        all_btn = tk.Button(self.filter_chips, text="Все",
                            command=lambda: self._set_table_filter("all"),
                            bd=0, highlightthickness=0, padx=10, pady=3,
                            relief="flat", cursor="hand2", font=FONT_XS)
        all_btn.pack(side="left", padx=(0, 4))
        self._filter_ws_active = getattr(self, "_filter_ws_active", "all")
        active_col = T["accent_soft"] if self._filter_ws_active == "all" else T["surface2"]
        active_fg  = T["accent"]      if self._filter_ws_active == "all" else T["muted"]
        all_btn.configure(bg=active_col, fg=active_fg, activebackground=T["accent_soft"])
        for ws in ws_set:
            active = self._filter_ws_active == ws
            b = tk.Button(self.filter_chips, text=ws,
                          command=lambda w=ws: self._set_table_filter(w),
                          bd=0, highlightthickness=0, padx=10, pady=3,
                          relief="flat", cursor="hand2", font=FONT_XS,
                          bg=T["accent_soft"] if active else T["surface2"],
                          fg=T["accent"] if active else T["muted"],
                          activebackground=T["accent_soft"])
            b.pack(side="left", padx=(0, 4))

    # ══════════════════════════════════════════════════════════════════════════
    #  ТЕМА
    # ══════════════════════════════════════════════════════════════════════════

    def _toggle_theme(self):
        self._theme_name = "dark" if self._theme_name == "light" else "light"
        self._T = THEMES[self._theme_name]
        self._repaint()
        if self._view_data:
            self._rebuild_chart()

    # ══════════════════════════════════════════════════════════════════════════
    #  СТАТУС-ПИЛЮЛЯ
    # ══════════════════════════════════════════════════════════════════════════

    def _render_status_chip(self, text: str, bg: str, fg: str):
        self._last_status = (text, bg, fg)
        c = self.status_canvas
        c.delete("all")
        w, h, r = int(c["width"]), int(c["height"]), 14
        c.create_oval(0, 0, r*2, h, fill=bg, outline=bg)
        c.create_oval(w-r*2, 0, w, h, fill=bg, outline=bg)
        c.create_rectangle(r, 0, w-r, h, fill=bg, outline=bg)
        c.create_text(w/2, h/2, text=text, fill=fg, font=FONT_SM_B)

    def _maybe_cleanup_exports(self):
        """Предложить пользователю удалить существующие файлы в папке exports."""
        try:
            exports_dir = Path(__file__).resolve().parents[1] / "exports"
            if not exports_dir.exists():
                return
            files = list(exports_dir.iterdir())
            if not files:
                return
            if messagebox.askyesno("Очистить экспорт?",
                                   f"Удалить все файлы в {exports_dir}?\n\nЭто действие необратимо."):
                for f in files:
                    try:
                        if f.is_file():
                            f.unlink()
                    except Exception:
                        pass
                messagebox.showinfo("Очистка", "Файлы экспорта удалены.")
        except Exception:
            return

    def _clear_loaded_data(self):
        """Удаляет загруженные файлы данных из текущей сессии и откатывает к пустому состоянию."""
        if not self._loaded_files:
            messagebox.showinfo("Очистка данных", "Нет загруженных файлов для удаления.")
            return
        if not messagebox.askyesno("Очистить данные", "Удалить все загруженные файлы и очистить отчёт?"):
            return
        self._loaded_files = []
        self._imported_rows = []
        self._all_data = []
        self._view_data = []
        self._repaint_file_pills()
        self._rebuild_controls()
        self._render_status_chip("Данные удалены — отчёт пуст", self._T["yellow"], "#1a202c")
        self._enable_export(False)

    # ══════════════════════════════════════════════════════════════════════════
    #  ЗАГРУЗКА ФАЙЛОВ
    # ══════════════════════════════════════════════════════════════════════════

    def _import_files(self):
        paths = filedialog.askopenfilenames(
            title="Выберите файлы данных",
            filetypes=[
                ("Все поддерживаемые", "*.csv *.json *.xlsx"),
                ("CSV", "*.csv"),
                ("JSON", "*.json"),
                ("Excel", "*.xlsx"),
                ("Все файлы", "*.*"),
            ],
        )
        if not paths:
            return
        # clear loader cache to avoid stale cached DataFrames
        try:
            from src import loader
            loader.clear_cache()
        except Exception:
            pass

        new_rows = []
        file_profiles = []
        for path in paths:
            p = Path(path)
            try:
                rows = self._parse_file(p)
                workshops = {r[0] for r in rows}
                products = {r[2] for r in rows}
                self._loaded_files.append({
                    "name": p.name,
                    "rows": len(rows),
                    "ok": True,
                    "workshops": workshops,
                    "products": products,
                })
                file_profiles.append((workshops, products))
                new_rows.extend(rows)
            except Exception as exc:
                self._loaded_files.append({"name": p.name, "rows": 0, "ok": False, "err": str(exc)})

        good_rows = [item["rows"] for item in self._loaded_files if item.get("ok")]
        if len(good_rows) > 1 and len(set(good_rows)) > 1:
            messagebox.showwarning(
                "Несоответствие строк",
                "Внимание: загруженные файлы имеют разное количество строк.\n"
                "Это может означать, что план и факт заданы не по одинаковым записям."
            )

        if len(file_profiles) > 1:
            workshop_sets = [frozenset(w) for w, _ in file_profiles]
            product_sets = [frozenset(p) for _, p in file_profiles]
            if len(set(workshop_sets)) > 1 or len(set(product_sets)) > 1:
                parts = []
                if len(set(workshop_sets)) > 1:
                    parts.append("цеха")
                if len(set(product_sets)) > 1:
                    parts.append("компоненты")
                messagebox.showwarning(
                    "Несоответствие структуры данных",
                    "Внимание: загруженные файлы содержат разные списки " + ", ".join(parts) + ".\n"
                    "Проверьте, что план и факт относятся к одним и тем же группам."
                )

        if new_rows:
            self._imported_rows.extend(new_rows)
            self._all_data = _enrich(self._imported_rows)
            self._repaint_file_pills()
            self._rebuild_controls()
            self._render_status_chip("Данные загружены — нажмите «Сформировать»",
                                     self._T["yellow"], "#1a202c")
        else:
            self._repaint_file_pills()
            self._rebuild_controls()
            self._render_status_chip("Не удалось загрузить ни одного набора данных",
                                     self._T["red"], "#ffffff")

    def _parse_file(self, path: Path) -> list[list]:
        # делегируем парсинг в loader.parse_table — там унифицированная логика
        try:
            from src import loader
            return loader.parse_table(path)
        except Exception:
            raise

    # ══════════════════════════════════════════════════════════════════════════
    #  КОНТРОЛЫ (цеха / периоды / продукция)
    # ══════════════════════════════════════════════════════════════════════════

    def _rebuild_controls(self):
        T = self._T
        workshops = sorted({r[0] for r in self._all_data})
        months    = sorted({r[1] for r in self._all_data})
        products  = sorted({r[2] for r in self._all_data})

        # WS vars
        current_ws = set(self._ws_vars)
        for w in workshops:
            if w not in self._ws_vars:
                self._ws_vars[w] = tk.BooleanVar(value=True)
        for w in current_ws - set(workshops):
            self._ws_vars.pop(w, None)

        self._rebuild_ws_list(workshops)
        self._repaint_filter_chips()

        prev_start = self.start_var.get() or (months[0] if months else "")
        prev_end   = self.end_var.get()   or (months[-1] if months else "")
        self.start_combo["values"] = months
        self.end_combo["values"]   = months
        self.start_var.set(prev_start if prev_start in months else (months[0] if months else ""))
        self.end_var.set(prev_end   if prev_end   in months else (months[-1] if months else ""))

        self.product_combo["values"] = ["Все"] + products
        if not self.product_var.get():
            self.product_var.set("Все")

    def _rebuild_ws_list(self, workshops):
        T = self._T
        self._ws_check_widgets.clear()
        for child in self.ws_frame.winfo_children():
            child.destroy()
        for idx, name in enumerate(workshops):
            col = idx % 2
            row_f = tk.Frame(self.ws_frame, bg=T["sidebar_bg"])
            row_f.grid(row=idx // 2, column=col, sticky="ew",
                       padx=(0, 4) if col == 0 else 0, pady=2)
            cb = tk.Checkbutton(row_f, text=name, variable=self._ws_vars[name],
                                bg=T["sidebar_bg"], fg=T["text"],
                                selectcolor=T["sidebar_bg"],
                                activebackground=T["sidebar_bg"],
                                activeforeground=T["text"],
                                bd=0, anchor="w", font=FONT_XS, cursor="hand2")
            cb.pack(side="left")
            pct = self._ws_pct(name)
            color = T["green"] if pct >= 100 else (T["yellow"] if pct >= 90 else T["red"])
            dot = tk.Canvas(row_f, width=8, height=8,
                            bg=T["sidebar_bg"], highlightthickness=0)
            dot.pack(side="right", padx=2)
            dot.create_oval(1, 1, 7, 7, fill=color, outline=color)
            self._ws_check_widgets[name] = (cb, dot)
        self._refresh_ws_chips()

    def _ws_pct(self, ws: str) -> float:
        rows = [r for r in self._all_data if r[0] == ws]
        plan = sum(r[3] for r in rows)
        fact = sum(r[4] for r in rows)
        return (fact / plan * 100) if plan else 0.0

    def _filter_ws_list(self):
        q = self.ws_search_var.get().lower()
        for name, (cb, dot) in self._ws_check_widgets.items():
            parent = cb.master
            if q and q not in name.lower():
                parent.grid_remove()
            else:
                parent.grid()

    def _refresh_ws_chips(self):
        T = self._T
        for child in self.chips_frame.winfo_children():
            child.destroy()
        self.chips_frame.configure(bg=T["sidebar_bg"])
        for name, var in self._ws_vars.items():
            if var.get():
                chip = tk.Frame(self.chips_frame, bg=T["chip_bg"], padx=6, pady=3)
                chip.pack(side="left", padx=(0, 4), pady=2)
                tk.Label(chip, text=name, bg=T["chip_bg"], fg=T["chip_fg"],
                         font=("Segoe UI", 8, "bold")).pack(side="left")
                x = tk.Label(chip, text=" ✕", bg=T["chip_bg"], fg=T["chip_fg"],
                             font=FONT_XS, cursor="hand2")
                x.pack(side="left")
                x.bind("<Button-1>", lambda e, n=name: (
                    self._ws_vars[n].set(False), self._refresh_ws_chips()))

    # ══════════════════════════════════════════════════════════════════════════
    #  ГЕНЕРАЦИЯ ОТЧЁТА
    # ══════════════════════════════════════════════════════════════════════════

    def _generate_report(self):
        T = self._T
        start   = self.start_var.get()
        end     = self.end_var.get()
        product = self.product_var.get() if hasattr(self, "product_var") else "Все"
        sel_ws  = [n for n, v in self._ws_vars.items() if v.get()]

        if not self._all_data:
            self._view_data = []
            self._render_status_chip("Импортируйте файл(ы) и нажмите «Сформировать»",
                                     T["yellow"], "#1a202c")
            self._render_table()
            self._enable_export(False)
            return

        if not sel_ws:
            messagebox.showwarning("Предупреждение", "Выберите хотя бы один цех.")
            return
        if start and end and start > end:
            messagebox.showwarning("Предупреждение", "Дата начала позже даты окончания.")
            return

        self._view_data = [
            r for r in self._all_data
            if r[0] in sel_ws
            and (not start or r[1] >= start)
            and (not end   or r[1] <= end)
            and (product == "Все" or r[2] == product)
        ]

        if not self._view_data:
            self._render_status_chip("❌ Нет данных за период", T["red"], "#ffffff")
            self._render_table()
            self._enable_export(False)
            return

        self._update_kpi(self._view_data)
        self._update_efficiency_summary(self._view_data)
        self._filter_ws_active = "all"
        self._repaint_filter_chips()
        self._render_table()
        if self._active_tab == "charts":
            if self._has_energy_data() and self._chart_type not in ("energy_ws", "time_ws", "utilization_ws"):
                self._set_chart_type("energy_ws")
            else:
                self._rebuild_chart()
        self._enable_export(True)

        total_plan = sum(r[3] for r in self._view_data)
        total_fact = sum(r[4] for r in self._view_data)
        avg_pct = (total_fact / total_plan * 100) if total_plan else None
        ws_str  = ", ".join(sel_ws) if len(sel_ws) <= 3 else f"{len(sel_ws)} цехов"
        period  = f"{start} – {end}" if start and end else "весь период"
        self.lbl_subtitle.configure(text=f"{ws_str} · {period}")

        if avg_pct is None:
            self._render_status_chip("❌ Нет планов — не с чем сравнивать", T["red"], "#ffffff")
            return
        if avg_pct >= 100:
            self._render_status_chip(f"✅ {avg_pct:.1f}% — план выполнен",
                                     T["green"], T["green_soft"])
        elif avg_pct >= 90:
            self._render_status_chip(f"⚠️ {avg_pct:.1f}% — почти выполнен",
                                     T["yellow"], T["yellow_soft"])
        else:
            self._render_status_chip(f"❌ {avg_pct:.1f}% — ниже плана",
                                     T["red"], T["red_soft"])

    # ══════════════════════════════════════════════════════════════════════════
    #  KPI
    # ══════════════════════════════════════════════════════════════════════════

    def _update_kpi(self, data: list[list]):
        T = self._T
        plan  = sum(r[3] for r in data)
        fact  = sum(r[4] for r in data)
        dev   = sum(r[5] for r in data)
        avg   = (fact / plan * 100) if plan else None
        over  = sum(1 for r in data if r[5] > 0)
        under = sum(1 for r in data if r[5] < 0)
        fmt   = lambda n: f"{abs(int(n)):,}".replace(",", "\u2009")

        def set_kpi(key, text, color):
            self.kpi_cards[key]["val"].configure(text=text, fg=color)

        set_kpi("plan",  fmt(plan), T["accent"])
        set_kpi("fact",  fmt(fact), T["green"] if fact >= plan else T["yellow"])
        pct_text = f"{avg:.1f}%" if avg is not None else "—"
        pct_color = (T["green"] if avg is not None and avg >= 100
                 else (T["yellow"] if avg is not None and avg >= 90 else T["red"]))
        set_kpi("pct",   pct_text, pct_color)
        set_kpi("dev",   ("+" if dev >= 0 else "−") + fmt(dev),
                T["green"] if dev >= 0 else T["red"])
        set_kpi("over",  str(over),  T["green"])
        set_kpi("under", str(under), T["red"])

    def _update_efficiency_summary(self, data: list[list]):
        T = self._T
        energy_cols = len(data[0]) >= 11 if data else False
        if not energy_cols:
            for label in self.efficiency_labels.values():
                label.configure(text="—", fg=T["muted"])
            return

        plan_qty = sum(int(r[3]) for r in data)
        fact_qty = sum(int(r[4]) for r in data)
        plan_energy = sum(float(r[7]) for r in data)
        fact_energy = sum(float(r[8]) for r in data)
        plan_time = sum(float(r[9]) for r in data)
        fact_time = sum(float(r[10]) for r in data)

        energy_intensity_fact = fact_energy / fact_qty if fact_qty else 0.0
        energy_intensity_plan = plan_energy / plan_qty if plan_qty else 0.0
        energy_deviation = fact_energy - plan_energy
        time_intensity_fact = fact_time / fact_qty if fact_qty else 0.0
        time_intensity_plan = plan_time / plan_qty if plan_qty else 0.0
        time_deviation = fact_time - plan_time
        time_utilization = (plan_time / fact_time * 100.0) if fact_time else 0.0

        def intensity_color(actual: float, target: float) -> str:
            """Зелёный если факт ≤ план, красный если факт > план."""
            if actual <= target:
                return T["green"]
            return T["red"]

        def utilization_color(value: float) -> str:
            """Зелёный ≥100%, жёлтый 90-99%, красный <90%."""
            if value >= 100.0:
                return T["green"]
            if value >= 90.0:
                return T["yellow"]
            return T["red"]

        self.efficiency_labels["Энергоёмкость (кВт·ч/ед)"].configure(
            text=f"{energy_intensity_fact:.2f}",
            fg=intensity_color(energy_intensity_fact, energy_intensity_plan)
        )
        self.efficiency_labels["Трудоёмкость (ч/ед)"].configure(
            text=f"{time_intensity_fact:.2f}",
            fg=intensity_color(time_intensity_fact, time_intensity_plan)
        )
        self.efficiency_labels["Использование времени (%)"].configure(
            text=f"{time_utilization:.1f}%",
            fg=utilization_color(time_utilization)
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  ТАБЛИЦА
    # ══════════════════════════════════════════════════════════════════════════

    def _set_table_filter(self, ws: str):
        self._filter_ws_active = ws
        self._repaint_filter_chips()
        self._render_table()

    def _sort_by(self, col: str):
        cols = ("workshop","date","product","plan","fact","deviation","pct",
                "energy_intensity","time_intensity","time_utilization")
        c = cols.index(col)
        if self._sort_col == c:
            self._sort_dir *= -1
        else:
            self._sort_col = c
            self._sort_dir = 1
        self._render_table()

    def _render_table(self):
        q   = self.search_var.get().strip().lower()
        fws = getattr(self, "_filter_ws_active", "all")
        data = [
            r for r in self._view_data
            if (fws == "all" or r[0] == fws)
            and (not q or q in " ".join(str(x) for x in r[:3]).lower())
        ]
        data.sort(key=lambda r: (str(r[self._sort_col]).lower()
                                 if isinstance(r[self._sort_col], str)
                                 else r[self._sort_col]),
                  reverse=(self._sort_dir == -1))

        self.tree.delete(*self.tree.get_children())
        T = self._T
        for r in data:
            sign = "+" if r[5] > 0 else ""
            if r[6] is not None:
                pct = f"{r[6]:.1f}%"
            elif r[3] != 0:
                pct = f"{r[4] / r[3] * 100:.1f}%"
            elif r[4] == 0:
                pct = "0.0%"
            else:
                pct = "—"
            self.tree.insert("", "end", values=(
                r[0], r[1], r[2],
                f"{int(r[3]):,}".replace(",","\u2009"),
                f"{int(r[4]):,}".replace(",","\u2009"),
                f"{sign}{int(r[5]):,}".replace(",","\u2009"),
                pct,
                f"{r[11]:.2f}",
                f"{r[12]:.2f}",
                f"{r[13]:.1f}%",
            ))
            # цветные теги
            tag = "pos" if r[5] > 0 else ("neg" if r[5] < 0 else "neu")
            self.tree.item(self.tree.get_children()[-1], tags=(tag,))

        self.tree.tag_configure("pos", foreground=T["green"])
        self.tree.tag_configure("neg", foreground=T["red"])
        self.tree.tag_configure("neu", foreground=T["muted"])



        self.lbl_row_count.configure(text=f"Записей: {len(data):,}".replace(",", "\u2009"), fg=T["muted"])

    # ══════════════════════════════════════════════════════════════════════════

    #  ВКЛАДКИ
    # ══════════════════════════════════════════════════════════════════════════

    def _switch_tab(self, tab: str, init: bool = False):
        T = self._T
        self._active_tab = tab

        if tab == "table":
            self.table_panel.grid(row=6, column=0, sticky="nsew")
            self.chart_panel.grid_forget()
        else:
            self.chart_panel.grid(row=6, column=0, sticky="nsew")
            self.table_panel.grid_forget()
            if not init and self._view_data:
                self._rebuild_chart()

        # перерисовать кнопки вкладок
        for tid, btn in self.tab_btns.items():
            active = tid == tab
            btn.configure(bg=T["accent_soft"] if active else T["bg"],
                          fg=T["accent"] if active else T["muted"])
        self._tab_sep.configure(bg=T["accent"])

    # ══════════════════════════════════════════════════════════════════════════
    #  ГРАФИКИ
    # ══════════════════════════════════════════════════════════════════════════

    def _set_chart_type(self, ct: str):
        self._chart_type = ct
        self._repaint_chart_type_btns()
        if self._view_data:
            self._rebuild_chart()

    def _has_energy_data(self) -> bool:
        if self._view_data:
            return len(self._view_data[0]) >= 11
        if self._all_data:
            return len(self._all_data[0]) >= 11
        return False

    def _rebuild_chart(self):
        T = self._T
        if not self._view_data:
            return
        self.chart_empty.grid_forget()

        months    = sorted({r[1] for r in self._view_data})
        workshops = sorted({r[0] for r in self._view_data})

        # Удалить старый холст
        if self._chart_canvas:
            self._chart_canvas.get_tk_widget().destroy()
            self._chart_canvas = None
        if self._current_figure:
            plt.close(self._current_figure)

        fig = plt.Figure(figsize=(8, 3.4), dpi=96)
        fig.patch.set_facecolor(T["mpl_bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(T["mpl_axes"])
        ax.tick_params(colors=T["mpl_tick"], labelsize=8)
        ax.xaxis.label.set_color(T["mpl_tick"])
        ax.yaxis.label.set_color(T["mpl_tick"])
        for spine in ax.spines.values():
            spine.set_edgecolor(T["mpl_grid"])
        ax.grid(axis="y", color=T["mpl_grid"], linewidth=.7, linestyle="--")
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(months, rotation=30, ha="right", fontsize=8)

        if self._chart_type == "pct":
            completion_by_date = []
            for m in months:
                rows = [r for r in self._view_data if r[1] == m]
                plan_sum = sum(r[3] for r in rows)
                fact_sum = sum(r[4] for r in rows)
                completion_by_date.append((fact_sum / plan_sum * 100) if plan_sum else float('nan'))

            ax.plot(range(len(months)), completion_by_date, marker="o", color="#a78bfa",
                    linewidth=2.2, markersize=6)
            ax.axhline(100, color="#94a3b8", linestyle="--", linewidth=1)
            ax.set_xticks(range(len(months)))
            ax.set_xticklabels(months, rotation=35, ha="right", fontsize=8)
            ax.set_title("Выполнение плана по месяцам", color=T["mpl_text"], fontsize=10, pad=8)
            ax.set_ylabel("Выполнение, %", color=T["mpl_tick"], fontsize=8)

            valid_values = [v for v in completion_by_date if v == v]
            if valid_values:
                min_val = min(valid_values)
                max_val = max(valid_values)
                pad = max((max_val - min_val) * 0.12, 5.0)
                ax.set_ylim(bottom=min_val - pad, top=max_val + pad)

            for x_val, y_val in zip(range(len(months)), completion_by_date):
                if y_val == y_val:
                    ax.annotate(f"{y_val:.1f}%", xy=(x_val, y_val), xytext=(0, 6), textcoords="offset points",
                                ha="center", va="bottom", color=T["mpl_text"], fontsize=8)

        elif self._chart_type == "energy_ws":
            # Энергоёмкость по цехам: kWh на единицу продукции
            try:
                if not self._view_data or len(self._view_data[0]) < 11:
                    raise RuntimeError("Нет данных по энергии")

                start = self.start_var.get()
                end = self.end_var.get()
                prod = self.product_var.get() if hasattr(self, 'product_var') else None
                rows = list(self._view_data)
                if prod and prod != "Все":
                    rows = [r for r in rows if r[2] == prod]
                if start:
                    rows = [r for r in rows if r[1] >= start]
                if end:
                    rows = [r for r in rows if r[1] <= end]

                workshops_list = sorted({r[0] for r in rows})
                intensities = []
                for ws in workshops_list:
                    sub = [r for r in rows if r[0] == ws]
                    total_energy = sum(r[8] for r in sub)
                    total_qty = sum(r[4] for r in sub)
                    intensity = (total_energy / total_qty) if total_qty else float('nan')
                    intensities.append(intensity)

                import numpy as _np
                med = float(_np.nanmedian([v for v in intensities if not _np.isnan(v)])) if any([not _np.isnan(v) for v in intensities]) else 0.0

                colors = []
                for val in intensities:
                    if _np.isnan(val):
                        colors.append('#94a3b8')
                    elif val < med * 0.9:
                        colors.append('#34d399')
                    elif val < med * 1.1:
                        colors.append('#fbbf24')
                    else:
                        colors.append('#f87171')

                xs = range(len(workshops_list))
                bars = ax.bar(xs, [v if not _np.isnan(v) else 0 for v in intensities],
                              color=colors, edgecolor=T['mpl_bg'], linewidth=0.8, alpha=0.96, zorder=3)
                ax.set_axisbelow(True)
                ax.set_xticks(xs)
                ax.set_xticklabels(workshops_list, rotation=30, ha='right', fontsize=8)
                ax.set_ylabel('kWh / ед.', color=T['mpl_tick'], fontsize=8)
                ax.set_title('Энергоёмкость по цехам', color=T['mpl_text'], fontsize=10, pad=8)
                ax.set_ylim(bottom=0, top=max([v for v in intensities if not _np.isnan(v)] + [1]) * 1.18)
                for side in ('top', 'right'):
                    ax.spines[side].set_visible(False)

                for bar, val in zip(bars, intensities):
                    h = bar.get_height()
                    label = f"{val:.2f}" if not _np.isnan(val) else "—"
                    ax.text(bar.get_x() + bar.get_width()/2, h + max(0.5, h*0.02), label,
                            ha='center', va='bottom', fontsize=8, color=T['mpl_text'])
            except Exception:
                ax.text(0.5, 0.5, 'Нет данных по энергии', ha='center', va='center', transform=ax.transAxes)

        elif self._chart_type == "energy_month":
            # План vs Факт по энергии по месяцам
            try:
                from src import loader
                plans_df = loader._CACHE.get('plans')
                facts_df = loader._CACHE.get('facts')
                if plans_df is None or facts_df is None:
                    raise RuntimeError('Нет данных план/факт с энергией')

                start = self.start_var.get()
                end = self.end_var.get()
                prod = self.product_var.get() if hasattr(self, 'product_var') else None
                sel_ws = sorted({r[0] for r in self._view_data}) if self._view_data else sorted({r[0] for r in self._all_data})

                p = plans_df.copy()
                f = facts_df.copy()
                if prod and prod != 'Все':
                    p = p[p['product'] == prod]
                    f = f[f['product'] == prod]
                if sel_ws:
                    p = p[p['workshop'].isin(sel_ws)]
                    f = f[f['workshop'].isin(sel_ws)]
                if start:
                    p = p[p['date'] >= start]
                    f = f[f['date'] >= start]
                if end:
                    p = p[p['date'] <= end]
                    f = f[f['date'] <= end]

                months_sorted = sorted(set(p['date']).union(set(f['date'])))
                plans_by_month = [p[p['date'] == m]['plan_energy'].sum() if 'plan_energy' in p.columns else 0.0 for m in months_sorted]
                facts_by_month = [f[f['date'] == m]['fact_energy'].sum() if 'fact_energy' in f.columns else 0.0 for m in months_sorted]

                ax.plot(range(len(months_sorted)), plans_by_month, color='#60a5fa', linewidth=1.2, linestyle='--')
                ax.plot(range(len(months_sorted)), facts_by_month, color='#fbbf24', linewidth=2, marker='o', markersize=6)
                ax.set_xticks(range(len(months_sorted)))
                ax.set_xticklabels(months_sorted, rotation=45, ha='right', fontsize=8)
                ax.set_ylabel('kWh', color=T['mpl_tick'], fontsize=8)
                ax.set_title('План vs Факт по энергии по месяцам', color=T['mpl_text'], fontsize=10, pad=8)
                ax.grid(axis='y', color=T['mpl_grid'], linewidth=.7, linestyle='--')
                # legend above
                ax.legend(['План (kWh)', 'Факт (kWh)'], loc='upper center', bbox_to_anchor=(0.5, 1.12), ncol=2, frameon=False)
            except Exception:
                ax.text(0.5, 0.5, 'Нет данных по энергии', ha='center', va='center', transform=ax.transAxes)

        elif self._chart_type == "time_ws":
            # Трудоёмкость по цехам: часы на единицу продукции
            try:
                if not self._view_data or len(self._view_data[0]) < 11:
                    raise RuntimeError('Нет данных по труду')

                start = self.start_var.get()
                end = self.end_var.get()
                prod = self.product_var.get() if hasattr(self, 'product_var') else None
                rows = list(self._view_data)
                if prod and prod != 'Все':
                    rows = [r for r in rows if r[2] == prod]
                if start:
                    rows = [r for r in rows if r[1] >= start]
                if end:
                    rows = [r for r in rows if r[1] <= end]

                workshops_list = sorted({r[0] for r in rows})
                intensities = []
                for ws in workshops_list:
                    sub = [r for r in rows if r[0] == ws]
                    total_time = sum(r[10] for r in sub)
                    total_qty = sum(r[4] for r in sub)
                    intensity = (total_time / total_qty) if total_qty else float('nan')
                    intensities.append(intensity)

                import numpy as _np
                med = float(_np.nanmedian([v for v in intensities if not _np.isnan(v)])) if any([not _np.isnan(v) for v in intensities]) else 0.0

                colors = []
                for val in intensities:
                    if _np.isnan(val):
                        colors.append('#94a3b8')
                    elif val < med * 0.9:
                        colors.append('#34d399')
                    elif val < med * 1.1:
                        colors.append('#fbbf24')
                    else:
                        colors.append('#f87171')

                xs = range(len(workshops_list))
                bars = ax.bar(xs, [v if not _np.isnan(v) else 0 for v in intensities],
                              color=colors, edgecolor=T['mpl_bg'], linewidth=0.8, alpha=0.96, zorder=3)
                ax.set_axisbelow(True)
                ax.set_xticks(xs)
                ax.set_xticklabels(workshops_list, rotation=30, ha='right', fontsize=8)
                ax.set_ylabel('ч / ед.', color=T['mpl_tick'], fontsize=8)
                ax.set_title('Трудоёмкость по цехам', color=T['mpl_text'], fontsize=10, pad=8)
                ax.set_ylim(bottom=0, top=max([v for v in intensities if not _np.isnan(v)] + [1]) * 1.18)
                for side in ('top', 'right'):
                    ax.spines[side].set_visible(False)

                for bar, val in zip(bars, intensities):
                    h = bar.get_height()
                    label = f"{val:.2f}" if not _np.isnan(val) else '—'
                    ax.text(bar.get_x() + bar.get_width()/2, h + max(0.25, h*0.02), label,
                            ha='center', va='bottom', fontsize=8, color=T['mpl_text'])
            except Exception:
                ax.text(0.5, 0.5, 'Нет данных по трудоёмкости', ha='center', va='center', transform=ax.transAxes)

        elif self._chart_type == "utilization_ws":
            # Использование времени по цехам: % планового времени
            try:
                if not self._view_data or len(self._view_data[0]) < 11:
                    raise RuntimeError('Нет данных по использованию времени')

                start = self.start_var.get()
                end = self.end_var.get()
                prod = self.product_var.get() if hasattr(self, 'product_var') else None
                rows = list(self._view_data)
                if prod and prod != 'Все':
                    rows = [r for r in rows if r[2] == prod]
                if start:
                    rows = [r for r in rows if r[1] >= start]
                if end:
                    rows = [r for r in rows if r[1] <= end]

                workshops_list = sorted({r[0] for r in rows})
                utilizations = []
                for ws in workshops_list:
                    sub = [r for r in rows if r[0] == ws]
                    total_plan_time = sum(r[9] for r in sub)
                    total_fact_time = sum(r[10] for r in sub)
                    util = (total_plan_time / total_fact_time * 100.0) if total_fact_time else float('nan')
                    utilizations.append(util)

                colors = []
                for val in utilizations:
                    if val != val:
                        colors.append('#94a3b8')
                    elif 90 <= val <= 110:
                        colors.append('#34d399')
                    elif 80 <= val < 90 or 110 < val <= 120:
                        colors.append('#fbbf24')
                    else:
                        colors.append('#f87171')

                xs = range(len(workshops_list))
                bars = ax.bar(xs, [v if v == v else 0 for v in utilizations],
                              color=colors, edgecolor=T['mpl_bg'], linewidth=0.8, alpha=0.96, zorder=3)
                ax.set_axisbelow(True)
                ax.set_xticks(xs)
                ax.set_xticklabels(workshops_list, rotation=30, ha='right', fontsize=8)
                ax.set_ylabel('%', color=T['mpl_tick'], fontsize=8)
                ax.set_title('Использование времени по цехам', color=T['mpl_text'], fontsize=10, pad=8)
                target = max([v for v in utilizations if v == v] + [100])
                ax.set_ylim(bottom=0, top=max(target * 1.15, 110))
                for side in ('top', 'right'):
                    ax.spines[side].set_visible(False)
                ax.axhline(100, color=T['muted'], linewidth=1, linestyle=':')

                for bar, val in zip(bars, utilizations):
                    h = bar.get_height()
                    label = f"{val:.1f}%" if val == val else '—'
                    ax.text(bar.get_x() + bar.get_width()/2, h + max(0.5, h*0.02), label,
                            ha='center', va='bottom', fontsize=8, color=T['mpl_text'])
            except Exception:
                ax.text(0.5, 0.5, 'Нет данных по использованию времени', ha='center', va='center', transform=ax.transAxes)

        elif self._chart_type == "line":
            for i, ws in enumerate(workshops):
                color = PALETTE[i % len(PALETTE)]
                plans = [sum(r[3] for r in self._view_data if r[0]==ws and r[1]==m) for m in months]
                facts = [sum(r[4] for r in self._view_data if r[0]==ws and r[1]==m) for m in months]
                ax.plot(range(len(months)), plans, color=color, linewidth=1.2,
                        linestyle="--", alpha=.6)
                ax.plot(range(len(months)), facts, color=color, linewidth=2,
                        label=ws, marker="o", markersize=3)
            ax.set_ylabel("Ед. продукции", color=T["mpl_tick"], fontsize=8)
            ax.set_title("Факт (сплошная) vs план (пунктир)", color=T["mpl_text"], fontsize=10, pad=8)

        else:  # bar
            products = sorted({r[2] for r in self._view_data})
            x = list(range(len(products)))
            width = 0.35
            plan_vals = [sum(r[3] for r in self._view_data if r[2] == product) for product in products]
            fact_vals = [sum(r[4] for r in self._view_data if r[2] == product) for product in products]

            bars1 = ax.bar([i - width / 2 for i in x], plan_vals, width=width, label="План", color="#60a5fa", alpha=0.95)
            bars2 = ax.bar([i + width / 2 for i in x], fact_vals, width=width, label="Факт", color="#34d399", alpha=0.95)
            ax.set_xticks(x)
            ax.set_xticklabels(products, rotation=15, ha='right', fontsize=8)
            ax.set_ylabel("Объём", color=T["mpl_tick"], fontsize=8)
            ax.set_title("План vs Факт по продукции", color=T["mpl_text"], fontsize=10, pad=8)

            if plan_vals or fact_vals:
                max_val = max(max(plan_vals, default=0), max(fact_vals, default=0))
                ax.set_ylim(bottom=0, top=max_val * 1.15 if max_val else 1)

            for b in bars1 + bars2:
                h = b.get_height()
                ax.annotate(f"{int(h):,}".replace(",", " "), xy=(b.get_x() + b.get_width() / 2, h), xytext=(0, 6),
                            textcoords="offset points", ha="center", va="bottom", color=T["mpl_text"], fontsize=8)

        legend = ax.legend(fontsize=7.5, framealpha=.8,
                           facecolor=T["mpl_bg"], edgecolor=T["mpl_grid"],
                           labelcolor=T["mpl_text"])
        fig.tight_layout(pad=1.4)

        self._current_figure = fig
        self._chart_canvas   = FigureCanvasTkAgg(fig, master=self.chart_area)
        self._chart_canvas.draw()
        self._chart_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    # ══════════════════════════════════════════════════════════════════════════
    #  ЭКСПОРТ
    # ══════════════════════════════════════════════════════════════════════════

    def _enable_export(self, on: bool):
        state = "normal" if on else "disabled"
        for btn in (self.exp_csv_btn, self.exp_json_btn, self.exp_html_btn):
            btn.configure(state=state)

    def _ask_save(self, ext: str, desc: str) -> Optional[Path]:
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        path  = filedialog.asksaveasfilename(
            title=f"Сохранить {desc}",
            defaultextension=f".{ext}",
            initialfile=f"workshop_report_{stamp}.{ext}",
            filetypes=[(desc, f"*.{ext}"), ("Все файлы", "*.*")],
        )
        return Path(path) if path else None

    def _export_csv(self):
        if not self._view_data: return
        path = self._ask_save("csv", "CSV файл")
        if not path: return
        has_energy = len(self._view_data[0]) >= 11
        header = ["Цех","Период","Продукт","План","Факт","Отклонение","Выполнение %"]
        if has_energy:
            header += ["Энергоёмкость","Трудоёмкость","Использование времени"]
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(header)
            for r in self._view_data:
                pct = (f"{r[6]:.1f}%" if r[6] is not None else "")
                row = [r[0], r[1], r[2], r[3], r[4], r[5], pct]
                if has_energy:
                    row += [f"{r[11]:.2f}", f"{r[12]:.2f}", f"{r[13]:.1f}%"]
                w.writerow(row)
        messagebox.showinfo("Экспорт", f"CSV сохранён:\n{path}")

    def _export_json(self):
        if not self._view_data: return
        path = self._ask_save("json", "JSON файл")
        if not path: return
        base_keys = ["workshop","date","product","plan_qty","fact_qty","deviation","completion_pct"]
        extra_keys = []
        if len(self._view_data[0]) >= 11:
            extra_keys = ["plan_energy","fact_energy","plan_time","fact_time",
                          "energy_intensity","time_intensity","time_utilization"]
        keys = base_keys + extra_keys
        obj  = {
            "generated": datetime.now().isoformat(),
            "data": [dict(zip(keys, r[: len(keys)])) for r in self._view_data]
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("Экспорт", f"JSON сохранён:\n{path}")

    def _export_html(self):
        if not self._view_data: return
        path = self._ask_save("html", "HTML отчёт")
        if not path: return

        plan  = sum(r[3] for r in self._view_data)
        fact  = sum(r[4] for r in self._view_data)
        avg   = (fact / plan * 100) if plan else None
        stamp = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        has_energy = len(self._view_data[0]) >= 11 if self._view_data else False
        if has_energy:
            plan_energy = sum(r[7] for r in self._view_data)
            fact_energy = sum(r[8] for r in self._view_data)
            plan_time = sum(r[9] for r in self._view_data)
            fact_time = sum(r[10] for r in self._view_data)
            plan_qty = sum(r[3] for r in self._view_data)
            fact_qty = sum(r[4] for r in self._view_data)
            energy_intensity_fact = fact_energy / fact_qty if fact_qty else 0.0
            energy_intensity_plan = plan_energy / plan_qty if plan_qty else 0.0
            time_intensity_fact = fact_time / fact_qty if fact_qty else 0.0
            time_intensity_plan = plan_time / plan_qty if plan_qty else 0.0

        rows_html = ""
        for r in self._view_data:
            sign = "+" if r[5] > 0 else ""
            cls  = "pos" if r[5] > 0 else ("neg" if r[5] < 0 else "")
            rows_html += (
                f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td>"
                f"<td>{int(r[3]):,}</td><td>{int(r[4]):,}</td>"
                f"<td class='{cls}'>{sign}{int(r[5]):,}</td>"
                f"<td>{(f'{r[6]:.1f}%' if r[6] is not None else '—')}</td>"
                f"<td>{r[11]:.2f}</td><td>{r[12]:.2f}</td>"
                f"<td>{r[13]:.1f}%</td></tr>\n"
            )

        df_columns = ["Цех","Период","Продукт","План","Факт","Отклонение","Выполнение %"]
        if has_energy:
            df_columns += ["Энергоёмкость","Трудоёмкость","Использование времени"]
        df = pd.DataFrame(self._view_data, columns=df_columns)
        workshop_summary = (
            df.groupby("Цех", as_index=False)
              .agg(План=("План","sum"), Факт=("Факт","sum"))
        )
        workshop_summary["Отклонение"] = workshop_summary["Факт"] - workshop_summary["План"]
        workshop_summary["Выполнение %"] = workshop_summary.apply(
            lambda row: f"{(row['Факт'] / row['План'] * 100):.1f}%" if row['План'] else "—",
            axis=1,
        )

        month_summary = (
            df.groupby("Период", as_index=False)
              .agg(План=("План","sum"), Факт=("Факт","sum"))
        )
        month_summary["Отклонение"] = month_summary["Факт"] - month_summary["План"]
        month_summary["Выполнение %"] = month_summary.apply(
            lambda row: f"{(row['Факт'] / row['План'] * 100):.1f}%" if row['План'] else "—",
            axis=1,
        )

        workshop_html = workshop_summary.to_html(index=False, border=1)
        month_html = month_summary.to_html(index=False, border=1)

        graph_html = ""
        if self._current_figure is not None:
            try:
                image_path = path.with_suffix(".png")
                self._current_figure.savefig(image_path, bbox_inches="tight")
                graph_html = f"<h2>График</h2>\n<img src=\"{image_path.name}\" alt=\"graph\" />"
            except Exception:
                graph_html = ""

        charts_html = ""
        if self._has_energy_data():
            def _save_chart(chart_type: str, filename: Path) -> bool:
                original_type = self._chart_type
                try:
                    self._set_chart_type(chart_type)
                    if self._current_figure is not None:
                        self._current_figure.savefig(filename, bbox_inches="tight")
                        return True
                except Exception:
                    return False
                finally:
                    self._set_chart_type(original_type)
                return False

            energy_ws_path = path.with_name(f"{path.stem}_energy_ws.png")
            time_ws_path = path.with_name(f"{path.stem}_time_ws.png")
            utilization_ws_path = path.with_name(f"{path.stem}_utilization_ws.png")
            saved_energy_ws = _save_chart("energy_ws", energy_ws_path)
            saved_time_ws = _save_chart("time_ws", time_ws_path)
            saved_utilization_ws = _save_chart("utilization_ws", utilization_ws_path)
            if saved_energy_ws:
                charts_html += f"<h2>Энергоёмкость по цехам</h2><img src=\"{energy_ws_path.name}\" alt=\"energy_ws\" />\n"
            if saved_time_ws:
                charts_html += f"<h2>Трудоёмкость по цехам</h2><img src=\"{time_ws_path.name}\" alt=\"time_ws\" />\n"
            if saved_utilization_ws:
                charts_html += f"<h2>Использование времени по цехам</h2><img src=\"{utilization_ws_path.name}\" alt=\"utilization_ws\" />\n"

        efficiency_summary_html = ""
        if has_energy:
            efficiency_summary_html = f"""
<h2>Сводка эффективности</h2>
<table>
<tr><td><b>Энергоёмкость (факт)</b></td><td>{energy_intensity_fact:.2f} кВт·ч/шт</td></tr>
<tr><td><b>Энергоёмкость (план)</b></td><td>{energy_intensity_plan:.2f} кВт·ч/шт</td></tr>
<tr><td><b>Трудоёмкость (факт)</b></td><td>{time_intensity_fact:.2f} ч/шт</td></tr>
<tr><td><b>Трудоёмкость (план)</b></td><td>{time_intensity_plan:.2f} ч/шт</td></tr>
</table>
"""

        html = f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"/>
<title>WorkshopReport</title>
<style>
body{{font-family:'Segoe UI',sans-serif;background:#f0f4f8;color:#1a202c;padding:32px}}
h1{{margin-bottom:4px;font-size:24px}}
.sub{{color:#718096;font-size:13px;margin-bottom:24px}}
.kpis{{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:28px}}
.k{{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px 18px;min-width:130px}}
.k-l{{font-size:10px;font-weight:700;text-transform:uppercase;color:#718096;
      letter-spacing:.07em;margin-bottom:6px}}
.k-v{{font-size:24px;font-weight:700;color:#3b5bdb}}
table{{width:100%;border-collapse:collapse;background:#fff;
       border-radius:10px;overflow:hidden;box-shadow:0 1px 6px rgba(0,0,0,.07);margin-bottom:28px}}
th{{background:#f7f9fc;padding:10px 14px;font-size:10px;font-weight:700;
    text-transform:uppercase;letter-spacing:.07em;color:#718096;
    text-align:left;border-bottom:2px solid #e2e8f0}}
td{{padding:9px 14px;border-bottom:1px solid #e2e8f0;font-size:13px}}
tr:last-child td{{border-bottom:none}}
tr:hover td{{background:#f7f9fc}}
.pos{{color:#2f9e44;font-weight:600}}
.neg{{color:#c92a2a;font-weight:600}}
.footer{{margin-top:20px;font-size:11px;color:#a0aec0}}
</style></head><body>
<h1>Отчёт по цехам</h1>
<p class="sub">Сформирован: {stamp}</p>
<div class="kpis">
  <div class="k"><div class="k-l">Итого план</div>
    <div class="k-v">{int(plan):,}</div></div>
  <div class="k"><div class="k-l">Итого факт</div>
    <div class="k-v">{int(fact):,}</div></div>
    <div class="k"><div class="k-l">Среднее выполнение</div>
        <div class="k-v">{(f'{avg:.1f}%' if avg is not None else '—')}</div></div>
</div>
<h2>Детальная таблица</h2>
<table>
<thead><tr><th>Цех</th><th>Период</th><th>Продукт</th>
<th>План</th><th>Факт</th><th>Отклонение</th><th>Выполнение %</th>
<th>Энергоёмкость</th><th>Трудоёмкость</th><th>Использование времени</th></tr></thead>
<tbody>{rows_html}</tbody></table>
<h2>Итоги по цехам</h2>
{workshop_html}
<h2>Итоги по периодам</h2>
{month_html}
{efficiency_summary_html}
{graph_html}
{charts_html}
<div class="footer">Экспорт WorkshopReport · {stamp}</div>
</body></html>"""

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        messagebox.showinfo("Экспорт", f"HTML сохранён:\n{path}")
        webbrowser.open(path.as_uri())

    @staticmethod
    def _normalize_header(value: object) -> str:
        if value is None:
            return ""
        return "".join(ch.lower() for ch in str(value) if ch.isalnum())

    def _find_matching_column(self, columns, *aliases) -> Optional[object]:
        aliases_norm = [self._normalize_header(a) for a in aliases]
        for col in columns:
            col_norm = self._normalize_header(col)
            if any(alias in col_norm or col_norm in alias for alias in aliases_norm):
                return col
        return None

    @staticmethod
    def _coerce_number(value) -> float:
        if value is None:
            return 0.0
        if isinstance(value, str):
            text = value.strip().replace(" ", "").replace(",", ".")
            if not text:
                return 0.0
            try:
                return float(text)
            except ValueError:
                return 0.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _parse_rows_from_table(self, df) -> list[list]:
        if df is None or df.empty:
            return []
        columns = list(df.columns)
        ws_col = self._find_matching_column(columns, "workshop", "цех", "shop", "workshopname")
        dt_col = self._find_matching_column(columns, "date", "period", "период", "месяц", "month", "дата")
        pr_col = self._find_matching_column(columns, "product", "продукт", "item", "detail", "деталь", "узел", "position", "name")
        pl_col = self._find_matching_column(columns, "plan", "planqty", "plan_qty", "план", "planned", "plannedqty", "qtyplan")
        ft_col = self._find_matching_column(columns, "fact", "factqty", "fact_qty", "факт", "actual", "actualqty", "qtyfact")

        if not all([ws_col, dt_col, pr_col]):
            raise ValueError(f"Не удалось сопоставить обязательные столбцы. Найдено: {columns}")

        rows = []
        for _, row in df.iterrows():
            ws = "" if ws_col is None else str(row[ws_col]) if not pd.isna(row[ws_col]) else ""
            dt = "" if dt_col is None else str(row[dt_col]) if not pd.isna(row[dt_col]) else ""
            pr = "" if pr_col is None else str(row[pr_col]) if not pd.isna(row[pr_col]) else ""
            plan = self._coerce_number(row[pl_col]) if pl_col is not None else 0.0
            fact = self._coerce_number(row[ft_col]) if ft_col is not None else 0.0
            if not any([ws, dt, pr, plan, fact]):
                continue
            rows.append([ws, dt, pr, plan, fact])
        return rows
