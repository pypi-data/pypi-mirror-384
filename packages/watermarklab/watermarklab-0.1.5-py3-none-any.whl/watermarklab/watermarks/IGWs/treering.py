# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT
import torch
import random
import numpy as np
from PIL import Image
from typing import List, Tuple
from watermarklab.utils.logger import logger
from watermarklab.utils.basemodel import BaseWatermarkModel, Result
from diffusers import StableDiffusionPipeline, DDIMScheduler, DDIMInverseScheduler

__all__ = ["TreeRing"]

from watermarklab.utils.parameters import LOAD_FROM_LOCAL

RED = "\033[91m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"


class TreeRing(BaseWatermarkModel):
    """
    A wrapper class for Tree-Ring Watermarking, a robust and invisible watermarking technique
    for diffusion models. The watermark is embedded in the Fourier space of the initial noise
    vector used in the DDIM sampling process. Detection is performed via DDIM inversion to
    recover the initial noise and verify the presence of the predefined watermark pattern.

    Reference:
        Wen, Y., Kirchenbauer, J., Geiping, J., & Goldstein, T. (2023).
        Tree-Ring Watermarks: Fingerprints for Diffusion Images that are Invisible and Robust.
        arXiv:2305.20030.
    """

    def __init__(self, img_size: int = 512, bits_len: int = 1, modelname: str = "TreeRing",
                 model_id: str = "stabilityai/stable-diffusion-2-1-base", w_pattern: str = "ring",
                 w_radius: int = 10, w_channel: int = 3, local_files_only=False):
        """
        Initialize the TreeRing watermarking system.

        Args:
            img_size (int): Size of the generated image (must be divisible by 8). Default is 512.
            bits_len (int): Length of the watermark bits (not used in this method). Ignored.
            modelname (str): Name of the watermark model. Default is "TreeRing".
            model_id (str): Hugging Face model ID for the diffusion model. Default is "stabilityai/stable-diffusion-2-1-base".
            w_pattern (str): Watermark pattern type. Supported: 'ring', 'rand', 'zeros'. Default is "ring".
            w_radius (int): Radius of the circular watermark mask in the frequency domain. Default is 10.
            w_channel (int): Channel index to embed the watermark. Use -1 for all channels, or 0-3 for a specific channel. Default is 3.
            device (str): Device to run the model on. Default is "cpu". Recommended: "cuda".
        """
        super().__init__(bits_len, img_size, f"{modelname}-{w_pattern.capitalize()}")
        self.w_seed = 999999
        self.img_size = img_size
        self.model_id = model_id
        self.w_pattern = w_pattern
        self.w_radius = w_radius
        self.w_channel = w_channel
        self.local_files_only = local_files_only
        assert w_channel in [-1, 0, 1, 2, 3], "w_channel must be -1 (all) or 0-3 (specific channel)"
        assert w_pattern in ["ring", "zeros", "rand"], "The embedding mode of TreeRing must be one of rand, zeros and ring"
        # Load Stable Diffusion pipeline with DDIM scheduler
        scheduler = DDIMScheduler.from_pretrained(model_id, subfolder='scheduler', local_files_only=self.local_files_only)
        self.pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            scheduler=scheduler,
            safety_checker=None,
            torch_dtype=torch.float16,
            local_files_only=self.local_files_only
        )
        # ✅ Enable model CPU offloading. DO NOT call .to(device) after this.
        self.pipe.enable_model_cpu_offload()
        # ✅ Disable safety checker
        self.pipe.safety_checker = None


        # Generate the watermark pattern and mask
        self.gt_patch = self._get_watermarking_pattern()
        self.watermark_mask = self._get_watermark_mask((1, 4, self.img_size // 8, self.img_size // 8))

        logger.info(f"TreeRing initialized with model {self.model_id}.")

    def _set_random_seed(self):
        """
        Set all random seeds to ensure reproducibility of the watermark pattern.
        This is crucial for generating the same `gt_patch` across different runs.
        """
        torch.manual_seed(self.w_seed + 0)
        torch.cuda.manual_seed(self.w_seed + 1)
        torch.cuda.manual_seed_all(self.w_seed + 2)
        np.random.seed(self.w_seed + 3)
        torch.cuda.manual_seed_all(self.w_seed + 4)
        random.seed(self.w_seed + 5)

    def _get_watermarking_pattern(self) -> torch.Tensor:
        """
        Generate the ground-truth watermark pattern (key) in the Fourier space of a random noise tensor.

        The pattern is generated based on `self.w_pattern`:
            - 'rand': Copy the first sample's FFT across the batch.
            - 'zeros': Set the watermark region to zero.
            - 'ring' (default): Fill concentric rings with values from the center of the original FFT.

        Note:
            The 'ring' implementation here is a simplified version. For robustness, consider using
            ring-wise averaging instead of copying from (0, i).

        Returns:
            torch.Tensor: The watermark pattern in complex Fourier space, shape [1, C, H, W].
        """
        self._set_random_seed()
        # Create a random initial latent (noise vector)
        gt_init = torch.randn(
            (1, 4, self.img_size // 8, self.img_size // 8),
            device=self.pipe.device
        )
        # Transform to Fourier space and shift DC to center
        gt_init_fft = torch.fft.fftshift(torch.fft.fft2(gt_init), dim=(-1, -2))
        gt_patch = torch.zeros_like(gt_init_fft)

        if 'rand' in self.w_pattern:
            # Use the FFT of the first sample as the pattern for all
            gt_patch[:] = gt_init_fft[0]
        elif 'zeros' in self.w_pattern:
            # Set the entire pattern to zero
            gt_patch[:] = 0.0
        else:  # 'ring' pattern
            # Fill concentric rings with values from the original FFT (simplified)
            for i in range(self.w_radius, 0, -1):
                tmp_mask = self._circle_mask(gt_init.shape[-1], r=i)
                tmp_mask = torch.tensor(tmp_mask, dtype=torch.bool)
                for j in range(gt_init.shape[1]):
                    # WARNING: This indexing is non-standard. Consider averaging over the ring.
                    gt_patch[:, j, tmp_mask] = gt_init_fft[0, j, 0, i].item()
        return gt_patch

    def _get_watermark_mask(self, shape: Tuple[int, ...]) -> torch.Tensor:
        """
        Generate a circular boolean mask in the latent space to define the watermark region.

        Args:
            shape (Tuple[int, ...]): Shape of the latent tensor, e.g., (1, 4, 64, 64).

        Returns:
            torch.Tensor: A boolean mask of the same spatial shape, with `True` inside the circle.
        """
        watermarking_mask = torch.zeros(shape, dtype=torch.bool)
        np_mask = self._circle_mask(shape[-1], r=self.w_radius)
        torch_mask = torch.tensor(np_mask, dtype=torch.bool)

        if self.w_channel == -1:
            # Apply mask to all channels
            watermarking_mask[:, :] = torch_mask
        else:
            # Apply mask to a specific channel
            watermarking_mask[:, self.w_channel] = torch_mask
        return watermarking_mask

    def _circle_mask(self, size: int = 64, r: int = 10, x_offset: int = 0, y_offset: int = 0) -> bool:
        """
        Generate a circular boolean mask.

        Args:
            size (int): Size of the square mask (H = W = size).
            r (int): Radius of the circle.
            x_offset (int): X-axis offset for the circle center.
            y_offset (int): Y-axis offset for the circle center.

        Returns:
            np.ndarray: A 2D boolean array where `True` indicates pixels inside the circle.
        """
        x0 = y0 = size // 2
        x0 += x_offset
        y0 += y_offset
        y, x = np.ogrid[:size, :size]
        # Note: y[::-1] flips the y-axis to match some coordinate systems. May not be necessary.
        y = y[::-1]
        return ((x - x0) ** 2 + (y - y0) ** 2) <= r ** 2

    def _inject_watermark(self, init_clean_latents: torch.Tensor) -> torch.Tensor:
        """
        Inject watermark into each latent in the batch.
        Handles batched input with broadcastable or per-sample mask.
        """
        B = init_clean_latents.shape[0]
        original_dtype = init_clean_latents.dtype
        device = init_clean_latents.device
        latent_float32 = init_clean_latents.to(torch.float32)
        latent_fft = torch.fft.fftshift(torch.fft.fft2(latent_float32), dim=(-1, -2))  # [B, C, H, W], complex64
        mask = self.watermark_mask.expand(B, -1, -1, -1)
        pattern = self.gt_patch.expand(B, -1, -1, -1)
        mask = mask.to(device)
        pattern = pattern.to(device).to(latent_fft.dtype)
        latent_fft[mask] = pattern[mask]
        latent_float32_w = torch.fft.ifft2(torch.fft.ifftshift(latent_fft, dim=(-1, -2))).real
        return latent_float32_w.to(original_dtype)

    def _extract_watermark(self, latents: torch.Tensor):
        """
        Extract watermark detection scores from the input latents by computing the mean L1 distance
        between the Fourier spectrum of latents and the predefined ground-truth pattern (gt_patch)
        within the watermark region.

        Args:
            latents (torch.Tensor): Input latent tensors of shape [B, C, H, W].

        Returns:
            List[List[float]]: A list of lists containing the detection scores for each sample,
                              e.g., [[score1], [score2], ...].
        """
        device = latents.device
        gt_patch = self.gt_patch.to(device).expand(latents.shape[0], -1, -1, -1)  # [B, C, H, W]
        watermark_mask = self.watermark_mask.to(device).expand(latents.shape[0], -1, -1, -1)
        latent_float32 = latents.to(torch.float32)
        latent_fft = torch.fft.fftshift(torch.fft.fft2(latent_float32), dim=(-1, -2))  # [B, C, H, W], complex64
        diff = torch.abs(latent_fft - gt_patch)  # [B, C, H, W]
        num_masked = watermark_mask.sum(dim=[1, 2, 3])  # [B]
        masked_sum = (diff * watermark_mask).sum(dim=[1, 2, 3])  # [B]
        detection_scores = (masked_sum / num_masked.clamp(min=1)).cpu().numpy().tolist()
        emb_bits = [[-score] for score in detection_scores]
        return emb_bits

    @torch.inference_mode()
    def Diffusion_inversion(self,
                            image_tensor: List[torch.Tensor],
                            num_steps: int = 50,
                            guidance_scale: float = 7.5) -> torch.Tensor:
        """
        Perform DDIM inversion to recover the initial noise vector from an image.

        Args:
            image_tensor (List[torch.Tensor]): List of image tensors, each of shape [1, 3, H, W] in [0, 1] range.
            num_steps (int): Number of inversion steps.
            guidance_scale (float): Guidance scale used during inversion.

        Returns:
            torch.Tensor: The inverted initial noise latent of shape [B, 4, H//8, W//8].
        """
        self.pipe.scheduler = DDIMInverseScheduler.from_pretrained(self.model_id, subfolder='scheduler')

        batched_tensor = torch.cat(image_tensor, dim=0)
        device = self.pipe._execution_device
        dtype = self.pipe.dtype
        batched_tensor = batched_tensor.to(device).to(dtype)

        latents = self.pipe.vae.encode(batched_tensor).latent_dist.sample()
        latents = latents * self.pipe.vae.config.scaling_factor

        inv_latents, _ = self.pipe(
            ["" for _ in range(len(batched_tensor))],
            guidance_scale=guidance_scale,
            width=self.img_size,
            height=self.img_size,
            output_type='latent',
            return_dict=False,
            num_inference_steps=num_steps,
            latents=latents
        )

        return inv_latents


    def embed(self, prompts: List[str], secrets: List[List[int]] = None) -> Result:
        """
        Generate watermarked images for a list of prompts.

        Args:
            prompts (List[str]): A list of text prompts for image generation.
            secrets (List[List[int]]): Not used. Tree-Ring does not use bit-based secrets.

        Returns:
            Result: An object containing:
                - stego_img: List of watermarked images.
                - clean_img: List of corresponding clean (unwatermarked) images.
        """
        batch_size = len(prompts)

        # Generate random latents on CPU (offloading will move to GPU as needed)
        latents = torch.randn(
            (batch_size, 4, 64, 64),
            dtype=torch.float16,
            device="cpu"
        )
        # Generate clean images
        clean_outputs = self.pipe(
            prompt=prompts,
            latents=latents,
            output_type="numpy"
        )
        clean_list = [np.array(img * 255, dtype=np.uint8) for img in clean_outputs.images]

        init_latents_w = self._inject_watermark(latents)
        emb_bits = self._extract_watermark(init_latents_w)

        # Generate watermarked images
        stego_outputs = self.pipe(
            prompt=prompts,
            latents=init_latents_w,
            output_type="numpy"
        )
        stego_list = [np.array(img * 255, dtype=np.uint8) for img in stego_outputs.images]
        return Result(stego_img=stego_list, clean_img=clean_list, emb_bits=emb_bits)

    def extract(self, stego_list: List[np.ndarray]) -> Result:
        """
        Extract the watermark from a list of watermarked images.

        Detection is performed by:
        1. Inverting the image to recover the initial latent.
        2. Comparing the Fourier transform of the recovered latent with the stored `gt_patch`.

        Args:
            stego_list (List[np.ndarray]): List of watermarked RGB images with shape [H, W, 3].

        Returns:
            Result: An object containing `detected_values`, a list of L1 distances.
                Lower values indicate a stronger presence of the watermark.
        """
        stego_tensor_list = []
        for stego_img in stego_list:
            # Convert numpy array to PIL and preprocess
            pil_image = Image.fromarray(np.uint8(stego_img))
            image_tensor = self.pipe.image_processor.preprocess(pil_image)
            stego_tensor_list.append(image_tensor)
        # Perform DDIM inversion to get initial latent
        reversed_latents = self.Diffusion_inversion(stego_tensor_list)
        ext_metric_list = self._extract_watermark(reversed_latents)
        return Result(ext_bits=ext_metric_list)

    def recover(self, stego_list: List[np.ndarray]) -> Result:
        """
        Recover the original image from a watermarked image.

        This method is not applicable for Tree-Ring watermarking, as it is a generative method
        without a reversible distortion process.

        Args:
            stego_list (List[np.ndarray]): List of watermarked images.

        Returns:
            Result: NotImplemented.
        """
        # Tree-Ring is not a reversible watermarking method
        pass
