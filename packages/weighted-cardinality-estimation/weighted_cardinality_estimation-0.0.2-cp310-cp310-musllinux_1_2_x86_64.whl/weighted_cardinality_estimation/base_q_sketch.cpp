#include "base_q_sketch.hpp"
#include <algorithm>
#include <cmath>
#include <stdexcept>
#include "hash_util.hpp"
#include "compact_vector.hpp"
#include "utils.hpp"

BaseQSketch::BaseQSketch(
    std::size_t sketch_size, 
    const std::vector<std::uint32_t>& seeds, 
    uint8_t amount_bits
): Sketch(sketch_size, seeds),
      amount_bits_(amount_bits),
      r_max((1 << (amount_bits - 1)) - 1),
      r_min(-(1 << (amount_bits - 1)) + 1),
      M_(amount_bits, sketch_size)
{
    if (amount_bits == 0) { throw std::invalid_argument("Amount of bits 'b' must be positive."); }
    for (std::size_t i = 0; i < size; ++i) {
        M_[i] = r_min;
    }
}

BaseQSketch::BaseQSketch(
    std::size_t sketch_size, 
    const std::vector<std::uint32_t>& seeds, 
    std::uint8_t amount_bits, 
    const std::vector<int>& registers
):  Sketch(sketch_size, seeds),
    amount_bits_(amount_bits),
    r_max((1 << (amount_bits - 1)) - 1),
    r_min(-(1 << (amount_bits - 1)) + 1),
    M_(amount_bits, sketch_size)
{
    if (amount_bits == 0) { throw std::invalid_argument("Amount of bits 'b' must be positive."); }
    for (std::size_t i = 0; i < size; ++i) {
        M_[i] = registers[i];
    }
}

void BaseQSketch::add(const std::string& elem, double weight)
{ 
    for (std::size_t i = 0; i < size; ++i) {
        std::uint64_t h = murmur64(elem, seeds_[i]);
        double u = to_unit_interval(h);   
        double g = -std::log(u) / weight;
        int q = static_cast<int>(std::floor(-std::log2(g)));
        q = std::min(q, r_max);
        if (q > M_[i]){
            M_[i] = q;
        }
    }
} 

size_t BaseQSketch::memory_usage_total() const {
    size_t total_size = 0;
    total_size += sizeof(size); // 8
    total_size += seeds_.bytes(); // m * 4
    total_size += M_.bytes(); // mb / 8
    total_size += sizeof(r_min); // 4
    total_size += sizeof(r_max); // 4
    total_size += sizeof(amount_bits_); // 1
    return total_size; // m * 4 + mb / 8 + 17
}

size_t BaseQSketch::memory_usage_write() const {
    return M_.bytes(); // mb / 8
}

size_t BaseQSketch::memory_usage_estimate() const {
    return M_.bytes(); // mb / 8
}

std::vector<int> BaseQSketch::get_registers() const {
    return std::vector<int>(M_.begin(), M_.end());
}

std::uint8_t BaseQSketch::get_amount_bits() const {
    return amount_bits_;
}

double BaseQSketch::initialValue() const {
    double tmp_sum = 0.0;
    for(int r: M_) { 
        tmp_sum += std::ldexp(1.0, -r);
    }
    return (double)(this->size-1) / tmp_sum;
}

double BaseQSketch::ffunc_divided_by_dffunc(double w) const {
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

double BaseQSketch::Newton(double c0) const {
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

double BaseQSketch::estimate() const {
    return Newton(initialValue());
}
