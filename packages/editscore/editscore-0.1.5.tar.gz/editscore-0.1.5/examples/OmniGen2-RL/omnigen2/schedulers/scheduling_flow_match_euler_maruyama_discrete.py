# Copyright 2024 Stability AI, Katherine Crowson and The HuggingFace Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

import numpy as np
import torch

from diffusers.configuration_utils import ConfigMixin, register_to_config
from diffusers.utils import BaseOutput, logging
from diffusers.utils.torch_utils import randn_tensor
from diffusers.schedulers.scheduling_utils import SchedulerMixin


logger = logging.get_logger(__name__)  # pylint: disable=invalid-name


def expand_as(tensor, other):
    """
    Expands a tensor to match the dimensions of another tensor.
    
    If tensor has shape [b] and other has shape [b, c, h, w],
    this function will reshape tensor to [b, 1, 1, 1] to enable broadcasting.
    
    Args:
        tensor (`torch.FloatTensor`): The tensor to expand
        other (`torch.FloatTensor`): The tensor whose shape will be matched
        
    Returns:
        `torch.FloatTensor`: The expanded tensor
    """
    for _ in range(other.ndim - tensor.ndim):
        tensor = tensor.unsqueeze(-1)
    return tensor

@dataclass
class FlowMatchEulerMaruyamaDiscreteSchedulerOutput(BaseOutput):
    """
    Output class for the scheduler's `step` function output.

    Args:
        prev_sample (`torch.FloatTensor` of shape `(batch_size, num_channels, height, width)` for images):
            Computed sample `(x_{t-1})` of previous timestep. `prev_sample` should be used as next model input in the
            denoising loop.
    """

    prev_sample: torch.FloatTensor
    log_prob: Optional[torch.FloatTensor] = None


