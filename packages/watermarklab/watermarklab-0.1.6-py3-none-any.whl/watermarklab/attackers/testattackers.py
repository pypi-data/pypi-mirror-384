# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT
import cv2
import torch
import random
import numpy as np
from numpy import ndarray
import torch.nn.functional as F
import torchvision.transforms as transforms
from diffusers import StableDiffusionPipeline
import torchvision.transforms.functional as TF
from typing import Optional, Union, Callable, List
from watermarklab.utils.basemodel import BaseTestAttackModel
from diffusers.pipelines.stable_diffusion import StableDiffusionPipelineOutput
from compressai.zoo import cheng2020_anchor, bmshj2018_hyperprior, bmshj2018_factorized, mbt2018_mean, mbt2018

__all__ = ["GaussianBlur", "Identity",
           "GaussianNoise", "Jpeg", "SaltPepperNoise",
           "Jpeg2000", "MedianFilter", "MeanFilter", "PixelDropout",
           "Cropout", "Crop", "RegionZoom", "Resize", "Rotate", "UnsharpMasking",
           "ContrastReduction", "ContrastEnhancement", "ColorQuantization",
           "ChromaticAberration", "GammaCorrection", "WebPCompression",
           "PoissonNoise", "VAE_BMshj2018FactorizedAttack", "FlipAttack",
           "VAE_BMshj2018HyperpriorAttack", "VAE_Cheng2020Attack", "TranslationAttack",
           "VAE_MBT2018Attack", "VAE_MBT2018MeanAttack", "HueShiftAttack", "DiffuseAttack",
           "DarkenAttack", "BrightenAttack", "DesaturateAttack", "OversaturateAttack", "MultiDiffuseAttack"]


class Identity(BaseTestAttackModel):
    """
    Identity noise model that performs no operation (no-op) on the input images.

    This model returns the input stego images unchanged and is primarily used as:
        - A baseline for robustness testing (e.g., "No Attack" scenario)
        - A control group to verify watermark extraction performance on clean images
        - A placeholder in noise model pipelines

    Since no distortion is applied, it represents the ideal condition where the watermark
    should be perfectly extractable (BER = 0, EA = 100%).

    The model supports batched input (list of images) for efficient processing.
    """

    def __init__(self, noisename: str = "Identity"):
        """
        Initializes the Identity noise model.

        Args:
            noisename (str): Display name for logging and reporting. Defaults to "Identity".
        """
        super().__init__(noisename=noisename, factor_inversely_related=False)

    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: float = None) -> List[ndarray]:
        """
        Alias for `test()`, applying no distortion to the input images.

        Provided for semantic clarity in adversarial testing contexts where "attack"
        implies a degradation process. In this case, the "attack" is null.

        Args:
            stego_imgs (List[ndarray]): Batch of stego images to be "attacked".
            cover_img (List[ndarray], optional): Original cover images (ignored).
            factor (float, optional): Intensity parameter (ignored).

        Returns:
            List[ndarray]: Unmodified stego images.

        Note:
            This method simply delegates to `test()` and adds no additional logic.
        """
        return stego_imgs


class VAE_BMshj2018FactorizedAttack(BaseTestAttackModel):
    """
    A Variational Autoencoder (VAE)-based attack using the bmshj2018_factorized model.
    Applies lossy compression to the input image to potentially disrupt embedded watermarks.
    Reference: Ballé, J., Laparra, V., & Simoncelli, E. P. (2018). End-to-end optimized image compression.
               International Conference on Learning Representations (ICLR).

    Args:
        device (str): Device to run the model on, defaults to "cuda".
        noisename (str): Name identifier for the model, defaults to "VAE_BMshj2018FactorizedAttack".

    Note:
        The 'factor' parameter controls compression quality (1-8):
        - 1: strongest compression (most aggressive watermark removal).
        - 8: weakest compression (most faithful to input).
        Input and output are uint8 [H, W, 3] [0,255].
    """
    _global_model_cache = {}

    def __init__(self, device: str = "cuda", noisename: str = "VAE_BMshj2018FactorizedAttack"):
        super().__init__(noisename, True)
        self.device = torch.device(device)
        self._cached_models = {}

    def _get_model(self, quality: int):
        """
        Retrieves or loads the VAE model for the specified compression quality, utilizing caching.

        Args:
            quality (int): Compression quality level (1-8).

        Returns:
            torch.nn.Module: The VAE model for the specified quality.
        """
        q = max(1, min(8, quality))
        cache_key = (q, self.device)
        if quality not in self._cached_models:
            if cache_key in VAE_BMshj2018FactorizedAttack._global_model_cache:
                self._cached_models[quality] = VAE_BMshj2018FactorizedAttack._global_model_cache[cache_key]
            else:
                model = bmshj2018_factorized(quality=q, pretrained=True).eval().to(self.device)
                VAE_BMshj2018FactorizedAttack._global_model_cache[cache_key] = model
                self._cached_models[quality] = model
        return self._cached_models[quality]

    @torch.inference_mode()
    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: int = 3) -> List[ndarray]:
        """
        Applies VAE-based compression attack to the input image.

        Args:
            stego_imgs (ndarray): Input image in RGB format, uint8 [H, W, 3] [0,255].
            cover_img (ndarray, optional): Not used.
            factor (int): Compression quality level (1-8).

        Returns:
            ndarray: Reconstructed image after compression, same shape and dtype as input.
        """
        if not stego_imgs:
            return []

        # Step 1: Detect if input is grayscale
        is_grayscale = len(stego_imgs[0].shape) == 2
        original_shapes = [img.shape[:2] for img in stego_imgs]
        target_h, target_w = original_shapes[0]

        # Step 2: Convert to 3-channel if grayscale
        if is_grayscale:
            # Convert (H, W) -> (H, W, 3) by repeating the single channel
            processed_imgs = [np.stack([img, img, img], axis=-1) for img in stego_imgs]
        else:
            processed_imgs = stego_imgs  # Already RGB

        # Step 3: Batch preprocessing
        batch_np = np.stack(processed_imgs, axis=0).astype(np.float32)  # [B, H, W, 3]
        batch_float = batch_np / 255.0  # Normalize to [0,1]

        # To tensor: [B, H, W, 3] -> [B, 3, H, W]
        batch_tensor = torch.from_numpy(batch_float).permute(0, 3, 1, 2).to(self.device)

        # Step 4: Resize to model input size
        batch_tensor = F.interpolate(
            batch_tensor,
            size=(512, 512),
            mode='bilinear',
            align_corners=False
        )  # [B, 3, 512, 512]

        # Step 5: Forward pass
        model = self._get_model(factor)
        output = model(batch_tensor)
        rec_batch = output["x_hat"].clamp(0, 1)  # [B, 3, 512, 512]

        # Step 6: Resize back to original size
        rec_batch = F.interpolate(
            rec_batch,
            size=(target_h, target_w),
            mode='bilinear',
            align_corners=False
        )  # [B, 3, H, W]

        # Step 7: Convert back to numpy
        rec_np = rec_batch.permute(0, 2, 3, 1).cpu().numpy()  # [B, H, W, 3]
        rec_np = (rec_np * 255).astype(np.uint8)  # [0,255]

        # Step 8: If input was grayscale, convert output back to grayscale
        # But keep shape consistent: if input was (H, W), output should be (H, W)
        if is_grayscale:
            # Convert back to grayscale using luminance formula
            # Y = 0.299*R + 0.587*G + 0.114*B
            rec_gray = np.dot(rec_np, [0.299, 0.587, 0.114]).astype(np.uint8)
            return [rec_gray[i] for i in range(rec_gray.shape[0])]
        else:
            return [rec_np[i] for i in range(rec_np.shape[0])]


class VAE_BMshj2018HyperpriorAttack(BaseTestAttackModel):
    """
    A Variational Autoencoder (VAE)-based attack using the bmshj2018_hyperprior model.
    Applies learned image compression with a scale hyperprior to disrupt embedded watermarks.

    This attack first resizes the input image to 512x512 using nearest-neighbor interpolation,
    then compresses and reconstructs it using the hyperprior VAE model, and finally resizes it
    back to the original resolution. The resize operations introduce additional geometric distortion,
    making this a stronger attack than compression alone.

    The 'factor' parameter controls the compression quality (1-8):
        - 1: strongest compression (lowest bitrate, highest distortion)
        - 8: weakest compression (highest bitrate, near lossless)

    Reference:
        Ballé, J., Minnen, D., Singh, S., Hwang, S. J., & Johnston, N. (2018).
        Variational image compression with a scale hyperprior. International Conference on Learning Representations (ICLR).
        https://arxiv.org/abs/1802.01436

    Note:
        - Input: List of uint8 RGB images [H, W, 3], range [0, 255]
        - Output: List of reconstructed images, same shape and dtype
        - The model is cached per quality level and device for efficiency
    """
    _global_model_cache = {}

    def __init__(self, device: str = "cuda", noisename: str = "VAE_BMshj2018HyperpriorAttack"):
        """
        Initializes the attack model with the specified device and name.

        Args:
            device (str): Device to run the model on ('cuda' or 'cpu').
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename, factor_inversely_related=True)  # Higher factor = less distortion
        self.device = torch.device(device)
        self._cached_models = {}

    def _get_model(self, quality: int):
        """
        Retrieves or loads the bmshj2018_hyperprior model for the given quality level.

        The model is cached globally using (quality, device) as key to prevent redundant loading
        and GPU memory duplication.

        Args:
            quality (int): Compression quality level (1-8).

        Returns:
            torch.nn.Module: The pre-trained VAE model with hyperprior in evaluation mode.
        """
        q = max(1, min(8, quality))
        cache_key = (q, self.device)
        if quality not in self._cached_models:
            if cache_key in VAE_BMshj2018HyperpriorAttack._global_model_cache:
                self._cached_models[quality] = VAE_BMshj2018HyperpriorAttack._global_model_cache[cache_key]
            else:
                model = bmshj2018_hyperprior(quality=q, pretrained=True).eval().to(self.device)
                VAE_BMshj2018HyperpriorAttack._global_model_cache[cache_key] = model
                self._cached_models[quality] = model
        return self._cached_models[quality]

    @torch.inference_mode()
    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: int = 3) -> List[
        ndarray]:
        """
        Applies the VAE-based compression attack with hyperprior and resize pre/post-processing.

        The attack pipeline is:
            1. Resize each input image to 512x512 using nearest-neighbor interpolation.
            2. Batch the preprocessed tensors and move to GPU.
            3. Forward pass through the hyperprior VAE model.
            4. Resize each reconstructed image back to its original size.
            5. Return the batch of distorted images.

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each of shape [H, W, 3], dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (not used in this attack).
            factor (int): Compression quality level (1-8). Higher values preserve more detail.

        Returns:
            List[ndarray]: Batch of reconstructed images, each with the same shape and dtype as the input.
        """
        if not stego_imgs:
            return []

        # Step 1: Detect if input is grayscale
        is_grayscale = len(stego_imgs[0].shape) == 2
        original_shapes = [img.shape[:2] for img in stego_imgs]
        target_h, target_w = original_shapes[0]

        # Step 2: Convert to 3-channel if grayscale
        if is_grayscale:
            # Convert (H, W) -> (H, W, 3) by repeating the single channel
            processed_imgs = [np.stack([img, img, img], axis=-1) for img in stego_imgs]
        else:
            processed_imgs = stego_imgs  # Already RGB

        # Step 3: Batch preprocessing
        batch_np = np.stack(processed_imgs, axis=0).astype(np.float32)  # [B, H, W, 3]
        batch_float = batch_np / 255.0  # Normalize to [0,1]

        # To tensor: [B, H, W, 3] -> [B, 3, H, W]
        batch_tensor = torch.from_numpy(batch_float).permute(0, 3, 1, 2).to(self.device)

        # Step 4: Resize to model input size
        batch_tensor = F.interpolate(
            batch_tensor,
            size=(512, 512),
            mode='bilinear',
            align_corners=False
        )  # [B, 3, 512, 512]

        # Step 5: Forward pass
        model = self._get_model(factor)
        output = model(batch_tensor)
        rec_batch = output["x_hat"].clamp(0, 1)  # [B, 3, 512, 512]

        # Step 6: Resize back to original size
        rec_batch = F.interpolate(
            rec_batch,
            size=(target_h, target_w),
            mode='bilinear',
            align_corners=False
        )  # [B, 3, H, W]

        # Step 7: Convert back to numpy
        rec_np = rec_batch.permute(0, 2, 3, 1).cpu().numpy()  # [B, H, W, 3]
        rec_np = (rec_np * 255).astype(np.uint8)  # [0,255]

        # Step 8: If input was grayscale, convert output back to grayscale
        # But keep shape consistent: if input was (H, W), output should be (H, W)
        if is_grayscale:
            # Convert back to grayscale using luminance formula
            # Y = 0.299*R + 0.587*G + 0.114*B
            rec_gray = np.dot(rec_np, [0.299, 0.587, 0.114]).astype(np.uint8)
            return [rec_gray[i] for i in range(rec_gray.shape[0])]
        else:
            return [rec_np[i] for i in range(rec_np.shape[0])]


class VAE_MBT2018MeanAttack(BaseTestAttackModel):
    """
    A Variational Autoencoder (VAE)-based attack using the mbt2018_mean model.
    Applies learned image compression with a mean-scale hyperprior to disrupt embedded watermarks.

    This attack first resizes the input image to 512x512 using nearest-neighbor interpolation,
    then compresses and reconstructs it using the MBT2018 (Minnen et al.) model with mean-scale hyperprior,
    and finally resizes it back to the original resolution. The resize operations introduce additional
    geometric distortion, making this a stronger attack than compression alone.

    The 'factor' parameter controls the compression quality (1-8):
        - 1: strongest compression (lowest bitrate, highest distortion)
        - 8: weakest compression (highest bitrate, near lossless)

    Reference:
        Minnen, D., Ballé, J., & Toderici, G. (2018).
        Joint autoregressive and hierarchical priors for learned image compression.
        Advances in Neural Information Processing Systems (NeurIPS).
        https://arxiv.org/abs/1809.02736

    Note:
        - Input: List of uint8 RGB images [H, W, 3], range [0, 255]
        - Output: List of reconstructed images, same shape and dtype
        - The model is cached per quality level and device for efficiency
    """
    _global_model_cache = {}

    def __init__(self, device: str = "cuda", noisename: str = "VAE_MBT2018MeanAttack"):
        """
        Initializes the attack model with the specified device and name.

        Args:
            device (str): Device to run the model on ('cuda' or 'cpu').
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename, factor_inversely_related=True)  # Higher factor = less distortion
        self.device = torch.device(device)
        self._cached_models = {}

    def _get_model(self, quality: int):
        """
        Retrieves or loads the mbt2018_mean model for the given quality level.

        The model is cached globally using (quality, device) as key to prevent redundant loading
        and GPU memory duplication.

        Args:
            quality (int): Compression quality level (1-8).

        Returns:
            torch.nn.Module: The pre-trained VAE model with mean-scale hyperprior in evaluation mode.
        """
        q = max(1, min(8, quality))
        cache_key = (q, self.device)
        if quality not in self._cached_models:
            if cache_key in VAE_MBT2018MeanAttack._global_model_cache:
                self._cached_models[quality] = VAE_MBT2018MeanAttack._global_model_cache[cache_key]
            else:
                model = mbt2018_mean(quality=q, pretrained=True).eval().to(self.device)
                VAE_MBT2018MeanAttack._global_model_cache[cache_key] = model
                self._cached_models[quality] = model
        return self._cached_models[quality]

    @torch.inference_mode()
    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: int = 3) -> List[
        ndarray]:
        """
        Applies the VAE-based compression attack with mean-scale hyperprior and resize pre/post-processing.

        The attack pipeline is:
            1. Resize each input image to 512x512 using nearest-neighbor interpolation.
            2. Batch the preprocessed tensors and move to GPU.
            3. Forward pass through the MBT2018 VAE model.
            4. Resize each reconstructed image back to its original size.
            5. Return the batch of distorted images.

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each of shape [H, W, 3], dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (not used in this attack).
            factor (int): Compression quality level (1-8). Higher values preserve more detail.

        Returns:
            List[ndarray]: Batch of reconstructed images, each with the same shape and dtype as the input.
        """
        if not stego_imgs:
            return []

        # Step 1: Detect if input is grayscale
        is_grayscale = len(stego_imgs[0].shape) == 2
        original_shapes = [img.shape[:2] for img in stego_imgs]
        target_h, target_w = original_shapes[0]

        # Step 2: Convert to 3-channel if grayscale
        if is_grayscale:
            # Convert (H, W) -> (H, W, 3) by repeating the single channel
            processed_imgs = [np.stack([img, img, img], axis=-1) for img in stego_imgs]
        else:
            processed_imgs = stego_imgs  # Already RGB

        # Step 3: Batch preprocessing
        batch_np = np.stack(processed_imgs, axis=0).astype(np.float32)  # [B, H, W, 3]
        batch_float = batch_np / 255.0  # Normalize to [0,1]

        # To tensor: [B, H, W, 3] -> [B, 3, H, W]
        batch_tensor = torch.from_numpy(batch_float).permute(0, 3, 1, 2).to(self.device)

        # Step 4: Resize to model input size
        batch_tensor = F.interpolate(
            batch_tensor,
            size=(512, 512),
            mode='bilinear',
            align_corners=False
        )  # [B, 3, 512, 512]

        # Step 5: Forward pass
        model = self._get_model(factor)
        output = model(batch_tensor)
        rec_batch = output["x_hat"].clamp(0, 1)  # [B, 3, 512, 512]

        # Step 6: Resize back to original size
        rec_batch = F.interpolate(
            rec_batch,
            size=(target_h, target_w),
            mode='bilinear',
            align_corners=False
        )  # [B, 3, H, W]

        # Step 7: Convert back to numpy
        rec_np = rec_batch.permute(0, 2, 3, 1).cpu().numpy()  # [B, H, W, 3]
        rec_np = (rec_np * 255).astype(np.uint8)  # [0,255]

        # Step 8: If input was grayscale, convert output back to grayscale
        # But keep shape consistent: if input was (H, W), output should be (H, W)
        if is_grayscale:
            # Convert back to grayscale using luminance formula
            # Y = 0.299*R + 0.587*G + 0.114*B
            rec_gray = np.dot(rec_np, [0.299, 0.587, 0.114]).astype(np.uint8)
            return [rec_gray[i] for i in range(rec_gray.shape[0])]
        else:
            return [rec_np[i] for i in range(rec_np.shape[0])]


