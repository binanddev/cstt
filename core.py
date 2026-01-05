import heapq
import math
import json
from collections import Counter


class FileFormatLayer:
    """Đảm nhiệm đọc/ghi định dạng file (bin/json) cho các thuật toán."""

    @staticmethod
    def save_bitstream(bit_stream, output_file_path):
        """Ghi chuỗi bit ra file .bin và lưu số bit đệm (padding) ở byte đầu."""
        padding_bits = (8 - (len(bit_stream) % 8)) % 8
        if padding_bits:
            bit_stream += "0" * padding_bits

        byte_array = bytearray(
            int(bit_stream[index : index + 8], 2)
            for index in range(0, len(bit_stream), 8)
        )
        with open(output_file_path, "wb") as binary_file:
            binary_file.write(bytes([padding_bits]))  # byte đầu chứa padding
            binary_file.write(byte_array)

    @staticmethod
    def load_bitstream(binary_file_path):
        """Đọc chuỗi bit từ file .bin, trả về chuỗi bit đã bỏ padding."""
        with open(binary_file_path, "rb") as binary_file:
            padding_raw = binary_file.read(1)
            if not padding_raw:
                return ""
            padding_bits = padding_raw[0]
            binary_data = binary_file.read()

        bit_stream = "".join(f"{byte_value:08b}" for byte_value in binary_data)
        if padding_bits > 0:
            bit_stream = bit_stream[:-padding_bits]
        return bit_stream

    @staticmethod
    def save_code_table(code_table, output_file_path):
        """Lưu bảng mã (mapping ký tự -> chuỗi bit) dạng JSON."""
        with open(output_file_path, "w", encoding="utf-8") as json_file:
            json.dump(code_table, json_file, indent=4, ensure_ascii=False)

    @staticmethod
    def load_code_table(json_file_path):
        """Đọc bảng mã từ file JSON."""
        with open(json_file_path, "r", encoding="utf-8") as json_file:
            return json.load(json_file)

class CompressionCore:
    """Cài đặt các thuật toán nén/giải nén và tính toán lý thuyết."""

    @staticmethod
    def get_frequency_table(input_text):
        """Đếm tần suất xuất hiện của từng ký tự, kể cả ký tự đặc biệt."""
        return Counter(input_text)

    def shannon_fano_encode(self, input_text):
        """Sinh bảng mã Shannon-Fano."""
        if not input_text:
            return {}

        frequency_table = sorted(
            self.get_frequency_table(input_text).items(),
            key=lambda item: item[1],
            reverse=True,
        )
        code_table = {symbol: "" for symbol, _ in frequency_table}

        def recursive_split(items):
            """Chia đôi danh sách theo tổng tần suất gần bằng nhau."""
            if len(items) <= 1:
                return

            total_frequency = sum(frequency for _, frequency in items)
            split_index, current_sum, min_difference = 1, 0, total_frequency

            for index, (_, frequency) in enumerate(items):
                current_sum += frequency
                difference = abs((total_frequency - current_sum) - current_sum)
                if difference < min_difference:
                    min_difference, split_index = difference, index + 1
                else:
                    break

            # Gán bit 0 cho nửa đầu, 1 cho nửa sau
            for index, (symbol, _) in enumerate(items):
                code_table[symbol] += "0" if index < split_index else "1"

            recursive_split(items[:split_index])
            recursive_split(items[split_index:])

        recursive_split(frequency_table)
        return code_table

    def huffman_encode(self, input_text):
        """Sinh bảng mã Huffman chuẩn bằng heap."""
        if not input_text:
            return {}

        frequency_table = self.get_frequency_table(input_text)
        heap = [[weight, [symbol, ""]] for symbol, weight in frequency_table.items()]
        heapq.heapify(heap)

        # Ghép hai node tần suất nhỏ nhất cho tới khi còn một cây
        while len(heap) > 1:
            low_node, high_node = heapq.heappop(heap), heapq.heappop(heap)
            for symbol_pair in low_node[1:]:
                symbol_pair[1] = "0" + symbol_pair[1]
            for symbol_pair in high_node[1:]:
                symbol_pair[1] = "1" + symbol_pair[1]
            heapq.heappush(
                heap,
                [low_node[0] + high_node[0]] + low_node[1:] + high_node[1:],
            )

        # Sắp xếp để kết quả nhất quán
        result_nodes = heapq.heappop(heap)[1:]
        return {
            symbol: code_bits
            for symbol, code_bits in sorted(
                result_nodes, key=lambda pair: (len(pair[1]), pair[0])
            )
        }

    def calculate_theoretical_metrics(self, input_text, codes):
        """Tính entropy, độ dài mã trung bình và hiệu suất."""
        frequency_table = self.get_frequency_table(input_text)
        total_characters = len(input_text)

        # Entropy theo định nghĩa Shannon
        entropy_value = -sum(
            (frequency / total_characters)
            * math.log2(frequency / total_characters)
            for frequency in frequency_table.values()
        )

        if not codes:
            raise ValueError("Cần cung cấp bảng mã để tính toán chỉ số.")

        average_code_length = sum(
            (frequency_table[character] / total_characters) * len(codes[character])
            for character in frequency_table
        )

        compression_efficiency = (
            (entropy_value / average_code_length) * 100
            if average_code_length > 0
            else 0
        )
        return entropy_value, average_code_length, compression_efficiency

    def build_bitstring(self, input_text, code_table):
        """Chuyển văn bản sang chuỗi bit dựa trên bảng mã."""
        return "".join(code_table[character] for character in input_text)

    def encode_text(self, input_text, algorithm_name):
        """Encode văn bản bằng Huffman hoặc Shannon-Fano, trả về chuỗi bit và bảng mã."""
        if algorithm_name == "Huffman":
            code_table = self.huffman_encode(input_text)
        elif algorithm_name == "Shannon-Fano":
            code_table = self.shannon_fano_encode(input_text)
        else:
            raise ValueError("Unsupported algorithm for binary encoding")

        bit_stream = self.build_bitstring(input_text, code_table)
        return bit_stream, code_table

