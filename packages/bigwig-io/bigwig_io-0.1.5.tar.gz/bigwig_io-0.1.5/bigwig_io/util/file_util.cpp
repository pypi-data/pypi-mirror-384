#pragma once

#include <cstdint>
#include <filesystem>
#include <fstream>
#include <future>
#include <iostream>
#include <memory>
#include <mutex>
#include <queue>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>
#include <tuple>

#include <curl/curl.h>
#include <zlib.h>

#include "byte_util.cpp"
#include "parallel_util.cpp"
#include "map_util.cpp"


class File {
public:

    virtual ~File() = default;

    virtual int64_t get_file_size(bool acquire_lock = true) = 0;
    virtual ByteArray read(int64_t size, int64_t offset) = 0;
    virtual void write(const ByteArray& data, int64_t offset) = 0;

    virtual void write_string(const std::string& input, int64_t offset = -1) {
        write(ByteArray::from_string(input), offset);
    }

};


class LocalFile : public File {
    std::string path;
    std::string mode;
    std::unique_ptr<std::fstream> file_handle;
    mutable std::mutex file_lock;

    void seek(int64_t offset, std::ios::seekdir dir = std::ios::beg) {
        file_handle->seekg(offset, dir);
        if (file_handle->fail()) {
            throw std::runtime_error("failed to seek to " + std::to_string(offset) + " in file " + path);
        }
    }

    int64_t tell() {
        int64_t offset = file_handle->tellg();
        if (offset < 0) throw std::runtime_error("error determining cursor position in file " + path);
        return offset;
    }

public:
    LocalFile(const std::string& path, const std::string& mode = "r") : path(path), mode(mode) {
        std::ios::openmode flag = std::ios::binary;
        if (mode == "r") {
            flag |= std::ios::in;
        } else if (mode == "w") {
            flag |= std::ios::out;
        } else {
            throw std::runtime_error("file open mode " + mode + " not supported");
        }
        file_handle = std::make_unique<std::fstream>(path, flag);
        if (!file_handle->is_open()) {
            throw std::runtime_error("failed to open file " + path);
        }
    }

    ~LocalFile() {
        if (file_handle && file_handle->is_open()) {
            file_handle->close();
        }
    }

    int64_t get_file_size(bool acquire_lock = true) override {
        std::unique_lock<std::mutex> lock(file_lock, std::defer_lock);
        if (acquire_lock) lock.lock();
        auto current_pos = tell();
        seek(0, std::ios::end);
        auto size = tell();
        seek(current_pos);
        return size;
    }

    ByteArray read(int64_t size = -1, int64_t offset = -1) override {
        if (mode != "r") throw std::runtime_error("error reading file " + path + " (not in read mode)");
        std::lock_guard<std::mutex> lock(file_lock);
        if (size < 0) size = get_file_size(false);
        if (offset >= 0) seek(offset);
        std::vector<uint8_t> buffer(size);
        if (size == 0) return buffer;
        file_handle->read(reinterpret_cast<char*>(buffer.data()), size);
        std::streamsize bytes_read = file_handle->gcount();
        if (file_handle->bad() || file_handle->fail()) {
            if (file_handle->eof()) {
                buffer.resize(bytes_read);
            } else {
                std::string reason = " (" + std::string(strerror(errno)) + ")";
                throw std::runtime_error("error reading file " + path + reason);
            }
        }
        return ByteArray(std::move(buffer));
    }

    void write(const ByteArray& data, int64_t offset = -1) override {
        if (mode != "w") throw std::runtime_error("error writing to file " + path + " (not in write mode)");
        std::lock_guard<std::mutex> lock(file_lock);
        if (offset >= 0) seek(offset);
        file_handle->write(reinterpret_cast<const char*>(data.data.data()), data.size());
        if (file_handle->bad() || file_handle->fail()) {
            std::string size = std::to_string(data.size());
            std::string reason = " (" + std::string(strerror(errno)) + ")";
            throw std::runtime_error("failed to write " + size + " bytes to file " + path + reason);
        }
    }

};


struct CurlWriteData {
    std::vector<uint8_t>* buffer;
    size_t expected_size;
};

