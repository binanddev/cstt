
import heapq
import math
import json
from collections import Counter


class FileFormatLayer:
    """Đảm nhiệm đọc/ghi định dạng file (bin/json) cho các thuật toán."""

    @staticmethod
    def save_bitstream(bit_string, output_path):
        padding = (8 - (len(bit_string) % 8)) % 8
        if padding:
            bit_string += "0" * padding
        byte_array = bytearray(int(bit_string[i:i+8], 2) for i in range(0, len(bit_string), 8))
        with open(output_path, 'wb') as f:
            f.write(bytes([padding]))  # byte đầu lưu padding
            f.write(byte_array)

    @staticmethod
    def load_bitstream(bin_path):
        with open(bin_path, 'rb') as f:
            padding_raw = f.read(1)
            if not padding_raw:
                return ""
            padding = padding_raw[0]
            byte_data = f.read()

        bit_string = "".join(f"{b:08b}" for b in byte_data)
        if padding > 0:
            bit_string = bit_string[:-padding]
        return bit_string

    @staticmethod
    def save_code_table(code_table, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(code_table, f, indent=4, ensure_ascii=False)

    @staticmethod
    def load_code_table(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def save_arithmetic_payload(payload, output_path):
        # Lưu payload range coder 32-bit: freqs, cum, total, bitstring và padding
        serializable = {
            "algorithm": "ArithmeticRange32",
            "length": payload["length"],
            "freqs": payload["freqs"],
            "cum": payload["cum"],
            "total": payload["total"],
            "bits": payload["bits"],
            "padding": payload["padding"],
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable, f, indent=4, ensure_ascii=False)

    @staticmethod
    def load_arithmetic_payload(path):
        with open(path, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        return payload

class CompressionCore:
    @staticmethod
    def get_frequencies(data):
        # Đếm chính xác mọi ký tự ASCII bao gồm dấu cách, xuống dòng, ký tự đặc biệt
        return Counter(data)

    def shannon_fano_encode(self, data):
        if not data: return {}
        freqs = sorted(self.get_frequencies(data).items(), key=lambda x: x[1], reverse=True)
        codes = {symbol: "" for symbol, _ in freqs}
        
        def recursive_step(items):
            if len(items) <= 1: return
            total = sum(f for s, f in items)
            split_idx, current_sum, min_diff = 1, 0, total
            for i in range(len(items)):
                current_sum += items[i][1]
                diff = abs((total - current_sum) - current_sum)
                if diff < min_diff:
                    min_diff, split_idx = diff, i + 1
                else: break
            for i in range(len(items)):
                codes[items[i][0]] += "0" if i < split_idx else "1"
            recursive_step(items[:split_idx])
            recursive_step(items[split_idx:])

        recursive_step(freqs)
        return codes

    def huffman_encode(self, data):
        if not data: return {}
        freqs = self.get_frequencies(data)
        # Sử dụng heap để xây dựng cây Huffman chuẩn
        heap = [[weight, [symbol, ""]] for symbol, weight in freqs.items()]
        heapq.heapify(heap)
        while len(heap) > 1:
            lo, hi = heapq.heappop(heap), heapq.heappop(heap)
            for pair in lo[1:]: pair[1] = '0' + pair[1]
            for pair in hi[1:]: pair[1] = '1' + pair[1]
            heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
        
        # Sắp xếp kết quả để đảm bảo tính nhất quán
        res = heapq.heappop(heap)[1:]
        return {pair[0]: pair[1] for pair in sorted(res, key=lambda x: (len(x[1]), x[0]))}

    # def arithmetic_analysis(self, data):
    #     """Tính toán dựa trên lý thuyết thông tin: -log2(P) cho từng ký tự"""
    #     freqs = self.get_frequencies(data)
    #     total = len(data)
    #     theoretical_bits = 0
    #     for char in data:
    #         prob = freqs[char] / total
    #         # Số bit cần thiết cho mỗi ký tự đặc biệt dựa trên xác suất của nó
    #         theoretical_bits -= math.log2(prob)
    #     return math.ceil(theoretical_bits)
    def arithmetic_analysis(self, data):
        freqs = self.get_frequencies(data)
        total = len(data)
        theoretical_bits = 0
        for char in data:
            prob = freqs[char] / total
            theoretical_bits -= math.log2(prob)
        
        # Cộng thêm sai số thực tế (Precision/Terminator overhead)
        # Thông thường Arithmetic thực tế tốn thêm khoảng 2-4 bit cho toàn bộ file
        actual_bits = theoretical_bits + 2 
        return math.ceil(actual_bits)

    def calculate_theoretical_metrics(self, data, codes=None, is_arithmetic=False):
        freqs = self.get_frequencies(data)
        total_chars = len(data)
        # 1. Entropy (Giới hạn Shannon)
        entropy = -sum((f/total_chars) * math.log2(f/total_chars) for f in freqs.values())
        
        if is_arithmetic:
            bits = self.arithmetic_analysis(data)
            avg_length = bits / total_chars
        else:
            avg_length = sum((freqs[char] / total_chars) * len(codes[char]) for char in freqs)
        
        efficiency = (entropy / avg_length) * 100 if avg_length > 0 else 0
        return entropy, avg_length, efficiency

    def build_bitstring(self, data, codes):
        return "".join(codes[char] for char in data)

    def decode_bitstring(self, bit_string, code_table):
        reverse = {v: k for k, v in code_table.items()}
        buffer = ""
        decoded = []
        for bit in bit_string:
            buffer += bit
            if buffer in reverse:
                decoded.append(reverse[buffer])
                buffer = ""
        return "".join(decoded)

    def encode_text(self, data, algo):
        if algo == "Huffman":
            codes = self.huffman_encode(data)
        elif algo == "Shannon-Fano":
            codes = self.shannon_fano_encode(data)
        else:
            raise ValueError("Unsupported algorithm for binary encoding")
        bit_string = self.build_bitstring(data, codes)
        return bit_string, codes

    def decode_text(self, bit_string, code_table):
        return self.decode_bitstring(bit_string, code_table)

    def arithmetic_encode(self, data):
        """Range coder 32-bit tối giản (không Decimal)."""
        freqs = Counter(data)
        symbols = sorted(freqs)
        cum = {}
        total = 0
        for s in symbols:
            cum[s] = total
            total += freqs[s]

        LOW, HIGH = 0, (1 << 32) - 1
        MSB = 1 << 31
        low, high = LOW, HIGH
        bits = []

        for ch in data:
            r = high - low + 1
            high = low + (r * (cum[ch] + freqs[ch]) // total) - 1
            low = low + (r * cum[ch] // total)

            while True:
                if high < MSB:
                    bits.append('0')
                    low = (low << 1) & HIGH
                    high = ((high << 1) | 1) & HIGH
                elif low >= MSB:
                    bits.append('1')
                    low = ((low - MSB) << 1) & HIGH
                    high = (((high - MSB) << 1) | 1) & HIGH
                else:
                    break

        # Flush 32 bit để hoàn tất
        for _ in range(32):
            bits.append('1' if (low & MSB) else '0')
            low = (low << 1) & HIGH

        bit_string = "".join(bits)
        padding = (8 - (len(bit_string) % 8)) % 8
        if padding:
            bit_string += "0" * padding

        return {
            "algorithm": "ArithmeticRange32",
            "length": len(data),
            "freqs": {k: int(v) for k, v in freqs.items()},
            "cum": {k: int(v) for k, v in cum.items()},
            "total": int(total),
            "bits": bit_string,
            "padding": padding,
        }

    def arithmetic_decode(self, payload):
        """Giải mã range coder 32-bit tối giản (không Decimal)."""
        length = payload["length"]
        freqs = payload["freqs"]
        cum = payload["cum"]
        total = payload["total"]
        bit_string = payload["bits"]
        padding = payload.get("padding", 0)

        if padding:
            bit_string = bit_string[:-padding]

        LOW, HIGH = 0, (1 << 32) - 1
        MSB = 1 << 31

        symbols = sorted(freqs)

        # Lấy 32 bit đầu tiên để khởi tạo value
        value_bits = bit_string[:32].ljust(32, '0')
        idx = 32
        value = int(value_bits, 2)

        low, high = LOW, HIGH
        result = []

        for _ in range(length):
            r = high - low + 1
            scaled = ((value - low + 1) * total - 1) // r

            for s in symbols:
                if cum[s] <= scaled < cum[s] + freqs[s]:
                    result.append(s)
                    high = low + (r * (cum[s] + freqs[s]) // total) - 1
                    low = low + (r * cum[s] // total)
                    break

            while True:
                if high < MSB:
                    pass
                elif low >= MSB:
                    low -= MSB
                    high -= MSB
                    value -= MSB
                else:
                    break
                low = (low << 1) & HIGH
                high = ((high << 1) | 1) & HIGH
                next_bit = int(bit_string[idx]) if idx < len(bit_string) else 0
                idx += 1
                value = ((value << 1) & HIGH) | next_bit

        return "".join(result)
