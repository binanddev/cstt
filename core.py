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

    @staticmethod
    def save_arithmetic_payload(payload, output_file_path):
        """Lưu dữ liệu nén Arithmetic (range coder 32-bit) ra JSON."""
        serializable_payload = {
            "algorithm": "ArithmeticRange32",
            "length": payload["length"],
            "freqs": payload["freqs"],
            "cum": payload["cum"],
            "total": payload["total"],
            "bits": payload["bits"],
            "padding": payload["padding"],
        }
        with open(output_file_path, "w", encoding="utf-8") as json_file:
            json.dump(serializable_payload, json_file, indent=4, ensure_ascii=False)

    @staticmethod
    def load_arithmetic_payload(json_file_path):
        """Đọc dữ liệu nén Arithmetic từ JSON."""
        with open(json_file_path, "r", encoding="utf-8") as json_file:
            arithmetic_payload = json.load(json_file)
        return arithmetic_payload


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

    def arithmetic_analysis(self, input_text):
        """Tính số bit lý thuyết cho Arithmetic Coding (cộng thêm overhead)."""
        frequency_table = self.get_frequency_table(input_text)
        total_characters = len(input_text)
        theoretical_bits = 0

        for character in input_text:
            probability = frequency_table[character] / total_characters
            theoretical_bits -= math.log2(probability)

        # Thêm phần overhead thực tế (2–4 bit cho toàn bộ file, lấy 2 cho đơn giản)
        actual_bits = theoretical_bits + 2
        return math.ceil(actual_bits)

    def calculate_theoretical_metrics(
        self, input_text, codes=None, is_arithmetic=False
    ):
        """Tính entropy, độ dài mã trung bình và hiệu suất."""
        frequency_table = self.get_frequency_table(input_text)
        total_characters = len(input_text)

        # Entropy theo định nghĩa Shannon
        entropy_value = -sum(
            (frequency / total_characters)
            * math.log2(frequency / total_characters)
            for frequency in frequency_table.values()
        )

        if is_arithmetic:
            total_bits = self.arithmetic_analysis(input_text)
            average_code_length = total_bits / total_characters
        else:
            average_code_length = sum(
                (frequency_table[character] / total_characters)
                * len(codes[character])
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

    def decode_bitstring(self, bit_stream, code_table):
        """Chuyển chuỗi bit về văn bản dựa trên bảng mã."""
        reversed_code_table = {
            code_bits: character for character, code_bits in code_table.items()
        }
        decoding_buffer = ""
        decoded_characters = []

        for bit in bit_stream:
            decoding_buffer += bit
            if decoding_buffer in reversed_code_table:
                decoded_characters.append(reversed_code_table[decoding_buffer])
                decoding_buffer = ""

        return "".join(decoded_characters)

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

    def decode_text(self, bit_stream, code_table):
        """Giải mã chuỗi bit về văn bản gốc."""
        return self.decode_bitstring(bit_stream, code_table)

    def arithmetic_encode(self, input_text):
        """Nén bằng range coder 32-bit đơn giản (không dùng Decimal)."""
        frequency_table = Counter(input_text)
        sorted_symbols = sorted(frequency_table)

        cumulative_frequency_table = {}
        total_frequency = 0
        for symbol in sorted_symbols:
            cumulative_frequency_table[symbol] = total_frequency
            total_frequency += frequency_table[symbol]

        low_bound, high_bound = 0, (1 << 32) - 1
        most_significant_bit = 1 << 31
        current_low, current_high = low_bound, high_bound
        encoded_bits = []

        for character in input_text:
            range_width = current_high - current_low + 1
            current_high = (
                current_low
                + (
                    range_width
                    * (
                        cumulative_frequency_table[character]
                        + frequency_table[character]
                    )
                    // total_frequency
                )
                - 1
            )
            current_low = (
                current_low
                + (
                    range_width
                    * cumulative_frequency_table[character]
                    // total_frequency
                )
            )

            # Chuẩn hóa khi interval nằm cùng phía MSB
            while True:
                if current_high < most_significant_bit:
                    encoded_bits.append("0")
                    current_low = (current_low << 1) & high_bound
                    current_high = ((current_high << 1) | 1) & high_bound
                elif current_low >= most_significant_bit:
                    encoded_bits.append("1")
                    current_low = (
                        (current_low - most_significant_bit) << 1
                    ) & high_bound
                    current_high = (
                        ((current_high - most_significant_bit) << 1) | 1
                    ) & high_bound
                else:
                    break

        # Đẩy thêm 32 bit để chốt khoảng
        for _ in range(32):
            encoded_bits.append("1" if (current_low & most_significant_bit) else "0")
            current_low = (current_low << 1) & high_bound

        bit_stream = "".join(encoded_bits)
        padding_bits = (8 - (len(bit_stream) % 8)) % 8
        if padding_bits:
            bit_stream += "0" * padding_bits

        return {
            "algorithm": "ArithmeticRange32",
            "length": len(input_text),
            "freqs": {
                symbol: int(frequency) for symbol, frequency in frequency_table.items()
            },
            "cum": {
                symbol: int(frequency)
                for symbol, frequency in cumulative_frequency_table.items()
            },
            "total": int(total_frequency),
            "bits": bit_stream,
            "padding": padding_bits,
        }

    def arithmetic_decode(self, payload):
        """Giải nén dữ liệu range coder 32-bit đơn giản."""
        expected_length = payload["length"]
        frequency_table = payload["freqs"]
        cumulative_frequency_table = payload["cum"]
        total_frequency = payload["total"]
        bit_stream = payload["bits"]
        padding_bits = payload.get("padding", 0)

        if padding_bits:
            bit_stream = bit_stream[:-padding_bits]

        low_bound, high_bound = 0, (1 << 32) - 1
        most_significant_bit = 1 << 31
        sorted_symbols = sorted(frequency_table)

        # Lấy 32 bit đầu tiên để khởi tạo giá trị giải mã
        initial_value_bits = bit_stream[:32].ljust(32, "0")
        bit_index = 32
        current_value = int(initial_value_bits, 2)

        current_low, current_high = low_bound, high_bound
        decoded_symbols = []

        for _ in range(expected_length):
            range_width = current_high - current_low + 1
            scaled_value = (
                ((current_value - current_low + 1) * total_frequency - 1)
                // range_width
            )

            # Tìm ký tự phù hợp với scaled_value trong bảng tích lũy
            for symbol in sorted_symbols:
                if (
                    cumulative_frequency_table[symbol]
                    <= scaled_value
                    < cumulative_frequency_table[symbol] + frequency_table[symbol]
                ):
                    decoded_symbols.append(symbol)
                    current_high = (
                        current_low
                        + (
                            range_width
                            * (
                                cumulative_frequency_table[symbol]
                                + frequency_table[symbol]
                            )
                            // total_frequency
                        )
                        - 1
                    )
                    current_low = (
                        current_low
                        + (
                            range_width
                            * cumulative_frequency_table[symbol]
                            // total_frequency
                        )
                    )
                    break

            # Chuẩn hóa giống bước encode
            while True:
                if current_high < most_significant_bit:
                    pass
                elif current_low >= most_significant_bit:
                    current_low -= most_significant_bit
                    current_high -= most_significant_bit
                    current_value -= most_significant_bit
                else:
                    break

                current_low = (current_low << 1) & high_bound
                current_high = ((current_high << 1) | 1) & high_bound
                next_bit = int(bit_stream[bit_index]) if bit_index < len(bit_stream) else 0
                bit_index += 1
                current_value = ((current_value << 1) & high_bound) | next_bit

        return "".join(decoded_symbols)

