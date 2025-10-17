# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT
import torch
import hashlib
import numpy as np
from typing import List
from numpy import ndarray
import onnxruntime as ort
from watermarklab.utils.logger import logger
from diffusers import StableDiffusionPipeline, DDIMScheduler
from watermarklab.utils.basemodel import BaseWatermarkModel, Result

__all__ = ["StableSignature"]

# --- Configuration ---
from watermarklab.utils.parameters import LOAD_FROM_LOCAL

_REPO_ID = "chenoly/watermarklab"
_VAE_DECODER_FILENAME = "watermarks/IGWs/pretrained_models/stablesignature/sd2_decoder.onnx"
_EXTRACTOR_FILENAME = "watermarks/IGWs/pretrained_models/stablesignature/dec_48b_whit.onnx"

_VAE_DECODER_SHA256 = "501d685e79b5cc8d534aba6a9f72ea788938aa579805c6f0c733e60ca6d5b7ae"
_EXTRACTOR_SHA256 = "4b211ff7f17a9e19e4d8ebac95b9fa7618de5d49e211f810b5d155bba7352a8b"

_WATERMARK_BITS_LEN = 48
_WATERMARK_LIST = [
    1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0,
    0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1,
    0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1
]
# --- End of Configuration ---
RED = "\033[91m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"


