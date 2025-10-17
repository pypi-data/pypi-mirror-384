#pragma once

#include <cstdint>
#include <vector>
#include <deque>

#include "util/main.cpp"
#include "locs.cpp"
#include "data_tree.cpp"


struct WigDataHeader {
    int64_t chr_index;
    int64_t chr_start;
    int64_t chr_end;
    int64_t item_step;
    int64_t item_span;
    uint8_t type;
    // uint8_t reserved;
    int64_t item_count;
};


struct ZoomDataRecord {
    int64_t chr_index;
    int64_t chr_start;
    int64_t chr_end;
    int64_t valid_count;
    float min_value;
    float max_value;
    float sum_data;
    float sum_squared;
};


WigDataHeader read_wig_data_header(const ByteArray& buffer) {
    WigDataHeader header;
    header.chr_index = static_cast<int64_t>(buffer.read_uint32(0));
    header.chr_start = static_cast<int64_t>(buffer.read_uint32(4));
    header.chr_end = static_cast<int64_t>(buffer.read_uint32(8));
    header.item_step = static_cast<int64_t>(buffer.read_uint32(12));
    header.item_span = static_cast<int64_t>(buffer.read_uint32(16));
    header.type = buffer.read_uint8(20);
    // header.reserved = buffer.read_uint8(21);
    header.item_count = buffer.read_uint16(22);
    return header;
}


ZoomDataRecord read_zoom_data_record(const ByteArray& buffer, int64_t offset) {
    ZoomDataRecord record;
    record.chr_index = static_cast<int64_t>(buffer.read_uint32(offset));
    record.chr_start = static_cast<int64_t>(buffer.read_uint32(offset + 4));
    record.chr_end = static_cast<int64_t>(buffer.read_uint32(offset + 8));
    record.valid_count = static_cast<int64_t>(buffer.read_uint32(offset + 12));
    record.min_value = buffer.read_float(offset + 16);
    record.max_value = buffer.read_float(offset + 20);
    record.sum_data = buffer.read_float(offset + 24);
    record.sum_squared = buffer.read_float(offset + 28);
    return record;
}


struct DataInterval {
    int64_t chr_index;
    int64_t start;
    int64_t end;
    float value;
};


class DataIntervalGenerator : public GeneratorBase<DataIntervalGenerator, DataInterval> {
    int64_t min_loc_start;
    int64_t max_loc_end;
    int64_t zoom_level;
    ByteArray buffer;
    WigDataHeader header;
    int64_t count;
    int64_t index = 0;

public:
    DataIntervalGenerator(
        FilePool& file,
        const DataTreeItem& data_tree_item,
        const std::vector<Loc>& locs,
        const LocsInterval& locs_interval,
        int64_t zoom_level,
        int64_t uncompress_buffer_size
    ) : zoom_level(zoom_level) {
        buffer = file.read(data_tree_item.data_size, data_tree_item.data_offset).get();
        if (uncompress_buffer_size > 0) buffer = buffer.decompressed(uncompress_buffer_size);
        if (zoom_level >= 0) {
            count = data_tree_item.data_size / 32;
        } else {
            header = read_wig_data_header(buffer);
            count = header.item_count;
        }
        min_loc_start = locs[locs_interval.start].binned_start;
        max_loc_end = locs[locs_interval.start].binned_end;
        for (int64_t i = locs_interval.start + 1; i < locs_interval.end; ++i) {
            if (locs[i].binned_end > max_loc_end) max_loc_end = locs[i].binned_end;
        }
    }
    
    NextResult next() {
        while (index < count) {
            DataInterval data;
            if (zoom_level >= 0) { // zoom record
                ZoomDataRecord record = read_zoom_data_record(buffer, index * 32);
                if (record.valid_count == 0) {
                    index += 1;
                    continue;
                }
                data.chr_index = record.chr_index;
                data.start = record.chr_start;
                data.end = record.chr_end;
                data.value = record.sum_data / record.valid_count;
            } else if (header.type == 1) { // bedgraph
                data.chr_index = header.chr_index;
                data.start = static_cast<int64_t>(buffer.read_uint32(24 + index * 12));
                data.end = static_cast<int64_t>(buffer.read_uint32(24 + index * 12 + 4));
                data.value = buffer.read_float(24 + index * 12 + 8);
            } else if (header.type == 2) { // variable step wig
                data.chr_index = header.chr_index;
                data.start = static_cast<int64_t>(buffer.read_uint32(24 + index * 8));
                data.end = data.start + static_cast<int64_t>(header.item_span);
                data.value = buffer.read_float(24 + index * 8 + 4);
            } else if (header.type == 3) { // fixed step wig
                data.chr_index = header.chr_index;
                data.start = static_cast<int64_t>(header.chr_start) + index * header.item_step;
                data.end = data.start +  static_cast<int64_t>(header.item_span);
                data.value = buffer.read_float(24 + index * 4);
            } else {
                throw std::runtime_error(fstring("wig data type {} invalid", header.type));
            }
            index += 1;
            if (data.end <= min_loc_start) continue;
            if (data.start >= max_loc_end) break;
            return {data, false};
        }
        return {DataInterval{}, true};
    }
};


struct BedEntry {
    int64_t chr_index;
    int64_t start;
    int64_t end;
    OrderedMap<std::string, std::string> fields;
};


class BedEntryGenerator : public GeneratorBase<BedEntryGenerator, BedEntry> {
    Loc first_loc;
    Loc last_loc;
    const OrderedMap<std::string, std::string>& auto_sql;
    ByteArray buffer;
    int64_t offset = 0;

public:
    BedEntryGenerator(
        FilePool& file,
        const DataTreeItem& data_tree_item,
        const std::vector<Loc>& locs,
        const LocsInterval& locs_interval,
        const OrderedMap<std::string, std::string>& auto_sql,
        int64_t uncompress_buffer_size
    ) : auto_sql(auto_sql) {
        buffer = file.read(data_tree_item.data_size, data_tree_item.data_offset).get();
        if (uncompress_buffer_size > 0) buffer = buffer.decompressed(uncompress_buffer_size);
        first_loc = locs[locs_interval.start];
        last_loc = locs[locs_interval.end - 1];
    }

    NextResult next() {
        while (offset < buffer.size()) {
            BedEntry entry;
            entry.chr_index = buffer.read_uint32(offset);
            entry.start = buffer.read_uint32(offset + 4);
            entry.end = buffer.read_uint32(offset + 8);
            offset += 12;
            int64_t end_offset = buffer.find('\0', offset);
            if (end_offset == -1) throw std::runtime_error("invalid bed entry (null terminator not found)");
            std::string raw_fields = buffer.read_string(offset, end_offset - offset);
            auto fields = split_string(raw_fields, '\t');
            if (static_cast<int64_t>(fields.size()) != auto_sql.size() - 3) {
                throw std::runtime_error("invalid bed entry (field count mismatch)");
            }
            int64_t field_index = 0;
            for (const auto& sql_field : auto_sql) {
                if (field_index >= 3) {
                    entry.fields.insert(sql_field.first, fields[field_index - 3]);
                }
                field_index += 1;
            }
            offset = end_offset + 1;
            if (entry.end <= first_loc.binned_start) continue;
            if (entry.start >= last_loc.binned_end) break;
            return {entry, false};
        }
        return {BedEntry{}, true};
    }
};