static size_t custom_curl_write_callback(void* contents, size_t size, size_t nmemb, CurlWriteData* write_data) {
    size_t total_size = size * nmemb;
    uint8_t* data = static_cast<uint8_t*>(contents);
    
    write_data->buffer->insert(write_data->buffer->end(), data, data + total_size);
    return total_size;
}

class CurlGlobalManager {
private:
    std::mutex manager_lock;
    uint64_t ref_count;
    
    CurlGlobalManager() : ref_count(0) {}
    
public:
    CurlGlobalManager(const CurlGlobalManager&) = delete;
    CurlGlobalManager& operator=(const CurlGlobalManager&) = delete;
    
    static CurlGlobalManager& getInstance() {
        static CurlGlobalManager instance;
        return instance;
    }
    
    void initialize() {
        std::lock_guard<std::mutex> lock(manager_lock);
        if (ref_count == 0) curl_global_init(CURL_GLOBAL_DEFAULT);
        ref_count++;
    }
    
    void cleanup() {
        std::lock_guard<std::mutex> lock(manager_lock);
        ref_count--;
        if (ref_count == 0) curl_global_cleanup();
    }
    
    ~CurlGlobalManager() {
        if (ref_count > 0) curl_global_cleanup();
    }
};

class UrlFile : public File {
    std::string path;
    std::string mode;
    mutable std::mutex curl_lock;
    CURL* curl_handle;
    int64_t current_file_size = -1;
    int64_t current_offset = 0;

    std::vector<uint8_t> read_all() {
        if (!curl_handle) throw std::runtime_error("curl_handle is not initialized");
        std::vector<uint8_t> buffer;
        CurlWriteData write_data;
        write_data.buffer = &buffer;
        write_data.expected_size = 0; // Not used for full read
        
        // Configure curl for this request
        curl_easy_setopt(curl_handle, CURLOPT_HTTPHEADER, nullptr); // No range header
        curl_easy_setopt(curl_handle, CURLOPT_WRITEFUNCTION, custom_curl_write_callback);
        curl_easy_setopt(curl_handle, CURLOPT_WRITEDATA, &write_data);
        curl_easy_setopt(curl_handle, CURLOPT_ACCEPT_ENCODING, ""); // All supported
        
        // Perform the request
        CURLcode res = curl_easy_perform(curl_handle);
        if (res != CURLE_OK) {
            std::string reason = " (curl request failed: " + std::string(curl_easy_strerror(res)) + ")";
            throw std::runtime_error("error reading " + path + reason);
        }
        
        // Check response code
        long response_code;
        curl_easy_getinfo(curl_handle, CURLINFO_RESPONSE_CODE, &response_code);
        if (response_code != 200) { // 200 = OK
            std::string reason = " (http request failed with code " + std::to_string(response_code) + ")";
            throw std::runtime_error("error reading " + path + reason);
        }
        return buffer;
    }

public:
    UrlFile(const std::string& path, const std::string& mode = "r") : path(path), mode(mode), curl_handle(nullptr) {
        CurlGlobalManager::getInstance().initialize();
        curl_handle = curl_easy_init();
        if (!curl_handle) {
            CurlGlobalManager::getInstance().cleanup(); // Clean up on failure
            throw std::runtime_error("failed to initialize curl");
        }
        
        curl_easy_setopt(curl_handle, CURLOPT_URL, path.c_str());
        curl_easy_setopt(curl_handle, CURLOPT_FOLLOWLOCATION, 1L);
        curl_easy_setopt(curl_handle, CURLOPT_TIMEOUT, 30L);
        curl_easy_setopt(curl_handle, CURLOPT_CONNECTTIMEOUT, 10L);
        curl_easy_setopt(curl_handle, CURLOPT_USERAGENT, "UrlFile/1.0");
        curl_easy_setopt(curl_handle, CURLOPT_FAILONERROR, 1L);
        curl_easy_setopt(curl_handle, CURLOPT_ACCEPT_ENCODING, ""); // All supported
        curl_easy_setopt(curl_handle, CURLOPT_HTTP_VERSION, CURL_HTTP_VERSION_2TLS);
    }
    
