#pragma once

#include <map>
#include <string>
#include <cstdint>
#include <vector>
#include <regex>
#include <sstream>
#include <tuple>
#include <set>

#include "util/main.cpp"
#include "headers.cpp"


struct ValueStats {
    float sum = 0;
    int64_t count = 0;
};


struct FullValueStats {
    float min = std::numeric_limits<float>::quiet_NaN();
    float max = std::numeric_limits<float>::quiet_NaN();
    float sum = 0;
    float sum_squared = 0;
    int64_t count = 0;
};


struct Loc {
    int64_t chr_index;
    int64_t start;
    int64_t end;
    int64_t binned_start;
    int64_t binned_end;
    double bin_size;
    int64_t output_start_index;
    int64_t output_end_index;
};


class Locs : public std::vector<Loc> {
public:
    int64_t bin_count;
    using std::vector<Loc>::vector;
};


struct LocsInterval {
    int64_t start;
    int64_t end;
};


class LocsIntervals : public std::vector<LocsInterval> {
public:
    using std::vector<LocsInterval>::vector;
};


std::tuple<std::vector<int64_t>, std::vector<int64_t>> preparse_locs(
    const std::vector<std::string>& chr_ids,
    const std::vector<int64_t>& starts={},
    const std::vector<int64_t>& ends={},
    const std::vector<int64_t>& centers={},
    int64_t span = -1
) {
    std::vector<int64_t> preparsed_starts;
    std::vector<int64_t> preparsed_ends;
    if (span >= 0) {
        uint8_t starts_specified = starts.empty() ? 0 : 1;
        uint8_t ends_specified = ends.empty() ? 0 : 1;
        uint8_t centers_specified = centers.empty() ? 0 : 1;
        if (starts_specified + ends_specified + centers_specified != 1) {
            throw std::runtime_error("either starts/ends/centers must be specified when using span");
        } else if (starts_specified != 0) {
            preparsed_starts = starts;
            preparsed_ends.resize(starts.size());
            for (uint64_t i = 0; i < starts.size(); ++i) {
                preparsed_ends[i] = starts[i] + span;
            }
        } else if (ends_specified != 0) {
            preparsed_ends = ends;
            preparsed_starts.resize(ends.size());
            for (uint64_t i = 0; i < ends.size(); ++i) {
                preparsed_starts[i] = ends[i] - span;
            }
        } else {
            preparsed_starts.resize(centers.size());
            preparsed_ends.resize(centers.size());
            for (uint64_t i = 0; i < centers.size(); ++i) {
                preparsed_starts[i] = centers[i] - span / 2;
                preparsed_ends[i] = centers[i] + (span + 1) / 2;
            }
        }
    } else if (starts.empty() || ends.empty()) {
        throw std::runtime_error("either starts+ends or starts/ends/centers+span must be specified");
    } else {
        preparsed_starts = starts;
        preparsed_ends = ends;
    }
    if (chr_ids.size() != preparsed_starts.size() || chr_ids.size() != preparsed_ends.size()) {
        throw std::runtime_error("length mismatch between chr_ids and starts/ends/centers");
    }
    return {preparsed_starts, preparsed_ends};
}


ChrTreeItem parse_chr(
    const std::string& chr_id,
    const OrderedMap<std::string, ChrTreeItem>& chr_map,
    int64_t key_size
) {
    std::string chr_key = chr_id.substr(0, key_size);
    auto it = chr_map.find(chr_key);
    if (it != chr_map.end()) return it->second;
    it = chr_map.find(to_lowercase(chr_key));
    if (it != chr_map.end()) return it->second;
    it = chr_map.find(to_uppercase(chr_key));
    if (it != chr_map.end()) return it->second;
    if (to_lowercase(chr_id.substr(0, 3)) == "chr") {
        chr_key = chr_id.substr(3).substr(0, key_size);
    } else {
        chr_key = ("chr" + chr_id).substr(0, key_size);
    }
    it = chr_map.find(chr_key);
    if (it != chr_map.end()) return it->second;
    it = chr_map.find(to_lowercase(chr_key));
    if (it != chr_map.end()) return it->second;
    it = chr_map.find(to_uppercase(chr_key));
    if (it != chr_map.end()) return it->second;
    std::string available;
    for (const auto& entry : chr_map) {
        if (!available.empty()) available += ", ";
        available += entry.first;
    }
    throw std::runtime_error(fstring("chr {} not in bigwig ({})", chr_id, available));
}


