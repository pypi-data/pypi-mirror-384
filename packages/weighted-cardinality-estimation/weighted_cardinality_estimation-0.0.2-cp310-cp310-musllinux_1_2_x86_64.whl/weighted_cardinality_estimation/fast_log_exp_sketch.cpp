#include <algorithm>
#include <cmath>
#include <stdexcept>
#include "hash_util.hpp"
#include<cstring>
#include "utils.hpp"
#include"fast_log_exp_sketch.hpp"

FastLogExpSketch::FastLogExpSketch(
    std::size_t sketch_size, 
    const std::vector<std::uint32_t>& seeds, 
    uint8_t amount_bits,
    float logarithm_base
)
    : Sketch(sketch_size, seeds),
      fisher_yates(size),
      amount_bits_(amount_bits),
      logarithm_base(logarithm_base),
      r_max((1 << (amount_bits - 1)) - 1),
      r_min(-(1 << (amount_bits - 1)) + 1),
      M_(amount_bits, sketch_size)
{
    if (amount_bits == 0) { throw std::invalid_argument("Amount of bits 'b' must be positive."); }

    std::fill(M_.begin(), M_.end(), r_min);
    update_treshold();
}

FastLogExpSketch::FastLogExpSketch(
    std::size_t sketch_size, 
    const std::vector<std::uint32_t>& seeds, 
    std::uint8_t amount_bits, 
    float logarithm_base,
    const std::vector<int>& registers
)
    : Sketch(sketch_size, seeds),
      fisher_yates(size),
      amount_bits_(amount_bits),
      logarithm_base(logarithm_base),
      r_max((1 << (amount_bits - 1)) - 1),
      r_min(-(1 << (amount_bits - 1)) + 1),
      M_(amount_bits, sketch_size)
{
    if (amount_bits == 0) { throw std::invalid_argument("Amount of bits 'b' must be positive."); }
    if (registers.size() != sketch_size) { throw std::invalid_argument("Invalid state: registers vector size mismatch"); }
    for (std::size_t i = 0; i < size; ++i) {
        M_[i] = registers[i];
    }
    update_treshold();
}


size_t FastLogExpSketch::memory_usage_total() const {
    size_t total_size = 0;
    total_size += sizeof(this->size); // 8
    total_size += seeds_.bytes(); // m * 4
    total_size += fisher_yates.bytes_total(); // 2m ceil(log_2 m)/8 + 8
    total_size += M_.bytes(); // mb/8
    total_size += sizeof(amount_bits_); // 1
    total_size += sizeof(r_max); // 4
    total_size += sizeof(r_min); // 4
    total_size += sizeof(logarithm_base); // 4
    total_size += sizeof(min_sketch_value); // 4
    total_size += sizeof(min_value_to_change_sketch); // 8
    return total_size; // 2m ceil(log_2 m)/8 + 4m + mb/8 + 41
}

size_t FastLogExpSketch::memory_usage_write() const {
    size_t write_size = 0;
    write_size += fisher_yates.bytes_write(); // m ceil(log_2 m)/8 + 8
    write_size += M_.bytes(); // mb/8
    write_size += sizeof(min_sketch_value); // 4
    write_size += sizeof(min_value_to_change_sketch); // 8
    return write_size; // m ceil(log_2 m)/8 + mb/8 + 20
}

size_t FastLogExpSketch::memory_usage_estimate() const {
    size_t estimate_size = M_.bytes(); // mb/8
    estimate_size += sizeof(logarithm_base); // 4
    return estimate_size; // mb/8 + 4
}

std::uint8_t FastLogExpSketch::get_amount_bits() const { return amount_bits_; }
float FastLogExpSketch::get_logarithm_base() const { return logarithm_base; }
std::vector<int> FastLogExpSketch::get_registers() const {
    return std::vector<int>(M_.begin(), M_.end());
}

void FastLogExpSketch::update_treshold(){
    this->min_sketch_value = *std::min_element(this->M_.begin(), this->M_.end());
    this->min_value_to_change_sketch = std::pow(logarithm_base, -this->min_sketch_value);
}

void FastLogExpSketch::add(const std::string& elem, double weight){ 
    double S = 0;
    bool touched_min = false; 

    fisher_yates.initialize(murmur64(elem, 1));
    for (size_t k = 0; k < this->size; ++k){
        std::uint64_t hashed = murmur64(elem, seeds_[k]); 
        double unit_interval_hash = to_unit_interval(hashed); 
        double exponential_variable = -std::log(unit_interval_hash) / weight; 
        S += exponential_variable/(double)(this->size-k); 

        if ( S >= this->min_value_to_change_sketch ) { break; } 

        auto j = fisher_yates.get_fisher_yates_element(k);
        int q = static_cast<int>(std::floor(-std::log(S)/std::log(logarithm_base)));

        q = std::min(q, r_max);
        if (q > this->M_[j]){
            if (this->M_[j] == min_sketch_value){
                touched_min = true;
            }
            this->M_[j] = q;
        }
    }

    if(touched_min){
        this->update_treshold();
    }
} 

double FastLogExpSketch::initialValue() const {
    double tmp_sum = 0.0;
    for(int r: M_) { 
        tmp_sum += std::pow(logarithm_base, -r);
    }
    return (double)(this->size-1) / tmp_sum;
}

double FastLogExpSketch::ffunc_divided_by_dffunc(double w) const {
    double ffunc = 0;
    double dffunc = 0;
    for (int r: M_) {
        double x = std::pow(logarithm_base, -r - 1);;
        double ex = std::exp(w * x);
        ffunc += x * (2.0 - ex) / (ex - 1.0);
        dffunc += -x * x * ex * pow(ex - 1, -2);
    }
    return ffunc / dffunc;
}

double FastLogExpSketch::Newton(double c0) const {
    double c1 = c0 - ffunc_divided_by_dffunc(c0);
    int it = 0;
    while (std::abs(c1 - c0) > NEWTON_MAX_ERROR) {
        c0 = c1;
        c1 = c0 - ffunc_divided_by_dffunc(c0);
        it += 1;
        if (it > NEWTON_MAX_ITERATIONS){ break; }
    }
    return c1;
}

double FastLogExpSketch::estimate() const {
    return Newton(initialValue());
}
