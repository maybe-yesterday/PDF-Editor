import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import ImageTk
from backend import PDFBackend

class PDFStamperUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Multi-Tool")
        self.root.geometry("1300x900")
        
        self.backend = PDFBackend()
        
        # --- STATE ---
        self.pdf_photo = None
        self.canvas_items = {} 
        self.selected_id = None 
        self.drag_data = {"x": 0, "y": 0}

        # --- STYLE ---
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.setup_ui()

    def setup_ui(self):
        # Sidebar
        sidebar = ttk.Frame(self.root, width=300, padding=10)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        
        # 1. Global Tools
        ttk.Label(sidebar, text="1. Document", font=("Arial", 11, "bold")).pack(anchor="w")
        ttk.Button(sidebar, text="Load PDF", command=self.load_pdf).pack(fill=tk.X, pady=2)
        ttk.Button(sidebar, text="Save PDF", command=self.save_pdf).pack(fill=tk.X, pady=10)
        
        ttk.Separator(sidebar).pack(fill=tk.X, pady=10)

        # 2. Add Items
        ttk.Label(sidebar, text="2. Add Items", font=("Arial", 11, "bold")).pack(anchor="w")
        ttk.Button(sidebar, text="Add Image", command=self.add_image).pack(fill=tk.X, pady=2)
        
        # Text Entry
        self.txt_input = ttk.Entry(sidebar)
        self.txt_input.insert(0, "Type text here...")
        self.txt_input.pack(fill=tk.X, pady=(5,0))
        ttk.Button(sidebar, text="✎ Add Text Box", command=self.add_text).pack(fill=tk.X, pady=2)

        ttk.Separator(sidebar).pack(fill=tk.X, pady=10)

        # 3. Selected Item Controls
        ttk.Label(sidebar, text="3. Edit Selected", font=("Arial", 11, "bold")).pack(anchor="w")
        self.lbl_selected = ttk.Label(sidebar, text="No item selected", foreground="gray")
        self.lbl_selected.pack(anchor="w", pady=5)

        # Image Controls Frame (Hidden by default)
        self.frm_img_ctrl = ttk.Frame(sidebar)
        ttk.Label(self.frm_img_ctrl, text="Scale:").pack(anchor="w")
        self.scale_slider = ttk.Scale(self.frm_img_ctrl, from_=0.1, to=2.0, command=self.on_slider_change)
        self.scale_slider.set(0.5)
        self.scale_slider.pack(fill=tk.X)
        
        # Text Controls Frame (Hidden by default)
        self.frm_txt_ctrl = ttk.Frame(sidebar)
        # REMOVED: Font Size Spinbox (The buggy feature)
        # KEPT: Color Picker (Safe)
        ttk.Button(self.frm_txt_ctrl, text="Change Color", command=self.pick_color).pack(fill=tk.X, pady=5)

        # Delete Button
        ttk.Button(sidebar, text="Delete Selected", command=self.delete_selected).pack(fill=tk.X, pady=20)

        # --- CANVAS ---
        self.canvas = tk.Canvas(self.root, bg="#525252", highlightthickness=0)
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Bindings
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_drag_motion)

    # --- LOADING ---
    def load_pdf(self):
        # Linux compatibility: Removed filetypes filter
        path = filedialog.askopenfilename()
        if not path: return
        
        try:
            pil_img = self.backend.load_pdf(path)
            self.pdf_photo = ImageTk.PhotoImage(pil_img)
            
            self.canvas.delete("all")
            self.canvas_items.clear()
            
            self.canvas.create_image(0, 0, image=self.pdf_photo, anchor="nw", tags="bg")
            self.canvas.config(scrollregion=(0,0, pil_img.width, pil_img.height))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load PDF: {e}")

    # --- ADDING ITEMS ---
    def add_image(self):
        if not self.backend.doc: return
        path = filedialog.askopenfilename()
        if not path: return
        
        pil_original = self.backend.load_image(path)
        scale = 0.5
        resized = self.backend.resize_image(pil_original, scale)
        photo = ImageTk.PhotoImage(resized)
        
        uid = self.canvas.create_image(200, 200, image=photo, anchor="nw", tags="item")
        
        self.canvas_items[uid] = {
            'type': 'image',
            'original': pil_original,
            'photo': photo, 
            'scale': scale
        }
        self.select_item(uid)

    def add_text(self):
        if not self.backend.doc: return
        text = self.txt_input.get()
        
        # Defaults: Size 24, Black
        uid = self.canvas.create_text(200, 200, text=text, 
                                      font=("Arial", 24), fill="black", 
                                      anchor="nw", tags="item")
        
        self.canvas_items[uid] = {
            'type': 'text',
            'fontsize': 24, # Fixed size
            'color': (0,0,0) 
        }
        self.select_item(uid)

    # --- SELECTION LOGIC ---
    def on_canvas_click(self, event):
        found = self.canvas.find_closest(event.x, event.y)
        if not found: return
        
        uid = found[0]
        tags = self.canvas.gettags(uid)
        
        if "item" in tags:
            self.select_item(uid)
            self.drag_data["item"] = uid
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
        else:
            self.deselect_all()

    def select_item(self, uid):
        self.deselect_all() 
        self.selected_id = uid
        
        bbox = self.canvas.bbox(uid)
        self.canvas.create_rectangle(bbox, outline="red", dash=(4, 4), tags="selection_box")

        data = self.canvas_items[uid]
        self.lbl_selected.config(text=f"Selected: {data['type'].upper()}", foreground="blue")

        if data['type'] == 'image':
            self.frm_txt_ctrl.pack_forget()
            self.frm_img_ctrl.pack(fill=tk.X)
            self.scale_slider.set(data['scale'])
            
        elif data['type'] == 'text':
            self.frm_img_ctrl.pack_forget()
            self.frm_txt_ctrl.pack(fill=tk.X)
            # No size controls to update anymore

    def deselect_all(self):
        self.canvas.delete("selection_box")
        self.selected_id = None
        self.lbl_selected.config(text="No item selected", foreground="gray")
        self.frm_img_ctrl.pack_forget()
        self.frm_txt_ctrl.pack_forget()

    def delete_selected(self):
        if self.selected_id:
            self.canvas.delete(self.selected_id)
            del self.canvas_items[self.selected_id]
            self.deselect_all()

    # --- DRAGGING ---
    def on_drag_motion(self, event):
        if not self.selected_id: return
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        
        self.canvas.move(self.selected_id, dx, dy)
        self.canvas.move("selection_box", dx, dy) 
        
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    # --- MODIFIERS ---
    def on_slider_change(self, val):
        if not self.selected_id: return
        data = self.canvas_items[self.selected_id]
        if data['type'] != 'image': return

        scale = float(val)
        data['scale'] = scale
        
        resized = self.backend.resize_image(data['original'], scale)
        new_photo = ImageTk.PhotoImage(resized)
        data['photo'] = new_photo 
        
        self.canvas.itemconfig(self.selected_id, image=new_photo)
        
        self.canvas.delete("selection_box")
        bbox = self.canvas.bbox(self.selected_id)
        self.canvas.create_rectangle(bbox, outline="red", dash=(4, 4), tags="selection_box")

    def pick_color(self):
        if not self.selected_id: return
        data = self.canvas_items[self.selected_id]
        
        c = colorchooser.askcolor(title="Choose Text Color")
        if c[1]:
            hex_col = c[1]
            rgb = [x/255.0 for x in c[0]] 
            data['color'] = rgb
            self.canvas.itemconfig(self.selected_id, fill=hex_col)

    # --- SAVE ---
    def save_pdf(self):
        if not self.backend.doc: return
        path = filedialog.asksaveasfilename(defaultextension=".pdf")
        if not path: return

        elements_to_save = []
        for uid, data in self.canvas_items.items():
            coords = self.canvas.coords(uid)
            item_data = {
                'type': data['type'],
                'x': coords[0],
                'y': coords[1]
            }
            if data['type'] == 'image':
                item_data['original_pil'] = data['original']
                item_data['scale'] = data['scale']
            elif data['type'] == 'text':
                item_data['content'] = self.canvas.itemcget(uid, "text")
                item_data['fontsize'] = data['fontsize']
                item_data['color'] = data['color']
            
            elements_to_save.append(item_data)

        self.backend.save_pdf(path, elements_to_save)
        messagebox.showinfo("Success", "PDF Saved!")