import types
from typing import Any, Literal, Mapping, Optional, Tuple, Type, Union

from anndata import AnnData

from aligndg.uopt import _constants
from aligndg.uopt._types import (
    CostKwargs_t,
    OttCostFnMap_t,
    Policy_t,
    ProblemStage_t,
    QuadInitializer_t,
    ScaleCost_t,
)
from aligndg.uopt.base.problems.compound_problem import B, CompoundProblem, K
from aligndg.uopt.base.problems.problem import OTProblem
from aligndg.uopt.problems._utils import handle_cost, handle_joint_attr
from aligndg.uopt.problems.space._mixins import SpatialAlignmentMixin

__all__ = ["AlignmentProblem"]


class AlignmentProblem(SpatialAlignmentMixin[K, B], CompoundProblem[K, B]):
    def __init__(self, adata: AnnData, **kwargs: Any):
        super().__init__(adata, **kwargs)

    def prepare(
        self,
        batch_key: str,
        spatial_key: str = "spatial",
        joint_attr: Optional[Union[str, Mapping[str, Any]]] = None,
        policy: Literal["sequential", "star"] = "sequential",
        reference: Optional[str] = None,
        normalize_spatial: bool = True,
        cost: OttCostFnMap_t = "sq_euclidean",
        cost_kwargs: CostKwargs_t = types.MappingProxyType({}),
        a: Optional[Union[bool, str]] = None,
        b: Optional[Union[bool, str]] = None,
        **kwargs: Any,
    ) -> "AlignmentProblem[K, B]":
        self.spatial_key = spatial_key
        self.batch_key = batch_key

        x = y = {"attr": "obsm", "key": self.spatial_key}

        if normalize_spatial and "x_callback" not in kwargs and "y_callback" not in kwargs:
            kwargs["x_callback"] = kwargs["y_callback"] = "spatial-norm"
            kwargs.setdefault("x_callback_kwargs", x)
            kwargs.setdefault("y_callback_kwargs", y)

        if "spatial-norm" in kwargs.get("x_callback", {}) and "spatial-norm" in kwargs.get("y_callback", {}):
            x = {}
            y = {}

        xy, kwargs = handle_joint_attr(joint_attr, kwargs)
        xy, x, y = handle_cost(xy=xy, x=x, y=y, cost=cost, cost_kwargs=cost_kwargs, **kwargs)  # type: ignore[arg-type]

        return super().prepare(  # type: ignore[return-value]
            x=x, y=y, xy=xy, policy=policy, key=batch_key, reference=reference, cost=cost, a=a, b=b, **kwargs
        )

    def solve(
        self,
        alpha: float = 0.5,
        epsilon: float = 1e-2,
        tau_a: float = 1.0,
        tau_b: float = 1.0,
        rank: int = -1,
        scale_cost: ScaleCost_t = "mean",
        batch_size: Optional[int] = None,
        stage: Union[ProblemStage_t, Tuple[ProblemStage_t, ...]] = ("prepared", "solved"),
        initializer: QuadInitializer_t = None,
        initializer_kwargs: Mapping[str, Any] = types.MappingProxyType({}),
        jit: bool = True,
        min_iterations: int = 5,
        max_iterations: int = 50,
        threshold: float = 1e-3,
        linear_solver_kwargs: Mapping[str, Any] = types.MappingProxyType({}),
        device: Optional[Literal["cpu", "gpu", "tpu"]] = None,
        **kwargs: Any,
    ) -> "AlignmentProblem[K,B]":

        return super().solve(  # type: ignore[return-value]
            alpha=alpha,
            epsilon=epsilon,
            tau_a=tau_a,
            tau_b=tau_b,
            rank=rank,
            scale_cost=scale_cost,
            batch_size=batch_size,
            stage=stage,
            initializer=initializer,
            initializer_kwargs=initializer_kwargs,
            jit=jit,
            min_iterations=min_iterations,
            max_iterations=max_iterations,
            threshold=threshold,
            linear_solver_kwargs=linear_solver_kwargs,
            device=device,
            **kwargs,
        )

    @property
    def _base_problem_type(self) -> Type[B]:
        return OTProblem  # type: ignore[return-value]

    @property
    def _valid_policies(self) -> Tuple[Policy_t, ...]:
        return _constants.SEQUENTIAL, _constants.STAR  # type: ignore[return-value]
