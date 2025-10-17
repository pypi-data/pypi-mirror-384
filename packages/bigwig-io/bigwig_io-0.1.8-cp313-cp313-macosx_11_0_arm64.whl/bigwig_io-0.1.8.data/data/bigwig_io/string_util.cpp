#pragma once

#include <algorithm>
#include <cctype>
#include <sstream>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>


template<typename T>
std::string fstring_tostr(T&& value) {
    if constexpr (std::is_same_v<std::decay_t<T>, std::string>) {
        return std::forward<T>(value);
    } else if constexpr (std::is_same_v<std::decay_t<T>, const char*>) {
        return std::string(value);
    } else if constexpr (std::is_arithmetic_v<std::decay_t<T>>) {
        return std::to_string(std::forward<T>(value));
    } else {
        std::ostringstream oss;
        oss << std::forward<T>(value);
        return oss.str();
    }
}

template<typename... Args>
std::string fstring(const std::string& fmt, Args&&... args) {
    if constexpr (sizeof...(args) == 0) {
        return fmt;
    } else {
        std::ostringstream result;
        std::vector<std::string> arg_strings = {fstring_tostr(std::forward<Args>(args))...};
        size_t arg_index = 0;
        size_t pos = 0;
        size_t found = 0;
        while ((found = fmt.find("{}", pos)) != std::string::npos) {
            if (arg_index >= arg_strings.size()) {
                throw std::runtime_error("not enough arguments for format string");
            }
            result << fmt.substr(pos, found - pos);
            result << arg_strings[arg_index++];
            pos = found + 2;
        }
        if (arg_index < arg_strings.size()) {
            throw std::runtime_error("too many arguments for format string");
        }
        result << fmt.substr(pos);
        return result.str();
    }
}


template<typename... Args>
void print(const std::string& fmt, Args&&... args) {
    std::string message = fstring(fmt, std::forward<Args>(args)...);
    std::cout << message << std::flush;
}


std::string to_lowercase(std::string input) {
    std::transform(
        input.begin(), input.end(), input.begin(),
        [](unsigned char c) { return std::tolower(c); }
    );
    return input;
}

std::string to_uppercase(std::string input) {
    std::transform(
        input.begin(), input.end(), input.begin(),
        [](unsigned char c) { return std::toupper(c); }
    );
    return input;
}


std::vector<std::string> split_string(const std::string& input, char delimiter) {
    std::vector<std::string> result;
    std::istringstream stream(input);
    std::string item;
    while (std::getline(stream, item, delimiter)) {
        result.push_back(item);
    }
    return result;
}
