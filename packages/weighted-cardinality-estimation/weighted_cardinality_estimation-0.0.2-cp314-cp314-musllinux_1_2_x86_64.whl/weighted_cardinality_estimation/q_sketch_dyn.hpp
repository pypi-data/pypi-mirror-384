#pragma once
#include <vector>
#include <string>
#include <cstdint>
#include "compact_vector.hpp"
#include "sketch.hpp"

class QSketchDyn : public Sketch {
public:
    QSketchDyn(
        std::size_t sketch_size, 
        const std::vector<std::uint32_t>& seeds, 
        std::uint8_t amount_bits, 
        std::uint32_t g_seed
    );
    QSketchDyn(
        std::size_t sketch_size,
        std::uint8_t amount_bits,
        std::uint32_t g_seed,
        const std::vector<std::uint32_t>& seeds,
        const std::vector<int>& registers,
        const std::vector<std::uint32_t>& t_histogram,
        double cardinality
    );

    void add(const std::string& elem, double weight = 1.0);
    [[nodiscard]] double estimate() const;
    std::uint8_t get_amount_bits() const;
    std::uint32_t get_g_seed() const;
    std::vector<int> get_registers() const;
    std::vector<std::uint32_t> get_t_histogram() const;
    double get_cardinality() const;

    [[nodiscard]] size_t memory_usage_total() const;
    [[nodiscard]] size_t memory_usage_write() const;
    [[nodiscard]] size_t memory_usage_estimate() const;

private:
    std::uint8_t amount_bits_;
    std::int32_t r_min;
    std::int32_t r_max;
    std::uint32_t g_seed_;

    double cardinality_;
    double q_r_;
    compact::vector<int> R_;
    compact::vector<std::uint32_t> T_; // here are values between 0 and m
};

