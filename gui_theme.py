import tkinter as tk
from tkinter import ttk

# --- Theme Colors (Premium Modern Dark Mode) ---
BG_MAIN = "#111215"       # Obsidian Black
BG_CARD = "#1c1d22"       # Charcoal Slate
BG_SIDEBAR = "#15161b"    # Medium Slate
ACCENT = "#00f0ff"        # Electric Cyan
INCOME = "#10b981"        # Neon Green
EXPENSE = "#ef4444"       # Neon Red / Coral
WARNING = "#f59e0b"       # Amber / Orange
BORDER = "#2e3039"         # Dark Grey outline

TEXT_PRIMARY = "#ffffff"  # Clear White
TEXT_MUTED = "#9ca3af"    # Muted Grey
TEXT_DARK = "#111215"     # Dark text for bright buttons

# --- Typography ---
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_SUBTITLE = ("Segoe UI", 12, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_BODY_BOLD = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 8)
FONT_SCORE = ("Segoe UI", 24, "bold")

def draw_rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    """
    Draws a smooth rounded rectangle on a Tkinter Canvas.
    """
    points = [
        x1 + radius, y1,
        x1 + radius, y1,
        x2 - radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1 + radius,
        x1, y1
    ]
    return canvas.create_polygon(points, **kwargs, smooth=True)

def setup_ttk_styles():
    """
    Styles ttk widgets to match the dark theme, modifying tables, dropdowns, etc.
    """
    style = ttk.Style()
    
    # Configure overall styles
    style.theme_use('clam')
    
    # Treeview (Transactions Table) Styling
    style.configure(
        "Treeview",
        background=BG_CARD,
        foreground=TEXT_PRIMARY,
        fieldbackground=BG_CARD,
        rowheight=28,
        font=FONT_BODY,
        borderwidth=0
    )
    style.map(
        "Treeview",
        background=[('selected', "#2d303b")],
        foreground=[('selected', ACCENT)]
    )
    
    style.configure(
        "Treeview.Heading",
        background=BG_SIDEBAR,
        foreground=TEXT_PRIMARY,
        font=FONT_BODY_BOLD,
        borderwidth=1,
        relief="flat"
    )
    
    # Scrollbar Styling
    style.configure(
        "Vertical.TScrollbar",
        gripcount=0,
        background=BG_CARD,
        troughcolor=BG_MAIN,
        bordercolor=BG_MAIN,
        arrowcolor=TEXT_MUTED
    )
    
    # Combobox (Dropdown) Styling
    style.configure(
        "TCombobox",
        arrowcolor=ACCENT,
        background=BG_CARD,
        fieldbackground=BG_CARD,
        foreground=TEXT_PRIMARY,
        bordercolor=BORDER,
        darkcolor=BG_CARD,
        lightcolor=BG_CARD,
        selectbackground=BG_CARD,
        selectforeground=TEXT_PRIMARY
    )
    
    style.map(
        "TCombobox",
        background=[
            ('readonly', BG_CARD),
            ('active', BG_CARD),
            ('focus', BG_CARD),
            ('disabled', BG_CARD)
        ],
        fieldbackground=[
            ('readonly', BG_CARD),
            ('active', BG_CARD),
            ('focus', BG_CARD),
            ('disabled', BG_CARD)
        ],
        foreground=[
            ('readonly', TEXT_PRIMARY),
            ('disabled', TEXT_MUTED),
            ('active', TEXT_PRIMARY),
            ('focus', TEXT_PRIMARY)
        ],
        bordercolor=[
            ('readonly', BORDER),
            ('active', ACCENT),
            ('focus', ACCENT)
        ],
        lightcolor=[
            ('readonly', BORDER),
            ('active', ACCENT),
            ('focus', ACCENT)
        ],
        darkcolor=[
            ('readonly', BORDER),
            ('active', BORDER),
            ('focus', BORDER)
        ]
    )
    
    # Configure the standard listbox options which the combobox dropdown uses
    style.master.option_add("*TCombobox*Listbox.background", BG_CARD)
    style.master.option_add("*TCombobox*Listbox.foreground", TEXT_PRIMARY)
    style.master.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    style.master.option_add("*TCombobox*Listbox.selectForeground", TEXT_DARK)
    style.master.option_add("*TCombobox*Listbox.font", FONT_BODY)
    style.master.option_add("*TCombobox*Listbox.relief", "flat")
    style.master.option_add("*TCombobox*Listbox.borderWidth", "0")
    
    # Configure standard Entry defaults to prevent default white highlights
    style.master.option_add("*Entry.background", BG_MAIN)
    style.master.option_add("*Entry.foreground", TEXT_PRIMARY)
    style.master.option_add("*Entry.insertBackground", TEXT_PRIMARY)
    style.master.option_add("*Entry.selectBackground", ACCENT)
    style.master.option_add("*Entry.selectForeground", TEXT_DARK)
    style.master.option_add("*Entry.font", FONT_BODY)
    style.master.option_add("*Entry.relief", "flat")
    style.master.option_add("*Entry.borderWidth", "0")
    
    # Tab styling
    style.configure("TNotebook", background=BG_MAIN, borderwidth=0)
    style.configure("TNotebook.Tab", background=BG_SIDEBAR, foreground=TEXT_MUTED, padding=[10, 5])
    style.map("TNotebook.Tab", background=[("selected", BG_CARD)], foreground=[("selected", TEXT_PRIMARY)])