class VAE_MBT2018Attack(BaseTestAttackModel):
    """
    A Variational Autoencoder (VAE)-based attack using the mbt2018 model.
    Applies learned image compression to disrupt embedded watermarks.

    This attack first resizes the input image to 512x512 using nearest-neighbor interpolation,
    then compresses and reconstructs it using the MBT2018 (Minnen et al.) model,
    and finally resizes it back to the original resolution. The resize operations introduce additional
    geometric distortion, making this a stronger attack than compression alone.

    The 'factor' parameter controls the compression quality (1-8):
        - 1: strongest compression (lowest bitrate, highest distortion)
        - 8: weakest compression (highest bitrate, near lossless)

    Reference:
        Minnen, D., Ballé, J., & Toderici, G. (2018).
        Joint autoregressive and hierarchical priors for learned image compression.
        Advances in Neural Information Processing Systems (NeurIPS).
        https://arxiv.org/abs/1809.02736

    Note:
        - Input: List of uint8 RGB images [H, W, 3], range [0, 255]
        - Output: List of reconstructed images, same shape and dtype
        - The model is cached per quality level and device for efficiency
    """
    _global_model_cache = {}

    def __init__(self, device: str = "cuda", noisename: str = "VAE_MBT2018Attack"):
        """
        Initializes the attack model with the specified device and name.

        Args:
            device (str): Device to run the model on ('cuda' or 'cpu').
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename, factor_inversely_related=True)  # Higher factor = less distortion
        self.device = torch.device(device)
        self._cached_models = {}

    def _get_model(self, quality: int):
        """
        Retrieves or loads the mbt2018 model for the given quality level.

        The model is cached globally using (quality, device) as key to prevent redundant loading
        and GPU memory duplication.

        Args:
            quality (int): Compression quality level (1-8).

        Returns:
            torch.nn.Module: The pre-trained VAE model in evaluation mode.
        """
        q = max(1, min(8, quality))
        cache_key = (q, self.device)
        if quality not in self._cached_models:
            if cache_key in VAE_MBT2018Attack._global_model_cache:
                self._cached_models[quality] = VAE_MBT2018Attack._global_model_cache[cache_key]
            else:
                model = mbt2018(quality=q, pretrained=True).eval().to(self.device)
                VAE_MBT2018Attack._global_model_cache[cache_key] = model
                self._cached_models[quality] = model
        return self._cached_models[quality]

    @torch.inference_mode()
    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: int = 3) -> List[
        ndarray]:
        """
        Applies the VAE-based compression attack with resize pre/post-processing.

        The attack pipeline is:
            1. Resize each input image to 512x512 using nearest-neighbor interpolation.
            2. Batch the preprocessed tensors and move to GPU.
            3. Forward pass through the MBT2018 VAE model.
            4. Resize each reconstructed image back to its original size.
            5. Return the batch of distorted images.

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each of shape [H, W, 3], dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (not used in this attack).
            factor (int): Compression quality level (1-8). Higher values preserve more detail.

        Returns:
            List[ndarray]: Batch of reconstructed images, each with the same shape and dtype as the input.
        """
        if not stego_imgs:
            return []

        # Step 1: Detect if input is grayscale
        is_grayscale = len(stego_imgs[0].shape) == 2
        original_shapes = [img.shape[:2] for img in stego_imgs]
        target_h, target_w = original_shapes[0]

        # Step 2: Convert to 3-channel if grayscale
        if is_grayscale:
            # Convert (H, W) -> (H, W, 3) by repeating the single channel
            processed_imgs = [np.stack([img, img, img], axis=-1) for img in stego_imgs]
        else:
            processed_imgs = stego_imgs  # Already RGB

        # Step 3: Batch preprocessing
        batch_np = np.stack(processed_imgs, axis=0).astype(np.float32)  # [B, H, W, 3]
        batch_float = batch_np / 255.0  # Normalize to [0,1]

        # To tensor: [B, H, W, 3] -> [B, 3, H, W]
        batch_tensor = torch.from_numpy(batch_float).permute(0, 3, 1, 2).to(self.device)

        # Step 4: Resize to model input size
        batch_tensor = F.interpolate(
            batch_tensor,
            size=(512, 512),
            mode='bilinear',
            align_corners=False
        )  # [B, 3, 512, 512]

        # Step 5: Forward pass
        model = self._get_model(factor)
        output = model(batch_tensor)
        rec_batch = output["x_hat"].clamp(0, 1)  # [B, 3, 512, 512]

        # Step 6: Resize back to original size
        rec_batch = F.interpolate(
            rec_batch,
            size=(target_h, target_w),
            mode='bilinear',
            align_corners=False
        )  # [B, 3, H, W]

        # Step 7: Convert back to numpy
        rec_np = rec_batch.permute(0, 2, 3, 1).cpu().numpy()  # [B, H, W, 3]
        rec_np = (rec_np * 255).astype(np.uint8)  # [0,255]

        # Step 8: If input was grayscale, convert output back to grayscale
        # But keep shape consistent: if input was (H, W), output should be (H, W)
        if is_grayscale:
            # Convert back to grayscale using luminance formula
            # Y = 0.299*R + 0.587*G + 0.114*B
            rec_gray = np.dot(rec_np, [0.299, 0.587, 0.114]).astype(np.uint8)
            return [rec_gray[i] for i in range(rec_gray.shape[0])]
        else:
            return [rec_np[i] for i in range(rec_np.shape[0])]


class VAE_Cheng2020Attack(BaseTestAttackModel):
    """
    A Variational Autoencoder (VAE)-based attack using the cheng2020_anchor model.
    Applies learned image compression with attention modules to disrupt embedded watermarks.

    This attack first resizes the input image to 512x512 using nearest-neighbor interpolation,
    then compresses and reconstructs it using the Cheng2020 (CVPR 2020) model,
    and finally resizes it back to the original resolution. The resize operations introduce additional
    geometric distortion, making this a stronger attack than compression alone.

    The 'factor' parameter controls the compression quality (1-6):
        - 1: strongest compression (lowest bitrate, highest distortion)
        - 6: weakest compression (highest bitrate, near lossless)

    Reference:
        Cheng, Z., Sun, H., & Takeuchi, M. (2020).
        Learned image compression with discretized Gaussian mixture likelihoods and attention modules.
        IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR).
        https://arxiv.org/abs/2001.01568

    Note:
        - Input: List of uint8 RGB images [H, W, 3], range [0, 255]
        - Output: List of reconstructed images, same shape and dtype
        - The model is cached per quality level and device for efficiency
    """
    _global_model_cache = {}

    def __init__(self, device: str = "cuda", noisename: str = "VAE_Cheng2020Attack"):
        """
        Initializes the attack model with the specified device and name.

        Args:
            device (str): Device to run the model on ('cuda' or 'cpu').
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename, factor_inversely_related=True)  # Higher factor = less distortion
        self.device = torch.device(device)
        self._cached_models = {}

    def _get_model(self, quality: int):
        """
        Retrieves or loads the cheng2020_anchor model for the given quality level.

        The model is cached globally using (quality, device) as key to prevent redundant loading
        and GPU memory duplication.

        Args:
            quality (int): Compression quality level (1-6).

        Returns:
            torch.nn.Module: The pre-trained VAE model in evaluation mode.
        """
        if quality not in self._cached_models:
            q = max(1, min(6, quality))
            cache_key = (q, self.device)
            if cache_key in VAE_Cheng2020Attack._global_model_cache:
                model = VAE_Cheng2020Attack._global_model_cache[cache_key]
                self._cached_models[quality] = model
            else:
                model = cheng2020_anchor(quality=q, pretrained=True).eval().to(self.device)
                VAE_Cheng2020Attack._global_model_cache[cache_key] = model
                self._cached_models[quality] = model
        return self._cached_models[quality]

    @torch.inference_mode()
    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: int = 3) -> List[
        ndarray]:
        """
        Applies the VAE-based compression attack with resize pre/post-processing.

        The attack pipeline is:
            1. Resize each input image to 512x512 using nearest-neighbor interpolation.
            2. Batch the preprocessed tensors and move to GPU.
            3. Forward pass through the Cheng2020 VAE model.
            4. Resize each reconstructed image back to its original size.
            5. Return the batch of distorted images.

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each of shape [H, W, 3], dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (not used in this attack).
            factor (int): Compression quality level (1-6). Higher values preserve more detail.

        Returns:
            List[ndarray]: Batch of reconstructed images, each with the same shape and dtype as the input.
        """
        if not stego_imgs:
            return []

        # Step 1: Detect if input is grayscale
        is_grayscale = len(stego_imgs[0].shape) == 2
        original_shapes = [img.shape[:2] for img in stego_imgs]
        target_h, target_w = original_shapes[0]

        # Step 2: Convert to 3-channel if grayscale
        if is_grayscale:
            # Convert (H, W) -> (H, W, 3) by repeating the single channel
            processed_imgs = [np.stack([img, img, img], axis=-1) for img in stego_imgs]
        else:
            processed_imgs = stego_imgs  # Already RGB

        # Step 3: Batch preprocessing
        batch_np = np.stack(processed_imgs, axis=0).astype(np.float32)  # [B, H, W, 3]
        batch_float = batch_np / 255.0  # Normalize to [0,1]

        # To tensor: [B, H, W, 3] -> [B, 3, H, W]
        batch_tensor = torch.from_numpy(batch_float).permute(0, 3, 1, 2).to(self.device)

        # Step 4: Resize to model input size
        batch_tensor = F.interpolate(
            batch_tensor,
            size=(512, 512),
            mode='bilinear',
            align_corners=False
        )  # [B, 3, 512, 512]

        # Step 5: Forward pass
        model = self._get_model(factor)
        output = model(batch_tensor)
        rec_batch = output["x_hat"].clamp(0, 1)  # [B, 3, 512, 512]

        # Step 6: Resize back to original size
        rec_batch = F.interpolate(
            rec_batch,
            size=(target_h, target_w),
            mode='bilinear',
            align_corners=False
        )  # [B, 3, H, W]

        # Step 7: Convert back to numpy
        rec_np = rec_batch.permute(0, 2, 3, 1).cpu().numpy()  # [B, H, W, 3]
        rec_np = (rec_np * 255).astype(np.uint8)  # [0,255]

        # Step 8: If input was grayscale, convert output back to grayscale
        # But keep shape consistent: if input was (H, W), output should be (H, W)
        if is_grayscale:
            # Convert back to grayscale using luminance formula
            # Y = 0.299*R + 0.587*G + 0.114*B
            rec_gray = np.dot(rec_np, [0.299, 0.587, 0.114]).astype(np.uint8)
            return [rec_gray[i] for i in range(rec_gray.shape[0])]
        else:
            return [rec_np[i] for i in range(rec_np.shape[0])]