Locs parse_locs(
    const OrderedMap<std::string, ChrTreeItem>& chr_map,
    int64_t key_size,
    const std::vector<std::string>& chr_ids,
    const std::vector<int64_t>& starts,
    const std::vector<int64_t>& ends,
    double bin_size = 1.0,
    int64_t bin_count = -1,
    bool full_bin = false
) {
    if (chr_ids.size() != starts.size() || (!ends.empty() && chr_ids.size() != ends.size())) {
        throw std::runtime_error("length mismatch between chr_ids, starts or ends");
    }
    Locs locs(chr_ids.size());
    std::set<int64_t> binned_spans;
    for (int64_t i = 0; i < static_cast<int64_t>(chr_ids.size()); ++i) {
        Loc loc;
        loc.chr_index = parse_chr(chr_ids[i], chr_map, key_size).chr_index;
        loc.start = starts[i];
        loc.end = ends[i];
        if (loc.start > loc.end) {
            throw std::runtime_error(fstring("loc {}:{}-{} at index {} invalid", chr_ids[i], loc.start, loc.end, i));
        }
        loc.binned_start = static_cast<int64_t>(std::floor(loc.start / bin_size) * bin_size);
        loc.binned_end = full_bin
            ? static_cast<int64_t>(std::ceil(loc.end / bin_size) * bin_size)
            : static_cast<int64_t>(std::floor(loc.end / bin_size) * bin_size);
        locs[i] = loc;
        binned_spans.insert(loc.binned_end - loc.binned_start);
    }
    if (bin_count < 0) bin_count = static_cast<int64_t>(std::floor(*binned_spans.rbegin() / bin_size));
    std::sort(locs.begin(), locs.end(), [](const Loc& a, const Loc& b) {
        return std::tie(a.chr_index, a.binned_start, a.binned_end) < std::tie(b.chr_index, b.binned_start, b.binned_end);
    });
    for (int64_t i = 0; i < static_cast<int64_t>(chr_ids.size()); ++i) {
        auto& loc = locs[i];
        loc.bin_size = static_cast<double>(loc.binned_end - loc.binned_start) / bin_count;
        loc.output_start_index = i * bin_count;
        loc.output_end_index = (i + 1) * bin_count;
    }
    locs.bin_count = bin_count;
    return locs;
}


int64_t get_locs_coverage(const Locs& locs) {
    int64_t coverage = 0;
    for (const auto& loc : locs) {
        coverage += (loc.binned_end - loc.binned_start);
    }
    return coverage;
}


std::tuple<LocsIntervals, int64_t> get_locs_batchs(
    const Locs& locs,
    int64_t parallel = 1
) {
    int64_t total_coverage = get_locs_coverage(locs);
    int64_t coverage_per_batch = total_coverage / parallel;
    LocsIntervals locs_batchs;
    if (locs.empty()) return {locs_batchs, 0};
    locs_batchs.push_back({0, 0});
    int64_t coverage = 0;
    for (int64_t i = 0 ; i < static_cast<int64_t>(locs.size()) - 1; ++i) {
        coverage += (locs[i].binned_end - locs[i].binned_start);
        if (coverage >= coverage_per_batch) {
            locs_batchs.back().end = i + 1;
            locs_batchs.push_back({i + 1, i + 1});
            coverage = 0;
        }
    }
    locs_batchs.back().end = locs.size();
    return {locs_batchs, total_coverage};
}
