from pydantic import Field

from .fujits_da_base import FujitsuDABase


class FujitsuDA(FujitsuDABase):
    """
    Parameters for the Fujitsu Digital Annealer (v3c).

    Attributes
    ----------
    time_limit_sec: int | None
        Maximum running time of DA in seconds. Specifies the upper limit of running
        time of DA. Time_limit_sec should be selected according to problem hardness
        and size (number of bits). Min: 1, Max: 3600
    target_energy: int | None
        Threshold energy for fast exit. This may not work correctly if the specified
        value is larger than its max value or lower than its min value.
        Min: -99_999_999_999, Max: 99_999_999_999
    num_group: int
        Number of independent optimization processes. Increasing the number of
        independent optimization processes leads to better coverage of the search
        space. Note: Increasing this number requires to also increase time_limit_sec
        such that the search time for each process is sufficient.
        Default: 1, Min: 1, Max: 16
    num_solution: int
        Number of solutions maintained and updated by each optimization process.
        Default: 16, Min: 1, Max: 1024
    num_output_solution: int
        Maximal number of the best solutions returned by each optimization.
        Total number of results is ``num_solution`` * ``num_group``.
        Default: 5, Min: 1, Max: 1024
    gs_num_iteration_factor: int
        Maximal number of iterations in one epoch of the global search in each
        optimization is ``gs_num_iteration_factor`` * *number of bits*.
        Default: 5, Min: 0, Max: 100
    gs_num_iteration_cl: int
        Maximal number of iterations without improvement in one epoch of the global
        search in each optimization before terminating and continuing with the next
        epoch. For problems with very deep local minima having a very low value is
        helpful. Default: 800, Min: 0, Max: 1000000
    gs_ohs_xw1h_num_iteration_factor: int
        Maximal number of iterations in one epoch of the global search in each
        optimization is ``gs_ohs_xw1h_num_iteration_factor`` * *number of bits*.
        Only used when 1Hot search is defined. Default: 3, Min: 0, Max: 100
    gs_ohs_xw1h_num_iteration_cl: int
        Maximal number of iterations without improvement in one epoch of the global
        search in each optimization before terminating and continuing with the next
        epoch. For problems with very deep local minima having a very low value is
        helpful. Only used when 1Hot search is defined.
        Default: 100, Min: 0, Max: 1000000
    ohs_xw1h_internal_penalty: int | str
        Mode of 1hot penalty constraint generation.
        - 0: internal penalty generation off: 1hot constraint as part of penalty
             polynomial required
        - 1: internal penalty generation on: 1hot constraint not as part of penalty
             polynomial required
        If 1way 1hot constraint or a 2way 1hot constraint is specified,
        ``ohs_xw1h_internal_penalty`` = 1 is recommended.
        Default: 0, Min: 0, Max: 1
    gs_penalty_auto_mode: int
        Parameter to choose whether to automatically incrementally adapt
        ``gs_penalty_coef`` to the optimal value.
        - 0: Use ``gs_penalty_coef`` as the fixed factor to weight the penalty
             polynomial during optimization.
        - 1: Start with ``gs_penalty_coef`` as weight factor for penalty polynomial
             and automatically and incrementally increase this factor during
             optimization by multiplying ``gs_penalty_inc_rate`` / 100 repeatedly
             until ``gs_max_penalty_coef`` is reached or the penalty energy iszero.
        Default: 1, Min: 0, Max: 1
    gs_penalty_coef: int
        Factor to weight the penalty polynomial. If ``gs_penalty_auto_mode`` is 0,
        this value does not change. If ``gs_penalty_auto_mode`` is 1, this initial
        weight factor is repeatedly increased by ``gs_penalty_inc_rate`` until
        ``gs_max_penalty_coef`` is reached or the penalty energy is zero.
        Default: 1, Min: 1, Max: 9_223_372_036_854_775_807
    gs_penalty_inc_rate: int
        Only used if ``gs_penalty_auto_mode`` is 1. In this case, the initial weight
        factor ``gs_penalty_coef`` for the penalty polynomial is repeatedly
        increased by multiplying ``gs_penalty_inc_rate`` / 100 until
        ``gs_max_penalty_coef`` is reached or the penalty energy is zero.
        Default: 150, Min: 100, Max: 200
    gs_max_penalty_coef: int
        Maximal value for the penalty coefficient. If ``gs_penalty_auto_mode`` is 0,
        this is the maximal value for ``gs_penalty_coef``.
        If ``gs_penalty_auto_mode`` is 1, this is the maximal value to which
        ``gs_penalty_coef`` can be increased during the automatic adjustment.
        If ``gs_max_penalty_coef`` is set to 0, then the maximal penalty coefficient
        is 2^63 - 1.
        Default: 0, Min: 0, Max: 9_223_372_036_854_775_807


    scaling_action: Literal["NOTHING", "SCALING", "AUTO_SCALING"]
        Method for scaling ``qubo`` and determining temperatures:
        - "NOTHING": No action (use parameters exactly as specified)
        - "SCALING": ``scaling_factor`` is multiplied to ``qubo``,
          ``temperature_start``, ``temperature_end`` and ``offset_increase_rate``.
        - "AUTO_SCALING": A maximum scaling factor w.r.t. ``scaling_bit_precision``
          is multiplied to ``qubo``, ``temperature_start``, ``temperature_end`` and
          ``offset_increase_rate``.
    scaling_factor: int | float
        Multiplicative factor applied to model coefficients, temperatures, and other
        parameters: the ``scaling_factor`` for ``qubo``, ``temperature_start``,
        ``temperature_end`` and ``offset_increase_rate``.
        Higher values can improve numerical precision but may lead to overflow.
        Default is 1.0 (no scaling).
    scaling_bit_precision: int
        Maximum bit precision to use when scaling. Determines the maximum allowable
        coefficient magnitude. Default is 64, using full double precision.
    random_seed: Union[int, None]
        Seed for random number generation to ensure reproducible results.
        Must be between 0 and 9_999. Default is None (random seed).
    penalty_factor: float
        Penalty factor used to scale the equality constraint penalty function,
        default 1.0.
    inequality_factor: int
        Penalty factor used to scale the inequality constraints, default 1.
    remove_ohg_from_penalty: bool
        If equality constraints, identified to be One-Hot constraints are only
        considered within one-hot groups (`remove_ohg_from_penalty=True`),
        i.e., identified one-hot constraints are not added to the penalty function,
        default True.
    """

    time_limit_sec: int | None = Field(default=None, ge=1, le=3600)
    target_energy: int | None = Field(
        default=None, ge=-99_999_999_999, le=99_999_999_999
    )
    num_group: int = Field(default=1, ge=1, le=16)
    num_solution: int = Field(default=16, ge=1, le=1024)
    num_output_solution: int = Field(default=5, ge=1, le=1024)
    gs_num_iteration_factor: int = Field(default=5, ge=0, le=100)
    gs_num_iteration_cl: int = Field(default=800, ge=0, le=1_000_000)
    gs_ohs_xw1h_num_iteration_factor: int = Field(default=3, ge=0, le=100)
    gs_ohs_xw1h_num_iteration_cl: int = Field(default=100, ge=0, le=1_000_000)
    ohs_xw1h_internal_penalty: int = Field(default=0, ge=0, le=1)
    gs_penalty_auto_mode: int = Field(default=1, ge=0, le=1)
    gs_penalty_coef: int = Field(default=1, ge=1, le=2**63 - 1)
    gs_penalty_inc_rate: int = Field(default=150, ge=100, le=200)
    gs_max_penalty_coef: int = Field(default=0, ge=0, le=2**63 - 1)

    @property
    def algorithm_name(self) -> str:
        """
        Returns the name of the algorithm.

        This abstract property method is intended to be overridden by subclasses.
        It should provide the name of the algorithm being implemented.

        Returns
        -------
        str
            The name of the algorithm.
        """
        return "FDAV3C"