class ReSDPipeline(StableDiffusionPipeline):
    """
    A custom Stable Diffusion pipeline for image generation with support for head-start latents and dual prompts.
    Extends the base StableDiffusionPipeline from the diffusers library.
    """

    @torch.no_grad()
    def __call__(
            self,
            prompt: Union[str, List[str]],
            prompt1_steps: Optional[int] = None,
            prompt2: Optional[str] = None,
            head_start_latents: Optional[Union[torch.FloatTensor, list]] = None,
            head_start_step: Optional[int] = None,
            height: Optional[int] = None,
            width: Optional[int] = None,
            num_inference_steps: int = 50,
            guidance_scale: float = 7.5,
            negative_prompt: Optional[Union[str, List[str]]] = None,
            num_images_per_prompt: Optional[int] = 1,
            eta: float = 0.0,
            generator: Optional[torch.Generator] = None,
            latents: Optional[torch.FloatTensor] = None,
            output_type: Optional[str] = "pil",
            return_dict: bool = True,
            callback: Optional[Callable[[int, int, torch.FloatTensor], None]] = None,
            callback_steps: Optional[int] = 1,
    ):
        """
        Generates images using the Stable Diffusion model with optional head-start latents and dual prompts.

        Args:
            prompt (Union[str, List[str]]): The text prompt(s) to guide image generation.
            prompt1_steps (Optional[int]): Number of steps to use the first prompt before switching to prompt2.
            prompt2 (Optional[str]): Secondary prompt for later denoising steps.
            head_start_latents (Optional[Union[torch.FloatTensor, list]]): Pre-generated latents for head-start.
            head_start_step (Optional[int]): Step to start denoising from when using head-start latents.
            height (Optional[int]): Height of the generated image in pixels.
            width (Optional[int]): Width of the generated image in pixels.
            num_inference_steps (int): Number of denoising steps, defaults to 50.
            guidance_scale (float): Guidance scale for classifier-free guidance, defaults to 7.5.
            negative_prompt (Optional[Union[str, List[str]]]): Negative prompt(s) to avoid in generation.
            num_images_per_prompt (Optional[int]): Number of images to generate per prompt, defaults to 1.
            eta (float): DDIM eta parameter, defaults to 0.0.
            generator (Optional[torch.Generator]): Random number generator for reproducibility.
            latents (Optional[torch.FloatTensor]): Pre-generated noisy latents.
            output_type (Optional[str]): Output format ("pil" or "np.array"), defaults to "pil".
            return_dict (bool): Whether to return a StableDiffusionPipelineOutput object, defaults to True.
            callback (Optional[Callable]): Callback function called during inference.
            callback_steps (Optional[int]): Frequency of callback invocation, defaults to 1.

        Returns:
            StableDiffusionPipelineOutput or tuple: Generated images and NSFW flags if return_dict is True,
                                                  otherwise a tuple of (images, nsfw_content_detected).
        """
        height = height or self.unet.config.sample_size * self.vae_scale_factor
        width = width or self.unet.config.sample_size * self.vae_scale_factor
        self.check_inputs(prompt, height, width, callback_steps)
        batch_size = 1 if isinstance(prompt, str) else len(prompt)
        device = self._execution_device
        do_classifier_free_guidance = guidance_scale > 1.0
        text_embeddings = self._encode_prompt(
            prompt, device, num_images_per_prompt, do_classifier_free_guidance, negative_prompt
        )
        if prompt2 is not None:
            text_embeddings2 = self._encode_prompt(
                prompt2, device, num_images_per_prompt, do_classifier_free_guidance, negative_prompt
            )
        self.scheduler.set_timesteps(num_inference_steps, device=device)
        timesteps = self.scheduler.timesteps
        if head_start_latents is None:
            num_channels_latents = self.unet.in_channels
            latents = self.prepare_latents(
                batch_size * num_images_per_prompt,
                num_channels_latents,
                height,
                width,
                text_embeddings.dtype,
                device,
                generator,
                latents,
            )
        else:
            if type(head_start_latents) == list:
                latents = head_start_latents[-1]
                assert len(head_start_latents) == self.scheduler.config.solver_order
            else:
                latents = head_start_latents
        extra_step_kwargs = self.prepare_extra_step_kwargs(generator, eta)
        num_warmup_steps = len(timesteps) - num_inference_steps * self.scheduler.order
        with self.progress_bar(total=num_inference_steps) as progress_bar:
            for i, t in enumerate(timesteps):
                if not head_start_step or i >= head_start_step:
                    latent_model_input = torch.cat([latents] * 2) if do_classifier_free_guidance else latents
                    latent_model_input = self.scheduler.scale_model_input(latent_model_input, t)
                    if prompt1_steps is None or i < prompt1_steps:
                        noise_pred = self.unet(latent_model_input, t, encoder_hidden_states=text_embeddings).sample
                    else:
                        noise_pred = self.unet(latent_model_input, t, encoder_hidden_states=text_embeddings2).sample
                    if do_classifier_free_guidance:
                        noise_pred_uncond, noise_pred_text = noise_pred.chunk(2)
                        noise_pred = noise_pred_uncond + guidance_scale * (noise_pred_text - noise_pred_uncond)
                        latents = self.scheduler.step(noise_pred, t, latents, **extra_step_kwargs).prev_sample
                if (i + 1) > num_warmup_steps and (i + 1) % self.scheduler.order == 0:
                    progress_bar.update()
                    if callback is not None and i % callback_steps == 0:
                        callback(i, t, latents)
        image = self.decode_latents(latents)
        has_nsfw_concept = False
        if output_type == "pil":
            image = self.numpy_to_pil(image)
        if not return_dict:
            return (image, has_nsfw_concept)
        return StableDiffusionPipelineOutput(images=image, nsfw_content_detected=has_nsfw_concept)



class DiffuseAttack(BaseTestAttackModel):
    """
    A single-step diffusion-based attack using ReSDPipeline.
    Adds noise at a specified timestep and regenerates the image via a head-start mechanism to disrupt embedded watermarks.

    This attack leverages classifier-free guidance to regenerate the image with high fidelity while preserving semantic content.
    It is particularly effective against watermarking schemes that rely on high-frequency signals.

    The process:
        1. Encodes the input image into latent space.
        2. Adds diffusion noise at a specified timestep.
        3. Uses "head-start decoding" to regenerate the image from an intermediate step, balancing fidelity and distortion.
    Note:
        - Input: List of uint8 images, each [H, W] (grayscale) or [H, W, 3] (RGB), range [0, 255]
        - Output: List of regenerated images, same shape and dtype
        - For grayscale images, the single channel is replicated to three channels for processing,
          and the output is converted back to grayscale by taking one channel
        - The model uses Stable Diffusion 2.1 base (fp16) and requires CUDA
        - 'factor' controls the noise timestep (1-200): higher = more noise
    """
    _global_model_cache = {}

    def __init__(self, model_id: str = "stabilityai/stable-diffusion-2-1-base", noisename: str = "DiffuseAttack"):
        """
        Initializes the diffusion attack model.

        Args:
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename, factor_inversely_related=False)
        self.model_id = model_id
        self.pipe = self._get_pipe()

    def _get_pipe(self):
        """
        Loads and caches the ReSDPipeline (a variant of Stable Diffusion 2.1) for efficient reuse.

        Returns:
            ReSDPipeline: The diffusion pipeline, loaded in fp16 and moved to GPU.

        Raises:
            RuntimeError: If CUDA is not available, as this attack is GPU-only.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        cache_key = (self.device, "sd2.1-diffuse-attack")
        if cache_key in DiffuseAttack._global_model_cache:
            return DiffuseAttack._global_model_cache[cache_key]

        if not torch.cuda.is_available():
            raise RuntimeError("DiffuseAttack requires CUDA. CPU is not supported.")

        pipe = ReSDPipeline.from_pretrained(
            self.model_id,
            torch_dtype=torch.float16,
            local_files_only=True
        )
        pipe.to(self.device)
        pipe.set_progress_bar_config(disable=True)
        DiffuseAttack._global_model_cache[cache_key] = pipe
        return pipe

    @torch.inference_mode()
    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: int = 60) -> List[ndarray]:
        """
        Applies a single-step diffusion regeneration attack to a batch of images (grayscale or RGB).

        The attack uses a "head-start" decoding strategy:
            - Noise is added at an early diffusion timestep (controlled by 'factor').
            - The decoder starts from a later step (head_start_step), allowing the model
              to regenerate content while preserving some original structure.

        For grayscale images:
            - The single channel is replicated to three channels to create a pseudo-RGB image.
            - After processing, one channel is taken to restore the grayscale shape.

        This method is highly efficient due to batched processing and minimizes CPU-GPU transfer.

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each [H, W] (grayscale) or [H, W, 3] (RGB),
                                       dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored, for interface compatibility).
            factor (int): Diffusion timestep for noise injection, range [1, 200]. Higher values = more noise.

        Returns:
            List[ndarray]: Batch of regenerated images, each with the same shape and dtype as input.
        """
        if not stego_imgs:
            return []

        # Determine if images are grayscale ([H, W]) or RGB ([H, W, 3])
        is_grayscale = len(stego_imgs[0].shape) == 2

        # Convert grayscale images to pseudo-RGB by replicating channels
        if is_grayscale:
            batch_np = np.stack([np.repeat(img[..., np.newaxis], 3, axis=-1) for img in stego_imgs], axis=0).astype(np.float32)
        else:
            batch_np = np.stack(stego_imgs, axis=0).astype(np.float32)

        pipe = self.pipe
        device = self.device
        generator = torch.Generator(device=device).manual_seed(1024)

        # Clip noise timestep to valid range
        noise_step = int(np.clip(factor, 1, 200))
        timestep = torch.tensor([noise_step], device=device)

        # -------------------------------
        # 🔥 High-efficiency preprocessing (vectorized)
        # -------------------------------
        # Normalize to [-1, 1] in one vectorized operation
        batch_np = (batch_np / 127.5) - 1.0
        # Convert to tensor: HWC -> CHW, then to GPU and fp16
        batch_tensor = torch.from_numpy(batch_np).permute(0, 3, 1, 2).contiguous().half().to(device)

        # -------------------------------
        # 🚀 Latent encoding and noise injection
        # -------------------------------
        # Encode to latent space
        latents = pipe.vae.encode(batch_tensor).latent_dist.sample(generator)
        latents = latents * pipe.vae.config.scaling_factor  # Scale latent

        # Add noise at specified timestep
        noise = torch.randn_like(latents)
        noisy_latents = pipe.scheduler.add_noise(latents, noise, timestep).type(torch.float16)

        # -------------------------------
        # 🔄 Head-start decoding configuration
        # -------------------------------
        # head_start_step: the step at which the diffusion decoder begins
        # Formula: start earlier for noisier inputs to allow more regeneration
        head_start_step = max(50 - max(noise_step // 20, 1), 1)

        # -------------------------------
        # 🎯 Batch generation with classifier-free guidance
        # -------------------------------
        with torch.autocast(device_type="cuda", dtype=torch.float16):
            output_images = pipe(
                prompt=["" for _ in range(len(stego_imgs))],
                head_start_latents=noisy_latents,
                head_start_step=head_start_step,
                guidance_scale=7.5,  # Standard guidance strength
                generator=generator,
            ).images  # List[PIL.Image] of length B

        # Convert PIL images back to numpy arrays
        noised_batch = [np.array(img) for img in output_images]

        # For grayscale inputs, return one channel to restore [H, W] shape
        if is_grayscale:
            noised_batch = [img[..., 0] for img in noised_batch]

        return noised_batch


class MultiDiffuseAttack(BaseTestAttackModel):
    """
    A multi-step diffusion-based attack that applies DiffuseAttack repeatedly for multiple rounds.
    Each round injects noise and regenerates the image using the same fixed diffusion timestep.

    This attack amplifies the watermark-removal effect by performing sequential regeneration.
    The cumulative distortion can effectively erase subtle, high-frequency watermark signals
    that survive a single diffusion step.

    The 'factor' parameter controls the number of attack rounds (iterations), enabling a
    continuous control over attack strength.

    Reference:
        Ho, J., Jain, C., & Abbeel, P. (2022).
        Classifier-Free Diffusion Guidance.
        arXiv:2207.12598
        https://arxiv.org/abs/2207.12598

    Note:
        - Input: List of uint8 RGB images [H, W, 3], range [0, 255]
        - Output: List of regenerated images, same shape and dtype
        - Each round uses the same fixed noise timestep (self.noise_step)
        - 'factor' specifies the number of iterations (attack strength)
    """

    def __init__(self, model_id: str = "stabilityai/stable-diffusion-2-1-base", noise_step: int = 30, noisename: str = "MultiDiffuseAttack"):
        """
        Initializes the multi-step diffusion attack.

        Args:
            noise_step (int): Fixed diffusion timestep for noise injection in each round, range [1, 200].
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename, factor_inversely_related=False)
        self.noise_step = int(np.clip(noise_step, 1, 200))
        self.diffuse = DiffuseAttack(noisename=f"{noisename}_inner", model_id=model_id)

    @torch.inference_mode()
    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: int = 1) -> List[
        ndarray]:
        """
        Applies multiple rounds of diffusion regeneration attack to a batch of stego images.

        The attack pipeline is:
            For round in range(factor):
                x = DiffuseAttack(x, factor=self.noise_step)
        Each round adds noise and regenerates the image, progressively distorting watermark signals.

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each of shape [H, W, 3], dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored, for interface compatibility).
            factor (int): Number of attack rounds (>=1). More rounds = stronger attack.

        Returns:
            List[ndarray]: Final images after `factor` rounds of diffusion attack, same shape and dtype as inputs.
        """
        if not stego_imgs:
            return []

        x = stego_imgs
        num_rounds = int(factor)

        for step in range(num_rounds):
            # Apply single-step diffusion attack
            x = self.diffuse.attack(x, cover_img=None, factor=self.noise_step)

        return x


class PoissonNoise(BaseTestAttackModel):
    """
    A noise attack that adds Poisson-distributed noise to a batch of images.

    Poisson noise models sensor noise in digital imaging systems, where the variance
    of the noise is proportional to the pixel intensity (e.g., photon counting noise).
    This makes it particularly relevant for evaluating watermark robustness under low-light conditions.

    The 'factor' parameter controls the effective signal-to-noise ratio:
        - Lower factor: stronger noise (simulates low light)
        - Higher factor: weaker noise (simulates high light)

    Reference:
        Foi, A., Trimeche, M., Katkovnik, V., & Egiazarian, K. (2008).
        Practical Poissonian-Gaussian noise modeling and denoising based on precise noise parameter estimation.
        IEEE Transactions on Image Processing, 17(6), 10.1109/TIP.2008.921849

    Note:
        - Input: List of uint8 RGB images [H, W, 3], range [0, 255]
        - Output: List of noisy images, same shape and dtype
        - This implementation uses fully vectorized NumPy operations for maximum CPU efficiency
    """

    def __init__(self, noisename: str = "PoissonNoise"):
        """
        Initializes the Poisson noise attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename, factor_inversely_related=False)  # Higher factor = less noise

    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: float = 1.0) -> List[
        ndarray]:
        """
        Applies Poisson noise to a batch of stego images using fully vectorized operations.

        The noise model is:
            noisy_img = clip( Poisson(img / factor) * factor, 0, 255 )

        This preserves the mean while scaling the variance, simulating realistic sensor noise.

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each [H, W, 3], dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored).
            factor (float): Noise intensity scaling factor. Typical range [0.1, 10.0].

        Returns:
            List[ndarray]: Batch of noisy images, each with the same shape and dtype as input.
        """
        if not stego_imgs:
            return []

        # Stack all images into a single 4D numpy array: [B, H, W, 3]
        batch_np = np.stack(stego_imgs, axis=0).astype(np.float32)  # Shape: (B, H, W, 3)

        # Normalize to [0, 1] for Poisson scaling
        img_normalized = batch_np / 255.0

        # Apply Poisson noise: scale up to increase photon count, then down
        if factor > 1e-6:
            # Simulate Poisson process: higher factor = more photons = less noise
            scaled_intensity = img_normalized * (255.0 / factor)
            noisy_intensity = np.random.poisson(scaled_intensity)
            noisy_normalized = noisy_intensity * (factor / 255.0)
        else:
            noisy_normalized = img_normalized  # No noise

        # Denormalize and clip
        noisy_batch = np.clip(noisy_normalized * 255.0, 0, 255).astype(np.uint8)

        # Convert back to list of arrays for output compatibility
        return [noisy_batch[i] for i in range(noisy_batch.shape[0])]


