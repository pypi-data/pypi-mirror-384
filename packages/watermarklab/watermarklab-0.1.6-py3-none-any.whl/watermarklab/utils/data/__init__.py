# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT

import os
import json
import numpy as np
from PIL import Image
from typing import List, Tuple

from numpy import ndarray

from watermarklab.utils.basemodel import BaseDataset

__all__ = ["DataLoader", "DecodeDataLoader", "AttackTestRobustnessDataLoader",
           "AttackedImageDataLoader", "DecodeCleanCoverDataLoader"]


class DataLoader:
    """
    Generic data loader for watermarking experiments that batches samples from a BaseDataset.

    This class iterates over cover images or prompts and their associated secret bits
    in configurable batch sizes. It abstracts data access to support both:
      - Post-Generation Watermarking (PGW)
      - In-Generation Watermarking (IGW)

    Each batch yields:
      - List of cover images (as ndarray) or text prompts (as str)
      - List of secret bit sequences
      - List of cover indices (identifying which base image/prompt)
      - List of iteration indices (identifying which run of that image)

    Designed for seamless integration with `BaseDataset` and watermarking evaluation pipelines.
    """

    def __init__(self, dataset: BaseDataset, batch_size: int = 1):
        """
        Initialize the data loader.

        Args:
            dataset (BaseDataset): The dataset providing cover/prompt and secret data.
            batch_size (int): Number of samples per batch. Larger batches improve throughput
                              but consume more memory. Default: 1.
        """
        self.dataset = dataset
        self.batch_size = batch_size
        self.indices = list(range(len(dataset)))  # Linearized indices for all samples

    def __iter__(self):
        """
        Reset and return iterator for a new epoch.

        Returns:
            DataLoader: Self, ready to iterate.
        """
        self.current_index = 0
        return self

    def __next__(self) -> Tuple[List, List, List[int], List[int]]:
        """
        Yield the next batch of data.

        Returns:
            Tuple containing:
                - covers: List of cover images (ndarray) or prompts (str)
                - secrets: List of secret bit sequences (List[int] or similar)
                - cover_indices: List of base image/prompt indices
                - iter_indices: List of iteration indices (0 to iter_num-1)

        Raises:
            StopIteration: When all batches have been yielded.
        """
        if self.current_index >= len(self.indices):
            raise StopIteration

        batch_indices = self.indices[self.current_index:self.current_index + self.batch_size]
        self.current_index += self.batch_size

        batch = [self.dataset[idx] for idx in batch_indices]
        covers, secrets, cover_indices, iter_indices = zip(*batch)

        return list(covers), list(secrets), list(cover_indices), list(iter_indices)

    def __len__(self) -> int:
        """
        Compute total number of batches per epoch.

        Uses ceiling division to include partial final batch.

        Returns:
            int: Total batch count.
        """
        return (len(self.dataset) + self.batch_size - 1) // self.batch_size


class DecodeDataLoader:
    """
    Simple image loader for decoding-only tasks.

    Loads batches of stego images from disk for watermark extraction.
    Assumes no ground-truth secrets or cover images are needed — standalone decoding.
    """

    def __init__(self, image_paths: List[str], batch_size: int = 1):
        """
        Initialize image loader.

        Args:
            image_paths (List[str]): List of file paths to stego images.
            batch_size (int): Number of images per batch. Default: 1.
        """
        self.image_paths = image_paths
        self.batch_size = batch_size
        self.num_images = len(image_paths)
        self.current_index = 0

    def __iter__(self):
        """
        Reset iterator for reuse.

        Returns:
            DecodeDataLoader: Self.
        """
        self.current_index = 0
        return self

    def __next__(self) -> Tuple[List[ndarray], List[str]]:
        """
        Load and return next batch of images.

        Images are loaded as RGB, converted to float32 NumPy arrays (H×W×C).

        Returns:
            Tuple containing:
                - batch_images: List of image arrays
                - path_list: Corresponding file paths

        Raises:
            StopIteration: When all images processed.
        """
        if self.current_index >= self.num_images:
            raise StopIteration

        batch_paths = self.image_paths[self.current_index:self.current_index + self.batch_size]
        self.current_index += self.batch_size

        batch_images = []
        path_list = []

        for path in batch_paths:
            image = Image.open(path).convert("RGB")
            image_array = np.float32(image)
            batch_images.append(image_array)
            path_list.append(path)

        return batch_images, path_list

    def __len__(self) -> int:
        """
        Return total number of batches.

        Uses ceiling division to account for final partial batch.

        Returns:
            int: Total batch count.
        """
        return (self.num_images + self.batch_size - 1) // self.batch_size


