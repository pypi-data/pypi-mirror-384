#pragma once

#include "seeds.hpp"
#include <cstddef>
class Sketch { 
public:
    Sketch(
        std::size_t sketch_size, 
        const std::vector<std::uint32_t>& seeds
    ) : size(sketch_size), seeds_(seeds) {
        if (sketch_size == 0) { throw std::invalid_argument("Sketch size 'm' must be positive."); }
        if ((!seeds.empty() && seeds.size() != size)) { 
            throw std::invalid_argument("Seeds must have length m or 0"); 
        }
    }
    virtual ~Sketch() = default; 

    std::size_t get_sketch_size() const { return size; };
    std::vector<std::uint32_t> get_seeds() const { return seeds_.toVector(); };
    virtual void add(const std::string& elem, double weight = 1.0) = 0;
    virtual double estimate() const = 0;

    virtual size_t memory_usage_total() const = 0;
    virtual size_t memory_usage_write() const = 0;
    virtual size_t memory_usage_estimate() const = 0;

    void add_many(
        const std::vector<std::string>& elems,
        const std::vector<double>& weights
    ) {
        if (elems.size() != weights.size()){
            throw std::invalid_argument("add_many: elems and weights size mismatch");
        }
        for (std::size_t i = 0; i < elems.size(); ++i) {
            this->add(elems[i], weights[i]);
        }
    }

protected:
    std::size_t size;
    Seeds seeds_;
};
