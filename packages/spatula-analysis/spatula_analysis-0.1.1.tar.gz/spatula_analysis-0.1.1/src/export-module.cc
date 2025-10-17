// Copyright (c) 2021-2025 The Regents of the University of Michigan
// Part of spatula, released under the BSD 3-Clause License.

#include <pybind11/pybind11.h>

#include "BOOSOP.h"
#include "PGOP.h"
#include "data/Quaternion.h"
#include "data/Vec3.h"
#include "optimize/export_optimize.h"
#include "util/Threads.h"
#include "util/Util.h"

PYBIND11_MODULE(_spatula, m)
{
    spatula::data::export_Vec3(m);
    spatula::data::export_quaternion(m);
    spatula::optimize::export_optimize(m);
    spatula::export_spatula(m);
    spatula::export_BOOSOP(m);
    spatula::util::export_threads(m);
    spatula::util::export_util(m);
}