class Card(tk.Canvas):
    """
    A custom widget that renders a vector card container with rounded borders.
    """
    def __init__(self, parent, width, height, bg_color=BG_CARD, border_color=BORDER, radius=12, **kwargs):
        super().__init__(parent, width=width, height=height, bg=BG_MAIN, bd=0, highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.border_color = border_color
        self.radius = radius
        self.draw_card()
        self.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        self.width = event.width
        self.height = event.height
        self.draw_card()

    def draw_card(self):
        self.delete("all")
        # Draw background rounded rect
        draw_rounded_rect(self, 2, 2, self.width - 2, self.height - 2, self.radius, fill=self.bg_color, outline=self.border_color, width=1)


class CircularGauge(tk.Canvas):
    """
    A custom radial dial drawn on canvas, representing the financial health score.
    """
    def __init__(self, parent, size=150, **kwargs):
        super().__init__(parent, width=size, height=size, bg=BG_CARD, bd=0, highlightthickness=0, **kwargs)
        self.size = size
        self.score = 0
        self.status = "N/A"
        self.color = TEXT_MUTED
        self.draw_gauge()

    def set_score(self, score, status, color):
        self.score = score
        self.status = status
        self.color = color
        self.draw_gauge()

    def draw_gauge(self):
        self.delete("all")
        
        # Geometry constants
        padding = 15
        width = 12
        r = self.size / 2
        
        # Draw background track (270 degrees arc from 225 to -45)
        self.create_arc(
            padding, padding, self.size - padding, self.size - padding,
            start=-45, extent=270, style="arc", outline="#2a2b36", width=width
        )
        
        # Draw active progress track based on score (extent = (score / 100) * 270)
        extent = (self.score / 100.0) * 270
        # Extent is negative to draw clockwise
        self.create_arc(
            padding, padding, self.size - padding, self.size - padding,
            start=225, extent=-extent, style="arc", outline=self.color, width=width
        )
        
        # Display health score digits in the center
        self.create_text(
            r, r - 12,
            text=str(self.score),
            fill=TEXT_PRIMARY,
            font=FONT_SCORE
        )
        
        # Display health rating status below the digits
        self.create_text(
            r, r + 15,
            text=self.status,
            fill=self.color,
            font=FONT_BODY_BOLD
        )
        
        # Small /100 indicator
        self.create_text(
            r, r + 35,
            text="Health Score",
            fill=TEXT_MUTED,
            font=FONT_SMALL
        )
