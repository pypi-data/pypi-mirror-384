#include "q_sketch_dyn.hpp"
#include <stdexcept>
#include <cmath>
#include "hash_util.hpp"

QSketchDyn::QSketchDyn(std::size_t sketch_size, const std::vector<std::uint32_t>& seeds, std::uint8_t amount_bits, std::uint32_t g_seed)
    : Sketch(sketch_size, seeds),
      amount_bits_(amount_bits),
      r_min(-(1 << (amount_bits - 1))),
      r_max((1 << (amount_bits - 1)) - 1),
      g_seed_(g_seed),
      cardinality_(0.0),
      q_r_(0.0),
      R_(amount_bits, sketch_size),
      T_(std::ceil(std::log2(sketch_size)), 1 << amount_bits)
{
    if (amount_bits == 0) { throw std::invalid_argument("Amount of bits 'b' must be positive."); }
    for(size_t i = 0; i < T_.size(); i++ ){
        T_[i] = 0;
    }
    T_[0] = sketch_size;
    for (std::size_t i = 0; i < size; ++i) {
        R_[i] = r_min;
    }
}

QSketchDyn::QSketchDyn(
    std::size_t sketch_size, std::uint8_t amount_bits, std::uint32_t g_seed,
    const std::vector<std::uint32_t>& seeds, const std::vector<int>& registers,
    const std::vector<std::uint32_t>& t_histogram, double cardinality)
    : Sketch(sketch_size, seeds),
      amount_bits_(amount_bits),
      r_min(-(1 << (amount_bits - 1))),
      r_max((1 << (amount_bits - 1)) - 1),
      g_seed_(g_seed),
      cardinality_(cardinality),
      q_r_(0.0),
      R_(amount_bits, sketch_size),
      T_(std::ceil(std::log2(sketch_size)), 1 << amount_bits)
{
    if (amount_bits == 0) { throw std::invalid_argument("Amount of bits 'b' must be positive."); }
    for(std::size_t i = 0; i < t_histogram.size(); ++i){
        T_[i] = t_histogram[i];
    }
    for (std::size_t i = 0; i < size; ++i) {
        R_[i] = registers[i];
    }
}

void QSketchDyn::add(const std::string& elem, double weight) {
    // std::cout << " ?" << '\n';
    const uint64_t g_hash = murmur64(elem, g_seed_);
    const size_t j = g_hash % size;

    const uint64_t u_hash = murmur64(elem, seeds_[j]);
    const double u = to_unit_interval(u_hash);
    if (u == 0.0) { return; }
    const double r = -std::log(u) / weight;
    const int y = static_cast<int>(std::floor(-std::log2(r)));

    if (y <= R_[j]) {
        return;
    }

    const int old_r_val = R_[j];
    const int new_r_val = std::min(y, r_max);

    const size_t old_t_idx = std::max(0, old_r_val - r_min);
    const size_t new_t_idx = std::max(0, new_r_val - r_min);
    
    if (old_t_idx < T_.size() && T_[old_t_idx] > 0) {
        T_[old_t_idx] = T_[old_t_idx] - 1;
    }
    if (new_t_idx < T_.size()) {
        T_[new_t_idx] = T_[new_t_idx] + 1;
    }
    R_[j] = new_r_val;

    double q_val_sum = 0.0;
    for (size_t k = 0; k < T_.size(); ++k) {
        if (T_[k] > 0) {
            double exponent = -((double)k + r_min + 1.0);
            double exp2_val = std::ldexp(1.0, static_cast<int>(exponent));
            double rate = std::exp(-weight * exp2_val);
            q_val_sum += static_cast<double>(T_[k]) * rate;
        }
    }

    this->q_r_ = 1.0 - (q_val_sum / (double)size);
    cardinality_ += weight / this->q_r_;
}

double QSketchDyn::estimate() const {
    return cardinality_;
}

std::uint8_t QSketchDyn::get_amount_bits() const { return amount_bits_; }
std::uint32_t QSketchDyn::get_g_seed() const { return g_seed_; }
std::vector<int> QSketchDyn::get_registers() const {
    return std::vector<int>(R_.begin(), R_.end());
}
std::vector<std::uint32_t> QSketchDyn::get_t_histogram() const { 
    return std::vector<std::uint32_t>(T_.begin(), T_.end()); 
}
double QSketchDyn::get_cardinality() const { return cardinality_; }

size_t QSketchDyn::memory_usage_total() const {
    size_t total_size = 0;
    total_size += sizeof(this->size); // 8
    total_size += seeds_.bytes(); // m * 4
    total_size += R_.bytes(); // mb/8
    total_size += T_.bytes(); // 2**b * ceil(log_2 m)/8
    total_size += sizeof(amount_bits_); // 1
    total_size += sizeof(r_min); // 4 
    total_size += sizeof(r_max); // 4
    total_size += sizeof(g_seed_); // 4
    total_size += sizeof(cardinality_); // 8
    total_size += sizeof(q_r_); // 8
    return total_size; // 2**b * ceil(log_2 m)/8 + m * 4 + mb/8 + 37 
}

size_t QSketchDyn::memory_usage_write() const {
    size_t write_size = 0;
    write_size += R_.bytes(); // mb/8
    write_size += T_.bytes(); // 2**b * ceil(log_2 m)/8
    write_size += sizeof(cardinality_); // 8
    write_size += sizeof(q_r_); // 8
    return write_size; // 2**b * ceil(log_2 m)/8 + mb/8 + 16
}

size_t QSketchDyn::memory_usage_estimate() const {
    return R_.bytes() + T_.bytes(); // 2**b * ceil(log_2 m)/8 + mb/8
}
