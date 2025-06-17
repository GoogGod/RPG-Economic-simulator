import tkinter as tk
from tkinter import PhotoImage, colorchooser, font
from PIL import Image, ImageTk
from math import cos, sin, radians
from timeit import timeit
from sys import argv
import json

class GridMap:
    def __init__(self, root : tk.Tk):
        self.root = root
        self.root.title("2D Grid Map")
        self.quality = 2
        
        self.scr_width = self.root.winfo_screenwidth()
        self.scr_height = self.root.winfo_screenheight()
        
        self.root.geometry(f"{self.scr_width}x{self.scr_height}")
        self.root.wm_resizable(False, False)

        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.grid_size = 10
        self.grid = {}
        self.rows = 27 * self.quality
        self.cols = 48 * self.quality
        
        # self.grid_state = {(x,y) : [visible, color, name, infobox]}
        self.grid_state = {}
        self.zoom_level = 2
        
        self.shape_image = Image.open("images/map.png")

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<MouseWheel>", self.on_zoom)
        self.canvas.bind("<ButtonPress-2>", self.on_middle_button_press)
        self.canvas.bind("<B2-Motion>", self.on_middle_button_drag)
        self.canvas.bind("<ButtonRelease-2>", self.on_middle_button_release)

        self.offset_x = 0
        self.offset_y = 0

        self.settings_panel_visible = False
        self.create_settings_panel()
        
        self.fps_counter = tk.Label(self.root, text="FPS: 0", bg="white")
        self.fps_counter.place(x=10, y=10)
        
        self.drawing_squares = tk.Label(self.root, text="Drawing: 0", bg="white")
        self.drawing_squares.place(x=10, y=30)
        
        self.zoom_counter = tk.Label(self.root, text="Zoom: 0", bg="white")
        self.zoom_counter.place(x=10, y=50)
        
        self.resample = Image.NEAREST if '-low' in argv else None
        
        # self.fps_warn = tk.Label(self.root, anchor=tk.CENTER, text="Low performance detected!", fg='red', bg='white', font=font.Font(family='Arial', size=18))
        # self.recounting_warn = tk.Label(self.root, anchor=tk.CENTER, text="Recounting map", fg='yellow', bg='white', font="Arial 18")
        
        self.background_image = ImageTk.PhotoImage(self.shape_image.resize((int(self.cols * 10.005 * self.zoom_level), int(self.rows * 10.005 * self.zoom_level)), resample=self.resample))
        self.update_grid()

    def on_middle_button_press(self, event):
        self.middle_button_pressed = True
        self.middle_button_start_x = event.x
        self.middle_button_start_y = event.y

    def on_middle_button_drag(self, event):
        if self.middle_button_pressed:
            delta_x = event.x - self.middle_button_start_x
            delta_y = event.y - self.middle_button_start_y
            self.offset_x += delta_x
            self.offset_y += delta_y
            self.middle_button_start_x = event.x
            self.middle_button_start_y = event.y
            self.update_grid()

    def on_middle_button_release(self, event):
        self.middle_button_pressed = False

    def create_settings_panel(self):
        self.settings_panel = tk.Frame(self.root, bg="lightgray", width=350, height=600)
        self.settings_panel.place(x=1650, y=0)
        
        coord_label = tk.Label(self.settings_panel, text=f"Coordinates: (None)", bg="lightgray", font="System 15")
        coord_label.pack(pady=3)
        
        label = tk.Label(self.settings_panel, text="Settings", bg="lightgray", font="System 11")
        label.pack(pady=10)

        self.settings_panel.place_forget()
        
    def toggle_settings_panel(self):
        if self.settings_panel_visible:
            self.settings_panel.place_forget()
        else:
            self.settings_panel.place(x=1650, y=0)
        self.settings_panel_visible = not self.settings_panel_visible

    def on_click(self, event):
        x, y = event.x, event.y
        row = int((y - self.offset_y) // (self.grid_size * self.zoom_level))
        col = int((x - self.offset_x) // (self.grid_size * self.zoom_level))
        if 0 <= row <= self.rows and 0 <= col <= self.cols:
            self.open_settings_panel(row, col)

    def open_settings_panel(self, row, col):
        self.settings_panel.place(x=1650, y=0)
        self.settings_panel_visible = True

        # Clear previous widgets
        for widget in self.settings_panel.winfo_children():
            widget.destroy()

        # Add coordinate information
        coord_label = tk.Label(self.settings_panel, text=f"Coordinates: ({row}, {col})", bg="lightgray", font="System 15")
        coord_label.pack(pady=3)

        # Add color selection widgets
        color_label = tk.Label(self.settings_panel, text="Settings", bg="lightgray", font="System 11")
        color_label.pack(pady=3)

        state = self.grid_state.get((row,col))

        if state is None:
            create_button = tk.Button(self.settings_panel, text="Create marker", bg="lightgrey", fg='green', activebackground="lightgrey", command= lambda: self.create_marker(row, col), font="System 11")
            create_button.pack(pady=3)
            return

        self.color_var = tk.StringVar(value=state[0])

        visible = tk.Checkbutton(self.settings_panel, text="Visible", variable=self.color_var, bg="lightgray", command=lambda: self.set_visibility(row, col), font="System 13")
        visible.pack(anchor="w")

        color_frame = tk.Frame(self.settings_panel, bg="lightgray")
        color_frame.pack(pady=3)

        choose_color_button = tk.Button(color_frame, text="Choose color", bg="lightgrey", activebackground="lightgrey", command=lambda: self.set_color(row, col) , font="System 11")
        choose_color_button.pack(side=tk.LEFT, padx=3)

        color_preview = tk.Label(color_frame, bg=state[1], width=4, height=2, bd=1)
        color_preview.pack(side=tk.LEFT, padx=3)

        # Add name input field
        name_label = tk.Label(self.settings_panel, text="Name", bg="lightgray", font="System 13")
        name_label.pack(pady=3)

        self.name_var = tk.StringVar(value=state[2] if state else "")
        name_input = tk.Entry(self.settings_panel, textvariable=self.name_var, font="System 11")
        name_input.bind('<Return>', lambda x: self.set_name(row=row, col=col))
        name_input.pack(pady=3, fill=tk.X)

        set_name_button = tk.Button(self.settings_panel, text="Set Name", bg="lightgrey", activebackground="lightgrey", command=lambda: self.set_name(row, col), font="System 11")
        set_name_button.pack(pady=3)
        
        info_label = tk.Label(self.settings_panel, text="Information", bg="lightgray", font="System 13")
        info_label.pack(pady=3)
        
        self.info_input = tk.Text(self.settings_panel, width=12, height=9, font="System 11")
        self.info_input.insert(tk.END, "" if state[3] is None else state[3])
        self.info_input.pack(pady=3, fill=tk.X)
        
        set_info_button = tk.Button(self.settings_panel, text="Set Info", bg="lightgrey", activebackground="lightgrey", command=lambda: self.set_info(row, col), font="System 11")
        set_info_button.pack(pady=3)

        delete_button = tk.Button(self.settings_panel, text="Delete marker", bg="lightgrey", activebackground="lightgrey", fg="red", command= lambda: self.delete_marker(row, col), font="System 11")
        delete_button.pack(pady=3)

    def create_marker(self, row, col):
        self.grid_state[(row,col)] = [True, "blue", None, None]
        self.open_settings_panel(row, col)
        self.update_grid()
        
    def delete_marker(self, row, col):
        self.grid_state.pop((row,col))
        self.open_settings_panel(row, col)
        self.update_grid()
    
    def set_visibility(self, row, col):
        state = self.grid_state.get((row,col))
        visible = True if self.color_var.get() == '1' else False
        self.grid_state[(row, col)] = [visible, state[1], state[2], state[3]]
        self.update_grid()
    
    def set_color(self, row, col):
        state = self.grid_state.get((row,col))
        choosecolor = colorchooser.askcolor(
            title="Choose Background Color",
            initialcolor=state[1],
            parent=self.root
        )
        self.grid_state[(row, col)] = [state[0], choosecolor[1], state[2], state[3]]
        self.open_settings_panel(row,col)
        self.update_grid()
    
    def set_name(self, row, col):
        state = self.grid_state.get((row,col))
        name = self.name_var.get()
        if state:
            self.grid_state[(row, col)] = [state[0], state[1], name, state[3]]
            self.open_settings_panel(row, col)
            self.update_grid()
    
    def set_info(self, row, col):
        state = self.grid_state.get((row,col))
        info = self.info_input.get("1.0", tk.END).strip()
        self.grid_state[(row, col)] = [state[0], state[1], state[2], info]

    def on_zoom(self, event):
        # pos = self.getCenterOfWindow(self.recounting_warn)
        # self.recounting_warn.place(x=pos[0], y=10)
        if event.delta > 0:
            if self.zoom_level < 5:
                self.zoom_level *= 1.1
                self.offset_x -= (event.x - (self.scr_width // 2)) * self.zoom_level / 10
                self.offset_y -= (event.y - (self.scr_height // 2)) * self.zoom_level / 10
            else:
                # self.recounting_warn.place_forget() 
                return
        else:
            if self.zoom_level > 1.1:
                self.zoom_level /= 1.1
                # self.offset_x -= (event.x - (self.scr_width // 2)) / 10
                # self.offset_y -= (event.y - (self.scr_height // 2)) / 10
            else:
                # self.recounting_warn.place_forget() 
                return

        self.root.after(1, self.update_background_image)
        
    def update_background_image(self):
        self.background_image = ImageTk.PhotoImage(self.shape_image.resize((int(self.cols * 10.005 * self.zoom_level), int(self.rows * 10.005 * self.zoom_level)), resample=self.resample))
        self.update_grid()
        # self.recounting_warn.place_forget()

    def create_stroked_text(self, canvas : tk.Canvas, cords : tuple[float, float] | list[int] | list[float], text_font : str, text : float | str, stroke_color : str = "white", fill_color : str = "black", stroke_width : int = 1, anchor = "center", font_size = 12, quality = 12):

        x, y = cords
        
        # iterates in a circle by angle and draws text
        for angle in range(0, 360, 360//quality):
            dx = stroke_width * cos(radians(angle))
            dy = stroke_width * sin(radians(angle))
            canvas.create_text(x + dx, y + dy, text=text, font=text_font, fill=stroke_color, anchor=anchor)
        canvas.create_text(x, y, text=text, font=text_font, fill=fill_color, anchor=anchor)

    def update_grid(self):
        fps = 0
        original_time = timeit(lambda: self.update_INNERgrid(), number=1)
        test = original_time
        while not test > 1:
            fps += 1
            test += original_time
        self.fps_counter.configure(text=f"FPS: {fps}")
        self.drawing_squares.configure(text=f"Drawing: {self.num_objects}")
        self.zoom_counter.configure(text=f"Zoom: {self.zoom_level}")
        # metric = {"fps": fps, "num_objects": self.num_objects}
        # with open("fps_metric", "a") as f:
        #     json.dump(metric, f)
        #     f.write("\n")
    
    def update_INNERgrid(self):
        # Only update the visible portion of the grid
        visible_rows = range(max(0, int(-self.offset_y // (self.grid_size * self.zoom_level))), min(self.rows+1, int((self.scr_height - self.offset_y) // (self.grid_size * self.zoom_level))))
        visible_cols = range(max(0, int(-self.offset_x // (self.grid_size * self.zoom_level))), min(self.cols+1, int((self.scr_width - self.offset_x) // (self.grid_size * self.zoom_level))))
        # 48 * 108 / 27 * 108 (MIN ZOOM = 11x11 (10.71)  |||  MAX ZOOM = 108x108 (1.08)) 
        self.canvas.delete("all")
        self.canvas.create_image((self.offset_x + self.background_image.width() / 2), (self.offset_y + self.background_image.height() / 2), image=self.background_image)        
        
        items = 0
        names = []
        
        if not self.zoom_level < 1.6:
            
            for row in visible_rows: # Horizontal 
                y = row * self.grid_size * self.zoom_level + self.offset_y
                x1 = max(0, self.offset_x)
                x2 = min(1920, self.cols * self.grid_size * self.zoom_level + self.offset_x)
                self.canvas.create_line(x1, y, x2, y, width=1, fill="gray")
                items += 1
                
            for col in visible_cols: # Vertical
                x = col * self.grid_size * self.zoom_level + self.offset_x
                y1 = max(0, self.offset_y)
                y2 = min(1080, self.rows * self.grid_size * self.zoom_level + self.offset_y)
                self.canvas.create_line(x, y1, x, y2, width=1, fill="gray")
                items += 1
        
        for row in visible_rows:
            for col in visible_cols:
                
                data = self.grid_state.get((row,col))
                if data is None: continue
                
                pinned, color, name, info = data
                if not pinned: continue
                
                x1 = col * self.grid_size * self.zoom_level + self.offset_x
                y1 = row * self.grid_size * self.zoom_level + self.offset_y
                x2 = x1 + self.grid_size * self.zoom_level
                y2 = y1 + self.grid_size * self.zoom_level
                
                items += 1
                self.canvas.create_oval(x1+1, y1+1, x2-1, y2-1, fill=color, width=0)
                self.scaled_off = (10 * self.zoom_level / 5)
                self.canvas.create_oval(x1+self.scaled_off, y1+self.scaled_off, x2-self.scaled_off, y2-self.scaled_off, fill=color, width=(5 * self.zoom_level / 5), outline="white")

                if not name is None:
                    items += 1
                    names.append([x1,x2,y1,y2,name])
                
        for name in names:
            self.create_stroked_text(self.canvas, ((name[0]+name[1])/2, 10 * self.zoom_level + (name[2]+name[3])/2), text=name[4], text_font=font.Font(family="Permanent Marker", size = int(6 * self.zoom_level), weight="bold", slant="roman"), quality=3, stroke_width=3)

        self.num_objects = items

    def save_grid_state(self):
        with open("grid_state.json", "w") as f:
            save = {
                'size': (self.rows, self.cols)
            }
            for ind in self.grid_state:
                save[f'{ind[0]}:{ind[1]}'] = self.grid_state[ind]

            json.dump(save, f)

    def load_grid_state(self):
        try:
            with open("grid_state.json", "r") as f:
                loader = json.load(f)
                loader = dict(loader)
                size = loader['size']
                loader.pop('size')
                if size[0] <= self.rows and size[1] <= self.cols:
                    grid_state = {}
                    for el in loader:
                        _str = el.split(':')
                        grid_state[(int(_str[0]), int(_str[1]))] = loader[el]
                    self.grid_state = grid_state
                    self.update_grid()
                    
                    _info = tk.Label(self.root, text="Save Loaded", fg='green', font="System 20")
                    x,y = self.getCenterOfWindow(_info)
                    _info.place(x=x, y=y)
                    self.root.update()
                    self.root.after(100, _info.destroy())
                    
                else:
                    _info = tk.Label(self.root, text="Size of save is bigger than size now", fg='blue', font="System 20")
                    x,y = self.getCenterOfWindow(_info)
                    _info.place(x=x, y=y)
                    self.root.update()
                    self.root.after(100, _info.destroy())
        except FileNotFoundError:
            pass
        
    def getCenterOfWindow(self, widget : tk.Widget) -> tuple:
        widget.place(x=self.scr_width, y=self.scr_height)
        widget.wait_visibility()
        widget_w = widget.winfo_width()
        widget_h = widget.winfo_height()
        return (self.scr_width//2 - widget_w//2, self.scr_height//2 - widget_h//2)
    
    def createNotification(self):
        # TODO
        pass
            

def main():
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.iconphoto(True, PhotoImage(file="images/GUI/icon.png"))
    grid_map = GridMap(root)

    close_image = PhotoImage(file="images/GUI/close.png").subsample(10, 10)
    equalizer_image = PhotoImage(file="images/GUI/equalizer.png").subsample(10, 10)
    save_image = PhotoImage(file="images/GUI/save.png").subsample(10, 10)
    import_image = PhotoImage(file="images/GUI/import.png").subsample(10, 10)

    # Create a new panel at the bottom of the window
    bottom_panel = tk.Frame(root, bg="lightgrey", height=60)
    bottom_panel.pack(side=tk.BOTTOM, fill=tk.X)
    
    close_button = tk.Button(bottom_panel, image=close_image, bg="lightgrey", activebackground="lightgrey", padx=10, pady=10, bd=0, command=root.quit)
    close_button.image = close_image

    equalizer_button = tk.Button(bottom_panel, image=equalizer_image, bg="lightgrey", activebackground="lightgrey", padx=10, pady=10, bd=0, command=grid_map.toggle_settings_panel)
    equalizer_button.image = equalizer_image 

    save_button = tk.Button(bottom_panel, image=save_image, bg="lightgrey", activebackground="lightgrey", padx=10, pady=10, bd=0, command=grid_map.save_grid_state)
    save_image.image = save_image
    
    import_button = tk.Button(bottom_panel, image=import_image, bg="lightgrey", activebackground="lightgrey", padx=10, pady=10, bd=0, command=grid_map.load_grid_state)
    import_image.image = import_image
    
    # Move the buttons to the new panel
    bottom_panel.propagate(False)
    close_button.pack(side=tk.RIGHT, expand=True)
    equalizer_button.pack(side=tk.RIGHT, expand=True)
    save_button.pack(side=tk.LEFT, expand=True)
    import_button.pack(side=tk.LEFT, expand=True)

    root.mainloop()

if __name__ == "__main__":
    main()
