#pragma once

#include <cstdint>
#include <vector>
#include <deque>

#include "util/main.cpp"
#include "locs.cpp"


struct DataTreeNodeHeader {
    uint8_t is_leaf;
    // uint8_t reserved;
    int64_t count;
};


DataTreeNodeHeader read_data_tree_node_header(FilePool& file, int64_t offset) {
    ByteArray buffer = file.read(4, offset).get();
    DataTreeNodeHeader node_header;
    node_header.is_leaf = buffer.read_uint8(0);
    // node_header.reserved = buffer.read_uint8(1);
    node_header.count = static_cast<int64_t>(buffer.read_uint16(2));
    return node_header;
}


struct DataTreeItem {
    int64_t start_chr_index;
    int64_t start_base;
    int64_t end_chr_index;
    int64_t end_base;
    int64_t data_offset;
    int64_t data_size;
};


struct DataTreeGeneratorItem {
    DataTreeItem item;
    LocsInterval locs;
};

struct DataTreeGeneratorState {
    DataTreeNodeHeader node_header;
    ByteArray node_buffer;
    int64_t node_size;
    int64_t item_index;
};


class DataTreeGenerator : public GeneratorBase<DataTreeGenerator, DataTreeGeneratorItem> {
    FilePool& file;
    const std::vector<Loc>& locs;
    LocsInterval locs_interval;
    ProgressTracker& tracker;
    std::deque<DataTreeGeneratorState> states;

    DataTreeGeneratorState next_node(int64_t offset) {
        auto node_header = read_data_tree_node_header(file, offset);
        int64_t node_size = node_header.is_leaf ? 32 : 24;
        ByteArray node_buffer = file.read(node_size * node_header.count, offset + 4).get();
        return {node_header, node_buffer, node_size, 0};
    }

public:
    DataTreeGenerator(
        FilePool& file,
        const std::vector<Loc>& locs,
        LocsInterval locs_interval,
        ProgressTracker& tracker,
        int64_t offset
    ) : file(file), locs(locs), locs_interval(locs_interval), tracker(tracker) {
            states.push_front(next_node(offset));
        }

    NextResult next() {
        while (!states.empty()) {
            DataTreeGeneratorState& state = states.front();
            if (state.item_index == state.node_header.count) {
                states.pop_front();
                continue;
            }
            while (state.item_index < state.node_header.count) {
                int64_t item_buffer_offset = state.item_index * state.node_size;
                int64_t item_start_chr_index = static_cast<int64_t>(state.node_buffer.read_uint32(item_buffer_offset));
                int64_t item_start_base = static_cast<int64_t>(state.node_buffer.read_uint32(item_buffer_offset + 4));
                int64_t item_end_chr_index = static_cast<int64_t>(state.node_buffer.read_uint32(item_buffer_offset + 8));
                int64_t item_end_base = static_cast<int64_t>(state.node_buffer.read_uint32(item_buffer_offset + 12));
                int64_t item_end_loc_index = locs_interval.start;
                for (int64_t loc_index = locs_interval.start; loc_index < locs_interval.end; ++loc_index) {
                    auto loc = locs[loc_index];
                    if (loc.chr_index < item_start_chr_index || (loc.chr_index == item_start_chr_index && loc.end <= item_start_base)) {
                        tracker.add(loc.binned_end - loc.binned_start);
                        locs_interval.start += 1;
                        continue;
                    }
                    if (loc.chr_index > item_end_chr_index || (loc.chr_index == item_end_chr_index && loc.binned_start > item_end_base)) {
                        break;
                    }
                    item_end_loc_index = loc_index + 1;
                }
                if (item_end_loc_index <= locs_interval.start) {
                    state.item_index += 1;
                    continue;
                }
                int64_t item_data_offset = static_cast<int64_t>(state.node_buffer.read_uint64(item_buffer_offset + 16));
                if (state.node_header.is_leaf) {
                    int64_t item_data_size = static_cast<int64_t>(state.node_buffer.read_uint64(item_buffer_offset + 24));
                    state.item_index += 1;
                    return {{{item_start_chr_index, item_start_base, item_end_chr_index, item_end_base, item_data_offset, item_data_size}, {locs_interval.start, item_end_loc_index}}, false};
                } else {
                    state.item_index += 1;
                    states.push_front(next_node(item_data_offset));
                    break;
                }
            }
        }
        while (locs_interval.start < locs_interval.end) {
            auto loc = locs[locs_interval.start];
            tracker.add(loc.binned_end - loc.binned_start);
            locs_interval.start += 1;
        }
        return {{{}, {}}, true};
    }
};
