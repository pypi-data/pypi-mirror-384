# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT
import torch
import hashlib
import numpy as np
from torch import nn
from typing import List, Any
from numpy import ndarray
from watermarklab.utils.basemodel import BaseWatermarkModel, Result

__all__ = ["iSteganoGAN"]

# --- Configuration ---
# Hugging Face repository ID
from watermarklab.utils.parameters import LOAD_FROM_LOCAL

_REPO_ID = "chenoly/watermarklab"  # Update if different

# Filenames for encoder and decoder per bpp
_ENCODER_FILES = {
    1: "watermarks/PGWs/pretrained_models/isteganogan/encoder_1bpp.pth",
    2: "watermarks/PGWs/pretrained_models/isteganogan/encoder_2bpp.pth",
    3: "watermarks/PGWs/pretrained_models/isteganogan/encoder_3bpp.pth"
}
_DECODER_FILES = {
    1: "watermarks/PGWs/pretrained_models/isteganogan/decoder_1bpp.pth",
    2: "watermarks/PGWs/pretrained_models/isteganogan/decoder_2bpp.pth",
    3: "watermarks/PGWs/pretrained_models/isteganogan/decoder_3bpp.pth"
}

# Expected SHA256 checksums
_ENCODER_SHA256 = {
    1: "060b6a46631b8cdd6ddfffa0a329bffbe17b5782a60b553f798e807b04a0e939",
    2: "5fbef95017b818c29e68af3e840cf0aa7c69cb1a1d2878f1d457e008a3496882",
    3: "fef9ef53e66c72c835ac53ae19059f9b9038cf03a9a62b969eebf6fe00ee3aee",
}
_DECODER_SHA256 = {
    1: "2aec23fcd224d6287e07d83be5e5617be3d9ca3659a9fabd3a11c7159dbdbb8c",
    2: "7776a2fd172938bad7c26255890a4481f6528b082eefc43b4e68725e6f401267",
    3: "ea299cc309ee08c9416012c2430651318400bfcb665bd31ab5b554fd853bdb25",
}

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"


# --- End of Configuration ---

