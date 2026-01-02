
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os, json
from core import CompressionCore, FileFormatLayer

class CompressionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Shannon-Fano, Huffman & Arithmetic Coding")
        self.root.geometry("650x520")
        self.core = CompressionCore()
        self.setup_ui()

    def setup_ui(self):
        pad_cfg = {'padx': 10, 'pady': 5}
        
        mode_frame = tk.Frame(self.root)
        mode_frame.pack(**pad_cfg)
        tk.Label(mode_frame, text="Chọn chế độ:").pack(side=tk.LEFT, padx=(0, 8))
        self.mode_var = tk.StringVar(value="Encode")
        ttk.Combobox(mode_frame, textvariable=self.mode_var,
                     values=["Encode", "Decode"], state="readonly",
                     width=10).pack(side=tk.LEFT)

        tk.Label(self.root, text="Chọn thuật toán:", font=('Arial', 10, 'bold')).pack(pady=(10, 5))
        self.algo_var = tk.StringVar(value="Huffman")
        ttk.Combobox(self.root, textvariable=self.algo_var, 
                     values=["Huffman", "Shannon-Fano", "Arithmetic"], state="readonly").pack()

        self.input1_label = tk.Label(self.root, text="File văn bản (.txt):", font=('Arial', 10, 'bold'))
        self.input1_label.pack(**pad_cfg)
        self.path_entry = tk.Entry(self.root, width=70)
        self.path_entry.pack(**pad_cfg)
        tk.Button(self.root, text="Duyệt", command=self.browse_file_main).pack()

        self.input2_label = tk.Label(self.root, text="Bảng mã (.json) cho giải mã Huffman/Shannon-Fano:", font=('Arial', 10, 'bold'))
        self.input2_label.pack(**pad_cfg)
        self.path_entry_aux = tk.Entry(self.root, width=70)
        self.path_entry_aux.pack(**pad_cfg)
        tk.Button(self.root, text="Duyệt", command=self.browse_file_aux).pack()

        tk.Button(self.root, text="CHẠY MÃ HÓA", bg="#0078d7", fg="white", 
                  font=('Arial', 10, 'bold'), width=20, command=self.process).pack(pady=10)

        self.result_text = tk.Text(self.root, height=14, width=75, bg="#fafafa", font=('Courier New', 9))
        self.result_text.pack(**pad_cfg)

        # Bind updates
        for var in [self.mode_var, self.algo_var]:
            var.trace_add('write', lambda *_: self.update_labels())
        self.update_labels()

    @staticmethod
    def algo_slug(algo):
        if algo == "Shannon-Fano":
            return "shannon_fano"
        return algo.lower()

    def browse_file_main(self):
        mode = self.mode_var.get()
        algo = self.algo_var.get()
        if mode == "Encode":
            filetypes = [("Text files", "*.txt")]
        else:
            if algo == "Arithmetic":
                filetypes = [("Arithmetic JSON", "*.json")]
            else:
                filetypes = [("Binary files", "*.bin")]
        f = filedialog.askopenfilename(filetypes=filetypes)
        if f:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, f)

    def browse_file_aux(self):
        mode = self.mode_var.get()
        algo = self.algo_var.get()
        if mode == "Encode" or algo == "Arithmetic":
            messagebox.showinfo("Thông tin", "Không cần file phụ trong chế độ hiện tại.")
            return
        f = filedialog.askopenfilename(filetypes=[("Code table JSON", "*.json")])
        if f:
            self.path_entry_aux.delete(0, tk.END)
            self.path_entry_aux.insert(0, f)

    def update_labels(self):
        mode = self.mode_var.get()
        algo = self.algo_var.get()
        if mode == "Encode":
            self.input1_label.config(text="File văn bản (.txt):")
            self.input2_label.config(text="Bảng mã (.json) – không cần cho Encode")
            self.path_entry_aux.configure(state='normal')
            self.path_entry_aux.delete(0, tk.END)
            self.path_entry_aux.configure(state='disabled')
        else:
            if algo == "Arithmetic":
                self.input1_label.config(text="File arithmetic.json:")
                self.input2_label.config(text="Không cần file phụ cho Arithmetic Decode")
                self.path_entry_aux.configure(state='normal')
                self.path_entry_aux.delete(0, tk.END)
                self.path_entry_aux.configure(state='disabled')
            else:
                self.input1_label.config(text="File nhị phân (.bin):")
                self.input2_label.config(text="Bảng mã (.json) đi kèm:")
                self.path_entry_aux.configure(state='normal')

    def process(self):
        input_path = self.path_entry.get()
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("Lỗi", "Vui lòng chọn file hợp lệ!")
            return

        try:
            algo = self.algo_var.get()
            mode = self.mode_var.get()
            self.result_text.delete(1.0, tk.END)

            if mode == "Encode":
                # Đọc văn bản nguồn
                with open(input_path, 'r', encoding='utf-8') as f:
                    data = f.read()
                if not data:
                    messagebox.showwarning("Cảnh báo", "File trống!")
                    return

                base_name = os.path.splitext(os.path.basename(input_path))[0]
                algo_slug = self.algo_slug(algo)
                output_dir = os.path.join(
                    os.path.dirname(input_path),
                    f"{algo_slug}_encode_{base_name}"
                )
                os.makedirs(output_dir, exist_ok=True)

                if algo == "Arithmetic":
                    payload = self.core.arithmetic_encode(data)
                    json_path = os.path.join(output_dir, "arithmetic.json")
                    FileFormatLayer.save_arithmetic_payload(payload, json_path)
                    h, l, eff = self.core.calculate_theoretical_metrics(data, is_arithmetic=True)
                    comp_size = os.path.getsize(json_path)
                    comp_info = f"File nén: {json_path} ({comp_size} bytes)"
                else:
                    bit_string, codes = self.core.encode_text(data, algo)
                    bin_path = os.path.join(output_dir, "data.bin")
                    json_path = os.path.join(output_dir, "code_table.json")
                    FileFormatLayer.save_bitstream(bit_string, bin_path)
                    FileFormatLayer.save_code_table(codes, json_path)
                    h, l, eff = self.core.calculate_theoretical_metrics(data, codes=codes)
                    comp_size = os.path.getsize(bin_path) + os.path.getsize(json_path)
                    comp_info = f"File nén: {bin_path} + {json_path} (tổng {comp_size} bytes)"

                orig_size = os.path.getsize(input_path)
                actual_ratio = (1 - comp_size / orig_size) * 100

                res = (
                    f"=== ENCODE ({algo}) ===\n"
                    f"Ký tự đã xử lý: {len(data)}\n"
                    f"Entropy nguồn (H): {h:.4f} bit/ký tự\n"
                    f"Độ dài mã TB (L):  {l:.4f} bit/ký tự\n"
                    f"Hiệu suất nén (η): {eff:.2f}%\n"
                    f"-----------------------------------\n"
                    f"Kích thước file gốc: {orig_size} bytes\n"
                    f"{comp_info}\n"
                    f"Tỷ lệ tiết kiệm:     {actual_ratio:.2f}%\n"
                    f"Thư mục lưu: {output_dir}"
                )
                self.result_text.insert(tk.END, res)
            else:
                base_name = os.path.splitext(os.path.basename(input_path))[0]
                algo_slug = self.algo_slug(algo)
                output_dir = os.path.join(
                    os.path.dirname(input_path),
                    f"{algo_slug}_decode_{base_name}"
                )
                os.makedirs(output_dir, exist_ok=True)
                output_text = os.path.join(output_dir, "decoded.txt")

                if algo == "Arithmetic":
                    payload = FileFormatLayer.load_arithmetic_payload(input_path)
                    decoded = self.core.arithmetic_decode(payload)
                else:
                    code_table_path = self.path_entry_aux.get()
                    if not code_table_path or not os.path.exists(code_table_path):
                        messagebox.showerror("Lỗi", "Cần chọn file code_table.json hợp lệ!")
                        return
                    bit_string = FileFormatLayer.load_bitstream(input_path)
                    code_table = FileFormatLayer.load_code_table(code_table_path)
                    decoded = self.core.decode_text(bit_string, code_table)

                with open(output_text, 'w', encoding='utf-8') as f:
                    f.write(decoded)

                res = (
                    f"=== DECODE ({algo}) ===\n"
                    f"Số ký tự khôi phục: {len(decoded)}\n"
                    f"Kết quả lưu tại: {output_text}"
                )
                self.result_text.insert(tk.END, res)

        except Exception as e:
            messagebox.showerror("Lỗi hệ thống", f"Có lỗi xảy ra: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CompressionApp(root)
    root.mainloop()