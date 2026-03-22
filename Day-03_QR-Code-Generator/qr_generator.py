"""Day 03 QR Code Generator - Tkinter desktop app."""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import qrcode
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q

try:
    from qrcode.image.svg import SvgPathImage

    SVG_AVAILABLE = True
except Exception:
    SVG_AVAILABLE = False
    SvgPathImage = None

from PIL import Image, ImageDraw, ImageTk
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText


APP_TITLE = "Day 03 - QR Code Generator"
PROFILE_PATH = Path(__file__).with_name("profile.json")

DEFAULTS = {
    "payload_type": "Plain",
    "payload_text": "",
    "url": "",
    "wifi_ssid": "",
    "wifi_password": "",
    "wifi_security": "WPA",
    "email": "",
    "email_subject": "",
    "email_body": "",
    "sms_number": "",
    "sms_body": "",
    "vcard_name": "",
    "vcard_phone": "",
    "vcard_email": "",
    "box_size": 10,
    "border": 4,
    "error_correction": "M",
    "fill_color": "#0b0f14",
    "back_color": "#ffffff",
    "use_logo": False,
    "logo_path": "",
    "logo_ratio": 0.22,
    "history": [],
}

ERROR_LEVELS = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}


@dataclass
class HistoryItem:
    label: str
    payload_type: str
    payload: dict[str, Any]


class QRApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1100x720")
        self.root.minsize(980, 640)
        self.root.configure(bg="#0f141a")

        self.config_data = self.load_profile()
        self.history: list[HistoryItem] = []
        for item in self.config_data.get("history", []):
            if isinstance(item, dict):
                self.history.append(
                    HistoryItem(
                        label=item.get("label", "Untitled"),
                        payload_type=item.get("payload_type", "Plain"),
                        payload=item.get("payload", {}),
                    )
                )

        self.current_image: Optional[Image.Image] = None
        self.current_photo: Optional[ImageTk.PhotoImage] = None
        self.current_payload: str = ""

        self.build_style()
        self.build_layout()
        self.apply_config_to_ui()
        self.render_payload_fields()
        self.refresh_history_list()
        self.update_preview()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_style(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TFrame", background="#0f141a")
        style.configure("TLabel", background="#0f141a", foreground="#e6edf3", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#f0f6fc")
        style.configure("Sub.TLabel", font=("Segoe UI", 11, "bold"), foreground="#c9d1d9")
        style.configure("TButton", font=("Segoe UI", 10, "bold"))
        style.configure("TEntry", fieldbackground="#0b1016", foreground="#e6edf3")
        style.configure("TCombobox", fieldbackground="#0b1016", foreground="#e6edf3")
        style.configure("TCheckbutton", background="#0f141a", foreground="#e6edf3")
        style.map("TButton", background=[("active", "#2d3748")])

    def build_layout(self) -> None:
        self.header = ttk.Label(self.root, text="QR Code Generator", style="Header.TLabel")
        self.header.pack(pady=12)

        self.main = ttk.Frame(self.root)
        self.main.pack(fill="both", expand=True, padx=16, pady=8)

        self.left = ttk.Frame(self.main)
        self.left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.right = ttk.Frame(self.main)
        self.right.pack(side="right", fill="y")

        self.build_payload_section()
        self.build_options_section()
        self.build_logo_section()
        self.build_action_section()
        self.build_history_section()

        self.build_preview_section()

    def build_payload_section(self) -> None:
        card = ttk.Frame(self.left)
        card.pack(fill="x", pady=6)

        ttk.Label(card, text="Payload", style="Sub.TLabel").pack(anchor="w")

        top = ttk.Frame(card)
        top.pack(fill="x", pady=4)

        ttk.Label(top, text="Type:").pack(side="left")
        self.payload_type = tk.StringVar(value=self.config_data.get("payload_type", "Plain"))
        self.payload_combo = ttk.Combobox(
            top,
            values=["Plain", "URL", "WiFi", "Email", "SMS", "vCard"],
            state="readonly",
            textvariable=self.payload_type,
            width=18,
        )
        self.payload_combo.pack(side="left", padx=6)
        self.payload_combo.bind("<<ComboboxSelected>>", lambda _e: self.render_payload_fields())

        self.payload_frame = ttk.Frame(card)
        self.payload_frame.pack(fill="x", pady=4)

        self.payload_text = ScrolledText(card, height=5, wrap="word")
        self.payload_text.pack(fill="x", pady=6)

    def build_options_section(self) -> None:
        card = ttk.Frame(self.left)
        card.pack(fill="x", pady=6)
        ttk.Label(card, text="Options", style="Sub.TLabel").pack(anchor="w")

        grid = ttk.Frame(card)
        grid.pack(fill="x", pady=4)

        ttk.Label(grid, text="Error correction:").grid(row=0, column=0, sticky="w")
        self.error_correction = tk.StringVar(value=self.config_data.get("error_correction", "M"))
        self.error_combo = ttk.Combobox(
            grid, values=["L", "M", "Q", "H"], state="readonly", textvariable=self.error_correction, width=6
        )
        self.error_combo.grid(row=0, column=1, sticky="w", padx=4)

        ttk.Label(grid, text="Box size:").grid(row=0, column=2, sticky="w", padx=(16, 0))
        self.box_size = tk.IntVar(value=int(self.config_data.get("box_size", 10)))
        self.box_scale = ttk.Scale(grid, from_=3, to=20, orient="horizontal", variable=self.box_size)
        self.box_scale.grid(row=0, column=3, sticky="we", padx=6)

        ttk.Label(grid, text="Border:").grid(row=1, column=0, sticky="w", pady=4)
        self.border = tk.IntVar(value=int(self.config_data.get("border", 4)))
        self.border_scale = ttk.Scale(grid, from_=1, to=10, orient="horizontal", variable=self.border)
        self.border_scale.grid(row=1, column=1, sticky="we", padx=4)

        ttk.Label(grid, text="Fill:").grid(row=1, column=2, sticky="w", padx=(16, 0))
        self.fill_color = tk.StringVar(value=self.config_data.get("fill_color", "#0b0f14"))
        self.fill_entry = ttk.Entry(grid, textvariable=self.fill_color, width=10)
        self.fill_entry.grid(row=1, column=3, sticky="w", padx=4)
        self.fill_btn = ttk.Button(grid, text="Pick", command=lambda: self.pick_color(self.fill_color))
        self.fill_btn.grid(row=1, column=4, sticky="w")

        ttk.Label(grid, text="Background:").grid(row=2, column=0, sticky="w", pady=4)
        self.back_color = tk.StringVar(value=self.config_data.get("back_color", "#ffffff"))
        self.back_entry = ttk.Entry(grid, textvariable=self.back_color, width=10)
        self.back_entry.grid(row=2, column=1, sticky="w", padx=4)
        self.back_btn = ttk.Button(grid, text="Pick", command=lambda: self.pick_color(self.back_color))
        self.back_btn.grid(row=2, column=2, sticky="w")

        grid.columnconfigure(3, weight=1)

    def build_logo_section(self) -> None:
        card = ttk.Frame(self.left)
        card.pack(fill="x", pady=6)
        ttk.Label(card, text="Logo", style="Sub.TLabel").pack(anchor="w")

        row = ttk.Frame(card)
        row.pack(fill="x", pady=4)

        self.use_logo = tk.BooleanVar(value=bool(self.config_data.get("use_logo", False)))
        ttk.Checkbutton(row, text="Embed logo", variable=self.use_logo).pack(side="left")

        self.logo_path = tk.StringVar(value=self.config_data.get("logo_path", ""))
        logo_entry = ttk.Entry(row, textvariable=self.logo_path)
        logo_entry.pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(row, text="Browse", command=self.pick_logo).pack(side="left")

        ratio_row = ttk.Frame(card)
        ratio_row.pack(fill="x", pady=4)
        ttk.Label(ratio_row, text="Logo size ratio:").pack(side="left")
        self.logo_ratio = tk.DoubleVar(value=float(self.config_data.get("logo_ratio", 0.22)))
        self.logo_scale = ttk.Scale(ratio_row, from_=0.12, to=0.4, orient="horizontal", variable=self.logo_ratio)
        self.logo_scale.pack(side="left", fill="x", expand=True, padx=6)
        ttk.Label(ratio_row, text="(auto uses H for best scan)").pack(side="left")

    def build_action_section(self) -> None:
        card = ttk.Frame(self.left)
        card.pack(fill="x", pady=6)
        ttk.Label(card, text="Actions", style="Sub.TLabel").pack(anchor="w")

        row = ttk.Frame(card)
        row.pack(fill="x", pady=4)

        ttk.Button(row, text="Generate", command=self.generate).pack(side="left", padx=4)
        ttk.Button(row, text="Save PNG", command=self.save_png).pack(side="left", padx=4)
        self.save_svg_btn = ttk.Button(row, text="Save SVG", command=self.save_svg)
        self.save_svg_btn.pack(side="left", padx=4)
        if not SVG_AVAILABLE:
            self.save_svg_btn.configure(state="disabled")

        ttk.Button(row, text="Copy data", command=self.copy_data).pack(side="left", padx=4)
        ttk.Button(row, text="Reset", command=self.reset).pack(side="left", padx=4)

        self.status = ttk.Label(card, text="Ready", foreground="#9fb3c8")
        self.status.pack(anchor="w", pady=4)

    def build_history_section(self) -> None:
        card = ttk.Frame(self.left)
        card.pack(fill="both", expand=True, pady=6)
        ttk.Label(card, text="History", style="Sub.TLabel").pack(anchor="w")

        frame = ttk.Frame(card)
        frame.pack(fill="both", expand=True)

        self.history_list = tk.Listbox(frame, height=6, bg="#0b1016", fg="#e6edf3")
        self.history_list.pack(side="left", fill="both", expand=True)
        self.history_list.bind("<<ListboxSelect>>", self.on_history_select)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.history_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.history_list.config(yscrollcommand=scrollbar.set)

    def build_preview_section(self) -> None:
        card = ttk.Frame(self.right)
        card.pack(fill="y", padx=6, pady=6)
        ttk.Label(card, text="Preview", style="Sub.TLabel").pack(anchor="w")

        self.preview_canvas = tk.Canvas(card, width=360, height=360, bg="#ffffff", highlightthickness=0)
        self.preview_canvas.pack(pady=8)

        self.preview_info = ttk.Label(card, text="No QR generated yet.")
        self.preview_info.pack(anchor="w")

        ttk.Label(card, text="Tip: bigger box size = higher resolution.\nUse error correction H if you embed a logo.").pack(
            anchor="w", pady=6
        )

    def apply_config_to_ui(self) -> None:
        self.payload_text.delete("1.0", "end")
        self.payload_text.insert("1.0", self.config_data.get("payload_text", ""))
        self.payload_type.set(self.config_data.get("payload_type", "Plain"))

        self.url_var = tk.StringVar(value=self.config_data.get("url", ""))
        self.wifi_ssid = tk.StringVar(value=self.config_data.get("wifi_ssid", ""))
        self.wifi_password = tk.StringVar(value=self.config_data.get("wifi_password", ""))
        self.wifi_security = tk.StringVar(value=self.config_data.get("wifi_security", "WPA"))
        self.email_var = tk.StringVar(value=self.config_data.get("email", ""))
        self.email_subject = tk.StringVar(value=self.config_data.get("email_subject", ""))
        self.email_body = tk.StringVar(value=self.config_data.get("email_body", ""))
        self.sms_number = tk.StringVar(value=self.config_data.get("sms_number", ""))
        self.sms_body = tk.StringVar(value=self.config_data.get("sms_body", ""))
        self.vcard_name = tk.StringVar(value=self.config_data.get("vcard_name", ""))
        self.vcard_phone = tk.StringVar(value=self.config_data.get("vcard_phone", ""))
        self.vcard_email = tk.StringVar(value=self.config_data.get("vcard_email", ""))

    def render_payload_fields(self) -> None:
        for child in self.payload_frame.winfo_children():
            child.destroy()

        payload_type = self.payload_type.get()
        if payload_type == "Plain":
            ttk.Label(self.payload_frame, text="Text:").pack(anchor="w")
            self.payload_text.configure(height=6)
        elif payload_type == "URL":
            ttk.Label(self.payload_frame, text="URL:").pack(anchor="w")
            entry = ttk.Entry(self.payload_frame, textvariable=self.url_var)
            entry.pack(fill="x")
            self.payload_text.configure(height=4)
        elif payload_type == "WiFi":
            ttk.Label(self.payload_frame, text="Network name (SSID):").pack(anchor="w")
            ttk.Entry(self.payload_frame, textvariable=self.wifi_ssid).pack(fill="x")
            ttk.Label(self.payload_frame, text="Password:").pack(anchor="w", pady=(4, 0))
            ttk.Entry(self.payload_frame, textvariable=self.wifi_password).pack(fill="x")
            ttk.Label(self.payload_frame, text="Security:").pack(anchor="w", pady=(4, 0))
            ttk.Combobox(self.payload_frame, values=["WPA", "WEP", "nopass"], textvariable=self.wifi_security).pack(
                fill="x"
            )
            self.payload_text.configure(height=4)
        elif payload_type == "Email":
            ttk.Label(self.payload_frame, text="Email:").pack(anchor="w")
            ttk.Entry(self.payload_frame, textvariable=self.email_var).pack(fill="x")
            ttk.Label(self.payload_frame, text="Subject:").pack(anchor="w", pady=(4, 0))
            ttk.Entry(self.payload_frame, textvariable=self.email_subject).pack(fill="x")
            ttk.Label(self.payload_frame, text="Body:").pack(anchor="w", pady=(4, 0))
            ttk.Entry(self.payload_frame, textvariable=self.email_body).pack(fill="x")
            self.payload_text.configure(height=4)
        elif payload_type == "SMS":
            ttk.Label(self.payload_frame, text="Phone number:").pack(anchor="w")
            ttk.Entry(self.payload_frame, textvariable=self.sms_number).pack(fill="x")
            ttk.Label(self.payload_frame, text="Message:").pack(anchor="w", pady=(4, 0))
            ttk.Entry(self.payload_frame, textvariable=self.sms_body).pack(fill="x")
            self.payload_text.configure(height=4)
        elif payload_type == "vCard":
            ttk.Label(self.payload_frame, text="Name:").pack(anchor="w")
            ttk.Entry(self.payload_frame, textvariable=self.vcard_name).pack(fill="x")
            ttk.Label(self.payload_frame, text="Phone:").pack(anchor="w", pady=(4, 0))
            ttk.Entry(self.payload_frame, textvariable=self.vcard_phone).pack(fill="x")
            ttk.Label(self.payload_frame, text="Email:").pack(anchor="w", pady=(4, 0))
            ttk.Entry(self.payload_frame, textvariable=self.vcard_email).pack(fill="x")
            self.payload_text.configure(height=4)

    def build_payload(self) -> str:
        payload_type = self.payload_type.get()
        if payload_type == "Plain":
            return self.payload_text.get("1.0", "end").strip()
        if payload_type == "URL":
            url = self.url_var.get().strip()
            if url and not re.match(r"^https?://", url):
                url = "https://" + url
            return url
        if payload_type == "WiFi":
            ssid = self.wifi_ssid.get().strip()
            password = self.wifi_password.get().strip()
            security = self.wifi_security.get().strip() or "WPA"
            if not ssid:
                return ""
            return f"WIFI:T:{security};S:{ssid};P:{password};;"
        if payload_type == "Email":
            email = self.email_var.get().strip()
            subject = self.email_subject.get().strip()
            body = self.email_body.get().strip()
            if not email:
                return ""
            query = []
            if subject:
                query.append(f"subject={subject}")
            if body:
                query.append(f"body={body}")
            query_text = ("?" + "&".join(query)) if query else ""
            return f"mailto:{email}{query_text}"
        if payload_type == "SMS":
            number = self.sms_number.get().strip()
            body = self.sms_body.get().strip()
            if not number:
                return ""
            if body:
                return f"SMSTO:{number}:{body}"
            return f"SMSTO:{number}"
        if payload_type == "vCard":
            name = self.vcard_name.get().strip()
            phone = self.vcard_phone.get().strip()
            email = self.vcard_email.get().strip()
            if not name and not phone and not email:
                return ""
            lines = ["BEGIN:VCARD", "VERSION:3.0"]
            if name:
                lines.append(f"FN:{name}")
            if phone:
                lines.append(f"TEL:{phone}")
            if email:
                lines.append(f"EMAIL:{email}")
            lines.append("END:VCARD")
            return "\n".join(lines)
        return ""

    def generate(self) -> None:
        payload = self.build_payload()
        if not payload:
            messagebox.showwarning("Missing data", "Please enter payload data first.")
            return

        error_key = self.error_correction.get()
        if self.use_logo.get():
            error_key = "H"

        qr = qrcode.QRCode(
            error_correction=ERROR_LEVELS.get(error_key, ERROR_CORRECT_M),
            box_size=int(self.box_size.get()),
            border=int(self.border.get()),
        )
        qr.add_data(payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color=self.fill_color.get(), back_color=self.back_color.get()).convert("RGBA")

        img = self.apply_logo(img)
        self.current_image = img
        self.current_payload = payload
        self.update_preview()
        self.status.configure(text=f"Generated ({len(payload)} chars)")

        self.add_history(payload)
        self.save_profile()

    def apply_logo(self, img: Image.Image) -> Image.Image:
        if not self.use_logo.get():
            return img
        path = Path(self.logo_path.get())
        if not path.exists():
            self.status.configure(text="Logo path not found; skipped.")
            return img
        try:
            logo = Image.open(path).convert("RGBA")
        except Exception:
            self.status.configure(text="Invalid logo image; skipped.")
            return img

        ratio = float(self.logo_ratio.get())
        target = max(40, int(min(img.size) * ratio))
        logo = logo.resize((target, target), Image.LANCZOS)

        # Draw a rounded white plate under the logo to improve contrast.
        plate = Image.new("RGBA", (target + 12, target + 12), (255, 255, 255, 0))
        draw = ImageDraw.Draw(plate)
        draw.rounded_rectangle(
            [0, 0, plate.size[0], plate.size[1]], radius=12, fill=(255, 255, 255, 235)
        )
        img.paste(plate, ((img.size[0] - plate.size[0]) // 2, (img.size[1] - plate.size[1]) // 2), plate)

        pos = ((img.size[0] - target) // 2, (img.size[1] - target) // 2)
        img.paste(logo, pos, logo)
        return img

    def update_preview(self) -> None:
        self.preview_canvas.delete("all")
        if not self.current_image:
            self.preview_info.configure(text="No QR generated yet.")
            return
        preview_size = 360
        img = self.current_image.copy()
        img.thumbnail((preview_size, preview_size), Image.NEAREST)
        self.current_photo = ImageTk.PhotoImage(img)
        self.preview_canvas.create_image(preview_size // 2, preview_size // 2, image=self.current_photo)
        self.preview_info.configure(text=f"Preview size: {img.size[0]}x{img.size[1]} px")

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
        self.status.configure(text=f"Saved PNG: {os.path.basename(filename)}")

    def save_svg(self) -> None:
        if not SVG_AVAILABLE:
            messagebox.showinfo("SVG not available", "SVG export is not available in this setup.")
            return
        payload = self.current_payload or self.build_payload()
        if not payload:
            messagebox.showinfo("Nothing to save", "Generate a QR code first.")
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".svg",
            filetypes=[("SVG", "*.svg")],
            initialfile=f"qr_{int(time.time())}.svg",
        )
        if not filename:
            return
        qr = qrcode.QRCode(error_correction=ERROR_LEVELS.get(self.error_correction.get(), ERROR_CORRECT_M))
        qr.add_data(payload)
        qr.make(fit=True)
        img = qr.make_image(image_factory=SvgPathImage)
        img.save(filename)
        self.status.configure(text=f"Saved SVG: {os.path.basename(filename)}")

    def copy_data(self) -> None:
        payload = self.current_payload or self.build_payload()
        if not payload:
            messagebox.showinfo("No data", "Nothing to copy yet.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(payload)
        self.status.configure(text="Payload copied to clipboard")

    def reset(self) -> None:
        self.payload_text.delete("1.0", "end")
        self.url_var.set("")
        self.wifi_ssid.set("")
        self.wifi_password.set("")
        self.wifi_security.set("WPA")
        self.email_var.set("")
        self.email_subject.set("")
        self.email_body.set("")
        self.sms_number.set("")
        self.sms_body.set("")
        self.vcard_name.set("")
        self.vcard_phone.set("")
        self.vcard_email.set("")
        self.current_image = None
        self.current_payload = ""
        self.update_preview()
        self.status.configure(text="Reset done")

    def pick_color(self, target: tk.StringVar) -> None:
        color = colorchooser.askcolor(initialcolor=target.get())
        if color[1]:
            target.set(color[1])

    def pick_logo(self) -> None:
        filename = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.webp")])
        if filename:
            self.logo_path.set(filename)
            self.use_logo.set(True)

    def add_history(self, payload: str) -> None:
        label = f"{self.payload_type.get()} - {payload[:32]}".strip()
        snapshot = self.snapshot_payload()
        self.history.insert(0, HistoryItem(label=label, payload_type=self.payload_type.get(), payload=snapshot))
        self.history = self.history[:20]
        self.refresh_history_list()

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "payload_text": self.payload_text.get("1.0", "end").strip(),
            "url": self.url_var.get().strip(),
            "wifi_ssid": self.wifi_ssid.get().strip(),
            "wifi_password": self.wifi_password.get().strip(),
            "wifi_security": self.wifi_security.get().strip(),
            "email": self.email_var.get().strip(),
            "email_subject": self.email_subject.get().strip(),
            "email_body": self.email_body.get().strip(),
            "sms_number": self.sms_number.get().strip(),
            "sms_body": self.sms_body.get().strip(),
            "vcard_name": self.vcard_name.get().strip(),
            "vcard_phone": self.vcard_phone.get().strip(),
            "vcard_email": self.vcard_email.get().strip(),
        }

    def refresh_history_list(self) -> None:
        self.history_list.delete(0, "end")
        for item in self.history:
            self.history_list.insert("end", item.label)

    def on_history_select(self, _event: tk.Event) -> None:
        if not self.history_list.curselection():
            return
        index = self.history_list.curselection()[0]
        item = self.history[index]
        self.payload_type.set(item.payload_type)
        self.render_payload_fields()
        payload = item.payload
        self.payload_text.delete("1.0", "end")
        self.payload_text.insert("1.0", payload.get("payload_text", ""))
        self.url_var.set(payload.get("url", ""))
        self.wifi_ssid.set(payload.get("wifi_ssid", ""))
        self.wifi_password.set(payload.get("wifi_password", ""))
        self.wifi_security.set(payload.get("wifi_security", "WPA"))
        self.email_var.set(payload.get("email", ""))
        self.email_subject.set(payload.get("email_subject", ""))
        self.email_body.set(payload.get("email_body", ""))
        self.sms_number.set(payload.get("sms_number", ""))
        self.sms_body.set(payload.get("sms_body", ""))
        self.vcard_name.set(payload.get("vcard_name", ""))
        self.vcard_phone.set(payload.get("vcard_phone", ""))
        self.vcard_email.set(payload.get("vcard_email", ""))
        self.generate()

    def save_profile(self) -> None:
        data = {
            "payload_type": self.payload_type.get(),
            "payload_text": self.payload_text.get("1.0", "end").strip(),
            "url": self.url_var.get().strip(),
            "wifi_ssid": self.wifi_ssid.get().strip(),
            "wifi_password": self.wifi_password.get().strip(),
            "wifi_security": self.wifi_security.get().strip(),
            "email": self.email_var.get().strip(),
            "email_subject": self.email_subject.get().strip(),
            "email_body": self.email_body.get().strip(),
            "sms_number": self.sms_number.get().strip(),
            "sms_body": self.sms_body.get().strip(),
            "vcard_name": self.vcard_name.get().strip(),
            "vcard_phone": self.vcard_phone.get().strip(),
            "vcard_email": self.vcard_email.get().strip(),
            "box_size": int(self.box_size.get()),
            "border": int(self.border.get()),
            "error_correction": self.error_correction.get(),
            "fill_color": self.fill_color.get(),
            "back_color": self.back_color.get(),
            "use_logo": self.use_logo.get(),
            "logo_path": self.logo_path.get(),
            "logo_ratio": float(self.logo_ratio.get()),
            "history": [
                {
                    "label": item.label,
                    "payload_type": item.payload_type,
                    "payload": item.payload,
                }
                for item in self.history
            ],
        }
        try:
            PROFILE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def load_profile(self) -> dict[str, Any]:
        if not PROFILE_PATH.exists():
            return dict(DEFAULTS)
        try:
            data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return dict(DEFAULTS)
        merged = dict(DEFAULTS)
        merged.update(data)
        return merged

    def on_close(self) -> None:
        self.save_profile()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = QRApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()