class FlowMatchEulerMaruyamaDiscreteScheduler(SchedulerMixin, ConfigMixin):
    """
    Euler scheduler.

    This model inherits from [`SchedulerMixin`] and [`ConfigMixin`]. Check the superclass documentation for the generic
    methods the library implements for all schedulers such as loading and saving.

    Args:
        num_train_timesteps (`int`, defaults to 1000):
            The number of diffusion steps to train the model.
        timestep_spacing (`str`, defaults to `"linspace"`):
            The way the timesteps should be scaled. Refer to Table 2 of the [Common Diffusion Noise Schedules and
            Sample Steps are Flawed](https://huggingface.co/papers/2305.08891) for more information.
        shift (`float`, defaults to 1.0):
            The shift value for the timestep schedule.
    """

    _compatibles = []
    order = 1

    @register_to_config
    def __init__(
        self,
        num_train_timesteps: int = 1000,
        dynamic_time_shift: bool = True,
        sigma_schedule: str = "v1",
        sigma_coef: float = 0.7,
        time_shift_base_res: int = 320,
    ):
        timesteps = torch.linspace(0, 1, num_train_timesteps + 1, dtype=torch.float32)[:-1]
        self.time_shift_base_res = time_shift_base_res
        self.timesteps = timesteps

        self._step_index = None
        self._begin_index = None

    @property
    def step_index(self):
        """
        The index counter for current timestep. It will increase 1 after each scheduler step.
        """
        return self._step_index

    @property
    def begin_index(self):
        """
        The index for the first timestep. It should be set from pipeline with `set_begin_index` method.
        """
        return self._begin_index

    # Copied from diffusers.schedulers.scheduling_dpmsolver_multistep.DPMSolverMultistepScheduler.set_begin_index
    def set_begin_index(self, begin_index: int = 0):
        """
        Sets the begin index for the scheduler. This function should be run from pipeline before the inference.

        Args:
            begin_index (`int`):
                The begin index for the scheduler.
        """
        self._begin_index = begin_index

    def index_for_timestep(self, timestep, schedule_timesteps=None):
        if schedule_timesteps is None:
            schedule_timesteps = self._timesteps

        indices = (schedule_timesteps == timestep).nonzero()

        # The sigma index that is taken for the **very** first `step`
        # is always the second index (or the last index if there is only 1)
        # This way we can ensure we don't accidentally skip a sigma in
        # case we start in the middle of the denoising schedule (e.g. for image-to-image)
        pos = 1 if len(indices) > 1 else 0

        return indices[pos].item()
    
    # def time_shift(self, mu: float, sigma: float, t: torch.Tensor):
    #     return math.exp(mu) / (math.exp(mu) + (1 / t - 1) ** sigma)

    def set_timesteps(
        self,
        num_inference_steps: int = None,
        device: Union[str, torch.device] = None,
        timesteps: Optional[List[float]] = None,
        num_tokens: Optional[Union[int, List[int]]] = None
    ):
        """
        Sets the discrete timesteps used for the diffusion chain (to be run before inference).

        Args:
            num_inference_steps (`int`):
                The number of diffusion steps used when generating samples with a pre-trained model.
            device (`str` or `torch.device`, *optional*):
                The device to which the timesteps should be moved to. If `None`, the timesteps are not moved.
        """

        if timesteps is None:
            self.num_inference_steps = num_inference_steps
            if self.config.dynamic_time_shift and num_tokens is not None:
                if isinstance(num_tokens, list):
                    timesteps = []
                    for i in range(len(num_tokens)):
                        _timesteps = np.linspace(0, 1, num_inference_steps + 1, dtype=np.float32)[:-1]
                        m = np.sqrt(num_tokens[i]) / (self.config.time_shift_base_res / 8) # when input resolution is 320 * 320, m = 1, when input resolution is 1024 * 1024, m = 3.2
                        _timesteps = _timesteps / (m - m * _timesteps + _timesteps)

                        timesteps.append(_timesteps)
                    timesteps = np.stack(timesteps, axis=0)
                else:
                    timesteps = np.linspace(0, 1, num_inference_steps + 1, dtype=np.float32)[:-1]
                    m = np.sqrt(num_tokens) / (self.config.time_shift_base_res / 8) # when input resolution is 320 * 320, m = 1, when input resolution is 1024 * 1024, m = 3.2
                    timesteps = timesteps / (m - m * timesteps + timesteps)

        timesteps = torch.from_numpy(timesteps).to(dtype=torch.float32, device=device)
        if self.config.dynamic_time_shift and num_tokens is not None and isinstance(num_tokens, list):
            _timesteps = torch.cat([timesteps, torch.ones(len(num_tokens), 1, device=timesteps.device)], dim=1)
        else:
            _timesteps = torch.cat([timesteps, torch.ones(1, device=timesteps.device)])
        
        self.timesteps = timesteps
        self._timesteps = _timesteps
        self._step_index = None
        self._begin_index = 0

    def _init_step_index(self, timestep):
        if self.begin_index is None:
            if isinstance(timestep, torch.Tensor):
                timestep = timestep.to(self.timesteps.device)
            self._step_index = self.index_for_timestep(timestep)
        else:
            self._step_index = self._begin_index
        
    def get_sigma_t(self, t, t_next=None):
        if t_next is None:
            t_next = t
        def _get_sigma_t(t, t_next):
            if self.config.sigma_schedule == "v1":
                return 0.7 * math.sqrt((1 - t) / max(t, 1e-4))
            elif self.config.sigma_schedule == "v2":
                if t <= 0.2:
                    return (1 - t) ** 2
                else:
                    return (1 - t) ** 4
            elif self.config.sigma_schedule == "v3":
                return 0.7 * ((1 - t) / (t_next)) ** 0.5
            elif self.config.sigma_schedule == "v4":
                return torch.tensor(0.3, dtype=torch.float32, device=t.device)
            elif self.config.sigma_schedule == "zero":
                return torch.tensor(0, dtype=torch.float32, device=t.device)
            else:
                raise ValueError(f"Invalid sigma scheduler: {self.config.sigma_schedule}")
        if t.ndim > 0:
            return torch.stack([_get_sigma_t(_t, _t_next) for _t, _t_next in zip(t, t_next)])
        else:
            return _get_sigma_t(t, t_next)

    def step(
        self,
        model_output: torch.FloatTensor,
        timestep: Union[float, torch.FloatTensor],
        sample: torch.FloatTensor,
        generator: Optional[torch.Generator] = None,
        return_log_prob: bool = False,
        img_mask: Optional[torch.Tensor] = None,
        mixed_precision: bool = False,
        return_dict: bool = True,
    ) -> Union[FlowMatchEulerMaruyamaDiscreteSchedulerOutput, Tuple]:
        """
        Predict the sample from the previous timestep by reversing the SDE. This function propagates the diffusion
        process from the learned model outputs (most often the predicted noise).

        Args:
            model_output (`torch.FloatTensor`):
                The direct output from learned diffusion model.
            timestep (`float`):
                The current discrete timestep in the diffusion chain.
            sample (`torch.FloatTensor`):
                A current instance of a sample created by the diffusion process.
            s_churn (`float`):
            s_tmin  (`float`):
            s_tmax  (`float`):
            s_noise (`float`, defaults to 1.0):
                Scaling factor for noise added to the sample.
            generator (`torch.Generator`, *optional*):
                A random number generator.
            return_dict (`bool`):
                Whether or not to return a [`~schedulers.scheduling_euler_discrete.EulerDiscreteSchedulerOutput`] or
                tuple.

        Returns:
            [`~schedulers.scheduling_euler_discrete.EulerDiscreteSchedulerOutput`] or `tuple`:
                If return_dict is `True`, [`~schedulers.scheduling_euler_discrete.EulerDiscreteSchedulerOutput`] is
                returned, otherwise a tuple is returned where the first element is the sample tensor.
        """

        if (
            isinstance(timestep, int)
            or isinstance(timestep, torch.IntTensor)
            or isinstance(timestep, torch.LongTensor)
        ):
            raise ValueError(
                (
                    "Passing integer indices (e.g. from `enumerate(timesteps)`) as timesteps to"
                    " `EulerDiscreteScheduler.step()` is not supported. Make sure to pass"
                    " one of the `scheduler.timesteps` as a timestep."
                ),
            )

        if self.step_index is None:
            self._init_step_index(timestep)
        # Upcast to avoid precision issues when computing prev_sample
        sample = sample.to(torch.float32)
        t = self._timesteps[:, self.step_index]
        t_next = self._timesteps[:, self.step_index + 1]

        sigma_t = self.get_sigma_t(t, t_next if self.step_index == 0 else None)

        sigma_t = expand_as(sigma_t, sample)
        t = expand_as(t, sample)
        t_next = expand_as(t_next, sample)

        dt = t_next - t

        sigma_t = sigma_t.to(dtype=torch.float32)
        t = t.to(dtype=torch.float32)
        t_next = t_next.to(dtype=torch.float32)
        dt = dt.to(dtype=torch.float32)

        prev_sample_mean = (
            sample.to(dtype=torch.float32) * (1 - sigma_t**2 / (2 * (1 - t)) * dt)
            + model_output * (1 + sigma_t**2 * t / (2 * (1 - t))) * dt
        )
        variance_noise = randn_tensor(
            model_output.shape,
            generator=generator,
            device=sample.device,
            dtype=sample.dtype,
        )
        prev_sample = (
            prev_sample_mean + sigma_t * torch.sqrt(dt) * variance_noise
        )

        if img_mask is not None:
            img_mask = expand_as(img_mask, sample).expand(sample.shape)
            prev_sample = prev_sample * img_mask

        log_prob = None
        if return_log_prob:
            log_prob = (
                -((prev_sample.detach().to(dtype=torch.float32) - prev_sample_mean) ** 2)
                / (2 * ((sigma_t ** 2) * dt))
                - torch.log(sigma_t * torch.sqrt(dt))
                - 0.5 * torch.log(2 * torch.as_tensor(math.pi, device=sample.device))
            )

            log_prob = (log_prob * img_mask).sum(
                dim=tuple(range(-log_prob.ndim + 1, 0)), dtype=torch.float32
            ) / img_mask.sum(
                dim=tuple(range(-log_prob.ndim + 1, 0)), dtype=torch.float32
            )
        
        # Cast sample back to model compatible dtype
        if not mixed_precision:
            prev_sample = prev_sample.to(model_output.dtype)

        # upon completion increase step index by one
        self._step_index += 1

        if return_log_prob:
            if not return_dict:
                return (prev_sample, log_prob)

            return FlowMatchEulerMaruyamaDiscreteSchedulerOutput(prev_sample=prev_sample, log_prob=log_prob)
        else:
            if not return_dict:
                return (prev_sample,)

            return FlowMatchEulerMaruyamaDiscreteSchedulerOutput(prev_sample=prev_sample)

    def __len__(self):
        return self.config.num_train_timesteps