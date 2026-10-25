from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

import customtkinter as ctk

from algorithms.huffman import Node, analyze, encode
from formats.huf_file import compress, decompress

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
except ImportError:
    FigureCanvasTkAgg = None
    Figure = None


class HuffmanStudio(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("HuffLab — Compression Workbench")
        self.geometry("1180x820")
        self.minsize(900, 650)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self._frequencies: dict[int, int] = {}
        self._codes: dict[int, str] = {}
        self._tree: Node | None = None
        self._source_bytes = b""
        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self, text="HuffLab", font=ctk.CTkFont(size=28, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=24, pady=(18, 4)
        )
        ctk.CTkLabel(
            self, text="Local compression workbench · UTF-8 text / Huffman-coded bytes",
            text_color="gray70",
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(56, 12))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 18))
        body.grid_columnconfigure((0, 1), weight=1)
        body.grid_rowconfigure(1, weight=1)

        source_panel = ctk.CTkFrame(body)
        source_panel.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 8))
        source_panel.grid_columnconfigure(0, weight=1)
        source_panel.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(source_panel, text="SOURCE TEXT", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=14, pady=(14, 6)
        )
        self.textbox = ctk.CTkTextbox(source_panel, wrap="word", font=ctk.CTkFont(size=14))
        self.textbox.grid(row=1, column=0, sticky="nsew", padx=12, pady=8)
        self.textbox.insert("1.0", "BANANA BANDANA\nHUFFMAN COMPRESSION DEMO")
        actions = ctk.CTkFrame(source_panel, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=10, pady=(4, 12))
        for column in range(3):
            actions.grid_columnconfigure(column, weight=1)
        ctk.CTkButton(actions, text="Open text", command=self.open_text).grid(
            row=0, column=0, padx=4, sticky="ew"
        )
        ctk.CTkButton(actions, text="Analyse", command=self.analyze_text).grid(
            row=0, column=1, padx=4, sticky="ew"
        )
        ctk.CTkButton(actions, text="Save .huf", command=self.save_compressed).grid(
            row=0, column=2, padx=4, sticky="ew"
        )
        ctk.CTkButton(actions, text="Open .huf", command=self.open_compressed).grid(
            row=1, column=0, columnspan=3, padx=4, pady=(8, 0), sticky="ew"
        )

        right = ctk.CTkFrame(body)
        right.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(8, 0))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(2, weight=1)
        stats = ctk.CTkFrame(right, fg_color="transparent")
        stats.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        stats.grid_columnconfigure((0, 1, 2), weight=1)
        self.stat_labels: dict[str, ctk.CTkLabel] = {}
        for index, (key, title) in enumerate(
            (("original", "Original"), ("encoded", "Encoded bits"), ("savings", "Savings vs raw"))
        ):
            card = ctk.CTkFrame(stats)
            card.grid(row=0, column=index, sticky="ew", padx=4)
            ctk.CTkLabel(card, text=title, text_color="gray70").pack(pady=(8, 0))
            label = ctk.CTkLabel(card, text="—", font=ctk.CTkFont(size=18, weight="bold"))
            label.pack(pady=(0, 8))
            self.stat_labels[key] = label

        self.chart_host = ctk.CTkFrame(right)
        self.chart_host.grid(row=1, column=0, sticky="nsew", padx=10, pady=8)
        self._build_chart()

        details = ctk.CTkTabview(right)
        details.grid(row=2, column=0, sticky="nsew", padx=10, pady=(4, 10))
        code_tab = details.add("Codes")
        tree_tab = details.add("Huffman tree")
        code_tab.grid_columnconfigure(0, weight=1)
        code_tab.grid_rowconfigure(0, weight=1)
        self.code_table = ttk.Treeview(code_tab, columns=("byte", "frequency", "code"), show="headings")
        for column, title, width in (
            ("byte", "Byte / character", 150), ("frequency", "Frequency", 90), ("code", "Code", 260)
        ):
            self.code_table.heading(column, text=title)
            self.code_table.column(column, width=width, anchor="w")
        self.code_table.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.tree_canvas = tk.Canvas(tree_tab, bg="#202020", highlightthickness=0)
        self.tree_canvas.pack(fill="both", expand=True, padx=6, pady=6)
        self.tree_canvas.bind("<Configure>", lambda _event: self._draw_tree())

    def _build_chart(self) -> None:
        if Figure is None or FigureCanvasTkAgg is None:
            ctk.CTkLabel(
                self.chart_host, text="Install matplotlib to view the frequency chart."
            ).pack(padx=10, pady=20)
            return
        self.figure = Figure(figsize=(5, 2.1), dpi=90, facecolor="#242424")
        self.axes = self.figure.add_subplot(111)
        self.axes.set_facecolor("#242424")
        self.axes.tick_params(colors="#dddddd", labelsize=8)
        self.axes.set_title("Byte frequency", color="#eeeeee", fontsize=10)
        self.chart = FigureCanvasTkAgg(self.figure, master=self.chart_host)
        self.chart.get_tk_widget().pack(fill="both", expand=True)

    @staticmethod
    def _display_byte(value: int) -> str:
        char = bytes([value]).decode("latin-1")
        return repr(char) if char.isprintable() and not char.isspace() else f"0x{value:02X}"

    def analyze_text(self) -> None:
        text = self.textbox.get("1.0", "end-1c")
        self._source_bytes = text.encode("utf-8")
        self._frequencies, self._tree, self._codes = analyze(self._source_bytes)
        encoded, bit_count = encode(self._source_bytes, self._codes)
        self.stat_labels["original"].configure(text=f"{len(self._source_bytes)} B")
        self.stat_labels["encoded"].configure(text=f"{bit_count:,}")
        raw_bits = len(self._source_bytes) * 8
        savings = (raw_bits - bit_count) / raw_bits * 100 if raw_bits else 0
        self.stat_labels["savings"].configure(text=f"{savings:.1f}%" if raw_bits else "—")
        for item in self.code_table.get_children():
            self.code_table.delete(item)
        for symbol, code in sorted(self._codes.items()):
            self.code_table.insert(
                "", "end",
                values=(self._display_byte(symbol), self._frequencies[symbol], code),
            )
        self._draw_chart()
        self._draw_tree()
        self.title(f"HuffLab — {len(encoded)} encoded bytes (payload only)")

    def _draw_chart(self) -> None:
        if Figure is None or not hasattr(self, "axes"):
            return
        self.axes.clear()
        self.axes.set_facecolor("#242424")
        self.axes.tick_params(colors="#dddddd", labelsize=8)
        self.axes.set_title("Byte frequency", color="#eeeeee", fontsize=10)
        if self._frequencies:
            symbols = sorted(self._frequencies)
            labels = [self._display_byte(symbol) for symbol in symbols]
            self.axes.bar(range(len(symbols)), [self._frequencies[s] for s in symbols], color="#4f9cf9")
            if len(symbols) <= 32:
                self.axes.set_xticks(range(len(symbols)), labels, rotation=45, ha="right")
            else:
                self.axes.set_xlabel(f"{len(symbols)} distinct bytes", color="#dddddd")
        self.figure.tight_layout()
        self.chart.draw_idle()

    def _draw_tree(self) -> None:
        if not hasattr(self, "tree_canvas"):
            return
        canvas = self.tree_canvas
        canvas.delete("all")
        if self._tree is None:
            return
        leaves: list[Node] = []

        def collect(node: Node) -> None:
            if node.is_leaf:
                leaves.append(node)
            else:
                assert node.left is not None and node.right is not None
                collect(node.left)
                collect(node.right)

        collect(self._tree)
        positions: dict[int, tuple[float, float]] = {}
        width = max(canvas.winfo_width(), 300)
        height = max(canvas.winfo_height(), 180)
        max_depth = max((len(self._codes[symbol]) for symbol in self._codes), default=0)
        leaf_x = {leaf.symbol: (i + 0.5) * width / len(leaves) for i, leaf in enumerate(leaves)}

        def place(node: Node, depth: int) -> float:
            if node.is_leaf:
                assert node.symbol is not None
                x = leaf_x[node.symbol]
            else:
                assert node.left is not None and node.right is not None
                x = (place(node.left, depth + 1) + place(node.right, depth + 1)) / 2
            y = 22 + depth * (height - 44) / max(max_depth, 1)
            positions[id(node)] = (x, y)
            return x

        place(self._tree, 0)

        def draw(node: Node) -> None:
            x, y = positions[id(node)]
            if not node.is_leaf:
                assert node.left is not None and node.right is not None
                for child, bit in ((node.left, "0"), (node.right, "1")):
                    cx, cy = positions[id(child)]
                    canvas.create_line(x, y + 10, cx, cy - 10, fill="#7892ad")
                    canvas.create_text((x + cx) / 2, (y + cy) / 2, text=bit, fill="#bbbbbb")
                    draw(child)
            label = self._display_byte(node.symbol) if node.is_leaf and node.symbol is not None else str(node.frequency)
            canvas.create_oval(x - 18, y - 11, x + 18, y + 11, fill="#315f8d", outline="")
            canvas.create_text(x, y, text=label[:8], fill="white", font=("Segoe UI", 8))

        draw(self._tree)

    def open_text(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            messagebox.showerror("Could not open file", str(error))
            return
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", text)
        self.analyze_text()

    def save_compressed(self) -> None:
        self.analyze_text()
        path = filedialog.asksaveasfilename(
            defaultextension=".huf", filetypes=[("Huffman files", "*.huf")]
        )
        if not path:
            return
        try:
            result = compress(self._source_bytes)
            Path(path).write_bytes(result)
        except OSError as error:
            messagebox.showerror("Could not save file", str(error))
            return
        messagebox.showinfo(
            "Compression saved",
            f"Original: {len(self._source_bytes):,} bytes\n"
            f"Compressed file: {len(result):,} bytes\n"
            f"Change: {len(result) - len(self._source_bytes):+,} bytes",
        )

    def open_compressed(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Huffman files", "*.huf")])
        if not path:
            return
        try:
            restored = decompress(Path(path).read_bytes())
            text = restored.decode("utf-8")
        except (OSError, UnicodeError, ValueError) as error:
            messagebox.showerror("Could not restore file", str(error))
            return
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", text)
        self.analyze_text()


if __name__ == "__main__":
    HuffmanStudio().mainloop()
