#include "q_sketch.hpp"
#include <algorithm>
#include <cmath>
#include <stdexcept>
#include "hash_util.hpp"
#include<cstring>
#include "utils.hpp"

QSketch::QSketch(std::size_t sketch_size, const std::vector<std::uint32_t>& seeds, uint8_t amount_bits)
    : Sketch(sketch_size, seeds),
      fisher_yates(size),
      amount_bits_(amount_bits),
      r_max((1 << (amount_bits - 1)) - 1),
      r_min(-(1 << (amount_bits - 1)) + 1),
      M_(amount_bits, sketch_size),
      j_star(0)
{
    if (amount_bits == 0) { throw std::invalid_argument("Amount of bits 'b' must be positive."); }
    for (std::size_t i = 0; i < size; ++i) {
        M_[i] = r_min;
    }
}

QSketch::QSketch(std::size_t sketch_size, const std::vector<std::uint32_t>& seeds, std::uint8_t amount_bits, const std::vector<int>& registers)
    : Sketch(sketch_size, seeds),
      fisher_yates(size),
      amount_bits_(amount_bits),
      r_max((1 << (amount_bits - 1)) - 1),
      r_min(-(1 << (amount_bits - 1)) + 1),
      M_(amount_bits, sketch_size),
      j_star(argmin(registers))
{
    if (amount_bits == 0) { throw std::invalid_argument("Amount of bits 'b' must be positive."); }
    if (registers.size() != sketch_size) { throw std::invalid_argument("Invalid state: registers vector size mismatch"); }
    for (std::size_t i = 0; i < size; ++i) {
        M_[i] = registers[i];
    }
}


size_t QSketch::memory_usage_total() const {
    size_t total_size = 0;
    total_size += sizeof(this->size); // 8
    total_size += seeds_.bytes(); // m * 4
    total_size += fisher_yates.bytes_total(); // 2m ceil(log_2 m)/8 + 8
    total_size += M_.bytes(); // mb/8
    total_size += sizeof(amount_bits_); // 1
    total_size += sizeof(r_max); // 4
    total_size += sizeof(r_min); // 4
    total_size += sizeof(j_star); // 4
    return total_size; // 2m ceil(log_2 m)/8 + 4m + Smb/8 + 29
}

size_t QSketch::memory_usage_write() const {
    size_t write_size = 0;
    write_size += fisher_yates.bytes_write(); // m ceil(log_2 m)/8 + 8
    write_size += M_.bytes(); // mb/8
    write_size += sizeof(j_star); // 4
    return write_size; // m ceil(log_2 m)/8 + mb/8 + 12
}

size_t QSketch::memory_usage_estimate() const {
    size_t estimate_size = M_.bytes(); // mb/8
    return estimate_size; // mb/8
}

std::uint8_t QSketch::get_amount_bits() const { return amount_bits_; }
std::vector<int> QSketch::get_registers() const {
    return std::vector<int>(M_.begin(), M_.end());
}

void QSketch::add(const std::string& elem, double weight){ 
    double r = 0;

    fisher_yates.initialize(murmur64(elem, 1));
    for (size_t k = 0; k < this->size; ++k){
        std::uint64_t hashed = murmur64(elem, seeds_[k]); 
        double unit_interval_hash = to_unit_interval(hashed); 
        r -= (std::log(unit_interval_hash) / (weight*(double)(size - k))); 
        int y = static_cast<int>(std::floor(-std::log2(r)));

        if ( y <= M_[j_star] ) { break; } 

        auto j = fisher_yates.get_fisher_yates_element(k);

        if (y > this->M_[j]){
            M_[j] = std::min(std::max(y, r_min), r_max);
            if (j == j_star){
                j_star = argmin(M_);
            }
        }
    }

} 

double QSketch::initialValue() const {
    double tmp_sum = 0.0;
    for(int r: M_) { 
        tmp_sum += std::ldexp(1.0, -r);
    }
    return (double)(this->size-1) / tmp_sum;
}

double QSketch::ffunc_divided_by_dffunc(double w) const {
    double ffunc = 0;
    double dffunc = 0;
    for (int r: M_) {
        double x = std::ldexp(1.0, -r - 1);
        double ex = std::exp(w * x);
        ffunc += x * (2.0 - ex) / (ex - 1.0);
        dffunc += -x * x * ex * pow(ex - 1, -2);
    }
    return ffunc / dffunc;
}

double QSketch::Newton(double c0) const {
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

double QSketch::estimate() const {
    return Newton(initialValue());
}
