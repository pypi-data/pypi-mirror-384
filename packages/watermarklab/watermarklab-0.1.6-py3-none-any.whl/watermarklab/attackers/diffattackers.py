# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT

import math
import cv2
import torch
import kornia
import random
import itertools
import numpy as np
import torch.nn as nn
from torch import Tensor
import torch.nn.functional as F
from kornia.filters import MedianBlur
from torchvision.transforms import transforms
import torchvision.transforms.functional as Fs

from watermarklab.utils.basemodel import BaseDiffAttackModel
from watermarklab.attackers.utils_printcapture import random_blur_kernel, get_rnd_brightness_torch, \
    jpeg_compress_decompress, \
    round_only_at_0

__all__ = ["Identity", "GaussianBlur", "MedianFilter",
           "GaussianNoise", "JpegMask", "JpegFourier", "JpegPolynomial",
           "FieldOfViewTransformer", "RandomCompensateTransformer",
           "Dropout", "Cropout", "Crop", "Contrast", "PIMoG",
           "Hue", "Brightness", "Saturation", "Resize", "Rotate",
           "StegaStamp", "UnsharpMasking", "MotionBlur",
           "PoissonNoise", "ColorQuantization", "SaltPepperNoise",
           "ChromaticAberration", "GammaCorrection", "SpeckleNoise",
           "RandomFlipping", "RandomTranslation", "RandomAffine"]


class Identity(BaseDiffAttackModel):
    def __init__(self, test: bool = False, max_step: int = 100, noisename: str = "Identity"):
        super().__init__(noisename)

    def forward(self, marked_img, cover_img: Tensor = None, now_step: int = 0):
        return marked_img

    def test(self, marked_img, cover_img: Tensor = None, now_step: int = 0):
        return marked_img


class RandomAffine(BaseDiffAttackModel):
    """
    A wrapper class that integrates torchvision's RandomAffine transform
    into a differentiable attack/distortion module compatible with
    GPU tensors and batched inputs (note: only works correctly with
    torchvision v2 or when input is properly handled as PIL/float tensor).

    """

    def __init__(
            self,
            degrees: float = 60.0,
            translate: tuple = (0.3, 0.3),
            scale: tuple = (0.7, 1.3),
            shear: float = 30,
            fill: float = 0,
            noise_name: str = "RandomAffine"
    ):
        """
        Initialize the RandomAffine distortion module.

        Args:
            degrees (float):
                Range of random rotation in degrees. The image will be rotated
                by an angle uniformly sampled from [-degrees, +degrees].
            translate (tuple of float):
                Maximum absolute fraction of translation in (horizontal, vertical)
                directions. For example, (0.3, 0.3) allows shifting up to 30% of
                width/height in each direction.
            scale (tuple of float):
                Scaling factor range. The image will be scaled by a factor
                uniformly sampled from [scale[0], scale[1]].
            shear (float):
                Range of random shear in degrees. Shear is applied as a tilt
                transformation (e.g., simulating slanted text or perspective skew).
            fill (float):
                Pixel fill value for areas outside the transformed image.
                Typically 0 for grayscale or (0,0,0) for RGB (though this implementation
                uses a scalar; for multi-channel, ensure compatibility).
            noise_name (str):
                Name identifier for this distortion type (used for logging or debugging).
        """
        super().__init__(noise_name)
        self.noise_name = noise_name
        # Create the torchvision RandomAffine transform
        self.random_affine = transforms.RandomAffine(
            degrees=degrees,
            translate=translate,
            scale=scale,
            shear=shear,
            fill=fill
        )

    def forward(
            self,
            stego_img: torch.Tensor,
            cover_img: torch.Tensor = None,
            now_step: int = 0
    ) -> torch.Tensor:
        """
        Forward pass during training. Applies random affine transformation
        to the input stego image.

        Args:
            stego_img (torch.Tensor):
                Input tensor of shape (N, C, H, W) or (C, H, W), typically in [0, 1] range.
            cover_img (torch.Tensor, optional):
                Cover image (not used in this distortion).
            now_step (int):
                Current training step (not used here).

        Returns:
            torch.Tensor: Affine-transformed image tensor of the same shape as input.
        """
        return self.test(stego_img, cover_img)

    def test(
            self,
            stego_img: torch.Tensor,
            cover_img: torch.Tensor = None,
            factor: float = None
    ) -> torch.Tensor:
        """
        Apply random affine distortion to the input image.

        Note:
        - This method directly calls torchvision's RandomAffine.
        - Ensure input tensor is compatible (e.g., float in [0, 1],
          and either single image or handled appropriately).
        - For batched GPU tensors in PyTorch >= 2.0, consider using
          torchvision.transforms.v2 for native support.

        Args:
            stego_img (torch.Tensor): Input image tensor.
            cover_img (torch.Tensor, optional): Ignored.
            factor (float, optional): Intensity scaling factor (not used in this implementation).

        Returns:
            torch.Tensor: Distorted image after random affine transformation.
        """
        # Apply the random affine transform
        transformed = self.random_affine(stego_img)
        return transformed


class RandomTranslation(BaseDiffAttackModel):
    """
    A differentiable random translation distortion layer that randomly shifts
    the input image horizontally and/or vertically by a percentage of its width/height.

    Uses affine transformation for more accurate translation.
    """

    def __init__(
            self,
            max_hshift_percent: float = 0.1,
            max_vshift_percent: float = 0.1,
            padding_mode: str = 'zeros',
            noise_name: str = "RandomTranslation"
    ):
        """
        Initialize the RandomTranslationDistortion layer.

        Args:
        - max_hshift_percent: float - Max horizontal shift as fraction of width (0.0 ~ 1.0).
        - max_vshift_percent: float - Max vertical shift as fraction of height (0.0 ~ 1.0).
        - padding_mode: str - Padding mode: 'zeros', 'border', 'reflection'.
        - noise_name: str - Name for the noise model.
        """
        super().__init__(noise_name)
        self.max_hshift_percent = max_hshift_percent
        self.max_vshift_percent = max_vshift_percent
        self.padding_mode = padding_mode
        self.noise_name = noise_name

    def forward(
            self,
            stego_img: torch.Tensor,
            cover_img: torch.Tensor = None,
            now_step: int = 0
    ) -> torch.Tensor:
        """
        Apply random translation to the input image.

        Args:
        - stego_img: Tensor - Input image tensor with shape (N, C, H, W).
        - cover_img: Tensor - Optional, not used.
        - now_step: int - Current training step (unused).

        Returns:
        - Tensor - Translated image tensor with shape (N, C, H, W).
        """
        return self.test(stego_img, cover_img)

    def test(
            self,
            stego_img: torch.Tensor,
            cover_img: torch.Tensor = None,
            factor: float = None
    ) -> torch.Tensor:
        """
        Apply random horizontal and vertical translations using affine transformation.

        Args:
        - stego_img: Tensor - Input image tensor (N, C, H, W).
        - cover_img: Tensor - Ignored.
        - factor: float - Optional scaling factor for shift magnitude (e.g., 1.0 for max).

        Returns:
        - Tensor - Distorted image after random translation.
        """
        if self.max_hshift_percent == 0.0 and self.max_vshift_percent == 0.0:
            return stego_img

        N, C, H, W = stego_img.shape

        # Determine actual shift values
        if factor is None:
            max_h_pixels = W * self.max_hshift_percent
            max_v_pixels = H * self.max_vshift_percent
            hshift = torch.empty(N).uniform_(-max_h_pixels, max_h_pixels)
            vshift = torch.empty(N).uniform_(-max_v_pixels, max_v_pixels)
        else:
            h_direction = torch.randint(0, 2, (N,)) * 2 - 1  # -1 or 1
            v_direction = torch.randint(0, 2, (N,)) * 2 - 1  # -1 or 1
            hshift = h_direction.float() * W * factor
            vshift = v_direction.float() * H * factor

        # Create affine transformation matrices
        # For translation: [[1, 0, dx], [0, 1, dy]]
        # In PyTorch, affine_grid expects [N, 2, 3] where each 2x3 matrix is:
        # [[1, 0, dx/W*2], [0, 1, dy/H*2]] (normalized to [-1, 1] coordinate system)
        theta = torch.zeros(N, 2, 3, device=stego_img.device, dtype=stego_img.dtype)
        theta[:, 0, 0] = 1.0  # scale x
        theta[:, 1, 1] = 1.0  # scale y
        # Normalize shifts to [-1, 1] coordinate system
        theta[:, 0, 2] = hshift / (W / 2)  # dx
        theta[:, 1, 2] = vshift / (H / 2)  # dy

        # Create sampling grid
        grid = F.affine_grid(theta, stego_img.size(), align_corners=True)

        # Apply transformation
        # Map padding_mode to F.grid_sample compatible mode
        padding_map = {
            'zeros': 'zeros',
            'border': 'border',
            'reflection': 'reflection',
            'reflect': 'reflection'
        }
        mode = padding_map.get(self.padding_mode, 'zeros')

        translated = F.grid_sample(
            stego_img,
            grid,
            mode='bilinear',
            padding_mode=mode,
            align_corners=True
        )

        return translated


class SpeckleNoise(BaseDiffAttackModel):
    """
    A differentiable speckle noise layer that adds multiplicative noise to the input image.

    Attributes:
    - factor: float - The intensity of the speckle noise.
                    Higher values result in more noise.
                    Typically, factor should range from 0.1 to 1.0.
    - max_step: int - Maximum number of steps for dynamic factor scaling.
    """

    def __init__(self, sigma: float = 0.5, max_step: int = 1000, noisename: str = "SpeckleNoise"):
        """
        Initialize the SpeckleNoise layer.

        Args:
        - factor: float - The intensity of the speckle noise (default: 0.5).
        - max_step: int - Maximum number of steps for dynamic factor scaling (default: 1000).
        - noisename: str - Name of the noise model (default: "SpeckleNoise").
        """
        super().__init__(noisename)
        self.factor = sigma
        self.max_step = max_step

    def forward(self, stego_img: Tensor, cover_img: Tensor = None, now_step: int = 0) -> Tensor:
        """
        Apply speckle noise with a dynamically adjusted factor based on now_step.

        Args:
        - stego_img: Tensor - Input image tensor with shape (N, C, H, W).
        - cover_img: Tensor - Optional, not used in this implementation.
        - now_step: int - Current step for scaling the noise factor.

        Returns:
        - Tensor - The noisy image tensor with shape (N, C, H, W).
        """
        # Dynamically scale the factor from 0 to self.factor based on now_step
        current_factor = self.factor * (min(now_step, self.max_step) / self.max_step)
        return self.test(stego_img, cover_img, factor=current_factor)

    def test(self, stego_img: Tensor, cover_img: Tensor = None, factor: float = None) -> Tensor:
        """
        Apply speckle noise with a specified factor.

        Args:
        - stego_img: Tensor - Input image tensor with shape (N, C, H, W).
        - cover_img: Tensor - Optional, not used in this implementation.
        - factor: float - The intensity of the speckle noise.

        Returns:
        - Tensor - The noisy image tensor with shape (N, C, H, W).
        """
        if factor is None:
            factor = self.factor

        # Ensure the input image is in the range [0, 1]
        stego_img = torch.clamp(stego_img, 0.0, 1.0)

        # Generate multiplicative noise (speckle noise)
        noise = torch.randn_like(stego_img) * factor

        # Add speckle noise to the image
        noised_img = stego_img + stego_img * noise.to(stego_img.device)

        # Clamp the result to the valid range [0, 1]
        noised_img = torch.clamp(noised_img, 0.0, 1.0)

        return noised_img