class ContrastReduction(BaseTestAttackModel):
    """
    A contrast reduction attack that decreases the intensity difference between light and dark regions of an image.

    This attack scales pixel values toward the overall mean intensity, reducing dynamic range.
    It can weaken watermark signals that rely on contrast variations.

    The 'factor' parameter controls the strength:
        - 1.0: No change (identity)
        - 0.0: All pixels become the mean value (maximum reduction)

    The transformation is: output = mean + (input - mean) * factor

    Note:
        - Input: List of uint8 images, each [H, W] (grayscale) or [H, W, 3] (RGB), range [0, 255]
        - Output: List of contrast-reduced images, same shape and dtype
        - The attack is applied independently to each image in the batch
    """

    def __init__(self, noisename: str = "ContrastReduction"):
        """
        Initializes the contrast reduction attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename, factor_inversely_related=True)  # Higher factor = less reduction
        self.factor_inversely_related = True

    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: float = 0.7) -> List[ndarray]:
        """
        Applies contrast reduction to a batch of images (grayscale or RGB) using a vectorized implementation.

        The attack reduces the dynamic range by scaling pixel intensities around the image mean.
        This is equivalent to reducing the gain of the image signal.

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each [H, W] (grayscale) or [H, W, 3] (RGB),
                                       dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored, for interface compatibility).
            factor (float): Contrast scaling factor in [0.0, 1.0].
                           1.0 = no change, 0.0 = fully flattened.

        Returns:
            List[ndarray]: Batch of contrast-reduced images, each with the same shape and dtype as input.
        """
        if not stego_imgs:
            return []

        # Stack all images into a single array for vectorized processing
        # Determine if images are grayscale ([H, W]) or RGB ([H, W, 3])
        first_img = stego_imgs[0]
        is_grayscale = len(first_img.shape) == 2

        if is_grayscale:
            # For grayscale: stack into [B, H, W, 1] for consistent processing
            batch_np = np.stack([img[..., np.newaxis] for img in stego_imgs], axis=0).astype(np.float32)
        else:
            # For RGB: stack into [B, H, W, 3]
            batch_np = np.stack(stego_imgs, axis=0).astype(np.float32)

        # Compute mean intensity for each image in the batch
        # For grayscale: mean over [H, W], for RGB: mean over [H, W, C]
        mean_values = np.mean(batch_np, axis=(1, 2), keepdims=True)  # Shape: [B, 1, 1] or [B, 1, 1, 1]

        # Apply contrast reduction: shift to zero-mean, scale, then restore mean
        noised_batch = mean_values + (batch_np - mean_values) * factor

        # Clip to valid range and convert back to uint8
        noised_batch = np.clip(noised_batch, 0, 255).astype(np.uint8)

        # Convert back to list of arrays, restoring original shape
        if is_grayscale:
            # Remove the channel dimension for grayscale images
            return [noised_batch[i, :, :, 0] for i in range(noised_batch.shape[0])]
        else:
            # Keep the RGB channels
            return [noised_batch[i] for i in range(noised_batch.shape[0])]


class ContrastEnhancement(BaseTestAttackModel):
    """
    A contrast enhancement attack that amplifies the intensity differences between light and dark areas of an image.

    This attack scales pixel values away from the mean intensity, increasing the dynamic range.
    It can stress watermarking schemes that are sensitive to local contrast changes.

    The 'factor' parameter controls the strength:
        - 1.0: No change (identity)
        - > 1.0: Increased contrast (e.g., 1.5, 2.0, 3.0)

    The transformation is: output = mean + (input - mean) * factor

    Note:
        - Input: List of uint8 images, each [H, W] (grayscale) or [H, W, 3] (RGB), range [0, 255]
        - Output: List of enhanced images, same shape and dtype
        - The attack is applied independently to each image in the batch
    """

    def __init__(self, noisename: str = "ContrastEnhancement"):
        """
        Initializes the contrast enhancement attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename, factor_inversely_related=False)  # Higher factor = more enhancement

    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: float = 1.5) -> List[ndarray]:
        """
        Applies contrast enhancement to a batch of images (grayscale or RGB) using a vectorized implementation.

        The attack increases the dynamic range by scaling pixel intensities around the image mean.
        This is equivalent to increasing the gain of the image signal.

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each [H, W] (grayscale) or [H, W, 3] (RGB),
                                       dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored, for interface compatibility).
            factor (float): Contrast scaling factor >= 1.0.
                           1.0 = no change, higher values = stronger enhancement.

        Returns:
            List[ndarray]: Batch of contrast-enhanced images, each with the same shape and dtype as input.
        """
        if not stego_imgs:
            return []

        # Determine if images are grayscale ([H, W]) or RGB ([H, W, 3])
        first_img = stego_imgs[0]
        is_grayscale = len(first_img.shape) == 2

        # Stack all images into a single array for vectorized processing
        if is_grayscale:
            # For grayscale: stack into [B, H, W, 1] for consistent processing
            batch_np = np.stack([img[..., np.newaxis] for img in stego_imgs], axis=0).astype(np.float32)
        else:
            # For RGB: stack into [B, H, W, 3]
            batch_np = np.stack(stego_imgs, axis=0).astype(np.float32)

        # Compute mean intensity for each image in the batch
        # For grayscale: mean over [H, W], for RGB: mean over [H, W, C]
        mean_values = np.mean(batch_np, axis=(1, 2), keepdims=True)  # Shape: [B, 1, 1] or [B, 1, 1, 1]

        # Apply contrast enhancement: shift to zero-mean, scale, then restore mean
        enhanced_batch = mean_values + (batch_np - mean_values) * factor

        # Clip to valid range and convert back to uint8
        enhanced_batch = np.clip(enhanced_batch, 0, 255).astype(np.uint8)

        # Convert back to list of arrays, restoring original shape
        if is_grayscale:
            # Remove the channel dimension for grayscale images
            return [enhanced_batch[i, :, :, 0] for i in range(enhanced_batch.shape[0])]
        else:
            # Keep the RGB channels
            return [enhanced_batch[i] for i in range(enhanced_batch.shape[0])]


class GammaCorrection(BaseTestAttackModel):
    """
    A brightness adjustment attack using gamma curve transformation.

    Gamma correction applies a non-linear power-law transformation to the image intensity,
    which can simulate display calibration differences or intentional brightness attacks.
    This can affect watermark robustness, especially for methods sensitive to non-linear pixel shifts.

    The 'factor' parameter is the gamma value:
        - factor < 1.0: brightens the image (expands dark tones)
        - factor = 1.0: no change
        - factor > 1.0: darkens the image (compresses bright tones)

    Reference:
        Poynton, C. (1998). Digital Video and HDTV: Algorithms and Interfaces.

    Note:
        - Input: List of uint8 images, each [H, W] (grayscale) or [H, W, 3] (RGB), range [0, 255]
        - Output: List of gamma-corrected images, same shape and dtype
        - The transformation is applied per-channel for RGB images and to the single channel for grayscale
    """

    def __init__(self, noisename: str = "GammaCorrection"):
        """
        Initializes the gamma correction attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename, factor_inversely_related=False)  # Higher factor = more darkening

    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: float = 1.5) -> List[ndarray]:
        """
        Applies gamma correction to a batch of images (grayscale or RGB) using a lookup table (LUT) for efficiency.

        The transformation: output = input ** (1/gamma)
        A lookup table is precomputed for all 256 possible pixel values and applied via cv2.LUT.

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each [H, W] (grayscale) or [H, W, 3] (RGB),
                                       dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored, for interface compatibility).
            factor (float): Gamma value, typically in [0.1, 3.0].
                           <1.0 brightens, >1.0 darkens.

        Returns:
            List[ndarray]: Batch of gamma-corrected images, each with the same shape and dtype as input.
        """
        if not stego_imgs:
            return []

        inv_gamma = 1.0 / max(factor, 1e-6)
        table = np.array([(i / 255.0) ** inv_gamma * 255 for i in range(256)]).astype(np.uint8)

        noised_batch = []
        is_grayscale = len(stego_imgs[0].shape) == 2

        for img in stego_imgs:
            if is_grayscale:
                # Ensure the image is contiguous
                img = np.ascontiguousarray(img, dtype=np.uint8)
                corrected_img = cv2.LUT(img, table)
            else:
                # Convert to BGR and ensure contiguous
                bgr_img = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_RGB2BGR)
                bgr_img = np.ascontiguousarray(bgr_img, dtype=np.uint8)
                corrected_img = cv2.LUT(bgr_img, table)
                corrected_img = cv2.cvtColor(corrected_img, cv2.COLOR_BGR2RGB)
            noised_batch.append(corrected_img)

        return noised_batch


class ChromaticAberration(BaseTestAttackModel):
    """
    A color distortion attack that simulates chromatic aberration by laterally shifting color channels.

    This attack mimics an optical phenomenon where different wavelengths (colors) are focused
    at different positions, causing red and blue fringes at high-contrast edges. It can disrupt
    watermark signals that rely on precise color alignment.

    The 'factor' parameter controls the pixel shift amount:
        - Positive values: blue shifts right, red shifts left
        - Higher magnitude = stronger visual artifact

    Note:
        - Input: List of uint8 images, each [H, W] (grayscale) or [H, W, 3] (RGB), range [0, 255]
        - Output: List of distorted images, same shape and dtype as input
        - For grayscale images, the single channel is replicated to three channels for processing,
          and the output is converted back to grayscale by taking one channel
        - For RGB images, the attack shifts red and blue channels while keeping green unchanged
        - The shift wraps around the horizontal edges (using np.roll)
    """

    def __init__(self, noisename: str = "ChromaticAberration"):
        """
        Initializes the chromatic aberration attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename, factor_inversely_related=False)  # Higher factor = stronger effect

    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: int = 2) -> List[ndarray]:
        """
        Applies chromatic aberration to a batch of images (grayscale or RGB) using vectorized NumPy operations.

        For RGB images:
            - Blue channel (index 2) is shifted to the right by 'factor' pixels
            - Red channel (index 0) is shifted to the left by 'factor' pixels
            - Green channel (index 1) remains unchanged
        For grayscale images:
            - The single channel is replicated to three channels ([H, W] -> [H, W, 3]) for processing
            - After applying the attack, one channel is taken to return a grayscale image ([H, W])

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each [H, W] (grayscale) or [H, W, 3] (RGB),
                                       dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored, for interface compatibility).
            factor (int): Number of pixels to shift the red and blue channels. Typical range [1, 10].

        Returns:
            List[ndarray]: Batch of images with chromatic aberration applied, same shape and dtype as input.
        """
        if not stego_imgs:
            return []

        # Determine if images are grayscale ([H, W]) or RGB ([H, W, 3])
        first_img = stego_imgs[0]
        is_grayscale = len(first_img.shape) == 2

        # Stack all images into a single 4D array: [B, H, W, 3]
        if is_grayscale:
            # Replicate grayscale channel to create pseudo-RGB images
            batch_np = np.stack([np.repeat(img[..., np.newaxis], 3, axis=-1) for img in stego_imgs], axis=0)
        else:
            # Stack RGB images directly
            batch_np = np.stack(stego_imgs, axis=0)

        # Split channels: [B, H, W]
        r = batch_np[..., 0]
        g = batch_np[..., 1]
        b = batch_np[..., 2]

        # Apply horizontal shift (wrap around)
        shift = int(factor)
        b_shifted = np.roll(b, shift=shift, axis=2)  # Right shift for blue
        r_shifted = np.roll(r, shift=-shift, axis=2)  # Left shift for red
        # Green remains unchanged

        # Merge channels back
        noised_batch = np.stack([r_shifted, g, b_shifted], axis=-1)  # [B, H, W, 3]

        # Convert back to list of arrays, restoring original shape
        if is_grayscale:
            # For grayscale inputs, return one channel to restore [H, W] shape
            return [noised_batch[i, :, :, 0] for i in range(noised_batch.shape[0])]
        else:
            # For RGB inputs, keep the full [H, W, 3] shape
            return [noised_batch[i] for i in range(noised_batch.shape[0])]


class FlipAttack(BaseTestAttackModel):
    """
    A spatial flip attack that flips images either horizontally or vertically.

    ✅ Assumes all input images have the SAME shape [H, W, C] or [H, W]
    ✅ Fully vectorized batch processing (no Python loops during flip)
    ✅ Supports both grayscale and color images
    ✅ GUARANTEES output dtype is uint8

    The 'factor' parameter controls the flip direction:
        - 'H': Horizontal flip (left-right mirror)
        - 'V': Vertical flip (up-down mirror)

    Note:
        - Input: List of uint8 images, all same shape [H, W] or [H, W, C], range [0, 255]
        - Output: List of flipped images, same shape and guaranteed uint8 dtype
    """

    def __init__(self, noisename: str = "FlipAttack"):
        super().__init__(noisename=noisename, factor_inversely_related=False)

    def attack(self, stego_imgs: List[ndarray[np.uint8]], cover_img: Optional[List[ndarray[np.uint8]]] = None,
               factor: str = 'H') -> List[ndarray[np.uint8]]:
        """
        Applies flip to a batch of images with identical shape using full vectorization.
        GUARANTEES that output dtype is uint8.

        Args:
            stego_imgs (List[ndarray]): List of uint8 images, all same shape [H, W] or [H, W, C].
            cover_img: Ignored (for compatibility).
            factor (str): 'H' for horizontal, 'V' for vertical flip.

        Returns:
            List[ndarray]: Flipped images, same shape and guaranteed uint8 dtype.

        Raises:
            ValueError: If factor is not 'H' or 'V'.
        """
        if not stego_imgs:
            return []

        if factor not in ('H', 'V'):
            raise ValueError(f"factor must be 'H' or 'V', got '{factor}'")

        # Step 1: Stack all images into a batch tensor
        batch_tensor = np.stack(stego_imgs, axis=0)  # [B, H, W] or [B, H, W, C]

        # Step 2: Handle grayscale vs color
        if batch_tensor.ndim == 3:
            # Grayscale [B, H, W] → expand to [B, H, W, 1] for uniform processing
            batch_tensor = np.expand_dims(batch_tensor, axis=-1)  # [B, H, W, 1]
            is_gray = True
        else:
            is_gray = False

        # Step 3: Perform flip (vectorized)
        flip_axis = 2 if factor == 'H' else 1  # axis=2: width, axis=1: height
        flipped_batch = np.flip(batch_tensor, axis=flip_axis)

        # Step 4: Restore original shape and ensure uint8 dtype
        if is_gray:
            flipped_batch = flipped_batch.squeeze(axis=-1)  # [B, H, W]

        # Ensure output is uint8 (defensive programming)
        flipped_batch = flipped_batch.astype(np.uint8)

        # Step 5: Convert back to list of arrays
        return [flipped_batch[i] for i in range(flipped_batch.shape[0])]


