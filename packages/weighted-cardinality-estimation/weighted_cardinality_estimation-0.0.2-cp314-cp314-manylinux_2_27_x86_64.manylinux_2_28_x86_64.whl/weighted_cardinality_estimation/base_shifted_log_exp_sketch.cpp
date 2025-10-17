#include <cmath>
#include <cstdint>
#include <stdexcept>
#include "hash_util.hpp"
#include<cstring>
#include"base_shifted_log_exp_sketch.hpp"

BaseShiftedLogExpSketch::BaseShiftedLogExpSketch(
    std::size_t sketch_size, 
    const std::vector<std::uint32_t>& seeds, 
    uint8_t amount_bits,
    float logarithm_base
)
    : Sketch(sketch_size, seeds),
      amount_bits_(amount_bits),
      logarithm_base(logarithm_base),
      structure(amount_bits, sketch_size)
{
    if (amount_bits == 0) { throw std::invalid_argument("Amount of bits 'b' must be positive."); }
}

BaseShiftedLogExpSketch::BaseShiftedLogExpSketch(
    std::size_t sketch_size, 
    const std::vector<std::uint32_t>& seeds, 
    std::uint8_t amount_bits, 
    float logarithm_base,
    const std::vector<std::uint32_t>& registers,
    std::int32_t offset
)
    : Sketch(sketch_size, seeds),
      amount_bits_(amount_bits),
      logarithm_base(logarithm_base),
      structure(amount_bits, sketch_size, offset, registers)
{
    if (amount_bits == 0) { throw std::invalid_argument("Amount of bits 'b' must be positive."); }
}


size_t BaseShiftedLogExpSketch::memory_usage_total() const {
    size_t total_size = 0;
    total_size += sizeof(size); // <long> 8
    total_size += sizeof(amount_bits_); // <byte> 1
    total_size += sizeof(logarithm_base); // <int> 4
    total_size += seeds_.bytes(); // m * 4
    total_size += structure.memory_usage_total(); // mb/8 + 8
    return total_size; // m * 4 + mb/8 + 21
}

size_t BaseShiftedLogExpSketch::memory_usage_write() const {
    size_t write_size = 0;
    write_size += structure.memory_usage_write(); // mb/8
    return write_size; // mb/8
}

size_t BaseShiftedLogExpSketch::memory_usage_estimate() const {
    size_t estimate_size = structure.memory_usage_estimate(); // mb/8 + 4
    estimate_size += sizeof(logarithm_base); // 4
    return estimate_size; // mb/8 + 8
}

std::uint8_t BaseShiftedLogExpSketch::get_amount_bits() const { return amount_bits_; }
float BaseShiftedLogExpSketch::get_logarithm_base() const { return logarithm_base; }
std::int32_t BaseShiftedLogExpSketch::get_offset() const { return structure.get_offset(); }
std::vector<std::uint32_t> BaseShiftedLogExpSketch::get_registers() const { return structure.get_registers(); }

void BaseShiftedLogExpSketch::add(const std::string& elem, double weight){ 
    for (std::size_t i = 0; i < size; ++i) {
        std::uint64_t h = murmur64(elem, seeds_[i]);
        double u = to_unit_interval(h);   
        double g = -std::log(u) / weight;
        int q = static_cast<int>(std::floor(-std::log(g)/std::log(logarithm_base)));
        if(q - get_offset() < 0) {
            continue;
        }
        std::uint32_t possible = q - get_offset();
        if (possible == structure[i]) {
            continue; // jaccard usage
        } 
        if (structure[i] < possible) { 
            structure.set(i, possible);
        }
    }
} 

double BaseShiftedLogExpSketch::estimate() const {
    return structure.estimate(logarithm_base);
}