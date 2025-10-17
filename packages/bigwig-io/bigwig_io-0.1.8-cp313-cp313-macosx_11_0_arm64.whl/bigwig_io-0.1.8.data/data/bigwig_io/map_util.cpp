#pragma once

#include <cstdint>
#include <initializer_list>
#include <list>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <unordered_map>
#include <utility>
#include <vector>


template <typename K, typename V, bool MoveOnReinsert = false, bool InsertOnLookup = false>
class OrderedMap {
    std::list<std::pair<K, V>> order;
    std::unordered_map<K, typename std::list<std::pair<K, V>>::iterator> map;

    template<typename KeyType>
    static std::string format_key(const KeyType& key) {
        if constexpr (std::is_same_v<KeyType, std::string>) {
            return "'" + key + "'";
        } else if constexpr (std::is_arithmetic_v<KeyType>) {
            return std::to_string(key);
        } else {
            return "< repr unavailable >";
        }
    }

public:
    OrderedMap() = default;
    
    OrderedMap(std::initializer_list<std::pair<K, V>> init) {
        for (const auto& pair : init) {
            order.push_back(pair);
            auto list_it = std::prev(order.end());
            map.emplace(pair.first, list_it);
        }
    }

    auto begin() { return order.begin(); }
    auto end() { return order.end(); }
    auto begin() const { return order.begin(); }
    auto end() const { return order.end(); }

    int64_t size() const { return static_cast<int64_t>(map.size()); }
    bool empty() const { return map.empty(); }

    V& operator[](const K& key) {
        auto it = map.find(key);
        if (it != map.end()) {
            if constexpr (MoveOnReinsert) {
                order.splice(order.end(), order, it->second);
            }
            return it->second->second;
        } else {
            if constexpr (InsertOnLookup) {
                order.emplace_back(key, V{});
                auto list_it = std::prev(order.end());
                map.emplace(key, list_it);
                return list_it->second;
            } else {
                throw std::out_of_range("key " + format_key(key) + " not found");
            }
        }
    }

    void insert(const K& key, const V& value) {
        auto it = map.find(key);
        if (it != map.end()) {
            if constexpr (MoveOnReinsert) {
                order.splice(order.end(), order, it->second);
            }
            it->second->second = value;
        } else {
            order.emplace_back(key, value);
            auto list_it = std::prev(order.end());
            map.emplace(key, list_it);
        }
    }

    void emplace(const K& key, V&& value) {
        auto it = map.find(key);
        if (it != map.end()) {
            if constexpr (MoveOnReinsert) {
                order.splice(order.end(), order, it->second);
            }
            it->second->second = std::move(value);
        } else {
            order.emplace_back(key, std::move(value));
            auto list_it = std::prev(order.end());
            map.emplace(key, list_it);
        }
    }

    void clear() {
        order.clear();
        map.clear();
    }

    void erase(const K& key) {
        auto it = map.find(key);
        if (it != map.end()) {
            order.erase(it->second);
            map.erase(it);
        }
    }

    V pop_front() {
        if (order.empty()) throw std::out_of_range("map is empty");
        auto it = order.begin();
        V value = std::move(it->second);  // Move the value before erasing
        map.erase(it->first);
        order.pop_front();
        return value;
    }

    V pop_back() {
        if (order.empty()) throw std::out_of_range("map is empty");
        auto it = std::prev(order.end());
        V value = std::move(it->second);  // Move the value before erasing
        map.erase(it->first);
        order.pop_back();
        return value;
    }

    V& at(const K& key) {
        auto it = map.find(key);
        if (it == map.end()) throw std::out_of_range("key " + format_key(key) + " not found");
        return it->second->second;
    }

    const V& at(const K& key) const {
        auto it = map.find(key);
        if (it == map.end()) throw std::out_of_range("key " + format_key(key) + " not found");
        return it->second->second;
    }

    V& at_index(uint64_t index) {
        if (index >= order.size()) throw std::out_of_range("index " + std::to_string(index) + " out of range");
        auto it = order.begin();
        std::advance(it, index);
        return it->second;
    }

    const V& at_index(int64_t index) const {
        if (index >= size()) throw std::out_of_range("index " + std::to_string(index) + " out of range");
        auto it = order.begin();
        std::advance(it, index);
        return it->second;
    }

    K& key_at_index(int64_t index) {
        if (index >= size()) throw std::out_of_range("index " + std::to_string(index) + " out of range");
        auto it = order.begin();
        std::advance(it, index);
        return it->first;
    }

    const K& key_at_index(uint64_t index) const {
        if (index >= size()) throw std::out_of_range("index " + std::to_string(index) + " out of range");
        auto it = order.begin();
        std::advance(it, index);
        return it->first;
    }

    bool contains(const K& key) const {
        return map.find(key) != map.end();
    }

    typename std::list<std::pair<K, V>>::iterator find(const K& key) {
        auto it = map.find(key);
        if (it != map.end()) return it->second;
        return order.end();
    }

    typename std::list<std::pair<K, V>>::const_iterator find(const K& key) const {
        auto it = map.find(key);
        if (it != map.end()) return it->second;
        return order.end();
    }

    std::vector<K> keys() const {
        std::vector<K> result;
        result.reserve(order.size());
        for (const auto& pair : order) {
            result.push_back(pair.first);
        }
        return result;
    }

    std::vector<V> values() const {
        std::vector<V> result;
        result.reserve(order.size());
        for (const auto& pair : order) {
            result.push_back(pair.second);
        }
        return result;
    }

};