class ColorQuantization(BaseTestAttackModel):
    """
    A color reduction attack that reduces the number of distinct colors in an image.

    This attack simulates low-color-depth displays or aggressive image compression by
    quantizing pixel values to the nearest multiple of the 'factor'. It can disrupt
    watermark signals that rely on fine color gradients or high color fidelity.

    The 'factor' parameter controls the quantization step size:
        - 4: Very coarse (16^3 = 4096 colors)
        - 16: Medium (16^3 = 4096 colors, but coarser steps)
        - 32: Very coarse (8^3 = 512 colors)

    The transformation is: output = (input // factor) * factor

    Note:
        - Input: List of uint8 RGB images [H, W, 3], range [0, 255]
        - Output: List of quantized images, same shape and dtype
        - The operation is applied independently to each channel
    """

    def __init__(self, noisename: str = "ColorQuantization"):
        """
        Initializes the color quantization attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename,
                         factor_inversely_related=False)  # Higher factor = fewer colors = stronger attack

    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: int = 16) -> List[
        ndarray]:
        """
        Applies color quantization to a batch of stego images using vectorized integer arithmetic.

        The attack reduces color precision by flooring each pixel value to the nearest
        multiple of 'factor'. This creates visible banding and eliminates subtle color variations.

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each [H, W, 3], dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored, for interface compatibility).
            factor (int): Quantization step size, typically in [4, 32]. Higher values = fewer colors.

        Returns:
            List[ndarray]: Batch of color-quantized images, each with the same shape and dtype as input.
        """
        if not stego_imgs:
            return []

        # Stack all images into a single 4D array: [B, H, W, 3]
        batch_np = np.stack(stego_imgs, axis=0).astype(np.uint8)

        # Apply color quantization: floor to nearest multiple of 'factor'
        # Using integer arithmetic: (x // factor) * factor
        if factor > 1:
            quantized_batch = (batch_np // factor) * factor
        else:
            quantized_batch = batch_np  # No quantization if factor <= 1

        # Clip to valid range (though not necessary with integer ops) and ensure dtype
        quantized_batch = np.clip(quantized_batch, 0, 255).astype(np.uint8)

        # Convert back to list of arrays for output compatibility
        return [quantized_batch[i] for i in range(quantized_batch.shape[0])]


class WebPCompression(BaseTestAttackModel):
    """
    A lossy compression attack that simulates WebP encoding artifacts.

    This attack encodes the input image into the WebP format at a specified quality level
    and then decodes it back to RGB. The recompression introduces compression artifacts
    such as blockiness, blurring, and color banding, which can disrupt embedded watermarks.

    The 'factor' parameter controls the compression quality:
        - 10: Very low quality (high compression, severe artifacts)
        - 100: Lossless (no artifacts, for baseline testing)

    This attack is highly relevant for evaluating watermark robustness against
    web-based image delivery systems where WebP is widely used.

    Reference:
        Google. (2023). WebP Image Format.
        https://developers.google.com/speed/webp

    Note:
        - Input: List of uint8 RGB images [H, W, 3], range [0, 255]
        - Output: List of compressed images, same shape and dtype
        - Requires OpenCV with WebP support enabled
    """

    def __init__(self, noisename: str = "WebPCompression"):
        """
        Initializes the WebP compression attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename,
                         factor_inversely_related=True)  # Higher factor = less compression = weaker attack

    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: int = 20) -> List[
        ndarray]:
        """
        Applies WebP compression to a batch of stego images using OpenCV.

        For each image:
            1. Converts from RGB to BGR (OpenCV default).
            2. Encodes to WebP format with specified quality.
            3. Decodes back to BGR.
            4. Converts back to RGB.

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each [H, W, 3], dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored, for interface compatibility).
            factor (int): WebP quality factor in [10, 100].
                         10 = high compression, 100 = lossless.

        Returns:
            List[ndarray]: Batch of WebP-compressed images, each with the same shape and dtype as input.
        """
        if not stego_imgs:
            return []

        noised_batch = []
        is_color = stego_imgs[0].ndim == 3
        encode_param = [cv2.IMWRITE_WEBP_QUALITY, int(np.clip(factor, 10, 100))]
        for img in stego_imgs:
            if is_color:
                img = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_RGB2BGR)
                _, encoded_img = cv2.imencode('.webp', img, encode_param)
                decoded_img = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)
                decoded_img = cv2.cvtColor(decoded_img, cv2.COLOR_BGR2RGB)
            else:
                _, encoded_img = cv2.imencode('.webp', img.astype(np.uint8), encode_param)
                decoded_img = cv2.imdecode(encoded_img, cv2.IMREAD_GRAYSCALE)
            noised_batch.append(decoded_img)
        return noised_batch


class UnsharpMasking(BaseTestAttackModel):
    """
    An image sharpening attack using unsharp masking technique with full batch support.

    This attack enhances high-frequency details by amplifying the residuals between the original
    and a blurred version of the image. It is effective against watermarking methods sensitive
    to edge enhancement.

    The 'factor' parameter controls the sharpening strength:
        - 0.0: No change
        - >0.0: Increasing sharpening (may amplify artifacts)

    This implementation uses torchvision for true batched Gaussian blur, enabling GPU acceleration
    and eliminating the need for Python loops.

    Reference:
        Pizer, S. M., et al. (1987). Adaptive histogram equalization and its variations.
        Computer Vision, Graphics, and Image Processing, 39(3), 355–368.

    Note:
        - Input: List of uint8 RGB images [H, W, 3], range [0, 255]
        - Output: List of sharpened images, same shape and dtype
        - Uses torchvision for batched Gaussian blur (supports GPU)
    """

    def __init__(self, noisename: str = "UnsharpMasking", sigma: float = 3.0, threshold: float = 0):
        """
        Initializes the unsharp masking attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
            sigma (float): Standard deviation of the Gaussian kernel. Default is 3.0.
            threshold (float): Threshold for high-frequency components (0 = no thresholding).
        """
        super().__init__(noisename=noisename, factor_inversely_related=False)
        self.sigma = sigma
        self.threshold = threshold
        # Pre-instantiate the transform for efficiency
        self.blur_op = transforms.GaussianBlur(kernel_size=int(6 * sigma + 1) // 2 * 2 + 1, sigma=sigma)

    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: float = 1.0) -> List[
        ndarray]:
        """
        Applies unsharp masking to a batch of stego images using fully vectorized operations.

        The pipeline:
            1. Stack images into a 4D numpy array
            2. Convert to float32 and normalize to [0,1]
            3. Convert to CHW tensor and move to device
            4. Apply batched Gaussian blur using torchvision
            5. Compute high-frequency residuals
            6. Apply thresholding (optional)
            7. Sharpen and clamp
            8. Convert back to numpy HWC uint8

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each [H, W, 3], dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored).
            factor (float): Sharpening strength factor, typically in [0.0, 5.0].

        Returns:
            List[ndarray]: Batch of sharpened images, each with the same shape and dtype as input.
        """
        if not stego_imgs:
            return []

        device = "cuda" if torch.cuda.is_available() else "cpu"

        # Stack all images into a single 4D array: [B, H, W, 3]
        batch_np = np.stack(stego_imgs, axis=0).astype(np.float32)  # [B, H, W, 3]

        is_color = batch_np.ndim == 4
        if batch_np.ndim == 3:
            batch_np = np.expand_dims(batch_np, axis=-1)
        # Normalize to [0,1]
        batch_np = batch_np / 255.0

        # Convert to tensor: HWC -> CHW, then to [B, C, H, W]
        batch_tensor = torch.from_numpy(batch_np).permute(0, 3, 1, 2).to(device)  # [B, 3, H, W]

        # Apply batched Gaussian blur
        with torch.no_grad():
            blurred_tensor = self.blur_op(batch_tensor)  # [B, 3, H, W]

        # Compute high-frequency residuals
        high_freq = batch_tensor - blurred_tensor  # [B, 3, H, W]

        # Optional thresholding
        if self.threshold > 0:
            high_freq = torch.where(torch.abs(high_freq) > self.threshold / 255.0, high_freq,
                                    torch.tensor(0.0, device=device))

        # Apply sharpening
        sharpened_tensor = batch_tensor + factor * high_freq  # [B, 3, H, W]
        sharpened_tensor = torch.clamp(sharpened_tensor, 0.0, 1.0)

        # Convert back to numpy: CHW -> HWC
        sharpened_np = (
                sharpened_tensor.permute(0, 2, 3, 1).cpu().numpy() * 255.0
        ).astype(np.uint8)  # [B, H, W, 3]

        noised_imgs = []
        for i in range(sharpened_np.shape[0]):
            if is_color:
                noised_img = sharpened_np[i]
            else:
                noised_img = sharpened_np[i][:, :, 0]
            noised_imgs.append(noised_img)
        # Convert back to list of arrays
        return noised_imgs


class GaussianBlur(BaseTestAttackModel):
    """
    A spatial smoothing attack that applies Gaussian blur to reduce image details.

    This attack convolves the image with a Gaussian kernel, suppressing high-frequency components
    where many watermark signals are embedded. It simulates defocus blur or motion blur effects.

    The 'sigma' parameter controls the standard deviation of the Gaussian kernel:
        - Higher sigma = larger blur radius = stronger smoothing
        - Lower sigma = milder blur

    This implementation uses torchvision for true batched processing, enabling GPU acceleration
    and eliminating Python loops for maximum efficiency.

    Reference:
        Gonzalez, R. C., & Woods, R. E. (2008). Digital Image Processing (3rd ed.). Prentice Hall.

    Note:
        - Input: List of uint8 RGB images [H, W, 3], range [0, 255]
        - Output: List of blurred images, same shape and dtype
        - Uses torchvision for batched, GPU-accelerated Gaussian blur
    """

    def __init__(self, noisename: str = "GaussianBlur"):
        """
        Initializes the Gaussian blur attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename, factor_inversely_related=False)  # Higher sigma = stronger blur

    @torch.inference_mode()
    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, sigma: float = 1.0) -> List[
        ndarray]:
        """
        Applies Gaussian blur to a batch of stego images using torchvision's batched implementation.

        The pipeline:
            1. Stack images into a 4D numpy array [B, H, W, 3]
            2. Convert to float32 and normalize to [0,1]
            3. Convert to CHW tensor and move to device
            4. Apply batched Gaussian blur using torchvision
            5. Convert back to HWC uint8

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each [H, W, 3], dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored).
            sigma (float): Standard deviation of the Gaussian kernel, controls blur strength.

        Returns:
            List[ndarray]: Batch of blurred images, each with the same shape and dtype as input.
        """
        if not stego_imgs:
            return []

        batch_np = np.stack(stego_imgs, axis=0).astype(np.float32)  # [B, H, W, 3]
        is_color = batch_np.ndim == 4

        if batch_np.ndim == 3:
            batch_np = np.expand_dims(batch_np, axis=-1)

        # Normalize to [0,1]
        batch_np = batch_np / 255.0

        # Convert to tensor: HWC -> CHW -> [B, C, H, W]
        batch_tensor = torch.from_numpy(batch_np).permute(0, 3, 1, 2)

        # Apply batched Gaussian blur
        gaussianblur = transforms.GaussianBlur(kernel_size=int(6 * sigma + 1) // 2 * 2 + 1, sigma=sigma)
        blurred_tensor = gaussianblur(batch_tensor)

        # Convert back to numpy: CHW -> HWC
        blurred_np = (
                blurred_tensor.permute(0, 2, 3, 1).cpu().numpy() * 255.0
        ).astype(np.uint8)  # [B, H, W, 3]

        noised_imgs = []
        for i in range(blurred_np.shape[0]):
            if is_color:
                noised_img = blurred_np[i]
            else:
                noised_img = blurred_np[i][:, :, 0]
            noised_imgs.append(noised_img)
        # Convert back to list of arrays
        return noised_imgs


class MedianFilter(BaseTestAttackModel):
    """
    Applies a median filter to the input image to reduce noise and smooth details.

    Args:
        noisename (str): Name identifier for the model, defaults to "MedianFilter".
    """

    def __init__(self, noisename: str = "MedianFilter"):
        super().__init__(noisename)

    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, kernel_size: int = 3) -> List[ndarray]:
        """
        Applies a median filter to the input image to smooth details and reduce noise.

        Args:
            stego_imgs (ndarray): Input image in RGB format, uint8 [H, W, 3] [0,255].
            cover_img (ndarray, optional): Not used.
            kernel_size (int): Size of the median filter kernel (must be odd and > 1).

        Returns:
            ndarray: Filtered image, same shape and dtype as input.
        """
        noise_imgs = []
        for stego in stego_imgs:
            result_img = cv2.medianBlur(np.uint8(np.clip(stego, 0., 255.)), kernel_size)
            noise_imgs.append(result_img)
        return noise_imgs


class MeanFilter(BaseTestAttackModel):
    """
    Applies a mean (average) filter to the input image to smooth details.

    Args:
        noisename (str): Name identifier for the model, defaults to "MeanFilter".
    """

    def __init__(self, noisename: str = "MeanFilter"):
        super().__init__(noisename)

    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, kernel_size: int = 5) -> List[ndarray]:
        """
        Applies a mean filter to the input image to smooth details.

        Args:
            stego_imgs (ndarray): Input image in RGB format, uint8 [H, W, 3] [0,255].
            cover_img (ndarray, optional): Not used.
            kernel_size (int): Size of the mean filter kernel (must be odd).

        Returns:
            ndarray: Filtered image, same shape and dtype as input.
        """
        noised_imgs = []
        for stego in stego_imgs:
            kernel = np.ones((kernel_size, kernel_size), np.float32) / (kernel_size * kernel_size)
            filtered_img = cv2.filter2D(stego.astype(np.uint8), -1, kernel)
            noised_imgs.append(filtered_img)
        return noised_imgs


class Crop(BaseTestAttackModel):
    """
    A spatial attack that simulates partial occlusion or inpainting by cropping a central region
    and filling the rest based on a specified mode.

    This attack removes peripheral information and can disrupt watermark signals embedded
    in image borders or relying on global context.

    The 'factor' parameter controls the area ratio of the kept region:
        - 1.0: No change (entire image kept)
        - <1.0: A central sub-region is preserved, rest is filled

    Supported fill modes:
        - 'constant_replace': Fill with a constant color (e.g., black)
        - 'cover_replace': Fill with the corresponding region from the original cover image

    Note:
        - Input: List of uint8 RGB images [H, W, 3], range [0, 255]
        - Output: List of modified images, same shape and dtype
        - For 'cover_replace', `cover_img` must be provided and at least as large as `stego_imgs`
    """

    def __init__(self, noisename: str = "Crop", mode: str = "constant_replace", constant: int = 0):
        """
        Initializes the crop attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
            mode (str): Fill strategy: 'constant_replace' or 'cover_replace'.
            constant (int): Pixel value (0-1) for 'constant_replace' mode. Default is 0 (black).

        Raises:
            ValueError: If mode is not supported.
        """
        super().__init__(noisename=noisename,
                         factor_inversely_related=True)  # Higher factor = less cropping = weaker attack
        if mode not in ["constant_replace", "cover_replace"]:
            raise ValueError(f"Invalid mode: {mode}. Choose from 'constant_replace', 'cover_replace'.")
        self.mode = mode
        self.constant = constant

    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: float = 0.7) -> List[
        ndarray]:
        """
        Applies crop-and-fill distortion to a batch of stego images.

        For each image:
            1. Calculates the size of the central region to keep based on 'factor'.
            2. Computes the top-left coordinate for a random or center-aligned crop.
            3. Fills the background based on the selected mode.
            4. Places the kept region onto the filled background.

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each [H, W, 3], dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images for 'cover_replace' mode.
            factor (float): Ratio of kept area to original area (0.01, 1.0].

        Returns:
            List[ndarray]: Batch of modified images, each with the same shape and dtype as input.
        """
        if not stego_imgs:
            return []

        # Clip factor to valid range
        factor = np.clip(factor, 0.01, 1.0)

        noised_batch = []
        for i, img in enumerate(stego_imgs):
            h, w = img.shape[:2]

            # Calculate crop dimensions to preserve aspect ratio
            area_to_keep = factor * h * w
            aspect_ratio = w / h
            crop_h = int(np.sqrt(area_to_keep / aspect_ratio))
            crop_w = int(crop_h * aspect_ratio)
            crop_h = max(1, min(crop_h, h))
            crop_w = max(1, min(crop_w, w))

            # Center the crop (you can modify to random placement if needed)
            y = (h - crop_h) // 2
            x = (w - crop_w) // 2

            # Initialize output image
            if self.mode == "constant_replace":
                noised_img = np.full_like(img, int(self.constant * 255), dtype=np.uint8)
            elif self.mode == "cover_replace":
                if cover_img is None or len(cover_img) <= i:
                    raise ValueError("cover_img must be provided for 'cover_replace' mode.")
                cover = cover_img[i].astype(np.uint8)
                if cover.shape[0] < h or cover.shape[1] < w:
                    raise ValueError("cover_img must be at least as large as stego_imgs.")
                noised_img = cover[:h, :w].copy()
            else:
                raise ValueError(f"Unsupported mode: {self.mode}")

            # Paste the cropped region
            noised_img[y:y + crop_h, x:x + crop_w] = img[y:y + crop_h, x:x + crop_w]

            noised_batch.append(noised_img)

        return noised_batch


class RegionZoom(BaseTestAttackModel):
    """
    A spatial attack that simulates digital zoom by cropping a random sub-region and resizing it to full resolution.

    This attack removes peripheral information and enlarges a central portion, potentially disrupting
    watermark signals embedded in image borders or relying on global structure.

    The 'factor' parameter controls the relative area of the cropped region:
        - 1.0: Crop covers almost the entire image (minimal zoom, weakest attack)
        - <1.0: Smaller region is cropped and upscaled (stronger zoom, stronger attack)

    The aspect ratio of the original image is preserved in the cropped region.

    Note:
        - Input: List of uint8 RGB images [H, W, 3], range [0, 255]
        - Output: List of zoomed images, same shape and dtype
        - Uses bilinear interpolation for resizing
    """

    def __init__(self, noisename: str = "RegionZoom"):
        """
        Initializes the region zoom attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename, factor_inversely_related=True)  # Smaller factor = stronger zoom

    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: float = 0.7) -> List[ndarray]:
        """
        Applies region zoom (crop + resize) distortion to a batch of stego images.

        For each image:
            1. Calculate the size of a sub-region to crop, based on 'factor' and aspect ratio.
            2. Randomly determine the top-left position of the crop.
            3. Crop the image to the sub-region.
            4. Resize the cropped region back to the original dimensions using bilinear interpolation.

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each [H, W, 3], dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored, for interface compatibility).
            factor (float): Ratio of the cropped area to the original image area, range (0.01, 1.0].

        Returns:
            List[ndarray]: Batch of zoomed images, each with the same shape and dtype as input.
        """
        if not stego_imgs:
            return []

        # Clip factor to valid range
        factor = np.clip(factor, 0.01, 1.0)

        noised_batch = []
        for img in stego_imgs:
            h, w = img.shape[:2]

            # Calculate crop dimensions to preserve aspect ratio
            area_to_crop = factor * h * w
            aspect_ratio = w / h
            crop_h = int(np.sqrt(area_to_crop / aspect_ratio))
            crop_w = int(crop_h * aspect_ratio)
            crop_h = max(1, min(crop_h, h))
            crop_w = max(1, min(crop_w, w))

            # Random placement of the crop
            x = random.randint(0, w - crop_w)
            y = random.randint(0, h - crop_h)

            # Crop the region
            cropped = img[y:y + crop_h, x:x + crop_w]

            # Resize back to original size
            zoomed = cv2.resize(cropped.astype(np.uint8), (w, h), interpolation=cv2.INTER_LINEAR)

            noised_batch.append(zoomed)

        return noised_batch


