# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT
import torch
import random
from torch import nn
from typing import List, Dict
from watermarklab.attackers.testattackers import *
from watermarklab.utils.basemodel import BaseDiffAttackModel, AttackerWithFactors

__all__ = ["DistortionLoader", "AttackersWithFactorsModel"]


class DistortionLoader(nn.Module):
    """
    A module that applies a sequence of noise layers to an image, simulating distortions.

    Parameters:
    -----------
    noise_list : List[BaseDiffNoiseModel]
        A list of noise models that will be applied sequentially.
    max_step : int, optional (default=100)
        The maximum training step, used for scheduling the number of applied noise layers.
    k_min : int, optional (default=1)
        The minimum number of noise layers to apply.
    k_max : int, optional (default=2)
        The maximum number of noise layers to apply. If larger than `len(noise_list)`, it will be clipped.

    Methods:
    --------
    stair_k(now_step: int) -> int:
        Determines the number of noise layers (`k`) to apply based on a step-wise (staircase) schedule.
    parabolic_k(now_step: int, gamma: float = 1.3) -> int:
        Determines `k` using a parabolic function, allowing a smooth increase over time.
    forward(marked_img: torch.Tensor, cover_img: torch.Tensor, now_step: int = 0) -> torch.Tensor:
        Applies `k` randomly selected noise layers sequentially to the marked image.
    """

    def __init__(self, noise_list: List[BaseDiffAttackModel], k_mode: str = "stair_k", k_min: int = 1, k_max: int = 2,
                 max_step=1):
        super(DistortionLoader, self).__init__()
        assert k_mode in ["stair_k", "parabolic_k"]
        self.k_mode = k_mode
        self.max_step = max_step
        self.k_min = k_min  # The minimum number of noise layers to apply
        self.k_max = min(k_max, len(noise_list))  # Ensure k_max does not exceed the available noise layers

        self.noise_list = noise_list
        # Ensure the noise list is sorted if required (note: sorting may require defining a comparison key)
        # self.noise_list.sort(key=lambda x: x.some_attribute)  # Uncomment and modify if sorting is necessary

    def stair_k(self, now_step: int) -> int:
        """
        Determines the number of noise layers (`k`) to apply using a staircase function.
        The number of noise layers increases in discrete steps as training progresses.

        Parameters:
        -----------
        now_step : int
            The current training step.

        Returns:
        --------
        k : int
            The number of noise layers to apply.
        """
        if self.k_max == self.k_min:
            return self.k_min  # Avoid division by zero if k_max == k_min

        total_steps = self.k_max - self.k_min + 1  # Total steps for transitioning between k_min and k_max
        max_steps_per_k = self.max_step / total_steps  # Steps required before incrementing k
        step_index = int(now_step // max_steps_per_k)  # Determine which level k should be at
        k = self.k_min + step_index
        return min(k, self.k_max)  # Ensure k does not exceed k_max

    def parabolic_k(self, now_step: int, gamma: float = 1.3) -> int:
        """
        Determines the number of noise layers (`k`) using a parabolic growth function.
        The number of layers smoothly increases over time.

        Parameters:
        -----------
        now_step : int
            The current training step.
        gamma : float, optional (default=1.3)
            A parameter controlling the curvature of the growth function.

        Returns:
        --------
        k : int
            The number of noise layers to apply.
        """
        # Factor smoothly transitions from 0 to 1 as training progresses
        factor = 1.0 if now_step >= self.max_step else (now_step / self.max_step) ** gamma
        k = self.k_min + (self.k_max - self.k_min) * factor  # Compute k using the parabolic function
        return max(self.k_min, int(k))  # Ensure k is at least k_min

    def forward(self, marked_img: torch.Tensor, cover_img: torch.Tensor, now_step: int = 0) -> torch.Tensor:
        """
        Applies randomly selected noise layers to the marked image.

        Parameters:
        -----------
        marked_img : torch.Tensor
            The input image to which noise is applied.
        cover_img : torch.Tensor
            The original reference image (may be used by noise models).
        now_step : int, optional (default=0)
            The current training step, used to determine `k`.

        Returns:
        --------
        noised_img : torch.Tensor
            The distorted image after applying `k` noise layers.
        """
        # Determine the number of noise layers to apply
        if self.k_mode == "stair_k":
            k = self.stair_k(now_step)  # Alternative: use self.parabolic_k(now_step)
        else:
            k = self.parabolic_k(now_step)  # Alternative: use self.parabolic_k(now_step)

        # Randomly select `k` noise models from the available list
        selected_keys = random.sample(range(len(self.noise_list)), k)

        # Apply the selected noise layers sequentially
        noised_img = marked_img
        for key in selected_keys:
            noised_img = self.noise_list[key](noised_img, cover_img, now_step)

        return noised_img.clamp(0, 1)  # Ensure pixel values remain in the valid range [0, 1]


class AttackersWithFactorsModel(list):
    """
    A class that extends Python's built-in list to hold attackers with their factors.
    This class behaves exactly like a regular list but provides a convenient way
    to initialize with a comprehensive set of default image attackers for adversarial attacks.

    The list is lazily initialized to prevent creation when the module is imported,
    only creating the attackers when actually needed. This improves import performance
    and memory usage.

    The default attackers cover various categories of image transformations and attacks:
    - Diffusion-based attacks for regenerating images
    - Neural compression attacks using VAE models
    - Noise injection attacks (salt & pepper, Gaussian, Poisson)
    - Blur attacks (Gaussian, median, mean, unsharp masking)
    - Image compression attacks (JPEG, JPEG2000, WebP)
    - Geometric transformations (resize, rotate, crop, etc.)
    - Color transformations (contrast, saturation, hue shifts, etc.)
    """

    def __init__(self, default_attackers: List[AttackerWithFactors] = None, attacker_groups: Dict = None):
        """
        Initialize the AttackersWithFactorsModel with either provided attackers or defaults.

        Args:
            default_attackers (List[AttackerWithFactors]): A list of pre-defined attackers.
                If provided, these attackers will be used instead of the default comprehensive set.
                If None, a default set of 40+ different attackers across multiple categories
                will be automatically created and populated.
        """
        # Call the parent list constructor to initialize the underlying list structure
        super().__init__()

        self.attacker_groups = {
            "Compression": [
                "BMshj2018Factorized",
                "BMshj2018Hyperprior",
                "MBT2018Mean",
                "MBT2018",
                "Cheng2020",
                "JPEGCompression",
                "JPEG2000Compression",
                "WebPCompression"
            ],
            "Noise": [
                "Salt&PepperNoise",
                "GaussianNoise",
                "PoissonNoise",
                "PixelDropout"
            ],
            "Blur": [
                "GaussianBlur",
                "MedianFilter",
                "MeanFilter"
            ],
            "Geometric": [
                "Resize",
                "Rotation",
                "Crop",
                "Cropout",
                "Flip",
                "RegionZoom",
                "TranslationAttack"
            ],
            "Color": [
                "ContrastReduction",
                "UnsharpMasking"
                "ContrastEnhancement",
                "ColorQuantization",
                "ChromaticAberration",
                "GammaCorrection",
                "HueShift",
                "Darken",
                "Brighten",
                "Desaturate",
                "Oversaturate"
            ],
            "Diffusion": [
                "Diffusion-Regen",
                "Mult-Diffusion"
            ]
        }
        if attacker_groups is not None:
            self.attacker_groups = attacker_groups
        # Store the provided attackers or create default ones
        if default_attackers is not None:
            # Extend this list instance with the provided attackers
            # This allows users to provide their own custom set of attackers
            self.extend(default_attackers)
        else:
            # Create the comprehensive default list of attackers with their factors
            # Each attacker is configured with specific parameter ranges for systematic testing
            default_attackers_list = [
                # ===================================================================
                # Diffusion Attacks - Regenerate images using diffusion models
                # These attacks attempt to reconstruct images through diffusion processes
                # ===================================================================
                AttackerWithFactors(
                    attacker=DiffuseAttack(),  # Regenerates images using diffusion process
                    attackername="Diffusion-Regen",  # Regeneration via diffusion
                    factors=[20, 40, 60, 80, 100, 120, 140, 160, 180, 200],  # Timestep values
                    factorsymbol=r"$t$"  # Timestep parameter symbol
                ),
                AttackerWithFactors(
                    attacker=MultiDiffuseAttack(noise_step=60),  # Multi-step diffusion attack
                    attackername="Mult-Diffusion",  # Multi-step diffusion process
                    factors=[1, 2, 3, 4, 6],  # Number of diffusion steps
                    factorsymbol=r"$N$"  # Number of steps parameter symbol
                ),

                # ===================================================================
                # Neural Compression Attacks - Compress images using learned models  ***************BMshj2018
                # Variational AutoEncoder (VAE) based compression from different papers
                # ===================================================================

                AttackerWithFactors(
                    attacker=VAE_BMshj2018FactorizedAttack(),
                    attackername="BMshj2018Factorized",
                    factors=[1, 2, 3, 4, 5, 6, 7, 8],
                    factorsymbol=r"$q$"
                ),
                AttackerWithFactors(
                    attacker=VAE_BMshj2018HyperpriorAttack(),
                    attackername="BMshj2018Hyperprior",
                    factors=[1, 2, 3, 4, 5, 6, 7, 8],
                    factorsymbol=r"$q$"
                ),
                AttackerWithFactors(
                    attacker=VAE_MBT2018MeanAttack(),
                    attackername="MBT2018Mean",
                    factors=[1, 2, 3, 4, 5, 6, 7, 8],
                    factorsymbol=r"$q$"
                ),
                AttackerWithFactors(
                    attacker=VAE_MBT2018Attack(),
                    attackername="MBT2018",
                    factors=[1, 2, 3, 4, 5, 6, 7, 8],
                    factorsymbol=r"$q$"
                ),
                AttackerWithFactors(
                    attacker=VAE_Cheng2020Attack(),
                    attackername="Cheng2020",
                    factors=[1, 2, 3, 4, 5, 6],  # Quality levels
                    factorsymbol=r"$q$"  # Quality parameter symbol
                ),

                # ===================================================================
                # Image Compression Attacks - Compress images using standard codecs
                # Simulate lossy compression artifacts from common image formats
                # ===================================================================
                AttackerWithFactors(
                    attacker=Jpeg(),  # Apply JPEG compression
                    attackername="JPEGCompression",  # Lossy compression standard
                    factors=[90, 80, 70, 60, 50, 40, 30, 20, 10],  # Quality factor (higher = better)
                    factorsymbol=r"$q$"  # Quality parameter symbol
                ),
                AttackerWithFactors(
                    attacker=Jpeg2000(),  # Apply JPEG 2000 compression
                    attackername="JPEG2000Compression",  # Wavelet-based compression [1000, 800, 600, 500, 400, 300, 200, 100, 50]
                    factors=[90, 80, 70, 60, 50, 40, 30, 20, 10],
                    # Compression ratio (higher = more compression)
                    factorsymbol=r"$c$"  # Compression ratio symbol
                ),
                AttackerWithFactors(
                    attacker=WebPCompression(),  # Apply WebP compression
                    attackername="WebPCompression",  # Google's modern image format
                    factors=[90, 80, 70, 60, 50, 40, 30, 20, 10],  # Quality factor
                    factorsymbol=r"$q$"  # Quality parameter symbol
                ),
                # ===================================================================
                # Noise Attacks - Add various types of noise to images
                # Simulate real-world sensor noise and transmission errors
                # ===================================================================
                AttackerWithFactors(
                    attacker=SaltPepperNoise(),
                    attackername="Salt&PepperNoise",
                    factors=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
                    factorsymbol=r"$p$"
                ),
                AttackerWithFactors(
                    attacker=GaussianNoise(),  # Add Gaussian white noise
                    attackername="GaussianNoise",  # Normal distribution noise
                    factors=[0.01, 0.03, 0.05, 0.07, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9],  # Standard deviation
                    factorsymbol=r"$\sigma$"  # Standard deviation symbol
                ),
                AttackerWithFactors(
                    attacker=PoissonNoise(),  # Add Poisson noise (photon noise)
                    attackername="PoissonNoise",  # Quantum noise in low-light conditions
                    factors=[30., 25., 20., 15., 10.0, 5.0, 2.0, 1.0, 0.5, 0.3],  # Scaling factor (inverse)
                    factorsymbol=r"$\alpha$"  # Scaling parameter symbol
                ),

                # ===================================================================
                # Blur Attacks - Apply various blur filters to images
                # Simulate camera motion, defocus, and image processing artifacts
                # ===================================================================
                AttackerWithFactors(
                    attacker=GaussianBlur(),  # Apply Gaussian blur
                    attackername="GaussianBlur",  # Normal distribution kernel blur
                    factors=[0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],  # Standard deviation
                    factorsymbol=r"$\sigma$"  # Standard deviation symbol
                ),
                AttackerWithFactors(
                    attacker=MedianFilter(),  # Apply median filter (edge-preserving)
                    attackername="MedianFilter",  # Non-linear filter for salt&pepper noise
                    factors=[3, 5, 7, 9, 11, 13, 15, 17, 21, 23],  # Kernel size (odd numbers)
                    factorsymbol=r"$k$"  # Kernel size symbol
                ),
                AttackerWithFactors(
                    attacker=MeanFilter(),  # Apply mean/box filter
                    attackername="MeanFilter",  # Linear averaging filter
                    factors=[3, 5, 7, 9, 11, 13, 15, 17, 21, 23],  # Kernel size (odd numbers)
                    factorsymbol=r"$k$"  # Kernel size symbol
                ),
                AttackerWithFactors(
                    attacker=UnsharpMasking(),  # Apply unsharp masking (edge enhancement)
                    attackername="UnsharpMasking",  # Enhance image sharpness/contrast
                    factors=[0.1, 0.3, 0.6, 1.05, 1.73, 2.74, 4.26, 6.53, 9.95, 15.08],  # Enhancement strength
                    factorsymbol=r"$\lambda$"  # Enhancement parameter symbol
                ),

                # ===================================================================
                # Geometric Transformations - Spatial transformations of images
                # Simulate camera movements, cropping, and scaling artifacts
                # ===================================================================
                AttackerWithFactors(
                    attacker=Resize(),  # Resize image to different scales
                    attackername="Resize",  # Scale image up or down
                    factors=[0.01, 0.03, 0.05, 0.07, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9],  # Scaling factor
                    factorsymbol=r"$s$"  # Scale parameter symbol
                ),
                AttackerWithFactors(
                    attacker=Rotate(),  # Rotate image by specific angles
                    attackername="Rotation",  # Rotate image in degrees
                    factors=[30, 60, 90, 120, 150, 180, 210, 240, 270],  # Rotation angles in degrees
                    factorsymbol=r"$\theta$"  # Angle parameter symbol
                ),
                AttackerWithFactors(
                    attacker=FlipAttack(),
                    factors=['H', 'V'],
                    factorsymbol='$d$',
                    attackername='FlipAttack'
                ),
                AttackerWithFactors(
                    attacker=TranslationAttack(),
                    factors=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
                    factorsymbol='$r$',
                    attackername='TranslationAttack'
                ),
                AttackerWithFactors(
                    attacker=Crop(),  # Crop image from edges
                    attackername="Crop",  # Remove image borders
                    factors=[0.01, 0.03, 0.05, 0.07, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9],  # Crop ratio
                    factorsymbol=r"$r$"  # Crop ratio symbol
                ),
                AttackerWithFactors(
                    attacker=Cropout(),  # Remove random regions from image
                    attackername="Cropout",  # Random region removal
                    factors=[0.01, 0.03, 0.05, 0.07, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9],  # Removal ratio
                    factorsymbol=r"$r$"  # Removal ratio symbol
                ),
                AttackerWithFactors(
                    attacker=RegionZoom(),  # Zoom into specific regions
                    attackername="RegionZoom",  # Magnify image regions
                    factors=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],  # Zoom ratio
                    factorsymbol=r"$r$"  # Zoom ratio symbol
                ),
                AttackerWithFactors(
                    attacker=PixelDropout(),  # Randomly drop pixels
                    attackername="PixelDropout",  # Random pixel removal
                    factors=[0.01, 0.03, 0.05, 0.07, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9],  # Dropout probability
                    factorsymbol=r"$p$"  # Probability parameter symbol
                ),

                # ===================================================================
                # Color Transformations - Modify color properties of images
                # Simulate display variations, lighting changes, and color effects
                # ===================================================================
                AttackerWithFactors(
                    attacker=ContrastReduction(),  # Reduce image contrast
                    attackername="ContrastReduction",  # Decrease dynamic range
                    factors=[0.01, 0.03, 0.05, 0.07, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9],  # Reduction factor
                    factorsymbol=r"$\alpha$"  # Contrast reduction parameter
                ),
                AttackerWithFactors(
                    attacker=ContrastEnhancement(),  # Enhance image contrast
                    attackername="ContrastEnhancement",  # Increase dynamic range
                    factors=[1.1, 1.3, 1.5, 2.0, 3.0, 5.0, 7.0, 9.0, 10.0, 11.0],  # Enhancement factor (gamma)
                    factorsymbol=r"$\gamma$"  # Gamma correction parameter
                ),
                AttackerWithFactors(
                    attacker=ColorQuantization(),  # Reduce color palette
                    attackername="ColorQuantization",  # Limit number of colors
                    factors=[4, 8, 12, 16, 20, 28, 36, 42, 50, 76],  # Number of colors
                    factorsymbol=r"$q$"  # Quantization levels symbol
                ),
                AttackerWithFactors(
                    attacker=ChromaticAberration(),  # Simulate lens chromatic aberration
                    attackername="ChromaticAberration",  # Color fringing effect
                    factors=[1, 3, 5, 7, 9, 13, 17, 21, 25, 30],  # Aberration strength
                    factorsymbol=r"$s$"  # Strength parameter symbol
                ),
                AttackerWithFactors(
                    attacker=GammaCorrection(),  # Apply gamma correction
                    attackername="GammaCorrection",  # Adjust image brightness
                    factors=[1.5, 3, 6, 7, 9, 13, 21, 37, 69, 133],  # Gamma values
                    factorsymbol=r"$\gamma$"  # Gamma parameter symbol
                ),
                AttackerWithFactors(
                    attacker=HueShiftAttack(),  # Shift color hue
                    attackername="HueShift",  # Change overall color tone
                    factors=[1, 3, 7, 15, 28, 48, 77, 115, 145, 170],  # Hue shift degrees
                    factorsymbol=r"$\Delta h$"  # Hue shift parameter symbol
                ),
                AttackerWithFactors(
                    attacker=DarkenAttack(),  # Make image darker
                    attackername="Darken",  # Reduce image brightness
                    factors=[0.006, 0.018, 0.047, 0.119, 0.269, 0.5, 0.731, 0.881, 0.953, 0.982],  # Darkening factor
                    factorsymbol=r"$\beta$"  # Brightness parameter symbol
                ),
                AttackerWithFactors(
                    attacker=BrightenAttack(),  # Make image brighter
                    attackername="Brighten",  # Increase image brightness
                    factors=[1.1, 1.3, 1.6, 2.0, 3.0, 7.0, 15.0, 31.0, 63.0, 95.0],  # Brightening factor
                    factorsymbol=r"$\beta$"  # Brightness parameter symbol
                ),
                AttackerWithFactors(
                    attacker=DesaturateAttack(),  # Reduce color saturation
                    attackername="Desaturate",  # Make image more grayscale
                    factors=[0.006, 0.018, 0.047, 0.119, 0.269, 0.5, 0.731, 0.881, 0.953, 0.982],
                    # Saturation reduction
                    factorsymbol=r"$\sigma_{\text{d}}$"  # Desaturation parameter symbol
                ),
                AttackerWithFactors(
                    attacker=OversaturateAttack(),  # Increase color saturation
                    attackername="Oversaturate",  # Make colors more vivid
                    factors=[1.1, 1.3, 1.6, 2.0, 3.0, 7.0, 11.0, 15.0, 19.0, 23.0],  # Saturation enhancement
                    factorsymbol=r"$\sigma_{\text{o}}$"  # Oversaturation parameter symbol
                ),
            ]
            # Extend this list instance with the comprehensive default attackers
            self.extend(default_attackers_list)

    def __repr__(self):
        """
        Return a string representation of the AttackersWithFactorsModel.

        Returns:
            str: A string showing the class name and the number of attackers.
        """
        return f"AttackersWithFactorsModel({len(self)} attackers)"


# Execute the test
if __name__ == "__main__":
    print(len(AttackersWithFactorsModel()))
