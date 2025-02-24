import os
import sys  # Tambahkan import sys
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, StringVar
from PIL import Image
import fitz
import io
import threading

class PDFCompressor:
    @staticmethod
    def compress_pdf(input_path, output_path, quality):
        """Kompres PDF dengan optimasi tingkat lanjut"""
        try:
            doc = fitz.open(input_path)
            compress_params = {
                "high": {
                    "dpi": 200,      # Dinaikkan dari 150
                    "quality": 80,   # Dinaikkan dari 50
                    "zoom": 0.95     # Dinaikkan dari 0.9
                },
                "medium": {
                    "dpi": 150,      # Dinaikkan dari 120
                    "quality": 60,   # Dinaikkan dari 30
                    "zoom": 0.8      # Dinaikkan dari 0.7
                },
                "low": {
                    "dpi": 120,      # Dinaikkan dari 96
                    "quality": 40,   # Dinaikkan dari 15
                    "zoom": 0.7      # Dinaikkan dari 0.5
                }
            }
            params = compress_params[quality]
            
            # Buat dokumen PDF baru
            new_doc = fitz.open()
            
            for page_num in range(len(doc)):
                # Ambil halaman dari dokumen asli
                page = doc[page_num]
                
                # Render halaman sebagai gambar dengan kualitas yang diinginkan
                zoom = params["zoom"]
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # Konversi ke PIL Image untuk kompresi
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Kompres gambar
                img_stream = io.BytesIO()
                img.save(img_stream, format='JPEG', 
                        quality=params["quality"], 
                        optimize=True,
                        dpi=[params["dpi"], params["dpi"]])
                img_stream.seek(0)
                
                # Buat halaman baru di dokumen baru
                new_page = new_doc.new_page(width=page.rect.width,
                                          height=page.rect.height)
                
                # Masukkan gambar yang sudah dikompres
                new_page.insert_image(new_page.rect, stream=img_stream.getvalue())

                # Salin teks dari halaman asli (jika ada)
                text_list = page.get_text("words")
                if text_list:
                    for text in text_list:
                        rect = fitz.Rect(text[:4])
                        new_page.insert_text(rect.tl, # top-left point
                                           text[4],   # the text
                                           fontsize=text[5], # font size
                                           color=(0, 0, 0))  # black color
            
            # Simpan dokumen yang sudah dikompress
            new_doc.save(output_path,
                        garbage=4,           # Hapus objek tidak terpakai
                        deflate=True,        # Kompres streams
                        clean=True,          # Bersihkan dan optimasi
                        linear=True,         # Optimasi untuk web
                        pretty=False,        # Minifikasi PDF
                        ascii=False)         # Gunakan binary encoding
            
            # Tutup kedua dokumen
            new_doc.close()
            doc.close()
            return True
            
        except Exception as e:
            raise Exception(f"Gagal kompres PDF: {str(e)}")

class DnDWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image & PDF Compressor")
        self.geometry("800x600")
        
        # Perbaikan setting icon
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            icon_path = os.path.join(base_path, 'icon.ico')
            print(f"Loading icon from: {icon_path}")
            
            if os.path.exists(icon_path):
                self.iconbitmap(default=icon_path)  # Tambahkan default=
                print("Icon loaded successfully")
            else:
                print(f"Icon not found at: {icon_path}")
        except Exception as e:
            print(f"Error setting icon: {e}")
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.configure(bg="#f0f0f0")
        
        self.setup_ui()
        self.processed_files = []
        self.current_progress = 0
        self.output_dir = None  # Tambahkan variabel untuk menyimpan direktori output

    def setup_ui(self):
        # Drag & Drop Area
        self.drop_label = ttk.Label(self, text="Seret file ke sini atau klik untuk memilih", 
                                  relief="groove", padding=30)
        self.drop_label.pack(pady=20, fill=tk.X, padx=20)
        self.drop_label.bind("<Button-1>", self.browse_files)

        # Quality Selection
        self.quality_frame = ttk.Frame(self)
        self.quality_frame.pack(pady=10)
        
        self.quality_var = StringVar(value="medium")
        ttk.Radiobutton(self.quality_frame, text="High", variable=self.quality_var, 
                       value="high").grid(row=0, column=0, padx=10)
        ttk.Radiobutton(self.quality_frame, text="Medium", variable=self.quality_var, 
                       value="medium").grid(row=0, column=1, padx=10)
        ttk.Radiobutton(self.quality_frame, text="Low", variable=self.quality_var, 
                       value="low").grid(row=0, column=2, padx=10)

        # Progress Bar
        self.progress = ttk.Progressbar(self, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=20)

        # Status Label
        self.status_label = ttk.Label(self, text="Status: Menunggu input...", font=("Arial", 10))
        self.status_label.pack(pady=10)

        # Action Buttons
        self.btn_frame = ttk.Frame(self)
        self.btn_frame.pack(pady=10)
        
        ttk.Button(self.btn_frame, text="Set Output Directory", 
                  command=self.set_output_directory).grid(row=0, column=0, padx=5)
        ttk.Button(self.btn_frame, text="Start Compression", 
                  command=self.start_compression).grid(row=0, column=1, padx=5)
        ttk.Button(self.btn_frame, text="Help", 
                  command=self.show_help).grid(row=0, column=2, padx=5)

    def set_output_directory(self):
        dir_path = filedialog.askdirectory(title="Pilih folder untuk menyimpan hasil kompresi")
        if (dir_path):
            self.output_dir = dir_path
            self.status_label.config(text=f"Output akan disimpan di: {dir_path}")

    def browse_files(self, event=None):
        files = filedialog.askopenfilenames(filetypes=[
            ("Supported Files", "*.jpg *.jpeg *.png *.pdf")
        ])
        if files:
            self.process_files(files)

    def process_files(self, files):
        self.processed_files = []
        valid_ext = (".jpg", ".jpeg", ".png", ".pdf")
        for f in files:
            if os.path.splitext(f)[1].lower() in valid_ext:
                self.processed_files.append(f)
            elif os.path.isdir(f):  # Jika direktori, tambahkan semua file di dalamnya
                for root, _, filenames in os.walk(f):
                    for filename in filenames:
                        if os.path.splitext(filename)[1].lower() in valid_ext:
                            self.processed_files.append(os.path.join(root, filename))
        
        self.progress["maximum"] = len(self.processed_files)
        self.drop_label.config(text=f"{len(self.processed_files)} file dipilih")
        self.status_label.config(text="File siap dikompres!")

    def start_compression(self):
        if not self.processed_files:
            messagebox.showwarning("Peringatan", "Pilih file terlebih dahulu!")
            return
        
        if not self.output_dir:
            messagebox.showwarning("Peringatan", "Pilih direktori output terlebih dahulu!")
            return
        
        threading.Thread(target=self.run_batch_compression).start()

    def run_batch_compression(self):
        quality = self.quality_var.get()
        total_files = len(self.processed_files)
        
        for idx, file in enumerate(self.processed_files, 1):
            try:
                ext = os.path.splitext(file)[1].lower()
                filename = os.path.basename(file)
                output_filename = f"{os.path.splitext(filename)[0]}_compressed{ext}"
                output_path = os.path.join(self.output_dir, output_filename)
                
                # Update status
                self.status_label.config(text=f"Mengompres {filename}...")
                
                if ext in (".jpg", ".jpeg", ".png"):
                    self.compress_image(file, output_path, quality)
                else:
                    PDFCompressor.compress_pdf(file, output_path, quality)
                
                self.current_progress = idx
                self.progress["value"] = idx
                self.update_idletasks()
            except Exception as e:
                messagebox.showerror("Error", f"Gagal kompres {file}:\n{str(e)}")
        
        self.status_label.config(text="Kompresi selesai!")
        messagebox.showinfo("Selesai", 
                          f"{total_files} file berhasil dikompres!\nTersimpan di: {self.output_dir}")

    def compress_image(self, input_path, output_path, quality):
        try:
            quality_params = {
                "high": {
                    "quality": 75,      # Reduced from 85
                    "subsampling": 1,   # Changed from 0 to 1
                    "optimize": True,
                    "progressive": True  # Added progressive JPEG
                },
                "medium": {
                    "quality": 65,      # Keep as is
                    "subsampling": 1,   
                    "optimize": True,
                },
                "low": {
                    "quality": 45,      # Keep as is
                    "subsampling": 2,   
                    "optimize": True,
                }
            }
            
            with Image.open(input_path) as img:
                # Convert to RGB if needed
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Calculate new dimensions while maintaining aspect ratio
                max_size = {
                    "high": 1800,    # Reduced from 2000
                    "medium": 1500,  # Keep as is
                    "low": 1000      # Keep as is
                }
                
                # Resize if image is larger than max size
                if max(img.size) > max_size[quality]:
                    ratio = min(max_size[quality] / max(img.size[0], img.size[1]))
                    new_size = tuple(int(dim * ratio) for dim in img.size)
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Save with optimized parameters
                img.save(
                    output_path, 
                    'JPEG',
                    **quality_params[quality]
                )
        except Exception as e:
            raise Exception(f"Failed to compress image: {str(e)}")

    def show_help(self):
        help_text = """**Kualitas Kompresi:**
- High: 200 DPI, 80% Quality (Recommended for important documents)
- Medium: 150 DPI, 60% Quality (Good balance)
- Low: 120 DPI, 40% Quality (Maximum compression)

**Fitur:**
1. Drag & Drop file/folder
2. Batch processing
3. Copy hasil ke direktori
4. Progress bar dan status proses

**Tips:**
- Gunakan 'High' untuk dokumen penting dengan gambar
- Gunakan 'Medium' untuk dokumen umum
- Gunakan 'Low' hanya jika ukuran file sangat kritis"""
        messagebox.showinfo("Panduan Penggunaan", help_text)

if __name__ == "__main__":
    app = DnDWindow()
    app.mainloop()