class Cropout(BaseTestAttackModel):
    """
    A localized occlusion attack that removes a rectangular region from the image and replaces it.

    This attack simulates partial damage, editing, or object removal, which can disrupt watermark signals
    embedded in specific spatial regions. It is particularly effective against spatial-domain watermarking.

    The 'factor' parameter controls the proportion of the image area to be removed:
        - 0.0: No region removed (identity)
        - 0.3: 30% of the area is removed and replaced
        - 1.0: Entire image is replaced

    Supported replacement modes:
        - 'constant_replace': Fill with a constant color (e.g., black)
        - 'cover_replace': Fill with the corresponding region from the original cover image

    Note:
        - Input: List of uint8 images [H, W] (grayscale) or [H, W, 3] (RGB), range [0, 255]
        - Output: List of modified images, same shape and dtype as input
        - For 'cover_replace', `cover_img` must be provided and at least as large as `stego_img`
    """

    def __init__(self, noisename: str = "Cropout", constant: int = 0, mode: str = "constant_replace"):
        """
        Initializes the cropout attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
            constant (int): Pixel value (0-1) for 'constant_replace' mode. Default is 0 (black).
            mode (str): Replacement strategy: 'constant_replace' or 'cover_replace'.

        Raises:
            AssertionError: If mode is not supported.
        """
        super().__init__(noisename=noisename, factor_inversely_related=True)
        assert mode in ["constant_replace", "cover_replace"], "Mode must be 'constant_replace' or 'cover_replace'"
        self.constant = constant * 255.0
        self.mode = mode

    def _random_rectangle_mask(self, h: int, w: int, crop_ratio: float) -> ndarray:
        """
        Generates a binary mask with a random rectangular region marked for removal.

        Args:
            h (int): Image height.
            w (int): Image width.
            crop_ratio (float): Proportion of the image area to remove [0.0, 1.0].

        Returns:
            ndarray: Binary mask of shape [H, W], dtype float32. 1 = keep, 0 = remove.
        """
        if crop_ratio >= 1.0:
            return np.zeros((h, w), dtype=np.float32)
        if crop_ratio <= 0.0:
            return np.ones((h, w), dtype=np.float32)

        remain_ratio = 1.0 - crop_ratio
        total_keep = h * w * remain_ratio
        aspect_ratio = w / h
        keep_h = int(np.sqrt(total_keep / aspect_ratio))
        keep_w = int(keep_h * aspect_ratio)
        keep_h = max(1, min(keep_h, h))
        keep_w = max(1, min(keep_w, w))

        x = random.randint(0, w - keep_w)
        y = random.randint(0, h - keep_h)

        mask = np.ones((h, w), dtype=np.float32)
        mask[y:y + keep_h, x:x + keep_w] = 0.0
        return mask

    def attack(self, stego_img: List[ndarray], cover_img: List[ndarray] = None, factor: float = 0.3) -> List[
        ndarray]:
        """
        Applies the cropout attack to a batch of stego images.

        For each image:
            1. Generates a random rectangular mask indicating which region to remove.
            2. Replaces the masked region with either a constant value or the cover image content.
            3. Preserves the rest of the image.

        Args:
            stego_img (List[ndarray]): Batch of watermarked images, each [H, W] or [H, W, 3], dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images for 'cover_replace' mode.
            factor (float): Proportion of the image area to remove, range [0.0, 1.0].

        Returns:
            List[ndarray]: Batch of modified images, each with the same shape and dtype as input.
        """
        if not stego_img:
            return []

        factor = np.clip(factor, 0.0, 1.0).item()
        noised_batch = []

        for i, img in enumerate(stego_img):
            h, w = img.shape[:2]
            is_grayscale = len(img.shape) == 2
            c = 1 if is_grayscale else img.shape[2]

            mask = self._random_rectangle_mask(h, w, crop_ratio=factor)
            mask_3d = np.repeat(mask[:, :, np.newaxis], c, axis=2)

            if self.mode == "constant_replace":
                fill_value = self.constant if is_grayscale else [self.constant] * c
                replace_value = np.full((h, w, c), fill_value, dtype=np.float32)
            elif self.mode == "cover_replace":
                if cover_img is None or len(cover_img) <= i:
                    raise ValueError("cover_img must be provided for 'cover_replace' mode.")
                cover = cover_img[i].astype(np.float32)
                if cover.shape[0] < h or cover.shape[1] < w:
                    raise ValueError("cover_img must be at least as large as stego_img.")
                replace_value = cover[:h, :w] if is_grayscale else cover[:h, :w, :]
            else:
                raise ValueError(f"Unsupported mode: {self.mode}")

            img_float = img.astype(np.float32)
            if is_grayscale:
                noised_float = img_float * mask_3d[:, :, 0] + replace_value[:, :, 0] * (1 - mask_3d[:, :, 0])
            else:
                noised_float = img_float * mask_3d + replace_value * (1 - mask_3d)
            noised_uint8 = np.clip(noised_float, 0, 255).astype(np.uint8)
            noised_batch.append(noised_uint8)

        return noised_batch


class TranslationAttack(BaseTestAttackModel):
    """
    A simplified translation attack using OpenCV's warpAffine for accurate translation.

    - Only one parameter: `percent` (e.g., 0.1 means up to 10% of width/height).
    - The actual shift magnitude is controlled by the input `factor` (0.0 ~ 1.0).
    - Supports both grayscale (H, W) and color (H, W, C) images.
    - Padding is always zero-filled (borderValue=(0,0,0)).
    """

    def __init__(
        self,
        noisename: str = "TranslationAttack"
    ):
        """
        Args:
            noisename (str): Name for logging. Defaults to "TranslationAttack".
        """
        super().__init__(noisename=noisename, factor_inversely_related=False)

    def attack(
        self,
        stego_imgs: List[ndarray],
        cover_img: Optional[List[ndarray]] = None,
        factor: Optional[float] = 0.1
    ) -> List[ndarray]:
        """
        Apply random translation with magnitude controlled by `factor`.

        Final shift = factor * image_dimension.
        If factor is None, it defaults to 1.0 (i.e., full intensity).

        Args:
            stego_imgs: List of images, each (H, W) or (H, W, C).
            cover_img: Ignored.
            factor: Float in [0, 1]. If None, treated as 1.0.

        Returns:
            List of translated images with same shapes and dtypes.
        """
        if factor is None:
            factor = 1.0
        if not (0.0 <= factor <= 1.0):
            raise ValueError("factor must be in [0, 1]")

        if factor == 0.0:
            return [img.copy() for img in stego_imgs]

        eff_factor = max(0.0, min(1.0, factor))

        attacked = []
        for img in stego_imgs:
            H, W = img.shape[:2]

            # Calculate shifts
            h_shift = int(np.round(eff_factor * W)) * np.random.choice([-1, 1])
            v_shift = int(np.round(eff_factor * H)) * np.random.choice([-1, 1])

            # Force at least 1 pixel if eff_factor > 0 and shift was rounded to 0
            if h_shift == 0 and eff_factor > 0:
                h_shift = np.random.choice([-1, 1])
            if v_shift == 0 and eff_factor > 0:
                v_shift = np.random.choice([-1, 1])

            # Create translation matrix: [[1, 0, dx], [0, 1, dy]]
            M = np.float32([[1, 0, h_shift], [0, 1, v_shift]])

            # Apply translation using warpAffine
            if len(img.shape) == 2:  # grayscale
                translated = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            else:  # color (H, W, C)
                translated = cv2.warpAffine(
                    img,
                    M,
                    (W, H),  # (width, height)
                    flags=cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_CONSTANT,
                    borderValue=(0, 0, 0)
                )

            attacked.append(translated.astype(img.dtype))

        return attacked


class PixelDropout(BaseTestAttackModel):
    """
    A pixel-level occlusion attack that randomly drops (replaces) pixels to simulate data loss or noise.

    This attack sets a random subset of pixels to a replacement value, disrupting local texture and
    high-frequency information where many watermark signals are embedded.

    The 'factor' parameter controls the dropout probability:
        - 0.0: No pixels dropped (identity)
        - 0.1: 10% of pixels replaced
        - 1.0: All pixels replaced (complete destruction)

    Supported replacement modes:
        - 'constant_replace': Replace with a constant color (e.g., black)
        - 'cover_replace': Replace with the corresponding pixel from the original cover image

    Note:
        - Input: List of uint8 RGB images [H, W, 3], range [0, 255]
        - Output: List of modified images, same shape and dtype
        - For 'cover_replace', `cover_img` must be provided and at least as large as `stego_img`
    """

    def __init__(self, noisename: str = "PixelDropout", mode: str = "constant_replace", constant: int = 0):
        """
        Initializes the pixel dropout attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
            mode (str): Replacement strategy: 'constant_replace' or 'cover_replace'.
            constant (int): Pixel value (0-1) for 'constant_replace' mode. Default is 0 (black).

        Raises:
            AssertionError: If mode is not supported.
        """
        super().__init__(noisename=noisename,
                         factor_inversely_related=False)  # Higher factor = more dropout = stronger attack
        assert mode in ["constant_replace",
                        "cover_replace"], f"Invalid mode: {mode}. Choose from 'constant_replace', 'cover_replace'."
        self.mode = mode
        self.constant = constant

    def attack(self, stego_img: List[ndarray], cover_img: List[ndarray] = None, factor: float = 0.1) -> List[
        ndarray]:
        """
        Applies pixel dropout to a batch of stego images.

        For each image:
            1. Generates a random binary mask based on the dropout probability ('factor').
            2. Keeps pixels where mask is True.
            3. Replaces pixels where mask is False with either a constant value or the cover image content.

        Args:
            stego_img (List[ndarray]): Batch of watermarked images, each [H, W, 3], dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images for 'cover_replace' mode.
            factor (float): Probability of dropping a pixel, range [0.0, 1.0].

        Returns:
            List[ndarray]: Batch of images with pixel dropout applied, each with the same shape and dtype as input.
        """
        if not stego_img:
            return []

        drop_prob = np.clip(factor, 0.0, 1.0)
        if drop_prob == 0.0:
            return [img.copy() for img in stego_img]

        noised_batch = []
        for i, img in enumerate(stego_img):
            img_uint8 = img.astype(np.uint8)
            h, w = img_uint8.shape[:2]
            is_grayimage = img_uint8.ndim == 2

            # Generate random dropout mask: True = keep, False = drop
            if is_grayimage:
                keep_mask = np.random.rand(h, w) > drop_prob  # [H, W, C]
            else:
                keep_mask = np.random.rand(h, w, img_uint8.shape[2]) > drop_prob  # [H, W, C]

            # Determine replacement value
            if self.mode == "constant_replace" or cover_img is None or len(cover_img) <= i:
                replace_value = np.full_like(img_uint8, self.constant * 255, dtype=np.uint8)
            elif self.mode == "cover_replace":
                cover = cover_img[i].astype(np.uint8)
                if cover.shape[0] < h or cover.shape[1] < w:
                    raise ValueError("cover_img must be at least as large as stego_img.")
                replace_value = cover[:h, :w]
            else:
                raise ValueError(f"Unsupported mode: {self.mode}")

            # Apply dropout: keep original where mask is True, else use replacement
            noised_img = np.where(keep_mask, img_uint8, replace_value)
            noised_batch.append(noised_img)

        return noised_batch


