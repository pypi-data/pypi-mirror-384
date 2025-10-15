import os
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox
import importlib.util
import importlib


# Path to the converter script
SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "convert-legacy-llama.py")


def load_conversion_script():
    """Load the convert-legacy-llama.py script as a module."""
    if not os.path.exists(SCRIPT_PATH):
        root = ctk.CTk()
        root.withdraw()
        messagebox.showerror("Script Not Found", f"Error: '{SCRIPT_PATH}' not found.")
        sys.exit(1)

    try:
        # Ensure script’s directory is in sys.path so imports work
        script_dir = os.path.dirname(SCRIPT_PATH)
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        # Ensure gguf is loaded fresh
        try:
            import gguf
            importlib.reload(gguf)
        except ImportError:
            root = ctk.CTk()
            root.withdraw()
            messagebox.showerror("Dependency Error", "The 'gguf' library is not installed.\nRun: pip install gguf")
            print(e)

            sys.exit(1)

        spec = importlib.util.spec_from_file_location("convert_legacy_llama", SCRIPT_PATH)
        convert_module = importlib.util.module_from_spec(spec)
        sys.modules["convert_legacy_llama"] = convert_module
        spec.loader.exec_module(convert_module)
        return convert_module
    except Exception as e:
        root = ctk.CTk()
        root.withdraw()
        messagebox.showerror("Script Load Error", f"Failed to load conversion script:\n{e}")
        print(e)
        sys.exit(1)


class ConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.convert_module = load_conversion_script()

        # Theme and Window Config
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.title("Modern GGUF Converter")
        self.geometry("600x400")
        self.resizable(False, False)

        # --- Main Frame ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # --- Title ---
        title_label = ctk.CTkLabel(
            self.main_frame, text="Safetensors to GGUF",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(10, 20))

        # --- Model Folder Input ---
        ctk.CTkLabel(self.main_frame, text="HuggingFace Model Folder").grid(
            row=1, column=0, columnspan=2, sticky="w"
        )
        self.entry_model = ctk.CTkEntry(self.main_frame, placeholder_text="Path to your model folder...")
        self.entry_model.grid(row=2, column=0, padx=(10, 5), sticky="ew")
        ctk.CTkButton(self.main_frame, text="Browse...", width=100, command=self.browse_model).grid(
            row=2, column=1, padx=(5, 10)
        )

        # --- Output File Input ---
        ctk.CTkLabel(self.main_frame, text="Output GGUF File").grid(row=3, column=0, columnspan=2, sticky="w")
        self.entry_outfile = ctk.CTkEntry(self.main_frame, placeholder_text="Path to save the .gguf file...")
        self.entry_outfile.grid(row=4, column=0, padx=(10, 5), sticky="ew")
        ctk.CTkButton(self.main_frame, text="Save As...", width=100, command=self.browse_outfile).grid(
            row=4, column=1, padx=(5, 10)
        )

        # --- Quantization Type ---
        ctk.CTkLabel(self.main_frame, text="Quantization Type").grid(row=5, column=0, sticky="w")
        quant_options = ["f32", "f16", "q8_0", "q4_k_m", "q5_k_m", "q6_k"]
        self.outtype_var = ctk.StringVar(value="f16")
        self.outtype_menu = ctk.CTkOptionMenu(self.main_frame, variable=self.outtype_var, values=quant_options)
        self.outtype_menu.grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        # --- Convert Button ---
        ctk.CTkButton(
            self.main_frame,
            text="Convert to GGUF",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.run_conversion,
            height=40,
            fg_color="#4CAF50",
            hover_color="#45a049",
        ).grid(row=7, column=0, columnspan=2, pady=(30, 10), sticky="ew")

    def browse_model(self):
        folder = filedialog.askdirectory(title="Select HuggingFace Model Folder")
        if folder:
            self.entry_model.delete(0, ctk.END)
            self.entry_model.insert(0, os.path.normpath(folder))

    def browse_outfile(self):
        file = filedialog.asksaveasfilename(
            title="Save GGUF As", defaultextension=".gguf", filetypes=[("GGUF files", "*.gguf")]
        )
        if file:
            self.entry_outfile.delete(0, ctk.END)
            self.entry_outfile.insert(0, os.path.normpath(file))

    def run_conversion(self):
        model_dir = self.entry_model.get().strip()
        out_file = self.entry_outfile.get().strip()
        out_type = self.outtype_var.get()

        if not model_dir or not os.path.isdir(model_dir):
            messagebox.showerror("Error", "Please select a valid model folder!")
            return
        if not out_file:
            messagebox.showerror("Error", "Please select an output file path!")
            return

        argv_backup = sys.argv
        try:
            # Call script like CLI
            sys.argv = [
                "convert-legacy-llama.py",
                model_dir,
                "--outfile",
                out_file,
                "--outtype",
                out_type,
            ]
            messagebox.showinfo("Processing", "Conversion started. Please wait...")
            self.update_idletasks()
            self.convert_module.main()
            messagebox.showinfo("Success", f"Conversion finished!\nSaved at:\n{out_file}")
        except Exception as e:
            messagebox.showerror("Conversion Failed", f"Error during conversion:\n{e}")
            print(e)
        finally:
            sys.argv = argv_backup


def run():
    app = ConverterApp()
    app.mainloop()
