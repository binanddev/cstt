# import heapq
# import os
# import pickle
# from collections import Counter

# class CompressionCore:
#     @staticmethod
#     def get_frequencies(data):
#         return Counter(data)

#     # --- THUẬT TOÁN SHANNON-FANO ---
#     def shannon_fano_encode(self, data):
#         freqs = sorted(self.get_frequencies(data).items(), key=lambda x: x[1], reverse=True)
#         codes = {symbol: "" for symbol, _ in freqs}
        
#         def recursive_step(items):
#             if len(items) <= 1:
#                 return
            
#             # Tìm điểm chia sao cho tổng tần suất 2 phần gần nhau nhất
#             split_idx = 1
#             total = sum(f for s, f in items)
#             current_sum = 0
#             min_diff = total
            
#             for i in range(len(items)):
#                 current_sum += items[i][1]
#                 diff = abs((total - current_sum) - current_sum)
#                 if diff < min_diff:
#                     min_diff = diff
#                     split_idx = i + 1
#                 else:
#                     break
            
#             for i in range(len(items)):
#                 if i < split_idx:
#                     codes[items[i][0]] += "0"
#                 else:
#                     codes[items[i][0]] += "1"
            
#             recursive_step(items[:split_idx])
#             recursive_step(items[split_idx:])

#         recursive_step(freqs)
#         return codes

#     # --- THUẬT TOÁN HUFFMAN ---
#     def huffman_encode(self, data):
#         freqs = self.get_frequencies(data)
#         heap = [[weight, [symbol, ""]] for symbol, weight in freqs.items()]
#         heapq.heapify(heap)
        
#         while len(heap) > 1:
#             lo = heapq.heappop(heap)
#             hi = heapq.heappop(heap)
#             for pair in lo[1:]:
#                 pair[1] = '0' + pair[1]
#             for pair in hi[1:]:
#                 pair[1] = '1' + pair[1]
#             heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
        
#         return {pair[0]: pair[1] for pair in sorted(heapq.heappop(heap)[1:], key=lambda x: (len(x[-1]), x[0]))}

#     # --- TÍNH TOÁN CHỈ SỐ ---
#     def calculate_theoretical_metrics(self, data, codes):
#         import math
#         freqs = self.get_frequencies(data)
#         total_chars = len(data)
        
#         # 1. Entropy (H) = -sum(p_i * log2(p_i))
#         entropy = 0
#         for char in freqs:
#             p_i = freqs[char] / total_chars
#             entropy -= p_i * math.log2(p_i)
            
#         # 2. Chiều dài trung bình từ mã (L) = sum(p_i * l_i)
#         avg_length = sum((freqs[char] / total_chars) * len(codes[char]) for char in freqs)
        
#         # 3. Hiệu suất nén (Efficiency) η = H / L
#         efficiency = (entropy / avg_length) * 100 if avg_length > 0 else 0
        
#         return entropy, avg_length, efficiency

#     @staticmethod
#     def save_binary(data, codes, output_path):
#         # Chuyển đổi chuỗi text thành chuỗi bit
#         bit_string = "".join(codes[char] for char in data)
        
#         # Thêm padding để đủ byte (8 bit)
#         padding = 8 - (len(bit_string) % 8)
#         bit_string += "0" * padding
        
#         # Chuyển chuỗi bit thành bytes thực sự
#         byte_array = bytearray()
#         for i in range(0, len(bit_string), 8):
#             byte_array.append(int(bit_string[i:i+8], 2))
            
#         with open(output_path, 'wb') as f:
#             # Lưu padding info ở byte đầu tiên để giải mã chính xác
#             f.write(bytes([padding]))
#             f.write(byte_array)


import heapq
import os
import math
from collections import Counter

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

    def save_binary(self, data, codes, output_path):
        """Chuyển đổi văn bản sang file nhị phân thực sự (.bin)"""
        bit_string = "".join(codes[char] for char in data)
        padding = 8 - (len(bit_string) % 8)
        bit_string += "0" * padding
        byte_array = bytearray(int(bit_string[i:i+8], 2) for i in range(0, len(bit_string), 8))
        with open(output_path, 'wb') as f:
            f.write(bytes([padding])) # Lưu byte đầu làm thông tin padding
            f.write(byte_array)

    def save_arithmetic_pseudo_bin(self, data, output_path):
        bits = self.arithmetic_analysis(data)
        bytes_needed = math.ceil(bits / 8)
        with open(output_path, 'wb') as f:
            # Ghi file với kích thước chính xác theo tính toán Arithmetic
            f.write(b'\x00' * bytes_needed)