class GaussianNoise(BaseTestAttackModel):
    """
    A noise attack that adds zero-mean Gaussian noise to the input image.

    This attack simulates random pixel perturbations caused by electronic sensor noise or transmission errors.
    It is a fundamental test for watermark robustness under random signal degradation.

    The 'std' parameter controls the standard deviation of the noise:
        - 0.0: No noise (identity)
        - 0.05: Low noise (barely perceptible)
        - 0.15: Medium noise (clearly visible)
        - >0.2: High noise (severe degradation)

    The noise is scaled to the [0, 255] range before addition.

    Reference:
        Foi, A., Trimeche, M., Katkovnik, V., & Egiazarian, K. (2008).
        Practical Poissonian-Gaussian noise modeling and denoising based on precise noise parameter estimation.
        IEEE Transactions on Image Processing, 17(6), 10.1109/TIP.2008.921849

    Note:
        - Input: List of uint8 RGB images [H, W, 3], range [0, 255]
        - Output: List of noisy images, same shape and dtype
        - The noise is generated independently for each image in the batch
    """

    def __init__(self, mu: float = 0.0, noisename: str = "GaussianNoise"):
        """
        Initializes the Gaussian noise attack.

        Args:
            mu (float): Mean of the Gaussian distribution. Default is 0.0.
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename,
                         factor_inversely_related=False)  # Higher std = more noise = stronger attack
        self.mu = mu

    def attack(self, stego_img: List[ndarray], cover_img: List[ndarray] = None, std: float = 1.5) -> List[
        ndarray]:
        """
        Applies Gaussian noise to a batch of stego images using vectorized operations.

        The noise model is:
            noised_img = clip( stego_img + N(mu, std) * 255, 0, 255 )

        Args:
            stego_img (List[ndarray]): Batch of watermarked images, each [H, W, 3], dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored, for interface compatibility).
            std (float): Standard deviation of the Gaussian noise, relative to [0,1] range.

        Returns:
            List[ndarray]: Batch of noisy images, each with the same shape and dtype as input.
        """
        if not stego_img:
            return []

        # Stack all images into a single 4D array
        batch_np = np.stack(stego_img, axis=0).astype(np.float32)  # [B, H, W, 3]

        # Generate Gaussian noise: scale std from [0,1] to [0,255]
        noise = np.random.normal(self.mu, std * 255.0, batch_np.shape)

        # Add noise and clip
        noised_batch = batch_np + noise
        noised_batch = np.clip(noised_batch, 0, 255).astype(np.uint8)

        # Convert back to list of arrays
        return [noised_batch[i] for i in range(noised_batch.shape[0])]


class SaltPepperNoise(BaseTestAttackModel):
    """
    A non-linear noise attack that simulates salt-and-pepper noise by randomly setting pixels to extreme values.

    This attack models severe pixel corruption, such as that caused by faulty sensors, bit errors,
    or transmission faults. It flips a random subset of pixels to either the minimum (0, "pepper")
    or maximum (255, "salt") intensity value.

    The 'noise_ratio' parameter controls the proportion of pixels affected:
        - 0.0: No noise (identity)
        - 0.1: 10% of pixels are corrupted (5% salt, 5% pepper)
        - 1.0: All pixels are set to either 0 or 255 (complete destruction)

    The attack is applied independently to each image in the batch and supports both grayscale
    and color images by checking the input dimensionality.

    Reference:
        González, R. C., & Woods, R. E. (2008). Digital Image Processing (3rd ed.). Prentice Hall.

    Note:
        - Input: List of uint8 images, either [H, W] (grayscale) or [H, W, 3] (RGB), range [0, 255]
        - Output: List of noisy images, same shape and dtype
        - The noise is distributed equally between salt (255) and pepper (0) pixels
    """

    def __init__(self, noisename: str = "SaltPepperNoise"):
        """
        Initializes the salt-and-pepper noise attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename,
                         factor_inversely_related=False)  # Higher ratio = more noise = stronger attack

    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, noise_ratio: float = 0.1) -> \
            List[ndarray]:
        """
        Applies salt-and-pepper noise to a batch of stego images.

        For each image:
            1. Creates a copy of the input image.
            2. Generates a random noise mask over the spatial dimensions.
            3. Sets pixels below `noise_ratio/2` to 255 ("salt").
            4. Sets pixels between `noise_ratio/2` and `noise_ratio` to 0 ("pepper").
            5. Preserves the remaining pixels.

        The method handles both grayscale and color images:
            - Grayscale: shape [H, W], scalar assignment
            - Color: shape [H, W, 3], vector assignment

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each [H, W] or [H, W, 3], dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored, for interface compatibility).
            noise_ratio (float): Proportion of pixels to corrupt, range [0.0, 1.0].

        Returns:
            List[ndarray]: Batch of noisy images, each with the same shape and dtype as input.
        """
        noised_imgs = []
        noise_ratio = np.clip(noise_ratio, 0.0, 1.0)
        if noise_ratio == 0.0:
            return [img.copy() for img in stego_imgs]

        for stego_img in stego_imgs:
            noisy_image = np.copy(stego_img)
            is_color = len(stego_img.shape) == 3

            # Generate noise mask on spatial dimensions only
            mask_shape = stego_img.shape[:2] if is_color else stego_img.shape
            noise_mask = np.random.random(mask_shape)

            # Apply salt (255)
            if is_color:
                noisy_image[noise_mask < noise_ratio / 2] = [255, 255, 255]
            else:
                noisy_image[noise_mask < noise_ratio / 2] = 255

            # Apply pepper (0)
            pepper_condition = (noise_mask >= noise_ratio / 2) & (noise_mask < noise_ratio)
            if is_color:
                noisy_image[pepper_condition] = [0, 0, 0]
            else:
                noisy_image[pepper_condition] = 0

            noised_imgs.append(noisy_image.astype(np.uint8))

        return noised_imgs


class HueShiftAttack(BaseTestAttackModel):
    """
    A color transformation attack that shifts the hue of an image in the HSV color space.

    This attack modifies the perceived color of the image by rotating the hue channel,
    which can disrupt watermark signals that rely on specific color distributions or
    chrominance components.

    The 'factor' parameter controls the degree of hue shift in degrees:
        - 0.0: No change (identity)
        - 30.0: Moderate color shift (e.g., red → orange)
        - 180.0: Maximum shift (complementary colors)

    The hue is cyclic modulo 180 (OpenCV convention), so shifts wrap around.

    Reference:
        Smith, A. R. (1978). Color gamut transform pairs.
        In Proceedings of the 5th annual conference on Computer graphics and interactive techniques (SIGGRAPH '78).

    Note:
        - Input: List of uint8 images, each [H, W] (grayscale) or [H, W, 3] (RGB), range [0, 255]
        - Output: List of hue-shifted images, same shape and dtype
        - For grayscale images, the single channel is replicated to three channels for HSV processing,
          and the output is converted back to grayscale by taking one channel
        - For RGB images, the attack shifts the hue channel in HSV space
        - Uses OpenCV's HSV representation (H: 0–180, S: 0–255, V: 0–255)
        - Supports batch processing for efficiency
    """

    def __init__(self, noisename: str = "Hue"):
        """
        Initializes the hue shift attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename, factor_inversely_related=False)  # Higher factor = stronger shift

    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: float = 30.0) -> List[ndarray]:
        """
        Applies hue shift to a batch of images (grayscale or RGB) in HSV color space.

        For RGB images:
            1. Converts from RGB to HSV.
            2. Adds the shift value to the H channel, modulo 180.
            3. Converts back to RGB.
        For grayscale images:
            1. Replicates the single channel to three channels to create a pseudo-RGB image.
            2. Applies the hue shift in HSV space.
            3. Converts back to grayscale by taking one channel.

        This operation preserves luminance and saturation while altering color appearance for RGB images.
        For grayscale images, the effect may be limited due to the lack of initial color information.

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each [H, W] (grayscale) or [H, W, 3] (RGB),
                                       dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored, for interface compatibility).
            factor (float): Hue shift amount in degrees, range [0, 180].

        Returns:
            List[ndarray]: Batch of hue-shifted images, each with the same shape and dtype as input.
        """
        if not stego_imgs:
            return []

        # Clip and wrap factor
        shift = float(factor) % 180.0
        noised_imgs = []
        for stego in stego_imgs:
            is_gray = stego.ndim == 2
            if is_gray:
                stego = np.stack([stego, stego, stego], axis=-1).astype(np.uint8)
            hsv = cv2.cvtColor(stego.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
            hsv[..., 0] = (hsv[..., 0] + shift) % 180.0
            hsv_uint8 = hsv.astype(np.uint8)
            rgb = cv2.cvtColor(hsv_uint8, cv2.COLOR_HSV2RGB)
            if is_gray:
                rgb = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            noised_imgs.append(rgb)
        return noised_imgs



class DesaturateAttack(BaseTestAttackModel):
    """
    A color degradation attack that reduces image saturation by scaling the S (saturation) channel in HSV space.

    This attack weakens color-based watermark signals by making the image appear more grayscale.
    It simulates poor display conditions or intentional color suppression.

    The 'factor' parameter controls the saturation level:
        - 1.0: No change (full color)
        - 0.0: Complete desaturation (grayscale)
        - Values in between: Partial desaturation

    Reference:
        Smith, A. R. (1978). Color gamut transform pairs.
        In Proceedings of the 5th annual conference on Computer graphics and interactive techniques (SIGGRAPH '78).

    Note:
        - Input: List of uint8 images, each [H, W] (grayscale) or [H, W, 3] (RGB), range [0, 255]
        - Output: List of desaturated images, same shape and dtype
        - For grayscale images, the single channel is replicated to three channels for HSV processing,
          and the output is converted back to grayscale by taking one channel
        - For RGB images, the attack scales the S channel in HSV space
        - Uses OpenCV's HSV representation (S ∈ [0, 255])
        - Desaturation has minimal effect on grayscale images due to their lack of color information
    """

    def __init__(self, noisename: str = "Desaturate"):
        """
        Initializes the desaturation attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename, factor_inversely_related=True)  # Higher factor = less desaturation

    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: float = 0.5) -> List[ndarray]:
        """
        Applies desaturation to a batch of images (grayscale or RGB) using HSV color space transformation.

        For RGB images:
            1. Converts RGB to HSV.
            2. Scales the saturation channel (S) by 'factor'.
            3. Clips to valid range [0, 255].
            4. Converts back to RGB.
        For grayscale images:
            1. Replicates the single channel to three channels to create a pseudo-RGB image.
            2. Applies desaturation in HSV space by scaling the S channel.
            3. Converts back to grayscale by taking one channel.

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each [H, W] (grayscale) or [H, W, 3] (RGB),
                                       dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored, for interface compatibility).
            factor (float): Saturation scaling factor in [0.0, 1.0].
                           1.0 = no change, 0.0 = grayscale.

        Returns:
            List[ndarray]: Batch of desaturated images, each with the same shape and dtype as input.
        """
        if not stego_imgs:
            return []

        # Clip factor to valid range
        noised_imgs = []
        factor = np.clip(factor, 0., 1.)
        for stego in stego_imgs:
            is_gray = stego.ndim == 2
            if is_gray:
                stego = np.stack([stego, stego, stego], axis=-1).astype(np.uint8)
            hsv = cv2.cvtColor(stego.astype(np.uint8), cv2.COLOR_RGB2HSV)
            hsv = hsv.astype(np.float32)
            hsv[..., 1] = np.clip(hsv[..., 1] * factor, 0, 255)
            hsv = hsv.astype(np.uint8)
            rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
            if is_gray:
                rgb = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            noised_imgs.append(rgb)
        return noised_imgs




