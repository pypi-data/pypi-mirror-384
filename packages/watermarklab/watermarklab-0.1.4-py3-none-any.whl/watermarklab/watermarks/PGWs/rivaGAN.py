# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT
import torch
import hashlib
import numpy as np
from typing import List
from numpy import ndarray
import onnxruntime as ort
from watermarklab.utils.basemodel import BaseWatermarkModel, Result

__all__ = ["rivaGAN"]

# --- Configuration ---
# Hugging Face repository ID
from watermarklab.utils.parameters import LOAD_FROM_LOCAL

_REPO_ID = "chenoly/watermarklab"  # Update if different

# ONNX model file paths in the repo
_ENCODER_FILENAME = "watermarks/PGWs/pretrained_models/rivaGAN/rivagan_encoder.onnx"
_DECODER_FILENAME = "watermarks/PGWs/pretrained_models/rivaGAN/rivagan_decoder.onnx"

# Expected SHA256 checksums
_ENCODER_SHA256 = "66bc7814fadac7d686105c8ab26c6cf2cc8e40deb83e67bb6ef5b9de9b8ece0d"
_DECODER_SHA256 = "6b006690cf352fa50a91a0b6d6241dbcded0a9957969e2c0665cf9a7011b3880"

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"


# --- End of Configuration ---

