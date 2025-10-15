# SPDX-FileCopyrightText: 2025 Qoro Quantum Ltd <divi@qoroquantum.de>
#
# SPDX-License-Identifier: Apache-2.0

import string
from functools import partial
from typing import TypeVar

import dimod
import hybrid
import numpy as np
import scipy.sparse as sps
from dimod import BinaryQuadraticModel

from divi.backends import CircuitRunner
from divi.qprog.algorithms import QAOA, QUBOProblemTypes
from divi.qprog.batch import ProgramBatch
from divi.qprog.optimizers import MonteCarloOptimizer, Optimizer
from divi.qprog.quantum_program import QuantumProgram


# Helper function to merge subsamples in-place
def _merge_substates(_, substates):
    a, b = substates
    return a.updated(subsamples=hybrid.hstack_samplesets(a.subsamples, b.subsamples))


T = TypeVar("T", bound=QUBOProblemTypes | BinaryQuadraticModel)


def _sanitize_problem_input(qubo: T) -> tuple[T, BinaryQuadraticModel]:
    if isinstance(qubo, BinaryQuadraticModel):
        return qubo, qubo

    if isinstance(qubo, (np.ndarray, sps.spmatrix)):
        x, y = qubo.shape
        if x != y:
            raise ValueError("Only matrices supported.")

    if isinstance(qubo, np.ndarray):
        return qubo, dimod.BinaryQuadraticModel(qubo, vartype=dimod.Vartype.BINARY)

    if isinstance(qubo, sps.spmatrix):
        return qubo, dimod.BinaryQuadraticModel(
            {(row, col): data for row, col, data in zip(qubo.row, qubo.col, qubo.data)},
            vartype=dimod.Vartype.BINARY,
        )

    raise ValueError(f"Got an unsupported QUBO input format: {type(qubo)}")


