# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT
import torch
import random
import numpy as np
from PIL import Image
from numpy import ndarray
from functools import reduce
from Crypto.Cipher import ChaCha20
from scipy.stats import norm, truncnorm
from typing import List, Optional, Tuple
from watermarklab.utils.logger import logger
from watermarklab.utils.basemodel import BaseWatermarkModel, Result
from diffusers import DDIMInverseScheduler, DDIMScheduler, StableDiffusionPipeline

__all__ = ["GaussianShading"]

from watermarklab.utils.parameters import LOAD_FROM_LOCAL

RED = "\033[91m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"


class GaussianShading(BaseWatermarkModel):
    """
    Implements the Gaussian Shading watermarking method from the CVPR 2024 paper.
    This method embeds watermarks in the initial noise vector of a stable diffusion model
    without performance loss or additional training. Supports two modes:
    - Detection: for copyright verification
    - Traceability: for user identification
    Reference:
        Zijin Yang, Kai Zeng, Kejiang Chen, Han Fang, Weiming Zhang, Nenghai Yu. (2023).
        Gaussian Shading: Provable Performance-Lossless Image Watermarking for Diffusion Models.
        arXiv:2404.04956.
    """

    def __init__(self,
                 image_size: int = 512,
                 bit_length: int = 256,
                 f_h: int = 8,
                 f_w: int = 8,
                 f_c: int = 1,
                 l: int = 1,
                 model_name: str = "GaussianShading",
                 model_id: str = "stabilityai/stable-diffusion-2-1-base",
                 embed_mode: str = "traceability",
                 threshold: float = 30.,
                 local_files_only=LOAD_FROM_LOCAL):
        """
        Initialize the Gaussian Shading watermarking model with CPU offloading.

        Args:
            image_size (int): Size of the input/output images (default: 512).
            bit_length (int): Length of the watermark bit sequence (default: 256).
            f_h (int): Height ratio for embedding (default: 8).
            f_w (int): Width ratio for embedding (default: 8).
            f_c (int): channels ratio for embedding (default: 1).
            l (int): bit per dimension (default: 1).
            model_name (str): Name of the model (default: "GaussianShading").
            embed_mode (str): Embedding mode, either 'detection' or 'traceability' (default: 'detection').
            model_id (str): Path to the pre-trained diffusion model (default: stabilityai/stable-diffusion-2-1-base).
        """
        super().__init__(bit_length, image_size, model_name)
        assert embed_mode in ["detection", "traceability"], "Embed mode must be 'detection' or 'traceability'!"
        self.l = l
        self.f_c = f_c
        self.f_w = f_w
        self.f_h = f_h
        self.threshold = threshold
        self.model_id = model_id
        self.latent_channels = 4
        self.latent_height = 64
        self.latent_width = 64
        self.embed_mode = embed_mode
        self.local_files_only = local_files_only
        self.watermark_length = self.l * (
                self.latent_channels * self.latent_height * self.latent_width
        ) // (self.f_c * self.f_w * self.f_h)
        self.watermark_latent_shape = (
            1,
            self.latent_channels // self.f_c,
            self.latent_height // self.f_h,
            self.latent_width // self.f_w
        )
        # Set watermark bits for detection
        self.detection_watermark = [1 for _ in range(self.watermark_length)]

        # Load Stable Diffusion pipeline with DDIM scheduler
        scheduler = DDIMScheduler.from_pretrained(model_id, subfolder='scheduler', local_files_only=local_files_only)
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

        random.seed(99)
        self.key = bytes(random.getrandbits(8) for _ in range(32))
        self.nonce = bytes(random.getrandbits(8) for _ in range(12))
        logger.info(f"GaussianShading initialized with model {self.model_id}.")

    def _decrypt_stream_key(self, reversed_message: np.ndarray) -> torch.Tensor:
        """
        Decrypt the watermark bitstream and convert it to a tensor.

        Args:
            reversed_message (np.ndarray): Flattened binary message to decrypt.

        Returns:
            torch.Tensor: Decrypted watermark tensor shaped for latent space.
        """
        decrypt_cipher = ChaCha20.new(key=self.key, nonce=self.nonce)
        decrypted_bytes = decrypt_cipher.decrypt(np.packbits(reversed_message).tobytes())
        decrypted_bits = np.unpackbits(np.frombuffer(decrypted_bytes, dtype=np.uint8))
        decrypted_tensor = torch.from_numpy(decrypted_bits).reshape(
            1, self.latent_channels, self.latent_height, self.latent_width
        ).to(torch.uint8)
        return decrypted_tensor

    def _encrypt_stream_key(self, watermark_data: np.ndarray) -> np.ndarray:
        """
        Encrypt the watermark bitstream.

        Args:
            watermark_data (np.ndarray): Watermark data to encrypt.

        Returns:
            np.ndarray: Encrypted watermark bits.
        """
        encrypt_cipher = ChaCha20.new(key=self.key, nonce=self.nonce)
        encrypted_bytes = encrypt_cipher.encrypt(np.packbits(watermark_data.astype(bool)).tobytes())
        encrypted_bits = np.unpackbits(np.frombuffer(encrypted_bytes, dtype=np.uint8))
        return encrypted_bits

    def _sample_truncated_normal(self, message: np.ndarray) -> torch.Tensor:
        """
        Sample from a truncated normal distribution based on the watermark message.

        Args:
            message (np.ndarray): Binary watermark message.

        Returns:
            torch.Tensor: Sampled values reshaped for latent space.
        """
        samples = np.zeros(self.latent_channels * self.latent_height * self.latent_width)
        denominator = 2.0
        ppf = [norm.ppf(j / denominator) for j in range(int(denominator) + 1)]
        for i in range(self.latent_channels * self.latent_height * self.latent_width):
            decoded_message = reduce(lambda a, b: 2 * a + b, message[i: i + 1])
            decoded_message = int(decoded_message)
            samples[i] = truncnorm.rvs(ppf[decoded_message], ppf[decoded_message + 1])
        samples_tensor = torch.from_numpy(samples).reshape(
            1, self.latent_channels, self.latent_height, self.latent_width
        ).to(dtype=torch.float16)
        return samples_tensor

    def _initialize_latent_watermark(self, watermark_bits: list) -> torch.Tensor:
        """
        Initialize the latent watermark variable from the watermark bits.

        Args:
            watermark_bits (list): Binary watermark sequence.

        Returns:
            torch.Tensor: Initialized latent watermark tensor.
        """
        watermark_tensor = torch.as_tensor(watermark_bits, dtype=torch.float32).reshape(
            self.watermark_latent_shape
        )
        repeated_tensor = watermark_tensor.repeat(
            1, self.f_c, self.f_h, self.f_w
        )
        encrypted_bits = self._encrypt_stream_key(repeated_tensor.flatten().cpu().numpy())
        latent_watermark = self._sample_truncated_normal(encrypted_bits)
        return latent_watermark

    def _decode_watermark_bits(self, watermark_tensor: torch.Tensor, threshold: float) -> list:
        """
        Decode the watermark bits from the latent watermark tensor.

        Args:
            watermark_tensor (torch.Tensor): Watermark tensor to decode.
            threshold (float): Threshold for binarization.

        Returns:
            List[int]: Decoded binary watermark as a list of integers (0 or 1).
        """
        channel_stride = self.latent_channels // self.f_c
        spatial_stride = self.latent_height // self.f_h
        channel_splits = [channel_stride] * self.f_c
        spatial_splits = [spatial_stride] * self.f_h
        split_dim1 = torch.cat(torch.split(watermark_tensor, tuple(channel_splits), dim=1), dim=0)
        split_dim2 = torch.cat(torch.split(split_dim1, tuple(spatial_splits), dim=2), dim=0)
        split_dim3 = torch.cat(torch.split(split_dim2, tuple(spatial_splits), dim=3), dim=0)
        vote = torch.sum(split_dim3, dim=0).clone()
        vote[vote <= threshold] = 0
        vote[vote > threshold] = 1
        return vote.flatten().cpu().numpy().tolist()

    @torch.inference_mode()
    def Diffusion_forward(self,
                          prompts: List[str],
                          latents: Optional[List[torch.Tensor]] = None,
                          num_steps: int = 50,
                          guidance_scale: float = 7.5) -> Tuple[List[np.ndarray], torch.Tensor]:
        """
        Generate a batch of images using the DDIM forward sampling process.

        Args:
            prompts (List[str]): A list of text prompts for image generation.
            latents (Optional[List[torch.Tensor]]): A list of latent tensors, each of shape [1, 4, H//8, W//8].
                If None, random latents are generated for each prompt.
            num_steps (int): Number of denoising steps. Default is 50.
            guidance_scale (float): Scale for classifier-free guidance. Default is 7.5.

        Returns:
            Tuple[List[np.ndarray], torch.Tensor]:
                - List of generated images as float32 numpy arrays [H, W, 3] in [0, 1] range.
                - The stacked initial latent tensor used for generation, shape [B, 4, H//8, W//8].
        """
        self.pipe.scheduler = DDIMScheduler.from_pretrained(self.model_id, subfolder='scheduler', local_files_only=self.local_files_only)
        batch_size = len(prompts)

        device = self.pipe._execution_device
        dtype = self.pipe.dtype

        if latents is None:
            initial_latents = torch.randn(
                (batch_size, 4, self.img_size // 8, self.img_size // 8),
                device=device,
                dtype=dtype
            )
        else:
            assert isinstance(latents, list), f"Latents must be a list of tensors, got {type(latents)}"
            assert len(
                latents) == batch_size, f"Number of latents ({len(latents)}) must match number of prompts ({batch_size})"
            initial_latents = torch.cat(latents, dim=0).to(device).to(dtype)

        outputs = self.pipe(
            prompt=prompts,
            num_inference_steps=num_steps,
            guidance_scale=guidance_scale,
            width=self.img_size,
            height=self.img_size,
            latents=initial_latents,
            output_type="numpy"
        )

        generated_images = outputs.images.tolist()
        stego_list = [np.uint8(np.clip(stego, 0, 1.) * 255.) for stego in generated_images]
        return stego_list, initial_latents

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
        self.pipe.scheduler = DDIMInverseScheduler.from_pretrained(self.model_id, subfolder='scheduler', local_files_only=self.local_files_only)

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

    @torch.inference_mode()
    def embed(self, prompts: List[str], secrets: List[List[int]]) -> Result:
        """
        Embed watermarks into images using the Gaussian Shading method.

        Args:
            prompts (List[str]): Text prompts for image generation.
            secrets (List[List[int]]): Watermark bit sequences for traceability mode.

        Returns:
            Result: Object containing the watermarked images and embedded bits.
        """
        emb_bits_list = []
        initial_latent_list = []
        clean_initial_latent_list = []
        device = self.pipe._execution_device
        dtype = self.pipe.dtype

        for secret in secrets:
            if self.embed_mode == "detection":
                emb_bits_list.append(self.detection_watermark)
                latent = self._initialize_latent_watermark(self.detection_watermark)
            else:
                emb_bits_list.append(secret)
                latent = self._initialize_latent_watermark(secret)
            clean_initial_latent = torch.randn(
                (1, 4, self.img_size // 8, self.img_size // 8),
                device=device,
                dtype=dtype
            )
            latent = latent.to(device).to(dtype)
            initial_latent_list.append(latent)
            clean_initial_latent_list.append(clean_initial_latent)
        stego_list, _ = self.Diffusion_forward(prompts, latents=initial_latent_list)
        clean_list, _ = self.Diffusion_forward(prompts, latents=clean_initial_latent_list)
        return Result(clean_img=clean_list, stego_img=stego_list, emb_bits=emb_bits_list)

    @torch.inference_mode()
    def extract(self, protected_images: List[ndarray]) -> Result:
        """
        Extract watermarks from watermarked images.

        Args:
            protected_images (List[ndarray]): Watermarked images to analyze.
        Returns:
            Result: Object containing the extracted watermark bits.
        """
        extracted_bits_list = []
        stego_tensor_list = []

        for stego in protected_images:
            pil_image = Image.fromarray(np.uint8(stego))
            image_tensor = self.pipe.image_processor.preprocess(pil_image)
            image_tensor = image_tensor.to(self.pipe.dtype)  # Match model dtype, no .cpu()
            stego_tensor_list.append(image_tensor)

        inv_latent_list = self.Diffusion_inversion(stego_tensor_list)

        for inv_latents in inv_latent_list:
            binary_latent = (inv_latents > 0).int()
            decrypted_watermark = self._decrypt_stream_key(binary_latent.flatten().cpu().numpy())
            extracted_watermark = self._decode_watermark_bits(decrypted_watermark, self.threshold)
            extracted_bits_list.append(extracted_watermark)

        return Result(ext_bits=extracted_bits_list)

    @torch.inference_mode()
    def recover(self, watermarked_images: List[ndarray]) -> Result:
        """
        Recover the original image from the watermarked image.
        This method is not supported by Gaussian Shading.

        Args:
            watermarked_images (List[ndarray]): Watermarked images.

        Returns:
            Result: NotImplemented.
        """
        return Result()