class rivaGAN(BaseWatermarkModel):
    """
    Wrapper for rivaGAN ONNX models.
    Implements embedding and extraction of 32-bit watermarks.
    Does not support image recovery.

    Reference:
        Kevin Alex Zhang, Lei Xu, Alfredo Cuesta-Infante, Kalyan Veeramachaneni.
        Robust Invisible Video Watermarking with Attention. arXiv:1909.01285
    """

    def __init__(self, img_size: int = 256, bits_len: int = 32, modelname: str = "rivaGAN", device: str = "cuda", local_files_only: bool = False):
        """
        Initialize the rivaGAN model.

        Args:
            img_size (int): Input image size (assumed square, default 256).
            bits_len (int): Length of watermark (must be 32).
            modelname (str): Model identifier.
            device (str): Device to run on ('cpu' or 'cuda').
        """
        super().__init__(bits_len, img_size, modelname)

        self.local_files_only = local_files_only
        if bits_len != 32:
            raise ValueError("rivaGAN only supports 32-bit watermarks.")
        self.bits_len = bits_len

        # --- Download and Verify Models ---
        try:
            from huggingface_hub import hf_hub_download
            import sys

            sys.stdout.write(f"[{GREEN}WatermarkLab{RESET} INFO] ")
            sys.stdout.flush()

            # Download encoder
            sys.stdout.write("Downloading rivaGAN encoder... ")
            sys.stdout.flush()
            self._encoder_local_path = hf_hub_download(
                repo_id=_REPO_ID,
                filename=_ENCODER_FILENAME,
                use_auth_token=True,
                local_files_only=self.local_files_only
            )
            sys.stdout.write(f"{GREEN}✓{RESET} | ")
            sys.stdout.write("Verifying SHA256... ")
            sys.stdout.flush()

            if not self._check_file_sha256(self._encoder_local_path, _ENCODER_SHA256):
                sys.stdout.write(f"{RED}FAILED{RESET}\n")
                raise ValueError(f"SHA256 checksum mismatch for encoder: {self._encoder_local_path}")
            sys.stdout.write(f"{BLUE}✓{RESET} | ")

            # Download decoder
            sys.stdout.write("Downloading decoder... ")
            sys.stdout.flush()
            self._decoder_local_path = hf_hub_download(
                repo_id=_REPO_ID,
                filename=_DECODER_FILENAME,
                use_auth_token=True,
                local_files_only=self.local_files_only
            )
            sys.stdout.write(f"{GREEN}✓{RESET} | ")
            sys.stdout.write("Verifying SHA256... ")
            sys.stdout.flush()

            if not self._check_file_sha256(self._decoder_local_path, _DECODER_SHA256):
                sys.stdout.write(f"{RED}FAILED{RESET}\n")
                raise ValueError(f"SHA256 checksum mismatch for decoder: {self._decoder_local_path}")
            sys.stdout.write(f"{BLUE}✓{RESET} | ")
            sys.stdout.write(f"rivaGAN models loaded. {GREEN}🎉{RESET}\n")

        except ImportError:
            print(f"[{RED}WatermarkLab{RESET} ERRO] 'huggingface_hub' not installed. Use: pip install huggingface_hub")
            raise
        except Exception as e:
            print()
            raise RuntimeError(f"Failed to download rivaGAN models from Hugging Face Hub: {e}") from e
        # --- End of Download Process ---

        # Determine GPU ID
        gpu_id = self._get_gpu_id(device)
        cuda_provider_options = {'device_id': gpu_id}

        # Define execution providers
        providers = [
            ('CUDAExecutionProvider', cuda_provider_options),
            'CPUExecutionProvider'
        ]
        if 'CUDAExecutionProvider' not in ort.get_available_providers():
            print(f"[{GREEN}WatermarkLab{RESET} INFO] {modelname} model loaded on CPU.")
            providers = ['CPUExecutionProvider']
        else:
            print(f"[{GREEN}WatermarkLab{RESET} INFO] {modelname} model loaded on cuda:{gpu_id}.")

        # Load ONNX sessions
        self._encoder_session = ort.InferenceSession(self._encoder_local_path, providers=providers)
        self._decoder_session = ort.InferenceSession(self._decoder_local_path, providers=providers)

        # Define I/O names
        self._encoder_input_frame = "frame"
        self._encoder_input_data = "data"
        self._encoder_output = "output"

        self._decoder_input_frame = "frame"
        self._decoder_output = "output"

    @staticmethod
    def _check_file_sha256(file_path: str, expected_hash: str) -> bool:
        """
        Compute and verify the SHA256 checksum of a file.

        Args:
            file_path (str): Path to the file.
            expected_hash (str): Expected SHA256 hash in hex.

        Returns:
            bool: True if match, False otherwise.
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest().lower() == expected_hash.lower()

    def _get_gpu_id(self, device: str) -> int:
        """
        Extract GPU ID from device string.

        Args:
            device (str): Device string (e.g., 'cuda:0').

        Returns:
            int: GPU ID, or -1 if using CPU.
        """
        dev = torch.device(device)
        return dev.index if dev.type == "cuda" and dev.index is not None else 0 if dev.type == "cuda" else -1

    def embed(self, cover_list: List[ndarray], secrets: List[List[int]]) -> Result:
        """
        Embed 32-bit watermarks into cover images.

        Args:
            cover_list (List[ndarray]): List of RGB images [H, W, 3], uint8 [0, 255].
            secrets (List[List[int]]): List of 32-bit binary watermarks.

        Returns:
            Result: Watermarked images and embedded bits.
        """
        assert all(len(s) == self.bits_len for s in secrets), f"Each secret must be {self.bits_len} bits."
        # Normalize to [-1, 1], transpose to [B, 3, H, W], add time dim
        cover_batch = np.stack(cover_list).astype(np.float32)
        cover_input = (cover_batch / 127.5) - 1.0
        cover_input = np.transpose(cover_input, (0, 3, 1, 2))  # [B, H, W, 3] -> [B, 3, H, W]
        cover_input = np.expand_dims(cover_input, axis=2)  # Add temporal dim: [B, 3, 1, H, W]

        secret_batch = np.array(secrets, dtype=np.float32)

        feed_dict = {
            self._encoder_input_frame: cover_input,
            self._encoder_input_data: secret_batch
        }

        wm_batch = self._encoder_session.run([self._encoder_output], feed_dict)[0]  # [B, 3, 1, H, W]
        wm_rgb_batch = np.transpose(wm_batch[:, :, 0, :, :], (0, 2, 3, 1))  # Remove batch, transpose
        wm_rgb_batch = np.clip((wm_rgb_batch + 1.0) * 127.5, 0, 255).astype(np.uint8)
        stego_list = [img for img in wm_rgb_batch]
        return Result(stego_img=stego_list, emb_bits=secrets)

    def extract(self, stego_list: List[ndarray]) -> Result:
        """
        Extract 32-bit watermarks from stego images.

        Args:
            stego_list (List[ndarray]): Watermarked images [H, W, 3], uint8.

        Returns:
            Result: Extracted binary watermarks.
        """
        stego_batch = np.stack(stego_list).astype(np.float32)
        stego_input = (stego_batch / 127.5) - 1.0
        stego_input = np.transpose(stego_input, (0, 3, 1, 2))  # [B, H, W, 3] -> [B, 3, H, W]
        stego_input = np.expand_dims(stego_input, axis=2)  # [B, 3, 1, H, W]

        decoder_input = {self._decoder_input_frame: stego_input}
        decoded_batch = self._decoder_session.run([self._decoder_output], decoder_input)[0]  # [B, 32]
        ext_bits = (decoded_batch > 0.52).astype(np.int32).tolist()

        return Result(ext_bits=ext_bits)

    def recover(self, stego_list: List[ndarray]) -> Result:
        """
        Recover original image from watermarked image.
        Not supported by rivaGAN.

        Args:
            stego_list (List[ndarray]): Watermarked images.

        Returns:
            Result: NotImplemented.

        Raises:
            NotImplementedError: Recovery not supported.
        """
        raise NotImplementedError("Recovery is not supported by rivaGAN.")
