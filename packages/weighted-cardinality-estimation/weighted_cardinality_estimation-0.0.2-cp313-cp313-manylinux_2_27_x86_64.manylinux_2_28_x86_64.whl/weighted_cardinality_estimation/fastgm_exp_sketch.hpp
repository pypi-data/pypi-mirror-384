#pragma once
#include <vector>
#include <string>
#include <cstdint>
#include "fisher_yates.hpp"
#include "sketch.hpp"

class FastGMExpSketch : public Sketch {
// Paper: https://arxiv.org/abs/2302.05176 
public:
    FastGMExpSketch(std::size_t sketch_size, const std::vector<std::uint32_t>& seeds);
    FastGMExpSketch(std::size_t sketch_size, const std::vector<std::uint32_t>& seeds, const std::vector<double>& registers);
    
    void add(const std::string& elem, double weight = 1.0);
    [[nodiscard]] double estimate() const;
    [[nodiscard]] double jaccard_struct(const FastGMExpSketch& other) const;

    const std::vector<double>& get_registers() const;

    [[nodiscard]] size_t memory_usage_total() const;
    [[nodiscard]] size_t memory_usage_write() const;
    [[nodiscard]] size_t memory_usage_estimate() const;
private:
    std::vector<double> M_;
    FisherYates fisher_yates;

    uint32_t j_star;
    uint32_t k_star;
    bool flagFastPrune;
};