class OversaturateAttack(BaseTestAttackModel):
    """
    A color enhancement attack that increases image saturation by amplifying the S (saturation) channel in HSV space.

    This attack pushes colors towards their most vivid state, potentially causing clipping and color distortion.
    It can disrupt watermark signals that rely on subtle color variations or are sensitive to chrominance changes.

    The 'factor' parameter controls the amplification level:
        - 1.0: No change (identity)
        - >1.0: Increased saturation (e.g., 1.5, 2.0, 3.0)

    Reference:
        Smith, A. R. (1978). Color gamut transform pairs.
        In Proceedings of the 5th annual conference on Computer graphics and interactive techniques (SIGGRAPH '78).

    Note:
        - Input: List of uint8 images, each [H, W] (grayscale) or [H, W, 3] (RGB), range [0, 255]
        - Output: List of oversaturated images, same shape and dtype
        - For grayscale images, the single channel is replicated to three channels for HSV processing,
          and the output is converted back to grayscale by taking one channel
        - For RGB images, the attack scales the S channel in HSV space
        - Uses OpenCV's HSV representation (S ∈ [0, 255])
        - Oversaturation has minimal effect on grayscale images due to their lack of color information
    """

    def __init__(self, noisename: str = "Oversaturate"):
        """
        Initializes the oversaturation attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename, factor_inversely_related=False)  # Higher factor = stronger oversaturation

    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: float = 2.0) -> List[ndarray]:
        """
        Applies oversaturation to a batch of images (grayscale or RGB) using HSV color space transformation.

        For RGB images:
            1. Converts RGB to HSV.
            2. Scales the saturation channel (S) by 'factor'.
            3. Clips the result to the valid range [0, 255].
            4. Converts back to RGB.
        For grayscale images:
            1. Replicates the single channel to three channels to create a pseudo-RGB image.
            2. Applies oversaturation in HSV space by scaling the S channel.
            3. Converts back to grayscale by taking one channel.

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each [H, W] (grayscale) or [H, W, 3] (RGB),
                                       dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored, for interface compatibility).
            factor (float): Saturation amplification factor, typically >= 1.0.
                           1.0 = no change, higher values = stronger saturation.

        Returns:
            List[ndarray]: Batch of oversaturated images, each with the same shape and dtype as input.
        """
        if not stego_imgs:
            return []

        noised_imgs = []
        factor = max(1.0, float(factor))
        for stego in stego_imgs:
            is_gray = stego.ndim == 2
            if is_gray:
                stego = np.stack([stego, stego, stego], axis=-1).astype(np.uint8)
            hsv = cv2.cvtColor(stego.astype(np.uint8), cv2.COLOR_RGB2HSV)
            hsv = hsv.astype(np.float32)
            hsv[..., 1] = np.clip(hsv[..., 1] * factor, 0, 255)
            hsv = hsv.astype(np.uint8)
            rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
            if is_gray:
                rgb = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            noised_imgs.append(rgb)
        return noised_imgs


class DarkenAttack(BaseTestAttackModel):
    """
    A brightness reduction attack that darkens the image by scaling the V (value) channel in HSV color space.

    This attack simulates low-light conditions or display dimming, which can degrade watermark signals
    embedded in darker regions of the image. It preserves hue and saturation while reducing overall luminance.

    The 'factor' parameter controls the brightness level:
        - 1.0: No change (identity)
        - 0.0: Completely black (maximum attack strength)
        - Values in between: Proportional darkening

    Reference:
        Smith, A. R. (1978). Color gamut transform pairs.
        In Proceedings of the 5th annual conference on Computer graphics and interactive techniques (SIGGRAPH '78).

    Note:
        - Input: List of uint8 images, each [H, W] (grayscale) or [H, W, 3] (RGB), range [0, 255]
        - Output: List of darkened images, same shape and dtype
        - For grayscale images, the single channel is replicated to three channels for HSV processing,
          and the output is converted back to grayscale by taking one channel
        - For RGB images, the attack scales the V channel in HSV space
        - Uses OpenCV's HSV representation (V ∈ [0, 255])
    """

    def __init__(self, noisename: str = "Darken"):
        """
        Initializes the darken attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename, factor_inversely_related=True)  # Higher factor = less darkening

    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: float = 0.7) -> List[ndarray]:
        """
        Applies a darkening effect to a batch of images (grayscale or RGB) using HSV color space transformation.

        For RGB images:
            1. Converts RGB to HSV.
            2. Scales the value channel (V) by 'factor'.
            3. Clips the result to the valid range [0, 255].
            4. Converts back to RGB.
        For grayscale images:
            1. Replicates the single channel to three channels to create a pseudo-RGB image.
            2. Applies the darkening in HSV space by scaling the V channel.
            3. Converts back to grayscale by taking one channel.

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each [H, W] (grayscale) or [H, W, 3] (RGB),
                                       dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored, for interface compatibility).
            factor (float): Brightness scaling factor in [0.0, 1.0].
                           1.0 = no change, 0.0 = completely black.

        Returns:
            List[ndarray]: Batch of darkened images, each with the same shape and dtype as input.
        """
        if not stego_imgs:
            return []

        # Clip factor to valid range
        factor = np.clip(factor, 0.0, 1.0)
        noised_imgs = []
        for stego in stego_imgs:
            is_gray = stego.ndim == 2
            if is_gray:
                stego = np.stack([stego, stego, stego], axis=-1).astype(np.uint8)
            hsv = cv2.cvtColor(stego.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
            hsv[..., 2] = np.clip(hsv[..., 2] * factor, 0, 255)
            hsv_uint8 = hsv.astype(np.uint8)
            rgb = cv2.cvtColor(hsv_uint8, cv2.COLOR_HSV2RGB)
            if is_gray:
                rgb = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            noised_imgs.append(rgb)
        return noised_imgs


class BrightenAttack(BaseTestAttackModel):
    """
    A brightness enhancement attack that increases image luminance by amplifying the V (value) channel in HSV color space.

    This attack simulates overexposure or display brightening, which can wash out subtle details and degrade watermark signals
    embedded in mid-to-dark tone regions. It preserves hue and saturation while increasing overall brightness.

    The 'factor' parameter controls the amplification level:
        - 1.0: No change (identity)
        - >1.0: Increased brightness (e.g., 1.5, 2.0)
        - Values are clipped to the valid range [0, 255] to prevent overflow

    Reference:
        Smith, A. R. (1978). Color gamut transform pairs.
        In Proceedings of the 5th annual conference on Computer graphics and interactive techniques (SIGGRAPH '78).

    Note:
        - Input: List of uint8 images, each [H, W] (grayscale) or [H, W, 3] (RGB), range [0, 255]
        - Output: List of brightened images, same shape and dtype
        - For grayscale images, the single channel is replicated to three channels for HSV processing,
          and the output is converted back to grayscale by taking one channel
        - For RGB images, the attack scales the V channel in HSV space
        - Uses OpenCV's HSV representation (V ∈ [0, 255])
    """

    def __init__(self, noisename: str = "Brighten"):
        """
        Initializes the brighten attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename, factor_inversely_related=False)  # Higher factor = stronger brightening

    def attack(self, stego_imgs: List[ndarray], cover_img: List[ndarray] = None, factor: float = 2.0) -> List[ndarray]:
        """
        Applies a brightening effect to a batch of images (grayscale or RGB) using HSV color space transformation.

        For RGB images:
            1. Converts RGB to HSV.
            2. Scales the value channel (V) by 'factor'.
            3. Clips the result to the valid range [0, 255].
            4. Converts back to RGB.
        For grayscale images:
            1. Replicates the single channel to three channels to create a pseudo-RGB image.
            2. Applies the brightening in HSV space by scaling the V channel.
            3. Converts back to grayscale by taking one channel.

        Args:
            stego_imgs (List[ndarray]): Batch of watermarked images, each [H, W] (grayscale) or [H, W, 3] (RGB),
                                       dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored, for interface compatibility).
            factor (float): Brightness amplification factor, typically >= 1.0.
                           1.0 = no change, higher values = brighter image.

        Returns:
            List[ndarray]: Batch of brightened images, each with the same shape and dtype as input.
        """
        if not stego_imgs:
            return []

        factor = max(1.0, factor)
        is_grayscale = len(stego_imgs[0].shape) == 2
        noised_imgs = []
        for stego in stego_imgs:
            is_gray = stego.ndim == 2
            if is_gray:
                stego = np.stack([stego, stego, stego], axis=-1).astype(np.uint8)
            hsv = cv2.cvtColor(stego.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
            hsv[..., 2] = np.clip(hsv[..., 2] * factor, 0, 255)
            hsv_uint8 = hsv.astype(np.uint8)
            rgb = cv2.cvtColor(hsv_uint8, cv2.COLOR_HSV2RGB)
            if is_gray:
                rgb = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            noised_imgs.append(rgb)
        return noised_imgs


class Resize(BaseTestAttackModel):
    """
    A spatial resampling attack that scales an image down and then back up to the original resolution.

    This attack introduces interpolation artifacts (blurring, aliasing) by reducing the image
    to a smaller size and then upsampling it. It simulates common image processing operations like
    thumbnail generation or transmission over bandwidth-limited channels.

    The 'scale_p' parameter controls the downscaling factor:
        - 1.0: No change (identity)
        - 0.8: Reduce to 80% size, then upscale back
        - 0.5: Halve the dimensions, then double back (stronger distortion)

    This implementation uses `torchvision.transforms.Resize` for true batched processing,
    enabling GPU acceleration and eliminating Python loops.

    Note:
        - Input: List of uint8 RGB images [H, W, 3], range [0, 255]
        - Output: List of resized images, same shape and dtype
        - Uses torchvision for batched, GPU-accelerated resizing
    """

    def __init__(self, noisename: str = "Resize", mode: str = "bilinear"):
        """
        Initializes the resize attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
            mode (str): Interpolation method: 'nearest', 'bilinear', 'bicubic'.
        """
        super().__init__(noisename=noisename, factor_inversely_related=True)  # Higher scale = less distortion

        self.interpolation = {
            "nearest": transforms.InterpolationMode.NEAREST,
            "bilinear": transforms.InterpolationMode.BILINEAR,
            "bicubic": transforms.InterpolationMode.BICUBIC
        }.get(mode, transforms.InterpolationMode.BILINEAR)

    @torch.inference_mode()
    def attack(self, stego_img: List[ndarray], cover_img: List[ndarray] = None, scale_p: float = 0.8) -> List[ndarray]:
        """
        Applies resize distortion to a batch of stego images using torchvision's Resize transform.
        Supports both RGB and grayscale images.

        The pipeline:
            1. Stack images into a 4D numpy array [B, H, W, C]
            2. Convert to float32 and normalize to [0,1]
            3. Convert to CHW tensor and move to device
            4. Downsample using transforms.Resize
            5. Upsample back to original size using transforms.Resize
            6. Convert back to HWC uint8 numpy arrays

        Args:
            stego_img (List[ndarray]): Batch of watermarked images, each [H, W] or [H, W, 3], dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored).
            scale_p (float): Downscaling factor, range (0.01, 1.0].

        Returns:
            List[ndarray]: Batch of resized images, each with the same shape and dtype as input.
        """
        if not stego_img:
            return []

        scale_p = np.clip(scale_p, 0.01, 1.0)

        is_grayscale = len(stego_img[0].shape) == 2
        original_shapes = [img.shape[:2] for img in stego_img]
        h, w = original_shapes[0]

        if is_grayscale:
            expanded_imgs = [np.expand_dims(img, axis=-1) for img in stego_img]
        else:
            expanded_imgs = stego_img

        batch_np = np.stack(expanded_imgs, axis=0).astype(np.float32)

        batch_np = batch_np / 255.0

        batch_tensor = torch.from_numpy(batch_np).permute(0, 3, 1, 2)

        new_h, new_w = int(h * scale_p), int(w * scale_p)

        down_transform = transforms.Resize(size=(new_h, new_w), interpolation=self.interpolation)
        up_transform = transforms.Resize(size=(h, w), interpolation=self.interpolation)

        resized_down = down_transform(batch_tensor)
        resized_up = up_transform(resized_down)

        resized_np = (
                resized_up.permute(0, 2, 3, 1).cpu().numpy() * 255.0
        ).astype(np.uint8)

        if is_grayscale:
            resized_np = resized_np.squeeze(-1)

        return [resized_np[i] for i in range(resized_np.shape[0])]


class Rotate(BaseTestAttackModel):
    """
    A geometric attack that rotates an image around its center by a specified angle.

    This attack simulates camera rotation or document misalignment, which can disrupt watermark signals
    that are sensitive to spatial orientation or rely on fixed pixel patterns.

    The 'factor' parameter controls the rotation angle in degrees:
        - 0.0: No rotation (identity)
        - 10.0: 10-degree clockwise rotation
        - 360: Maximum rotation (wraps around)

    The rotation is performed around the image center using bilinear interpolation,
    and the borders are filled with black (0, 0, 0).

    This implementation uses `torchvision.transforms.functional.rotate` for true batched processing,
    enabling GPU acceleration and eliminating Python loops.

    Note:
        - Input: List of uint8 RGB images [H, W, 3], range [0, 255]
        - Output: List of rotated images, same shape and dtype
        - Uses torchvision for batched, GPU-accelerated rotation
    """

    def __init__(self, noisename: str = "Rotate"):
        """
        Initializes the rotation attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename, factor_inversely_related=True)  # Higher |angle| = stronger attack

    @torch.inference_mode()
    def attack(self, stego_img: List[ndarray], cover_img: List[ndarray] = None, factor: float = 10.0) -> List[ndarray]:
        """
        Applies rotation to a batch of stego images using torchvision's rotate function.

        Args:
            stego_img (List[ndarray]): Batch of watermarked images, each [H, W, 3], dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored).
            factor (float): Rotation angle in degrees, range [-180, 180].

        Returns:
            List[ndarray]: Batch of rotated images, each with the same shape and dtype as input.
        """
        if not stego_img:
            return []

        angle = np.clip(factor, 0, 360).item()

        is_grayscale = len(stego_img[0].shape) == 2
        if is_grayscale:
            expanded_imgs = [np.expand_dims(img, axis=-1) for img in stego_img]
        else:
            expanded_imgs = stego_img

        batch_np = np.stack(expanded_imgs, axis=0).astype(np.float32)
        batch_np = batch_np / 255.0

        batch_tensor = torch.from_numpy(batch_np).permute(0, 3, 1, 2)
        rotated_tensor = TF.rotate(
            batch_tensor,
            angle=angle,
            interpolation=TF.InterpolationMode.BILINEAR
        )

        rotated_np = (rotated_tensor.permute(0, 2, 3, 1).cpu().numpy() * 255.0).astype(np.uint8)

        if is_grayscale:
            rotated_np = rotated_np.squeeze(-1)

        return [rotated_np[i] for i in range(rotated_np.shape[0])]


class Jpeg(BaseTestAttackModel):
    """
    A lossy compression attack that applies JPEG encoding to introduce compression artifacts.

    This attack simulates common image degradation from web publishing, social media sharing,
    or storage optimization. It introduces blockiness, ringing, and high-frequency loss,
    which are particularly effective at disrupting watermark signals embedded in AC coefficients
    or high-frequency DCT components.

    The 'factor' parameter controls the JPEG quality setting:
        - 100: Near-lossless (very weak attack)
        - 95: High quality (minimal artifacts)
        - 50: Medium quality (visible block artifacts)
        - 20: Low quality (severe degradation, strong attack)
        - 1: Lowest quality (maximum compression, extreme distortion)

    This implementation uses OpenCV's imencode/imdecode for JPEG compression.

    Note:
        - Input: List of uint8 RGB images [H, W, 3], range [0, 255]
        - Output: List of JPEG-compressed images, same shape and dtype
        - Uses OpenCV with JPEG quality factor [1, 100]
    """

    def __init__(self, noisename: str = "Jpeg"):
        """
        Initializes the JPEG compression attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename,
                         factor_inversely_related=True)  # Higher factor = less compression = weaker attack

    def attack(self, stego_img: List[ndarray], cover_img: List[ndarray] = None, factor: int = 20) -> List[
        ndarray]:
        """
        Applies JPEG compression to a batch of stego images using OpenCV.

        For each image:
            1. Converts from RGB to BGR (OpenCV default).
            2. Encodes to JPEG format with specified quality.
            3. Decodes back to BGR.
            4. Converts back to RGB.

        Args:
            stego_img (List[ndarray]): Batch of watermarked images, each [H, W, 3], dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored, for interface compatibility).
            factor (int): JPEG quality factor in [1, 100].
                         100 = best quality, 1 = worst quality.

        Returns:
            List[ndarray]: Batch of JPEG-compressed images, each with the same shape and dtype as input.
        """
        if not stego_img:
            return []

        # Clip factor to valid range
        quality = max(1, min(100, int(factor)))
        noised_batch = []
        encode_param = [cv2.IMWRITE_JPEG_QUALITY, quality]
        is_color = stego_img[0].ndim == 3
        for img in stego_img:
            if is_color:
                img = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_RGB2BGR)
                _, encoded_img = cv2.imencode('.jpg', img, encode_param)
                decoded_img = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)
                decoded_img = cv2.cvtColor(decoded_img, cv2.COLOR_BGR2RGB)
            else:
                _, encoded_img = cv2.imencode('.jpg', img.astype(np.uint8), encode_param)
                decoded_img = cv2.imdecode(encoded_img, cv2.IMREAD_GRAYSCALE)
            noised_batch.append(decoded_img.astype(np.float32))
        return noised_batch


class Jpeg2000(BaseTestAttackModel):
    """
    A lossy wavelet-based compression attack using the JPEG2000 format.

    This attack applies JPEG2000 compression, which uses discrete wavelet transform (DWT) instead of DCT,
    resulting in different artifacts (e.g., less blockiness, more ringing) compared to standard JPEG.
    It is effective for evaluating watermark robustness against modern compression standards.

    The 'factor' parameter controls the compression ratio:
        - 1: Minimal compression (highest quality)
        - 100: Maximum compression (lowest quality)
        Higher values = stronger attack.

    This implementation uses OpenCV's imencode/imdecode for JPEG2000 compression.
    Note: OpenCV relies on external libraries (e.g., Jasper, OpenJPEG) for JP2 support.

    Reference:
        Skodras, A., Christopoulos, C., & Ebrahimi, T. (2001).
        The JPEG 2000 still image compression standard.
        IEEE Signal Processing Magazine, 18(5), 36–58.

    Note:
        - Input: List of uint8 RGB images [H, W, 3], range [0, 255]
        - Output: List of JPEG2000-compressed images, same shape and dtype
        - Requires OpenCV with JPEG2000 support (IMWRITE_JPEG2000_COMPRESSION_X1000)
    """

    def __init__(self, noisename: str = "Jpeg2000"):
        """
        Initializes the JPEG2000 compression attack.

        Args:
            noisename (str): Name identifier for logging and reporting.
        """
        super().__init__(noisename=noisename,
                         factor_inversely_related=False)  # Higher factor = more compression = stronger attack

    def attack(self, stego_img: List[ndarray], cover_img: List[ndarray] = None, factor: int = 20) -> List[ndarray]:
        """
        Applies JPEG2000 compression to a batch of stego images using OpenCV.

        For each image:
            1. Converts from RGB to BGR (OpenCV default).
            2. Encodes to JPEG2000 (.jp2) format with specified compression ratio.
            3. Decodes back to BGR.
            4. Converts back to RGB.

        Args:
            stego_img (List[ndarray]): Batch of watermarked images, each [H, W, 3], dtype=uint8, range [0,255].
            cover_img (List[ndarray], optional): Cover images (ignored, for interface compatibility).
            factor (int): Compression ratio factor in [1, 100].
                         1 = low compression, 100 = high compression.

        Returns:
            List[ndarray]: Batch of JPEG2000-compressed images, each with the same shape and dtype as input.
        """
        if not stego_img:
            return []

        # Clip factor to valid range
        noised_batch = []
        is_color = stego_img[0].ndim == 3
        compression_ratio = np.clip(factor, 0, 1000)
        encode_param = [cv2.IMWRITE_JPEG2000_COMPRESSION_X1000, compression_ratio]
        for img in stego_img:
            if is_color:
                img = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_RGB2BGR)
                _, encoded_img = cv2.imencode('.jp2', img, encode_param)
                decoded_img = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)
                decoded_img = cv2.cvtColor(decoded_img, cv2.COLOR_BGR2RGB)
            else:
                _, encoded_img = cv2.imencode('.jp2', img.astype(np.uint8), encode_param)
                decoded_img = cv2.imdecode(encoded_img, cv2.IMREAD_GRAYSCALE)
            noised_batch.append(decoded_img.astype(np.float32))
        return noised_batch