class AttackTestRobustnessDataLoader:
    """
    Data loader for evaluating watermark robustness under simulated attacks.

    Automatically discovers and loads structured data from disk. Each sample provides:
      - Original cover image
      - Clean stego image (watermarked)
      - Original secret message (ground truth)
      - Output directory path for saving attacked/noised image

    Expected directory structure:
        images_dir/
            image_1/
                iter_1/
                    cover.png (or clean.png)
                    stego.png
                    secret.json
                iter_2/
                    ...
            image_2/
                ...

        noise_dir/ (output)
            image_1/
                iter_1/   ← where noised.png will be saved
                iter_2/
                    ...

    Eliminates need to manually specify image/iteration counts — scans structure automatically.
    """

    def __init__(self, noise_dir: str, images_dir: str, batch_size: int = 1):
        """
        Initialize loader by scanning directory structure.

        Args:
            noise_dir (str): Root directory to save attacked/noised images.
            images_dir (str): Root directory containing original cover/stego/secret data.
            batch_size (int, optional): Samples per batch. Default: 1.

        Raises:
            FileNotFoundError: If images_dir does not exist.
            ValueError: If no valid 'image_X/iter_Y' structure found.
        """
        self.org_secret_paths: List[str] = []
        self.cover_clean_img_paths: List[str] = []
        self.stego_clean_img_paths: List[str] = []
        self.noise_output_dirs: List[str] = []

        if not os.path.exists(images_dir):
            raise FileNotFoundError(f"Source directory not found: {images_dir}")

        # Discover image directories
        image_dirs = sorted([d for d in os.listdir(images_dir) if d.startswith("image_")])
        if not image_dirs:
            raise ValueError(f"No 'image_*' directories found in {images_dir}")

        # Discover iterations from first image dir
        first_image_path = os.path.join(images_dir, image_dirs[0])
        iter_dirs = sorted([d for d in os.listdir(first_image_path) if d.startswith("iter_")])
        if not iter_dirs:
            raise ValueError(f"No 'iter_*' directories found in {first_image_path}")

        total_images_num = len(image_dirs)
        iter_num = len(iter_dirs)

        # Build full path lists
        for image_index in range(total_images_num):
            for iter_index in range(iter_num):
                secret_path = os.path.join(
                    images_dir,
                    f"image_{image_index + 1}",
                    f"iter_{iter_index + 1}",
                    "secret.json"
                )
                cover_path = os.path.join(
                    images_dir,
                    f"image_{image_index + 1}",
                    f"iter_{iter_index + 1}",
                    "cover.png"
                )
                clean_path = os.path.join(
                    images_dir,
                    f"image_{image_index + 1}",
                    f"iter_{iter_index + 1}",
                    "clean.png"
                )
                stego_clean_path = os.path.join(
                    images_dir,
                    f"image_{image_index + 1}",
                    f"iter_{iter_index + 1}",
                    "stego.png"
                )
                noise_output_dir = os.path.join(
                    noise_dir,
                    f"image_{image_index + 1}",
                    f"iter_{iter_index + 1}"
                )

                # Add to path lists
                self.org_secret_paths.append(secret_path)
                if os.path.exists(cover_path):
                    self.cover_clean_img_paths.append(cover_path)
                else:
                    self.cover_clean_img_paths.append(clean_path)
                self.stego_clean_img_paths.append(stego_clean_path)
                self.noise_output_dirs.append(noise_output_dir)

        if not self.org_secret_paths:
            raise ValueError("No complete data samples found.")

        self.num_images = len(self.org_secret_paths)
        self.batch_size = batch_size
        self.current_index = 0

    def __iter__(self) -> 'AttackTestRobustnessDataLoader':
        """
        Reset iterator for reuse.

        Returns:
            Self as iterator.
        """
        self.current_index = 0
        return self

    def __next__(self) -> Tuple[List[np.ndarray], List[np.ndarray], List[List], List[str]]:
        """
        Load next batch of cover, stego, secret, and output paths.

        Images loaded as RGB float32 arrays.

        Returns:
            Tuple containing:
                - cover_images: List of original cover images
                - stego_images: List of watermarked stego images
                - secret_messages: List of original secrets (from JSON)
                - batch_noise_dirs: List of output directories for attacked images

        Raises:
            StopIteration: When all batches processed.
            IOError: If any file fails to load.
        """
        if self.current_index >= self.num_images:
            raise StopIteration

        batch_cover_paths = self.cover_clean_img_paths[self.current_index:self.current_index + self.batch_size]
        batch_stego_paths = self.stego_clean_img_paths[self.current_index:self.current_index + self.batch_size]
        batch_secret_paths = self.org_secret_paths[self.current_index:self.current_index + self.batch_size]
        batch_noise_dirs = self.noise_output_dirs[self.current_index:self.current_index + self.batch_size]
        self.current_index += self.batch_size

        cover_images = []
        stego_images = []
        secret_messages = []

        for cover_path, stego_path, secret_path in zip(batch_cover_paths, batch_stego_paths, batch_secret_paths):
            # Load cover
            try:
                cover_pil = Image.open(cover_path).convert("RGB")
                cover = np.float32(cover_pil)
            except Exception as e:
                raise IOError(f"Failed to load cover image {cover_path}: {e}")
            cover_images.append(cover)

            # Load stego
            try:
                stego_pil = Image.open(stego_path).convert("RGB")
                stego = np.float32(stego_pil)
            except Exception as e:
                raise IOError(f"Failed to load stego image {stego_path}: {e}")
            stego_images.append(stego)

            # Load secret
            try:
                with open(secret_path, "r") as f:
                    secret = json.load(f)
            except Exception as e:
                raise IOError(f"Failed to load secret file {secret_path}: {e}")
            secret_messages.append(secret)

        return cover_images, stego_images, secret_messages, batch_noise_dirs

    def __len__(self) -> int:
        """
        Compute total number of batches.

        Returns:
            int: Batch count (ceiling division).
        """
        return (self.num_images + self.batch_size - 1) // self.batch_size


