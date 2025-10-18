"""Python Module to contain the functions for performing resampling.

Resamplers all subclass ``pydpf.Module``
"""
import torch
from torch import Tensor
from typing import Tuple, Any
from .utils import batched_select
from .base import Module
from . import optimal_transport
from math import sqrt, log



class MultinomialResampler(Module):
    """Multinomial resampler.

        Resamples particles from the multinomial distribution. With

        Parameters
        ----------
        generator: torch.Generator
            The generator to track the random state of the resampling process.
    """
    def __init__(self, generator:torch.Generator):


        super().__init__()
        self.cache = {}
        self.generator = generator
        self._need_weight_output = True

    def forward(self, state:Tensor, weight:Tensor, **data):
        """Run the multinomial resampler."""
        with torch.no_grad():
            sampled_indices = torch.multinomial(torch.exp(weight), weight.size(1), replacement=True, generator=self.generator).detach()
            self.cache['used_weight'] = weight
            self.cache['sampled_indices'] = sampled_indices
        if self._need_weight_output:
            return batched_select(state, sampled_indices), torch.full(weight.size(), -log(weight.size(1)), device=weight.device, dtype=weight.dtype)
        return batched_select(state, sampled_indices)

class SystematicResampler(Module):
    """Systematic resampler.

        Under systematic resampling, the expected number of times a given particle is resampled is the same as for multinomial resampling. But it
        inter-correlates all the particles within a sample so it is difficult to provide the same theoretical guarantees on the asymptotic
        behaviour of filters that use systematic resampling compared to multinomial resampling. However, the stability offered by systematic
        resampling often results in better performance in practice.

        Parameters
        ----------
        generator: torch.Generator
            The generator to track the random state of the resampling process.

        Notes
        -----
        Equivalent to the Systematic resampler described in [1]_. Systematic resampling was first proposed in [2]_.
        Systematic resampling introduces strong dependence between particles and their index. Should the forward kernel be dependent on the
        particle index then the particles should be shuffled after resampling.

        References
        ----------
        .. [1] Chopin N, Papaspiliopoulos O (2020). An Introduction to Sequential Monte Carlo, chapter Importance Resampling, pp. 105–127. Springer.
        .. [2] Carpenter J, Clifford P, Fearnhead P (1999). “Improved particle filter for nonlinear problems.” In IEE Proc. Radar, Sonar and Navi., volume 146.
    """
    def __init__(self, generator:torch.Generator):
        super().__init__()
        self.cache = {}
        self.generator = generator
        self._need_weight_output = True

    def forward(self, state:Tensor, weight:Tensor, **data):
        """Run the systematic resampler."""
        with torch.no_grad():
            offset = torch.rand((weight.size(0),), device=state.device, generator=self.generator)
            cum_probs = torch.cumsum(torch.exp(weight), dim=1)
            # No index can be above 1. and the last index must be exactly 1.
            # Fix this in case of numerical errors
            cum_probs = torch.where(cum_probs > 1., 1., cum_probs)
            cum_probs[:, -1] = 1.
            resampling_points = torch.arange(weight.size(1), device=state.device) + offset.unsqueeze(1)
            sampled_indices = torch.searchsorted(cum_probs * weight.size(1), resampling_points)
            self.cache['used_weight'] = weight
            self.cache['sampled_indices'] = sampled_indices
        if self._need_weight_output:
            return batched_select(state, sampled_indices), torch.full(weight.size(), -log(weight.size(1)), device=weight.device, dtype=weight.dtype)
        return batched_select(state, sampled_indices)


