#pragma once

#include <condition_variable>
#include <functional>
#include <future>
#include <mutex>
#include <queue>
#include <stdexcept>
#include <thread>
#include <type_traits>
#include <vector>



int64_t get_available_threads() {
    unsigned int n = std::thread::hardware_concurrency();
    return (n == 0) ? 1 : static_cast<int64_t>(n);
}


class ThreadPool {
private:
    std::vector<std::thread> workers;
    std::queue<std::function<void()>> tasks;
    std::mutex queue_mutex;
    std::condition_variable condition;
    std::condition_variable wait_condition;
    bool stop;
    int64_t active_tasks;

public:
    explicit ThreadPool(uint64_t parallel) : stop(false), active_tasks(0) {
        if (parallel == 0) parallel = 1;
        for (uint64_t i = 0; i < parallel; ++i) {
            workers.emplace_back([this] {
                while (true) {
                    std::function<void()> task;
                    {
                        std::unique_lock<std::mutex> lock(this->queue_mutex);
                        this->condition.wait(lock, [this] { 
                            return this->stop || !this->tasks.empty(); 
                        });
                        if (this->stop && this->tasks.empty()) {
                            return;
                        }
                        task = std::move(this->tasks.front());
                        this->tasks.pop();
                        this->active_tasks += 1;
                    }
                    task();
                    {
                        std::unique_lock<std::mutex> lock(this->queue_mutex);
                        this->active_tasks -= 1;
                        if (this->active_tasks == 0 && this->tasks.empty()) {
                            this->wait_condition.notify_all();
                        }
                    }
                }
            });
        }
    }

    ~ThreadPool() {
        {
            std::unique_lock<std::mutex> lock(queue_mutex);
            stop = true;
        }
        condition.notify_all();
        for (std::thread& worker : workers) {
            if (worker.joinable()) {
                worker.join();
            }
        }
    }

    template<typename F, typename... Args>
    auto enqueue(F&& f, Args&&... args) -> std::future<std::invoke_result_t<F, Args...>> {
        using return_type = std::invoke_result_t<F, Args...>;

        auto task = std::make_shared<std::packaged_task<return_type()>>(
            std::bind(std::forward<F>(f), std::forward<Args>(args)...)
        );

        std::future<return_type> result = task->get_future();
        {
            std::unique_lock<std::mutex> lock(queue_mutex);
            if (stop) {
                throw std::runtime_error("enqueue on stopped ThreadPool");
            }
            tasks.emplace([task]() { (*task)(); });
        }
        condition.notify_one();
        return result;
    }

    void wait() {
        std::unique_lock<std::mutex> lock(queue_mutex);
        wait_condition.wait(lock, [this] {
            return this->tasks.empty() && this->active_tasks == 0;
        });
    }

    ThreadPool(const ThreadPool&) = delete;
    ThreadPool& operator=(const ThreadPool&) = delete;

};


class Semaphore {
    std::mutex mtx;
    std::condition_variable cv;
    int count;

public:
    explicit Semaphore(int initial) : count(initial) {}

    void acquire() {
        std::unique_lock<std::mutex> lock(mtx);
        cv.wait(lock, [&] { return count > 0; });
        count -= 1;
    }

    void release() {
        std::unique_lock<std::mutex> lock(mtx);
        count += 1;
        lock.unlock();
        cv.notify_one();
    }

};


class SemaphoreGuard {
    Semaphore& sem;
    bool owns;

public:
    explicit SemaphoreGuard(Semaphore& sem) : sem(sem), owns(true) {
        sem.acquire();
    }

    ~SemaphoreGuard() {
        if (owns) sem.release();
    }

    SemaphoreGuard(const SemaphoreGuard&) = delete;
    SemaphoreGuard& operator=(const SemaphoreGuard&) = delete;
    SemaphoreGuard& operator=(SemaphoreGuard&&) = delete;

    SemaphoreGuard(SemaphoreGuard&& other) noexcept : sem(other.sem), owns(other.owns) {
        other.owns = false;
    }

};
