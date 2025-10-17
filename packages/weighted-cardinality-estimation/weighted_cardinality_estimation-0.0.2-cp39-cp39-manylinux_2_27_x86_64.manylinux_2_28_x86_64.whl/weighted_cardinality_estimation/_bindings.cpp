#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "base_log_exp_sketch.hpp"
#include "base_q_sketch.hpp"
#include "exp_sketch.hpp"
#include "fast_exp_sketch.hpp"
#include "fast_q_sketch.hpp"
#include "fastgm_exp_sketch.hpp"
#include "q_sketch_dyn.hpp"
#include "q_sketch.hpp"
#include "fast_log_exp_sketch.hpp"
#include "base_shifted_log_exp_sketch.hpp"
#include "fast_shifted_log_exp_sketch.hpp"

namespace py = pybind11;

template <typename SketchType>
void bind_common_sketch_methods(py::class_<SketchType>& cls) {
    cls.def("add", &SketchType::add, py::arg("x"), py::arg("weight") = 1.0)
       .def("add_many", &SketchType::add_many, py::arg("elems"), py::arg("weights"))
       .def("estimate", &SketchType::estimate)
       .def("memory_usage_total", &SketchType::memory_usage_total)
       .def("memory_usage_write", &SketchType::memory_usage_write)
       .def("memory_usage_estimate", &SketchType::memory_usage_estimate);
}

