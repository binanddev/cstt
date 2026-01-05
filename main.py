
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from core import CompressionCore, FileFormatLayer


class CompressionApp:
    """Giao diện người dùng cho các thuật toán nén."""

    def __init__(self, root_window):
        """Khởi tạo ứng dụng và dựng giao diện."""
        self.root_window = root_window
        self.root_window.title("Shannon-Fano & Huffman Coding")
        self.root_window.geometry("650x500")

        # Lớp lõi xử lý thuật toán
        self.compression_core = CompressionCore()

        # Biến giao diện
        self.algorithm_var = tk.StringVar(value="Huffman")

        # Các phần tử giao diện
        self.primary_input_label = None
        self.main_file_entry = None
        self.result_text_widget = None

        self.initialize_user_interface()

    def initialize_user_interface(self):
        """Dựng toàn bộ giao diện và gắn sự kiện."""
        padding_config = {"padx": 10, "pady": 5}

        # Khối chọn thuật toán
        tk.Label(
            self.root_window, text="Chọn thuật toán:", font=("Arial", 10, "bold")
        ).pack(pady=(10, 5))
        ttk.Combobox(
            self.root_window,
            textvariable=self.algorithm_var,
            values=["Huffman", "Shannon-Fano"],
            state="readonly",
        ).pack()

        # Khối chọn file chính
        self.primary_input_label = tk.Label(
            self.root_window, text="File văn bản (.txt):", font=("Arial", 10, "bold")
        )
        self.primary_input_label.pack(**padding_config)
        self.main_file_entry = tk.Entry(self.root_window, width=70)
        self.main_file_entry.pack(**padding_config)
        tk.Button(
            self.root_window, text="Duyệt", command=self.browse_primary_file
        ).pack()

        # Nút thực thi
        tk.Button(
            self.root_window,
            text="CHẠY MÃ HÓA",
            bg="#0078d7",
            fg="white",
            font=("Arial", 10, "bold"),
            width=20,
            command=self.execute_processing,
        ).pack(pady=10)

        # Khu vực hiển thị kết quả
        self.result_text_widget = tk.Text(
            self.root_window,
            height=14,
            width=75,
            bg="#fafafa",
            font=("Courier New", 9),
        )
        self.result_text_widget.pack(**padding_config)

    @staticmethod
    def get_algorithm_slug(algorithm_name):
        """Chuyển tên thuật toán thành định dạng slug dùng cho tên thư mục."""
        if algorithm_name == "Shannon-Fano":
            return "shannon_fano"
        return algorithm_name.lower()

    def browse_primary_file(self):
        """Mở hộp thoại chọn file chính tùy theo chế độ/thuật toán."""
        selected_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if selected_path:
            self.main_file_entry.delete(0, tk.END)
            self.main_file_entry.insert(0, selected_path)

    def execute_processing(self):
        """Thực thi Encode dựa trên lựa chọn thuật toán."""
        input_file_path = self.main_file_entry.get()
        if not input_file_path or not os.path.exists(input_file_path):
            messagebox.showerror("Lỗi", "Vui lòng chọn file hợp lệ!")
            return

        try:
            algorithm_name = self.algorithm_var.get()
            self.result_text_widget.delete(1.0, tk.END)

            # Đọc văn bản nguồn
            with open(input_file_path, "r", encoding="utf-8") as input_file:
                source_text = input_file.read()
            if not source_text:
                messagebox.showwarning("Cảnh báo", "File trống!")
                return

            base_filename = os.path.splitext(os.path.basename(input_file_path))[0]
            algorithm_slug = self.get_algorithm_slug(algorithm_name)
            output_directory = os.path.join(
                os.path.dirname(input_file_path),
                f"{algorithm_slug}_encode_{base_filename}",
            )
            os.makedirs(output_directory, exist_ok=True)

            # Thực hiện encode
            encoded_bit_stream, code_table = self.compression_core.encode_text(
                source_text, algorithm_name
            )
            binary_output_path = os.path.join(output_directory, "data.bin")
            code_table_json_path = os.path.join(output_directory, "code_table.json")
            FileFormatLayer.save_bitstream(encoded_bit_stream, binary_output_path)
            FileFormatLayer.save_code_table(code_table, code_table_json_path)
            entropy_value, average_code_length, compression_efficiency = (
                self.compression_core.calculate_theoretical_metrics(
                    source_text, codes=code_table
                )
            )
            compressed_size_bytes = os.path.getsize(binary_output_path) + os.path.getsize(
                code_table_json_path
            )
            compressed_info_text = (
                f"File nén: {binary_output_path} + {code_table_json_path} "
                f"(tổng {compressed_size_bytes} bytes)"
            )

            original_file_size = os.path.getsize(input_file_path)
            saving_ratio_percent = (1 - compressed_size_bytes / original_file_size) * 100

            encode_result_text = (
                f"=== ENCODE ({algorithm_name}) ===\n"
                f"Ký tự đã xử lý: {len(source_text)}\n"
                f"Entropy nguồn (H): {entropy_value:.4f} bit/ký tự\n"
                f"Độ dài mã TB (L):  {average_code_length:.4f} bit/ký tự\n"
                f"Hiệu suất nén (η): {compression_efficiency:.2f}%\n"
                f"-----------------------------------\n"
                f"Kích thước file gốc: {original_file_size} bytes\n"
                f"{compressed_info_text}\n"
                f"Tỷ lệ tiết kiệm:     {saving_ratio_percent:.2f}%\n"
                f"Thư mục lưu: {output_directory}"
            )
            self.result_text_widget.insert(tk.END, encode_result_text)

        except Exception as error:
            messagebox.showerror("Lỗi hệ thống", f"Có lỗi xảy ra: {str(error)}")


if __name__ == "__main__":
    root_window = tk.Tk()
    app = CompressionApp(root_window)
    root_window.mainloop()