    ~UrlFile() {
        if (curl_handle) curl_easy_cleanup(curl_handle);
        CurlGlobalManager::getInstance().cleanup();
    }
    
    int64_t get_file_size(bool acquire_lock = true) override {
        if (current_file_size >= 0) return current_file_size;
        std::unique_lock<std::mutex> lock(curl_lock, std::defer_lock);
        if (acquire_lock) lock.lock();
        if (!curl_handle) throw std::runtime_error("curl_handle is not initialized");
        double file_size = 0.0;
        curl_easy_setopt(curl_handle, CURLOPT_NOBODY, 1L);
        curl_easy_setopt(curl_handle, CURLOPT_HEADER, 0L);
        curl_easy_setopt(curl_handle, CURLOPT_FILETIME, 1L);
        CURLcode res = curl_easy_perform(curl_handle);
        if (res != CURLE_OK) {
            std::string reason = " (curl request failed: " + std::string(curl_easy_strerror(res)) + ")";
            throw std::runtime_error("error determining size of " + path + reason);
        }
        res = curl_easy_getinfo(curl_handle, CURLINFO_CONTENT_LENGTH_DOWNLOAD_T, &file_size);
        if (res != CURLE_OK || file_size < 0) {
            std::string reason = " (could not get content length)";
            throw std::runtime_error("error determining size of " + path + reason);
        }
        curl_easy_setopt(curl_handle, CURLOPT_NOBODY, 0L);
        curl_easy_setopt(curl_handle, CURLOPT_FILETIME, 0L);
        current_file_size = static_cast<int64_t>(file_size);
        return current_file_size;
    }

    ByteArray read(int64_t size = -1, int64_t offset = -1) override {
        if (mode != "r") throw std::runtime_error("error reading file " + path + " (not in read mode)");
        std::lock_guard<std::mutex> lock(curl_lock);
        if (offset < 0) offset = current_offset;
        if (size < 0) {
            if (offset == 0) return read_all();
            size = get_file_size(false) - offset;
        }
        if (!curl_handle) throw std::runtime_error("curl_handle is not initialized");
        
        // Initialize buffer as empty, let curl callback fill it
        std::vector<uint8_t> buffer;
        buffer.reserve(size);
        CurlWriteData write_data;
        write_data.buffer = &buffer;
        write_data.expected_size = size;
        
        // Set up range request
        std::string range_header = "Range: bytes=" + std::to_string(offset) + "-" + std::to_string(offset + size - 1);
        struct curl_slist* headers = nullptr;
        headers = curl_slist_append(headers, range_header.c_str());
        
        // Configure curl for this request
        curl_easy_setopt(curl_handle, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl_handle, CURLOPT_WRITEFUNCTION, custom_curl_write_callback);
        curl_easy_setopt(curl_handle, CURLOPT_WRITEDATA, &write_data);
        curl_easy_setopt(curl_handle, CURLOPT_ACCEPT_ENCODING, "");  // All supported
        
        // DEBUG: Enable verbose output to see all headers
        //curl_easy_setopt(curl_handle, CURLOPT_VERBOSE, 1L);
        // Perform the request
        CURLcode res = curl_easy_perform(curl_handle);
        // DEBUG: Disable verbose output after request
        //curl_easy_setopt(curl_handle, CURLOPT_VERBOSE, 0L);
        //throw std::runtime_error("debug");
        
        // Clean up headers
        curl_slist_free_all(headers);
        
        if (res != CURLE_OK) {
            std::string reason = " (curl request failed: " + std::string(curl_easy_strerror(res)) + ")";
            throw std::runtime_error("error reading " + path + reason);
        }
        
        // Check response code
        long response_code;
        curl_easy_getinfo(curl_handle, CURLINFO_RESPONSE_CODE, &response_code);
        if (response_code != 206 && response_code != 200) { // 206 = Partial Content, 200 = OK
            std::string reason = " (http request failed with code " + std::to_string(response_code) + ")";
            throw std::runtime_error("error reading " + path + reason);
        }

        current_offset = offset + buffer.size();
        return ByteArray(std::move(buffer));
    }

