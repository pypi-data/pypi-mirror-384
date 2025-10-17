# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT
import torch
import hashlib
import numpy as np
import cv2
from typing import List
from numpy import ndarray
import onnxruntime as ort
from watermarklab.utils.basemodel import BaseWatermarkModel, Result

__all__ = ["TrustMark"]

# --- Configuration ---
# Hugging Face repository ID
_REPO_ID = "chenoly/watermarklab"

# Model types supported
_MODEL_TYPES = ['C', 'Q', 'B', 'P']

# Filenames for encoder, decoder, and remover per model type
_ENCODER_FILE = lambda t: f"watermarks/PGWs/pretrained_models/trustmark/{t}/trustmark_{t}_encoder.onnx"
_DECODER_FILE = lambda t: f"watermarks/PGWs/pretrained_models/trustmark/{t}/trustmark_{t}_decoder.onnx"
_REMOVER_FILE = lambda t: f"watermarks/PGWs/pretrained_models/trustmark/{t}/trustmark_{t}_remover.onnx"

# SHA256 checksums for each model type
_MODEL_SHA256 = {
    'B': {
        'encoder': 'fa28707a1a103ddc58ffb4fb257610e4960c30abb07606bf1c696ff86575bf9c',
        'decoder': '14681d6b4de45bc740cdd4d523377cbd9d83f2cf027e698319dc93a9af10bf88',
        'remover': '1422382f809125f8041fd3a885cbd48a72463a5042facebaf44b53e769e75044',
    },
    'C': {
        'encoder': '1816954c1800ef7813a6d30b07e02a3c6b10d53aee627f9a42a8f6f316f11333',
        'decoder': '681d811dcfe4453d31508498bfe2288b689b3a5750bd6c1cd47f80ff5bc83aed',
        'remover': 'e53ba4c6d0c8c9949f31f1a0a563a37bae86c5cf2cc7c4ad8f80e93d7d728cac',
    },
    'P': {
        'encoder': '6ec452b568cd6a660859032cbe1ec641af83ff12623bf6877db4f8516631a629',
        'decoder': 'a89deab164dddbe15e0abc9730395eb14da74575103a7cbbec9c3824a2d8c39a',
        'remover': '306825981595ec17cc8e31f9d179c41caea0ddeac360d76b35586cea5afe1fb3',
    },
    'Q': {
        'encoder': '288fafc70165e1d1acef4707961e9fe5b85d8543b1b7cd604c4a708b670f72fb',
        'decoder': 'c7caaff48f4d4e66dc7065552b10fdf3cfe3dfbf6f0a43dc7aaec3783bd0a741',
        'remover': '00a46123013a7a8e8c2e1786c302aecc7c495316496ca41e570f46bb15a765f5',
    }
}

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"


# --- End of Configuration ---

