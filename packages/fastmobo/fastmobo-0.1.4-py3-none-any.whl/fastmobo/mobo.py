
from __future__ import annotations
from botorch.utils.multi_objective.box_decompositions.non_dominated import FastNondominatedPartitioning
from botorch.utils.multi_objective.box_decompositions.dominated import DominatedPartitioning
from botorch.utils.multi_objective.scalarization import get_chebyshev_scalarization
from gpytorch.mlls.sum_marginal_log_likelihood import SumMarginalLogLikelihood
from botorch.utils.sampling import sample_simplex, draw_sobol_samples
from botorch.utils.transforms import unnormalize, normalize
from botorch.acquisition.multi_objective.logei import (
    qLogNoisyExpectedHypervolumeImprovement,
    qLogExpectedHypervolumeImprovement,
)
from botorch.optim.optimize import optimize_acqf, optimize_acqf_list
from botorch.acquisition.logei import qLogNoisyExpectedImprovement
from botorch.models.model_list_gp_regression import ModelListGP
from botorch.acquisition.objective import GenericMCObjective
from botorch.exceptions import BadInitialCandidatesWarning
from botorch.models.transforms.outcome import Standardize
from botorch.sampling.normal import SobolQMCNormalSampler
from botorch.models.gp_regression import SingleTaskGP
from botorch.models.model import Model as GPModel
from fastmobo.problems import FastMoboProblem
from botorch.sampling.base import MCSampler
from matplotlib.cm import ScalarMappable
from botorch import fit_gpytorch_mll
from dataclasses import dataclass
from typing import Optional, Any, TYPE_CHECKING
import matplotlib.pyplot as plt
from loguru import logger
import numpy as np
import warnings
import torch
import time

if TYPE_CHECKING:
    from botorch.models.model import Model as BotorchModel
    from gpytorch.module import Module as GPyTorchModule


