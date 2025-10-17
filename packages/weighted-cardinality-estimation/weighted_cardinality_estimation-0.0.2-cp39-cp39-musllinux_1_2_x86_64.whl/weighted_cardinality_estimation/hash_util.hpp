#pragma once
#include <cstdint>
#include <limits>
#include <string>
#include "MurmurHash3.h"



inline std::uint64_t murmur64(
    const std::string& key, 
    std::uint32_t seed
)
{
    std::uint64_t hash_answer[2];
    MurmurHash3_x64_128(key.data(),
                        static_cast<int>(key.size()),
                        seed,
                        hash_answer);
    return hash_answer[0];                              // pierwsze 64 bity
}

inline double to_unit_interval(std::uint64_t num)
{
    static const double MAX_UINT64 = static_cast<double>(std::numeric_limits<std::uint64_t>::max());
    return static_cast<double>(num + 1ULL) / MAX_UINT64;
}