class iSteganoGAN(BaseWatermarkModel):
    """
    improved SteganoGAN (iSteganoGAN) via enhanced optimization (Author: Jiale Chen et.al. <chenoly@outlook.com>).
    Furthermore, For the extract accuracy. it uses L-BFGS for more accurate and stable watermark extraction, just like following methods:

    Outperforms L-BFGS-based steganography methods such as:
    - FNNS (Fixed Neural Network Steganography): https://openreview.net/pdf?id=hcMvApxGSzZ
    - LISO (Learning Iterative Neural Optimizers for Image Steganography): https://arxiv.org/abs/2303.16206

    iSteganoGAN achieves superior extraction accuracy and visual quality.
    """

    def __init__(self, bpp: int = 1, modelname: str = "iSteganoGAN", device: str = "cuda"):
        """
        Initialize the iSteganoGAN model.

        Args:
            bpp (int): Bits per pixel (1, 2, or 3).
            modelname (str): Model identifier.
            device (str): Device to run on ('cpu' or 'cuda').
        """
        super().__init__(int(bpp * 512), 512, modelname)
        assert bpp in [1, 2, 3], "bpp must be 1, 2, or 3"
        self.bpp = bpp
        self.device = device

        # Initialize network components
        self.encoder = BasicEncoder(self.bpp, hidden_size=32)
        self.decoder = DenseDecoder(self.bpp, hidden_size=32)

        # --- Download and Verify Models ---
        try:
            from huggingface_hub import hf_hub_download
            import sys

            sys.stdout.write(f"[{GREEN}WatermarkLab{RESET} INFO] ")
            sys.stdout.flush()

            # Select model files based on bpp
            enc_filename = _ENCODER_FILES[self.bpp]
            dec_filename = _DECODER_FILES[self.bpp]
            enc_sha256 = _ENCODER_SHA256[self.bpp]
            dec_sha256 = _DECODER_SHA256[self.bpp]

            # Download encoder
            sys.stdout.write(f"Downloading iSteganoGAN encoder ({self.bpp}bpp)... ")
            sys.stdout.flush()
            enc_path = hf_hub_download(repo_id=_REPO_ID, filename=enc_filename, use_auth_token=True)
            sys.stdout.write(f"{GREEN}✓{RESET} | ")
            sys.stdout.write("Verifying SHA256... ")
            sys.stdout.flush()

            if not self._check_file_sha256(enc_path, enc_sha256):
                sys.stdout.write(f"{RED}FAILED{RESET}\n")
                raise ValueError(f"SHA256 mismatch for encoder: {enc_path}")
            sys.stdout.write(f"{BLUE}✓{RESET} | ")

            # Download decoder
            sys.stdout.write("Downloading decoder... ")
            sys.stdout.flush()
            dec_path = hf_hub_download(repo_id=_REPO_ID,
                                       filename=dec_filename,
                                       use_auth_token=True,
                                       local_files_only=LOAD_FROM_LOCAL)
            sys.stdout.write(f"{GREEN}✓{RESET} | ")
            sys.stdout.write("Verifying SHA256... ")
            sys.stdout.flush()

            if not self._check_file_sha256(dec_path, dec_sha256):
                sys.stdout.write(f"{RED}FAILED{RESET}\n")
                raise ValueError(f"SHA256 mismatch for decoder: {dec_path}")
            sys.stdout.write(f"{BLUE}✓{RESET} | ")
            sys.stdout.write(f"iSteganoGAN models loaded. {GREEN}🎉{RESET}\n")

            # Load state dicts
            self.encoder.load_state_dict(torch.load(enc_path, map_location=device))
            self.decoder.load_state_dict(torch.load(dec_path, map_location=device))

        except ImportError:
            print(f"[{RED}WatermarkLab{RESET} ERROR] 'huggingface_hub' not installed. Use: pip install huggingface_hub")
            raise
        except Exception as e:
            print()
            raise RuntimeError(f"Failed to download iSteganoGAN models from Hugging Face Hub: {e}") from e
        # --- End of Download Process ---

        # Move models to device
        self.encoder.to(self.device).eval()
        self.decoder.to(self.device).eval()

        # Log device info
        gpu_id = self._get_gpu_id(device)
        if gpu_id >= 0:
            print(f"[{GREEN}WatermarkLab{RESET} INFO] iSteganoGAN model loaded on cuda:{gpu_id}.")
        else:
            print(f"[{GREEN}WatermarkLab{RESET} INFO] iSteganoGAN model loaded on CPU.")

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
        """Extract GPU ID from device string."""
        dev = torch.device(device)
        return dev.index if dev.type == "cuda" and dev.index is not None else 0 if dev.type == "cuda" else -1

    def LBFGS_optimize(self, stego_image: torch.Tensor, secret: torch.Tensor, epsilon: float = 0.3,
                       steps: int = 2000, max_iterations: int = 10, learning_rate: float = 1.0,
                       quantize: bool = True) -> torch.Tensor:
        """
        Optimize stego image using L-BFGS for better extraction accuracy.

        Args:
            stego_image (torch.Tensor): Initial stego image.
            secret (torch.Tensor): Secret to embed.
            epsilon (float): Max perturbation.
            steps (int): Total optimization steps.
            max_iterations (int): Max iterations per L-BFGS step.
            learning_rate (float): L-BFGS learning rate.
            quantize (bool): Whether to quantize output.

        Returns:
            torch.Tensor: Optimized stego image.
        """
        adv_image = stego_image.clone().detach()
        criterion = torch.nn.BCEWithLogitsLoss(reduction="sum")
        adv_image_q = adv_image.clone().detach()
        for _ in range(steps // max_iterations):
            adv_image.requires_grad = True
            optimizer = torch.optim.LBFGS([adv_image], lr=learning_rate, max_iter=max_iterations)

            def closure():
                optimizer.zero_grad()
                outputs = self.decoder(adv_image)
                loss = criterion(outputs, secret)
                loss.backward()
                return loss

            optimizer.step(closure)
            delta = torch.clamp(adv_image - stego_image, -epsilon, epsilon)
            adv_image = torch.clamp(stego_image + delta, 0, 1).detach()

            adv_image_q = torch.round(adv_image * 255) / 255.0 if quantize else adv_image
            error = 1 - (self.decoder(adv_image_q) >= 0).eq(secret >= 0.5).sum().float() / secret.numel()
            if error < 0.0005:
                epsilon = 0.7
            if error == 0:
                break

        return adv_image_q

    def embed(self, cover_list: List[ndarray], secrets: List[List[Any]], steps: int = 2000) -> Result:
        """
        Embed message into cover images.

        Args:
            cover_list (List[ndarray]): List of RGB images [H, W, 3], uint8 [0,255].
            secrets (List[List[int]]): List of binary watermarks.
            steps (int): Number of L-BFGS optimization steps.

        Returns:
            Result: Watermarked images and embedded bits.
        """
        stego_list = []
        for cover, secret in zip(cover_list, secrets):
            cover_tensor = torch.as_tensor(cover).permute(2, 0, 1).unsqueeze(0).float().to(self.device) / 255.0
            secret_tensor = torch.tensor(secret, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0).to(self.device)
            stego = self.encoder(cover_tensor, secret_tensor)
            stego = torch.clamp(stego, 0, 1)
            adv_image = self.LBFGS_optimize(stego, secret_tensor, steps=steps)
            stego_np = adv_image[0].permute(1, 2, 0).cpu().numpy()
            stego_list.append((stego_np * 255).astype(np.uint8))
        return Result(stego_img=stego_list, emb_bits=secrets)

    @torch.inference_mode()
    def extract(self, stego_list: List[ndarray]) -> Result:
        """
        Extract watermarks from stego images.

        Args:
            stego_list (List[ndarray]): Watermarked images [H, W, 3], uint8.

        Returns:
            Result: Extracted binary watermarks.
        """
        ext_secrets = []
        for stego in stego_list:
            stego_tensor = torch.as_tensor(stego).permute(2, 0, 1).unsqueeze(0).float().to(self.device) / 255.0
            decoded = self.decoder(stego_tensor).squeeze(0).permute(1, 2, 0)
            bits = (decoded > 0).int().cpu().tolist()
            ext_secrets.append(bits)
        return Result(ext_bits=ext_secrets)

    def recover(self, stego_list: List[ndarray]) -> Result:
        """
        Recover original image (not supported).

        Args:
            stego_list (List[ndarray]): Watermarked images.

        Returns:
            Result: NotImplemented.

        Raises:
            NotImplementedError: Recovery not supported.
        """
        raise NotImplementedError("Recovery is not supported by iSteganoGAN.")


# -*- coding: utf-8 -*-

class BasicDecoder(nn.Module):
    """
    The BasicDecoder module takes an steganographic image and attempts to decode
    the embedded data tensor.

    Input: (N, 3, H, W)
    Output: (N, D, H, W)
    """

    def _conv2d(self, in_channels, out_channels):
        return nn.Conv2d(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=3,
            padding=1
        )

    def _build_models(self):
        self.layers = nn.Sequential(
            self._conv2d(3, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size),

            self._conv2d(self.hidden_size, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size),

            self._conv2d(self.hidden_size, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size),

            self._conv2d(self.hidden_size, self.data_depth)
        )

        return [self.layers]

    def __init__(self, data_depth, hidden_size):
        super().__init__()
        self.version = '1'
        self.data_depth = data_depth
        self.hidden_size = hidden_size

        self._models = self._build_models()

    def upgrade_legacy(self):
        """Transform legacy pretrained models to make them usable with new code versions."""
        # Transform to version 1
        if not hasattr(self, 'version'):
            self._models = [self.layers]

            self.version = '1'

    def forward(self, x):
        x = self._models[0](x)

        if len(self._models) > 1:
            x_list = [x]
            for layer in self._models[1:]:
                x = layer(torch.cat(x_list, dim=1))
                x_list.append(x)

        return x


class DenseDecoder(BasicDecoder):
    """
    The DenseDecoder module takes an steganographic image and attempts to decode
    the embedded data tensor.

    Input: (N, 3, H, W)
    Output: (N, D, H, W)
    """

    def _build_models(self):
        self.conv1 = nn.Sequential(
            self._conv2d(3, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size)
        )

        self.conv2 = nn.Sequential(
            self._conv2d(self.hidden_size, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size)
        )

        self.conv3 = nn.Sequential(
            self._conv2d(self.hidden_size * 2, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size)
        )

        self.conv4 = nn.Sequential(self._conv2d(self.hidden_size * 3, self.data_depth))

        return self.conv1, self.conv2, self.conv3, self.conv4

    def upgrade_legacy(self):
        """Transform legacy pretrained models to make them usable with new code versions."""
        # Transform to version 1
        if not hasattr(self, 'version'):
            self._models = [
                self.conv1,
                self.conv2,
                self.conv3,
                self.conv4
            ]

            self.version = '1'


# -*- coding: utf-8 -*-
class BasicEncoder(nn.Module):
    """
    The BasicEncoder module takes an cover image and a data tensor and combines
    them into a steganographic image.

    Input: (N, 3, H, W), (N, D, H, W)
    Output: (N, 3, H, W)
    """

    add_image = False

    def _conv2d(self, in_channels, out_channels):
        return nn.Conv2d(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=3,
            padding=1
        )

    def _build_models(self):
        self.features = nn.Sequential(
            self._conv2d(3, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size),
        )
        self.layers = nn.Sequential(
            self._conv2d(self.hidden_size + self.data_depth, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size),
            self._conv2d(self.hidden_size, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size),
            self._conv2d(self.hidden_size, 3),
            nn.Tanh(),
        )
        return self.features, self.layers

    def __init__(self, data_depth, hidden_size):
        super().__init__()
        self.version = '1'
        self.data_depth = data_depth
        self.hidden_size = hidden_size
        self._models = self._build_models()

    def upgrade_legacy(self):
        """Transform legacy pretrained models to make them usable with new code versions."""
        # Transform to version 1
        if not hasattr(self, 'version'):
            self.version = '1'

    def forward(self, image, data):
        x = self._models[0](image)
        x_list = [x]

        for layer in self._models[1:]:
            x = layer(torch.cat(x_list + [data], dim=1))
            x_list.append(x)

        if self.add_image:
            x = image + x

        return x


class ResidualEncoder(BasicEncoder):
    """
    The ResidualEncoder module takes an cover image and a data tensor and combines
    them into a steganographic image.

    Input: (N, 3, H, W), (N, D, H, W)
    Output: (N, 3, H, W)
    """

    add_image = True

    def _build_models(self):
        self.features = nn.Sequential(
            self._conv2d(3, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size),
        )
        self.layers = nn.Sequential(
            self._conv2d(self.hidden_size + self.data_depth, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size),
            self._conv2d(self.hidden_size, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size),
            self._conv2d(self.hidden_size, 3),
        )
        return self.features, self.layers


class DenseEncoder(BasicEncoder):
    """
    The DenseEncoder module takes an cover image and a data tensor and combines
    them into a steganographic image.

    Input: (N, 3, H, W), (N, D, H, W)
    Output: (N, 3, H, W)
    """

    add_image = True

    def _build_models(self):
        self.conv1 = nn.Sequential(
            self._conv2d(3, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size),
        )
        self.conv2 = nn.Sequential(
            self._conv2d(self.hidden_size + self.data_depth, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size),
        )
        self.conv3 = nn.Sequential(
            self._conv2d(self.hidden_size * 2 + self.data_depth, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size),
        )
        self.conv4 = nn.Sequential(
            self._conv2d(self.hidden_size * 3 + self.data_depth, 3)
        )

        return self.conv1, self.conv2, self.conv3, self.conv4
