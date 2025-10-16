# Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""The library of Hexaly algorithm."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar

from gemseo.algos.design_space import DesignSpace
from gemseo.algos.opt.base_optimization_library import BaseOptimizationLibrary
from gemseo.algos.opt.base_optimization_library import OptimizationAlgorithmDescription
from gemseo.utils.seeder import SEED
from hexaly.optimizer import HexalyOptimizer

from gemseo_hexaly.algos.opt.hexaly._core.hexaly_function import HexalyFunction
from gemseo_hexaly.algos.opt.hexaly.hexaly_settings import HexalySettings

if TYPE_CHECKING:
    from gemseo.algos.optimization_problem import OptimizationProblem
    from hexaly.optimizer import HxModel

    from gemseo_hexaly.algos.opt.hexaly._core.hexaly_callback import HexalyCallback


@dataclass
class HexalyAlgorithmDescription(OptimizationAlgorithmDescription):
    """The description of an optimization algorithm from the Hexaly library."""

    algorithm_name: str = "HEXALY"
    """The algorithm name."""

    internal_algorithm_name: str = "HEXALY"
    """The internal algorithm name."""

    library_name: str = "Hexaly"
    """The library name."""

    description: str = (
        "Commercial black-box Hexaly library. "
        "It relies on a global mixed-integer solver."
    )
    """The library description."""

    website: str = "https://www.hexaly.com/docs/last/index.html"
    """The documentation of Hexaly."""

    handle_integer_variables: bool = True
    """Whether Hexaly handles integer variables."""

    handle_equality_constraints: bool = True
    """Whether Hexaly handles equality constraints."""

    handle_inequality_constraints: bool = True
    """Whether Hexaly handles inequality constraints."""

    Settings: type[HexalySettings] = HexalySettings
    """The option validation model for the Hexaly library."""


class HexalyOpt(BaseOptimizationLibrary[HexalySettings]):
    """The library of Hexaly optimization algorithm.

    It contains
        - the creation of the Hexaly model,
        - the warm start by using the current values of the design variables,
        - its execution and
        - the exploitation of the solution.
    """

    ALGORITHM_INFOS: ClassVar[dict[str, HexalyAlgorithmDescription]] = {
        "HEXALY": HexalyAlgorithmDescription()
    }

    __callback: HexalyCallback | None
    """The Hexaly callback."""

    __external_function: HexalyFunction
    """The external function to be considered in the Hexaly model."""

    __scalar_design_space: DesignSpace
    """The scalar design space of the problem."""

    __variables: dict[str, Any]
    """The Hexaly variables."""

    def _run(self, problem: OptimizationProblem) -> tuple[str, int]:
        self.__callback = self._settings.callback
        self.__variables = {}

        with HexalyOptimizer() as optimizer:
            self.__create_model(optimizer, problem)
            self.__set_initial_solution()
            self.__solve(optimizer)

        msg = (
            "Hexaly should not stop by itself. ",
            "Hence, GEMSEO should manage its termination criteria.",
        )  # pragma: no cover
        raise ValueError(msg)  # pragma: no cover
        return "ERROR", -1  # pragma: no cover

    def __create_model(
        self,
        optimizer: HexalyOptimizer,
        optimization_problem: OptimizationProblem,
    ) -> None:
        """Create the Hexaly model.

        Args:
            optimizer: The Hexaly optimizer.
            optimization_problem: The optimization problem.
        """
        model: HxModel = optimizer.model
        if self.__callback is not None:
            # If the callback is defined
            # it will be called at every iteration
            # (at each external function evaluation)
            optimizer.add_callback(
                self.__callback._CALLBACK_TYPE, self.__callback.execute_callback
            )
            optimizer.param.iteration_between_ticks = (
                self.__callback._N_ITERATIONS_BETWEEN_TICKS
            )

        self.__create_hexaly_variables(model, optimization_problem)

        # external function
        # the outputs are Objective + Constraints
        self.__external_function = HexalyFunction(
            optimization_problem, self._settings.normalize_design_space
        )

        external_function = model.create_double_array_external_function(
            self.__external_function.evaluate
        )
        if self._settings.activate_surrogate:
            _ = external_function.external_context.enable_surrogate_modeling()

        outputs = external_function(list(self.__variables.values()))

        # objective function
        model.minimize(outputs[0])

        # constraints
        for i in range(len(optimization_problem.constraints)):
            model.constraint(outputs[i + 1] <= 0)

        model.close()

    def __set_initial_solution(
        self,
    ) -> None:
        """Set the initial solution."""
        if not self._settings.warm_start:
            return

        for variable_name, variable in self.__variables.items():
            variable.value = self.__scalar_design_space.get_current_value(
                [variable_name],
                normalize=self._settings.normalize_design_space,
            )[0]

    def __solve(self, optimizer: HexalyOptimizer) -> None:
        """Solve the model.

        Args:
            optimizer: The Hexaly optimizer.
        """
        optimizer.param.nb_threads = self._settings.nb_threads
        optimizer.param.verbosity = self._settings.verbosity
        optimizer.param.seed = self._settings.seed or SEED
        if self._settings.use_reproducible_surrogate:
            optimizer.param.set_advanced_param(
                "bbInnerSolverChoiceForReproducibility", 1
            )
        optimizer.solve()

    def __create_hexaly_variables(
        self,
        model: HxModel,
        optimization_problem: OptimizationProblem,
    ) -> None:
        """Create the Hexaly variables.

        Args:
            model: The Hexaly model.
            optimization_problem: The optimization problem.
        """
        self.__scalar_design_space = (
            optimization_problem.design_space.to_scalar_variables()
        )
        normalize_design_space = self._settings.normalize_design_space

        for name, normalize in self.__scalar_design_space.normalize.items():
            if normalize_design_space and normalize[0]:
                variable_type = model.float
                type_ = float
                lower_bound = 0
                upper_bound = 1
            else:
                lower_bound = self.__scalar_design_space.get_lower_bound(name)[0]
                upper_bound = self.__scalar_design_space.get_upper_bound(name)[0]
                if (
                    self.__scalar_design_space.get_type(name)
                    == DesignSpace.DesignVariableType.INTEGER
                ):
                    variable_type = model.int
                    type_ = int
                else:
                    variable_type = model.float
                    type_ = float

            self.__variables[name] = variable_type(
                type_(lower_bound), type_(upper_bound)
            )
