#pragma once

#include <cstdint>
#include <functional>
#include <iostream>
#include <mutex>


class ProgressTracker {
    int64_t total;
    int64_t current = 0;
    std::function<void(int64_t, int64_t)> callback;
    double report_interval;
    double last_reported = 0.0;
    std::mutex update_mutex;

public:
    ProgressTracker(
        int64_t total,
        std::function<void(int64_t, int64_t)> callback,
        double report_interval = 0.01
    ) : total(total), callback(callback), report_interval(report_interval) {}

    void add(int64_t value) {
        std::lock_guard<std::mutex> lock(update_mutex);
        current += value;
        double progress = (total > 0) ? static_cast<double>(current) / total : 0.0;
        if (callback && progress > last_reported + report_interval) {
            last_reported = progress;
            callback(current, total);
        }
    }

    void done() {
        std::lock_guard<std::mutex> lock(update_mutex);
        if (callback && last_reported < 1.0) {
            last_reported = 1.0;
            callback(total, total);
        }
    }

};


void print_progress(int64_t current, int64_t total) {
    int64_t percent = (total > 0) ? (current * 100) / total : 100;
    if (percent == 100) {
        std::cout << "\rProgress: 100% " << std::endl;
    } else {
        std::cout << "\rProgress: " << percent << "% " << std::flush;
    }
}
