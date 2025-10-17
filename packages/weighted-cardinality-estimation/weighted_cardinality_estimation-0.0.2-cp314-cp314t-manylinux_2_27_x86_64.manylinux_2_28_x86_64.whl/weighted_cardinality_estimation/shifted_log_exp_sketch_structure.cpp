#include "shifted_log_exp_sketch_structure.hpp"
#include "utils.hpp"
#include <cmath>
#include <stdexcept>

ShiftedLogExpSketchStructure::ShiftedLogExpSketchStructure(
    std::uint8_t amount_bits,
    std::size_t sketch_size
) : r_max((1 << amount_bits) - 1),
    offset(-(1 << (amount_bits - 1)) + 1),
    M_(amount_bits, sketch_size) {
    
    std::fill(M_.begin(), M_.end(), 0);  
}

ShiftedLogExpSketchStructure::ShiftedLogExpSketchStructure(
    std::uint8_t amount_bits,
    std::size_t sketch_size,
    std::int32_t offset,
    const std::vector<std::uint32_t>& registers
) : r_max((1 << amount_bits) - 1),
    offset(offset),
    M_(amount_bits, sketch_size) {

    if (registers.size() != sketch_size) { throw std::invalid_argument("Invalid state: registers vector size mismatch"); }
    
    for(size_t i = 0; i < M_.size(); i++){
        M_[i] = registers[i];
    }
}

std::int32_t ShiftedLogExpSketchStructure::get_offset() const {
    return offset;
}

std::vector<uint32_t> ShiftedLogExpSketchStructure::get_registers() const {
    return std::vector<std::uint32_t>(M_.begin(), M_.end());
}

double ShiftedLogExpSketchStructure::initialValue(float logarithm_base) const {
    double tmp_sum = 0.0;
    for(std::uint32_t r: M_) { 
        tmp_sum += std::pow(logarithm_base, -(int)(r+offset));
    }
    return (double)(this->M_.size()-1) / tmp_sum;
}

double ShiftedLogExpSketchStructure::ffunc_divided_by_dffunc(double w, float logarithm_base) const {
    double ffunc = 0;
    double dffunc = 0;
    for (std::uint32_t r: M_) {
        double x = std::pow(logarithm_base, -(int)(r+offset) - 1);;
        double ex = std::exp(w * x);
        ffunc += x * (2.0 - ex) / (ex - 1.0);
        dffunc += -x * x * ex * pow(ex - 1, -2);
    }
    return ffunc / dffunc;
}

double ShiftedLogExpSketchStructure::Newton(double c0, float logarithm_base) const {
    double c1 = c0 - ffunc_divided_by_dffunc(c0, logarithm_base);
    int it = 0;
    while (std::abs(c1 - c0) > NEWTON_MAX_ERROR) {
        c0 = c1;
        c1 = c0 - ffunc_divided_by_dffunc(c0, logarithm_base);
        it += 1;
        if (it > NEWTON_MAX_ITERATIONS){ break; }
    }
    return c1;
}

double ShiftedLogExpSketchStructure::estimate(float logarithm_base) const {
    return Newton(initialValue(logarithm_base), logarithm_base);
}

size_t ShiftedLogExpSketchStructure::memory_usage_total() const {
    size_t total_size = 0;
    total_size += sizeof(r_max); // 4
    total_size += sizeof(offset); // 4
    total_size += M_.bytes(); // mb/8 
    return total_size; // mb/8 + 8
}

size_t ShiftedLogExpSketchStructure::memory_usage_write() const {
    size_t write_size = 0;
    write_size += M_.bytes(); // mb/8
    return write_size; // mb/8
}

size_t ShiftedLogExpSketchStructure::memory_usage_estimate() const {
    size_t estimate_size = M_.bytes(); // mb/8
    estimate_size += sizeof(offset); // <int> 4
    return estimate_size; // mb/8 + 4
}

std::uint32_t ShiftedLogExpSketchStructure::operator[](std::uint32_t index) const{
    return M_[index];
}

void ShiftedLogExpSketchStructure::decrease_structure_by(uint32_t value){
    for (std::size_t j = 0; j < M_.size(); j++) {
        if (M_[j] >= value) {
            M_[j] = M_[j] - value;
        } else {
            M_[j] = 0;
        }
    }
}

void ShiftedLogExpSketchStructure::set(uint32_t index, uint32_t value){
        if (value > r_max) {
            // handling overflow here :) 
            std::uint32_t increase_offset = value - r_max; // this is safe.
            this->decrease_structure_by(increase_offset);
            offset += (int)increase_offset; // theoretically it's not safe but who cares :)
            M_[index] = r_max;
        } 
        else {
            M_[index] = value;
        }
    }

std::uint32_t ShiftedLogExpSketchStructure::min() const {
    return *std::min_element(M_.begin(), M_.end());
}
