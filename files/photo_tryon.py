
import cv2
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import datetime

from pose_engine     import PoseDetectionEngine
from overlay_engine  import OverlayEngine
from catalog_manager import ClothingCatalogManager

C_BG      = '#0d0d1a'
C_SURFACE = '#141428'
C_CARD    = '#1e1e3a'
C_ACCENT  = '#7c5cfc'
C_ACCENT2 = '#fc5c7d'
C_GREEN   = '#00e676'
C_WARN    = '#ffab40'
C_TEXT    = '#f0f0ff'
C_MUTED   = '#7070a0'
C_BORDER  = '#2a2a4a'

SHOTS_DIR = 'screenshots'


class PhotoTryOnWindow:

    def __init__(self, parent_root, catalog: ClothingCatalogManager,
                 overlay_engine: OverlayEngine, selected_outfit: str = None):

        self.win = tk.Toplevel(parent_root)
        self.win.title("Photo Try-On")
        self.win.configure(bg=C_BG)
        self.win.geometry("1280x760")
        self.win.minsize(1000, 640)

        self.win.update_idletasks()
        self.win.update()

        self.catalog         = catalog
        self.overlay_engine  = overlay_engine
        self.selected_outfit = selected_outfit

        self.pose_engine = PoseDetectionEngine(static_image_mode=True)

        self.original_pil = None
        self.result_pil   = None
        self._cached_kp   = None
        self._photo_refs  = []

        os.makedirs(SHOTS_DIR, exist_ok=True)
        self._build_ui()

        self.win.update_idletasks()
        self.win.update()

        if self.selected_outfit and self.selected_outfit in self.catalog.catalog:
            idx = self.catalog.catalog.index(self.selected_outfit)
            self.outfit_listbox.selection_set(idx)
            self.outfit_listbox.see(idx)


    def _build_ui(self):
        hdr = tk.Frame(self.win, bg='#0a0a18', height=46)
        hdr.pack(side='top', fill='x')
        hdr.pack_propagate(False)

        tk.Label(hdr, text="📷  Photo Try-On",
                 font=('Segoe UI', 14, 'bold'),
                 bg='#0a0a18', fg=C_TEXT).pack(side='left', padx=16, pady=10)

        self.status_var = tk.StringVar(value="Upload a photo to begin")
        tk.Label(hdr, textvariable=self.status_var,
                 font=('Segoe UI', 9),
                 bg='#0a0a18', fg=C_WARN).pack(side='right', padx=16)

        body = tk.Frame(self.win, bg=C_BG)
        body.pack(side='top', fill='both', expand=True, padx=8, pady=8)

        right = tk.Frame(body, bg=C_SURFACE, width=190)
        right.pack(side='right', fill='y', padx=(6, 0))
        right.pack_propagate(False)

        tk.Label(right, text="OUTFITS",
                 font=('Segoe UI', 8, 'bold'),
                 bg=C_SURFACE, fg=C_MUTED).pack(anchor='w', padx=12, pady=(14, 4))

        lb_wrap = tk.Frame(right, bg=C_SURFACE)
        lb_wrap.pack(fill='both', expand=True, padx=6, pady=(0, 8))

        vsb = tk.Scrollbar(lb_wrap, orient='vertical')
        self.outfit_listbox = tk.Listbox(
            lb_wrap,
            yscrollcommand=vsb.set,
            font=('Segoe UI', 10),
            bg=C_CARD, fg=C_TEXT,
            selectbackground=C_ACCENT,
            selectforeground='white',
            activestyle='none',
            relief='flat', bd=0,
        )
        vsb.config(command=self.outfit_listbox.yview)
        vsb.pack(side='right', fill='y')
        self.outfit_listbox.pack(side='left', fill='both', expand=True)
        self.outfit_listbox.bind('<<ListboxSelect>>', self._on_outfit_pick)

        for fn in self.catalog.catalog:
            self.outfit_listbox.insert('end', '  ' + self.catalog.get_display_name(fn))

        left = tk.Frame(body, bg=C_SURFACE, width=200)
        left.pack(side='left', fill='y', padx=(0, 6))
        left.pack_propagate(False)

        def section(label):
            tk.Frame(left, bg=C_BORDER, height=1).pack(fill='x', padx=10, pady=6)
            tk.Label(left, text=label, font=('Segoe UI', 8, 'bold'),
                     bg=C_SURFACE, fg=C_MUTED).pack(anchor='w', padx=14, pady=(4, 2))

        tk.Label(left, text="STEP 1", font=('Segoe UI', 8, 'bold'),
                 bg=C_SURFACE, fg=C_MUTED).pack(anchor='w', padx=14, pady=(18, 2))
        self._btn(left, "📂  Upload Photo",
                  self._upload_photo, C_ACCENT).pack(fill='x', padx=10, pady=4)
        tk.Label(left, text="JPG or PNG · full body visible",
                 font=('Segoe UI', 8), bg=C_SURFACE, fg=C_MUTED).pack(
                 anchor='w', padx=14)

        section("STEP 2")
        tk.Label(left, text="Pick outfit from\nthe right panel →",
                 font=('Segoe UI', 9), bg=C_SURFACE, fg=C_TEXT,
                 justify='left').pack(anchor='w', padx=14, pady=(0, 4))

        section("STEP 3")
        self.apply_btn = self._btn(left, "✨  Apply Outfit",
                                   self._apply_outfit, C_ACCENT2)
        self.apply_btn.pack(fill='x', padx=10, pady=4)
        self.apply_btn.configure(state='disabled')

        section("SAVE")
        self.save_btn = self._btn(left, "💾  Save Result",
                                  self._save_result, '#1a6a3a')
        self.save_btn.pack(fill='x', padx=10, pady=4)
        self.save_btn.configure(state='disabled')

        tk.Frame(left, bg=C_BORDER, height=1).pack(fill='x', padx=10, pady=8)
        self.info_var = tk.StringVar(value="")
        tk.Label(left, textvariable=self.info_var,
                 font=('Segoe UI', 8), bg=C_SURFACE, fg=C_MUTED,
                 wraplength=170, justify='left').pack(anchor='w', padx=14)

        center = tk.Frame(body, bg=C_BG)
        center.pack(side='left', fill='both', expand=True)

        heads = tk.Frame(center, bg=C_BG)
        heads.pack(side='top', fill='x', pady=(0, 4))
        tk.Label(heads, text="ORIGINAL",
                 font=('Segoe UI', 9, 'bold'),
                 bg=C_BG, fg=C_MUTED).pack(side='left', expand=True)
        tk.Label(heads, text="WITH OUTFIT",
                 font=('Segoe UI', 9, 'bold'),
                 bg=C_BG, fg=C_MUTED).pack(side='left', expand=True)

        panels = tk.Frame(center, bg=C_BG)
        panels.pack(side='top', fill='both', expand=True)

        orig_frame = tk.Frame(panels, bg=C_CARD, bd=1, relief='flat')
        orig_frame.pack(side='left', fill='both', expand=True, padx=(0, 4))
        self.orig_canvas = tk.Canvas(orig_frame, bg=C_CARD,
                                     highlightthickness=0, bd=0)
        self.orig_canvas.pack(fill='both', expand=True)

        # Result canvas
        res_frame = tk.Frame(panels, bg=C_CARD, bd=1, relief='flat')
        res_frame.pack(side='left', fill='both', expand=True, padx=(4, 0))
        self.result_canvas = tk.Canvas(res_frame, bg=C_CARD,
                                       highlightthickness=0, bd=0)
        self.result_canvas.pack(fill='both', expand=True)

        self.win.after(150, self._draw_placeholders)

    def _draw_placeholders(self):
        self._redraw_placeholder(self.orig_canvas,   "Upload a photo\nto get started")
        self._redraw_placeholder(self.result_canvas, "Result will\nappear here")

    def _redraw_placeholder(self, canvas, text):
        canvas.delete('all')
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 2: w = 400
        if h < 2: h = 500
        canvas.create_text(w // 2, h // 2, text=text,
                           fill=C_MUTED, font=('Segoe UI', 13),
                           anchor='center', justify='center')

    def _btn(self, parent, text, cmd, color):
        def dk(c):
            c = c.lstrip('#')
            r, g, b = int(c[:2], 16), int(c[2:4], 16), int(c[4:], 16)
            return '#{:02x}{:02x}{:02x}'.format(int(r*.75), int(g*.75), int(b*.75))
        b = tk.Button(parent, text=text,
                      font=('Segoe UI', 9, 'bold'),
                      bg=color, fg='white',
                      activebackground=dk(color),
                      relief='flat', bd=0, padx=8, pady=9,
                      cursor='hand2', command=cmd)
        hov = dk(color)
        b.bind('<Enter>', lambda e: b.configure(bg=hov))
        b.bind('<Leave>', lambda e: b.configure(bg=color))
        return b

    def _show_in_canvas(self, canvas, pil_img):
        """Scale pil_img to fill the canvas and display it."""
        canvas.update_idletasks()
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 10: w = 500
        if h < 10: h = 600

        iw, ih = pil_img.size
        scale  = min(w / iw, h / ih)
        nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
        fitted = pil_img.resize((nw, nh), Image.Resampling.LANCZOS)

        photo = ImageTk.PhotoImage(fitted)
        canvas.delete('all')
        canvas.create_image(w // 2, h // 2, anchor='center', image=photo)
        canvas._ph = photo         
        self._photo_refs.append(photo)

    def _on_outfit_pick(self, event):
        sel = self.outfit_listbox.curselection()
        if sel:
            self.selected_outfit = self.catalog.catalog[sel[0]]

    def _upload_photo(self):
        path = filedialog.askopenfilename(
            title="Select a full-body photo",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.webp"),
                       ("All files", "*.*")]
        )
        if not path:
            return
        try:
            img = Image.open(path).convert('RGB')
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open image:\n{e}")
            return

        iw, ih = img.size
        scale  = min(1200 / iw, 1800 / ih, 1.0)
        if scale < 1.0:
            img = img.resize((int(iw * scale), int(ih * scale)),
                             Image.Resampling.LANCZOS)

        self.original_pil = img
        self.result_pil   = None
        self._cached_kp   = None

        self.win.after(50, lambda: self._show_in_canvas(self.orig_canvas, img))

        self.result_canvas.delete('all')
        self.result_canvas.create_text(
            self.result_canvas.winfo_width() // 2 or 200,
            self.result_canvas.winfo_height() // 2 or 300,
            text="Detecting pose…", fill=C_WARN,
            font=('Segoe UI', 13), anchor='center')
        self.status_var.set("Detecting body pose…")
        self.win.update_idletasks()

        bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        kp  = self.pose_engine.detect(bgr)

        if kp is None:
            self.status_var.set("⚠ No pose found — use a clear full-body photo")
            self.info_var.set("Tip: face the camera,\nfull body visible,\ngood lighting.")
            self._redraw_placeholder(self.result_canvas,
                                     "Pose not detected.\nTry a clearer photo.")
            self.apply_btn.configure(state='disabled')
        else:
            n = len(kp)
            self._cached_kp = kp
            self.status_var.set(f"✓ Pose detected — {n} landmarks")
            self.info_var.set(f"✓ {n} landmarks found.\nPick an outfit\nand press Apply.")
            self._redraw_placeholder(self.result_canvas, "Press  ✨ Apply Outfit")
            self.apply_btn.configure(state='normal')

    def _apply_outfit(self):
        if self.original_pil is None:
            messagebox.showinfo("", "Upload a photo first.")
            return
        if not self.selected_outfit:
            messagebox.showinfo("", "Select an outfit from the right panel.")
            return
        if self._cached_kp is None:
            messagebox.showinfo("", "No pose detected in this photo.")
            return

        self.status_var.set("Applying outfit…")
        self.win.update_idletasks()

        try:
            bgr      = cv2.cvtColor(np.array(self.original_pil), cv2.COLOR_RGB2BGR)
            clothing = self.catalog.get_image(self.selected_outfit)
            out_bgr  = self.overlay_engine.composite(
                bgr, self._cached_kp, clothing,
                cache_key=self.selected_outfit)
            out_rgb       = cv2.cvtColor(out_bgr, cv2.COLOR_BGR2RGB)
            self.result_pil = Image.fromarray(out_rgb)

            self._show_in_canvas(self.result_canvas, self.result_pil)
            self.save_btn.configure(state='normal')
            name = self.catalog.get_display_name(self.selected_outfit)
            self.status_var.set(f"✓ Done! Showing: {name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed:\n{e}")
            self.status_var.set(f"Error: {e}")

    def _save_result(self):
        if self.result_pil is None:
            return
        ts   = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(SHOTS_DIR, f'photo_tryon_{ts}.png')
        self.result_pil.save(path)
        messagebox.showinfo("Saved!", f"Saved to:\n{os.path.abspath(path)}")