PYBIND11_MODULE(_core, m) {
    auto exp_sketch = py::class_<ExpSketch>(m, "ExpSketch")
        .def(py::init<std::size_t, const std::vector<std::uint32_t>&>(),
             py::arg("m"), py::arg("seeds"))
        .def("jaccard_struct", &ExpSketch::jaccard_struct)
        .def(py::pickle(
            [](const ExpSketch &p) {return py::make_tuple(p.get_sketch_size(), p.get_seeds(), p.get_registers());},
            [](const py::tuple& t) {
                if (t.size() != 3) {
                    throw std::runtime_error("Invalid state for ExpSketch pickle!");
                }
                return ExpSketch( 
                    t[0].cast<std::size_t>(),
                    t[1].cast<std::vector<std::uint32_t>>(),
                    t[2].cast<std::vector<double>>()
                );
            }
        ));
    bind_common_sketch_methods(exp_sketch);
 
    auto fast_exp_sketch = py::class_<FastExpSketch>(m, "FastExpSketch")
        .def(py::init<std::size_t, const std::vector<std::uint32_t>&>())
        .def("jaccard_struct", &FastExpSketch::jaccard_struct)
        .def(py::pickle(
    [](const FastExpSketch &p) {
        return py::make_tuple(
            p.get_sketch_size(),
            p.get_seeds(),
            p.get_registers()
        );
    },
    [](const py::tuple& t) {
        if (t.size() != 3) {
            throw std::runtime_error("Invalid state for FastExpSketch pickle!");
        }
        return FastExpSketch(
            t[0].cast<std::size_t>(),
            t[1].cast<std::vector<std::uint32_t>>(),
            t[2].cast<std::vector<double>>()
        );
    }
    ));
    bind_common_sketch_methods(fast_exp_sketch);

    auto fastgm_exp_sketch = py::class_<FastGMExpSketch>(m, "FastGMExpSketch")
        .def(py::init<std::size_t, const std::vector<std::uint32_t>&>())
        .def("jaccard_struct", &FastGMExpSketch::jaccard_struct)
        .def(py::pickle(
    [](const FastGMExpSketch &p) {
        return py::make_tuple(
            p.get_sketch_size(),
            p.get_seeds(),
            p.get_registers()
        );
    },
    [](const py::tuple& t) {
        if (t.size() != 3) {
            throw std::runtime_error("Invalid state for FastGMExpSketch pickle!");
        }
        return FastGMExpSketch(
            t[0].cast<std::size_t>(),
            t[1].cast<std::vector<std::uint32_t>>(),
            t[2].cast<std::vector<double>>()
        );
    }
    ));
    bind_common_sketch_methods(fastgm_exp_sketch);

    auto fast_q_sketch = py::class_<FastQSketch>(m, "FastQSketch")
        .def(py::init<std::size_t, const std::vector<std::uint32_t>&, std::uint8_t>(),
            py::arg("m"), py::arg("seeds"), py::arg("amount_bits"))
        .def(py::pickle(
        [](const FastQSketch &p) {
            return py::make_tuple(
                p.get_sketch_size(),
                p.get_seeds(),
                p.get_amount_bits(),
                p.get_registers()
            );
        },
        [](const py::tuple& t) {
            if (t.size() != 4) {
                throw std::runtime_error("Invalid state for FastQSketch pickle!");
            }
            return FastQSketch(
                t[0].cast<std::size_t>(),
                t[1].cast<std::vector<std::uint32_t>>(),
                t[2].cast<std::uint8_t>(),
                t[3].cast<std::vector<int>>()
            );
        }
    ));;
    bind_common_sketch_methods(fast_q_sketch);

    auto qsketchdyn = py::class_<QSketchDyn>(m, "QSketchDyn")
    .def(py::init<std::size_t, const std::vector<std::uint32_t>&, std::uint8_t, std::uint32_t>(),
            py::arg("m"), py::arg("seeds"), py::arg("amount_bits"), py::arg("g_seed") = 42)
    .def(py::pickle(
        [](const QSketchDyn &p) {
            return py::make_tuple(
                p.get_sketch_size(),
                p.get_amount_bits(),
                p.get_g_seed(),
                p.get_seeds(),
                p.get_registers(),
                p.get_t_histogram(),
                p.get_cardinality()
            );
        },
        [](const py::tuple &t) {
            if (t.size() != 7) { throw std::runtime_error("Invalid state for QSketchDyn pickle!"); }
            return QSketchDyn(
                t[0].cast<std::size_t>(),
                t[1].cast<std::uint8_t>(),
                t[2].cast<std::uint32_t>(),
                t[3].cast<std::vector<std::uint32_t>>(),
                t[4].cast<std::vector<int>>(),
                t[5].cast<std::vector<std::uint32_t>>(),
                t[6].cast<double>()
            );
        }
    ));
    bind_common_sketch_methods(qsketchdyn);

    auto baseqsketch = py::class_<BaseQSketch>(m, "BaseQSketch")
        .def(py::init<std::size_t, const std::vector<std::uint32_t>&, std::uint8_t>(),
            py::arg("m"), py::arg("seeds"), py::arg("amount_bits"))
        .def(py::pickle(
        [](const BaseQSketch &p) {
            return py::make_tuple(
                p.get_sketch_size(),
                p.get_seeds(),
                p.get_amount_bits(),
                p.get_registers()
            );
        },
        [](const py::tuple& t) {
            if (t.size() != 4) {
                throw std::runtime_error("Invalid state for BaseQSketch pickle!");
            }
            return BaseQSketch(
                t[0].cast<std::size_t>(),
                t[1].cast<std::vector<std::uint32_t>>(),
                t[2].cast<std::uint8_t>(),
                t[3].cast<std::vector<int>>()
            );
        }
    ));
    bind_common_sketch_methods(baseqsketch);

    auto qsketch = py::class_<QSketch>(m, "QSketch")
        .def(py::init<std::size_t, const std::vector<std::uint32_t>&, std::uint8_t>(),
            py::arg("m"), py::arg("seeds"), py::arg("amount_bits"))
        .def(py::pickle(
        [](const QSketch &p) {
            return py::make_tuple(
                p.get_sketch_size(),
                p.get_seeds(),
                p.get_amount_bits(),
                p.get_registers()
            );
        },
        [](const py::tuple& t) {
            if (t.size() != 4) {
                throw std::runtime_error("Invalid state for QSketch pickle!");
            }
            return QSketch(
                t[0].cast<std::size_t>(),
                t[1].cast<std::vector<std::uint32_t>>(),
                t[2].cast<std::uint8_t>(),
                t[3].cast<std::vector<int>>()
            );
        }
    ));
    bind_common_sketch_methods(qsketch);

    auto fastlogexpsketch = py::class_<FastLogExpSketch>(m, "FastLogExpSketch")
        .def(py::init<std::size_t, const std::vector<std::uint32_t>&, std::uint8_t, float>(),
            py::arg("m"), py::arg("seeds"), py::arg("amount_bits"), py::arg("logarithm_base"))
        .def(py::pickle(
        [](const FastLogExpSketch &p) {
            return py::make_tuple(
                p.get_sketch_size(),
                p.get_seeds(),
                p.get_amount_bits(),
                p.get_registers(),
                p.get_logarithm_base()
            );
        },
        [](const py::tuple& t) {
            if (t.size() != 5) {
                throw std::runtime_error("Invalid state for FastLogExpSketch pickle!");
            }
            return FastLogExpSketch(
                t[0].cast<std::size_t>(),
                t[1].cast<std::vector<std::uint32_t>>(),
                t[2].cast<std::uint8_t>(),
                t[4].cast<float>(),
                t[3].cast<std::vector<int>>()
            );
        }
    ));;
    bind_common_sketch_methods(fastlogexpsketch);

    auto baselogexpsketch = py::class_<BaseLogExpSketch>(m, "BaseLogExpSketch")
        .def(py::init<std::size_t, const std::vector<std::uint32_t>&, std::uint8_t, float>(),
            py::arg("m"), py::arg("seeds"), py::arg("amount_bits"), py::arg("logarithm_base"))
        .def(py::pickle(
        [](const BaseLogExpSketch &p) {
            return py::make_tuple(
                p.get_sketch_size(),
                p.get_seeds(),
                p.get_amount_bits(),
                p.get_registers(),
                p.get_logarithm_base()
            );
        },
        [](const py::tuple& t) {
            if (t.size() != 5) {
                throw std::runtime_error("Invalid state for BaseLogExpSketch pickle!");
            }
            return BaseLogExpSketch(
                t[0].cast<std::size_t>(),
                t[1].cast<std::vector<std::uint32_t>>(),
                t[2].cast<std::uint8_t>(),
                t[4].cast<float>(),
                t[3].cast<std::vector<int>>()
            );
        }
    ));
    bind_common_sketch_methods(baselogexpsketch);

    auto baseshiftedlogexpsketch = py::class_<BaseShiftedLogExpSketch>(m, "BaseShiftedLogExpSketch")
        .def(py::init<std::size_t, const std::vector<std::uint32_t>&, std::uint8_t, float>(),
            py::arg("m"), py::arg("seeds"), py::arg("amount_bits"), py::arg("logarithm_base"))
        .def(py::pickle(
        [](const BaseShiftedLogExpSketch &p) {
            return py::make_tuple(
                p.get_sketch_size(),
                p.get_seeds(),
                p.get_amount_bits(),
                p.get_logarithm_base(),
                p.get_registers(),
                p.get_offset()
            );
        },
        [](const py::tuple& t) {
            if (t.size() != 6) {
                throw std::runtime_error("Invalid state for BaseShiftedLogExpSketch pickle!");
            }
            return BaseShiftedLogExpSketch(
                t[0].cast<std::size_t>(),
                t[1].cast<std::vector<std::uint32_t>>(),
                t[2].cast<std::uint8_t>(),
                t[3].cast<float>(),
                t[4].cast<std::vector<uint32_t>>(),
                t[5].cast<int>()
            );
        }
    ));
    bind_common_sketch_methods(baseshiftedlogexpsketch);

    auto fastshiftedlogexpsketch = py::class_<FastShiftedLogExpSketch>(m, "FastShiftedLogExpSketch")
        .def(py::init<std::size_t, const std::vector<std::uint32_t>&, std::uint8_t, float>(),
            py::arg("m"), py::arg("seeds"), py::arg("amount_bits"), py::arg("logarithm_base"))
        .def(py::pickle(
        [](const FastShiftedLogExpSketch &p) {
            return py::make_tuple(
                p.get_sketch_size(),
                p.get_seeds(),
                p.get_amount_bits(),
                p.get_logarithm_base(),
                p.get_registers(),
                p.get_offset()
            );
        },
        [](const py::tuple& t) {
            if (t.size() != 6) {
                throw std::runtime_error("Invalid state for FastShiftedLogExpSketch pickle!");
            }
            return FastShiftedLogExpSketch(
                t[0].cast<std::size_t>(),
                t[1].cast<std::vector<std::uint32_t>>(),
                t[2].cast<std::uint8_t>(),
                t[3].cast<float>(),
                t[4].cast<std::vector<uint32_t>>(),
                t[5].cast<int>()
            );
        }
    ));
    bind_common_sketch_methods(fastshiftedlogexpsketch);
}
