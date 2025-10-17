// Copyright (c) 2021-2025 The Regents of the University of Michigan
// Part of spatula, released under the BSD 3-Clause License.

#include <pybind11/stl.h>

#include "Mesh.h"
#include "NoOptimization.h"
#include "Optimize.h"
#include "RandomSearch.h"
#include "StepGradientDescent.h"
#include "Union.h"
#include "export_optimize.h"

namespace spatula { namespace optimize {
void export_optimize(py::module& m)
{
    export_base_optimize(m);
    export_step_gradient_descent(m);
    export_mesh(m);
    export_random_search(m);
    export_union(m);
    export_no_optimization(m);
}
}} // namespace spatula::optimize
