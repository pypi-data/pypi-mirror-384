import tkinter as tk
import pathlib
import os
import sys

class main_window(tk.Tk):
    '''
    '''
    def __init__(self, current_dir, icon_dir):
        super().__init__()
        
        # Load the splash screen
        try:
            from Splash_Screen import splash_screen
        except:
            from .Splash_Screen import splash_screen
            
        splash_screen_object = splash_screen(current_dir, icon_dir)
        self.gg_draw_glycans_path = splash_screen_object.get_gg_draw_path()
        
        # Class imports
        from tkinter import ttk
        from PIL import Image, ImageTk
        
        self.ttk = ttk
        self.Image = Image
        self.ImageTk = ImageTk
        
        # Destroy the splash screen
        splash_screen_object.destroy()
        
        # Class variables
        self.current_dir = current_dir
        self.icon_dir = icon_dir
        
        # Configure window properties
        self.title("GlycoGenius")
        self.iconphoto(False, self.ImageTk.PhotoImage(file=self.icon_dir))
        
        # Screen resolution to base off scalings
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        
        # self.ttk styles
        self.default_font_size = 10
        top_row_buttons_style = self.ttk.Style().configure("top_row.TButton", font=("Segoe UI", self.default_font_size), padding=0, justify="center")
        chromatograms_list_style = ttk.Style().configure("chromatograms_list.Treeview", bg="white", fg="black", font=("Segoe UI", self.default_font_size))
        qcp_frame_style = ttk.Style().configure("qcp_frame.TLabelframe", font=("Segoe UI", self.default_font_size))
        chromatogram_plot_frame_style = ttk.Style().configure("chromatogram.TLabelframe", font=("Segoe UI", self.default_font_size))
        
        # Place top row widgets
        self.create_top_row_widgets()
        self.place_top_row_widgets()
        
        # Place additional functions widgets
        self.create_add_fun_widgets()
        self.place_add_fun_widgets()
        
        # Place plot area widgets
        self.create_plot_area_widgets()
        self.place_plot_area_widgets()
        
        # Organize rows and columns
        self.grid_columnconfigure(1, weight=0, minsize=self.screen_width//20)
        self.grid_columnconfigure(11, weight=1)
        self.grid_columnconfigure(12, weight=0, minsize=self.screen_width//20)
        self.grid_rowconfigure(3, weight=1)
        
        # Set window minimum size to current one
        self.after(100, lambda: self.minsize(self.winfo_width(), self.winfo_height()))
        
    def right_pointing_arrow(self, parent, row, column, rowspan=1, pady=0, padx=0, sticky='nsew'):
        temp_widget = tk.Label(parent, text="▶", font=("Segoe UI", 24))
        temp_widget.grid(row=row, rowspan=rowspan, column=column, pady=pady, padx=padx, sticky=sticky)
        
    def create_top_row_widgets(self):
        # Main logo
        main_logo = self.Image.open(os.path.join(self.current_dir, "Assets/logo.png"))
        main_logo = main_logo.resize((self.screen_width//12, self.screen_width//12))
        self.main_logo = self.ImageTk.PhotoImage(main_logo)
        self.main_logo_widget = tk.Label(self, image=self.main_logo)
        
        # Select Files button
        self.select_files_frame = tk.Frame(self, bd=3, relief="flat") #Within a frame
        self.select_files_button = self.ttk.Button(self.select_files_frame, text="Select\nFiles", style="top_row.TButton", command=None)
        
        # Set Parameters button
        self.set_parameters_frame = tk.Frame(self, bd=3, relief="flat") #Within a frame
        self.set_parameters_button = self.ttk.Button(self.set_parameters_frame, text="Set\nParameters", style="top_row.TButton", command=None)
        
        # Generate Library button
        self.generate_library_frame = tk.Frame(self, bd=3, relief="flat") #Within a frame
        self.generate_library_button = self.ttk.Button(self.generate_library_frame, text="Generate Library", style="top_row.TButton", command=None)
        
        # Import Library button
        self.import_library_frame = tk.Frame(self, bd=3, relief="flat") #Within a frame
        self.import_library_button = self.ttk.Button(self.import_library_frame, text="Import Library", style="top_row.TButton", command=None)
        
        # Check Library button
        self.check_library_frame = tk.Frame(self, bd=3, relief="flat") #Within a frame
        self.check_library_button = self.ttk.Button(self.check_library_frame, text="Check\nLibrary", style="top_row.TButton", command=None)
        
        # Run Analysis button
        self.run_analysis_frame = tk.Frame(self, bd=3, relief="flat") #Within a frame
        self.run_analysis_button = self.ttk.Button(self.run_analysis_frame, text="Run\nAnalysis", style="top_row.TButton", command=None)
        
        # Export Results button
        self.export_results_frame = tk.Frame(self, bd=3, relief="flat") #Within a frame
        self.export_results_button = self.ttk.Button(self.export_results_frame, text="Export\nResults", style="top_row.TButton", command=None)
        
        # About button
        self.about_frame = tk.Frame(self, bd=3, relief="flat") #Within a frame
        self.about_button = self.ttk.Button(self.about_frame, text="About", style="top_row.TButton", command=None)
        
    def place_top_row_widgets(self):
        self.main_logo_widget.grid(row=0, rowspan=3, column=0, pady=0, padx=0, sticky='nsew')
        
        self.select_files_frame.grid(row=0, rowspan=2, column=1, pady=(10, 50), padx=0, sticky='nsew')
        self.select_files_button.pack(padx=0, pady=0, fill=tk.BOTH, expand=True)
        
        self.right_pointing_arrow(parent=self, row=0, rowspan=2, column=2, pady=(10, 50))
        
        self.set_parameters_frame.grid(row=0, rowspan=2, column=3, pady=(10, 50), padx=0, sticky='nsew')
        self.set_parameters_button.pack(padx=0, pady=0, fill=tk.BOTH, expand=True)
        
        self.right_pointing_arrow(parent=self, row=0, column=4, pady=(10, 0))
        self.right_pointing_arrow(parent=self, row=1, column=4, pady=(0, 50))
        
        self.generate_library_frame.grid(row=0, column=5, columnspan=2, pady=(10,0), padx=0, sticky='nsew')
        self.generate_library_button.pack(padx=0, pady=0, fill=tk.BOTH, expand=True)
        
        self.import_library_frame.grid(row=1, column=5, pady=(0,50), padx=0, sticky='nsew')
        self.import_library_button.pack(padx=0, pady=0, fill=tk.BOTH, expand=True)
        
        self.check_library_frame.grid(row=1, column=6, pady=(0,50), padx=0, sticky='nsew')
        self.check_library_button.pack(padx=0, pady=0, fill=tk.BOTH, expand=True)
        
        self.right_pointing_arrow(parent=self, row=0, column=7, pady=(10, 0))
        self.right_pointing_arrow(parent=self, row=1, column=7, pady=(0, 50))
        
        self.run_analysis_frame.grid(row=0, rowspan=2, column=8, pady=(10, 50), padx=0, sticky='nsew')
        self.run_analysis_button.pack(padx=0, pady=0, fill=tk.BOTH, expand=True)
        
        self.right_pointing_arrow(parent=self, row=0, rowspan=2, column=9, pady=(10, 50), sticky='nsew')
        
        self.export_results_frame.grid(row=0, rowspan=2, column=10, pady=(10, 50), padx=0, sticky='nsew')
        self.export_results_button.pack(padx=0, pady=0, fill=tk.BOTH, expand=True)
        
        self.about_frame.grid(row=0, rowspan=2, column=12, pady=(10, 50), padx=0, sticky='nsew')
        self.about_button.pack(padx=0, pady=0, fill=tk.BOTH, expand=True)
        
    def create_add_fun_widgets(self):
        # Spectra file editing button
        spectra_edit_icon = self.Image.open(os.path.join(self.current_dir, "Assets/spectra_edit.png"))
        self.spectra_edit_icon = self.ImageTk.PhotoImage(spectra_edit_icon)
        self.spectra_edit_button = self.ttk.Button(self, image=self.spectra_edit_icon, command=None)
        
        # 2-D plot button
        two_d_icon = self.Image.open(os.path.join(self.current_dir, "Assets/heatmap_small.png"))
        self.two_d_icon = self.ImageTk.PhotoImage(two_d_icon)
        self.two_d_button = self.ttk.Button(self, image=self.two_d_icon, command=None)
        
        # MIS button
        mis_icon = self.Image.open(os.path.join(self.current_dir, "Assets/mis.png"))
        self.mis_icon = self.ImageTk.PhotoImage(mis_icon)
        self.mis_button = self.ttk.Button(self, image=self.mis_icon, command=None)
        
        # Quick trace button
        quick_trace_icon = self.Image.open(os.path.join(self.current_dir, "Assets/eic.png"))
        self.quick_trace_icon = self.ImageTk.PhotoImage(quick_trace_icon)
        self.quick_trace_button = self.ttk.Button(self, image=self.quick_trace_icon, command=None)
        
        # GG draw button
        ggdraw_on_icon = self.Image.open(os.path.join(self.current_dir, "Assets/gg_draw.png"))
        self.ggdraw_on_icon = self.ImageTk.PhotoImage(ggdraw_on_icon)
        ggdraw_off_icon = self.Image.open(os.path.join(self.current_dir, "Assets/gg_draw_off.png"))
        self.ggdraw_off_icon = self.ImageTk.PhotoImage(ggdraw_off_icon)
        self.gg_draw_button = self.ttk.Button(self, image=self.ggdraw_on_icon, command=None)
        
    def place_add_fun_widgets(self):
        self.spectra_edit_button.grid(row=1, rowspan=2, column=1, columnspan=12, pady=(50,0), padx=(0, 5), sticky='ne')
        
        self.two_d_button.grid(row=1, rowspan=2, column=1, columnspan=12, pady=(50,0), padx=(0, 40), sticky='ne')
        
        self.mis_button.grid(row=1, rowspan=2, column=1, columnspan=12, pady=(50,0), padx=(0, 75), sticky='ne')
        
        self.quick_trace_button.grid(row=1, rowspan=2, column=1, columnspan=12, pady=(50,0), padx=(0, 110), sticky='ne')
        
        self.gg_draw_button.grid(row=1, rowspan=2, column=1, columnspan=12, pady=(50,0), padx=(0, 145), sticky='ne')
        
    def create_plot_area_widgets(self):
        # Create panned window for plot area widgets
        self.left_right_paned_window = tk.PanedWindow(self, sashwidth=5, orient=tk.HORIZONTAL)
       
        # Create the left side widgets frame in the left/right paned window
        self.left_side_widgets_frame = self.ttk.Frame(self.left_right_paned_window)
        
        # Samples dropdown on the left side frame
        self.samples_dropdown = self.ttk.Combobox(self.left_side_widgets_frame, state="readonly", values=[1, 2, 3])
        
        # Filter list entry field
        self.filter_list = tk.Entry(self.left_side_widgets_frame, fg='grey', width=6)
        self.filter_list.insert(0, "Filter the list of glycans...")
        
        # Chromatograms/glycans list
        self.chromatograms_list_scrollbar = tk.Scrollbar(self.left_side_widgets_frame, orient=tk.VERTICAL)
        self.chromatograms_list = self.ttk.Treeview(self.left_side_widgets_frame, height=15, style="chromatograms_list.Treeview", yscrollcommand=self.chromatograms_list_scrollbar.set)
        self.chromatograms_list["show"] = "tree" #removes the header
        self.chromatograms_list["columns"] = ("#1")
        self.chromatograms_list.column("#0", width=230)
        self.chromatograms_list.column("#1", width=35, stretch=False) #this column is for showing ambiguities/ms2
        
        # Compare samples button
        self.compare_samples_button = self.ttk.Button(self.left_side_widgets_frame, text="Compare samples", style="top_row.TButton", command=None)
        
        # Plot graph button
        self.plot_graph_button = self.ttk.Button(self.left_side_widgets_frame, text="Plot Graph", style="top_row.TButton", command=None)
        
        # Quality criteria parameters frame
        self.qcp_frame = self.ttk.Labelframe(self.left_side_widgets_frame, text="Quality Scores Thresholds:", style="qcp_frame.TLabelframe")
        
        # Widgets inside QC parameters frame left side
        self.check_qc_dist_button = self.ttk.Button(self.qcp_frame, text="Check Scores Distribution", style="top_row.TButton", command=None)
        self.iso_fit_label = self.ttk.Label(self.qcp_frame, text='Minimum Isotopic Fitting Score:', font=("Segoe UI", self.default_font_size))
        self.curve_fit_label = self.ttk.Label(self.qcp_frame, text='Minimum Curve Fitting Score:', font=("Segoe UI", self.default_font_size))
        self.s_n_label = self.ttk.Label(self.qcp_frame, text='Minimum Signal-to-Noise Ratio:', font=("Segoe UI", self.default_font_size))
        self.ppm_error_label = self.ttk.Label(self.qcp_frame, text='Min/Max PPM Error:', font=("Segoe UI", self.default_font_size))
        
        # Widgets inside QC parameters frame right side
        self.iso_fit_entry = self.ttk.Spinbox(self.qcp_frame, width=5, from_=0, to=1.0, increment=0.01)
        self.iso_fit_entry.insert(0, 0.8) # Placeholder number
        self.curve_fit_entry = self.ttk.Spinbox(self.qcp_frame, width=5, from_=0, to=1.0, increment=0.01)
        self.curve_fit_entry.insert(0, 0.8) # Placeholder number
        self.s_n_entry = self.ttk.Spinbox(self.qcp_frame, width=5, from_=0, to=9999, increment=1)
        self.s_n_entry.insert(0, 3) # Placeholder number
        self.ppm_error_min_entry = self.ttk.Spinbox(self.qcp_frame, width=5, from_=-999, to=999, increment=1)
        self.ppm_error_min_entry.insert(0, -10) # Placeholder number
        self.ppm_error_hyphen_label = self.ttk.Label(self.qcp_frame, text='-', font=("Segoe UI", self.default_font_size))
        self.ppm_error_max_entry = self.ttk.Spinbox(self.qcp_frame, width=5, from_=-999, to=999, increment=1)
        self.ppm_error_max_entry.insert(0, 10) # Placeholder number
        
        # QC numbers
        self.chromatograms_qc_numbers = self.ttk.Label(self.left_side_widgets_frame, text=f"Compositions Quality:\n        Good: {0}    Average: {0}    Bad: {0}\n        Ambiguities: {0}", font=("Segoe UI", self.default_font_size))
    
        # Add a top/bottom paned window to the right side pane of the right/left pane
        self.paned_window_plots = tk.PanedWindow(self.left_right_paned_window, sashwidth=5, orient=tk.VERTICAL)
        
        # Right side widgets - Chromatogram plot frame
        self.chromatogram_plot_frame = self.ttk.Labelframe(self.paned_window_plots, text="Chromatogram/Electropherogram Viewer", style="chromatogram.TLabelframe")
        
        # Right side widgets - Spectra plot frame
        self.spectra_plot_frame = self.ttk.Labelframe(self.paned_window_plots, text="Spectra Viewer", style="chromatogram.TLabelframe")
    
    def place_plot_area_widgets(self):
        self.left_right_paned_window.grid(row=3, column=0, columnspan=13, padx = 0, pady = (0, 10), sticky='nsew')
        self.left_side_widgets_frame.grid_columnconfigure(0, weight=1)
        self.left_side_widgets_frame.grid_columnconfigure(1, weight=1)
        self.left_side_widgets_frame.grid_rowconfigure(0, weight=0)
        self.left_side_widgets_frame.grid_rowconfigure(1, weight=0)
        self.left_side_widgets_frame.grid_rowconfigure(2, weight=1)
        self.left_side_widgets_frame.grid_rowconfigure(3, weight=0)
        self.left_side_widgets_frame.grid_rowconfigure(4, weight=0)
        
        # Left side widgets
        self.left_right_paned_window.add(self.left_side_widgets_frame)
        self.samples_dropdown.grid(row=0, column=0, columnspan=2, padx=10, sticky='new')
        self.filter_list.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 0), sticky='new')
        self.chromatograms_list_scrollbar.config(command=self.chromatograms_list.yview, width=10)
        self.chromatograms_list.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 0), sticky="nsew")
        self.chromatograms_list_scrollbar.grid(row=2, column=0, columnspan=2, pady=(0, 0), sticky="nse")
        self.compare_samples_button.grid(row=3, column=0, padx=(10, 0), pady=(0, 0), sticky="sew")
        self.plot_graph_button.grid(row=3, column=1, padx=(0, 10), pady=(0, 0), sticky="sew")
        
        # QCP Frame and its contents
        self.qcp_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=(0, 0), sticky="sew")
        self.qcp_frame.grid_columnconfigure(0, weight=1)
        self.qcp_frame.grid_columnconfigure(1, weight=0)
        self.qcp_frame.grid_rowconfigure(0, weight=0)
        self.qcp_frame.grid_rowconfigure(1, weight=0)
        self.qcp_frame.grid_rowconfigure(2, weight=0)
        self.qcp_frame.grid_rowconfigure(3, weight=0)
        self.qcp_frame.grid_rowconfigure(4, weight=0)
        
        self.check_qc_dist_button.grid(row=0, column=0, columnspan=2, padx=10, pady=(5, 0), sticky="new")
        self.iso_fit_label.grid(row=1, column=0, padx=(10, 10), pady=(5, 0), sticky="w")
        self.iso_fit_entry.grid(row=1, column=1, padx=(5, 10), pady=(5, 0), sticky='e')
        self.curve_fit_label.grid(row=2, column=0, padx=(10, 10), pady=(5, 0), sticky="w")
        self.curve_fit_entry.grid(row=2, column=1, padx=(5, 10), pady=(5, 0), sticky='e')
        self.s_n_label.grid(row=3, column=0, padx=(10, 10), pady=(5, 0), sticky="w")
        self.s_n_entry.grid(row=3, column=1, padx=(5, 10), pady=(5, 0), sticky='e')
        self.ppm_error_label.grid(row=4, column=0, padx=(10, 10), pady=(5, 10), sticky="w")
        self.ppm_error_min_entry.grid(row=4, column=0, padx=(10, 0), pady=(5, 10), sticky="e")
        self.ppm_error_hyphen_label.grid(row=4, column=1, padx=(0, 60), pady=(5, 10), sticky="e")
        self.ppm_error_max_entry.grid(row=4, column=1, padx=(5, 10), pady=(5, 10), sticky='e')
        self.chromatograms_qc_numbers.grid(row=5, column=0, columnspan=2, padx=10, pady=(0, 0), sticky="sew")
        
        # Right side widgets
        self.left_right_paned_window.add(self.paned_window_plots)
        self.chromatogram_plot_frame.pack(fill=tk.BOTH, expand=True)
        self.paned_window_plots.add(self.chromatogram_plot_frame, stretch='always')
        self.paned_window_plots.paneconfigure(self.chromatogram_plot_frame, minsize=self.screen_height//4)
        
        self.spectra_plot_frame.pack(fill=tk.BOTH, expand=True)
        self.paned_window_plots.add(self.spectra_plot_frame, stretch='always')
        self.paned_window_plots.paneconfigure(self.spectra_plot_frame, minsize=self.screen_height//4)
        
        # Chromatogram frame
        
        
        # Spectra frame
        
        
        self.left_right_paned_window.paneconfigure(self.left_side_widgets_frame, minsize=self.screen_width//7)
        self.left_right_paned_window.paneconfigure(self.paned_window_plots, minsize=self.screen_width//5)
        
def main():    
    # Check if running from EXE or py
    if getattr(sys, 'frozen', False):
        current_dir = os.path.dirname(sys.executable)
    else:
        current_dir = pathlib.Path(__file__).parent.resolve()
        
    icon_dir = os.path.join(current_dir, "Assets/gg_icon.ico")
    
    glycogenius_gui = main_window(current_dir, icon_dir)
    glycogenius_gui.mainloop()  
    
if __name__ == "__main__":
    main()