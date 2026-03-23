"""Day 03 QR Code Generator - Simple Edition."""

from __future__ import annotations

import time
from pathlib import Path

import qrcode
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_TITLE = "Day 03 - QR Code Generator (Simple)"


class SimpleQRApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("720x520")
        self.root.minsize(640, 480)

        self.current_image: Image.Image | None = None
        self.current_photo: ImageTk.PhotoImage | None = None

        self.build_ui()

    def build_ui(self) -> None:
        wrapper = ttk.Frame(self.root, padding=16)
        wrapper.pack(fill="both", expand=True)

        ttk.Label(wrapper, text="QR Code Generator", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(wrapper, text="Paste text or URL, then generate.").pack(anchor="w", pady=(4, 12))

        ttk.Label(wrapper, text="Data:").pack(anchor="w")
        self.data_entry = ttk.Entry(wrapper)
        self.data_entry.pack(fill="x", pady=6)

        row = ttk.Frame(wrapper)
        row.pack(fill="x", pady=6)
        ttk.Label(row, text="Box size:").pack(side="left")
        self.box_size = tk.IntVar(value=10)
        ttk.Scale(row, from_=3, to=20, orient="horizontal", variable=self.box_size).pack(
            side="left", fill="x", expand=True, padx=8
        )

        buttons = ttk.Frame(wrapper)
        buttons.pack(fill="x", pady=8)
        ttk.Button(buttons, text="Generate", command=self.generate).pack(side="left")
        ttk.Button(buttons, text="Save PNG", command=self.save_png).pack(side="left", padx=6)
        ttk.Button(buttons, text="Clear", command=self.clear).pack(side="left")

        self.preview = tk.Canvas(wrapper, width=280, height=280, bg="#ffffff", highlightthickness=1)
        self.preview.pack(pady=10)

        self.status = ttk.Label(wrapper, text="Ready")
        self.status.pack(anchor="w")

    def generate(self) -> None:
        data = self.data_entry.get().strip()
        if not data:
            messagebox.showwarning("Missing data", "Please enter text or URL.")
            return

        qr = qrcode.QRCode(box_size=int(self.box_size.get()), border=4)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        self.current_image = img
        self.update_preview(img)
        self.status.configure(text=f"Generated ({len(data)} chars)")

    def update_preview(self, img: Image.Image) -> None:
        self.preview.delete("all")
        preview = img.copy()
        preview.thumbnail((280, 280), Image.NEAREST)
        self.current_photo = ImageTk.PhotoImage(preview)
        self.preview.create_image(140, 140, image=self.current_photo)

    def save_png(self) -> None:
        if not self.current_image:
            messagebox.showinfo("Nothing to save", "Generate a QR code first.")
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png")],
            initialfile=f"qr_{int(time.time())}.png",
        )
        if not filename:
            return
        self.current_image.save(filename)
        self.status.configure(text=f"Saved: {Path(filename).name}")

    def clear(self) -> None:
        self.data_entry.delete(0, "end")
        self.preview.delete("all")
        self.current_image = None
        self.status.configure(text="Cleared")


def main() -> None:
    root = tk.Tk()
    app = SimpleQRApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()