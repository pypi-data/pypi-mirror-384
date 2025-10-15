"""Clonal Selection Algorithm (CLONALG)."""

from __future__ import annotations

import heapq
from typing import Optional, Callable, Dict, Literal

import numpy as np
import numpy.typing as npt

from ..utils.display import ProgressTable
from ..base import BaseOptimizer, set_seed_numba
from ..base.mutation import clone_and_mutate_binary, clone_and_mutate_ranged, \
    clone_and_mutate_continuous, clone_and_mutate_permutation
from ..base.populations import generate_random_antibodies
from ..utils.sanitizers import sanitize_seed, sanitize_param, sanitize_bounds
from ..utils.types import FeatureTypeAll


class Clonalg(BaseOptimizer):
    """Clonal Selection Algorithm (CLONALG).

    The Clonal Selection Algorithm (CSA) is an optimization algorithm inspired by the biological
    process of clonal selection and expansion of antibodies in the immune system [1]_. This
    implementation of CLONALG has been adapted for the minimization or maximization of cost
    functions in binary, continuous, ranged-value, and permutation problems.


    Parameters
    ----------
    problem_size : int
        Dimension of the problem to be minimized.
    N : int, default=50
        Number of memory cells (antibodies) in the population.
    rate_clonal : float, default=10
        Maximum number of possible clones of a cell. This value is multiplied by
        cell_affinity to determine the number of clones.
    rate_hypermutation : float, default=0.75
        Rate of mutated clones, used as a scalar factor.
    n_diversity_injection : int, default=5
        Number of new random memory cells injected to maintain diversity.
    selection_size : int, default=5
        Number of the best antibodies selected for cloning.
    affinity_function : Optional[Callable[..., npt.NDArray]], default=None
        Objective function to evaluate candidate solutions in minimizing the problem.
    feature_type : FeatureTypeAll, default='ranged-features'
        Type of problem samples: binary, continuous, or based on value ranges.
        Specifies the type of features: "continuous-features", "binary-features",
        "ranged-features", or "permutation-features".
    bounds : Optional[Dict], default=None
        Definition of search limits when ``feature_type='ranged-features'``.
        Can be provided in two ways:

        * Fixed values: ``{'low': float, 'high': float}``
            Values are replicated across all dimensions, generating equal limits for each
            dimension.
        * Arrays: ``{'low': list, 'high': list}``
            Each dimension has specific limits. Both arrays must be
            ``problem_size``.

    mode : Literal["min", "max"], default="min"
        Defines whether the algorithm minimizes or maximizes the cost function.
    seed : Optional[int], default=None
        Seed for random generation of detector values. If None, the value is random.

    Notes
    -----
    This CLONALG implementation contains some changes based on the AISP context, for general
    application to various problems, which may produce results different from the standard or
    specific implementation. This adaptation aims to generalize CLONALG to minimization and
    maximization tasks, in addition to supporting continuous, discrete, and permutation problems.

    References
    ----------
    .. [1] BROWNLEE, Jason. Clonal Selection Algorithm. Clever Algorithms: Nature-inspired
    Programming Recipes., 2011. Available at:
    https://cleveralgorithms.com/nature-inspired/immune/clonal_selection_algorithm.html
    """

    def __init__(
        self,
        problem_size: int,
        N: int = 50,
        rate_clonal: int = 10,
        rate_hypermutation: float = 0.75,
        n_diversity_injection: int = 5,
        selection_size: int = 5,
        affinity_function: Optional[Callable[..., npt.NDArray]] = None,
        feature_type: FeatureTypeAll = 'ranged-features',
        bounds: Optional[Dict] = None,
        mode: Literal["min", "max"] = "min",
        seed: Optional[int] = None
    ):
        super().__init__()
        self.problem_size = sanitize_param(problem_size, 1, lambda x: x > 0)
        self.N: int = sanitize_param(N, 50, lambda x: x > 0)
        self.rate_clonal: int = sanitize_param(rate_clonal, 10, lambda x: x > 0)
        self.rate_hypermutation: np.float64 = np.float64(
            sanitize_param(
                rate_hypermutation, 0.75, lambda x: x > 0
            )
        )
        self.n_diversity_injection: int = sanitize_param(
            n_diversity_injection, 5, lambda x: x > 0
        )
        self.selection_size: int = sanitize_param(
            selection_size, 5, lambda x: x > 0
        )
        self._affinity_function = affinity_function
        self.feature_type: FeatureTypeAll = feature_type

        self._bounds = None
        self._bounds_extend_cache = None
        self.bounds = bounds

        self.mode: Literal["min", "max"] = sanitize_param(
            mode,
            "min",
            lambda x: x == "max"
        )

        self.seed: Optional[int] = sanitize_seed(seed)
        if self.seed is not None:
            np.random.seed(self.seed)
            set_seed_numba(self.seed)

        self.population = None

    @property
    def bounds(self) -> Optional[Dict]:
        """Getter for the bounds attribute."""
        return self._bounds

    @bounds.setter
    def bounds(self, value: Optional[Dict]):
        """Setter for the bounds attribute."""
        if self.feature_type == 'ranged-features':
            self._bounds = sanitize_bounds(value, self.problem_size)
            low_bounds = np.array(self._bounds['low'])
            high_bounds = np.array(self._bounds['high'])
            self._bounds_extend_cache = np.array([low_bounds, high_bounds])
        else:
            self._bounds = None
            self._bounds_extend_cache = None

    def optimize(
        self,
        max_iters: int = 50,
        n_iter_no_change=10,
        verbose: bool = True
    ) -> npt.NDArray:
        """Execute the optimization process and return the population.

        Parameters
        ----------
        max_iters : int, default=50
            Maximum number of interactions when searching for the best solution using clonalg.
        n_iter_no_change: int, default=10
            the maximum number of iterations without updating the best cell
        verbose : bool, default=True
            Feedback on interactions, indicating the best antibody.

        Returns
        -------
        population : npt.NDArray
            Antibody population after clonal expansion.
        """
        self.reset()
        self.population = self._init_population_antibodies()

        t = 1
        antibodies = [(antibody, self.affinity_function(antibody)) for antibody in self.population]
        best_cost = None
        stop = 0
        progress = ProgressTable(
            {
                "Iteration": 11,
                f"Best Affinity ({self.mode})": 25,
                "Worse Affinity": 20,
                "Stagnation": 17},
            verbose
        )

        while t <= max_iters:
            p_select = self._select_top_antibodies(self.selection_size, antibodies)
            self._record_best(p_select[0][1], p_select[0][0])

            clones = self._clone_and_hypermutation(p_select)

            p_rand = [
                (antibody, self.affinity_function(antibody))
                for antibody in self._diversity_introduction()
            ]
            antibodies = p_select
            antibodies.extend(clones)
            antibodies = self._select_top_antibodies(
                self.N - self.n_diversity_injection, antibodies
            )
            antibodies.extend(p_rand)
            if len(antibodies) > self.N:
                antibodies = self._select_top_antibodies(self.N, antibodies)
            if best_cost == self.best_cost:
                stop += 1
            else:
                stop = 0
                best_cost = self.best_cost
            progress.update(
                {
                    "Iteration": t,
                    f"Best Affinity ({self.mode})": f"{self.best_cost:>25.6f}",
                    "Worse Affinity": f"{antibodies[-1][1]:>20.6f}",
                    "Stagnation": stop
                }
            )
            if stop == n_iter_no_change:
                break

            t += 1
        progress.finish()
        self.population = np.array([antibody for antibody, _ in antibodies]).astype(dtype=float)
        return self.population

    def _select_top_antibodies(self, n: int, antibodies: list[tuple]) -> list[tuple]:
        """Select the antibodies with the highest or lowest values, depending on the mode.

        Parameters
        ----------
        n : int
            Number of antibodies to select.
        antibodies : list[tuple]
            Representing the antibodies and their associated score.

        Returns
        -------
            List containing the `n` antibodies selected according to the defined min or max
            criterion.
        """
        if self.mode == "max":
            return heapq.nlargest(n, antibodies, key=lambda x: x[1])

        return heapq.nsmallest(n, antibodies, key=lambda x: x[1])

    def affinity_function(self, solution: npt.NDArray) -> np.float64:
        """
        Evaluate the affinity of a candidate cell.

        Parameters
        ----------
        solution : npt.NDArray
            Candidate solution to evaluate.

        Returns
        -------
        affinity : float
            Affinity value associated with the given cell.

        Raises
        ------
        NotImplementedError
            If no affinity function has been provided.
        """
        if not callable(self._affinity_function):
            raise NotImplementedError(
                "No affinity function to evaluate the candidate cell was provided."
            )
        return np.float64(self._affinity_function(solution))

    def _init_population_antibodies(self) -> npt.NDArray:
        """Initialize the antibody set of the population randomly.

        Returns
        -------
        npt.NDArray
            List of initialized antibodies.
        """
        return generate_random_antibodies(
            self.N,
            self.problem_size,
            self.feature_type,
            self._bounds_extend_cache
        )

    def _diversity_introduction(self):
        """Introduce diversity into the antibody population.

        Returns
        -------
        npt.NDArray
            Array of new random antibodies for diversity introduction.
        """
        return generate_random_antibodies(
            self.n_diversity_injection,
            self.problem_size,
            self.feature_type,
            self._bounds_extend_cache
        )

    def _clone_and_mutate(
        self,
        antibody: npt.NDArray,
        n_clone: int,
        rate_hypermutation: float
    ) -> npt.NDArray:
        """
        Generate mutated clones from an antibody, based on the feature type.

        Parameters
        ----------
        antibody : npt.NDArray
            Original antibody vector to be cloned and mutated.
        n_clone : int
            Number of clones to generate.

        Returns
        -------
        npt.NDArray
            Array of shape (n_clone, len(antibody)) containing mutated clones
        """
        if self.feature_type == "binary-features":
            return clone_and_mutate_binary(antibody, n_clone)
        if self.feature_type == "ranged-features" and self._bounds_extend_cache is not None:
            return clone_and_mutate_ranged(
                antibody, n_clone, self._bounds_extend_cache, rate_hypermutation
            )
        if self.feature_type == "permutation-features":
            return clone_and_mutate_permutation(antibody, n_clone, rate_hypermutation)
        return clone_and_mutate_continuous(antibody, n_clone, rate_hypermutation)

    def _clone_and_hypermutation(
        self,
        population: list[tuple]
    ) -> list:
        """Clone and hypermutate the population's antibodies.

        The clone list is returned with the clones and their affinities with respect to the cost
        function.

        Parameters
        ----------
        population: list
            The list of antibodies (solutions) to be evaluated and cloned.

        Returns
        -------
        list[npt.NDArray]
            List of mutated clones.
        """
        clonal_m = []
        min_affinity = min(item[1] for item in population)
        max_affinity = max(item[1] for item in population)
        affinity_range = max_affinity - min_affinity

        for antibody, affinity in population:
            if affinity_range == 0:
                normalized_affinity = 1
            else:
                normalized_affinity = (affinity - min_affinity) / affinity_range
                if self.mode == "min":
                    normalized_affinity = max(0.0, 1.0 - normalized_affinity)

            num_clones = max(0, int(self.rate_clonal * normalized_affinity))
            clones = self._clone_and_mutate(
                antibody,
                num_clones,
                1 - np.exp(-self.rate_hypermutation * normalized_affinity)
            )
            clonal_m.extend(clones)

        return [(clone, self.affinity_function(clone)) for clone in clonal_m]
