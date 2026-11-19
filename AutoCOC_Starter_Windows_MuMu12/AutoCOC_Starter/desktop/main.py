import tkinter as tk
from tkinter import ttk, messagebox
import requests, json, uuid, webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
API = CFG["api_url"].rstrip("/")
VERSION = CFG["version"]
DEVICE_ID = str(uuid.getnode())

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auto COC – MuMu Player 12")
        self.geometry("620x440")
        self.resizable(False, False)
        self.key = tk.StringVar()
        self.status = tk.StringVar(value="Chưa kích hoạt")
        self._ui()
        self.after(1500, self.check_update)

    def _ui(self):
        f = ttk.Frame(self, padding=22); f.pack(fill="both", expand=True)
        ttk.Label(f, text="AUTO COC", font=("Segoe UI", 24, "bold")).pack(anchor="w")
        ttk.Label(f, text=f"Windows 11 · MuMu Player 12 · v{VERSION}").pack(anchor="w", pady=(0,18))
        ttk.Label(f, text="License Key").pack(anchor="w")
        ttk.Entry(f, textvariable=self.key, width=48).pack(anchor="w", pady=7)
        ttk.Button(f, text="Kích hoạt / Kiểm tra key", command=self.activate).pack(anchor="w")
        ttk.Label(f, textvariable=self.status, foreground="#176b3a").pack(anchor="w", pady=10)
        ttk.Separator(f).pack(fill="x", pady=10)
        ttk.Label(f, text="Tiện ích").pack(anchor="w")
        ttk.Button(f, text="Mở website Auto COC", command=lambda: webbrowser.open(API)).pack(anchor="w", pady=5)
        ttk.Button(f, text="Kiểm tra cập nhật", command=self.check_update).pack(anchor="w")
        ttk.Label(f, text="Bản starter hiện cung cấp kích hoạt bản quyền và kiểm tra cập nhật.\nChức năng bot thao tác trong game chưa được tích hợp.", foreground="#6b7280").pack(anchor="w", pady=18)

    def activate(self):
        key = self.key.get().strip()
        if not key:
            messagebox.showwarning("Auto COC", "Vui lòng nhập License Key."); return
        try:
            r = requests.post(API + "/api/license/activate",
                              json={"key": key, "device_id": DEVICE_ID}, timeout=10)
            data = r.json()
            if r.ok and data.get("ok"):
                self.status.set("Đã kích hoạt · " + data.get("plan", ""))
                messagebox.showinfo("Auto COC", "Kích hoạt thành công.")
            else:
                messagebox.showerror("Không kích hoạt được", data.get("message", "Lỗi máy chủ."))
        except Exception as e:
            messagebox.showerror("Lỗi kết nối", str(e))

    def check_update(self):
        try:
            data = requests.get(API + "/api/version", timeout=5).json()
            latest = data.get("version", VERSION)
            if latest != VERSION and data.get("download_url"):
                if messagebox.askyesno("Có phiên bản mới", f"Đã có bản {latest}. Mở trang tải cập nhật?"):
                    webbrowser.open(data["download_url"])
            else:
                self.status.set(self.status.get() if "Đã kích hoạt" in self.status.get() else "Ứng dụng đã ở phiên bản mới nhất.")
        except Exception:
            self.status.set("Không kết nối được máy chủ cập nhật.")

if __name__ == "__main__":
    App().mainloop()
