#pragma once
#include <compact_vector.hpp>
#include <cstdint>
#include <vector>
class ShiftedLogExpSketchStructure {
public:
    ShiftedLogExpSketchStructure(
        std::uint8_t amount_bits,
        std::size_t sketch_size
    );
    ShiftedLogExpSketchStructure(
        std::uint8_t amount_bits,
        std::size_t sketch_size,
        std::int32_t offset,
        const std::vector<std::uint32_t>& registers
    );

    void set(uint32_t index, uint32_t value);

    std::uint32_t operator[](std::uint32_t index) const;
    [[nodiscard]] double estimate(float logarithm_base) const;
    std::int32_t get_offset() const;
    std::vector<uint32_t> get_registers() const;
    std::uint32_t min() const;

    [[nodiscard]] size_t memory_usage_total() const;
    [[nodiscard]] size_t memory_usage_write() const;
    [[nodiscard]] size_t memory_usage_estimate() const;
private:
    double initialValue(float logarithm_base) const;
    double ffunc_divided_by_dffunc(double w, float logarithm_base) const;
    double Newton(double c0, float logarithm_base) const;
    void decrease_structure_by(uint32_t value);

    std::uint32_t r_max; // maximum possible value of register (0 to 2**amount_bits-1)
    std::int32_t offset; // this is a relative value for all registers. real_value = value + offset
    compact::vector<uint32_t> M_; // sketch structure with elements between < r_min ... r_max >
};