    void write(const ByteArray& /* data */, int64_t /* offset */) override {
        if (mode != "w") throw std::runtime_error("error writing to file " + path + " (not in write mode)");
        throw std::runtime_error("writing to url not supported");
    }

};


std::shared_ptr<File> open_file(const std::string& path, const std::string& mode) {
    if (path.substr(0, 6) == "ftp://" || path.substr(0, 7) == "http://" || path.substr(0, 8) == "https://") {
        return std::make_shared<UrlFile>(path, mode);
    } else {
        return std::make_shared<LocalFile>(path, mode);
    }
}


class FilePoolBuffer {
public:
    int64_t offset;
    int64_t length;
    std::promise<ByteArray> data_promise;
    std::shared_future<ByteArray> data_future;

    FilePoolBuffer(int64_t offset, int64_t length) : offset(offset), length(length) {
        data_promise = std::promise<ByteArray>();
        data_future = data_promise.get_future().share();
    }

    ByteArray extract(int64_t req_offset, int64_t req_length) const {
        int64_t buffer_req_offset = req_offset - offset;
        const auto& data = data_future.get();
        return data.sliced(buffer_req_offset, req_length, true);
    }

};


class FilePool {
    std::mutex pool_lock;
    Semaphore read_lock;
    std::mutex write_lock;
    std::queue<std::shared_ptr<File>> file_pool;
    ThreadPool thread_pool;
    ThreadPool buffer_thread_pool;
    OrderedMap<int64_t, std::shared_ptr<FilePoolBuffer>> buffer_pool;
    std::mutex buffer_pool_lock;
    int64_t buffer_size;
    int64_t max_buffer_count;

    std::shared_ptr<File> get_file() {
        std::lock_guard<std::mutex> lock(pool_lock);
        auto file = file_pool.front();
        file_pool.pop();
        return file;
    }

    void put_file(std::shared_ptr<File> file) {
        std::lock_guard<std::mutex> lock(pool_lock);
        file_pool.push(file);
    }

    std::tuple<int64_t, int64_t> align_buffer(int64_t offset, int64_t length) const {
        int64_t aligned_offset = (offset / buffer_size) * buffer_size;
        int64_t aligned_length = ((length + (offset - aligned_offset) + buffer_size - 1) / buffer_size) * buffer_size;
        return {aligned_offset, aligned_length};
    }

    std::tuple<std::shared_ptr<FilePoolBuffer>, bool> get_buffer(int64_t offset, int64_t length) {
        auto [aligned_offset, aligned_length] = align_buffer(offset, length);
        std::lock_guard<std::mutex> lock(buffer_pool_lock);
        auto it = buffer_pool.find(aligned_offset);
        if (it != buffer_pool.end()) {
            auto buffer = it->second;
            buffer_pool.erase(aligned_offset);
            if (buffer->length >= aligned_length) {
                buffer_pool.insert(aligned_offset, buffer);
                return {buffer, true};
            }
        }
        while (buffer_pool.size() >= max_buffer_count) {
            buffer_pool.pop_front();
        }
        auto buffer = std::make_shared<FilePoolBuffer>(aligned_offset, aligned_length);
        buffer_pool.insert(aligned_offset, buffer);
        return {buffer, false};
    }

public:
    FilePool(
        const std::string& path,
        const std::string& mode = "r",
        int64_t parallel = 1,
        int64_t buffer_size = 32768,
        int64_t max_buffer_count = 128
    ) : read_lock(parallel), thread_pool(parallel), buffer_thread_pool(parallel * 2),
        buffer_size(buffer_size), max_buffer_count(max_buffer_count) {
        for (int64_t i = 0; i < parallel; ++i) {
            file_pool.push(open_file(path, mode));
        }
    }

    std::future<int64_t> get_file_size() {
        return thread_pool.enqueue([this]() {
            SemaphoreGuard guard(read_lock);
            auto file = get_file();
            try {
                auto size = file->get_file_size();
                put_file(file);
                return size;
            } catch (...) {
                put_file(file);
                throw;
            }
        });
    }