class TrustMark(BaseWatermarkModel):
    """
    Wrapper for TrustMark ONNX models.
    Supports embedding, extraction, and removal of watermarks using separate ONNX models.
    Supports multiple model variants: C, Q, B, P.

    Reference:
        Tu Bui, Shruti Agarwal, John Collomosse. TrustMark: Universal Watermarking for Arbitrary Resolution Images. arXiv:2311.18297v1
    """

    def __init__(self, img_size: int = 256, bits_len: int = 100, model_type: str = 'Q', device: str = "cuda",
                 local_files_only: bool = False):
        """
        Initialize the TrustMark model.

        Args:
            img_size (int): Input image size (ignored; model handles arbitrary resolution).
            bits_len (int): Length of watermark (must be 100).
            model_type (str): Model variant ('C', 'Q', 'B', 'P').
            device (str): Device to run on ('cpu' or 'cuda').
        """
        model_type = model_type.upper()
        assert model_type in _MODEL_TYPES, f"model_type must be one of {_MODEL_TYPES}"
        modelname = f"TrustMark-{model_type}"
        super().__init__(bits_len, img_size, modelname)
        self.local_files_only = local_files_only
        self.bits_len = bits_len
        self.model_type = model_type

        # --- Download and Verify Models ---
        try:
            from huggingface_hub import hf_hub_download
            import sys

            sys.stdout.write(f"[{GREEN}WatermarkLab{RESET} INFO] ")
            sys.stdout.flush()

            # Define components to download
            components = [
                ("encoder", _ENCODER_FILE(model_type), _MODEL_SHA256[model_type]['encoder']),
                ("decoder", _DECODER_FILE(model_type), _MODEL_SHA256[model_type]['decoder']),
                ("remover", _REMOVER_FILE(model_type), _MODEL_SHA256[model_type]['remover'])
            ]

            for i, (name, filename, expected_sha256) in enumerate(components):
                sys.stdout.write(f"Downloading {modelname} {name}... ")
                sys.stdout.flush()
                local_path = hf_hub_download(repo_id=_REPO_ID,
                                             filename=filename,
                                             use_auth_token=True,
                                             local_files_only=self.local_files_only)
                sys.stdout.write(f"{GREEN}✓{RESET} | ")
                sys.stdout.write("Verifying SHA256... ")
                sys.stdout.flush()

                if not self._check_file_sha256(local_path, expected_sha256):
                    sys.stdout.write(f"{RED}FAILED{RESET}\n")
                    raise ValueError(f"SHA256 mismatch for {name} ({filename})")
                sys.stdout.write(f"{BLUE}✓{RESET} | ")

            sys.stdout.write(f"{modelname} loaded. {GREEN}🎉{RESET}\n")

            # Assign paths after successful download
            self._encoder_path = components[0][1]
            self._decoder_path = components[1][1]
            self._remover_path = components[2][1]
            # We'll use hf_hub_download result again in session init

        except ImportError:
            print(
                f"[{GREEN}WatermarkLab{RESET} ERROR] 'huggingface_hub' not installed. Use: pip install huggingface_hub")
            raise
        except Exception as e:
            print()
            raise RuntimeError(f"Failed to download TrustMark models from Hugging Face Hub: {e}") from e
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

        # Re-download or get cached paths via hf_hub_download for ONNX Runtime
        try:
            enc_path = hf_hub_download(_REPO_ID, _ENCODER_FILE(model_type), use_auth_token=True)
            dec_path = hf_hub_download(_REPO_ID, _DECODER_FILE(model_type), use_auth_token=True)
            rmv_path = hf_hub_download(_REPO_ID, _REMOVER_FILE(model_type), use_auth_token=True)
        except Exception as e:
            raise RuntimeError(f"Failed to resolve model paths: {e}")

        # Load ONNX sessions
        self._encoder_session = ort.InferenceSession(enc_path, providers=providers)
        self._decoder_session = ort.InferenceSession(dec_path, providers=providers)
        self._remover_session = ort.InferenceSession(rmv_path, providers=providers)

        # Define I/O names
        self._enc_input_cover = "cover"
        self._enc_input_secret = "secret"
        self._enc_output_stego = "stego"
        self._enc_output_residual = "residual"

        self._dec_input_stego = "stego"
        self._dec_output_secret = "decoded_secret"

        self._rm_input_stego = "stego"
        self._rm_output_clean = "clean"

        # Model-specific resolutions
        self._resolution_enc = 256
        self._resolution_dec = 224 if self.model_type == 'P' else 245
        self._resolution_rm = 256

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
        Embed 100-bit watermarks into cover images.

        Args:
            cover_list (List[ndarray]): List of RGB images [H, W, 3], uint8 [0, 255].
            secrets (List[List[int]]): List of 100-bit binary watermarks.

        Returns:
            Result: Watermarked images and embedded bits.
        """
        # Normalize to [-1, 1] and transpose to [B, 3, H, W]
        cover_batch = np.stack(cover_list).astype(np.float32)
        cover_input = (cover_batch / 127.5) - 1.0
        cover_input = np.transpose(cover_input, (0, 3, 1, 2))

        secret_batch = np.array(secrets, dtype=np.float32)

        feed_dict = {
            self._enc_input_cover: cover_input,
            self._enc_input_secret: secret_batch
        }

        stego_batch, _ = self._encoder_session.run([self._enc_output_stego, self._enc_output_residual], feed_dict)

        # Convert back to [0, 255] and HWC
        stego_rgb_batch = np.transpose(stego_batch, (0, 2, 3, 1))
        stego_rgb_batch = np.clip((stego_rgb_batch + 1.0) * 127.5, 0, 255).astype(np.uint8)
        stego_list = [img for img in stego_rgb_batch]

        return Result(stego_img=stego_list, emb_bits=secrets)

    def extract(self, stego_list: List[ndarray]) -> Result:
        """
        Extract 100-bit watermarks from stego images.

        Args:
            stego_list (List[ndarray]): Watermarked images [H, W, 3], uint8.

        Returns:
            Result: Extracted binary watermarks.
        """
        # Resize for decoder
        resized_batch = [cv2.resize(img, (self._resolution_dec, self._resolution_dec)) for img in stego_list]
        stego_batch = np.stack(resized_batch).astype(np.float32)
        stego_input = (stego_batch / 127.5) - 1.0
        stego_input = np.transpose(stego_input, (0, 3, 1, 2))

        decoder_input = {self._dec_input_stego: stego_input}
        decoded_batch = self._decoder_session.run([self._dec_output_secret], decoder_input)[0]
        ext_bits = (decoded_batch > 0.5).astype(np.int32).tolist()

        return Result(ext_bits=ext_bits)

    def recover(self, stego_list: List[ndarray]) -> Result:
        """
        Recover original images from watermarked images.

        Args:
            stego_list (List[ndarray]): Watermarked images [H, W, 3], uint8.

        Returns:
            Result: Recovered clean images.
        """
        stego_batch = np.stack(stego_list).astype(np.float32)
        stego_input = (stego_batch / 127.5) - 1.0
        stego_input = np.transpose(stego_input, (0, 3, 1, 2))

        remover_input = {self._rm_input_stego: stego_input}
        clean_batch = self._remover_session.run([self._rm_output_clean], remover_input)[0]

        clean_rgb_batch = np.transpose(clean_batch, (0, 2, 3, 1))
        clean_rgb_batch = np.clip((clean_rgb_batch + 1.0) * 127.5, 0, 255).astype(np.uint8)
        recovered_list = [img for img in clean_rgb_batch]

        return Result(rec_img=recovered_list)
