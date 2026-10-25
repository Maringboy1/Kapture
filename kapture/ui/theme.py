from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QApplication

ACCENTS = {
    "blue": "#3b82f6",
    "violet": "#8b5cf6",
    "green": "#22c55e",
    "orange": "#f97316",
    "red": "#ef4444",
    "cyan": "#06b6d4",
}

DARK = {
    "bg": "rgba(18, 20, 28, 0.88)",
    "bg2": "rgba(26, 29, 39, 0.92)",
    "card": "rgba(34, 38, 52, 0.9)",
    "border": "rgba(255,255,255,0.08)",
    "text": "#f5f7fa",
    "muted": "#9aa4b2",
    "hover": "rgba(255,255,255,0.06)",
}

LIGHT = {
    "bg": "rgba(248, 249, 252, 0.92)",
    "bg2": "rgba(255,255,255,0.95)",
    "card": "rgba(255,255,255,0.98)",
    "border": "rgba(0,0,0,0.08)",
    "text": "#1a1d24",
    "muted": "#5b6472",
    "hover": "rgba(0,0,0,0.05)",
}


def apply_app_style(app, cfg):
    app.setStyle("Fusion")
    font = QFont("Inter", 10)
    if font.family() != "Inter":
        font = QFont("Sans Serif", 10)
    app.setFont(font)
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(24, 26, 34))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(245, 247, 250))
    palette.setColor(QPalette.ColorRole.Base, QColor(30, 33, 44))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(36, 40, 54))
    palette.setColor(QPalette.ColorRole.Text, QColor(245, 247, 250))
    palette.setColor(QPalette.ColorRole.Button, QColor(36, 40, 54))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(245, 247, 250))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(cfg.get("ui", "accent", default="#3b82f6")))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)


def qss(cfg):
    accent = cfg.get("ui", "accent", default="#3b82f6")
    t = DARK if cfg.get("ui", "theme", default="dark") == "dark" else LIGHT
    return f"""
    QWidget {{ color: {t['text']}; font-family: Inter, 'Sans Serif'; font-size: 10pt; }}
    QFrame#card {{ background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {t['bg2']}, stop:1 {t['card']}); border: 1px solid {t['border']}; border-radius: 18px; }}
    QPushButton {{
        background: {t['card']}; border: 1px solid {t['border']}; border-radius: 10px;
        padding: 8px 14px; color: {t['text']};
    }}
    QPushButton:hover {{ background: {t['hover']}; }}
    QPushButton#primary {{
        background: {accent}; border: none; color: white; font-weight: 600;
    }}
    QPushButton#primary:hover {{ background: #2563eb; }}
    QPushButton#ghost {{ background: transparent; border: none; }}
    QPushButton#ghost:hover {{ background: {t['hover']}; }}
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox, QDoubleSpinBox {{
        background: {t['bg2']}; border: 1px solid {t['border']}; border-radius: 8px;
        padding: 6px 10px; color: {t['text']};
    }}
    QComboBox::drop-down {{ border: none; width: 20px; }}
    QTabBar::tab {{ background: transparent; padding: 8px 16px; border-radius: 8px; color: {t['muted']}; }}
    QTabBar::tab:selected {{ color: {t['text']}; background: {t['hover']}; }}
    QSlider::groove:horizontal {{ height: 4px; background: {t['border']}; border-radius: 2px; }}
    QSlider::handle:horizontal {{ width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; background: {accent}; }}
    QCheckBox {{ spacing: 8px; }}
    QScrollBar:vertical {{ background: transparent; width: 8px; }}
    QScrollBar::handle:vertical {{ background: {t['border']}; border-radius: 4px; min-height: 20px; }}
    QLabel#muted {{ color: {t['muted']}; }}
    QLabel#title {{ font-size: 15pt; font-weight: 700; }}
    QLabel#subtitle {{ color: {t['muted']}; font-size: 9pt; }}
    """