class AttackedImageDataLoader:
    """
    Loader for decoding watermarks from previously attacked/noised images.

    Loads:
      - Attacked stego images (noised.png)
      - Corresponding original secrets (secret.json)

    Assumes same directory structure as AttackTestRobustnessDataLoader.

    Used in second phase of robustness testing: after attacks are applied and saved to disk.
    """

    def __init__(self, attacked_stego_dir: str, image_dir: str, batch_size: int = 1):
        """
        Initialize loader for attacked images.

        Args:
            attacked_stego_dir (str): Directory containing 'noised.png' files.
            image_dir (str): Directory containing original 'secret.json' files.
            batch_size (int): Samples per batch. Default: 1.

        Raises:
            FileNotFoundError: If attacked_stego_dir not found.
            ValueError: If no valid 'image_X/iter_Y' structure found.
        """
        self.original_secret_paths: List[str] = []
        self.attacked_stego_paths: List[str] = []

        if not os.path.exists(attacked_stego_dir):
            raise FileNotFoundError(f"Source directory not found: {attacked_stego_dir}")

        # Discover structure
        image_dirs = sorted([d for d in os.listdir(attacked_stego_dir) if d.startswith("image_")])
        if not image_dirs:
            raise ValueError(f"No 'image_*' directories found in {attacked_stego_dir}")

        first_image_path = os.path.join(attacked_stego_dir, image_dirs[0])
        iter_dirs = sorted([d for d in os.listdir(first_image_path) if d.startswith("iter_")])
        if not iter_dirs:
            raise ValueError(f"No 'iter_*' directories found in {first_image_path}")

        total_images_num = len(image_dirs)
        iter_num = len(iter_dirs)

        # Build path lists
        for image_index in range(total_images_num):
            for iter_index in range(iter_num):
                secret_path = os.path.join(
                    image_dir,
                    f"image_{image_index + 1}",
                    f"iter_{iter_index + 1}",
                    "secret.json"
                )
                attacked_stego_path = os.path.join(
                    attacked_stego_dir,
                    f"image_{image_index + 1}",
                    f"iter_{iter_index + 1}",
                    "noised.png"
                )

                self.original_secret_paths.append(secret_path)
                self.attacked_stego_paths.append(attacked_stego_path)

        if not self.attacked_stego_paths or not self.original_secret_paths:
            raise ValueError("No complete data samples found.")

        self.num_images = len(self.original_secret_paths)
        self.batch_size = batch_size
        self.current_index = 0

    def __iter__(self) -> 'AttackedImageDataLoader':
        """
        Reset iterator.

        Returns:
            Self as iterator.
        """
        self.current_index = 0
        return self

    def __next__(self) -> Tuple[List[List], List[np.ndarray], List[str]]:
        """
        Load next batch of attacked images and their original secrets.

        Returns:
            Tuple containing:
                - secret_messages: List of original secrets (ground truth)
                - attacked_stego_images: List of attacked image arrays (float32, RGB)
                - batch_attacked_stego_paths: List of corresponding file paths

        Raises:
            StopIteration: When all batches processed.
            IOError: If any file fails to load.
        """
        if self.current_index >= self.num_images:
            raise StopIteration

        batch_attacked_stego_paths = self.attacked_stego_paths[self.current_index:self.current_index + self.batch_size]
        batch_original_secret_paths = self.original_secret_paths[self.current_index:self.current_index + self.batch_size]
        self.current_index += self.batch_size

        attacked_stego_images = []
        secret_messages = []
        attacked_stego_paths = []

        for secret_path, stego_path in zip(batch_original_secret_paths, batch_attacked_stego_paths):
            # Load attacked image
            try:
                stego_pli = Image.open(stego_path).convert("RGB")
                stego = np.float32(stego_pli)
                attacked_stego_images.append(stego)
                attacked_stego_paths.append(os.path.dirname(stego_path))
            except Exception as e:
                raise IOError(f"Failed to load attacked stego image {stego_path}: {e}")
            # Load secret
            try:
                with open(secret_path, "r") as f:
                    secret = json.load(f)
            except Exception as e:
                raise IOError(f"Failed to load secret file {secret_path}: {e}")
            secret_messages.append(secret)

        return secret_messages, attacked_stego_images, attacked_stego_paths

    def __len__(self) -> int:
        """
        Compute total number of batches.

        Returns:
            int: Batch count (ceiling division).
        """
        return (self.num_images + self.batch_size - 1) // self.batch_size