    std::future<ByteArray> read(int64_t size, int64_t offset) {
        auto [buffer_ptr, found] = get_buffer(offset, size);
        auto buffer = buffer_ptr; // C++17: capture structured bindings by copying to named variables
        if (found) return buffer_thread_pool.enqueue([buffer, offset, size]() {
            return buffer->extract(offset, size);
        });
        return thread_pool.enqueue([this, buffer, offset, size]() {
            SemaphoreGuard guard(read_lock);
            auto file = get_file();
            try {
                auto result = file->read(buffer->length, buffer->offset);
                buffer->data_promise.set_value(std::move(result));
                put_file(file);
            } catch (...) {
                buffer->data_promise.set_exception(std::current_exception());
                put_file(file);
                throw;
            }
            return buffer->extract(offset, size);
        });
    }

    std::future<ByteArray> read_until(
        char delimiter,
        int64_t offset,
        bool include = false,
        bool partial = false,
        int64_t chunk_size = 4096,
        int64_t max_chunk_size = 1048576
    ) {
        return thread_pool.enqueue([this, delimiter, offset, include, partial, chunk_size, max_chunk_size]() mutable {
            ByteArray result;
            while (true) {
                auto chunk = read(chunk_size, offset).get();
                if (chunk.size() == 0) {
                    if (partial) return result;
                    throw std::runtime_error("delimiter not found (end of file reached)");
                }
                auto index = chunk.find(delimiter, 0);
                if (index != -1) {
                    if (include) index += 1;
                    result.extend(chunk.sliced(0, index));
                    return result;
                }
                if (result.size() + chunk.size() > max_chunk_size) {
                    throw std::runtime_error("delimiter not found (maximum size exceeded)");
                }
                result.extend(chunk);
                offset += chunk.size();
            }
        });
    }

    std::future<void> write(const ByteArray& data, int64_t offset) {
        return thread_pool.enqueue([this, data, offset]() {
            std::lock_guard<std::mutex> lock(write_lock);
            auto file = get_file();
            try {
                file->write(data, offset);
                put_file(file);
            } catch (...) {
                put_file(file);
                throw;
            }
        });
    }

};


class TemporaryDirectory {
private:
    std::string path;
    bool cleanup_on_destroy = true;
    
    std::string find_random_suffix() {
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dis(0, 15);
        std::string hex_chars = "0123456789abcdef";
        std::string random_suffix;
        for (int i = 0; i < 8; ++i) {
            random_suffix += hex_chars[dis(gen)];
        }
        return random_suffix;
    }

public:
    TemporaryDirectory(std::string parent, std::string prefix = "tmp.") {
        if (parent == "") parent = std::filesystem::temp_directory_path().string();
        path = parent + "/" + prefix + find_random_suffix();
        uint8_t counter = 0;
        while (std::filesystem::exists(path)) {
            path = parent + "/" + prefix + find_random_suffix();
            counter += 1;
            if (counter > 100) {
                throw std::runtime_error("failed to find a unique directory name in " + parent);
            }
        }
        std::error_code ec;
        if (!std::filesystem::create_directories(path, ec)) {
            throw std::runtime_error("failed to create temporary directory " +
                path + " (" + ec.message() + ")");
        }
    }

    TemporaryDirectory(const TemporaryDirectory&) = delete;
    TemporaryDirectory& operator=(const TemporaryDirectory&) = delete;
    TemporaryDirectory(TemporaryDirectory&& other) noexcept 
        : path(std::move(other.path)), cleanup_on_destroy(other.cleanup_on_destroy) {
        other.cleanup_on_destroy = false;
    }
    
    ~TemporaryDirectory() {
        if (cleanup_on_destroy) cleanup();
    }

    void cleanup() {
        if (std::filesystem::exists(path)) {
            std::error_code ec;
            std::filesystem::remove_all(path, ec);
            if (ec) {
                std::cerr << "WARNING: failed to remove temporary directory " 
                    << path << " (" << ec.message() << ")" << std::endl;
            }
        }
    }

    std::string file(const std::string& name) const {
        return path + "/" + name;
    }

};
