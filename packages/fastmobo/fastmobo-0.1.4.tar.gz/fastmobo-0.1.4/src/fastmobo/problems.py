from botorch.test_functions.base import MultiObjectiveTestProblem
from botorch.utils.multi_objective.hypervolume import Hypervolume
from botorch.utils.multi_objective.pareto import is_non_dominated
from typing import Callable, Optional
from torch import Tensor
import torch 

class FastMoboProblem(MultiObjectiveTestProblem):
    """ Custom multi-objective problem wrapper """


    # TODO:: add setters for bounds, ref_point
    def __init__(self, 
                 objective_func: Callable[[Tensor], Tensor],
                 bounds: torch.Tensor,
                 ref_point: torch.Tensor,
                 num_objectives: int,
                 noise_std: Optional[torch.Tensor] = None,
                 negate: bool = True,
                 max_hv: Optional[float] = None):
        """
        Args:
            objective_func: Function that takes x (n_points x dim) and returns objectives (n_points x num_obj)
            bounds: 2 x dim tensor with [lower_bounds, upper_bounds]
            ref_point: Reference point for hypervolume calculation
            num_objectives: Number of objectives
            noise_std: Standard deviation of observation noise
            negate: Whether to negate objectives (for maximization)
            max_hv: Maximum achievable hypervolume (for plotting)
        """
        self.objective_func = objective_func
        self.bounds = bounds
        self.ref_point = ref_point
        self.num_objectives = num_objectives
        self.noise_std = noise_std if noise_std is not None else torch.zeros(num_objectives)
        self.negate = negate
        self._max_hv = max_hv
        self.dim = bounds.shape[1]
    
    @property
    def max_hv(self) -> float:
        if self._max_hv is not None:
            return self._max_hv
        else:
            return  self._estimate_max_hv(self.objective_func, self.bounds, self.ref_point)
    
    def _estimate_max_hv(objective_func: Callable, bounds: torch.Tensor, ref_point: torch.Tensor, n_samples:int=10000):
        """ Estimate maximum hypervolume using random sampling """
        # Uniform random samples in input space
        X = torch.rand(n_samples, bounds.shape[1]) * (bounds[1] - bounds[0]) + bounds[0]
        Y = objective_func(X)
        
        # Keep only non-dominated solutions
        mask = is_non_dominated(Y)
        pareto_Y = Y[mask]
        
        # Compute HV of Pareto front
        hv = Hypervolume(ref_point=ref_point)
        return hv.compute(pareto_Y)

    def __call__(self, X: Tensor):
        return self._evaluate_true(X)
    
    def _evaluate_true(self, X: Tensor):
        obj = self.objective_func(X)
        return -obj if self.negate else obj
    
    def gen_pareto_front(self, n: int) -> Tensor:
        """ assuming problem will be generally a continuous black box function """
        X = torch.rand(5000, self.dim) * (self.bounds[1] - self.bounds[0]) + self.bounds[0]
        Y = self.objective_func(X)
        
        mask = is_non_dominated(Y)
        pareto_Y = Y[mask]

        # If too many points, downsample to n evenly spaced points
        if pareto_Y.shape[0] > n:
            idx = torch.linspace(0, pareto_Y.shape[0]-1, n).long()
            pareto_Y = pareto_Y[idx]

        return pareto_Y

