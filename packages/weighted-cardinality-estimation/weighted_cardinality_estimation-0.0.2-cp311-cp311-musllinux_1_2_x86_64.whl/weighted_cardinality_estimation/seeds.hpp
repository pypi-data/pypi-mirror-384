#pragma once
#include <compact_vector.hpp>
#include <cstdint>
#include <vector>
class Seeds {
public:
    Seeds(const std::vector<std::uint32_t>& seeds); // this will be returning from list
    Seeds(); // this will be whenever seeds should just return value of index
    std::uint32_t get(uint32_t index) const; 
    std::uint32_t bytes() const;
    std::uint32_t operator[](uint32_t index) const;
    std::vector<std::uint32_t> toVector() const;
private:
    std::vector<uint32_t> seeds_;
    static bool is_sequential_from_one(const std::vector<std::uint32_t>& vec);
    static std::vector<uint32_t> create_seeds_vector(const std::vector<std::uint32_t>& seeds);
};
