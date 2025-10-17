#pragma once

#include <cstdint>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

#include <zlib.h>


class ByteArray {
public:
    std::vector<uint8_t> data;

    ByteArray() {}
    ByteArray(const std::vector<uint8_t>& d) : data(d) {}
    ByteArray(std::vector<uint8_t>&& d) : data(std::move(d)) {}

    static ByteArray from_string(const std::string& input) {
        std::vector<uint8_t> bytes(input.begin(), input.end());
        return ByteArray(std::move(bytes));
    }

    auto begin() { return data.begin(); }
    auto end() { return data.end(); }
    auto begin() const { return data.begin(); }
    auto end() const { return data.end(); }

    bool empty() const {  return data.empty(); }
    int64_t size() const { return static_cast<int64_t>(data.size()); }

    uint8_t operator[](int64_t index) const { return data[index]; }
    uint8_t& operator[](int64_t index) { return data[index]; }

    int8_t read_int8(int64_t offset) const {
        return static_cast<int8_t>(data[offset]);
    }

    uint8_t read_uint8(int64_t offset) const {
        return data[offset];
    }

    int16_t read_int16(int64_t offset) const {
        return *reinterpret_cast<const int16_t*>(&data[offset]);
    }

    uint16_t read_uint16(int64_t offset) const {
        return *reinterpret_cast<const uint16_t*>(&data[offset]);
    }

    int32_t read_int32(int64_t offset) const {
        return *reinterpret_cast<const int32_t*>(&data[offset]);
    }

    uint32_t read_uint32(int64_t offset) const {
        return *reinterpret_cast<const uint32_t*>(&data[offset]);
    }

    int64_t read_int64(int64_t offset) const {
        return *reinterpret_cast<const int64_t*>(&data[offset]);
    }

    uint64_t read_uint64(int64_t offset) const {
        return *reinterpret_cast<const uint64_t*>(&data[offset]);
    }

    float read_float(int64_t offset) const {
        return *reinterpret_cast<const float*>(&data[offset]);
    }

    double read_double(int64_t offset) const {
        return *reinterpret_cast<const double*>(&data[offset]);
    }

    std::string read_string(int64_t offset, int64_t length, bool trim_null = true) const {
        if (trim_null) {
            auto null_index = std::find(data.begin() + offset, data.begin() + offset + length, 0);
            return std::string(data.begin() + offset, null_index);
        }
        return std::string(data.begin() + offset, data.begin() + offset + length);
    }

    std::string to_string(bool trim_null = true) const {
        if (trim_null) {
            auto null_index = std::find(data.begin(), data.end(), 0);
            return std::string(data.begin(), null_index);
        }
        return std::string(data.begin(), data.end());
    }

    int64_t find(uint8_t byte, int64_t offset = 0) const {
        for (int64_t i = offset; i < size(); ++i) {
            if (data[i] == byte) return i;
        }
        return -1;
    }

    int64_t find(const ByteArray& bytes, int64_t offset = 0) const {
        if (bytes.empty()) return -1;
        int64_t search_end = size() - bytes.size() + 1;
        for (int64_t i = offset; i < search_end; ++i) {
            bool match = true;
            for (int64_t j = 0; j < bytes.size(); ++j) {
                if (data[i + j] != bytes[j]) {
                    match = false;
                    break;
                }
            }
            if (match) return i;
        }
        return -1;
    }

    void slice(int64_t offset, int64_t length, bool check_bounds = false) {
        if (check_bounds && (offset < 0 || length < 0 || offset + length > size())) {
            throw std::out_of_range("slice offset or length out of range");
        }
        if (offset > size()) offset = size();
        if (offset + length > size()) length = size() - offset;
        data = std::vector<uint8_t>(data.begin() + offset, data.begin() + offset + length);
    }

    ByteArray sliced(int64_t offset, int64_t length, bool check_bounds = false) const {
        if (check_bounds && (offset < 0 || length < 0 || offset + length > size())) {
            throw std::out_of_range("slice offset or length out of range");
        }
        if (offset > size()) offset = size();
        if (offset + length > size()) length = size() - offset;
        std::vector<uint8_t> slice_data(data.begin() + offset, data.begin() + offset + length);
        return ByteArray(std::move(slice_data));
    }
    
    template<typename T>
    void slice_at(const T& delimiter, int64_t offset = 0, bool include = false, bool partial = false) {
        auto index = find(delimiter, offset);
        if (index == -1) {
            if (partial) {
                slice(offset, size() - offset);
            } else {
                throw std::runtime_error("delimiter not found");
            }
        } else if (include) {
            int64_t delimiter_length;
            if constexpr (std::is_same_v<T, uint8_t>) {
                delimiter_length = 1;
            } else {
                delimiter_length = delimiter.size();
            }
            slice(offset, index - offset + delimiter_length);
        } else {
            slice(offset, index - offset);
        }
    }

    template<typename T>
    ByteArray sliced_at(const T& delimiter, int64_t offset = 0, bool include = false, bool partial = false) const {
        auto index = find(delimiter, offset);
        if (index == -1) {
            if (partial) return sliced(offset, size() - offset);
            throw std::runtime_error("delimiter not found");
        } else if (include) {
            int64_t delimiter_length;
            if constexpr (std::is_same_v<T, uint8_t>) {
                delimiter_length = 1;
            } else {
                delimiter_length = delimiter.size();
            }
            return sliced(offset, index - offset + delimiter_length);
        } else {
            return sliced(offset, index - offset);
        }
    }