class ColorQuantization(BaseDiffAttackModel):
    """
    Color quantization reduces the number of colors in an image by approximating pixel values
    to the nearest multiple of the factor. This is a fully differentiable version using a
    soft quantization approach in PyTorch.

    Attributes:
    - factor: int - The maximum quantization factor.
                    Higher values result in more color reduction (fewer distinct colors).
                    Typically, factor should range from 4 to 32.
    - max_step: int - Maximum number of steps for dynamic factor scaling.
    """

    def __init__(self, factor: int = 16, max_step: int = 1000, noisename: str = "ColorQuantization"):
        """
        Initialize the differentiable ColorQuantization class.

        Args:
        - factor: int - The maximum quantization factor (typically 4 to 32).
        - max_step: int - Maximum number of steps for dynamic factor scaling in forward.
        """
        super().__init__(noisename)  # Assuming BaseDiffAttackModel inherits from nn.Module
        self.factor = max(4, min(32, factor))  # Clamp factor between 4 and 32
        self.max_step = max_step

    def forward(self, stego_img: Tensor, cover_img: Tensor = None, now_step: int = 0) -> Tensor:
        """
        Apply differentiable color quantization with a dynamically adjusted factor based on now_step,
        delegating the core computation to the test method.

        Args:
        - stego_img: Tensor - Input image tensor with shape (N, C, H, W).
        - cover_img: Tensor - Optional, not used in this implementation.
        - now_step: int - Current step for scaling the quantization factor.

        Returns:
        - Tensor - The color-quantized image tensor with shape (N, C, H, W).
        """
        # Dynamically scale the factor from 1 (no quantization) to self.factor based on now_step
        current_factor = int((min(now_step, self.max_step) / self.max_step) * self.factor)
        return self.test(stego_img, cover_img, factor=current_factor)

    def test(self, stego_img: Tensor, cover_img: Tensor = None, factor=None) -> Tensor:
        """
        Core computation for color quantization with a specified factor using a differentiable
        soft quantization approximation.

        Args:
        - stego_img: Tensor - Input image tensor with shape (N, C, H, W).
        - cover_img: Tensor - Optional, not used in this implementation.
        - factor: float - The quantization factor determining color reduction.

        Returns:
        - Tensor - The color-quantized image tensor with shape (N, C, H, W).
        """
        if factor is None:
            factor = self.factor
        stego_img = stego_img * 255.
        # Compute a soft quantization using a sigmoid-based interpolation
        noised_img = stego_img / factor + (stego_img // factor - stego_img / factor).detach()
        noised_img = torch.clamp(noised_img * factor / 255., 0, 1)
        return noised_img


class ChromaticAberration(BaseDiffAttackModel):
    """
    Chromatic aberration introduces a color distortion effect by shifting the red and blue channels.
    This is a differentiable version implemented using PyTorch. For grayscale images (C=1),
    the effect is skipped, returning the input unchanged.

    Attributes:
    - factor: int - The maximum shift amount for the red and blue channels.
                    The higher the factor, the greater the shift.
                    Typically, factor should range from 1 to 10.
    - max_step: int - Maximum number of steps for dynamic factor scaling.
    """

    def __init__(self, factor: int = 2, max_step: int = 1000, noisename: str = "ChromaticAberration"):
        """
        Initialize the differentiable ChromaticAberration class.

        Args:
        - factor: int - The maximum shift amount in pixels (typically 1 to 10).
        - max_step: int - Maximum number of steps for dynamic factor scaling in forward.
        """
        super().__init__(noisename)  # Assuming BaseDiffAttackModel inherits from nn.Module
        self.factor = max(1, min(10, factor))  # Clamp factor between 1 and 10
        self.max_step = max_step

    def forward(self, stego_img: Tensor, cover_img: Tensor = None, now_step: int = 0) -> Tensor:
        """
        Apply differentiable chromatic aberration with a dynamically adjusted shift based on now_step,
        delegating the core computation to the test method.

        Args:
        - stego_img: Tensor - Input image tensor with shape (N, C, H, W), where C=1 (grayscale) or C=3 (RGB).
        - cover_img: Tensor - Optional, not used in this implementation.
        - now_step: int - Current step for scaling the shift factor.

        Returns:
        - Tensor - The image tensor with chromatic aberration (RGB) or unchanged (grayscale), shape (N, C, H, W).
        """
        # Dynamically scale the factor from 0 (no shift) to self.factor based on now_step
        current_factor = int((min(now_step, self.max_step) / self.max_step) * self.factor)
        # Call test with the dynamically computed factor
        return self.test(stego_img, cover_img, factor=current_factor)

    def test(self, stego_img: Tensor, cover_img: Tensor = None, factor=None) -> Tensor:
        """
        Core computation for chromatic aberration with a specified shift factor.
        For grayscale images (C=1), returns the input unchanged.

        Args:
        - stego_img: Tensor - Input image tensor with shape (N, C, H, W), where C=1 or C=3.
        - cover_img: Tensor - Optional, not used in this implementation.
        - factor: int - The number of pixels to shift the red and blue channels.

        Returns:
        - Tensor - The image tensor with chromatic aberration (RGB) or unchanged (grayscale), shape (N, C, H, W).
        """
        if factor is None:
            factor = self.factor
        # Check if the image is grayscale (C=1)
        if stego_img.shape[1] == 1:
            return stego_img  # No chromatic aberration for grayscale, return unchanged

        # Split channels assuming C=3 (R, G, B order in tensor)
        r, g, b = stego_img[:, 0:1, :, :], stego_img[:, 1:2, :, :], stego_img[:, 2:3, :, :]

        # Create shift kernels for red (left) and blue (right)
        kernel_size = 2 * factor + 1  # Ensure odd size for centered kernel
        r_kernel = torch.zeros(1, 1, 1, kernel_size, device=stego_img.device).to(stego_img.device)
        r_kernel[0, 0, 0, factor - factor] = 1.0  # Shift left by factor
        b_kernel = torch.zeros(1, 1, 1, kernel_size, device=stego_img.device).to(stego_img.device)
        b_kernel[0, 0, 0, factor + factor] = 1.0  # Shift right by factor

        # Apply convolution to shift red and blue channels
        padding = factor  # Pad to maintain size
        r_shifted = F.conv2d(r, r_kernel, padding=(0, padding), groups=1)
        b_shifted = F.conv2d(b, b_kernel, padding=(0, padding), groups=1)

        # Combine shifted channels with unchanged green channel
        noised_img = torch.cat([r_shifted, g, b_shifted], dim=1)

        # Clip values to the valid range [0, 255]
        noised_img = torch.clamp(noised_img, 0, 1)

        return noised_img


class GammaCorrection(BaseDiffAttackModel):
    """
    Gamma correction adjusts the brightness of an image using a gamma curve.
    This is a differentiable version implemented using PyTorch.

    Attributes:
    - factor: float - The maximum gamma value.
                      A value > 1 brightens the image, a value < 1 darkens it.
                      Typically, factor should range from 0.1 to 3.0.
    - max_step: int - Maximum number of steps for dynamic factor scaling.
    """

    def __init__(self, factor: float = 0.5, max_step: int = 1000, noisename: str = "GammaCorrection"):
        """
        Initialize the differentiable GammaCorrection class.

        Args:
        - factor: float - The maximum gamma value for brightness adjustment (typically 0.1 to 3.0).
        - max_step: int - Maximum number of steps for dynamic factor scaling in forward.
        """
        super().__init__(noisename)
        self.factor = factor
        self.max_step = max_step

    def forward(self, stego_img: Tensor, cover_img: Tensor = None, now_step: int = 0) -> Tensor:
        """
        Apply differentiable gamma correction with a dynamically adjusted factor based on now_step,
        delegating the core computation to the test method.

        Args:
        - stego_img: Tensor - Input image tensor with shape (N, C, H, W).
        - cover_img: Tensor - Optional, not used in this implementation.
        - now_step: int - Current step for scaling the gamma factor.

        Returns:
        - Tensor - The gamma-corrected image tensor with shape (N, C, H, W).
        """
        # Dynamically scale the factor from 1.0 (no change) to self.factor based on now_step
        current_factor = 1 + (min(now_step, self.max_step) / self.max_step) * self.factor
        rdn_factor = random.uniform(max(1e-5, 1 / current_factor), current_factor)  # Ensure gamma > 0

        # Call test with the dynamically computed factor
        return self.test(stego_img, cover_img, gamma=rdn_factor)

    def test(self, stego_img: Tensor, cover_img: Tensor = None, gamma=None) -> Tensor:
        """
        Core computation for gamma correction with a specified factor.

        Args:
        - stego_img: Tensor - Input image tensor with shape (N, C, H, W).
        - cover_img: Tensor - Optional, not used in this implementation.
        - gamma: float - The gamma value for brightness adjustment.

        Returns:
        - Tensor - The gamma-corrected image tensor with shape (N, C, H, W).
        """
        if gamma is None:
            gamma = self.factor
        gamma = max(1e-5, gamma)  # Ensure gamma > 0

        # Normalize image to [0, 1] range
        stego_img = torch.clamp(stego_img, 0.0, 1.0)

        # Apply gamma correction
        noised_img = torch.pow(stego_img, gamma)

        # Clip values to the valid range [0, 1]
        noised_img = torch.clamp(noised_img, 0.0, 1.0)
        return noised_img


class PoissonNoise(BaseDiffAttackModel):
    """
    A differentiable Poisson noise layer that adds Poisson-distributed noise to the input image.

    Attributes:
    - factor: float - The intensity of the Poisson noise.
                    Higher values result in more noise.
                    Typically, factor should range from 0.1 to 10.0.
    - max_step: int - Maximum number of steps for dynamic factor scaling.
    """

    def __init__(self, factor: float = 0.3, max_step: int = 1000, noisename: str = "PoissonNoise"):
        """
        Initialize the PoissonNoise layer.

        Args:
        - factor: float - The intensity of the Poisson noise (default: 1.0).
        - max_step: int - Maximum number of steps for dynamic factor scaling (default: 1000).
        - noisename: str - Name of the noise model (default: "PoissonNoise").
        """
        super().__init__(noisename)
        self.factor = factor
        self.max_step = max_step

    def forward(self, stego_img: Tensor, cover_img: Tensor = None, now_step: int = 0) -> Tensor:
        """
        Apply Poisson noise with a dynamically adjusted factor based on now_step.

        Args:
        - stego_img: Tensor - Input image tensor with shape (N, C, H, W).
        - cover_img: Tensor - Optional, not used in this implementation.
        - now_step: int - Current step for scaling the noise factor.

        Returns:
        - Tensor - The noisy image tensor with shape (N, C, H, W).
        """
        # Dynamically scale the factor from 0 to self.factor based on now_step
        current_factor = self.factor * (min(now_step, self.max_step) / self.max_step)
        rdn_factor = 1 + random.uniform(-current_factor, current_factor)
        return self.test(stego_img, cover_img, factor=rdn_factor)

    def test(self, stego_img: Tensor, cover_img: Tensor = None, factor: float = None) -> Tensor:
        """
        Apply Poisson noise with a specified factor.

        Args:
        - stego_img: Tensor - Input image tensor with shape (N, C, H, W).
        - cover_img: Tensor - Optional, not used in this implementation.
        - factor: float - The intensity of the Poisson noise.

        Returns:
        - Tensor - The noisy image tensor with shape (N, C, H, W).
        """
        if factor is None:
            factor = self.factor

        # Ensure the input image is in the range [0, 1]
        stego_img = torch.clamp(stego_img, 0.0, 1.0)

        # Scale the image to the range [0, 255] for Poisson noise
        scaled_img = stego_img * 255.0

        # Generate Poisson noise with intensity proportional to the image pixel values
        noised_img = torch.poisson(scaled_img * factor) / 255.0

        # Clamp the result to the valid range [0, 1]
        noised_img = torch.clamp(noised_img, 0.0, 1.0)

        return noised_img


class MotionBlur(BaseDiffAttackModel):
    """
    Motion blur applies a blur effect that simulates the effect of camera motion.
    This is a differentiable version implemented using PyTorch with a randomized factor.

    Attributes:
    - factor: int - The maximum size of the kernel used for the motion blur.
                    The higher the value, the more pronounced the blur effect.
                    Typically, factor should be between 3 and 15.
    - max_step: int - Maximum number of steps for dynamic factor scaling.
    - noisename: str - Name of the noise model (inherited from BaseDiffAttackModel).
    """

    def __init__(self, factor: int = 5, max_step: int = 1000, noisename: str = "MotionBlur"):
        """
        Initialize the differentiable MotionBlur class.

        Args:
        - factor: int - The maximum kernel size for the motion blur (typically 3 to 15).
        - max_step: int - Maximum number of steps for dynamic factor scaling in forward.
        - noisename: str - Name of the noise model (default: "MotionBlur").
        """
        super().__init__(noisename)
        self.factor = min(max(3, int(factor)), 15)  # Clamp factor between 3 and 15, ensure int
        self.max_step = max(1, int(max_step))  # Ensure max_step is at least 1, ensure int

    def forward(self, stego_img: Tensor, cover_img: Tensor = None, now_step: int = 0) -> Tensor:
        """
        Apply differentiable motion blur with a dynamically adjusted and randomized kernel size
        based on now_step, delegating the core computation to the test method.

        Args:
        - stego_img: Tensor - Input image tensor with shape (N, C, H, W).
        - cover_img: Tensor - Optional, not used in this implementation.
        - now_step: int - Current step for scaling the maximum motion blur kernel size.

        Returns:
        - Tensor - The motion-blurred image tensor with shape (N, C, H, W).
        """
        # Ensure now_step is an integer and within bounds
        now_step = max(0, int(now_step))  # Prevent negative steps
        # Calculate the maximum kernel size based on now_step
        t = min(now_step, self.max_step) / self.max_step  # Normalized step [0, 1]
        current_factor = max(3, int(1 + t * (self.factor - 1)))  # Scale from 3 to self.factor, ensure at least 3
        # Randomly sample a factor between 3 and max_factor (inclusive)
        if current_factor <= 3:
            current_factor = 3  # If max_factor is 3 or less, use minimum kernel size
        # Call test with the dynamically computed and randomized factor
        return self.test(stego_img, cover_img, factor=current_factor)

    def test(self, stego_img: Tensor, cover_img: Tensor = None, factor=None) -> Tensor:
        """
        Core computation for motion blur with a specified kernel size and randomly chosen direction.

        Args:
        - stego_img: Tensor - Input image tensor with shape (N, C, H, W).
        - cover_img: Tensor - Optional, not used in this implementation.
        - factor: int - The kernel size for the motion blur (larger values increase blur).

        Returns:
        - Tensor - The motion-blurred image tensor with shape (N, C, H, W).
        """
        if factor is None:
            factor = self.factor
        # Ensure factor is a valid odd integer kernel size
        kernel_size = max(3, int(factor))  # Ensure minimum size of 3
        if kernel_size % 2 == 0:  # Make sure kernel_size is odd
            kernel_size += 1

        # Randomly choose the motion blur direction: horizontal, vertical, diagonal, or anti-diagonal
        direction = random.choice(['horizontal', 'vertical', 'diagonal', 'anti-diagonal'])

        # Initialize an empty kernel tensor
        kernel = torch.zeros((kernel_size, kernel_size), device=stego_img.device, dtype=torch.float32)

        # Create motion blur kernel based on the chosen direction
        if direction == 'horizontal':
            # Horizontal motion: blur along the center row
            kernel[kernel_size // 2, :] = 1.0 / kernel_size
        elif direction == 'vertical':
            # Vertical motion: blur along the center column
            kernel[:, kernel_size // 2] = 1.0 / kernel_size
        elif direction == 'diagonal':
            # Main diagonal motion: blur from top-left to bottom-right
            for i in range(kernel_size):
                kernel[i, i] = 1.0 / kernel_size
        elif direction == 'anti-diagonal':
            # Anti-diagonal motion: blur from top-right to bottom-left
            for i in range(kernel_size):
                kernel[i, kernel_size - 1 - i] = 1.0 / kernel_size

        # Reshape kernel for group convolution (C, 1, K, K)
        kernel = kernel.view(1, 1, kernel_size, kernel_size)
        kernel = kernel.expand(stego_img.shape[1], 1, kernel_size, kernel_size)  # Match channel count

        # Apply the motion blur using depthwise 2D convolution
        padding = kernel_size // 2  # Pad to maintain input size
        noised_img = F.conv2d(stego_img, kernel, padding=padding, groups=stego_img.shape[1])

        # Clip values to [0, 1] to keep output valid (differentiable)
        noised_img = torch.clamp(noised_img, 0, 1)

        return noised_img


class RandomBlur(BaseDiffAttackModel):
    """
    Random blur applies a blur effect that simulates the effect of camera motion.
    This is a differentiable version implemented using PyTorch with a randomized factor.

    Attributes:
    - factor: int - The maximum size of the kernel used for the motion blur.
                    The higher the value, the more pronounced the blur effect.
                    Typically, factor should be between 3 and 15.
    - max_step: int - Maximum number of steps for dynamic factor scaling.
    - noisename: str - Name of the noise model (inherited from BaseDiffAttackModel).
    """

    def __init__(self, factor: int = 5, max_step: int = 1000, noisename: str = "RandomBlur"):
        """
        Initialize the differentiable MotionBlur class.

        Args:
        - factor: int - The maximum kernel size for the motion blur (typically 3 to 15).
        - max_step: int - Maximum number of steps for dynamic factor scaling in forward.
        - noisename: str - Name of the noise model (default: "MotionBlur").
        """
        super().__init__(noisename)
        self.factor = min(max(3, int(factor)), 15)  # Clamp factor between 3 and 15, ensure int
        self.max_step = max(1, int(max_step))  # Ensure max_step is at least 1, ensure int

    def forward(self, stego_img: Tensor, cover_img: Tensor = None, now_step: int = 0) -> Tensor:
        """
        Apply differentiable motion blur with a dynamically adjusted and randomized kernel size
        based on now_step, delegating the core computation to the test method.

        Args:
        - stego_img: Tensor - Input image tensor with shape (N, C, H, W).
        - cover_img: Tensor - Optional, not used in this implementation.
        - now_step: int - Current step for scaling the maximum motion blur kernel size.

        Returns:
        - Tensor - The motion-blurred image tensor with shape (N, C, H, W).
        """
        # Ensure now_step is an integer and within bounds
        now_step = max(0, int(now_step))  # Prevent negative steps
        # Calculate the maximum kernel size based on now_step
        t = min(now_step, self.max_step) / self.max_step  # Normalized step [0, 1]
        current_factor = max(3, int(1 + t * (self.factor - 1)))  # Scale from 3 to self.factor, ensure at least 3
        # Randomly sample a factor between 3 and max_factor (inclusive)
        if current_factor <= 3:
            current_factor = 3  # If max_factor is 3 or less, use minimum kernel size
        # Call test with the dynamically computed and randomized factor
        return self.test(stego_img, cover_img, factor=current_factor)

    def test(self, stego_img: Tensor, cover_img: Tensor = None, factor=None) -> Tensor:
        """
        Core computation for motion blur with a specified kernel size and randomly chosen direction.

        Args:
        - stego_img: Tensor - Input image tensor with shape (N, C, H, W).
        - cover_img: Tensor - Optional, not used in this implementation.
        - factor: int - The kernel size for the motion blur (larger values increase blur).

        Returns:
        - Tensor - The motion-blurred image tensor with shape (N, C, H, W).
        """
        if factor is None:
            factor = self.factor
        # Ensure factor is a valid odd integer kernel size
        kernel_size = max(3, int(factor))  # Ensure minimum size of 3
        if kernel_size % 2 == 0:  # Make sure kernel_size is odd
            kernel_size += 1

        f = random_blur_kernel(probs=[.25, .25], N_blur=kernel_size, sigrange_gauss=[1., 3.], sigrange_line=[.25, 1.],
                               wmin_line=3).to(stego_img.device)

        noised_img = F.conv2d(stego_img, f, bias=None, padding=int((kernel_size - 1) / 2))

        # Clip values to [0, 1] to keep output valid (differentiable)
        noised_img = torch.clamp(noised_img, 0, 1)

        return noised_img


class Contrast(BaseDiffAttackModel):
    """
    Contrast adjustment modifies the contrast of an image with a factor sampled from
    [1-contrast_factor, 1+contrast_factor]. This ensures a differentiable transformation
    inspired by torchvision.transforms.ColorJitter.

    Attributes:
    - contrast_factor: float - Maximum absolute value of contrast adjustment.
    - max_step: int - Maximum number of steps for dynamic factor scaling.
    """

    def __init__(self, contrast_factor: float = 0.15, max_step: int = 100, noisename: str = "Contrast"):
        """
        Initialize the Contrast transformation.

        Args:
        - contrast_factor: float - The maximum absolute value of contrast adjustment.
        - max_step: int - Maximum step count to control contrast scaling.
        """
        super().__init__(noisename)
        self.max_step = max(max_step, 1)  # Ensure max_step is at least 1
        self.contrast_factor = max(0.0, contrast_factor)  # Ensure non-negative

    def forward(self, marked_img: Tensor, cover_img: Tensor = None, now_step: int = 0) -> Tensor:
        """
        Apply differentiable contrast adjustment with a dynamically adjusted factor.

        Args:
        - marked_img: Tensor - Input image tensor with shape (N, C, H, W), assumed in [0, 1] range.
        - cover_img: Tensor - Optional, not used in this implementation.
        - now_step: int - Current step for dynamic adjustment of contrast factor.

        Returns:
        - Tensor - Contrast-adjusted image tensor, clamped to [0, 1].
        """
        progress = min(now_step / self.max_step, 1.0)  # Normalize progress to [0, 1]
        max_factor = self.contrast_factor * progress  # Increase factor with training step
        factor = torch.empty(1).uniform_(-max_factor,
                                         max_factor).item() + 1.  # Sample from [1-max_factor, 1+max_factor]

        return self.test(marked_img, cover_img, contrast_factor=factor)  # Call test with computed factor

    def test(self, marked_img: Tensor, cover_img: Tensor = None, contrast_factor=None) -> Tensor:
        """
        Apply the contrast transformation in test mode.

        Args:
        - marked_img: Tensor - Input image tensor with shape (N, C, H, W), assumed in [0, 1] range.
        - cover_img: Tensor - Optional, not used in this implementation.
        - contrast_factor: float - The contrast multiplier in [1-A, 1+A].

        Returns:
        - Tensor - Contrast-adjusted image tensor, clamped to [0, 1].
        """
        if contrast_factor is None:
            contrast_factor = self.contrast_factor
        noised_img = Fs.adjust_contrast(marked_img, contrast_factor)
        return noised_img.clamp(0, 1)


class UnsharpMasking(BaseDiffAttackModel):
    def __init__(self, amount: float = 5, sigma: float = 3.0, threshold: float = 0, max_step: int = 1000,
                 noisename: str = "UnsharpMasking"):
        """
        Initialize the differentiable UnsharpMasking class.

        Args:
        - amount: float - amount for unsharp masking.
        - sigma: float - Standard deviation of the Gaussian kernel.
        - threshold: float - Threshold for edge enhancement.
        - device: str - Computation device ("cpu" or "cuda").
        """
        super().__init__(noisename)
        self.amount = amount
        self.sigma = sigma
        self.threshold = threshold
        self.max_step = max(max_step, 1)  # Ensure max_step is at least 1

    def forward(self, stego_img: Tensor, cover_img: Tensor = None, now_step: int = 0) -> Tensor:
        """
        Apply differentiable Unsharp Masking distortion to the stego image.

        Args:
        - stego_img: Tensor - Input image tensor with shape (B, C, H, W) or (C, H, W).
        - cover_img: Tensor - Optional, not used in this implementation.
        - amount: float - Sharpening strength factor.

        Returns:
        - result_img: Tensor - Sharpened image tensor after unsharp masking.
        """

        amount = min(now_step, self.max_step) / self.max_step * self.amount
        sharpened = self.test(stego_img, cover_img, amount)
        return sharpened

    def test(self, stego_img: Tensor, cover_img: Tensor = None, amount=None) -> Tensor:
        """
        Apply differentiable Unsharp Masking distortion to the stego image.

        Args:
        - stego_img: Tensor - Input image tensor with shape (B, C, H, W) or (C, H, W).
        - cover_img: Tensor - Optional, not used in this implementation.
        - amount: float - Sharpening strength factor.

        Returns:
        - result_img: Tensor - Sharpened image tensor after unsharp masking.
        """
        if amount is None:
            amount = self.amount
        # Calculate Gaussian kernel size based on sigma
        kernel_size = self._calculate_kernel_size(self.sigma)

        # Step 1: Apply Gaussian blur (differentiable)
        blurred = self._gaussian_blur(stego_img, kernel_size, self.sigma)

        # Step 2: Compute high-frequency component by subtracting blurred image
        high_freq = stego_img - blurred

        # Step 3: Apply threshold processing (approximation for differentiability)
        mask = torch.abs(high_freq) > self.threshold  # Boolean mask for edges
        high_freq = high_freq * mask.float().to(stego_img.device)  # Convert mask to float for multiplication

        # Step 4: Enhance high-frequency component and add it back to the original image
        sharpened = stego_img + amount * high_freq

        # Step 5: Clip output values to the valid range [0, 255] (differentiable)
        sharpened = torch.clamp(sharpened, 0, 1)

        return sharpened

    def _calculate_kernel_size(self, sigma: float) -> int:
        """
        Calculate the kernel size based on the standard deviation (sigma).

        The kernel size is chosen as 6 * sigma + 1 to cover most of the Gaussian distribution.

        Args:
        - sigma: float - Standard deviation of the Gaussian kernel.

        Returns:
        - int: Calculated kernel size (ensured to be odd).
        """
        kernel_size = int(6 * sigma + 1)
        # Ensure kernel size is odd for symmetry in convolution
        if kernel_size % 2 == 0:
            kernel_size += 1
        return kernel_size

    def _gaussian_blur(self, img: Tensor, kernel_size: int, sigma: float) -> Tensor:
        """
        Apply Gaussian blur to the image using a differentiable convolution.

        Args:
        - img: Tensor - Input image tensor with shape (B, C, H, W).
        - kernel_size: int - Size of the Gaussian kernel.
        - sigma: float - Standard deviation of the Gaussian kernel.

        Returns:
        - Tensor: Blurred image tensor.
        """
        # Create Gaussian kernel and move it to the specified device
        kernel = self._create_gaussian_kernel(kernel_size, sigma).to(img.device)
        # Expand kernel to match the number of channels (C, 1, K, K)
        kernel = kernel.expand(img.shape[1], 1, kernel_size, kernel_size)

        # Apply convolution with padding to maintain image size
        padding = kernel_size // 2
        blurred = F.conv2d(img, kernel, padding=padding, groups=img.shape[1])
        return blurred

    def _create_gaussian_kernel(self, size: int, sigma: float) -> Tensor:
        """
        Create a 2D Gaussian kernel for blurring.

        Args:
        - size: int - Size of the kernel (must be odd).
        - sigma: float - Standard deviation of the Gaussian distribution.

        Returns:
        - Tensor: Normalized 2D Gaussian kernel with shape (size, size).
        """
        # Create coordinate grid for the kernel
        ax = torch.arange(-(size // 2), size // 2 + 1, dtype=torch.float32)
        xx, yy = torch.meshgrid(ax, ax, indexing="ij")
        # Compute Gaussian function
        kernel = torch.exp(-(xx ** 2 + yy ** 2) / (2.0 * sigma ** 2))
        # Normalize kernel so it sums to 1
        kernel = kernel / kernel.sum()
        return kernel


class GaussianBlur(BaseDiffAttackModel):
    """
    Gaussian blur applies a blur effect to an image using a Gaussian kernel.
    This is a differentiable version implemented using PyTorch.

    Attributes:
    - sigma: float - The maximum standard deviation of the Gaussian kernel.
                     Higher values result in stronger blur.
                     Typically in the range [0.1, 5.0].
    - max_step: int - Maximum number of steps for dynamic sigma scaling.
    """

    def __init__(self, sigma: float = 1.5, max_step: int = 1000, noisename: str = "GaussianBlur"):
        """
        Initialize the differentiable GaussianBlur class.

        Args:
        - sigma: float - The maximum standard deviation of the Gaussian kernel.
        - max_step: int - Maximum step count to control sigma scaling.
        """
        super().__init__(noisename)
        self.sigma = max(0.1, sigma)  # Ensure sigma is positive and reasonable
        self.max_step = max(max_step, 1)  # Ensure max_step is at least 1

    def forward(self, stego_img: Tensor, cover_img: Tensor = None, now_step: int = 0) -> Tensor:
        """
        Apply differentiable Gaussian blur with a dynamically adjusted sigma based on now_step,
        delegating the core computation to the test method.

        Args:
        - stego_img: Tensor - Input image tensor with shape (N, C, H, W).
        - cover_img: Tensor - Optional, not used in this implementation.
        - now_step: int - Current step for dynamic adjustment of sigma.

        Returns:
        - Tensor - Blurred image tensor with shape (N, C, H, W).
        """
        # Calculate sigma based on current step, scaling from 0 (no blur) to self.sigma
        current_sigma = (min(now_step, self.max_step) / self.max_step) * self.sigma
        # Call test with the dynamically computed sigma
        return self.test(stego_img, cover_img, sigma=current_sigma)

    def test(self, stego_img: Tensor, cover_img: Tensor = None, sigma=None) -> Tensor:
        """
        Core computation for Gaussian blur with a specified sigma.

        Args:
        - stego_img: Tensor - Input image tensor with shape (N, C, H, W).
        - cover_img: Tensor - Optional, not used in this implementation.
        - sigma: float - The standard deviation of the Gaussian kernel.

        Returns:
        - Tensor - Blurred image tensor with shape (N, C, H, W).
        """
        if sigma is None:
            sigma = self.sigma
        # Calculate kernel size based on sigma
        kernel_size = self._calculate_kernel_size(sigma)

        # Generate 1D Gaussian kernel
        ax = torch.arange(-(kernel_size // 2), kernel_size // 2 + 1, dtype=torch.float32, device=stego_img.device)
        gaussian = torch.exp(-(ax ** 2) / (2 * sigma ** 2))
        gaussian = gaussian / gaussian.sum()  # Normalize
        kernel = gaussian.view(1, 1, kernel_size, 1) * gaussian.view(1, 1, 1, kernel_size)  # 2D kernel

        # Expand kernel for all channels
        kernel = kernel.expand(stego_img.shape[1], 1, kernel_size, kernel_size)

        # Apply separable 2D Gaussian blur using convolution
        padding = kernel_size // 2
        noised_img = F.conv2d(stego_img, kernel, padding=padding, groups=stego_img.shape[1])

        # Clamp to valid range [0, 255] assuming input is in this range
        noised_img = torch.clamp(noised_img, 0, 255)
        return noised_img

    def _calculate_kernel_size(self, sigma: float) -> int:
        """
        Calculate the kernel size based on the standard deviation (sigma).

        The kernel size is chosen as 6 * sigma + 1 to cover most of the Gaussian distribution.

        Args:
        - sigma: float - The standard deviation of the Gaussian kernel.

        Returns:
        - int - The calculated kernel size (odd).
        """
        kernel_size = int(6 * sigma + 1)
        # Ensure kernel size is odd
        if kernel_size % 2 == 0:
            kernel_size += 1
        return kernel_size


class Brightness(BaseDiffAttackModel):
    """
    Brightness adjustment modifies the intensity of an image with a factor sampled from
    [-brightness_factor, brightness_factor], applied as a multiplicative scaling from
    [1-brightness_factor, 1+brightness_factor]. This ensures a differentiable transformation
    inspired by torchvision.transforms.ColorJitter.

    Attributes:
    - brightness_factor: float - Maximum absolute value of brightness adjustment.
    - max_step: int - Maximum number of steps for dynamic factor scaling.
    """

    def __init__(self, brightness_factor: float = 0.15, max_step: int = 100, noisename: str = "Brightness"):
        """
        Initialize the Brightness transformation.

        Args:
        - brightness_factor: float - The maximum absolute value of brightness range (non-negative).
        - max_step: int - Maximum step count to control brightness scaling.
        """
        super().__init__(noisename)
        self.max_step = max(max_step, 1)  # Ensure max_step is at least 1
        self.brightness_factor = max(0.0, brightness_factor)  # Ensure non-negative

    def forward(self, marked_img: Tensor, cover_img: Tensor = None, now_step: int = 0) -> Tensor:
        """
        Apply differentiable brightness adjustment with a dynamically adjusted factor.

        Args:
        - marked_img: Tensor - Input image tensor with shape (N, C, H, W), assumed in [0, 1] range.
        - cover_img: Tensor - Optional, not used in this implementation.
        - now_step: int - Current step for dynamic adjustment of brightness factor.

        Returns:
        - Tensor - Brightness-adjusted image tensor, clamped to [0, 1].
        """
        progress = min(now_step / self.max_step, 1.0)  # Normalize progress to [0, 1]
        max_factor = self.brightness_factor * progress  # Increase factor with training step
        factor = torch.empty(1).uniform_(-max_factor,
                                         max_factor).item() + 1.  # Sample from [1-max_factor, 1+max_factor]

        return self.test(marked_img, cover_img, brightness_factor=factor)  # Call test with computed factor

    def test(self, marked_img: Tensor, cover_img: Tensor = None, brightness_factor=None) -> Tensor:
        """
        Apply the brightness transformation in test mode.

        Args:
        - marked_img: Tensor - Input image tensor with shape (N, C, H, W), assumed in [0, 1] range.
        - cover_img: Tensor - Optional, not used in this implementation.
        - brightness_factor: float - The brightness multiplier in [1-A, 1+A].

        Returns:
        - Tensor - Brightness-adjusted image tensor, clamped to [0, 1].
        """
        if brightness_factor is None:
            brightness_factor = self.brightness_factor
        noised_img = Fs.adjust_brightness(marked_img, brightness_factor)
        return noised_img.clamp(0, 1)


class MedianFilter(BaseDiffAttackModel):
    """
    A class that applies a median filter to images for noise reduction.

    The median filter is useful for removing noise while preserving edges.
    It operates by replacing each pixel's value with the median value of the
    neighboring pixels defined by a kernel.

    Attributes:
        kernel (int): The size of the kernel for the median filter (should be odd).
        prob (float): The probability of applying the median filter.
        max_step (int): The maximum number of steps for dynamic adjustment (not currently used).
    """

    def __init__(self, kernel: int = 7, prob: float = 0.8, max_step: int = 100,
                 noisename: str = "MedianFilter"):
        """
        Initializes the MedianFilter class with specified parameters.

        Args:
            kernel (int): The size of the kernel for the median filter (default is 7).
            prob (float): The probability of applying the median filter (default is 0.8).
            max_step (int): The maximum number of steps for dynamic adjustment (default is 100).
        """
        super(MedianFilter, self).__init__(noisename)
        self.prob = prob  # Probability of applying the median filter
        self.kernel = kernel  # Size of the median filter kernel
        self.max_step = max(max_step, 1)  # Maximum step count for dynamic adjustment (not currently used)

    def forward(self, marked_img: torch.Tensor, cover_img: torch.Tensor = None, now_step: int = 0) -> torch.Tensor:
        """
        Applies the median filter to the input marked image.

        The method randomly decides whether to apply the median filter based on the
        defined probability. If in test mode, the filter is always applied.

        Args:
            marked_img (torch.Tensor): The input image tensor to which the median filter will be applied.
            cover_img (torch.Tensor, optional): The cover image tensor (not used in this method).
            now_step (int): The current step in the training process (not currently used).

        Returns:
            torch.Tensor: The resulting image after applying the median filter.
        """
        # Calculate dynamic kernel size based on current step
        _kernel = int(min(now_step, self.max_step) / self.max_step * self.kernel)
        if _kernel % 2 == 0:
            _kernel += 1  # Ensure kernel size is odd
        _kernel = max(3, _kernel)
        noised_img = self.test(marked_img, cover_img, _kernel)
        return noised_img.clamp(0, 1.)  # Clamp pixel values to [0, 1]

    def test(self, marked_img: torch.Tensor, cover_img: torch.Tensor = None, kernel=None) -> torch.Tensor:
        """
        Applies the median filter to the input image tensor for testing.

        Args:
            marked_img (torch.Tensor): The input image tensor.
            cover_img (torch.Tensor, optional): An optional cover image tensor (not used in this method).
            kernel (int): The kernel size to use for the median filter (default is 7).

        Returns:
            torch.Tensor: The resulting image after applying the median filter, clamped to [0, 1].
        """
        if kernel is None:
            kernel = self.kernel
        _kernel = (kernel, kernel)  # Define the kernel size
        noised_img = MedianBlur(_kernel)(marked_img)  # Apply the median blur
        return noised_img.clamp(0, 1.)  # Clamp pixel values to [0, 1]


class Saturation(BaseDiffAttackModel):
    def __init__(self, saturation_factor: float = 0.15, max_step: int = 100, noisename: str = "Saturation"):
        """
        Initialize the Saturation transformation.

        Args:
            saturation_factor (float): Base factor for adjusting saturation.
                                       Should be in the range [0, ∞), where 1 means no change.
            max_step (int): The maximum number of steps for dynamic adjustment.
        """
        super(Saturation, self).__init__(noisename)
        self.saturation_factor = saturation_factor
        self.max_step = max(max_step, 1)

    def forward(self, marked_img: torch.Tensor, cover_img: torch.Tensor = None, now_step: int = 0) -> torch.Tensor:
        """
        Apply the saturation transformation.

        Args:
            marked_img (torch.Tensor): The input image tensor.
            cover_img (torch.Tensor, optional): An optional cover image tensor (not used in this transform).
            now_step (int): The current step in the training process.

        Returns:
            torch.Tensor: The transformed image.
        """
        progress = min(now_step / self.max_step, 1.0)  # Normalize progress to [0, 1]
        max_factor = self.saturation_factor * progress  # Increase factor with training step
        factor = torch.empty(1).uniform_(-max_factor, max_factor).item()  # Sample random factor
        return self.test(marked_img, cover_img, factor)  # Call test with the computed factor

    def test(self, marked_img: torch.Tensor, cover_img: torch.Tensor = None, saturation_factor=None) -> torch.Tensor:
        """
        Apply the saturation transformation in test mode.

        Args:
            marked_img (torch.Tensor): The input image tensor.
            cover_img (torch.Tensor, optional): An optional cover image tensor (not used in this transform).
            saturation_factor (float): The saturation adjustment factor.

        Returns:
            torch.Tensor: The transformed image.
        """
        if saturation_factor is None:
            saturation_factor = self.saturation_factor
        noised_img = Fs.adjust_saturation(marked_img, 1. + saturation_factor)
        return noised_img.clamp(0, 1.)


class Hue(BaseDiffAttackModel):
    """
    Hue adjustment modifies the hue of an image by applying a transformation based on a factor.
    The hue factor ranges from [-0.5, 0.5], where 0 means no change, and the factor is dynamically adjusted
    based on the training step.

    Attributes:
    - hue_factor: float - The maximum hue adjustment factor.
    - max_step: int - Maximum number of steps for dynamic scaling.
    """

    def __init__(self, hue_factor: float = 0.1, max_step: int = 100, noisename: str = "Hue"):
        """
        Initialize the Hue transformation.

        Args:
        - hue_factor: float - The maximum hue adjustment factor, should be in the range [-0.5, 0.5].
        - max_step: int - Maximum number of steps for dynamic scaling.
        """
        super().__init__(noisename)
        self.hue_factor = max(-0.5, min(hue_factor, 0.5))  # Ensure hue_factor is within [-0.5, 0.5]
        self.max_step = max(max_step, 1)  # Ensure max_step is at least 1

    def forward(self, marked_img: torch.Tensor, cover_img: torch.Tensor = None, now_step: int = 0) -> torch.Tensor:
        """
        Apply the hue transformation with a dynamically adjusted factor.

        Args:
        - marked_img: Tensor - Input image tensor with shape (N, C, H, W), assumed in [0, 1] range.
        - cover_img: Tensor - Optional, not used in this implementation.
        - now_step: int - Current step for dynamic adjustment of the hue factor.

        Returns:
        - Tensor - Hue-adjusted image tensor, clamped to [0, 1].
        """
        progress = min(now_step / self.max_step, 1.0)  # Normalize progress to [0, 1]
        max_factor = self.hue_factor * progress  # Adjust factor based on progress
        factor = torch.empty(1).uniform_(-max_factor,
                                         max_factor).item()  # Sample hue factor from [-max_factor, max_factor]
        return self.test(marked_img, cover_img, factor=factor)  # Call test with computed factor

    def test(self, marked_img: torch.Tensor, cover_img: torch.Tensor = None, factor=None) -> torch.Tensor:
        """
        Apply the hue transformation in test mode by modifying the image's hue channel.

        Args:
        - marked_img: Tensor - Input image tensor with shape (N, C, H, W), assumed in [0, 1] range.
        - cover_img: Tensor - Optional, not used in this implementation.
        - hue_factor: float - The hue factor to apply during testing.

        Returns:
        - Tensor - Hue-adjusted image tensor, clamped to [0, 1].
        """
        if factor is None:
            factor = self.hue_factor
        noised_img = Fs.adjust_hue(marked_img, factor)
        return noised_img.clamp(0, 1)


class RandomFlipping(BaseDiffAttackModel):
    """
    A differentiable random flip distortion layer that randomly applies
    horizontal and/or vertical flips to the input image.

    Attributes:
    - p_hflip: float - Probability of applying horizontal flip (default: 0.5).
    - p_vflip: float - Probability of applying vertical flip (default: 0.5).
    - noisename: str - Name of the distortion model.
    """

    def __init__(
            self,
            p_hflip: float = 0.5,
            p_vflip: float = 0.5,
            noisename: str = "RandomFlipping"
    ):
        """
        Initialize the RandomFlipDistortion layer.

        Args:
        - p_hflip: float - Probability of horizontal flip (0.0 to 1.0).
        - p_vflip: float - Probability of vertical flip (0.0 to 1.0).
        - noisename: str - Name of the noise model.
        """
        super().__init__(noisename)
        self.p_hflip = p_hflip
        self.p_vflip = p_vflip

    def forward(
            self,
            stego_img: Tensor,
            cover_img: Tensor = None,
            now_step: int = 0
    ) -> Tensor:
        """
        Apply random flips to the input image.

        Args:
        - stego_img: Tensor - Input image tensor with shape (N, C, H, W).
        - cover_img: Tensor - Optional, not used.
        - now_step: int - Current step (unused, kept for interface consistency).

        Returns:
        - Tensor - The flipped (or not) image tensor with shape (N, C, H, W).
        """
        return self.test(stego_img, cover_img)

    def test(
            self,
            stego_img: Tensor,
            cover_img: Tensor = None,
            factor: float = None  # unused, kept for compatibility
    ) -> Tensor:
        """
        Apply random horizontal and vertical flips independently.

        Args:
        - stego_img: Tensor - Input image tensor (N, C, H, W).
        - cover_img: Tensor - Ignored.
        - factor: float - Ignored (for API compatibility).

        Returns:
        - Tensor - Distorted image after random flips.
        """
        x = stego_img.clone()  # avoid in-place modification

        # Horizontal flip (dim=-1)
        if random.random() < self.p_hflip:
            x = torch.flip(x, dims=[-1])

        # Vertical flip (dim=-2)
        if random.random() < self.p_vflip:
            x = torch.flip(x, dims=[-2])

        return x


class Crop(BaseDiffAttackModel):
    def __init__(self, retain_ratio_max=0.7, mode="constant_pad", constant: float = 0.0,
                 prob: float = 1, max_step: int = 100, noisename: str = "Crop"):
        """
        Initializes the Crop layer.

        Args:
            retain_ratio_max (float): Maximum ratio of the image to be retained.
            mode (str): The mode of operation, either 'cover_pad' or 'constant_pad'.
            constant (float): Constant value used in 'constant_pad' mode.
            prob (float): Probability of applying the Crop operation.
            max_step (int): The maximum number of steps for dynamic adjustment.
            noisename (str): Name of the noise model.
        """
        super(Crop, self).__init__(noisename)

        # Validate mode
        if mode not in ["cover_pad", "constant_pad"]:
            mode = "constant_pad"
        self.mode = mode

        # Validate and set parameters
        self.constant = max(min(constant, 1.0), 0.0)
        self.crop_ratio_max = max(min(retain_ratio_max, 1.0), 0.0)
        self.prob = max(min(prob, 1.0), 0.0)
        self.max_step = max(max_step, 1)

    def forward(self, marked_img: Tensor, cover_img: Tensor = None, now_step: int = 0) -> Tensor:
        """
        Apply the Crop operation to the input image.
        The crop ratio is dynamically adjusted based on the current step.

        Args:
            marked_img (Tensor): The marked image tensor.
            cover_img (Tensor): The cover image tensor (used when mode is 'cover_pad').
            now_step (int): Current step in the training process.

        Returns:
            Tensor: The resulting image after applying Crop.
        """
        # Calculate the effective crop ratio based on the current step
        crop_ratio = self.crop_ratio_max * (min(now_step, self.max_step) / self.max_step)
        return self.test(marked_img, cover_img, crop_ratio)

    def test(self, marked_img: Tensor, cover_img: Tensor = None, factor: float = None) -> Tensor:
        """
        Apply the Crop operation for testing with a fixed crop ratio.

        Args:
            marked_img (Tensor): The marked image tensor.
            cover_img (Tensor): The cover image tensor (used when mode is 'cover_pad').
            crop_ratio (float): The ratio of the image area to be cropped out.

        Returns:
            Tensor: The resulting image after applying Crop.
        """
        if factor is None:
            factor = self.crop_ratio_max

        # Generate a random rectangle mask
        crop_mask = self.random_cropout_mask(marked_img, factor)

        # Apply different filling methods based on mode
        if self.mode == "cover_pad" and cover_img is not None:
            noised_img = marked_img * (1. - crop_mask) + crop_mask * cover_img  # Use cover_img for padding
        else:
            noised_img = marked_img * (1. - crop_mask) + crop_mask * self.constant  # Use constant value for padding

        return noised_img.clamp(0.0, 1.0)

    def random_cropout_mask(self, marked_img: Tensor, crop_ratio: float) -> Tensor:
        """
        Generate a mask for Cropout operation, where a rectangular region in the middle of the image is cropped out.

        Args:
            marked_img (Tensor): Input tensor of shape (N, C, H, W), where N is the batch size,
                                 C is the number of channels, H is the height, and W is the width.
            crop_ratio (float): The ratio of the image area to be cropped out.

        Returns:
            Tensor: A mask of shape (N, C, H, W) with values 1 for the visible area and 0 for the cropped-out region.
        """
        N, C, H, W = marked_img.shape  # Get the shape of the input image tensor
        mask = torch.ones((N, C, H, W), dtype=torch.float32, device=marked_img.device)  # Initialize the mask with ones

        for i in range(N):
            num_pixels_to_crop = int(H * W * crop_ratio)

            # Ensure we don't try to crop more than the image area
            num_pixels_to_crop = min(num_pixels_to_crop, H * W)

            if num_pixels_to_crop == 0:
                continue  # No cropping needed

            # Calculate maximum possible width and height
            max_width = min(W, num_pixels_to_crop)
            max_height = min(H, num_pixels_to_crop)

            # Calculate minimum width and height to ensure valid range for sampling
            min_width = min(1, max_width)
            min_height = min(1, max_height)

            # Use Gaussian distribution to sample width (mean at sqrt of desired area)
            desired_area = num_pixels_to_crop
            mean_width = min(max_width, max(1, int(np.sqrt(desired_area))))

            # Standard deviation as a fraction of the mean for controlled variance
            std_width = max(1, mean_width * 0.3)  # 30% of mean as std

            # Sample width using Gaussian distribution and clip to valid range
            width = int(np.clip(np.random.normal(mean_width, std_width), min_width, max_width))
            width = max(min_width, min(width, max_width))  # Final bounds check

            # Calculate corresponding height based on desired area
            height = min(num_pixels_to_crop // width, max_height)
            height = max(min_height, min(height, max_height))  # Final bounds check

            # Ensure width * height <= num_pixels_to_crop
            if width * height > num_pixels_to_crop:
                # Adjust width or height to fit the desired area
                if width > height:
                    width = min(num_pixels_to_crop, max_width)
                    height = min(num_pixels_to_crop // width, max_height)
                else:
                    height = min(num_pixels_to_crop, max_height)
                    width = min(num_pixels_to_crop // height, max_width)

                width = max(min_width, min(width, max_width))
                height = max(min_height, min(height, max_height))

            # Calculate valid starting positions
            max_start_w = W - width
            max_start_h = H - height

            if max_start_w >= 0 and max_start_h >= 0:
                rect_w = random.randint(0, max_start_w) if max_start_w > 0 else 0
                rect_h = random.randint(0, max_start_h) if max_start_h > 0 else 0
                mask[i, :, rect_h:rect_h + height, rect_w:rect_w + width] = 0.0  # Crop out area set to 0

        return mask.to(marked_img.device)


class Cropout(BaseDiffAttackModel):
    def __init__(self, crop_ratio_max=0.5, max_step: int = 100, noisename: str = "Cropout", mode: str = "constant",
                 constant_value: float = 0):
        """
        Initializes the Cropout layer.

        Args:
            crop_ratio_max (float): Maximum ratio of the image to be cropped out.
            max_step (int): The maximum number of steps for dynamic adjustment.
            mode (str): The mode to use for filling the cropped area. Options: 'cover_pad' or 'constant'.
            constant_value (float): The constant value to use for the 'constant' mode.
        """
        super(Cropout, self).__init__(noisename)

        # Ensure crop_ratio_max is between 0 and 1
        self.crop_ratio_max = max(min(crop_ratio_max, 1.0), 0.0)
        self.max_step = max(max_step, 1)
        self.mode = mode
        self.constant_value = constant_value  # Default value for the constant mode

    def forward(self, marked_img: Tensor, cover_img: Tensor = None, now_step: int = 0) -> Tensor:
        """
        Applies the Cropout operation to the input image.

        Args:
            marked_img (Tensor): The marked image tensor.
            cover_img (Tensor): The cover image tensor (used when mode is 'cover_pad').
            now_step (int): Current step in the training process.

        Returns:
            Tensor: The resulting image after applying Cropout.
        """
        # Calculate the remain ratio based on current step, gradually increasing
        remain_ratio = self.crop_ratio_max * min(now_step, self.max_step) / self.max_step
        noised_img = self.test(marked_img, cover_img, remain_ratio)
        return noised_img

    def test(self, marked_img: Tensor, cover_img: Tensor = None, factor: float = None) -> Tensor:
        """
        Applies the Cropout operation to the input image during testing.

        Args:
            marked_img (Tensor): The marked image tensor.
            cover_img (Tensor): The cover image tensor (used when mode is 'cover_pad').
            remain_ratio (float): The ratio of pixels to remain in the marked image.

        Returns:
            Tensor: The resulting image after applying Cropout.
        """
        if factor is None:
            factor = self.crop_ratio_max

        crop_out_mask = self.random_cropout_mask(marked_img, factor)

        # Apply different filling methods based on mode
        if self.mode == "cover_pad" and cover_img is not None:
            noised_img = marked_img * crop_out_mask + (1 - crop_out_mask) * cover_img  # Use cover_img for padding
        else:
            noised_img = marked_img * crop_out_mask + (
                    1 - crop_out_mask) * self.constant_value  # Use constant value for padding

        return noised_img.clamp(0.0, 1.0)  # Clamp values to [0, 1]

    def random_cropout_mask(self, marked_img: Tensor, crop_ratio: float) -> Tensor:
        """
        Generate a mask for Cropout operation, where a rectangular region in the middle of the image is cropped out.

        Args:
            marked_img (Tensor): Input tensor of shape (N, C, H, W), where N is the batch size,
                                 C is the number of channels, H is the height, and W is the width.
            crop_ratio (float): The ratio of the image area to be cropped out.

        Returns:
            Tensor: A mask of shape (N, C, H, W) with values 1 for the visible area and 0 for the cropped-out region.
        """
        N, C, H, W = marked_img.shape  # Get the shape of the input image tensor
        mask = torch.ones((N, C, H, W), dtype=torch.float32, device=marked_img.device)  # Initialize the mask with ones

        for i in range(N):
            num_pixels_to_crop = int(H * W * crop_ratio)

            # Ensure we don't try to crop more than the image area
            num_pixels_to_crop = min(num_pixels_to_crop, H * W)

            if num_pixels_to_crop == 0:
                continue  # No cropping needed

            # Calculate maximum possible width and height
            max_width = min(W, num_pixels_to_crop)
            max_height = min(H, num_pixels_to_crop)

            # Calculate minimum width and height to ensure valid range for sampling
            min_width = min(1, max_width)
            min_height = min(1, max_height)

            # Use Gaussian distribution to sample width (mean at sqrt of desired area)
            desired_area = num_pixels_to_crop
            mean_width = min(max_width, max(1, int(np.sqrt(desired_area))))

            # Standard deviation as a fraction of the mean for controlled variance
            std_width = max(1, mean_width * 0.3)  # 30% of mean as std

            # Sample width using Gaussian distribution and clip to valid range
            width = int(np.clip(np.random.normal(mean_width, std_width), min_width, max_width))
            width = max(min_width, min(width, max_width))  # Final bounds check

            # Calculate corresponding height based on desired area
            height = min(num_pixels_to_crop // width, max_height)
            height = max(min_height, min(height, max_height))  # Final bounds check

            # Ensure width * height <= num_pixels_to_crop
            if width * height > num_pixels_to_crop:
                # Adjust width or height to fit the desired area
                if width > height:
                    width = min(num_pixels_to_crop, max_width)
                    height = min(num_pixels_to_crop // width, max_height)
                else:
                    height = min(num_pixels_to_crop, max_height)
                    width = min(num_pixels_to_crop // height, max_width)

                width = max(min_width, min(width, max_width))
                height = max(min_height, min(height, max_height))

            # Calculate valid starting positions
            max_start_w = W - width
            max_start_h = H - height

            if max_start_w >= 0 and max_start_h >= 0:
                rect_w = random.randint(0, max_start_w) if max_start_w > 0 else 0
                rect_h = random.randint(0, max_start_h) if max_start_h > 0 else 0
                mask[i, :, rect_h:rect_h + height, rect_w:rect_w + width] = 0.0  # Crop out area set to 0

        return mask.to(marked_img.device)


class Dropout(BaseDiffAttackModel):
    def __init__(self, drop_prob=0.3, max_step: int = 100, noisename: str = "Dropout"):
        """
        Initializes the Dropout layer, which simulates the process of randomly dropping pixels in the image.

        Args:
            drop_prob (float): Probability of dropping a pixel. Should be between 0 and 1.
            max_step (int): Maximum number of steps for dynamic adjustment of drop probability during training.
            noisename (str): The name of the noise model.
        """
        super(Dropout, self).__init__(noisename)

        # Ensure max_step is at least 1 and drop_prob is between 0 and 1
        self.max_step = max(max_step, 1)
        self.drop_prob = max(min(drop_prob, 1.), 0.)  # Clamp drop_prob to be within [0, 1]

    def forward(self, marked_img: Tensor, cover_image: Tensor = None, now_step: int = 0) -> Tensor:
        """
        Applies the Dropout operation to the input image by randomly dropping pixels.

        Args:
            marked_img (Tensor): The marked image tensor that contains the information to be distorted.
            cover_image (Tensor): The cover image tensor used to replace the dropped pixels when using the 'cover_pad' mode.
            now_step (int): Current step in the training process, used to dynamically adjust drop probability.

        Returns:
            Tensor: The resulting image after applying dropout.
        """
        # Dynamically adjust the drop probability based on the current step
        adjusted_drop_prob = min(now_step, self.max_step) / self.max_step * self.drop_prob
        noised_img = self.test(marked_img, cover_image, adjusted_drop_prob)
        return noised_img

    def test(self, marked_img: Tensor, cover_image: Tensor, drop_prob=None) -> Tensor:
        """
        Applies the Dropout operation to the input image during testing.

        Args:
            marked_img (Tensor): The marked image tensor that contains the information to be distorted.
            cover_image (Tensor): The cover image tensor used for padding the dropped areas.
            drop_prob (float): Probability of dropping a pixel during testing. Should be between 0 and 1.

        Returns:
            Tensor: The resulting image after applying dropout.
        """
        if drop_prob is None:
            drop_prob = self.drop_prob
        # Create a mask tensor where each element is 1 with probability (1 - drop_prob) and 0 with probability drop_prob
        mask_tensor = torch.bernoulli(torch.full(marked_img.shape, 1 - drop_prob, device=marked_img.device))

        # Generate the noised image by keeping the pixels where mask is 1 and replacing with cover_image where mask is 0
        noised_img = marked_img * mask_tensor + cover_image * (1 - mask_tensor)

        # Clamp the resulting image to ensure pixel values are in the range [0, 1]
        return noised_img.clamp(0, 1.)


class GaussianNoise(BaseDiffAttackModel):
    def __init__(self, mu: float = 0, std: float = 1.5, intensity: float = 1.,
                 max_step: int = 100, noisename: str = "GaussianNoise"):
        """
        Initializes the GaussianNoise layer, which adds Gaussian noise to the image.

        Args:
            mu (float): Mean of the Gaussian noise.
            std (float): Standard deviation of the Gaussian noise.
            intensity (float): Maximum intensity of the noise.
            max_step (int): Maximum number of steps for dynamic adjustment of noise.
        """
        super(GaussianNoise, self).__init__(noisename)
        self.mu = mu  # Mean of the Gaussian noise
        self.std = std  # Standard deviation of the Gaussian noise
        self.max_step = max(max_step, 1)  # Maximum steps for adjusting the noise standard deviation
        self.intensity = intensity  # Maximum intensity of the noise

    def forward(self, marked_img: Tensor, cover_img: Tensor = None, now_step: int = 0) -> Tensor:
        """
        Applies Gaussian noise to the input image during training.

        Args:
            marked_img (Tensor): The input image to which noise will be added.
            cover_img (Tensor, optional): Not used in this implementation.
            now_step (int): Current step to adjust noise standard deviation.

        Returns:
            Tensor: The resulting image after adding Gaussian noise.
        """
        # Dynamically adjust the standard deviation based on the current step
        adjusted_std = min(now_step, self.max_step) / self.max_step * self.std
        noised_img = self.test(marked_img, cover_img, adjusted_std)
        return noised_img.clamp(0, 1.)  # Clamp values to [0, 1]

    def test(self, marked_img: Tensor, cover_img: Tensor = None, std=None) -> Tensor:
        """
        Applies Gaussian noise to the input image during testing.

        Args:
            marked_img (Tensor): The input image to which noise will be added.
            cover_img (Tensor, optional): Not used in this implementation.
            std (float): Standard deviation of the Gaussian noise during testing.

        Returns:
            Tensor: The resulting noised image.
        """
        if std is None:
            std = self.std
        # Generate Gaussian noise using torch's normal distribution
        noise = torch.normal(self.mu, std, size=marked_img.shape, device=marked_img.device)
        # Apply the noise to the input image
        noised_img = self.intensity * noise + marked_img
        return noised_img.clamp(0, 1.)  # Clamp values to [0, 1]


class SaltPepperNoise(BaseDiffAttackModel):
    def __init__(self, noise_ratio: float = 0.1, noise_prob: float = 0.5, prob: float = 0.8,
                 max_step: int = 100, noisename: str = "SaltPepperNoise"):
        """
        Initializes the SaltPepperNoise layer.

        Args:
            noise_ratio (float): Proportion of pixels to be noised (default is 0.1).
            noise_prob (float): Probability of applying "salt" (1) or "pepper" (0) to the selected pixels (default is 0.5).
            prob (float): Probability of applying the noise overall (default is 0.8).
            max_step (int): Maximum number of steps for dynamic adjustment.
        """
        super(SaltPepperNoise, self).__init__(noisename)
        self.noise_prob = max(min(noise_prob, 1.), 0.)  # Clamp noise probability between 0 and 1
        self.noise_ratio = max(min(noise_ratio, 1.), 0.)  # Clamp noise ratio between 0 and 1
        self.prob = max(min(prob, 1.), 0.)  # Clamp overall probability between 0 and 1
        self.max_step = max(max_step, 1)

    def apply_noise(self, img: torch.Tensor, noise_ratio: float, noise_mode="salt") -> torch.Tensor:
        """
        Applies differentiable salt and pepper noise to the input image.

        Args:
            img (Tensor): The input image (C, H, W).
            noise_ratio (float): Proportion of pixels to be noised.
            noise_mode (str): Mode of noise ("salt" or "pepper").

        Returns:
            Tensor: The noised image.
        """
        batch_size, channels, height, width = img.shape
        num_noisy_pixels = int(noise_ratio * height * width)  # Number of pixels to be noised

        # Generate random indices for the positions of the noisy pixels
        indices = torch.randperm(height * width, device=img.device)[:num_noisy_pixels]

        # Convert 1D indices to 2D positions (height, width)
        noisy_positions = torch.unravel_index(indices, (height, width))

        # Generate random values to decide between "salt" (1) or "pepper" (0)
        random_noise = torch.rand(num_noisy_pixels, device=img.device)
        salt_pepper_values = torch.where(random_noise < self.noise_prob,
                                         torch.ones_like(random_noise),
                                         torch.zeros_like(random_noise))
        # Create a soft mask for differentiable noise
        soft_mask = torch.ones_like(img)
        for c in range(channels):  # Apply the same noise to all channels
            soft_mask[:, c, noisy_positions[0], noisy_positions[1]] = salt_pepper_values.unsqueeze(0)

        if noise_mode == "salt":
            noised_img = img * soft_mask + (1 - soft_mask)  # Apply salt noise
        else:
            noised_img = img * soft_mask  # Apply pepper noise
        return noised_img

    def forward(self, marked_img: torch.Tensor, cover_img: torch.Tensor = None, now_step: int = 0) -> torch.Tensor:
        """
        Applies differentiable salt and pepper noise to the input image during training.

        Args:
            marked_img (Tensor): The input image (C, H, W).
            cover_img (Tensor, optional): A cover image, not used in this implementation.
            now_step (int): Current step to adjust noise ratio.

        Returns:
            Tensor: The noised image.
        """
        _noise_ratio = min(now_step / self.max_step, 1.0) * self.noise_ratio  # Adjust noise ratio
        noised_img = self.test(marked_img, cover_img, _noise_ratio)
        return noised_img

    def test(self, marked_img: torch.Tensor, cover_img: torch.Tensor = None, noise_ratio=None) -> torch.Tensor:
        """
        Applies differentiable salt and pepper noise to the input image during testing.

        Args:
            marked_img (Tensor): The input image (C, H, W).
            cover_img (Tensor, optional): Not used in this implementation.
            noise_ratio (float): Proportion of pixels to be noised during testing.

        Returns:
            Tensor: The noised image.
        """
        if noise_ratio is None:
            noise_ratio = self.noise_ratio
        noised_img = marked_img.clone()
        # Apply salt and pepper noise in equal proportions
        noised_img = self.apply_noise(noised_img, noise_ratio / 2., noise_mode="salt")
        noised_img = self.apply_noise(noised_img, noise_ratio / 2., noise_mode="pepper")
        return noised_img.clamp(0, 1.)  # Clamp the values to [0, 1]


class Resize(BaseDiffAttackModel):
    """
    Resize the image using a random scaling factor.

    Args:
        scale_p (float): Minimum scale factor (range: 0.5 to 1.0).
        prob (float): Probability of applying the resizing operation.
        mode (str): Interpolation mode, either 'nearest' or 'bilinear'.
        max_step (int): Maximum number of steps for dynamic adjustment.
    """

    def __init__(self, scale_p: float = 0.8, prob: float = 0.8, mode: str = "bilinear",
                 max_step: int = 100, noisename: str = "Resize"):
        super(Resize, self).__init__(noisename)

        # Ensure scale_p is within the range [0.5, 1.0]
        self.scale_p = max(min(scale_p, 1.0), 0.5)
        self.prob = max(min(prob, 1.0), 0.0)  # Clamp probability between 0 and 1
        self.max_step = max(max_step, 1)

        # Set the interpolation mode, default to 'bilinear' if invalid
        self.mode = mode if mode in ["nearest", "bilinear"] else "bilinear"

    def forward(self, marked_img: Tensor, cover_img: Tensor = None, now_step: int = 0) -> torch.Tensor:
        """
        Perform the resizing operation on the input image.

        Args:
            marked_img (Tensor): Input image tensor of shape (N, C, H, W).
            cover_img (Tensor, optional): Not used in this operation.
            now_step (int): Current step to adjust scale factor.

        Returns:
            Tensor: Resized image tensor of the same shape as the input.
        """
        # Calculate the adjusted scale factor based on the current step
        _scale_p = 1.0 - (1.0 - self.scale_p) * min(now_step, self.max_step) / self.max_step
        # Perform the resizing with the calculated scale
        noised_img = self.test(marked_img, cover_img, _scale_p)
        return noised_img.clamp(0.0, 1.0)  # Clamp values to [0, 1]

    def test(self, marked_img: Tensor, cover_img: Tensor = None, scale_p=None) -> torch.Tensor:
        """
        Resizes the input image during testing using a specified scale factor.

        Args:
            marked_img (Tensor): Input image tensor of shape (N, C, H, W).
            cover_img (Tensor, optional): Not used in this operation.
            scale_p (float): Scale factor for resizing during testing.

        Returns:
            Tensor: Resized image tensor of the same shape as the input.
        """
        if scale_p is None:
            scale_p = self.scale_p
        H, W = marked_img.shape[-2:]

        # Randomly determine the scaling factors for height and width
        p_h = random.uniform(scale_p, 1.0)  # Scale for height
        p_w = random.uniform(scale_p, 1.0)  # Scale for width

        # Calculate the new scaled height and width
        scaled_h = int(p_h * H)
        scaled_w = int(p_w * W)

        # Downscale the image to the new dimensions
        noised_down = F.interpolate(
            marked_img,
            size=(scaled_h, scaled_w),
            mode=self.mode
        )

        # Upscale the downscaled image back to the original dimensions
        noised_img = F.interpolate(
            noised_down,
            size=(H, W),
            mode=self.mode
        )

        return noised_img.clamp(0.0, 1.0)  # Clamp values to [0, 1]


class Rotate(BaseDiffAttackModel):
    """
    Applies a random rotation to the input image.

    Args:
        angle (int): Maximum rotation angle in degrees (0 to 360).
        prob (float): Probability of applying the rotation.
        max_step (int): Maximum number of steps for dynamic adjustment.
    """

    def __init__(self, angle: float = 180, prob: float = 0.8, max_step: int = 100, noisename: str = "Rotate"):
        super(Rotate, self).__init__(noisename)

        # Clamp the rotation angle within the range [0, 360]
        self.angle = angle
        self.prob = max(min(prob, 1.0), 0.0)  # Clamp probability between 0 and 1
        self.max_step = max(max_step, 1)

    def forward(self, marked_img: Tensor, cover_img: Tensor = None, now_step: int = 0) -> Tensor:
        """
        Applies rotation to the input image.

        Args:
            marked_img (Tensor): Input image tensor of shape (N, C, H, W).
            cover_img (Tensor, optional): Not used in this operation.
            now_step (int): Current step to adjust the rotation angle.

        Returns:
            Tensor: Rotated image tensor with the same shape as input.
        """
        # Compute the adjusted angle based on the current step
        _angle = round((min(now_step, self.max_step) / self.max_step) * self.angle)
        rdn_angle = random.uniform(-_angle, _angle)
        noised_img = self.test(marked_img, cover_img, rdn_angle)
        return noised_img.clamp(0.0, 1.0)  # Clamp values to [0, 1]

    def test(self, marked_img: Tensor, cover_img: Tensor = None, angle=None) -> Tensor:
        """
        Applies a fixed-angle rotation to the input image during testing.

        Args:
            marked_img (Tensor): Input image tensor of shape (N, C, H, W).
            cover_img (Tensor, optional): Not used in this operation.
            angle (float): Rotation angle in degrees.

        Returns:
            Tensor: Rotated image tensor with the same shape as input.
        """
        if angle is None:
            angle = self.angle
        noised_img = Fs.rotate(marked_img, angle, expand=False, center=None, fill=0)
        return noised_img.clamp(0.0, 1.0)  # Clamp values to [0, 1]


class RandomCompensateTransformer(BaseDiffAttackModel):
    def __init__(self, shift_d: int = 8, test: bool = False, max_step: int = 100,
                 noisename: str = "RandomCompensateTransformer"):
        """
        Initializes the RandomCompensateTrans layer.

        Args:
            prob (float): Probability of applying the transformation.
            shift_d (int): Maximum displacement for the image vertices during transformation (in pixels).
            test (bool): Whether the layer is in test mode (not currently used).
            max_step (int): Maximum number of steps for dynamic adjustment.
        """
        super(RandomCompensateTransformer, self).__init__(noisename)
        self.test = test
        self.shift_d = shift_d
        self.max_step = max(max_step, 1)
        # self.normalize = Normalize()  # Normalization layer (if used)

    def forward(self, marked_img: Tensor, cover_img: Tensor = None, now_step: int = 0) -> Tensor:
        """
        Applies a random perspective transformation to the input image.

        Args:
            marked_img (Tensor): The input image tensor of shape (N, C, H, W).
            cover_img (Tensor, optional): Not used in this operation.
            now_step (int): Current step to adjust the displacement.

        Returns:
            Tensor: The transformed image after applying the perspective transformation.
        """
        # Calculate the displacement based on the current step
        d = int(min(now_step, self.max_step) / self.max_step * self.shift_d) + 1
        noised_img = self.perspective(marked_img, d=d)
        return noised_img.clamp(0, 1.)  # Clamp values to [0, 1]

    def perspective(self, marked_img: Tensor, d: int = 8) -> Tensor:
        """
        Applies a random perspective transformation to the input batch of images.

        Args:
            marked_img (Tensor): Input batch of images, shape (N, C, H, W).
            d (int): Maximum displacement for the image vertices during transformation.

        Returns:
            Tensor: The transformed batch of images with the same shape (N, C, H, W).
        """
        N, C, H, W = marked_img.shape  # Get the batch size, channels, height, and width
        points_src = torch.ones(N, 4, 2)  # Source points (image corners), shape (N, 4, 2)
        points_dst = torch.ones(N, 4, 2)  # Destination points after displacement, shape (N, 4, 2)

        for i in range(N):
            # Set the source points as the original image corners
            points_src[i, :, :] = torch.tensor([
                [0., 0.],  # Top-left corner
                [W - 1., 0.],  # Top-right corner
                [W - 1., H - 1.],  # Bottom-right corner
                [0., H - 1.],  # Bottom-left corner
            ], dtype=torch.float32)

            # Randomly displace each corner within the range [-d, d]
            points_dst[i, 0] = torch.tensor([random.uniform(-d, d), random.uniform(-d, d)], dtype=points_dst.dtype,
                                            device=points_dst.device)  # Top-left
            points_dst[i, 1] = torch.tensor([random.uniform(-d, d) + W, random.uniform(-d, d)], dtype=points_dst.dtype,
                                            device=points_dst.device)  # Top-right
            points_dst[i, 2] = torch.tensor([random.uniform(-d, d) + W, random.uniform(-d, d) + H],
                                            dtype=points_dst.dtype, device=points_dst.device)  # Bottom-right
            points_dst[i, 3] = torch.tensor([random.uniform(-d, d), random.uniform(-d, d) + H], dtype=points_dst.dtype,
                                            device=points_dst.device)  # Bottom-left

        # Compute the perspective transformation matrix using the source and destination points
        M = kornia.geometry.get_perspective_transform(points_src, points_dst).to(marked_img.device)

        # Apply the perspective transformation to the input images
        noised_img = kornia.geometry.warp_perspective(marked_img, M, dsize=(H, W)).to(marked_img.device)

        return noised_img


class FieldOfViewTransformer(nn.Module):
    """
    A module to apply random affine and perspective transformations to a batch of images.
    The transformations include rotation, scaling, translation, and perspective warping.
    """

    def __init__(
            self,
            max_z_angle: int = 60,
            max_x_angle: int = 60,
            max_y_angle: int = 60,
            max_fov: int = 70,
            min_fov: int = 60,
            max_translate_factor: float = 0.2,
            max_plane_angle: int = 60,
    ):
        """
        Initialize the transformer with maximum transformation parameters.

        Args:
            max_z_angle (int): Maximum rotation angle around the z-axis (in degrees).
            max_x_angle (int): Maximum rotation angle around the x-axis (in degrees).
            max_y_angle (int): Maximum rotation angle around the y-axis (in degrees).
            max_fov (int): Maximum field of view (FOV) for perspective transformation (in degrees).
            min_fov (int): Minimum field of view (FOV) for perspective transformation (in degrees).
            max_translate_factor (float): Maximum translation factor as a fraction of image size.
            max_plane_angle (int): Maximum tilt angle for the plane (in degrees).
        """
        super().__init__()
        self.max_z_angle = max_z_angle
        self.max_x_angle = max_x_angle
        self.max_y_angle = max_y_angle
        self.max_fov = max_fov
        self.min_fov = min_fov
        self.max_translate_factor = max_translate_factor
        self.max_plane_angle = max_plane_angle

    def random_perspective_transform(self, img_shape, angle_xs, angle_ys, angle_zs, field_of_view):
        """
        Generate a perspective transformation matrix based on rotation angles and field of view.

        Args:
            img_shape (tuple): Shape of the input image (N, C, H, W).
            angle_xs (torch.Tensor): Rotation angles around the x-axis (in degrees).
            angle_ys (torch.Tensor): Rotation angles around the y-axis (in degrees).
            angle_zs (torch.Tensor): Rotation angles around the z-axis (in degrees).
            field_of_view (torch.Tensor): Field of view for perspective transformation (in degrees).

        Returns:
            torch.Tensor: Perspective transformation matrix of shape (N, 3, 3).
        """
        N, C, H, W = img_shape

        def rad(x):
            """Convert degrees to radians."""
            return x * np.pi / 180

        perspective_matrix = torch.zeros(size=(N, 3, 3), device=angle_xs.device)

        for i in range(N):
            fov = field_of_view[i]
            angle_x = angle_xs[i]
            angle_y = angle_ys[i]
            angle_z = angle_zs[i]
            z = np.sqrt(H ** 2 + W ** 2) / 2 / np.tan(rad(fov / 2))

            # Rotation matrices for x, y, and z axes
            rx = np.array(
                [
                    [1, 0, 0, 0],
                    [0, np.cos(rad(angle_x)), -np.sin(rad(angle_x)), 0],
                    [0, -np.sin(rad(angle_x)), np.cos(rad(angle_x)), 0],
                    [0, 0, 0, 1],
                ],
                np.float32,
            )

            ry = np.array(
                [
                    [np.cos(rad(angle_y)), 0, np.sin(rad(angle_y)), 0],
                    [0, 1, 0, 0],
                    [-np.sin(rad(angle_y)), 0, np.cos(rad(angle_y)), 0],
                    [0, 0, 0, 1],
                ],
                np.float32,
            )

            rz = np.array(
                [
                    [np.cos(rad(angle_z)), np.sin(rad(angle_z)), 0, 0],
                    [-np.sin(rad(angle_z)), np.cos(rad(angle_z)), 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1],
                ],
                np.float32,
            )

            # Combined rotation matrix
            r = rx.dot(ry).dot(rz)

            # Define source corners (shape: (4, 2), dtype: float32)
            p_center = np.array([W / 2, H / 2, 0, 0], np.float32)
            p1 = np.array([0, 0, 0, 0], np.float32) - p_center
            p2 = np.array([H, 0, 0, 0], np.float32) - p_center
            p3 = np.array([0, W, 0, 0], np.float32) - p_center
            p4 = np.array([H, W, 0, 0], np.float32) - p_center

            # Transform corners using rotation matrix
            dst1 = r.dot(p1)
            dst2 = r.dot(p2)
            dst3 = r.dot(p3)
            dst4 = r.dot(p4)

            list_dst = [dst1, dst2, dst3, dst4]
            org = np.array([[0, 0], [H - 1, 0], [0, W - 1], [H - 1, W - 1]], np.float32)
            dst = np.zeros((4, 2), np.float32)

            for j in range(4):
                dst[j, 0] = list_dst[j][0] * z / (z - list_dst[j][2]) + p_center[0]
                dst[j, 1] = list_dst[j][1] * z / (z - list_dst[j][2]) + p_center[1]

            # Compute perspective transformation matrix using OpenCV
            org_tensor = torch.as_tensor(org, dtype=torch.float32).unsqueeze(0)
            dst_tensor = torch.as_tensor(dst, dtype=torch.float32).unsqueeze(0)
            warpR = kornia.geometry.get_perspective_transform(org_tensor, dst_tensor)
            perspective_matrix[i] = warpR[0].to(angle_xs.device)

        return perspective_matrix

    def transform_points(self, pts, matrix):
        """
        Transform 2D points using a 3x3 transformation matrix.

        Args:
            pts (torch.Tensor): Original points of shape (N, 4, 2).
            matrix (torch.Tensor): Transformation matrix of shape (N, 3, 3).

        Returns:
            torch.Tensor: Transformed points of shape (N, 4, 2).
        """
        homogenous_points = torch.cat((pts, torch.ones((pts.shape[0], pts.shape[1], 1), device=pts.device)), dim=2)
        transformed_homogeneous = torch.bmm(matrix, homogenous_points.permute(0, 2, 1))
        transformed_points = transformed_homogeneous.permute(0, 2, 1)[:, :, :2] / transformed_homogeneous.permute(0, 2,
                                                                                                                  1)[:,
                                                                                  :, 2:]
        return transformed_points

    def forward(self, batch_img: Tensor, current_step: int, reset_step: int, batch_img_mask: Tensor = None,
                scale_factor: float = 1.1):
        """
        Apply random affine and perspective transformations to the input batch of images.

        Args:
            batch_img (torch.Tensor): Input batch of images of shape (N, C, H, W).
            current_step (int): Current step in the transformation schedule.
            reset_step (int): Step interval for resetting the transformation parameters.
            batch_img_mask (torch.Tensor, optional): Optional mask for the input images of shape (N, C, H, W).

        Returns:
            tuple: A tuple containing:
                - warped_images (torch.Tensor): Transformed images of shape (N, C, H, W).
                - warped_masks (torch.Tensor): Transformed masks of shape (N, C, H, W).
                - warped_corners (torch.Tensor): Transformed corner points of shape (N, 4, 2).
                :param scale_factor:
        """
        N, C, H, W = batch_img.shape
        min_size = min(H, W)
        self.max_scale_factor = min_size / np.sqrt(H ** 2 + W ** 2) * scale_factor

        assert self.max_fov > self.min_fov
        assert self.max_x_angle > 0
        assert self.max_y_angle > 0
        assert self.max_z_angle > 0
        assert self.max_plane_angle > 0

        if batch_img_mask is None:
            batch_img_mask = torch.ones_like(batch_img)

        # Source points (corners of the image)
        src_pts = torch.tensor([[[0.0, 0.0], [H - 1, 0.0], [0.0, W - 1], [H - 1, W - 1]]],
                               device=batch_img.device).repeat(N, 1, 1)
        centers = torch.tensor([[H / 2.0, W / 2.0]], device=batch_img.device).repeat(N, 1)

        # Calculate transformation ratio based on the current step
        current_step = current_step % reset_step
        step_ratio = 1 / (1 + np.exp(-(((current_step - 0) / (reset_step - 0)) * 15 - 7.5)))

        # Parameters for affine transformation
        max_scale_f = int(self.max_scale_factor * reset_step)
        min_scale_f = int(max_scale_f - (max_scale_f / 2) * step_ratio)
        now_scale_factor = torch.randint(low=min_scale_f, high=max_scale_f, size=(N, 1), dtype=torch.float32,
                                         device=batch_img.device).repeat(1, 2) / reset_step

        max_trans_f = self.max_translate_factor
        min_trans_f = max_trans_f * (1.0 - step_ratio)
        now_trans_factor = (torch.randint(0, 2, size=(N, 1), device=batch_img.device) - 1) * torch.randint(
            low=int(min_trans_f * H) - 1, high=int(max_trans_f * W) + 1, size=(N, 2), dtype=torch.float32,
            device=batch_img.device
        )

        max_plane_angle_f = self.max_plane_angle
        min_plane_angle_f = max_plane_angle_f * (1.0 - step_ratio)
        now_plane_angle_factor = torch.randint(
            low=int(min_plane_angle_f), high=int(max_plane_angle_f), size=(N,), dtype=torch.float32,
            device=batch_img.device
        )

        # Apply affine transformation
        affine_matrix = kornia.geometry.get_affine_matrix2d(now_trans_factor, centers, now_scale_factor,
                                                            now_plane_angle_factor)
        affine_img = kornia.geometry.warp_perspective(batch_img, affine_matrix, dsize=(H, W))
        affine_img_mask = kornia.geometry.warp_perspective(batch_img_mask, affine_matrix, dsize=(H, W))
        affine_pts = self.transform_points(src_pts, affine_matrix)

        # Parameters for perspective transformation
        max_dx_f = int(self.max_x_angle * step_ratio)
        min_dx_f = 0
        now_dx_factor = (torch.randint(0, 2, size=(N,), device=batch_img.device) - 1) * torch.randint(
            min_dx_f, max_dx_f + 1, size=(N,), device=batch_img.device
        )

        max_dy_f = int(self.max_y_angle * step_ratio)
        min_dy_f = 0
        now_dy_factor = (torch.randint(0, 2, size=(N,), device=batch_img.device) - 1) * torch.randint(
            min_dy_f, max_dy_f + 1, size=(N,), device=batch_img.device
        )

        max_dz_f = int(self.max_z_angle * step_ratio)
        min_dz_f = 0
        now_dz_factor = (torch.randint(0, 2, size=(N,), device=batch_img.device) - 1) * torch.randint(
            min_dz_f, max_dz_f + 1, size=(N,), device=batch_img.device
        )

        max_fov_f = self.max_fov
        min_fov_f = self.min_fov
        now_fov_factor = torch.randint(min_fov_f, max_fov_f, size=(N,), dtype=torch.float32, device=batch_img.device)

        # Apply perspective transformation
        perspective_matrix = self.random_perspective_transform(batch_img.shape, now_dx_factor, now_dy_factor,
                                                               now_dz_factor, now_fov_factor)
        warped_img = kornia.geometry.warp_perspective(affine_img, perspective_matrix, dsize=(H, W))
        warped_pts = self.transform_points(affine_pts, perspective_matrix)
        warped_img_mask = kornia.geometry.warp_perspective(affine_img_mask, perspective_matrix, dsize=(H, W))

        return warped_img, warped_img_mask, warped_pts


class TestJpeg(nn.Module):
    def __init__(self, Q):
        """
        Initialize the TestJpeg module.

        Args:
            Q (int): JPEG quality factor for compression.
        """
        super(TestJpeg, self).__init__()
        self.Q = Q  # Set quality factor

    def forward(self, marked_img):
        """
        Forward pass for JPEG compression and decompression.

        Args:
            marked_img (Tensor): Input image tensor with shape (N, C, H, W).

        Returns:
            Tensor: Noised image tensor after JPEG processing.
        """
        N, C, H, W = marked_img.shape  # Extract dimensions
        marked_img = torch.clip(marked_img, 0, 1)  # Clip values to range [0, 1]
        noised_image = torch.zeros_like(marked_img)  # Initialize output tensor
        for i in range(N):
            # Convert the single image to uint8 format for OpenCV
            single_image = (marked_img[i].permute(1, 2, 0) * 255).to('cpu', torch.uint8).numpy()
            if single_image.shape[2] == 1:
                single_image_for_compression = single_image[:, :, 0]
            else:
                single_image_for_compression = single_image
            result, encoded_img = cv2.imencode('.jpg', single_image_for_compression, [cv2.IMWRITE_JPEG_QUALITY, self.Q])
            if result:  # Check if encoding was successful
                compressed_img = np.frombuffer(encoded_img, dtype=np.uint8)  # Convert encoded image to numpy array
                if single_image.shape[2] == 1:
                    decoded_image = cv2.imdecode(compressed_img, cv2.IMREAD_GRAYSCALE)  # Decode the compressed image
                    noised_image[i] = torch.as_tensor(decoded_image).unsqueeze(0) / 255.
                else:
                    decoded_image = cv2.imdecode(compressed_img, cv2.IMREAD_COLOR)  # Decode the compressed image
                    noised_image[i] = torch.as_tensor(decoded_image).permute(2, 0, 1) / 255.  # Store the decoded image
        noised_image = noised_image.to(marked_img.device)  # Move output tensor to the original device
        return noised_image  # Return the processed image


class DiffJpeg(nn.Module):
    def __init__(self, Q: int, round_mode="mask"):
        """
        Initialize the differentiable JPEG compression module.

        Args:
            Q (int): Quality factor for JPEG compression (1-100). Lower values mean higher compression/lower quality.
            round_mode (str): Rounding mode for quantization. Options: "mask", "polynomial", "fourier".
        """
        super().__init__()
        # Ensure round_mode is valid
        assert round_mode in ["mask", "polynomial", "fourier"]
        self.Q = Q  # JPEG quality factor
        self.factor = None  # Scaling factor for quantization tables, computed in init_params
        self.init_params()  # Initialize parameters like matrices and tables
        self.round_mode = round_mode  # Store the rounding mode for quantization

    def forward(self, marked_img: Tensor):
        """
        Forward pass to compress and decompress an image using JPEG-like processing.

        Args:
            marked_img (Tensor): Input image tensor in RGB format, normalized to [0, 1].

        Returns:
            Tensor: Processed (noised) image tensor after compression and decompression, normalized to [0, 1].
        """
        # Scale image from [0, 1] to [0, 255] for JPEG processing
        y_cb_cr_quantized = self.compress_jpeg(marked_img * 255.)
        # Decompress and scale back to [0, 1]
        noised_img = self.decompress_jpeg(y_cb_cr_quantized, marked_img) / 255.
        return noised_img

    def init_params(self):
        """
        Initialize parameters for JPEG compression, including color conversion matrices, DCT/IDCT tensors,
        and quantization tables based on the quality factor (Q).
        """
        # Compute scaling factor based on quality (Q)
        if self.Q < 50:
            quality = 5000. / self.Q
        else:
            quality = 200. - self.Q * 2
        self.factor = quality / 100.  # Scaling factor for quantization tables

        # RGB to YCbCr conversion matrix (ITU-R BT.601 standard)
        self.rgb2ycbcr_matrix = nn.Parameter(torch.as_tensor([[0.299, 0.587, 0.114],
                                                              [-0.168736, -0.331264, 0.5],
                                                              [0.5, -0.418688, -0.081312]], dtype=torch.float32).T)
        # Shift vector for YCbCr (adds 128 to Cb and Cr channels)
        self.rgb2ycbcr_shift = nn.Parameter(torch.tensor([0., 128., 128.]))

        # Precompute 8x8 DCT tensor for 2D discrete cosine transform
        dct_tensor = np.zeros((8, 8, 8, 8), dtype=np.float32)
        for x, y, u, v in itertools.product(range(8), repeat=4):
            dct_tensor[x, y, u, v] = np.cos((2 * x + 1) * u * np.pi / 16) * np.cos((2 * y + 1) * v * np.pi / 16)
        dct_alpha = np.array([1. / np.sqrt(2)] + [1] * 7)  # Normalization for first DCT coefficient
        self.dct_tensor = nn.Parameter(torch.from_numpy(dct_tensor).float())
        self.scale = nn.Parameter(torch.from_numpy(np.outer(dct_alpha, dct_alpha) * 0.25).float())  # Scaling for DCT

        # Standard luminance (Y) quantization table (transposed for consistency)
        y_table = np.array([[16, 11, 10, 16, 24, 40, 51, 61],
                            [12, 12, 14, 19, 26, 58, 60, 55],
                            [14, 13, 16, 24, 40, 57, 69, 56],
                            [14, 17, 22, 29, 51, 87, 80, 62],
                            [18, 22, 37, 56, 68, 109, 103, 77],
                            [24, 35, 55, 64, 81, 104, 113, 92],
                            [49, 64, 78, 87, 103, 121, 120, 101],
                            [72, 92, 95, 98, 112, 100, 103, 99]], dtype=np.float32).T
        self.y_table = nn.Parameter(torch.from_numpy(y_table))

        # Standard chrominance (Cb, Cr) quantization table
        c_table = np.empty((8, 8), dtype=np.float32)
        c_table.fill(99)  # Default high quantization for lower frequencies
        c_table[:4, :4] = np.array([[17, 18, 24, 47], [18, 21, 26, 66],
                                    [24, 26, 56, 99], [47, 66, 99, 99]]).T
        self.c_table = nn.Parameter(torch.from_numpy(c_table))

        # Precompute IDCT scaling and tensor
        idct_alpha = np.array([1. / np.sqrt(2)] + [1] * 7)  # Normalization for first IDCT coefficient
        self.alpha = nn.Parameter(torch.from_numpy(np.outer(idct_alpha, idct_alpha)).float())
        idct_tensor = np.zeros((8, 8, 8, 8), dtype=np.float32)
        for x, y, u, v in itertools.product(range(8), repeat=4):
            idct_tensor[x, y, u, v] = np.cos((2 * u + 1) * x * np.pi / 16) * np.cos((2 * v + 1) * y * np.pi / 16)
        self.idct_tensor = nn.Parameter(torch.from_numpy(idct_tensor).float())

        # YCbCr to RGB conversion matrix (inverse of rgb2ycbcr_matrix)
        self.ycbcr2rgb_matrix = nn.Parameter(torch.as_tensor([[1., 0., 1.402],
                                                              [1, -0.344136, -0.714136],
                                                              [1, 1.772, 0]], dtype=torch.float32)).T
        # Shift vector for RGB conversion (subtracts 128 from Cb and Cr)
        self.ycbcr2rgb_shift = nn.Parameter(torch.tensor([0, -128., -128.]))

    def compress_jpeg(self, marked_img: Tensor):
        """
        Simulate JPEG compression process.

        Args:
            marked_img (Tensor): Input image tensor in RGB format, scaled to [0, 255].

        Returns:
            dict: Quantized YCbCr blocks after compression.
        """
        # Convert RGB to YCbCr
        y_cb_cr = self.rgb2ycbcr(marked_img)
        # Apply chroma subsampling (4:2:0)
        sub_sampled_y_cb_cr = self.chroma_subsampling(y_cb_cr)
        # Split into 8x8 blocks
        y_cb_cr_blocks = self.block_splitting(sub_sampled_y_cb_cr)
        # Apply 2D DCT to each block
        y_cb_cr_dct_blocks = self.dct_8x8(y_cb_cr_blocks)
        # Quantize DCT coefficients
        y_cb_cr_quantized = self.quantize(y_cb_cr_dct_blocks)
        return y_cb_cr_quantized

    def rgb2ycbcr(self, marked_img: Tensor):
        """
        Convert RGB image to YCbCr color space.

        Args:
            marked_img (Tensor): Input RGB image tensor [N, C, H, W], scaled to [0, 255].

        Returns:
            dict: Dictionary with 'y', 'cb', 'cr' channels as tensors.
        """
        if marked_img.shape[1] > 1:  # Check if image has multiple channels (RGB)
            image = marked_img.permute(0, 2, 3, 1)  # Reshape to [N, H, W, C]
            # Matrix multiplication for RGB to YCbCr conversion
            y_cb_cr = torch.tensordot(image, self.rgb2ycbcr_matrix.to(marked_img.device),
                                      dims=1) + self.rgb2ycbcr_shift.to(marked_img.device)
            y_cb_cr = y_cb_cr.view(image.shape).permute(0, 3, 1, 2)  # Reshape back to [N, C, H, W]
            result = {"y": y_cb_cr[:, 0, :, :].unsqueeze(1),  # Luminance
                      "cb": y_cb_cr[:, 1, :, :].unsqueeze(1),  # Blue chrominance
                      "cr": y_cb_cr[:, 2, :, :].unsqueeze(1)}  # Red chrominance
        else:  # Grayscale image
            result = {"y": marked_img}  # Only luminance channel
        return result

    def chroma_subsampling(self, y_cb_cr: dict):
        """
        Perform 4:2:0 chroma subsampling by averaging Cb and Cr channels over 2x2 blocks.

        Args:
            y_cb_cr (dict): YCbCr channels as tensors.

        Returns:
            dict: Subsampled YCbCr channels.
        """
        avg_pool = nn.AvgPool2d(kernel_size=2, stride=(2, 2), count_include_pad=False)  # 2x2 pooling
        subsampled_y_cb_cr = y_cb_cr.copy()
        for k in y_cb_cr.keys():
            if k in ["cb", "cr"]:  # Subsample only chrominance channels
                subsampled_y_cb_cr[k] = avg_pool(y_cb_cr[k])
        return subsampled_y_cb_cr

    def block_splitting(self, subsampled_y_cb_cr: dict, k: int = 8):
        """
        Split YCbCr channels into 8x8 blocks for DCT processing.

        Args:
            subsampled_y_cb_cr (dict): Subsampled YCbCr channels.
            k (int): Block size (default 8).

        Returns:
            dict: YCbCr channels split into 8x8 blocks.
        """
        blocks_y_cb_cr = subsampled_y_cb_cr.copy()
        for key in subsampled_y_cb_cr.keys():
            channel = subsampled_y_cb_cr[key].permute(0, 2, 3, 1)  # [N, H, W, C]
            N, H, W, C = channel.shape
            # Reshape into blocks: [N, H//k, k, W//k, k]
            image_reshaped = channel.view(N, H // k, k, -1, k)
            # Transpose to [N, H//k, W//k, k, k]
            image_transposed = image_reshaped.permute(0, 1, 3, 2, 4)
            # Flatten to [N, num_blocks, k, k]
            blocks = image_transposed.contiguous().view(N, -1, k, k)
            blocks_y_cb_cr[key] = blocks
        return blocks_y_cb_cr

    def dct_8x8(self, blocks_y_cb_cr):
        """
        Apply 2D Discrete Cosine Transform (DCT) to 8x8 blocks.

        Args:
            blocks_y_cb_cr (dict): YCbCr channels as 8x8 blocks.

        Returns:
            dict: DCT-transformed YCbCr blocks.
        """
        dct_blocks_y_cb_cr = blocks_y_cb_cr.copy()
        for k in blocks_y_cb_cr.keys():
            channel = blocks_y_cb_cr[k]
            channel = channel - 128  # Level shift to [-128, 127]
            # Apply 2D DCT using precomputed tensor
            dct_channel = self.scale.to(channel.device) * torch.tensordot(channel, self.dct_tensor.to(channel.device),
                                                                          dims=2).view(channel.shape)
            dct_blocks_y_cb_cr[k] = dct_channel
        return dct_blocks_y_cb_cr

    def quantize(self, dct_blocks_y_cb_cr):
        """
        Quantize DCT coefficients using quality-scaled tables and apply rounding.

        Args:
            dct_blocks_y_cb_cr (dict): DCT-transformed YCbCr blocks.

        Returns:
            dict: Quantized YCbCr blocks.
        """
        quantized_dct_blocks_y_cb_cr = dct_blocks_y_cb_cr.copy()
        for k in dct_blocks_y_cb_cr.keys():
            channel = dct_blocks_y_cb_cr[k]
            if k == "y":
                # Quantize luminance using Y table
                q_channel = channel / (self.y_table.to(channel.device) * self.factor)
                if self.round_mode == "mask":
                    q_channel = self.mask_round_y(q_channel)  # Mask-based rounding for Y
                elif self.round_mode == "polynomial":
                    q_channel = self.polynomial_round(q_channel)  # Polynomial approximation
                else:
                    q_channel = self.fourier_round(q_channel)  # Fourier-based rounding
            else:
                # Quantize chrominance using C table
                q_channel = channel / (self.c_table.to(channel.device) * self.factor)
                if self.round_mode == "mask":
                    q_channel = self.mask_round_uv(q_channel)  # Mask-based rounding for Cb/Cr
                elif self.round_mode == "polynomial":
                    q_channel = self.polynomial_round(q_channel)  # Polynomial approximation
                else:
                    q_channel = self.fourier_round(q_channel)  # Fourier-based rounding
            quantized_dct_blocks_y_cb_cr[k] = q_channel
        return quantized_dct_blocks_y_cb_cr

    def polynomial_round(self, x):
        """
        Approximate rounding using a cubic polynomial for differentiability.

        Args:
            x (Tensor): Input tensor to round.

        Returns:
            Tensor: Rounded tensor with cubic correction.
        """
        return torch.round(x) + (x - torch.round(x)) ** 3

    def fourier_round(self, input_tensor):
        """
        Approximate rounding using a Fourier series for differentiability.

        Args:
            input_tensor (Tensor): Input tensor to round.

        Returns:
            Tensor: Rounded tensor with Fourier correction.
        """
        fourier = 0
        for n in range(1, 10):  # Sum first 9 terms of Fourier series
            fourier += math.pow(-1, n + 1) / n * torch.sin(2 * math.pi * n * input_tensor)
        final_tensor = input_tensor - 1 / math.pi * fourier
        return final_tensor

    def mask_round_y(self, input_tensor):
        """
        Apply mask-based rounding to luminance (Y) channel, preserving low-frequency coefficients.

        Args:
            input_tensor (Tensor): Input tensor to round.

        Returns:
            Tensor: Masked tensor (high frequencies zeroed out).
        """
        mask = torch.zeros(1, 1, 8, 8).to(input_tensor.device)
        mask[:, :, :5, :5] = 1.  # Keep only 5x5 low-frequency coefficients
        return input_tensor * mask

    def mask_round_uv(self, input_tensor):
        """
        Apply mask-based rounding to chrominance (Cb, Cr) channels, preserving low-frequency coefficients.

        Args:
            input_tensor (Tensor): Input tensor to round.

        Returns:
            Tensor: Masked tensor (high frequencies zeroed out).
        """
        mask = torch.zeros(1, 1, 8, 8).to(input_tensor.device)
        mask[:, :, :3, :3] = 1.  # Keep only 3x3 low-frequency coefficients
        return input_tensor * mask

    def decompress_jpeg(self, y_cb_cr_quantized: dict, marked_img: Tensor):
        """
        Simulate JPEG decompression process.

        Args:
            y_cb_cr_quantized (dict): Quantized YCbCr blocks.
            marked_img (Tensor): Original image tensor for shape reference.

        Returns:
            Tensor: Reconstructed RGB image tensor.
        """
        # Dequantize DCT coefficients
        y_cb_cr_de_quantized = self.de_quantize(y_cb_cr_quantized)
        # Apply inverse DCT
        y_cb_cr_i_dct = self.idct_8x8(y_cb_cr_de_quantized)
        # Merge blocks back into full image
        y_cb_cr_merged = self.blocks_merging(y_cb_cr_i_dct, marked_img)
        # Upsample chrominance channels
        y_cb_cr_merged = self.chroma_upsampling(y_cb_cr_merged)
        # Convert back to RGB
        rgb = self.ycbcr2rgb(y_cb_cr_merged)
        return rgb

    def de_quantize(self, y_cb_cr_quantized):
        """
        Dequantize DCT coefficients by multiplying with scaled quantization tables.

        Args:
            y_cb_cr_quantized (dict): Quantized YCbCr blocks.

        Returns:
            dict: Dequantized YCbCr blocks.
        """
        y_cb_cr_dequantized = y_cb_cr_quantized.copy()
        for k in y_cb_cr_quantized.keys():
            channel = y_cb_cr_dequantized[k]
            if k == "y":
                de_q_channel = channel * (self.y_table.to(channel.device) * self.factor)
            else:
                de_q_channel = channel * (self.c_table.to(channel.device) * self.factor)
            y_cb_cr_dequantized[k] = de_q_channel
        return y_cb_cr_dequantized

    def idct_8x8(self, y_cb_cr_dequantized):
        """
        Apply 2D Inverse Discrete Cosine Transform (IDCT) to 8x8 blocks.

        Args:
            y_cb_cr_dequantized (dict): Dequantized YCbCr blocks.

        Returns:
            dict: IDCT-transformed YCbCr blocks.
        """
        y_cb_cr_dequantized_idct = y_cb_cr_dequantized.copy()
        for k in y_cb_cr_dequantized.keys():
            channel = y_cb_cr_dequantized[k]
            channel = channel * self.alpha.to(channel.device)  # Apply scaling
            # Apply 2D IDCT and level shift back to [0, 255]
            idct_channel = 0.25 * torch.tensordot(channel, self.idct_tensor.to(channel.device), dims=2) + 128
            idct_channel = idct_channel.view(channel.shape)
            y_cb_cr_dequantized_idct[k] = idct_channel
        return y_cb_cr_dequantized_idct

    def blocks_merging(self, y_cb_cr_idct_blocks, marked_img: Tensor, k: int = 8):
        """
        Merge 8x8 blocks back into full YCbCr channels.

        Args:
            y_cb_cr_idct_blocks (dict): IDCT-transformed YCbCr blocks.
            marked_img (Tensor): Original image tensor for shape reference.
            k (int): Block size (default 8).

        Returns:
            dict: Merged YCbCr channels.
        """
        y_cb_cr_idct_imgs = y_cb_cr_idct_blocks.copy()
        for key in y_cb_cr_idct_blocks.keys():
            channel = y_cb_cr_idct_blocks[key]
            N, C, H, W = marked_img.shape
            if key in ["cb", "cr"]:  # Chrominance channels are subsampled
                H, W = H // 2, W // 2
            # Reshape blocks back into image: [N, H//k, W//k, k, k]
            image_reshaped = channel.view(N, H // k, W // k, k, k)
            # Transpose to [N, H//k, k, W//k, k]
            image_transposed = image_reshaped.permute(0, 1, 3, 2, 4)
            # Merge into [N, H, W]
            channel_img = image_transposed.contiguous().view(N, H, W)
            y_cb_cr_idct_imgs[key] = channel_img
        return y_cb_cr_idct_imgs

    def chroma_upsampling(self, y_cb_cr_idct_imgs, k: int = 2):
        """
        Upsample chrominance channels (Cb, Cr) to match luminance (Y) resolution.

        Args:
            y_cb_cr_idct_imgs (dict): Merged YCbCr channels.
            k (int): Upsampling factor (default 2).

        Returns:
            dict: Upsampled YCbCr channels.
        """
        y_cb_cr_idct_unsample_imgs = y_cb_cr_idct_imgs.copy()
        for key in y_cb_cr_idct_imgs.keys():
            if key in ["cb", "cr"]:
                channel_idct = y_cb_cr_idct_imgs[key]
                channel = channel_idct.unsqueeze(-1)
                # Repeat each pixel k times in both dimensions
                channel = channel.repeat(1, 1, k, k)
                # Reshape to full resolution
                channel = channel.view(-1, channel_idct.shape[1] * k, channel_idct.shape[2] * k)
                y_cb_cr_idct_unsample_imgs[key] = channel
        return y_cb_cr_idct_unsample_imgs

    def ycbcr2rgb(self, y_cb_cr_idct_unsample_imgs: dict):
        """
        Convert YCbCr image back to RGB color space.

        Args:
            y_cb_cr_idct_unsample_imgs (dict): Upsampled YCbCr channels.

        Returns:
            Tensor: Reconstructed RGB image tensor [N, C, H, W].
        """
        channel_len = len(y_cb_cr_idct_unsample_imgs)
        if channel_len == 1:  # Grayscale image
            rgb = y_cb_cr_idct_unsample_imgs["y"].unsqueeze(1)
            return rgb
        else:  # Color image
            y = y_cb_cr_idct_unsample_imgs["y"].unsqueeze(3)
            cb = y_cb_cr_idct_unsample_imgs["cb"].unsqueeze(3)
            cr = y_cb_cr_idct_unsample_imgs["cr"].unsqueeze(3)
            # Concatenate channels along channel dimension
            cat_y_cb_cr = torch.cat([y, cb, cr], dim=3)
            # Convert YCbCr to RGB with matrix multiplication and shift
            rgb = torch.tensordot(cat_y_cb_cr + self.ycbcr2rgb_shift.to(cat_y_cb_cr.device),
                                  self.ycbcr2rgb_matrix.to(cat_y_cb_cr.device), dims=1)
            rgb = rgb.view(cat_y_cb_cr.shape).permute(0, 3, 1, 2)  # Reshape to [N, C, H, W]
            return rgb


class JpegMask(BaseDiffAttackModel):
    def __init__(self, Q: int = 50, max_step: int = 100, noisename: str = "JpegMask"):
        """
        Initialize the Jpeg module.

        Args:
            Q (int): JPEG quality factor, clamped between 50 and 100.
            max_step (int): Maximum number of steps for quality adjustment.
        """
        super(JpegMask, self).__init__(noisename)
        self.Q = min(max(10, Q), 100)  # Clamp quality factor to [50, 100]
        self.max_step = max(max_step, 1)  # Store maximum step

    def gamma_density(self, Q, shape=2.0, scale=1.0):
        """
        Calculate gamma density for quality adjustment.

        Args:
            Q (int): Quality factor.
            shape (float): Shape parameter for the gamma distribution.
            scale (float): Scale parameter for the gamma distribution.

        Returns:
            List[float]: List of gamma density values.
        """
        values = torch.arange(Q, 100, dtype=torch.float32)  # Create range of quality values
        gamma_dist = torch.distributions.Gamma(concentration=shape, rate=1.0 / scale)  # Create gamma distribution
        gamma_density = gamma_dist.log_prob(values).exp()  # Compute gamma density
        return gamma_density.tolist()  # Return as list

    def forward(self, marked_img: Tensor, cover_img=None, now_step: int = 1):
        """
        Forward pass for JPEG processing with dynamic quality adjustment.

        Args:
            marked_img (Tensor): Input image tensor.
            cover_img (Tensor, optional): Cover image tensor (unused).
            now_step (int): Current step for quality adjustment.

        Returns:
            Tensor: Noised image tensor after JPEG processing.
        """
        # Calculate dynamic quality factor based on current step
        _Q = 100 - int((100 - self.Q) * min(now_step, self.max_step) / self.max_step) - 1
        # Uncomment the following lines if weighted sampling is needed
        # weights = self.gamma_density(_Q - 1)
        # Q_list = range(_Q - 1, 100)
        # _Q = random.choices(Q_list, weights=weights)[0]

        # Process the marked image with DiffJpeg
        noised_img = DiffJpeg(_Q, round_mode="mask")(marked_img)
        return noised_img.clamp(0, 1.)  # Clamp values to [0, 1]

    def test(self, marked_img: Tensor, cover_img=None, Q=None):
        """
        Test mode for JPEG processing.

        Args:
            marked_img (Tensor): Input image tensor.
            cover_img (Tensor, optional): Cover image tensor (unused).
            Q (int): JPEG quality factor for testing.

        Returns:
            Tensor: Noised image tensor after JPEG processing.
        """
        if Q is None:
            Q = self.Q
        noised_img = TestJpeg(Q)(marked_img)  # Process the image with TestJpeg
        return noised_img.clamp(0, 1.)  # Clamp values to [0, 1]


class JpegPolynomial(BaseDiffAttackModel):
    def __init__(self, Q: int = 50, max_step: int = 100, noisename: str = "JpegPolynomial"):
        """
        Initialize the Jpeg module.

        Args:
            Q (int): JPEG quality factor, clamped between 50 and 100.
            max_step (int): Maximum number of steps for quality adjustment.
        """
        super(JpegPolynomial, self).__init__(noisename)
        self.Q = min(max(10, Q), 100)  # Clamp quality factor to [50, 100]
        self.max_step = max(max_step, 1)  # Store maximum step

    def gamma_density(self, Q, shape=2.0, scale=1.0):
        """
        Calculate gamma density for quality adjustment.

        Args:
            Q (int): Quality factor.
            shape (float): Shape parameter for the gamma distribution.
            scale (float): Scale parameter for the gamma distribution.

        Returns:
            List[float]: List of gamma density values.
        """
        values = torch.arange(Q, 100, dtype=torch.float32)  # Create range of quality values
        gamma_dist = torch.distributions.Gamma(concentration=shape, rate=1.0 / scale)  # Create gamma distribution
        gamma_density = gamma_dist.log_prob(values).exp()  # Compute gamma density
        return gamma_density.tolist()  # Return as list

    def forward(self, marked_img: Tensor, cover_img=None, now_step: int = 1):
        """
        Forward pass for JPEG processing with dynamic quality adjustment.

        Args:
            marked_img (Tensor): Input image tensor.
            cover_img (Tensor, optional): Cover image tensor (unused).
            now_step (int): Current step for quality adjustment.

        Returns:
            Tensor: Noised image tensor after JPEG processing.
        """
        # Calculate dynamic quality factor based on current step
        _Q = 100 - int((100 - self.Q) * min(now_step, self.max_step) / self.max_step) - 1
        # Uncomment the following lines if weighted sampling is needed
        # weights = self.gamma_density(_Q - 1)
        # Q_list = range(_Q - 1, 100)
        # _Q = random.choices(Q_list, weights=weights)[0]

        # Process the marked image with DiffJpeg
        noised_img = DiffJpeg(_Q, round_mode="polynomial")(marked_img)
        return noised_img.clamp(0, 1.)  # Clamp values to [0, 1]

    def test(self, marked_img: Tensor, cover_img=None, Q=None):
        """
        Test mode for JPEG processing.

        Args:
            marked_img (Tensor): Input image tensor.
            cover_img (Tensor, optional): Cover image tensor (unused).
            Q (int): JPEG quality factor for testing.

        Returns:
            Tensor: Noised image tensor after JPEG processing.
        """
        if Q is None:
            Q = self.Q
        noised_img = TestJpeg(Q)(marked_img)  # Process the image with TestJpeg
        return noised_img.clamp(0, 1.)  # Clamp values to [0, 1]


class JpegFourier(BaseDiffAttackModel):
    def __init__(self, Q: int = 50, max_step: int = 100, noisename: str = "JpegFourier"):
        """
        Initialize the Jpeg module.

        Args:
            Q (int): JPEG quality factor, clamped between 50 and 100.
            max_step (int): Maximum number of steps for quality adjustment.
            round_mode (str): Rounding mode for quantization.
        """
        super(JpegFourier, self).__init__(noisename)
        self.Q = min(max(10, Q), 100)  # Clamp quality factor to [50, 100]
        self.max_step = max(max_step, 1)  # Store maximum step

    def gamma_density(self, Q, shape=2.0, scale=1.0):
        """
        Calculate gamma density for quality adjustment.

        Args:
            Q (int): Quality factor.
            shape (float): Shape parameter for the gamma distribution.
            scale (float): Scale parameter for the gamma distribution.

        Returns:
            List[float]: List of gamma density values.
        """
        values = torch.arange(Q, 100, dtype=torch.float32)  # Create range of quality values
        gamma_dist = torch.distributions.Gamma(concentration=shape, rate=1.0 / scale)  # Create gamma distribution
        gamma_density = gamma_dist.log_prob(values).exp()  # Compute gamma density
        return gamma_density.tolist()  # Return as list

    def forward(self, marked_img: Tensor, cover_img=None, now_step: int = 1):
        """
        Forward pass for JPEG processing with dynamic quality adjustment.

        Args:
            marked_img (Tensor): Input image tensor.
            cover_img (Tensor, optional): Cover image tensor (unused).
            now_step (int): Current step for quality adjustment.

        Returns:
            Tensor: Noised image tensor after JPEG processing.
        """
        # Calculate dynamic quality factor based on current step
        _Q = 100 - int((100 - self.Q) * min(now_step, self.max_step) / self.max_step) - 1
        # Uncomment the following lines if weighted sampling is needed
        # weights = self.gamma_density(_Q - 1)
        # Q_list = range(_Q - 1, 100)
        # _Q = random.choices(Q_list, weights=weights)[0]

        # Process the marked image with DiffJpeg
        noised_img = DiffJpeg(_Q, round_mode="fourier")(marked_img)
        return noised_img.clamp(0, 1.)  # Clamp values to [0, 1]

    def test(self, marked_img: Tensor, cover_img=None, Q=None):
        """
        Test mode for JPEG processing.

        Args:
            marked_img (Tensor): Input image tensor.
            cover_img (Tensor, optional): Cover image tensor (unused).
            Q (int): JPEG quality factor for testing.

        Returns:
            Tensor: Noised image tensor after JPEG processing.
        """
        if Q is None:
            Q = self.Q
        noised_img = TestJpeg(Q)(marked_img)  # Process the image with TestJpeg
        return noised_img.clamp(0, 1.)  # Clamp values to [0, 1]


class PIMoG(BaseDiffAttackModel):
    def __init__(self, noisename="ScreenCapture"):
        """
        ScreenCapture Class simulates screen-shooting noise, including light distortion and Moire patterns.

        This noiselayer is proposed by the work in:
        H. Fang, Z. Jia, Z. Ma, E. Chang, and W. Zhang.
        PIMoG: An Effective Screen-shooting Noise-Layer Simulation for Deep-Learning-Based Watermarking Network.
        Proceedings of the 30th ACM International Conference on Multimedia (ACM MM), 2022.

        [Code]: https://github.com/FangHanNUS/PIMoG-An-Effective-Screen-shooting-Noise-Layer-Simulation-for-Deep-Learning-Based-Watermarking-Netw/
        """
        super(PIMoG, self).__init__(noisename)

    # Generate Moire pattern based on polar coordinates
    def MoireGen(self, p_size, theta, center_x, center_y):
        """
        Generates a Moire pattern with specified parameters, simulating the screen capture effect.

        Args:
            p_size (int): Size of the generated pattern.
            theta (float): Rotation angle in degrees.
            center_x (float): X-coordinate of the pattern center.
            center_y (float): Y-coordinate of the pattern center.

        Returns:
            M (numpy array): Generated Moire pattern matrix.
        """
        z = np.zeros((p_size, p_size))
        for i in range(p_size):
            for j in range(p_size):
                # Calculate radial and linear cosine components to simulate Moire pattern
                z1 = 0.5 + 0.5 * math.cos(2 * math.pi * np.sqrt((i + 1 - center_x) ** 2 + (j + 1 - center_y) ** 2))
                z2 = 0.5 + 0.5 * math.cos(
                    math.cos(theta / 180 * math.pi) * (j + 1) + math.sin(theta / 180 * math.pi) * (i + 1))
                z[i, j] = np.min([z1, z2])
        M = (z + 1) / 2
        return M

    # Light distortion simulation
    def Light_Distortion(self, c, embed_image):
        """
        Simulates light distortion over an embedded image by altering brightness gradients or introducing radial distortion.

        Args:
            c (int): Random selection parameter to choose between gradient or radial distortion.
            embed_image (Tensor): The input image with the embedded watermark.

        Returns:
            O (numpy array): Light distortion mask applied to the image.
        """
        mask = np.zeros((embed_image.shape))
        mask_2d = np.zeros((embed_image.shape[2], embed_image.shape[3]))
        a = 0.7 + np.random.rand(1) * 0.2
        b = 1.1 + np.random.rand(1) * 0.2

        if c == 0:
            direction = np.random.randint(1, 5)
            for i in range(embed_image.shape[2]):
                mask_2d[i, :] = -((b - a) / (mask.shape[2] - 1)) * (i - mask.shape[3]) + a
            O = np.rot90(mask_2d, direction - 1)  # Rotating mask based on random direction
            for batch in range(embed_image.shape[0]):
                for channel in range(embed_image.shape[1]):
                    mask[batch, channel, :, :] = mask_2d
        else:
            # Radial light distortion based on random center
            x = np.random.randint(0, mask.shape[2])
            y = np.random.randint(0, mask.shape[3])
            max_len = np.max(
                [np.sqrt(x ** 2 + y ** 2), np.sqrt((x - 255) ** 2 + y ** 2), np.sqrt(x ** 2 + (y - 255) ** 2),
                 np.sqrt((x - 255) ** 2 + (y - 255) ** 2)])
            for i in range(mask.shape[2]):
                for j in range(mask.shape[3]):
                    mask[:, :, i, j] = np.sqrt((i - x) ** 2 + (j - y) ** 2) / max_len * (a - b) + b
            O = mask
        return O

    # Moire distortion simulation
    def Moire_Distortion(self, embed_image):
        """
        Simulates Moire distortion on the embedded image by generating multiple Moire patterns.

        Args:
            embed_image (Tensor): The input image with the embedded watermark.

        Returns:
            Z (numpy array): Moire distortion pattern applied to the image.
        """
        Z = np.zeros((embed_image.shape))
        for i in range(3):  # Apply Moire pattern on each channel
            theta = np.random.randint(0, 180)
            center_x = np.random.rand(1) * embed_image.shape[2]
            center_y = np.random.rand(1) * embed_image.shape[3]
            M = self.MoireGen(embed_image.shape[2], theta, center_x, center_y)
            Z[:, i, :, :] = M
        return Z

    def forward(self, embed_image, cover_img: Tensor = None, now_step: int = 0):
        """
        Applies combined light distortion and Moire distortion to the input image.

        Args:
            embed_image (Tensor): The input image with the embedded watermark.
            cover_img (Tensor): The original cover image (not used in current implementation).

        Returns:
            noised_image (Tensor): The distorted image after applying noise layers.
        """
        # Randomly select distortion method (light gradient or radial)
        c = np.random.randint(0, 2)
        L = self.Light_Distortion(c, embed_image)
        Z = self.Moire_Distortion(embed_image) * 2 - 1  # Scale Moire pattern

        # Copy distortions and apply to the embedded image
        Li = L.copy()
        Mo = Z.copy()
        noised_image = embed_image * torch.from_numpy(Li).to(embed_image.device) * 0.85 + torch.from_numpy(Mo).to(
            embed_image.device) * 0.15

        # Gaussian noise
        noised_image = noised_image + 0.001 ** 0.5 * torch.randn(noised_image.size()).to(embed_image.device)
        return noised_image.clamp(0, 1.).to(embed_image.dtype)


class StegaStamp(nn.Module):
    def __init__(self, rnd_trans=0.1, rnd_bri_ramp=1000, rnd_sat_ramp=1000, rnd_hue_ramp=1000,
                 rnd_noise_ramp=1000, contrast_ramp=1000,
                 jpeg_quality_ramp=1000, rnd_bri=0.3, rnd_hue=0.1, jpeg_quality=50, rnd_noise=0.02, contrast_low=0.5,
                 contrast_high=1.5, rnd_sat=1.0, no_jpeg=True, borders="white"):
        super().__init__()
        self.rnd_trans = rnd_trans
        self.rnd_bri_ramp = rnd_bri_ramp
        self.rnd_sat_ramp = rnd_sat_ramp
        self.rnd_hue_ramp = rnd_hue_ramp
        self.rnd_noise_ramp = rnd_noise_ramp
        self.contrast_ramp = contrast_ramp
        self.jpeg_quality_ramp = jpeg_quality_ramp
        self.rnd_bri = rnd_bri
        self.rnd_hue = rnd_hue
        self.jpeg_quality = jpeg_quality
        self.rnd_noise = rnd_noise
        self.contrast_low = contrast_low
        self.contrast_high = contrast_high
        self.rnd_sat = rnd_sat
        self.no_jpeg = no_jpeg
        self.borders = borders

    def __call__(self, encoded_image, cover_img=None, now_step=0):
        ramp_fn = lambda ramp: np.min([now_step / ramp, 1.])
        rnd_bri = ramp_fn(self.rnd_bri_ramp) * self.rnd_bri
        rnd_hue = ramp_fn(self.rnd_hue_ramp) * self.rnd_hue
        rnd_brightness = get_rnd_brightness_torch(rnd_bri, rnd_hue, encoded_image.shape[0]).to(
            encoded_image.device)  # [batch_size, 3, 1, 1]
        jpeg_quality = 100. - torch.rand(1)[0] * ramp_fn(self.jpeg_quality_ramp) * (100. - self.jpeg_quality)
        rnd_noise = torch.rand(1)[0] * ramp_fn(self.rnd_noise_ramp) * self.rnd_noise
        contrast_low = 1. - (1. - self.contrast_low) * ramp_fn(self.contrast_ramp)
        contrast_high = 1. + (self.contrast_high - 1.) * ramp_fn(self.contrast_ramp)
        contrast_params = [contrast_low, contrast_high]
        rnd_sat = torch.rand(1)[0] * ramp_fn(self.rnd_sat_ramp) * self.rnd_sat

        # blur
        N_blur = 7
        f = random_blur_kernel(probs=[.25, .25], N_blur=N_blur, sigrange_gauss=[1., 3.], sigrange_line=[.25, 1.],
                               wmin_line=3).to(encoded_image.device)
        encoded_image = F.conv2d(encoded_image, f, bias=None, padding=int((N_blur - 1) / 2))

        # noise
        noise = torch.normal(mean=0, std=rnd_noise, size=encoded_image.size(), dtype=torch.float32).to(
            encoded_image.device)
        encoded_image = encoded_image + noise
        encoded_image = torch.clamp(encoded_image, 0, 1)

        # contrast & brightness
        contrast_scale = torch.Tensor(encoded_image.size()[0]).uniform_(contrast_params[0], contrast_params[1])
        contrast_scale = contrast_scale.reshape(encoded_image.size()[0], 1, 1, 1).to(encoded_image.device)
        encoded_image = encoded_image * contrast_scale
        encoded_image = encoded_image + rnd_brightness
        encoded_image = torch.clamp(encoded_image, 0, 1)

        # saturation
        sat_weight = torch.FloatTensor([.3, .6, .1]).reshape(1, 3, 1, 1).to(encoded_image.device)
        encoded_image_lum = torch.mean(encoded_image * sat_weight, dim=1).unsqueeze_(1)
        encoded_image = (1 - rnd_sat) * encoded_image + rnd_sat * encoded_image_lum

        # jpeg
        encoded_image = encoded_image.reshape([-1, 3, encoded_image.shape[2], encoded_image.shape[3]])
        if not self.no_jpeg:
            encoded_image = jpeg_compress_decompress(encoded_image, rounding=round_only_at_0, quality=jpeg_quality)
        return encoded_image.clamp(0, 1.)
