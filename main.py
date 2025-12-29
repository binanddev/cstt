# import tkinter as tk
# from tkinter import filedialog, messagebox, ttk
# import os
# import json
# from core import CompressionCore

# class CompressionApp:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("Công cụ Mã hóa Shannon-Fano & Huffman")
#         self.root.geometry("500x450")
#         self.core = CompressionCore()
        
#         self.setup_ui()

#     def setup_ui(self):
#         # File selection
#         tk.Label(self.root, text="Chọn file .txt cần nén:").pack(pady=10)
#         self.path_entry = tk.Entry(self.root, width=50)
#         self.path_entry.pack(pady=5)
#         tk.Button(self.root, text="Duyệt File", command=self.browse_file).pack(pady=5)

#         # Algorithm selection
#         tk.Label(self.root, text="Chọn thuật toán:").pack(pady=10)
#         self.algo_var = tk.StringVar(value="Huffman")
#         ttk.Combobox(self.root, textvariable=self.algo_var, values=["Huffman", "Shannon-Fano"]).pack()

#         # Action button
#         tk.Button(self.root, text="Nén và Tính toán", command=self.process, bg="green", fg="white", height=2).pack(pady=20)

#         # Results area
#         self.result_text = tk.Text(self.root, height=10, width=55)
#         self.result_text.pack(pady=10)

#     def browse_file(self):
#         filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
#         self.path_entry.delete(0, tk.END)
#         self.path_entry.insert(0, filename)

#     def process(self):
#         input_path = self.path_entry.get()
#         if not input_path or not os.path.exists(input_path):
#             messagebox.showerror("Lỗi", "Vui lòng chọn file hợp lệ!")
#             return

#         with open(input_path, 'r', encoding='utf-8') as f:
#             data = f.read()

#         if not data:
#             messagebox.showwarning("Chú ý", "File trống!")
#             return

#         # Thực hiện mã hóa
#         algo = self.algo_var.get()
#         if algo == "Huffman":
#             codes = self.core.huffman_encode(data)
#         else:
#             codes = self.core.shannon_fano_encode(data)

#         # Tạo folder output
#         base_name = os.path.basename(input_path).split('.')[0]
#         output_dir = f"output_{algo}_{base_name}"
#         os.makedirs(output_dir, exist_ok=True)

#         # Lưu bảng mã và file bin
#         bin_path = os.path.join(output_dir, "compressed.bin")
#         table_path = os.path.join(output_dir, "code_table.json")
        
#         self.core.save_binary(data, codes, bin_path)
#         with open(table_path, 'w', encoding='utf-8') as f:
#             json.dump(codes, f, indent=4)

#         # Tính toán thông số
#         h, l, eff = self.core.calculate_theoretical_metrics(data, codes)
        
#         original_size = os.path.getsize(input_path)
#         compressed_size = os.path.getsize(bin_path)
#         actual_ratio = (1 - compressed_size / original_size) * 100

#         # Hiển thị kết quả
#         self.result_text.delete(1.0, tk.END)
#         results = (
#             f"--- Kết quả ({algo}) ---\n"
#             f"1. Entropy (H): {h:.4f} bits/symbol\n"
#             f"2. Chiều dài TB (L): {l:.4f} bits/symbol\n"
#             f"3. Hiệu suất (η): {eff:.2f}%\n"
#             f"----------------------------\n"
#             f"Kích thước gốc: {original_size} bytes\n"
#             f"Kích thước nén: {compressed_size} bytes\n"
#             f"Tỉ lệ nén thực tế: {actual_ratio:.2f}%\n"
#             f"\nĐã lưu tại thư mục: {output_dir}"
#         )
#         self.result_text.insert(tk.END, results)

# if __name__ == "__main__":
#     root = tk.Tk()
#     app = CompressionApp(root)
#     root.mainloop()

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os, json
from core import CompressionCore

class CompressionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Shannon-Fano, Huffman & Arithmetic Analysis")
        self.root.geometry("550x500")
        self.core = CompressionCore()
        self.setup_ui()

    def setup_ui(self):
        pad_cfg = {'padx': 10, 'pady': 5}
        
        tk.Label(self.root, text="Chọn file văn bản (ASCII/English):", font=('Arial', 10, 'bold')).pack(**pad_cfg)
        self.path_entry = tk.Entry(self.root, width=60)
        self.path_entry.pack(**pad_cfg)
        tk.Button(self.root, text="Duyệt File", command=self.browse_file).pack()

        tk.Label(self.root, text="Chọn thuật toán:").pack(pady=(15, 5))
        self.algo_var = tk.StringVar(value="Huffman")
        ttk.Combobox(self.root, textvariable=self.algo_var, 
                     values=["Huffman", "Shannon-Fano", "Arithmetic"], state="readonly").pack()

        tk.Button(self.root, text="CHẠY MÃ HÓA", bg="#0078d7", fg="white", 
                  font=('Arial', 10, 'bold'), width=20, command=self.process).pack(pady=20)

        self.result_text = tk.Text(self.root, height=12, width=65, bg="#fafafa", font=('Courier New', 9))
        self.result_text.pack(**pad_cfg)

    def browse_file(self):
        f = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if f:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, f)

    def process(self):
        input_path = self.path_entry.get()
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("Lỗi", "Vui lòng chọn file .txt hợp lệ!")
            return

        try:
            # Đọc với utf-8 để xử lý mọi ký tự tiếng Anh/đặc biệt
            with open(input_path, 'r', encoding='utf-8') as f:
                data = f.read()
            
            if not data:
                messagebox.showwarning("Cảnh báo", "File trống!")
                return

            algo = self.algo_var.get()
            base_name = os.path.basename(input_path).split('.')[0]
            output_dir = f"result_{algo}_{base_name}"
            os.makedirs(output_dir, exist_ok=True)

            bin_path = os.path.join(output_dir, "data.bin")
            
            if algo == "Arithmetic":
                self.core.save_arithmetic_pseudo_bin(data, bin_path)
                h, l, eff = self.core.calculate_theoretical_metrics(data, is_arithmetic=True)
            else:
                codes = self.core.huffman_encode(data) if algo == "Huffman" else self.core.shannon_fano_encode(data)
                self.core.save_binary(data, codes, bin_path)
                with open(os.path.join(output_dir, "code_table.json"), 'w', encoding='utf-8') as f:
                    json.dump(codes, f, indent=4, ensure_ascii=False)
                h, l, eff = self.core.calculate_theoretical_metrics(data, codes=codes)

            orig_size = os.path.getsize(input_path)
            comp_size = os.path.getsize(bin_path)
            actual_ratio = (1 - comp_size / orig_size) * 100

            self.result_text.delete(1.0, tk.END)
            res = (
                f"=== KẾT QUẢ PHÂN TÍCH ({algo}) ===\n"
                f"Ký tự đã xử lý: {len(data)}\n"
                f"Entropy nguồn (H): {h:.4f} bit/ký tự\n"
                f"Độ dài mã TB (L):  {l:.4f} bit/ký tự\n"
                f"Hiệu suất nén (η): {eff:.2f}%\n"
                f"-----------------------------------\n"
                f"Kích thước file gốc: {orig_size} bytes\n"
                f"Kích thước nén thực: {comp_size} bytes\n"
                f"Tỷ lệ tiết kiệm:     {actual_ratio:.2f}%\n"
                f"-----------------------------------\n"
                f"Thư mục lưu: {output_dir}"
            )
            self.result_text.insert(tk.END, res)
            
        except Exception as e:
            messagebox.showerror("Lỗi hệ thống", f"Có lỗi xảy ra: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CompressionApp(root)
    root.mainloop()