class StableSignature(BaseWatermarkModel):
    """
    StableSignature watermarking method for AIGC.
    Uses a fixed 48-bit watermark embedded via modified VAE decoding.
    Extracts watermark using a trained ONNX message extractor.

    Reference:
        The Stable Signature: Rooting Watermarks in Latent Diffusion Models
        Pierre Fernandez, Guillaume Couairon, Hervé Jégou, Matthijs Douze, Teddy Furon

    """

    def __init__(self, img_size: int = 512, bits_len: int = 48, model_id: str = "stabilityai/stable-diffusion-2-1-base",
                 modelname: str = "StableSignature", local_files_only=False):
        """
        Initialize the StableSignature model.

        Args:
            img_size (int): Image size (default 512).
            bits_len (int): Length of watermark (must be 48).
            model_id (str): Hugging Face ID for the Stable Diffusion base model.
            modelname (str): Model identifier.
        """
        super().__init__(48, img_size, modelname)
        self.local_files_only = local_files_only
        # --- Download and Verify Models ---
        try:
            from huggingface_hub import hf_hub_download
            import sys

            sys.stdout.write(f"[{GREEN}WatermarkLab{RESET} INFO] ")
            sys.stdout.flush()

            # Download VAE decoder
            sys.stdout.write("Downloading VAE decoder... ")
            sys.stdout.flush()
            self._vae_decoder_path = hf_hub_download(
                repo_id=_REPO_ID,
                filename=_VAE_DECODER_FILENAME,
                use_auth_token=True,
                local_files_only=self.local_files_only
            )
            sys.stdout.write(f"{GREEN}✓{RESET} | ")
            sys.stdout.write("Verifying SHA256... ")
            sys.stdout.flush()

            if not self._check_file_sha256(self._vae_decoder_path, _VAE_DECODER_SHA256):
                sys.stdout.write(f"{RED}FAILED{RESET}\n")
                logger.error(f"SHA256 mismatch for VAE decoder: {self._vae_decoder_path}")
                raise ValueError(f"SHA256 mismatch for VAE decoder: {self._vae_decoder_path}")
            sys.stdout.write(f"{BLUE}✓{RESET} | ")

            # Download extractor
            sys.stdout.write("Downloading message extractor... ")
            sys.stdout.flush()
            self._extractor_path = hf_hub_download(
                repo_id=_REPO_ID,
                filename=_EXTRACTOR_FILENAME,
                use_auth_token=True
            )
            sys.stdout.write(f"{GREEN}✓{RESET} | ")
            sys.stdout.write("Verifying SHA256... ")
            sys.stdout.flush()

            if not self._check_file_sha256(self._extractor_path, _EXTRACTOR_SHA256):
                sys.stdout.write(f"{RED}FAILED{RESET}\n")
                logger.error(f"SHA256 mismatch for extractor: {self._extractor_path}")
                raise ValueError(f"SHA256 mismatch for extractor: {self._extractor_path}")
            sys.stdout.write(f"{BLUE}✓{RESET} | ")
            sys.stdout.write(f"StableSignature models loaded. {GREEN}🎉{RESET}\n")

        except ImportError:
            logger.error(f"'huggingface_hub' not installed. Use: pip install huggingface_hub")
            raise
        except Exception as e:
            logger.error(f"Failed to download StableSignature models: {e}")
            raise RuntimeError(f"Failed to download StableSignature models: {e}") from e
        # --- End of Download Process ---

        # Load ONNX models
        self._load_vae_decoder()
        self._load_extractor()

        # Load Stable Diffusion pipelines
        self._load_pipeline(model_id)

        logger.info(f"{modelname} has been initialized")

    @staticmethod
    def _check_file_sha256(file_path: str, expected_hash: str) -> bool:
        """
        Compute and verify the SHA256 checksum of a file.
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest().lower() == expected_hash.lower()

    def _get_ort_providers(self):
        """
        Return appropriate ONNX Runtime execution providers.
        Use CUDA if available and ONNX supports it.
        """
        # if "CUDAExecutionProvider" in ort.get_available_providers():
        #     return [("CUDAExecutionProvider", {"device_id": 0}), "CPUExecutionProvider"]
        # return ["CPUExecutionProvider"]
        return ["CPUExecutionProvider"]

    def _load_vae_decoder(self):
        """
        Load the ONNX VAE decoder model.
        """
        sess_options = ort.SessionOptions()
        providers = self._get_ort_providers()
        self.vae_decoder_session = ort.InferenceSession(
            self._vae_decoder_path,
            sess_options=sess_options,
            providers=providers
        )
        logger.info(f"ONNX VAE Decoder loaded.")

    def _load_extractor(self):
        """
        Load the ONNX message extractor model.
        """
        sess_options = ort.SessionOptions()
        providers = self._get_ort_providers()
        self.extractor_session = ort.InferenceSession(
            self._extractor_path,
            sess_options=sess_options,
            providers=providers
        )
        logger.info(f"ONNX Message Extractor loaded.")

    def _load_pipeline(self, model_id: str):
        """
        Load the Stable Diffusion pipeline and replace VAE decode with ONNX version.
        Uses CPU offloading for memory efficiency.
        """
        scheduler = DDIMScheduler.from_pretrained(model_id, subfolder="scheduler", local_files_only=self.local_files_only)

        # Original pipeline (no watermark)
        self.pipe_org = StableDiffusionPipeline.from_pretrained(
            model_id,
            scheduler=scheduler,
            safety_checker=None,
            torch_dtype=torch.float16,
            local_files_only=self.local_files_only
        )
        self.pipe_org.enable_model_cpu_offload()

        # Watermarked pipeline
        self.pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            scheduler=scheduler,
            safety_checker=None,
            torch_dtype=torch.float16,
            local_files_only=self.local_files_only
        )
        self.pipe.enable_model_cpu_offload()

        def onnx_decode(latents, return_dict=True, **kwargs):
            # Move to CPU for ONNX (ONNX handles GPU internally via CUDA provider)
            latents_np = latents.cpu().numpy().astype(np.float32)
            image_np = self.vae_decoder_session.run(["image"], {"latent": latents_np})[0]
            # Convert back to tensor, let pipeline handle device
            image_tensor = torch.from_numpy(image_np)
            return {"sample": image_tensor} if return_dict else (image_tensor,)

        self.pipe.vae.decode = onnx_decode

    @torch.inference_mode()
    def embed(self, prompts: List[str], secrets: List[List[int]] = None) -> Result:
        """
        Generate watermarked images from text prompts (batched).

        Args:
            prompts (List[str]): List of text prompts.
            secrets (List[List[int]]): Ignored. Uses fixed watermark.

        Returns:
            Result: Watermarked images, clean images, and embedded bits.
        """
        batch_size = len(prompts)

        # Generate random latents on CPU (offloading will move to GPU as needed)
        latents = torch.randn(
            (batch_size, 4, 64, 64),
            dtype=torch.float16,
            device="cpu"
        )

        # Generate clean images
        clean_outputs = self.pipe_org(
            prompt=prompts,
            latents=latents,
            output_type="numpy"
        )
        clean_images = [np.array(img * 255, dtype=np.uint8) for img in clean_outputs.images]

        # Generate watermarked images
        stego_outputs = self.pipe(
            prompt=prompts,
            latents=latents,
            output_type="numpy"
        )
        stego_images = [np.array(img * 255, dtype=np.uint8) for img in stego_outputs.images]

        # Repeat fixed watermark for each image
        emb_bits_list = [_WATERMARK_LIST for _ in range(batch_size)]

        return Result(stego_img=stego_images, clean_img=clean_images, emb_bits=emb_bits_list)

    @torch.inference_mode()
    def extract(self, stego_list: List[ndarray]) -> Result:
        """
        Extract 48-bit watermark from watermarked images (batched).

        Args:
            stego_list (List[ndarray]): List of watermarked images [H, W, 3], uint8.

        Returns:
            Result: Extracted binary watermarks.
        """
        if len(stego_list) == 0:
            return Result(ext_bits=[])

        # Convert to float32 and normalize
        stego_batch = np.stack(stego_list).astype(np.float32) / 255.0  # [B, H, W, 3]
        stego_batch = np.transpose(stego_batch, (0, 3, 1, 2))  # [B, 3, H, W]

        # Normalize using ImageNet stats
        mean = np.array([0.485, 0.456, 0.406]).reshape(1, 3, 1, 1)
        std = np.array([0.229, 0.224, 0.225]).reshape(1, 3, 1, 1)
        normalized_image_np = (stego_batch - mean) / std

        # Run ONNX extractor
        logits = self.extractor_session.run(
            ["message_logits"],
            {"image": normalized_image_np.astype(np.float32)}
        )[0]  # [B, 48]

        ext_bits_batch = (logits > 0.0).astype(np.int32).tolist()

        return Result(ext_bits=ext_bits_batch)

    def recover(self, stego_list: List[ndarray]) -> Result:
        """
        Recover original image from watermarked image.
        Not supported by StableSignature.

        Args:
            stego_list (List[ndarray]): Watermarked images.

        Returns:
            Result: NotImplemented.

        Raises:
            NotImplementedError: Recovery not supported.
        """
        raise NotImplementedError("Recovery is not supported by StableSignature.")
