#pragma once
#include <compact_vector.hpp>
#include <cstdint>
#include <random>

class FisherYates {
public:
    FisherYates(std::uint32_t sketch_size);

    void initialize(std::uint64_t rng_seed); // this function will set new rng_seed and permWork = permInit
    uint32_t get_fisher_yates_element(uint32_t index);

    std::uint32_t bytes_write() const ;
    std::uint32_t bytes_total() const ;
private:
    std::mt19937_64 rng_engine;
    uint32_t rand(uint32_t min, uint32_t max);
    compact::vector<uint32_t> permInit; // static structure, only used to fast copy to permWork
    compact::vector<uint32_t> permWork; // used at the beginning of every update
};
