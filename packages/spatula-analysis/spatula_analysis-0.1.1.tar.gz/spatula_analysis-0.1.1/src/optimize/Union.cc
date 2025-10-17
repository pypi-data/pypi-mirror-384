// Copyright (c) 2021-2025 The Regents of the University of Michigan
// Part of spatula, released under the BSD 3-Clause License.

#include <pybind11/stl.h>

#include "StepGradientDescent.h"
#include "Union.h"

namespace spatula { namespace optimize {
Union::Union(const std::shared_ptr<const Optimizer>& initial_opt,
             std::function<std::unique_ptr<Optimizer>(const Optimizer&)> instantiate_final)
    : Optimizer(), m_inital_opt(initial_opt->clone()), m_final_opt(nullptr),
      m_instantiate_final(instantiate_final), m_on_final_opt(false)
{
}

Union::Union(const Union& original)
    : Optimizer(), m_inital_opt(original.m_inital_opt->clone()), m_final_opt(nullptr),
      m_instantiate_final(original.m_instantiate_final), m_on_final_opt(original.m_on_final_opt)
{
    if (m_on_final_opt) {
        m_final_opt = original.m_final_opt->clone();
    }
}

void Union::record_objective(double objective)
{
    if (!m_need_objective) {
        throw std::runtime_error("Must get new point before recording objective.");
    }
    m_need_objective = false;
    m_objective = objective;
    if (objective < m_best_point.second) {
        m_best_point.first = m_point;
        m_best_point.second = objective;
    }
    getCurrentOptimizer().record_objective(objective);
}

void Union::internal_next_point()
{
    if (!m_on_final_opt && getCurrentOptimizer().terminate()) {
        createFinalOptimizer();
        m_on_final_opt = true;
    }
    m_point = getCurrentOptimizer().next_point();
}

bool Union::terminate() const
{
    return m_on_final_opt && getCurrentOptimizer().terminate();
}

std::unique_ptr<Optimizer> Union::clone() const
{
    return std::make_unique<Union>(*this);
}

Optimizer& Union::getCurrentOptimizer()
{
    if (m_on_final_opt) {
        return *m_final_opt.get();
    } else {
        return *m_inital_opt.get();
    }
}

const Optimizer& Union::getCurrentOptimizer() const
{
    if (m_on_final_opt) {
        return *m_final_opt.get();
    } else {
        return *m_inital_opt.get();
    }
}

void Union::createFinalOptimizer()
{
    m_final_opt = m_instantiate_final(*m_inital_opt.get());
}

void export_union(py::module& m)
{
    py::class_<Union, Optimizer, std::shared_ptr<Union>>(m, "Union")
        .def_static("with_step_gradient_descent",
                    [](const std::shared_ptr<const Optimizer> initial_opt,
                       unsigned int max_iter,
                       double initial_jump,
                       double learning_rate,
                       double tol) -> auto {
                        return std::make_shared<Union>(
                            initial_opt,
                            [max_iter, initial_jump, learning_rate, tol](const Optimizer& opt) {
                                return std::make_unique<StepGradientDescent>(
                                    opt.get_optimum().first,
                                    max_iter,
                                    initial_jump,
                                    learning_rate,
                                    tol);
                            });
                    });
}
}} // namespace spatula::optimize