warnings.filterwarnings("ignore", category=BadInitialCandidatesWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

@dataclass
class OptimizationResult:
    """Container for optimization results"""
    hypervolumes: dict[str, list[float]]
    train_x: dict[str, torch.Tensor]
    train_obj: dict[str, torch.Tensor]
    train_obj_true: dict[str, torch.Tensor]
    n_iterations: int
    total_time: float
    
    def plot_convergence(self, problem: Optional[FastMoboProblem]=None, save_path: Optional[str] = None):
        """Plot hypervolume convergence"""
        # TODO:: allow custom labels 

        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        
        # Fixed batch size calculation
        first_method = list(self.train_x.keys())[0]
        n_initial = len(self.train_x[first_method]) // (self.n_iterations + 1)
        batch_size = (len(self.train_x[first_method]) - n_initial) // self.n_iterations
        
        # Create iteration axis
        iterations = list(range(self.n_iterations + 1))
        
        for method, hvs in self.hypervolumes.items():
            if problem and hasattr(problem, 'max_hv'):
                log_hv_diff = np.log10(np.maximum(problem.max_hv - np.asarray(hvs), 1e-10))
                ax.plot(iterations, log_hv_diff, label=method, linewidth=2, marker='o')
                ax.set_ylabel("Log Hypervolume Difference")
            else:
                ax.plot(iterations, hvs, label=method, linewidth=2, marker='o')
                ax.set_ylabel("Hypervolume")
        
        ax.set_xlabel("Iteration")
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_title("Optimization Convergence")
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_objectives(self, save_path: Optional[str] = None):
        """Plot objective space exploration"""
        n_methods = len(self.train_obj_true)
        fig, axes = plt.subplots(1, n_methods, figsize=(6*n_methods, 5), 
                                sharex=True, sharey=True)
        if n_methods == 1:
            axes = [axes]

        cm = plt.get_cmap("viridis")

        for i, (method, train_obj) in enumerate(self.train_obj_true.items()):
            obj_np = train_obj.cpu().numpy()
            n_total = len(obj_np)

            batch_numbers = np.linspace(0, self.n_iterations, n_total)

            # ensure lengths match
            assert len(batch_numbers) == n_total, \
                f"Length mismatch: batch_numbers={len(batch_numbers)}, data={n_total}"

            axes[i].set_title(method)
            axes[i].set_xlabel("Objective 1")
            if i == 0:
                axes[i].set_ylabel("Objective 2")

        # Add colorbar
        norm = plt.Normalize(0, self.n_iterations)
        sm = ScalarMappable(norm=norm, cmap=cm)
        sm.set_array([])
        fig.subplots_adjust(right=0.9)
        cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
        cbar = fig.colorbar(sm, cax=cbar_ax)
        cbar.ax.set_title("Iteration")

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
class OptimizationStorage:
    """Custom storage class for optimization data"""
    
    def __init__(self, initial_x: torch.Tensor, initial_obj: torch.Tensor):
        self.train_x = initial_x.clone()
        self.train_obj = initial_obj.clone()
        self.train_obj_true = initial_obj.clone()  # Will be updated with true values
    
    def append_data(self, new_x: torch.Tensor, new_obj: torch.Tensor, new_obj_true: torch.Tensor):
        """Append new optimization data"""
        self.train_x = torch.cat([self.train_x, new_x])
        self.train_obj = torch.cat([self.train_obj, new_obj])
        self.train_obj_true = torch.cat([self.train_obj_true, new_obj_true])

class FastMobo:
    """Fast Multi-Objective Bayesian Optimization"""
    
    # Supported acquisition functions
    SUPPORTED_ACQ_FUNCS = ['qEHVI', 'qNEHVI', 'qNParEGO', 'Random']
    # TODO:: custom GP, Kernels, acquistion function , samplers, schedulers 

    def __init__(self, 
                 problem: Optional[FastMoboProblem],
                 train_x: Optional[torch.Tensor] = None,
                 train_y: Optional[torch.Tensor] = None,
                 acquisition_functions: Optional[list[str]] = None,
                 bounds: Optional[torch.Tensor] = None, # TODO;: already got from problem 
                 ref_point: Optional[torch.Tensor] = None, # TODO;: already got from problem 
                 batch_size: int = 4,
                 num_restarts: int = 10,
                 raw_samples: int = 512,
                 mc_samples: int = 64,
                 maxiter: int = 200,
                 batch_limit: int = 5,
                 n_initial: Optional[int] = None,
                 noise_std: Optional[torch.Tensor] = None,
                 device: str = "cpu",
                 dtype: torch.dtype = torch.double):
        """
        Initialize FastMobo optimizer
        
        Args:
            problem: Problem instance or None (will use BraninCurrin default)
            train_x: Initial input data
            train_y: Initial objective data (noisy observations)
            acquisition_functions: List of acquisition functions to compare
            bounds: Problem bounds (2 x dim tensor)
            ref_point: Reference point for hypervolume
            batch_size: Number of candidates to generate per iteration
            num_restarts: Number of restarts for acquisition optimization
            raw_samples: Number of raw samples for acquisition initialization
            mc_samples: Number of Monte Carlo samples
            maxiter: Maximum iterations for acquisition optimization
            batch_limit: Batch limit for sequential optimization
            n_initial: Number of initial points (default: 2 * (dim + 1))
            noise_std: Noise standard deviation for each objective
            device: Device to run on
            dtype: Data type
        """
        self.device = device
        self.dtype = dtype
        self.tkwargs = {"device": device, "dtype": dtype}
        
        self.problem = problem
            
        if bounds is not None:
            self.problem.bounds = bounds.to(**self.tkwargs)
        if ref_point is not None:
            self.problem.ref_point = ref_point.to(**self.tkwargs)
            
        # Validate acquisition functions
        if acquisition_functions is None:
            acquisition_functions = ['qEHVI', 'qNEHVI', 'qNParEGO', 'Random']
        
        invalid_acqs = set(acquisition_functions) - set(self.SUPPORTED_ACQ_FUNCS)
        if invalid_acqs:
            raise ValueError(f"Unsupported acquisition functions: {invalid_acqs}. "
                           f"Supported: {self.SUPPORTED_ACQ_FUNCS}")
        
        self.acquisition_functions = acquisition_functions
        
        # Optimization parameters
        self.batch_size = batch_size
        self.num_restarts = num_restarts
        self.raw_samples = raw_samples
        self.mc_samples = mc_samples
        self.maxiter = maxiter
        self.batch_limit = batch_limit
        self.n_initial = n_initial or 2 * (self.problem.dim + 1)
        
        self.standard_bounds = torch.zeros(2, self.problem.dim, **self.tkwargs)
        self.standard_bounds[1] = 1
        
        # Set noise standard deviation
        if noise_std is not None:
            self.noise_se = noise_std.to(**self.tkwargs)
        elif hasattr(self.problem, 'noise_std'):
            self.noise_se = self.problem.noise_std
        else:
            n_obj = getattr(self.problem, 'num_objectives', 2)
            self.noise_se = torch.ones(n_obj, **self.tkwargs) * 0.1
        
        # Handle initial data
        self.initial_data = None
        if train_x is not None and train_y is not None:
            self._validate_and_set_initial_data(train_x, train_y)
        
        self.result = None
    
    def _validate_and_set_initial_data(self, train_x: torch.Tensor, train_y: torch.Tensor):
        """Validate and set initial training data"""
        train_x = train_x.to(**self.tkwargs)
        train_y = train_y.to(**self.tkwargs)
        
        # Validate input dimensions
        if train_x.shape[-1] != self.problem.dim:
            raise ValueError(f"Input dimension mismatch: expected {self.problem.dim}, got {train_x.shape[-1]}")
        
        # Validate output dimensions
        expected_obj = getattr(self.problem, 'num_objectives', 2)
        if train_y.shape[-1] != expected_obj:
            raise ValueError(f"Output dimension mismatch: expected {expected_obj}, got {train_y.shape[-1]}")
        
        # Check bounds compliance
        if torch.any(train_x < self.problem.bounds[0]) or torch.any(train_x > self.problem.bounds[1]):
            logger.warning("Some initial data points are outside problem bounds")
        
        # Validate tensor shapes
        if train_x.shape[0] != train_y.shape[0]:
            raise ValueError(f"Batch size mismatch: train_x has {train_x.shape[0]} points, train_y has {train_y.shape[0]}")
        
        self.initial_data = (train_x, train_y)

    def generate_initial_data(self, n: Optional[int] = None) -> tuple[torch.Tensor, torch.Tensor]:
        """Generate initial training data"""
        if n is None:
            n = self.n_initial
            
        train_x = draw_sobol_samples(
            bounds=self.problem.bounds, n=n, q=1
        ).squeeze(1)
        train_y_true = self.problem(train_x)
        train_y_noisy = train_y_true + torch.randn_like(train_y_true) * self.noise_se
        return train_x, train_y_noisy

    def get_initial_data(self) -> tuple[torch.Tensor, torch.Tensor]:
        """Get initial training data, generating if not provided"""
        if self.initial_data is not None:
            return self.initial_data
        else:
            return self.generate_initial_data()

    def append_initial_data(self, train_x: torch.Tensor, train_y: torch.Tensor):
        """Append data to existing initial training data"""
        train_x = train_x.to(**self.tkwargs)
        train_y = train_y.to(**self.tkwargs)
        
        # Validate new data
        self._validate_tensor_properties(train_x, train_y)
        
        if self.initial_data is not None:
            existing_x, existing_y = self.initial_data
            combined_x = torch.cat([existing_x, train_x], dim=0)
            combined_y = torch.cat([existing_y, train_y], dim=0)
            self.initial_data = (combined_x, combined_y)
        else:
            self.initial_data = (train_x, train_y)

    def _validate_tensor_properties(self, train_x: torch.Tensor, train_y: torch.Tensor):
        """Validate tensor properties for consistency"""
        if train_x.device != self.device or train_y.device != self.device:
            raise ValueError(f"Device mismatch: expected {self.device}")
        
        if train_x.dtype != self.dtype or train_y.dtype != self.dtype:
            raise ValueError(f"Data type mismatch: expected {self.dtype}")
        
        if train_x.shape[0] != train_y.shape[0]:
            raise ValueError("Batch size mismatch between train_x and train_y")

    def set_initial_data(self, train_x: torch.Tensor, train_y: torch.Tensor):
        """Set initial training data (useful for warm-starting)"""
        self._validate_and_set_initial_data(train_x, train_y)
    
    def initialize_model(self, train_x: torch.Tensor, train_y: torch.Tensor) -> tuple[GPyTorchModule, BotorchModel]:
        """Initialize GP model"""
        train_x_normalized = normalize(train_x, self.problem.bounds)
        models = []
        
        for i in range(train_y.shape[-1]):
            train_y_i = train_y[..., i:i+1]
            train_yvar = torch.full_like(train_y_i, self.noise_se[i] ** 2)
            models.append(
                SingleTaskGP(
                    train_x_normalized, 
                    train_y_i, 
                    train_yvar,
                    outcome_transform=Standardize(m=1)
                )
            )
        
        model = ModelListGP(*models)
        mll = SumMarginalLogLikelihood(model.likelihood, model)
        return mll, model
    
    def _get_acq_options(self) -> dict[str, Any]:
        """Get acquisition optimization options"""
        return {
            "batch_limit": self.batch_limit, 
            "maxiter": self.maxiter
        }
    
    def _generate_new_candidates(self, new_x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Generate new objective values for candidates"""
        new_obj_true = self.problem(new_x)
        new_obj = new_obj_true + torch.randn_like(new_obj_true) * self.noise_se
        return new_obj, new_obj_true
    
    def optimize_qehvi(self, model:GPModel, train_x: torch.Tensor, train_obj: torch.Tensor, sampler: MCSampler) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Optimize qEHVI acquisition function"""
        with torch.no_grad():
            pred = model.posterior(normalize(train_x, self.problem.bounds)).mean
        
        partitioning = FastNondominatedPartitioning(
            ref_point=self.problem.ref_point,
            Y=pred,
        )
        
        acq_func = qLogExpectedHypervolumeImprovement(
            model=model,
            ref_point=self.problem.ref_point,
            partitioning=partitioning,
            sampler=sampler,
        )
        
        candidates, _ = optimize_acqf(
            acq_function=acq_func,
            bounds=self.standard_bounds,
            q=self.batch_size,
            num_restarts=self.num_restarts,
            raw_samples=self.raw_samples,
            options=self._get_acq_options(),
            sequential=True,
        )
        
        new_x = unnormalize(candidates.detach(), bounds=self.problem.bounds)
        new_obj, new_obj_true = self._generate_new_candidates(new_x)
        return new_x, new_obj, new_obj_true
    
    def optimize_qnehvi(self, model:GPModel, train_x: torch.Tensor, train_obj: torch.Tensor, sampler: MCSampler) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Optimize qNEHVI acquisition function"""
        acq_func = qLogNoisyExpectedHypervolumeImprovement(
            model=model,
            ref_point=self.problem.ref_point.tolist(),
            X_baseline=normalize(train_x, self.problem.bounds),
            prune_baseline=True,
            sampler=sampler,
        )
        
        candidates, _ = optimize_acqf(
            acq_function=acq_func,
            bounds=self.standard_bounds,
            q=self.batch_size,
            num_restarts=self.num_restarts,
            raw_samples=self.raw_samples,
            options=self._get_acq_options(),
            sequential=True,
        )
        
        new_x = unnormalize(candidates.detach(), bounds=self.problem.bounds)
        new_obj, new_obj_true = self._generate_new_candidates(new_x)
        return new_x, new_obj, new_obj_true
    
    def optimize_qnparego(self, model:GPModel, train_x: torch.Tensor, train_obj: torch.Tensor, sampler: MCSampler) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Optimize qNParEGO acquisition function"""
        train_x_norm = normalize(train_x, self.problem.bounds)
        with torch.no_grad():
            pred = model.posterior(train_x_norm).mean
        
        acq_func_list = []
        for _ in range(self.batch_size):
            weights = sample_simplex(self.problem.num_objectives, **self.tkwargs).squeeze()
            objective = GenericMCObjective(
                get_chebyshev_scalarization(weights=weights, Y=pred)
            )
            acq_func = qLogNoisyExpectedImprovement(
                model=model,
                objective=objective,
                X_baseline=train_x_norm,
                sampler=sampler,
                prune_baseline=True,
            )
            acq_func_list.append(acq_func)
        
        candidates, _ = optimize_acqf_list(
            acq_function_list=acq_func_list,
            bounds=self.standard_bounds,
            num_restarts=self.num_restarts,
            raw_samples=self.raw_samples,
            options=self._get_acq_options(),
        )
        
        new_x = unnormalize(candidates.detach(), bounds=self.problem.bounds)
        new_obj, new_obj_true = self._generate_new_candidates(new_x)
        return new_x, new_obj, new_obj_true
    
    def optimize_random(self) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Generate random samples"""
        train_x, train_y = self.generate_initial_data(n=self.batch_size)
        train_y_true = self.problem(train_x)
        return train_x, train_y, train_y_true
    
    def optimize(self, n_iterations: int = 5, verbose: bool = True) -> OptimizationResult:
        """Run multi-objective Bayesian optimization"""
        start_time = time.time()
        
        # Initialize data
        initial_data = self.get_initial_data()
        train_x_init, train_obj_init = initial_data
        
        # Get true initial objectives for hypervolume computation
        train_obj_true_init = self.problem(train_x_init)
        
        # Storage for results using custom storage class
        results: dict[str, OptimizationStorage] = {}
        models = {}
        mlls = {}
        hypervolumes = {}
        
        # Initialize for each acquisition function
        for acq_name in self.acquisition_functions:
            results[acq_name] = OptimizationStorage(train_x_init, train_obj_init)
            results[acq_name].train_obj_true = train_obj_true_init.clone()
            
            if acq_name != 'Random':
                mll, model = self.initialize_model(train_x_init, train_obj_init)
                models[acq_name] = model
                mlls[acq_name] = mll
            
            # Compute initial hypervolume
            bd = DominatedPartitioning(
                ref_point=self.problem.ref_point, 
                Y=train_obj_true_init
            )
            volume = bd.compute_hypervolume().item()
            hypervolumes[acq_name] = [volume]
        
        # Main optimization loop
        for iteration in range(1, n_iterations + 1):
            if verbose:
                logger.info(f"\nIteration {iteration}/{n_iterations}")
            
            t0 = time.monotonic()
            
            # Fit models
            for acq_name in self.acquisition_functions:
                if acq_name != 'Random':
                    try:
                        fit_gpytorch_mll(mlls[acq_name])
                    except Exception as e:
                        if verbose:
                            logger.error(f"Warning: Failed to fit model for {acq_name}: {e}")
            
            # Create samplers
            samplers = {}
            for acq_name in self.acquisition_functions:
                if acq_name != 'Random':
                    samplers[acq_name] = SobolQMCNormalSampler(
                        sample_shape=torch.Size([self.mc_samples])
                    )
            
            # Optimize each acquisition function
            for acq_name in self.acquisition_functions:
                try:
                    storage = results[acq_name]
                    
                    if acq_name == 'qEHVI':
                        new_x, new_obj, new_obj_true = self.optimize_qehvi(
                            models[acq_name], storage.train_x, storage.train_obj, samplers[acq_name]
                        )
                    elif acq_name == 'qNEHVI':
                        new_x, new_obj, new_obj_true = self.optimize_qnehvi(
                            models[acq_name], storage.train_x, storage.train_obj, samplers[acq_name]
                        )
                    elif acq_name == 'qNParEGO':
                        new_x, new_obj, new_obj_true = self.optimize_qnparego(
                            models[acq_name], storage.train_x, storage.train_obj, samplers[acq_name]
                        )
                    elif acq_name == 'Random':
                        new_x, new_obj, new_obj_true = self.optimize_random()
                    
                    # Update training data using storage
                    storage.append_data(new_x, new_obj, new_obj_true)
                    
                    # Compute hypervolume
                    bd = DominatedPartitioning(
                        ref_point=self.problem.ref_point,
                        Y=storage.train_obj_true
                    )
                    volume = bd.compute_hypervolume().item()
                    hypervolumes[acq_name].append(volume)
                    
                    # Reinitialize model
                    if acq_name != 'Random':
                        mll, model = self.initialize_model(storage.train_x, storage.train_obj)
                        models[acq_name] = model
                        mlls[acq_name] = mll
                        
                except Exception as e:
                    if verbose:
                        logger.error(f"Warning: Failed optimization for {acq_name}: {e}")
                    # Add previous hypervolume to maintain consistency
                    hypervolumes[acq_name].append(hypervolumes[acq_name][-1])
            
            t1 = time.monotonic()
            
            if verbose:
                hv_str = ", ".join([
                    f"{name}: {hypervolumes[name][-1]:.3f}" 
                    for name in self.acquisition_functions
                ])
                logger.info(f"Hypervolumes - {hv_str}, time: {t1-t0:.2f}s")
        
        total_time = time.time() - start_time
        
        # Store results
        self.result = OptimizationResult(
            hypervolumes=hypervolumes,
            train_x={name: results[name].train_x for name in self.acquisition_functions},
            train_obj={name: results[name].train_obj for name in self.acquisition_functions},
            train_obj_true={name: results[name].train_obj_true for name in self.acquisition_functions},
            n_iterations=n_iterations,
            total_time=total_time
        )
        
        if verbose:
            logger.success(f"\nOptimization completed in {total_time:.2f}s")
            logger.success("\nFinal Hypervolumes:")
            for name in self.acquisition_functions:
                logger.info(f"  {name}: {hypervolumes[name][-1]:.4f}")
        
        return self.result