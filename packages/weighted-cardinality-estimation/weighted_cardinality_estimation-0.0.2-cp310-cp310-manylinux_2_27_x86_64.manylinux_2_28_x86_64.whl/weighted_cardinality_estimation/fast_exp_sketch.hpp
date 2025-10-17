#pragma once
#include <vector>
#include <string>
#include <cstdint>
#include "fisher_yates.hpp"
#include "sketch.hpp"

class FastExpSketch : public Sketch {
public:
    FastExpSketch(
        std::size_t size, 
        const std::vector<std::uint32_t>& seeds
    );
    FastExpSketch(
        std::size_t sketch_size, 
        const std::vector<std::uint32_t>& seeds, 
        const std::vector<double>& registers
    );
    void add(const std::string& elem, double weight = 1.0);
    [[nodiscard]] double estimate() const;
    [[nodiscard]] double jaccard_struct(const FastExpSketch& other) const;

    const std::vector<double>& get_registers() const;

    [[nodiscard]] size_t memory_usage_total() const;
    [[nodiscard]] size_t memory_usage_write() const;
    [[nodiscard]] size_t memory_usage_estimate() const;
private:
    std::vector<double> M_;
    FisherYates fisher_yates;
    double max;    
};
