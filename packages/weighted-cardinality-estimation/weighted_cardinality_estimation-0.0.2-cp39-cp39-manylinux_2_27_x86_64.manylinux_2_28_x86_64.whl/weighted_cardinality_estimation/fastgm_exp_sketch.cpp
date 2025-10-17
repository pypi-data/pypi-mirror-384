#include "fastgm_exp_sketch.hpp"
#include "fisher_yates.hpp"
#include "hash_util.hpp"
#include <cmath>
#include <cstdint>
#include"utils.hpp"

FastGMExpSketch::FastGMExpSketch(
    std::size_t sketch_size, 
    const std::vector<std::uint32_t>& seeds
):  Sketch(sketch_size, seeds),
    M_(std::vector<double>(sketch_size, -1)),
    fisher_yates(FisherYates(sketch_size)),
    j_star(1),
    k_star(sketch_size),
    flagFastPrune(false)
{
} 

FastGMExpSketch::FastGMExpSketch(
    std::size_t sketch_size, 
    const std::vector<std::uint32_t>& seeds, 
    const std::vector<double>& registers
):  Sketch(sketch_size, seeds),
    M_(registers),
    fisher_yates(FisherYates(sketch_size)),
    j_star(argmax(M_))
    {
        k_star = size;
        for(double elem: M_){
            if (elem >= 0){
                k_star--;
            }
        }
        flagFastPrune = k_star == 0;
    }

void FastGMExpSketch::add(const std::string& elem, double weight)
{ 
    // TODO: Get to know why in original paper there is s_vec
    double b = 0;
    fisher_yates.initialize(murmur64(elem, 1)); 

    for(uint32_t l = 1; l < size; ++l){
        std::uint64_t hashed = murmur64(elem, seeds_[l-1]); 
        double U = to_unit_interval(hashed); 
        b = b - ((1/weight)*(std::log(U)/(double)(size-l+1)));
        uint32_t c = fisher_yates.get_fisher_yates_element(l-1);

        if (!flagFastPrune){
            if (M_[c] < 0){
                M_[c] = b;
                k_star--;
                if(k_star == 0){ 
                    flagFastPrune = true;
                    j_star = argmax(M_);
                }
            } else if(b < M_[c]){
                M_[c] = b;
            }
        } else if (flagFastPrune) {
            if ( b > M_[j_star]){
                break;
            }
            if ( b < M_[c]){
                M_[c] = b;
                if ( c == j_star){
                    j_star = argmax(M_);
                }
            }
        }
    }
} 

size_t FastGMExpSketch::memory_usage_total() const {
    size_t total_size = 0;
    total_size += sizeof(this->size); // 8
    total_size += seeds_.bytes(); // m * 4
    total_size += fisher_yates.bytes_total(); // 2m ceil(log_2 m)/8 + 8
    total_size += M_.capacity() * sizeof(double); // 8m
    total_size += sizeof(k_star); // 4
    total_size += sizeof(j_star); // 4
    total_size += sizeof(flagFastPrune); // 1
    return total_size;  // 2m*ceil(log_2 m)/8 + 12m + 25
}

size_t FastGMExpSketch::memory_usage_write() const {
    size_t total_size = 0;
    total_size += fisher_yates.bytes_write(); // m ceil(log_2 m)/8 + 8
    total_size += M_.capacity() * sizeof(double); // 8m
    total_size += sizeof(k_star); // 4
    total_size += sizeof(j_star); // 4
    total_size += sizeof(flagFastPrune); // 1
    return total_size; // m ceil(log_2 m)/8 + 8m + 17
}

size_t FastGMExpSketch::memory_usage_estimate() const {
    size_t estimate_size = M_.capacity() * sizeof(double); // 8m
    return estimate_size; // 8m
}

double FastGMExpSketch::estimate() const {
    double total = 0.0;
    for (double value : M_) { total += value; }
    return ((double)this->size - 1.0) / total;
}

double FastGMExpSketch::jaccard_struct(const FastGMExpSketch& other) const {
    if (other.size != size) { return 0.0; }
    std::size_t equal = 0;
    for (std::size_t i = 0; i < size; ++i) {
        if (M_[i] == other.M_[i]) { ++equal; }
    }
    return static_cast<double>(equal) / static_cast<double>(size);
}


const std::vector<double>& FastGMExpSketch::get_registers() const {
    return M_;
}
