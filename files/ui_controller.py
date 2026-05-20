import tkinter as tk
from tkinter import messagebox
import cv2, math, os, datetime
from PIL import Image, ImageTk

from camera_module   import CameraModule
from pose_engine     import PoseDetectionEngine
from overlay_engine  import OverlayEngine
from catalog_manager import ClothingCatalogManager
from photo_tryon     import PhotoTryOnWindow
import time

start = time.time()

FRAME_MS  = 33
CAM_W     = 720
CAM_H     = 540
PANEL_W   = 260
SHOTS_DIR = 'screenshots'

C_BG      = '#0d0d1a'
C_SURFACE = '#141428'
C_CARD    = '#1e1e3a'
C_CARD_SEL= '#2d2d5e'
C_ACCENT  = '#7c5cfc'
C_ACCENT2 = '#fc5c7d'
C_GREEN   = '#00e676'
C_WARN    = '#ffab40'
C_TEXT    = '#f0f0ff'
C_MUTED   = '#7070a0'
C_BORDER  = '#2a2a4a'


class VirtualTryOnApp:

    def __init__(self, root: tk.Tk):
        self.root    = root
        self.root.title("AI Virtual Outfit Try-On  ✦  SE Project")
        self.root.configure(bg=C_BG)
        self.root.resizable(True, True)

        self.selected_outfit   = None
        self.current_keypoints = None
        self.last_raw_bgr      = None
        self.running           = True
        self._imgtk            = None   
        self._thumb_refs       = []

        try:
            self.camera = CameraModule()
        except RuntimeError as e:
            messagebox.showerror("Camera Error", str(e))
            root.destroy()
            return

        self.pose_engine    = PoseDetectionEngine()
        self.overlay_engine = OverlayEngine()
        self.catalog        = ClothingCatalogManager()
        os.makedirs(SHOTS_DIR, exist_ok=True)

        self._build_ui()
        self._populate_catalog()
        self.root.after(200, self._update_frame)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg='#0a0a18', height=50)
        hdr.pack(side='top', fill='x')
        hdr.pack_propagate(False)
        tk.Label(hdr, text="✦  AI Virtual Outfit Try-On",
                 font=('Segoe UI', 15, 'bold'),
                 bg='#0a0a18', fg=C_TEXT).pack(side='left', padx=18, pady=12)
        self.pose_badge = tk.Label(hdr, text="● Starting…",
                                   font=('Segoe UI', 9),
                                   bg='#0a0a18', fg=C_WARN)
        self.pose_badge.pack(side='right', padx=18)

        body = tk.Frame(self.root, bg=C_BG)
        body.pack(side='top', fill='both', expand=True)

        panel = tk.Frame(body, bg=C_SURFACE, width=PANEL_W)
        panel.pack(side='right', fill='y', padx=(0,10), pady=10)
        panel.pack_propagate(False)
        self._build_panel(panel)
        
        cam_wrap = tk.Frame(body, bg='#000000')
        cam_wrap.pack(side='left', fill='both', expand=True, padx=(10,4), pady=10)

        self.canvas = tk.Canvas(cam_wrap, bg='#000000',
                                width=CAM_W, height=CAM_H,
                                highlightthickness=0, bd=0)
        self.canvas.pack(fill='both', expand=True)

        self._canvas_img_id = self.canvas.create_image(0, 0, anchor='nw', image='')

    def _build_panel(self, panel):
        sc = tk.Frame(panel, bg=C_CARD, padx=12, pady=12)
        sc.pack(fill='x', padx=10, pady=(14,6))
        tk.Label(sc, text="ESTIMATED SIZE",
                 font=('Segoe UI', 8, 'bold'),
                 bg=C_CARD, fg=C_MUTED).pack(anchor='w')
        self.size_var = tk.StringVar(value="—")
        tk.Label(sc, textvariable=self.size_var,
                 font=('Segoe UI', 30, 'bold'),
                 bg=C_CARD, fg=C_ACCENT).pack(anchor='w')
        self.shoulder_var = tk.StringVar(value="Stand in front of camera")
        tk.Label(sc, textvariable=self.shoulder_var,
                 font=('Segoe UI', 8),
                 bg=C_CARD, fg=C_MUTED, wraplength=220).pack(anchor='w')

        tk.Frame(panel, bg=C_BORDER, height=1).pack(fill='x', padx=10, pady=6)

        row = tk.Frame(panel, bg=C_SURFACE)
        row.pack(fill='x', padx=10)
        tk.Label(row, text="OUTFITS",
                 font=('Segoe UI', 8, 'bold'),
                 bg=C_SURFACE, fg=C_MUTED).pack(side='left')
        tk.Button(row, text="✕ None",
                  font=('Segoe UI', 8),
                  bg=C_SURFACE, fg=C_MUTED,
                  relief='flat', bd=0, cursor='hand2',
                  command=self._clear_outfit).pack(side='right')

        outer = tk.Frame(panel, bg=C_SURFACE)
        outer.pack(fill='both', expand=True, padx=10, pady=4)
        scr = tk.Canvas(outer, bg=C_SURFACE, highlightthickness=0)
        vsb = tk.Scrollbar(outer, orient='vertical', command=scr.yview)
        scr.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        scr.pack(side='left', fill='both', expand=True)
        self.card_container = tk.Frame(scr, bg=C_SURFACE)
        win_id = scr.create_window((0,0), window=self.card_container, anchor='nw')
        self.card_container.bind('<Configure>',
            lambda e: scr.configure(scrollregion=scr.bbox('all')))
        scr.bind('<Configure>',
            lambda e: scr.itemconfig(win_id, width=e.width))
        self._outfit_canvas = scr

        tk.Frame(panel, bg=C_BORDER, height=1).pack(fill='x', padx=10, pady=6)

        tk.Label(panel, text="PHOTO MODE",
                 font=('Segoe UI', 8, 'bold'),
                 bg=C_SURFACE, fg=C_MUTED).pack(anchor='w', padx=14, pady=(4,2))
        self._btn(panel, "🖼  Photo Try-On",
                  self._open_photo_tryon, C_ACCENT2).pack(fill='x', padx=10, pady=3)

        tk.Frame(panel, bg=C_BORDER, height=1).pack(fill='x', padx=10, pady=6)

        self._btn(panel, "📸  Capture Screenshot",
                  self._take_screenshot, C_ACCENT).pack(fill='x', padx=10, pady=3)
        self._btn(panel, "✕  Quit",
                  self._on_close, '#2a2a4a').pack(fill='x', padx=10, pady=3)

        tk.Label(panel,
                 text="Stand ~1 m from camera\nFace camera directly",
                 font=('Segoe UI', 8),
                 bg=C_SURFACE, fg=C_MUTED, justify='left').pack(
                 anchor='w', padx=14, pady=(8,0))

    def _btn(self, parent, text, cmd, color):
        def dk(c):
            c=c.lstrip('#'); r,g,b=int(c[:2],16),int(c[2:4],16),int(c[4:],16)
            return '#{:02x}{:02x}{:02x}'.format(int(r*.75),int(g*.75),int(b*.75))
        b = tk.Button(parent, text=text,
                      font=('Segoe UI', 9, 'bold'),
                      bg=color, fg='white', activebackground=dk(color),
                      relief='flat', bd=0, padx=8, pady=9,
                      cursor='hand2', command=cmd)
        h = dk(color)
        b.bind('<Enter>', lambda e: b.configure(bg=h))
        b.bind('<Leave>', lambda e: b.configure(bg=color))
        return b

    def _populate_catalog(self):
        for w in self.card_container.winfo_children():
            w.destroy()
        self._thumb_refs.clear()

        for filename in self.catalog.catalog:
            card = tk.Frame(self.card_container, bg=C_CARD,
                            padx=8, pady=8, cursor='hand2')
            card.pack(fill='x', pady=3)

            try:
                img = self.catalog.get_image(filename)
                th  = img.copy()
                th.thumbnail((60, 60), Image.Resampling.LANCZOS)
                bg  = Image.new('RGB', (60, 60), '#1e1e3a')
                if th.mode == 'RGBA':
                    bg.paste(th, mask=th.split()[3])
                else:
                    bg.paste(th)
                tk_th = ImageTk.PhotoImage(bg)
                self._thumb_refs.append(tk_th)
                tk.Label(card, image=tk_th, bg=C_CARD).pack(side='left', padx=(0,8))
            except Exception:
                pass

            name_lbl = tk.Label(card,
                                text=self.catalog.get_display_name(filename),
                                font=('Segoe UI', 10, 'bold'),
                                bg=C_CARD, fg=C_TEXT, anchor='w')
            name_lbl.pack(side='left', fill='x', expand=True)

            for w in (card, name_lbl):
                w.bind('<Button-1>',
                       lambda e, fn=filename, c=card: self._select_card(fn, c))

        if self.catalog.catalog:
            self.selected_outfit = self.catalog.catalog[0]
            kids = self.card_container.winfo_children()
            if kids:
                self._highlight(kids[0])

        self._outfit_canvas.update_idletasks()

    def _select_card(self, filename, card):
        self.overlay_engine.clear_cache()
        self.selected_outfit = filename
        for c in self.card_container.winfo_children():
            self._set_bg(c, C_CARD)
        self._highlight(card)

    def _highlight(self, card):
        self._set_bg(card, C_CARD_SEL)

    def _set_bg(self, frame, color):
        try:
            frame.configure(bg=color)
            for ch in frame.winfo_children():
                ch.configure(bg=color)
        except Exception:
            pass

    def _clear_outfit(self):
        self.selected_outfit = None
        for c in self.card_container.winfo_children():
            self._set_bg(c, C_CARD)
        self.size_var.set("—")


    def _update_frame(self):
        if not self.running:
            return

        ok, frame = self.camera.read_frame()
        if not ok:
            self.root.after(FRAME_MS, self._update_frame)
            return

        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (CAM_W, CAM_H))
        self.last_raw_bgr = frame.copy()

        # Pose
        kp = self.pose_engine.detect(frame)
        self.current_keypoints = kp
        
        if self.selected_outfit:
         name = self.catalog.get_display_name(self.selected_outfit)
        cv2.putText(frame, name, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                (255,255,255), 2)
        
        if kp:
            ls = kp['left_shoulder']; rs = kp['right_shoulder']
            sw = math.hypot(rs[0]-ls[0], rs[1]-ls[1])
            self.size_var.set(self.catalog.estimate_size(sw, frame_w=CAM_W))
            if sw < 80:
                self.shoulder_var.set(f"⚠ Move closer! ({int(sw)}px)")
            else:
                self.shoulder_var.set(f"Shoulder: {int(sw)}px ✓")
            self.pose_badge.configure(text="● Pose detected ✓", fg=C_GREEN)
        else:
            self.pose_badge.configure(text="● No pose — face camera", fg=C_WARN)

        if self.selected_outfit and kp:
            clothing = self.catalog.get_image(self.selected_outfit)
            first    = self.selected_outfit not in self.overlay_engine._cache
            frame    = self.overlay_engine.composite(
                frame, kp, clothing, cache_key=self.selected_outfit)
            if first:
                cv2.putText(frame, "Processing...",
                    (10, CAM_H-20), cv2.FONT_HERSHEY_DUPLEX,
                    0.7, (255,255,100), 2, cv2.LINE_AA)

        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        imgtk  = ImageTk.PhotoImage(Image.fromarray(rgb))
        self.canvas.itemconfig(self._canvas_img_id, image=imgtk)
        self._imgtk = imgtk      # prevent GC — this is the critical line

        self.root.after(FRAME_MS, self._update_frame)


        fps = 1 / (time.time() - start)
        cv2.putText(frame, f"FPS: {int(fps)}", (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6,
            (0,255,0), 2)

    def _take_screenshot(self):
        if self.last_raw_bgr is None:
            messagebox.showinfo("", "No frame yet.")
            return
        frame = self.last_raw_bgr.copy()
        if self.selected_outfit and self.current_keypoints:
            frame = self.overlay_engine.composite(
                frame, self.current_keypoints,
                self.catalog.get_image(self.selected_outfit),
                cache_key=self.selected_outfit)
        ts   = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(SHOTS_DIR, f'outfit_{ts}.png')
        cv2.imwrite(path, frame)
        messagebox.showinfo("Saved!", f"Screenshot saved:\n{os.path.abspath(path)}")

    def _open_photo_tryon(self):
        PhotoTryOnWindow(
            parent_root    = self.root,
            catalog        = self.catalog,
            overlay_engine = self.overlay_engine,
            selected_outfit= self.selected_outfit,
        )


    def _on_close(self):
        self.running = False
        self.camera.release()
        self.pose_engine.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    VirtualTryOnApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