class DecodeCleanCoverDataLoader:
    """
    Data loader for evaluating watermark extraction on clean (unattacked) cover images.

    Loads:
      - Clean/cover images (cover.png or clean.png)
      - Corresponding original secrets (secret.json)

    Purpose:
      - Establish baseline performance of watermark decoder on pristine images
      - Compute metrics like BER, accuracy without noise/attacks
      - Used in robustness testing as reference point

    Assumes directory structure:
        cover_dir/
            image_1/
                iter_1/
                    cover.png (or clean.png)
                    secret.json
                iter_2/
                    ...
            image_2/
                ...
    """

    def __init__(self,
                 cover_dir: str,
                 img_len: int,
                 iter_len: int,
                 batch_size: int = 1):
        """
        Initialize loader for clean cover images.

        Args:
            cover_dir (str): Root directory containing image folders.
            img_len (int): Number of distinct images to process.
            iter_len (int): Number of iterations per image.
            batch_size (int): Samples per batch. Default: 1.
        """
        self.org_secret_paths = []
        self.img_paths = []

        # Build path lists
        for image_index in range(img_len):
            for iter_index in range(iter_len):
                secret_path = os.path.join(
                    cover_dir,
                    f"image_{image_index + 1}",
                    f"iter_{iter_index + 1}",
                    "secret.json"
                )
                cover_path = os.path.join(
                    cover_dir,
                    f"image_{image_index + 1}",
                    f"iter_{iter_index + 1}",
                    "cover.png"
                )
                clean_path = os.path.join(
                    cover_dir,
                    f"image_{image_index + 1}",
                    f"iter_{iter_index + 1}",
                    "clean.png"
                )

                self.org_secret_paths.append(secret_path)

                if os.path.exists(cover_path):
                    self.img_paths.append(cover_path)
                elif os.path.exists(clean_path):
                    self.img_paths.append(clean_path)
                else:
                    print(f"Warning: No cover/clean image found for {secret_path}")

        self.num_images = len(self.img_paths)
        self.batch_size = batch_size
        self.current_index = 0

    def __iter__(self):
        """
        Reset iterator.

        Returns:
            Self as iterator.
        """
        self.current_index = 0
        return self

    def __next__(self) -> Tuple[List[List], List[ndarray]]:
        """
        Load next batch of clean images and their secrets.

        Returns:
            Tuple containing:
                - secret_list: List of original secret bit sequences
                - batch_cover_clean: List of clean image arrays (float32, RGB)

        Raises:
            StopIteration: When all samples processed.
            FileNotFoundError: If required files missing.
        """
        if self.current_index >= self.num_images:
            raise StopIteration

        batch_image_paths = self.img_paths[self.current_index:self.current_index + self.batch_size]
        batch_secret_paths = self.org_secret_paths[self.current_index:self.current_index + self.batch_size]
        self.current_index += self.batch_size

        secret_list = []
        batch_cover_clean = []

        for image_path, secret_path in zip(batch_image_paths, batch_secret_paths):
            # Load image
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            image = Image.open(image_path).convert("RGB")
            image_array = np.float32(image)
            batch_cover_clean.append(image_array)

            # Load secret
            if not os.path.exists(secret_path):
                raise FileNotFoundError(f"Secret file not found: {secret_path}")
            with open(secret_path, "r") as f:
                secret_data = json.load(f)
                secret_list.append(secret_data)

        return secret_list, batch_cover_clean

    def __len__(self) -> int:
        """
        Compute total number of batches.

        Returns:
            int: Batch count (ceiling division).
        """
        return (self.num_images + self.batch_size - 1) // self.batch_size