# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT
import torch
import hashlib
import numpy as np
from typing import List
from numpy import ndarray
import onnxruntime as ort
from watermarklab.utils.basemodel import BaseWatermarkModel, Result

__all__ = ["InvisMark"]

# --- Configuration ---
# Hugging Face repository ID
from watermarklab.utils.parameters import LOAD_FROM_LOCAL

_REPO_ID = "chenoly/watermarklab"

# Filenames of the ONNX models in the Hugging Face repository
_ENCODER_FILENAME = "watermarks/PGWs/pretrained_models/invismark/invismark_encoder.onnx"
_DECODER_FILENAME = "watermarks/PGWs/pretrained_models/invismark/invismark_decoder.onnx"

# Expected SHA256 checksums for the model files (computed from the uploaded files)
_ENCODER_SHA256 = "7fce8700d4fddd47e61f23b519110f4ceba359940482ff84f060ac9196f93e3d"
_DECODER_SHA256 = "f344fc2e776f75a11940ff10b4e61d33adcbb1a9648553b44f3ce269a39d84e2"

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"  # Reset to default color


# --- End of Configuration ---

class InvisMark(BaseWatermarkModel):
    """
    The InvisMark watermark.

    Reference:
        Rui Xu, Mengya Hu, Deren Lei, Yaxi Li, David Lowe, Alex Gorevski, Mingyu Wang, Emily Ching, Alex Deng.
        InvisMark: Invisible and Robust Watermarking for AI-generated Image Provenance. arXiv:2411.07795

    """

    def __init__(self, img_size: int = 256, bits_len: int = 100, modelname: str = "InvisMark", device: str = "cuda", local_files_only=False):
        """
        Initialize the InvisMark wrapper with ONNX models.

        Args:
            img_size (int): Expected image size (assumed square, default 256).
            bits_len (int): Length of the watermark (must be 100).
            modelname (str): Model identifier (default 'InvisMark').
            device (str): Specifies the device to use ('cuda' or 'cpu').
        """
        super().__init__(bits_len, img_size, modelname)
        self.bits_len = bits_len
        self.local_files_only = local_files_only
        # --- Download and Verify Models ---
        try:
            from huggingface_hub import hf_hub_download
            import sys

            # Start the progress message
            sys.stdout.write(f"[{GREEN}WatermarkLab{RESET} INFO] ")
            sys.stdout.flush()

            # Download encoder model
            sys.stdout.write("Downloading InvisMark encoder... ")
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

            # Validate encoder checksum
            if not self._check_file_sha256(self._encoder_local_path, _ENCODER_SHA256):
                sys.stdout.write(f"{RED}FAILED{RESET}\n")
                raise ValueError(f"SHA256 checksum mismatch for encoder: {self._encoder_local_path}")

            sys.stdout.write(f"{BLUE}✓{RESET} | ")

            # Download decoder model
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

            # Validate decoder checksum
            if not self._check_file_sha256(self._decoder_local_path, _DECODER_SHA256):
                sys.stdout.write(f"{RED}FAILED{RESET}\n")
                raise ValueError(f"SHA256 checksum mismatch for decoder: {self._decoder_local_path}")

            sys.stdout.write(f"{BLUE}✓{RESET} | ")
            sys.stdout.write(f"InvisMark models loaded successfully. {GREEN}🎉{RESET}\n")

        except ImportError:
            # Inform user if huggingface_hub is not installed
            print(
                f"[{RED}WatermarkLab{RESET} ERROR] 'huggingface_hub' is required. Install it via: pip install huggingface_hub")
            raise

        except Exception as e:
            # Ensure a newline if error occurs during download/verification
            print()
            raise RuntimeError(f"Failed to download InvisMark models from Hugging Face Hub: {e}") from e

        # --- End of Download Process ---

        # Determine the GPU ID based on the provided device string
        gpu_id = self._get_gpu_id(device)
        cuda_provider_options = {'device_id': gpu_id}

        # Define the execution providers for ONNX Runtime
        providers = [
            ('CUDAExecutionProvider', cuda_provider_options),
            'CPUExecutionProvider'
        ]

        # Fallback to CPU if CUDA is not available
        if 'CUDAExecutionProvider' not in ort.get_available_providers():
            print(f"[{GREEN}WatermarkLab{RESET} INFO] {modelname} model loaded on CPU.")
            providers = ['CPUExecutionProvider']
        else:
            print(f"[{GREEN}WatermarkLab{RESET} INFO] {modelname} model loaded on cuda {gpu_id}.")

        # Load the ONNX models directly from the paths returned by hf_hub_download
        self._encoder_session = ort.InferenceSession(self._encoder_local_path, providers=providers)
        self._decoder_session = ort.InferenceSession(self._decoder_local_path, providers=providers)

        # Define the input and output names for the ONNX models
        self._encoder_input_cover = "cover"
        self._encoder_input_secret = "secret"
        self._encoder_output = "encoded_image"
        self._decoder_input = "stego_image"
        self._decoder_output = "decoded_secret"

    def _get_gpu_id(self, device: str) -> int:
        """Extract the GPU ID from a device string."""
        device = torch.device(device)
        if device.type == "cuda":
            return device.index if device.index is not None else 0
        return -1

    @staticmethod
    def _check_file_sha256(file_path: str, expected_hash: str) -> bool:
        """
        Compute and verify the SHA256 checksum of a file.

        Args:
            file_path (str): Path to the file.
            expected_hash (str): Expected SHA256 hash in hex format.

        Returns:
            bool: True if the computed checksum matches the expected hash, False otherwise.
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest().lower() == expected_hash.lower()

    def embed(self, cover_list: List[ndarray], secrets: List[List[int]]) -> Result:
        """
        Embed 100-bit watermarks into a batch of cover images.

        Args:
            cover_list (List[ndarray]): A list of RGB images with shape [H, W, 3], pixel values in [0, 255].
            secrets (List[List[int]]): A list of 100-bit binary watermarks.

        Returns:
            Result: A Result object containing the list of watermarked images.
        """
        # Convert the list of images to a single batch tensor
        cover_batch = np.stack(cover_list)  # shape: (B, H, W, 3)

        # Normalize to [0, 1] and transpose to [B, C, H, W]
        cover_float32 = cover_batch.astype(np.float32) / 255.0
        cover_tensor = np.transpose(cover_float32, (0, 3, 1, 2))  # [B, H, W, 3] -> [B, 3, H, W]

        # Convert the list of secrets to a single batch tensor
        secret_tensor = np.array(secrets, dtype=np.float32)  # shape: (B, 100)

        # Prepare the input dictionary for the encoder
        feed_dict = {
            self._encoder_input_cover: cover_tensor,
            self._encoder_input_secret: secret_tensor
        }

        # Run the encoder model on the entire batch
        encoded_img_batch = self._encoder_session.run([self._encoder_output], feed_dict)[0]

        # Convert the batch output back to [B, H, W, 3] and [0, 255] range
        stego_rgb_batch = np.transpose(encoded_img_batch, (0, 2, 3, 1))  # [B, 3, H, W] -> [B, H, W, 3]
        stego_rgb_batch = np.clip(stego_rgb_batch * 255, 0, 255).astype(np.uint8)

        # Convert the batch tensor back to a list of individual images
        stego_list = [img for img in stego_rgb_batch]

        return Result(stego_img=stego_list, emb_bits=secrets)

    def extract(self, stego_list: List[ndarray]) -> Result:
        """
        Extract 100-bit watermarks from a batch of watermarked images.

        Args:
            stego_list (List[ndarray]): A list of watermarked RGB images with shape [H, W, 3], pixel values in [0, 255].

        Returns:
            Result: A Result object containing the list of extracted binary watermarks.
        """
        # Convert the list of stego images to a single batch tensor
        stego_batch = np.stack(stego_list)  # shape: (B, H, W, 3)

        # Normalize to [0, 1] and transpose to [B, C, H, W]
        stego_float32 = stego_batch.astype(np.float32) / 255.0
        stego_tensor = np.transpose(stego_float32, (0, 3, 1, 2))  # [B, H, W, 3] -> [B, 3, H, W]

        # Prepare the input dictionary for the decoder
        decoder_input = {self._decoder_input: stego_tensor}

        # Run the decoder model on the entire batch
        decoded_secret_batch = self._decoder_session.run([self._decoder_output], decoder_input)[0]  # [B, 100]

        # Convert logits to binary bits using a threshold of 0.5
        binary_secret_batch = (decoded_secret_batch > 0.5).astype(np.int32)  # [B, 100]

        # Convert the batch tensor back to a list of individual watermark lists
        ext_secret_list = [secret.tolist() for secret in binary_secret_batch]

        return Result(ext_bits=ext_secret_list)

    def recover(self, stego_list: List[ndarray]) -> Result:
        """
        Recover the original image from the watermarked image.
        This functionality is not supported by the InvisMark model.

        Args:
            stego_list (List[ndarray]): A list of watermarked images.

        Returns:
            Result: NotImplemented.
        """
        pass
