
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from core import CompressionCore, FileFormatLayer


class CompressionApp:
    """Giao diện người dùng cho các thuật toán nén/giải nén."""

    def __init__(self, root_window):
        """Khởi tạo ứng dụng và dựng giao diện."""
        self.root_window = root_window
        self.root_window.title("Shannon-Fano & Huffman Coding")
        self.root_window.geometry("650x500")

        # Lớp lõi xử lý thuật toán
        self.compression_core = CompressionCore()

        # Biến giao diện
        self.operation_mode_var = tk.StringVar(value="Encode")
        self.algorithm_var = tk.StringVar(value="Huffman")

        # Các phần tử giao diện
        self.primary_input_label = None
        self.secondary_input_label = None
        self.main_file_entry = None
        self.auxiliary_file_entry = None
        self.result_text_widget = None

        self.initialize_user_interface()

    def initialize_user_interface(self):
        """Dựng toàn bộ giao diện và gắn sự kiện."""
        padding_config = {"padx": 10, "pady": 5}

        # Khối chọn chế độ Encode/Decode
        mode_frame = tk.Frame(self.root_window)
        mode_frame.pack(**padding_config)
        tk.Label(mode_frame, text="Chọn chế độ:").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Combobox(
            mode_frame,
            textvariable=self.operation_mode_var,
            values=["Encode", "Decode"],
            state="readonly",
            width=10,
        ).pack(side=tk.LEFT)

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

        # Khối chọn file phụ (bảng mã) cho Decode
        self.secondary_input_label = tk.Label(
            self.root_window,
            text="Bảng mã (.json) cho giải mã Huffman/Shannon-Fano:",
            font=("Arial", 10, "bold"),
        )
        self.secondary_input_label.pack(**padding_config)
        self.auxiliary_file_entry = tk.Entry(self.root_window, width=70)
        self.auxiliary_file_entry.pack(**padding_config)
        tk.Button(
            self.root_window, text="Duyệt", command=self.browse_auxiliary_file
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

        # Theo dõi thay đổi mode/algorithm để cập nhật label, enable/disable input
        for tracking_var in [self.operation_mode_var, self.algorithm_var]:
            tracking_var.trace_add("write", lambda *_: self.refresh_labels())
        self.refresh_labels()

    @staticmethod
    def get_algorithm_slug(algorithm_name):
        """Chuyển tên thuật toán thành định dạng slug dùng cho tên thư mục."""
        if algorithm_name == "Shannon-Fano":
            return "shannon_fano"
        return algorithm_name.lower()

    def browse_primary_file(self):
        """Mở hộp thoại chọn file chính tùy theo chế độ/thuật toán."""
        operation_mode = self.operation_mode_var.get()
        if operation_mode == "Encode":
            filetypes = [("Text files", "*.txt")]
        else:
            filetypes = [("Binary files", "*.bin")]

        selected_path = filedialog.askopenfilename(filetypes=filetypes)
        if selected_path:
            self.main_file_entry.delete(0, tk.END)
            self.main_file_entry.insert(0, selected_path)

    def browse_auxiliary_file(self):
        """Mở hộp thoại chọn file phụ (bảng mã) cho chế độ Decode."""
        operation_mode = self.operation_mode_var.get()
        if operation_mode == "Encode":
            messagebox.showinfo("Thông tin", "Không cần file phụ trong chế độ hiện tại.")
            return

        selected_path = filedialog.askopenfilename(
            filetypes=[("Code table JSON", "*.json")]
        )
        if selected_path:
            self.auxiliary_file_entry.delete(0, tk.END)
            self.auxiliary_file_entry.insert(0, selected_path)

    def refresh_labels(self):
        """Cập nhật label và trạng thái ô nhập theo chế độ/thuật toán."""
        operation_mode = self.operation_mode_var.get()
        algorithm_name = self.algorithm_var.get()

        if operation_mode == "Encode":
            self.primary_input_label.config(text="File văn bản (.txt):")
            self.secondary_input_label.config(text="Bảng mã (.json) – không cần cho Encode")
            self.auxiliary_file_entry.configure(state="normal")
            self.auxiliary_file_entry.delete(0, tk.END)
            self.auxiliary_file_entry.configure(state="disabled")
        else:
            self.primary_input_label.config(text="File nhị phân (.bin):")
            self.secondary_input_label.config(text="Bảng mã (.json) đi kèm:")
            self.auxiliary_file_entry.configure(state="normal")

    def execute_processing(self):
        """Thực thi Encode/Decode dựa trên lựa chọn hiện tại."""
        input_file_path = self.main_file_entry.get()
        if not input_file_path or not os.path.exists(input_file_path):
            messagebox.showerror("Lỗi", "Vui lòng chọn file hợp lệ!")
            return

        try:
            algorithm_name = self.algorithm_var.get()
            operation_mode = self.operation_mode_var.get()
            self.result_text_widget.delete(1.0, tk.END)

            if operation_mode == "Encode":
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
            else:
                base_filename = os.path.splitext(os.path.basename(input_file_path))[0]
                algorithm_slug = self.get_algorithm_slug(algorithm_name)
                output_directory = os.path.join(
                    os.path.dirname(input_file_path),
                    f"{algorithm_slug}_decode_{base_filename}",
                )
                os.makedirs(output_directory, exist_ok=True)
                decoded_output_path = os.path.join(output_directory, "decoded.txt")

                # Thực hiện decode
                code_table_path = self.auxiliary_file_entry.get()
                if not code_table_path or not os.path.exists(code_table_path):
                    messagebox.showerror("Lỗi", "Cần chọn file code_table.json hợp lệ!")
                    return
                loaded_bit_stream = FileFormatLayer.load_bitstream(input_file_path)
                loaded_code_table = FileFormatLayer.load_code_table(code_table_path)
                decoded_text = self.compression_core.decode_text(
                    loaded_bit_stream, loaded_code_table
                )

                with open(decoded_output_path, "w", encoding="utf-8") as output_text_file:
                    output_text_file.write(decoded_text)

                decode_result_text = (
                    f"=== DECODE ({algorithm_name}) ===\n"
                    f"Số ký tự khôi phục: {len(decoded_text)}\n"
                    f"Kết quả lưu tại: {decoded_output_path}"
                )
                self.result_text_widget.insert(tk.END, decode_result_text)

        except Exception as error:
            messagebox.showerror("Lỗi hệ thống", f"Có lỗi xảy ra: {str(error)}")


if __name__ == "__main__":
    root_window = tk.Tk()
    app = CompressionApp(root_window)
    root_window.mainloop()