class QUBOPartitioningQAOA(ProgramBatch):
    def __init__(
        self,
        qubo: QUBOProblemTypes | BinaryQuadraticModel,
        decomposer: hybrid.traits.ProblemDecomposer,
        n_layers: int,
        backend: CircuitRunner,
        composer: hybrid.traits.SubsamplesComposer = hybrid.SplatComposer(),
        optimizer: Optimizer | None = None,
        max_iterations: int = 10,
        **kwargs,
    ):
        """
        Initialize a QUBOPartitioningQAOA instance for solving QUBO problems using partitioning and QAOA.

        Args:
            qubo (QUBOProblemTypes | BinaryQuadraticModel): The QUBO problem to solve, provided as a supported type or a BinaryQuadraticModel.
                Note: Variable types are assumed to be binary (not Spin).
            decomposer (hybrid.traits.ProblemDecomposer): The decomposer used to partition the QUBO problem into subproblems.
            n_layers (int): Number of QAOA layers to use for each subproblem.
            backend (CircuitRunner): Backend responsible for running quantum circuits.
            composer (hybrid.traits.SubsamplesComposer, optional): Composer to aggregate subsamples from subproblems.
                Defaults to hybrid.SplatComposer().
            optimizer (Optimizer, optional): Optimizer to use for QAOA.
                Defaults to Optimizer.MONTE_CARLO.
            max_iterations (int, optional): Maximum number of optimization iterations.
                Defaults to 10.
            **kwargs: Additional keyword arguments passed to the QAOA constructor.

        """
        super().__init__(backend=backend)

        self.main_qubo, self._bqm = _sanitize_problem_input(qubo)

        self._partitioning = hybrid.Unwind(decomposer)
        self._aggregating = hybrid.Reduce(hybrid.Lambda(_merge_substates)) | composer

        self.max_iterations = max_iterations

        self.trivial_program_ids = set()

        self._constructor = partial(
            QAOA,
            optimizer=optimizer if optimizer is not None else MonteCarloOptimizer(),
            max_iterations=self.max_iterations,
            backend=self.backend,
            n_layers=n_layers,
            **kwargs,
        )
        pass

    def create_programs(self):
        """
        Partition the main QUBO problem and instantiate QAOA programs for each subproblem.

        This implementation:
        - Uses the configured decomposer to split the main QUBO into subproblems.
        - For each subproblem, creates a QAOA program with the specified parameters.
        - Stores each program in `self.programs` with a unique identifier.

        Unique Identifier Format:
            Each key in `self.programs` is a tuple of the form (letter, size), where:
                - letter: An uppercase letter ('A', 'B', 'C', ...) indicating the partition index.
                - size: The number of variables in the subproblem.

            Example: ('A', 5) refers to the first partition with 5 variables.
        """

        super().create_programs()

        self.prog_id_to_bqm_subproblem_states = {}

        init_state = hybrid.State.from_problem(self._bqm)
        _bqm_partitions = self._partitioning.run(init_state).result()

        for i, partition in enumerate(_bqm_partitions):
            if i > 0:
                # We only need 'problem' on the first partition since
                # it will propagate to the other partitions during
                # aggregation, otherwise it's a waste of memory
                del partition["problem"]

            prog_id = (string.ascii_uppercase[i], len(partition.subproblem))
            self.prog_id_to_bqm_subproblem_states[prog_id] = partition

            if partition.subproblem.num_interactions == 0:
                # Skip creating a full QAOA program for this trivial case.
                self.trivial_program_ids.add(prog_id)
                continue

            ldata, (irow, icol, qdata), _ = partition.subproblem.to_numpy_vectors(
                partition.subproblem.variables
            )

            coo_mat = sps.coo_matrix(
                (
                    np.r_[ldata, qdata],
                    (
                        np.r_[np.arange(len(ldata)), icol],
                        np.r_[np.arange(len(ldata)), irow],
                    ),
                ),
                shape=(len(ldata), len(ldata)),
            )

            self._programs[prog_id] = self._constructor(
                job_id=prog_id,
                problem=coo_mat,
                progress_queue=self._queue,
            )

    def aggregate_results(self):
        """
        Aggregate results from all QUBO subproblems into a global solution.

        Collects solutions from each partitioned subproblem (both QAOA-optimized and
        trivial ones) and uses the hybrid framework composer to combine them into
        a final solution for the original QUBO problem.

        Returns:
            tuple: A tuple containing:
                - solution (np.ndarray): Binary solution vector for the QUBO problem.
                - solution_energy (float): Energy/cost of the solution.

        Raises:
            RuntimeError: If programs haven't been run or if final probabilities
                haven't been computed.
        """
        super().aggregate_results()

        if any(len(program.probs) == 0 for program in self.programs.values()):
            raise RuntimeError(
                "Not all final probabilities computed yet. Please call `run()` first."
            )

        for (
            prog_id,
            bqm_subproblem_state,
        ) in self.prog_id_to_bqm_subproblem_states.items():

            if prog_id in self.trivial_program_ids:
                # Case 1: Trivial problem. Solve classically.
                # The solution is any bitstring (e.g., all zeros) with energy 0.
                var_to_val = {v: 0 for v in bqm_subproblem_state.subproblem.variables}
            else:
                subproblem = self._programs[prog_id]
                var_to_val = dict(
                    zip(bqm_subproblem_state.subproblem.variables, subproblem.solution)
                )

            sample_set = dimod.SampleSet.from_samples(
                dimod.as_samples(var_to_val), "BINARY", 0
            )

            self.prog_id_to_bqm_subproblem_states[prog_id] = (
                bqm_subproblem_state.updated(subsamples=sample_set)
            )

        states = hybrid.States(*list(self.prog_id_to_bqm_subproblem_states.values()))
        final_state = self._aggregating.run(states).result()

        self.solution, self.solution_energy, _ = final_state.samples.record[0]

        return self.solution, self.solution_energy
