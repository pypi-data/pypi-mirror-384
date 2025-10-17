#include <compact_vector.hpp>
#include <vector>
#include <iostream>
#include <cstdint>
#include<numeric>


void print_vector(std::vector<int> vec){
    std::cout << "vec:[";
    for(size_t i = 0; i < vec.size();i++){
        std::cout << vec[i] << ", ";
    }
    std::cout << "]\n";
}

void print_vector(std::vector<std::uint32_t> vec){
    std::cout << "vec:[";
    for(size_t i = 0; i < vec.size();i++){
        std::cout << vec[i] << ", ";
    }
    std::cout << "]\n";
}

std::vector<uint32_t> range(uint32_t min, uint32_t max){
    std::vector<std::uint32_t> vec(max - min + 1);
    std::iota(vec.begin(), vec.end(), min); 
    return vec;
}

std::uint32_t argmax(std::vector<double> vec){
    double max = vec[0];
    uint32_t argmax = 0;
    for(uint32_t j = 1; j < vec.size(); j++){
        if (vec[j] > max){
            argmax = j;
            max = vec[j];
        }
    }
    return argmax;
}

std::uint32_t argmin(std::vector<int> vec){
    int min = vec[0];
    uint32_t argmin = 0;
    for(uint32_t j = 1; j < vec.size(); j++){
        if (vec[j] < min){
            argmin = j;
            min = vec[j];
        }
    }
    return argmin;
}

std::uint32_t argmin(compact::vector<int> vec){
    int min = vec[0];
    uint32_t argmin = 0;
    for(uint32_t j = 1; j < vec.size(); j++){
        if (vec[j] < min){
            argmin = j;
            min = vec[j];
        }
    }
    return argmin;
}