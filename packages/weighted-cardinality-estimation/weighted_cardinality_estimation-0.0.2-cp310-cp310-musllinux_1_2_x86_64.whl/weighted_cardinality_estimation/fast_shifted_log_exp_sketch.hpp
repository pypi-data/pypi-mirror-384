#pragma once
#include "fisher_yates.hpp"
#include "sketch.hpp"
#include <sys/types.h>
#include <vector>
#include <string>
#include <cstdint>
#include"shifted_log_exp_sketch_structure.hpp"

class FastShiftedLogExpSketch : public Sketch {
public:
    FastShiftedLogExpSketch( 
        std::size_t sketch_size, 
        const std::vector<std::uint32_t>& seeds, 
        std::uint8_t amount_bits,
        float logarithm_base
    );
    FastShiftedLogExpSketch(
        std::size_t sketch_size, 
        const std::vector<std::uint32_t>& seeds, 
        std::uint8_t amount_bits, 
        float logarithm_base,
        const std::vector<uint32_t>& registers,
        std::int32_t offset
    );
    void add(const std::string& elem, double weight = 1.0);
    [[nodiscard]] double estimate() const ;

    std::uint8_t get_amount_bits() const;
    float get_logarithm_base() const;
    std::vector<uint32_t> get_registers() const;
    std::int32_t get_offset() const;

    [[nodiscard]] size_t memory_usage_total() const;
    [[nodiscard]] size_t memory_usage_write() const;
    [[nodiscard]] size_t memory_usage_estimate() const;
private:
    FisherYates fisher_yates;
    std::uint8_t amount_bits_;
    float logarithm_base;
    ShiftedLogExpSketchStructure structure;

    void update_threshold();
    std::uint32_t min_sketch_value; 
    double min_value_to_change_sketch; // that's 2**{-min_sketch_value}
};