    void extend(const ByteArray& other) {
        data.insert(data.end(), other.begin(), other.end());
    }

    ByteArray extended(const ByteArray& other) const {
        std::vector<uint8_t> combined_data = data;
        combined_data.insert(combined_data.end(), other.begin(), other.end());
        return ByteArray(std::move(combined_data));
    }

    std::vector<std::string> read_lines() const {
        std::vector<std::string> lines;
        int64_t line_start = 0;
        for (int64_t i = 0; i < size(); ++i) {
            if (data[i] == '\n') {
                int64_t line_end = i;
                if (line_end > line_start && data[line_end - 1] == '\r') line_end -= 1;
                lines.emplace_back(data.begin() + line_start, data.begin() + line_end);
                line_start = i + 1;
            }
        }
        if (line_start < size()) {
            int64_t line_end = size();
            if (line_end > line_start && data[line_end - 1] == '\r') line_end -= 1;
            lines.emplace_back(data.begin() + line_start, data.begin() + line_end);
        }
        return lines;
    }

    ByteArray decompressed(int64_t buffer_size = 32768, int64_t max_size = 1073741824) const {
        if (buffer_size < 1 || buffer_size > max_size) {
            throw std::runtime_error("buffer size " + std::to_string(buffer_size) + " invalid");
        }
        std::vector<uint8_t> decompressed_data;
        std::vector<uint8_t> buffer(buffer_size);
        z_stream stream{};
        stream.avail_in = static_cast<uInt>(data.size());
        stream.next_in = const_cast<Bytef*>(data.data());
        int init_result = inflateInit2(&stream, 15 + 32);
        if (init_result != Z_OK) {
            throw std::runtime_error("failed to initialize zlib for decompression: " + 
                std::string(stream.msg ? stream.msg : "unknown error"));
        }
        while (true) {
            stream.avail_out = static_cast<uInt>(buffer_size);
            stream.next_out = buffer.data();
            int ret = inflate(&stream, Z_NO_FLUSH);
            if (ret != Z_OK && ret != Z_STREAM_END) {
                std::string error_msg = "zlib decompression failed: ";
                switch (ret) {
                    case Z_STREAM_ERROR: error_msg += "invalid compression level"; break;
                    case Z_DATA_ERROR: error_msg += "invalid or incomplete deflate data"; break;
                    case Z_MEM_ERROR: error_msg += "out of memory"; break;
                    case Z_BUF_ERROR: error_msg += "no progress possible or output buffer too small"; break;
                    default: error_msg += "error code " + std::to_string(ret); break;
                }
                if (stream.msg) error_msg += " (" + std::string(stream.msg) + ")";
                inflateEnd(&stream);
                throw std::runtime_error(error_msg);
            }
            int64_t decompressed = buffer_size - stream.avail_out;
            if (decompressed_data.size() + decompressed > static_cast<uint64_t>(max_size)) {
                inflateEnd(&stream);
                throw std::runtime_error("decompressed data exceeds limit (" + std::to_string(max_size) + ")");
            }
            if (ret == Z_STREAM_END && decompressed_data.size() == 0 && decompressed == buffer_size) {
                decompressed_data = std::move(buffer);
                break;
            }
            decompressed_data.insert(decompressed_data.end(), buffer.begin(), buffer.begin() + decompressed);
            if (ret == Z_STREAM_END) break;
        }
        inflateEnd(&stream);
        return ByteArray(std::move(decompressed_data));
    }

    ByteArray compressed(std::string format = "gzip", int8_t compression_level = Z_DEFAULT_COMPRESSION) const {
        uLong compressed_size = compressBound(static_cast<uLong>(data.size()));
        std::vector<uint8_t> compressed_data(compressed_size);
        z_stream stream{};
        stream.avail_in = static_cast<uInt>(data.size());
        stream.next_in = const_cast<Bytef*>(data.data());
        stream.avail_out = static_cast<uInt>(compressed_size);
        stream.next_out = compressed_data.data();
        int window_bits = format == "gzip" ? (15 + 16) : (format == "zlib" ? 15 : -15); // -15 = raw deflate
        int init_result = deflateInit2(&stream, compression_level, Z_DEFLATED, window_bits, 8, Z_DEFAULT_STRATEGY);
        if (init_result != Z_OK) {
            throw std::runtime_error("failed to initialize zlib for compression: " + 
                std::string(stream.msg ? stream.msg : "unknown error"));
        }
        int ret = deflate(&stream, Z_FINISH);
        if (ret != Z_STREAM_END) {
            std::string error_msg = "zlib compression failed: ";
            switch (ret) {
                case Z_OK: error_msg += "incomplete compression"; break;
                case Z_STREAM_ERROR: error_msg += "invalid compression level or parameters"; break;
                case Z_BUF_ERROR: error_msg += "no progress possible or output buffer too small"; break;
                default: error_msg += "error code " + std::to_string(ret); break;
            }
            if (stream.msg) error_msg += " (" + std::string(stream.msg) + ")";
            deflateEnd(&stream);
            throw std::runtime_error(error_msg);
        }
        compressed_data.resize(stream.total_out);
        deflateEnd(&stream);
        return ByteArray(std::move(compressed_data));
    }

};
