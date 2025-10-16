# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT
import torch
import hashlib
import numpy as np
from typing import List
from numpy import ndarray
import onnxruntime as ort
from watermarklab.utils.basemodel import BaseWatermarkModel, Result

__all__ = ["StegaStamp"]

# --- Configuration ---
# Hugging Face repository ID
from watermarklab.utils.parameters import LOAD_FROM_LOCAL

_REPO_ID = "chenoly/watermarklab"  # Update if hosted elsewhere

# ONNX model file path in the repo
_MODEL_FILENAME = "watermarks/PGWs/pretrained_models/stegastamp/stegastamp.onnx"

# Expected SHA256 checksum
_MODEL_SHA256 = "1670296839494145683f0946a70d0113fefe0757cfb54219fb16fcdd9763fcf7"

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"


# --- End of Configuration ---

class StegaStamp(BaseWatermarkModel):
    """
    Wrapper for the StegaStamp ONNX model.
    Implements embed and extract interfaces for 100-bit watermarking.
    Does not support image recovery.

    Reference:
        Matthew Tancik, Ben Mildenhall, Ren Ng. StegaStamp: Invisible Hyperlinks in Physical Photographs. arXiv:1904.05343
    """

    def __init__(self, img_size: int = 400, bits_len: int = 100, modelname: str = "StegaStamp", device: str = "cuda",
                 local_files_only: bool = False):
        """
        Initialize the StegaStamp model.

        Args:
            img_size (int): Input image size (assumed square, default 400).
            bits_len (int): Length of the watermark (must be 100).
            modelname (str): Model identifier.
            device (str): Device to run on ('cpu' or 'cuda').
        """
        super().__init__(bits_len, img_size, modelname)
        assert bits_len == 100, "StegaStamp only supports 100-bit watermarks"
        self.bits_len = bits_len
        self.local_files_only = local_files_only

        # --- Download and Verify Model ---
        try:
            from huggingface_hub import hf_hub_download
            import sys

            sys.stdout.write(f"[{GREEN}WatermarkLab{RESET} INFO] ")
            sys.stdout.flush()

            # Download model
            sys.stdout.write("Downloading StegaStamp ONNX model... ")
            sys.stdout.flush()
            self._model_local_path = hf_hub_download(
                repo_id=_REPO_ID,
                filename=_MODEL_FILENAME,
                use_auth_token=True,
                local_files_only=self.local_files_only
            )
            sys.stdout.write(f"{GREEN}✓{RESET} | ")
            sys.stdout.write("Verifying SHA256... ")
            sys.stdout.flush()

            # Validate checksum
            if not self._check_file_sha256(self._model_local_path, _MODEL_SHA256):
                sys.stdout.write(f"{RED}FAILED{RESET}\n")
                raise ValueError(f"SHA256 checksum mismatch for {self._model_local_path}")
            sys.stdout.write(f"{BLUE}✓{RESET} | ")
            sys.stdout.write(f"StegaStamp model loaded successfully. {GREEN}🎉{RESET}\n")

        except ImportError:
            print(
                f"[{RED}WatermarkLab{RESET} ERROR] 'huggingface_hub' is required. Install with: pip install huggingface_hub")
            raise
        except Exception as e:
            print()
            raise RuntimeError(f"Failed to download StegaStamp model from Hugging Face Hub: {e}") from e
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

        # Load ONNX session
        self._session = ort.InferenceSession(self._model_local_path, providers=providers)

        # Get input/output names
        self._input_names = [inp.name for inp in self._session.get_inputs()]
        self._output_names = [out.name for out in self._session.get_outputs()]

        # Resolve input names (support multiple naming conventions)
        self._input_image_name = "image" if "image" in self._input_names else "input_hide:0"
        self._input_secret_name = "secret" if "secret" in self._input_names else "input_prep:0"

        # Output names
        self._output_stegastamp_name = "clip_by_value:0"
        self._output_residual_name = "gen_encoder/enc_conv_15/BiasAdd:0"
        self._output_decoded_name = "Round:0"

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
            device (str): Device string (e.g., 'cuda:0', 'cpu').

        Returns:
            int: GPU ID, or -1 if using CPU.
        """
        dev = torch.device(device)
        return dev.index if dev.type == "cuda" and dev.index is not None else 0 if dev.type == "cuda" else -1

    def embed(self, cover_list: List[ndarray], secrets: List[List[int]]) -> Result:
        """
        Embed 100-bit watermarks into a batch of cover images.

        Args:
            cover_list (List[ndarray]): List of RGB images [H, W, 3], uint8 [0, 255].
            secrets (List[List[int]]): List of 100-bit binary watermarks.

        Returns:
            Result: Watermarked images and embedded bits.
        """
        assert all(len(s) == self.bits_len for s in secrets), f"Each secret must be {self.bits_len} bits."

        # Batch and normalize cover images
        cover_batch = np.stack(cover_list).astype(np.float32) / 255.0  # [B, H, W, 3]

        # Convert secrets to float32 batch
        secret_batch = np.array(secrets, dtype=np.float32)  # [B, 100]

        # Prepare input feed
        feed_dict = {
            self._input_image_name: cover_batch,
            self._input_secret_name: secret_batch
        }

        # Run encoder
        stego_batch, _ = self._session.run(
            [self._output_stegastamp_name, self._output_residual_name],
            feed_dict
        )

        # Denormalize and convert to uint8
        stego_rgb_batch = np.clip(stego_batch * 255, 0, 255).astype(np.uint8)
        stego_list = [img for img in stego_rgb_batch]

        return Result(stego_img=stego_list, emb_bits=secrets)

    def extract(self, stego_list: List[ndarray]) -> Result:
        """
        Extract 100-bit watermarks from a batch of watermarked images.

        Args:
            stego_list (List[ndarray]): List of watermarked images [H, W, 3], uint8.

        Returns:
            Result: Extracted binary watermarks.
        """
        # Batch and normalize stego images
        stego_batch = np.stack(stego_list).astype(np.float32) / 255.0  # [B, H, W, 3]

        # Placeholder for secret input
        placeholder_secret = np.zeros((len(stego_list), self.bits_len), dtype=np.float32)

        # Prepare input feed
        decoder_input = {
            self._input_image_name: stego_batch,
            self._input_secret_name: placeholder_secret
        }

        # Run decoder
        decoded_batch = self._session.run([self._output_decoded_name], decoder_input)[0]  # [B, 100]

        # Threshold to binary
        ext_bits_batch = (decoded_batch > 0.5).astype(np.int32).tolist()

        return Result(ext_bits=ext_bits_batch)

    def recover(self, stego_list: List[ndarray]) -> Result:
        """
        Recover original image from watermarked image.
        Not supported by StegaStamp.

        Args:
            stego_list (List[ndarray]): Watermarked images.

        Returns:
            Result: NotImplemented.

        Raises:
            NotImplementedError: Recovery not supported.
        """
        raise NotImplementedError("Recovery is not supported by StegaStamp.")
