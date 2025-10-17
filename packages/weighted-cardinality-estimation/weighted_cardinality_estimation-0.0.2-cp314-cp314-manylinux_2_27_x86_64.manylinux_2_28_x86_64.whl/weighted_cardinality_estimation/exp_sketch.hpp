#pragma once
#include <vector>
#include <string>
#include <cstdint>
#include "sketch.hpp"

class ExpSketch : public Sketch {
public:
    ExpSketch(
        std::size_t sketch_size, 
        const std::vector<std::uint32_t>& seeds
    );
    ExpSketch(
        std::size_t sketch_size, 
        const std::vector<std::uint32_t>& seeds, 
        const std::vector<double>& registers
    );

    void add(const std::string& elem, double weight = 1.0);
    [[nodiscard]] double estimate() const;
    [[nodiscard]] double jaccard_struct(const ExpSketch& other) const;

    const std::vector<double>& get_registers() const;
    [[nodiscard]] size_t memory_usage_total() const;
    [[nodiscard]] size_t memory_usage_write() const;
    [[nodiscard]] size_t memory_usage_estimate() const;
private:
    std::vector<double> M_;
};