class SoftResampler(Module):
    """Soft resampler.

    Module for perfoming soft-resampling, (P. Karkus, D. Hsu and W. S. Lee 'Particle Filter Networks with Application to
    Visual Localization' 2018).

    Soft resampling allows gradients to be passed through resampling by inducing importance weights. This is done by instead drawing the
    resampled particle from an alternative distribution and re-weighting the samples. The chosen alternative distribution is a mixture of
    the target with probability a; and a uniform distribution over the particles, with probability 1-a.

    The ``softness`` parameter, can be thought of as trading off between unbiased gradients (``softness`` = 0) and efficient resampling (``softness`` = 1). With
    ``softness`` > 0, the resampled index depends (randomly) on the previous weights. The contribution to the gradient from this dependence is ignored.

    Parameters
    ----------
    softness:  float
        The trade-off parameter between unbiased gradients (``softness`` = 0) and efficient resampling (``softness`` = 1).
    base_resampler: Module
        The base resampler to use.
    device: torch.device.
        The device that filtering is performed on

    Notes
    -----
    Proposed in [1]_. Like many of the resamplers in PyDPF this resampler acts on top of another resampler, generally this should be either ``MultinomialResampler``, ``SystematicResampler`` or ``OptimalTransportResampler``.
    Stacking other resamplers should be done with great care and in the order: -- Resamplers that modify gradient computation above Resamplers that modify the weights above Resamplers that modify the distribution
    for given weights) --. But it will nearly always be safer to define a new resampler with the desired behaviour than to stack exotic resamplers.

    References
    ----------
    .. [1] Karkus P, Hsu D, Lee WS (2018). “Particle filter networks with application to visual localization.” In Proc. Conf. Robot Learn., pp. 169–178. PMLR, Zurich, CH.
    """

    def __new__(cls, softness:float, base_resampler:Module, device:torch.device):
        if softness == 1:
            return base_resampler
        else:
            return super().__new__(cls)

    def __init__(self, softness:float, base_resampler:Module, device:torch.device):
        super().__init__()
        self.cache = {}
        self.softness = softness
        if softness < 0 or softness >= 1:
            raise ValueError(f'Softness {softness} is out of range, must be in [0,1)')
        self.log_softness = torch.log(torch.tensor(softness, device = device))
        self.neg_log_softness = torch.log(torch.tensor(1-softness ,device = device))
        self.resampler = base_resampler
        self._need_weight_output = True

    def forward(self, state:Tensor, weight:Tensor, **data):
        """Run the soft-resampler"""
        log_n = torch.log(torch.tensor(weight.size(1), device=state.device))
        soft_weight = torch.logaddexp(weight + self.log_softness, self.neg_log_softness - log_n)
        state, output_weights = self.resampler(state, soft_weight)
        self.cache = self.resampler.cache
        if self._need_weight_output:
            return state, batched_select(weight, self.cache['sampled_indices']) - batched_select(self.cache['used_weight'], self.cache['sampled_indices']) - log_n
        return state


class StopGradientResampler(Module):
    '''Stop-gradient resampling

    Stop-gradient resampling uses the REINFORCE or score-based Monte-Carlo gradient technique applied at each time-step.
    For numerical stability our implementation attaches the gradients to the log-space weights, rather than the linear-space particles.

    Parameters
    ----------
    generator: torch.Generator
        The generator to track the random state of the resampling process.

    Notes
    -----
    REINFORCE is unbiased after a single application but not so when applied in series as we do here when ``time_extent`` > 1.
    Proposed in [1]_. Like many of the resamplers in PyDPF this resampler acts on top of another resampler, generally this should be either ``MultinomialResampler``, ``SystematicResampler`` or ``OptimalTransportResampler``.
    Stacking other resamplers should be done with great care and in the order: -- Resamplers that modify gradient computation above Resamplers that modify the weights above Resamplers that modify the distribution
    for given weights) --. But it will nearly always be safer to define a new resampler with the desired behaviour than to stack exotic resamplers.

    References
    ----------
    .. [1] Scibior A, Wood F (2021). “Differentiable particle filtering without modifying the forward pass.” arXiv:2106.10314
    '''
    def __init__(self, base_resampler:Module):
        super().__init__()
        self.cache = {}
        self.base_resampler = base_resampler
        self._need_weight_output = True

    def forward(self, state:Tensor, weight:Tensor, **data):
        """Run the stop-gradient resampler"""

        if self._need_weight_output and torch.is_grad_enabled():
            self.base_resampler._need_weight_output = True
            state, new_weight = self.base_resampler(state, weight)
            resampled_weight = batched_select(self.base_resampler.cache['used_weight'], self.base_resampler.cache['sampled_indices'])
            self.cache = self.base_resampler.cache
            self.cache['used_weight'] = self.cache['used_weight'].detach()
            return state, new_weight + resampled_weight - resampled_weight.detach()

        if self._need_weight_output:
            self.base_resampler._need_weight_output = True
            state, new_weight = self.base_resampler(state, weight)
            self.cache = self.base_resampler.cache
            return state, new_weight

        self.base_resampler._need_weight_output = False
        state = self.base_resampler(state, weight)
        self.cache = self.base_resampler.cache
        return state

