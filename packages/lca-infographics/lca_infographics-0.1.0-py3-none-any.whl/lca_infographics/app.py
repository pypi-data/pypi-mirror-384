import os, sys, json, pathlib, argparse
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

def load_json_or_empty(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:
        return {}, str(e)

class LCAWindow(QWidget):
    def __init__(self, json_path, mode="research"):
        super().__init__()
        self.json_path = json_path
        self.mode = mode
        self.setWindowTitle("LCA Infographics")
        self.resize(900, 600)

        layout = QVBoxLayout(self)
        self.info = QLabel(f"JSON: {json_path or '(embedded sample)'}  |  mode={mode}")
        self.info.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.info)

        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.reload_btn = QPushButton("Reload JSON and Replot")
        self.reload_btn.clicked.connect(self.plot_from_json)
        layout.addWidget(self.reload_btn)

        self.export_btn = QPushButton("Export Chart as PNG")
        self.export_btn.clicked.connect(self.export_png)
        layout.addWidget(self.export_btn)

        self.plot_from_json()

        if self.mode == "research":
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.plot_from_json)
            self.timer.start(10000)

    def plot_from_json(self):
        if self.json_path and os.path.exists(self.json_path):
            data, err = load_json_or_empty(self.json_path)
        else:
            bundle = pathlib.Path(__file__).with_name("sample_data.json")
            data, err = load_json_or_empty(str(bundle))

        if err:
            QMessageBox.warning(self, "Load error", f"Failed to load JSON:\n{err}")
            data = {}

        totals = data.get("totals", {"CO2e": 120, "Cost": 300, "Energy": 600})
        labels = list(totals.keys())
        values = [totals[k] for k in labels]

        ax = self.figure.subplots()
        ax.clear()
        ax.bar(labels, values)
        ax.set_title("LCA Totals")
        ax.set_ylabel("Value (arbitrary units)")
        self.canvas.draw_idle()

    def export_png(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save PNG", "lca_chart.png", "PNG Images (*.png)")
        if not path:
            return
        try:
            self.figure.savefig(path, dpi=150, bbox_inches="tight")
            QMessageBox.information(self, "Saved", f"Chart saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save PNG:\n{e}")

def main():
    parser = argparse.ArgumentParser(description="LCA Infographics Viewer")
    parser.add_argument("--json", help="Path to lca_results.json", default=None)
    parser.add_argument("--mode", choices=["normal", "research"], default="research")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 9))
    w = LCAWindow(args.json, mode=args.mode)
    w.show()
    sys.exit(app.exec_())
