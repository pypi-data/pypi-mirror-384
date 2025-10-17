#include "exp_sketch.hpp"
#include <algorithm>
#include <cmath>
#include <limits>
#include "hash_util.hpp"

ExpSketch::ExpSketch(std::size_t sketch_size, const std::vector<std::uint32_t>& seeds)
    : Sketch(sketch_size, seeds),
      M_(sketch_size, std::numeric_limits<double>::infinity())
{}

ExpSketch::ExpSketch(std::size_t sketch_size, const std::vector<std::uint32_t>& seeds, const std::vector<double>& registers)
    : Sketch(sketch_size, seeds), M_(registers)
{}

void ExpSketch::add(const std::string& elem, double weight)
{ 
    for (std::size_t i = 0; i < size; ++i) {
        std::uint64_t h = murmur64(elem, seeds_[i]);
        double u = to_unit_interval(h);   
        double g = -std::log(u) / weight;
        M_[i] = std::min(g, M_[i]);
    }
} 

size_t ExpSketch::memory_usage_total() const {
    size_t total_size = 0;
    total_size += sizeof(size); // <int>
    total_size += seeds_.bytes(); // m * 4
    total_size += M_.capacity() * sizeof(double); // <double> * m
    return total_size; // 12m + 4
}

size_t ExpSketch::memory_usage_write() const {
    size_t total_size =  M_.capacity() * sizeof(double); // <double> * m
    return total_size; // 8m
}

size_t ExpSketch::memory_usage_estimate() const {
    size_t estimate_size = M_.capacity() * sizeof(double); // <double> * m
    return estimate_size; // 8m
}

double ExpSketch::estimate() const
{
    double total = 0.0;
    for (double value : M_) { total += value; }
    return ((double)this->size - 1.0) / total;
}

double ExpSketch::jaccard_struct(const ExpSketch& other) const
{
    if (other.size != size) { return 0.0; }
    std::size_t equal = 0;
    for (std::size_t i = 0; i < size; ++i) {
        if (M_[i] == other.M_[i]) { ++equal; }
    }
    return static_cast<double>(equal) / static_cast<double>(size);
}

const std::vector<double>& ExpSketch::get_registers() const {
    return M_;
}