class OptimalTransportResampler(Module):
    r"""Optimal transport based resampling


        Optimal transport resampling produces a differentiable deterministic transport map from the proposal distribution to the posterior.
        This is achieved by finding the solution to an entropy regularised Kantorovich optimal transport problem between the two empirical
        distributions. The particles are transformed by the resulting optimal map to obtain a new unweighted approximation of the posterior.


        Parameters
        ----------
        regularisation: float
            The minimum strength of the entropy regularisation, in our implementation regularisation automatically chosen per sample and
             exponentially decayed to this value.
        decay_rate: float
            The factor by which to decrease the entropy regularisation per Sinkhorn loop.
        min_update_size: float
            The size of update to the transport potentials below which iteration should stop.
        max_iterations: int
            The maximum number iterations of the Sinkhorn loop, before stopping. Regardless of convergence.
        transport_gradient_clip: float
            The maximum per-element gradient of the transport matrix that should be passed. Higher valued gradients will be clipped to this value.

        Notes
        -----
        Our implementation is closely based on the original code of Thornton and Corenflos, the following details being taken from theirs:
        We exponentially decay the regularisation strength over the Sinkhorn iterations.
        We chose the initial strength of the regularisation parameter to be equal to maximum value minus the minimum value in the particle-state 2D array of the particle positions after each dimension is normalised to standard deviation 1.
        For numerical stability we cap the magnitude of the contribution to the gradient due to the transport matrix.

        Optimal transport resampling places particles in new positions on :math:`\mathbb{R}^n`, so it cannot directly be applied when some component of
        the state space is discrete/categorical.

        Optimal transport resampling results in biased (but asymptotically consistent) estimates of all non-affine functions of the latent state.
        Including the likelihood. The authors of the proposing paper investigate this effect and find it sufficiently small to ignore. See their
        paper [1]_ for details.
        """

    def __init__(self, regularisation: float, decay_rate: float, min_update_size: float, max_iterations: int, transport_gradient_clip: float):
        super().__init__()
        self.cache = {}
        self.regularisation = regularisation
        self.decay_rate = decay_rate
        self.min_update_size = min_update_size
        self.max_iterations = max_iterations
        self._need_weight_output = True

        class OTGradientWrapper(torch.autograd.Function):
            """
            Optimal transport gradient can suffer from numerical instability.
            Clip the gradient of the loss wrt the transport matrix to some user specified value.
            This is done in Corenflos and Thornton's original implementation.
            """

            @staticmethod
            def forward(ctx: Any, transport_matrix: Tensor):
                return transport_matrix

            @staticmethod
            def backward(ctx: Any, dtransport) -> Any:
                return torch.clip(dtransport, -transport_gradient_clip, transport_gradient_clip)

        self.gradient_wrapper = OTGradientWrapper

    @staticmethod
    def diameter(x: Tensor):
        """
        Calculates the diameter of the data.
        The diameter is defined as the maximum of the standard deviation across a sample across data dimensions.

        Parameters
        ----------
        x: Tensor
            Input tensor.

        Returns
        -------
        diameter: Tensor
            The diameter of the data per batch.
        """
        diameter_x = torch.amax(x.std(dim=1, unbiased=False), dim=-1, keepdim=True)
        return torch.where(torch.eq(diameter_x, 0.), 1., diameter_x)

    @staticmethod
    def extent(x: Tensor):
        return torch.amax(x, dim=(1,2)) - torch.amin(x, dim=(1,2))

    @staticmethod
    def get_sinkhorn_inputs_OT(Nk, log_weight: Tensor, x_t: Tensor) -> Tuple[Tensor, Tensor, Tensor]:
        """
        Get the inputs to the Sinkhorn algorithm as used for OT resampling

        Parameters
        ----------
        log_weights: (B,N) Tensor
            The particle weights

        N: int
            Number of particles

        x_t: (B,N,D) Tensor
            The particle state

        Returns
        -------
        log_uniform_weights: (B,N) Tensor
            A tensor of log(1/N)

        cost_matrix: (B, N, N) Tensor
            The auto-distance matrix of scaled_x_t under the 2-Norm.

        scale_x: (B, N, D) Tensor
            The amount the particles where scaled by in calculating the cost matrix.
        """
        log_uniform_weight = torch.log(torch.ones((log_weight.size(0), Nk), device=log_weight.device) / Nk)
        centred_x_t = x_t - torch.mean(x_t, dim=1, keepdim=True).detach()
        scale_x = OptimalTransportResampler.diameter(x_t).detach() * sqrt(x_t.size(-1))
        scaled_x_t = centred_x_t / scale_x.unsqueeze(2)
        cost_matrix = torch.cdist(scaled_x_t, scaled_x_t, 2) ** 2
        extent = OptimalTransportResampler.extent(scaled_x_t)
        return log_uniform_weight, cost_matrix, extent


    def forward(self, state: Tensor, weight: Tensor, **data):
        """Run the optimal transport resampler."""
        N = state.size(1)
        log_b, cost, extent = self.get_sinkhorn_inputs_OT(N, weight, state)
        f, g, epsilon_used = optimal_transport.sinkhorn_loop(weight, log_b, cost, self.regularisation, self.min_update_size, self.max_iterations, extent.reshape(-1, 1, 1), self.decay_rate)
        transport = optimal_transport.get_transport_from_potentials(weight, log_b, cost, f, g, self.regularisation)
        transport = self.gradient_wrapper.apply(transport)
        self.cache['used_weight'] = weight
        if self._need_weight_output:
            return optimal_transport.apply_transport(state, transport, N), torch.full(weight.size(), -log(weight.size(1)), device=weight.device, dtype=weight.dtype)
        return optimal_transport.apply_transport(state, transport, N)

