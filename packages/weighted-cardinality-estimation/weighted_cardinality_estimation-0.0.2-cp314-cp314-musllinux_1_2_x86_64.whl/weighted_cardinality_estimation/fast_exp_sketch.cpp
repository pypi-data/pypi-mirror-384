#include "fast_exp_sketch.hpp"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include "hash_util.hpp"
#include <cstring>

FastExpSketch::FastExpSketch(
    std::size_t sketch_size, 
    const std::vector<std::uint32_t>& seeds
):    Sketch(sketch_size, seeds),
      M_(sketch_size, std::numeric_limits<double>::infinity()),
      fisher_yates(sketch_size),
      max(std::numeric_limits<double>::infinity())
{
}
FastExpSketch::FastExpSketch(
    std::size_t sketch_size,
    const std::vector<std::uint32_t>& seeds,
    const std::vector<double>& registers)
:   Sketch(sketch_size, seeds),
    M_(registers),
    fisher_yates(sketch_size)
{
    max = *std::max_element(M_.begin(), M_.end());
}


void FastExpSketch::add(const std::string& elem, double weight)
{ 
    double S = 0;
    bool updateMax = false; 

    fisher_yates.initialize(murmur64(elem, 1)); 
    for (size_t k = 0; k < this->size; ++k){
        std::uint64_t hashed = murmur64(elem, seeds_[k]); 
        double U = to_unit_interval(hashed); 
        double E = -std::log(U) / weight; 

        S += E/(double)(this->size-k); 
        if ( S >= this->max ) { break; }

        std::uint32_t j = fisher_yates.get_fisher_yates_element(k);

        if (this->M_[j] == this->max ) { updateMax = true; }
        this->M_[j] = std::min(this->M_[j], S);
    }

    if(updateMax){
        this->max = *std::max_element(this->M_.begin(), this->M_.end());
    }
} 

size_t FastExpSketch::memory_usage_total() const {
    size_t total_size = 0;
    total_size += sizeof(this->size); // 8
    total_size += seeds_.bytes(); // m * 4
    total_size += fisher_yates.bytes_total(); // 2m ceil(log_2 m)/8 + 8
    total_size += M_.capacity() * sizeof(double); // 8m
    total_size += sizeof(max); // 8
    return total_size; // 2m ceil(log_2 m)/8 + 12m + 24
}

size_t FastExpSketch::memory_usage_write() const {
    size_t write_size = 0;
    write_size += fisher_yates.bytes_write(); // m ceil(log_2 m)/8 + 8
    write_size += M_.capacity() * sizeof(double); // 8m
    write_size += sizeof(max); // 8
    return write_size; // m ceil(log_2 m)/8 + 8m + 16
}

size_t FastExpSketch::memory_usage_estimate() const {
    size_t estimate_size = M_.capacity() * sizeof(double); // 8m
    return estimate_size; // 8m
}


double FastExpSketch::estimate() const
{
    double total = 0.0;
    for (double val : M_) { total += val;}
    return ((double)this->size - 1.0) / total;
}

double FastExpSketch::jaccard_struct(const FastExpSketch& other) const
{
    if (other.size != this->size) { return 0.0; }
    std::size_t equal = 0;
    for (std::size_t i = 0; i < this->size; ++i) {
        if (M_[i] == other.M_[i]) { ++equal; } 
    }
    return static_cast<double>(equal) / static_cast<double>(this->size);
}

const std::vector<double>& FastExpSketch::get_registers() const { return M_; }
