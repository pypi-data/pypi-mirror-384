#pragma once
#include "compact_vector.hpp"
#include <vector>
#include <string>
#include <cstdint>
#include "fisher_yates.hpp"
#include "sketch.hpp"

class FastQSketch : public Sketch {
public:
    FastQSketch(std::size_t sketch_size, 
        const std::vector<std::uint32_t>& seeds, 
        std::uint8_t amount_bits
    );
    FastQSketch(
        std::size_t sketch_size, 
        const std::vector<std::uint32_t>& seeds, 
        std::uint8_t amount_bits, 
        const std::vector<int>& registers
    );
    void add(const std::string& elem, double weight = 1.0);
    [[nodiscard]] double estimate() const;

    std::uint8_t get_amount_bits() const;
    std::vector<int> get_registers() const;

    [[nodiscard]] size_t memory_usage_total() const;
    [[nodiscard]] size_t memory_usage_write() const;
    [[nodiscard]] size_t memory_usage_estimate() const;
private:
    double initialValue() const;
    double ffunc_divided_by_dffunc(double w) const;
    double Newton(double c0) const;

    void update_treshold();

    FisherYates fisher_yates;
    std::uint8_t amount_bits_;
    std::int32_t r_max; // maximum possible value in sketch due to amount of bits per register
    std::int32_t r_min; // minimum possible value in sketch due to amount of bits per register

    compact::vector<int> M_; // sketch structure with elements between < r_min ... r_max >
    int min_sketch_value; 
    double min_value_to_change_sketch; // that's 2**{-min_sketch_value}
};