class KernelResampler(Module):


    def __init__(self, kernel):
        """
            Returns a function for performing differentiable kernel resampling (Younis and Sudderth 'Differentiable and Stable Long-Range Tracking of Multiple Posterior Modes' 2024).

            Notes
            -----
            Unlike the majority of implemented resampling schemes this function returns a Module object so that learnable parameters may be properly registered.
            In this case the final returned field is always a tensor containing a single zero.

            Parameters
            ----------
            kernel: Distribution
                The kernel to convolve over the particles to form the KDE sampling distribution.
            generator: torch.Generator
                The generator to track the random state of the resampling process.

            Returns
            -------
            kernel_resampler: Resampler:
                A Module whose forward method implements kernel resampling.
        """
        super().__init__()
        self.mixture = kernel
        self.cache = {}
        self._need_weight_output = True

    def forward(self, state: Tensor, weight: Tensor, **data):
        """Run the kernel transport resampler."""
        with torch.no_grad():
            new_state = self.mixture.sample(state, weight, sample_size=(state.size(1),))
            self.cache = self.mixture.resampler.cache
        # Save computation if gradient is not required
        if torch.is_grad_enabled() and self._need_weight_output:
            density = self.mixture.log_density(new_state, state, weight)
            new_weight = density - density.detach()
            return new_state, new_weight

        if self._need_weight_output:
            return new_state, torch.full(weight.size(), -log(weight.size(1)), device=weight.device, dtype=weight.dtype)

        return new_state