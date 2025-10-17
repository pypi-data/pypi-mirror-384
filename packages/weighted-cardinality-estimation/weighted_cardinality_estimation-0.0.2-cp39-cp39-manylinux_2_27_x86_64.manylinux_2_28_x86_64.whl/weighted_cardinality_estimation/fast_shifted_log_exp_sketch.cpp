#include <cmath>
#include <cstdint>
#include <stdexcept>
#include "fisher_yates.hpp"
#include "hash_util.hpp"
#include<cstring>
#include"fast_shifted_log_exp_sketch.hpp"

FastShiftedLogExpSketch::FastShiftedLogExpSketch(
    std::size_t sketch_size, 
    const std::vector<std::uint32_t>& seeds, 
    uint8_t amount_bits,
    float logarithm_base
)
    : Sketch(sketch_size, seeds),
      fisher_yates(sketch_size),
      amount_bits_(amount_bits),
      logarithm_base(logarithm_base),
      structure(amount_bits, sketch_size)
{
    if (amount_bits == 0) { throw std::invalid_argument("Amount of bits 'b' must be positive."); }
    update_threshold();
}

FastShiftedLogExpSketch::FastShiftedLogExpSketch( 
    std::size_t sketch_size, 
    const std::vector<std::uint32_t>& seeds, 
    std::uint8_t amount_bits, 
    float logarithm_base,
    const std::vector<std::uint32_t>& registers,
    std::int32_t offset
)
    : Sketch(sketch_size, seeds),
      fisher_yates(sketch_size),
      amount_bits_(amount_bits),
      logarithm_base(logarithm_base),
      structure(amount_bits, sketch_size, offset, registers)
{
    if (amount_bits == 0) { throw std::invalid_argument("Amount of bits 'b' must be positive."); }
    update_threshold();
}


size_t FastShiftedLogExpSketch::memory_usage_total() const {
    size_t total_size = 0;
    total_size += sizeof(this->size); // 8
    total_size += seeds_.bytes(); // m * 4
    total_size += fisher_yates.bytes_total(); // 2m ceil(log_2 m)/8 + 8
    total_size += structure.memory_usage_total(); // mb/8 + 8
    total_size += sizeof(amount_bits_); // 1
    total_size += sizeof(logarithm_base); // 4
    total_size += sizeof(min_sketch_value); // 4
    total_size += sizeof(min_value_to_change_sketch); // 8
    return total_size; // 2m ceil(log_2 m)/8 + 4m + mb/8 + 29
}

size_t FastShiftedLogExpSketch::memory_usage_write() const {
    size_t write_size = 0;
    write_size += structure.memory_usage_write(); // mb/8
    write_size += fisher_yates.bytes_write(); // m ceil(log_2 m)/8 + 8
    return write_size; // m ceil(log_2 m)/8 + mb/8 + 8
}

size_t FastShiftedLogExpSketch::memory_usage_estimate() const {
    size_t estimate_size = structure.memory_usage_estimate(); // mb/8 + 4
    estimate_size += sizeof(logarithm_base);// 4
    return estimate_size; // mb/8 + 8
}

std::uint8_t FastShiftedLogExpSketch::get_amount_bits() const { return amount_bits_; }
float FastShiftedLogExpSketch::get_logarithm_base() const { return logarithm_base; }
std::int32_t FastShiftedLogExpSketch::get_offset() const { return structure.get_offset(); }
std::vector<std::uint32_t> FastShiftedLogExpSketch::get_registers() const { return structure.get_registers(); }

void FastShiftedLogExpSketch::add(const std::string& elem, double weight){ 
    double S = 0;
    bool touched_min = false;
    fisher_yates.initialize(murmur64(elem, 1)); 

    for (std::size_t k = 0; k < size; ++k) {
        std::uint64_t h = murmur64(elem, seeds_[k]);
        double u = to_unit_interval(h);   
        double g = -std::log(u) / weight;

        S += g / (double)(this->size -k);

        if (S >= this->min_value_to_change_sketch ) { break; }

        std::uint32_t j = fisher_yates.get_fisher_yates_element(k);

        int q = static_cast<int>(std::floor(-std::log(g)/std::log(logarithm_base)));
        if(q < get_offset()) {
            continue;
        }
        std::uint32_t possible = q - get_offset();
        if (possible == structure[j]) {
            continue; 
        } 
        if (structure[j] < possible) { 
            if (structure[j] == min_sketch_value){
                touched_min = true;
            }
            structure.set(j, possible);
        }
    }
    if (touched_min){
        this->update_threshold();
    }
} 

double FastShiftedLogExpSketch::estimate() const {
    return structure.estimate(logarithm_base);
}

void FastShiftedLogExpSketch::update_threshold(){
    this->min_sketch_value = structure.min();
    this->min_value_to_change_sketch = std::pow(logarithm_base, -this->min_sketch_value-get_offset());
}
