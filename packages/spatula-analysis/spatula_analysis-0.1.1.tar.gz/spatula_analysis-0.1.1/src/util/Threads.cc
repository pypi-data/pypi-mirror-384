// Copyright (c) 2021-2025 The Regents of the University of Michigan
// Part of spatula, released under the BSD 3-Clause License.

#include "Threads.h"

namespace spatula { namespace util {
void export_threads(py::module& m)
{
    m.def("set_num_threads",
          [](size_t num_threads) { ThreadPool::get().set_threads(num_threads); });
    m.def("get_num_threads", []() { return ThreadPool::get().get_num_threads(); });
}
}} // End namespace spatula::util
