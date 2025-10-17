# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT
import os
import glob
import json
import random
import hashlib
import numpy as np
from typing import Tuple, List
from PIL import Image, ImageOps
from watermarklab.utils.basemodel import BaseDataset

# --------------------------------------------------------------------
# Configuration: Hugging Face Repository
# --------------------------------------------------------------------
_REPO_ID = "chenoly/watermarklab"

# Dataset file mappings and expected SHA256
_DATASET_CONFIG = {
    "usc_sipi": {
        "filename": "datasets/USC-SIPI.zip",
        "sha256": "7e1b679ceb71f810c8019a58df3e7cd7a38e61f1d43ee0275ea2c09102ec8b70",
        "folder": "USC-SIPI",
    },
    "kodak24": {
        "filename": "datasets/KODAK24.zip",
        "sha256": "a0df8e6e2fd3b268042adf2c04ca2b16badc721efd86776cb24cc816819a3a35",
        "folder": "KODAK24",
    },
    "coco_prompts": {
        "filename": "datasets/MS-COCO-PROMPTS.zip",
        "sha256": "f7791519211abc8d1c302a0b3c2bc327657b5676c8f09f9577f40f2234f9b354",
        "folder": "MS-COCO-PROMPTS",
    },
    "mscoco2017val": {
        "filename": "datasets/MSCOCO2017VAL.zip",
        "sha256": "4f7e2ccb2866ec5041993c9cf2a952bbed69647b115d0f74da7ce8f4bef82f05",
        "folder": "MS-COCO-2017-VAL",
    }
}

# Import logger
from watermarklab.utils.logger import logger


def _download_and_extract_hf(repo_id: str, filename: str, sha256: str, target_folder: str, local_files_only: bool = False) -> str:
    """
    Download a dataset ZIP from Hugging Face and extract it if not already present.
    Uses hf_hub_download for caching and integrity.

    Args:
        repo_id (str): Hugging Face repo ID.
        filename (str): Path within repo.
        sha256 (str): Expected SHA256 hash.
        target_folder (str): Local folder name to extract into.

    Returns:
        str: Path to extracted folder.
    """
    try:
        from huggingface_hub import hf_hub_download
        import sys
        import os
        from zipfile import ZipFile

        RED = "\033[91m"
        GREEN = "\033[92m"
        BLUE = "\033[94m"
        RESET = "\033[0m"

        basename = os.path.basename(filename)

        # Start progress on one line
        sys.stdout.write(f"[{GREEN}WatermarkLab{RESET} INFO] ")
        sys.stdout.flush()

        # Step 1: Download
        sys.stdout.write(f"Downloading {basename}... ")
        sys.stdout.flush()
        try:
            archive_path = hf_hub_download(repo_id=repo_id, filename=filename, use_auth_token=True, local_files_only=local_files_only)
            sys.stdout.write(f"{GREEN}✓{RESET} | ")
        except Exception as e:
            sys.stdout.write(f"{RED}✗{RESET}\n")
            logger.error(f"Failed to download {basename}: {e}")
            raise RuntimeError(f"Failed to download {basename}: {e}")

        # Step 2: Verify SHA256
        sys.stdout.write("Verifying SHA256... ")
        sys.stdout.flush()
        if not _check_sha256(archive_path, sha256):
            sys.stdout.write(f"{RED}✗{RESET}\n")
            logger.error(f"SHA256 mismatch for {filename}")
            raise ValueError(f"SHA256 mismatch for {filename}")
        sys.stdout.write(f"{BLUE}✓{RESET} | ")

        # Step 3: Extract
        extract_path = os.path.join(os.path.dirname(archive_path), target_folder)
        if os.path.exists(extract_path) and os.listdir(extract_path):
            sys.stdout.write(f"Using cached {target_folder}/ {GREEN}✓{RESET} | ")
        else:
            sys.stdout.write("Extracting... ")
            sys.stdout.flush()
            os.makedirs(extract_path, exist_ok=True)
            try:
                with ZipFile(archive_path, 'r') as zipf:
                    zipf.extractall(extract_path)
                sys.stdout.write(f"{GREEN}✓{RESET} | ")
            except Exception as e:
                sys.stdout.write(f"{RED}✗{RESET}\n")
                logger.error(f"Failed to extract {basename}: {e}")
                raise RuntimeError(f"Failed to extract {basename}: {e}")

        # Final success
        sys.stdout.write(f"{GREEN}Done.{RESET}\n")
        return extract_path

    except ImportError:
        sys.stdout.write(f"\n[ERROR] Missing 'huggingface_hub'. Install with: pip install huggingface_hub\n")
        logger.error("Missing 'huggingface_hub'. Install with: pip install huggingface_hub")
        raise ImportError("huggingface_hub is required to download datasets.")
    except Exception as e:
        # Ensure error breaks line for clarity
        if not str(e).startswith("\n"):
            sys.stdout.write("\n")
        raise e


def _check_sha256(file_path: str, expected_hash: str) -> bool:
    """Verify SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest().lower() == expected_hash.lower()


class USC_SIPI(BaseDataset):
    """
    USC-SIPI dataset loader.
    Loads only RGB images from the 'misc' subset.
    Automatically downloads and extracts from Hugging Face Hub.
    """

    def __init__(self, im_size: int, bit_len: int, iter_num: int = 1, dataset_name: str = "USC_SIPI", local_files_only: bool = False):
        super().__init__(im_size, bit_len, iter_num, dataset_name)
        self.im_size = im_size
        self.bit_length = bit_len
        config = _DATASET_CONFIG["usc_sipi"]
        self.root_path = _download_and_extract_hf(_REPO_ID, config["filename"], config["sha256"], config["folder"], local_files_only)
        self.covers = []
        self.load_paths()

    def load_paths(self):
        patterns = ['*.tiff']
        self.covers = []
        for pattern in patterns:
            for img_path in glob.glob(os.path.join(self.root_path, "**", pattern), recursive=True):
                try:
                    with Image.open(img_path) as img:
                        if img.mode == 'RGB':
                            self.covers.append(img_path)
                except Exception:
                    continue
        random.seed(99)
        random.shuffle(self.covers)
        logger.info(f"[USC_SIPI] Loaded {len(self.covers)} RGB images.")

    def load_data(self, index: int) -> Tuple[np.ndarray, List[int]]:
        if index >= len(self.covers):
            raise IndexError(f"Index {index} out of range.")
        img_path = self.covers[index]
        img = Image.open(img_path).convert("RGB")
        img = ImageOps.fit(img, (self.im_size, self.im_size))
        cover = np.float32(img)
        random.seed(index)
        secret = [random.randint(0, 1) for _ in range(self.bit_length)]
        return cover, secret

    def get_num_covers(self) -> int:
        return len(self.covers)


class KODAK24(BaseDataset):
    """
    KODAK24 dataset loader.
    Loads 24 high-quality PNG images from Hugging Face.
    """

    def __init__(self, im_size: int, bit_len: int, iter_num: int = 1, dataset_name: str = "KODAK24", local_files_only: bool = False):
        super().__init__(im_size, bit_len, iter_num, dataset_name)
        self.im_size = im_size
        self.bit_length = bit_len
        config = _DATASET_CONFIG["kodak24"]
        self.root_path = _download_and_extract_hf(_REPO_ID, config["filename"], config["sha256"], config["folder"], local_files_only)
        self.covers = []
        self.load_paths()

    def load_paths(self):
        pattern = os.path.join(self.root_path, "*.BMP")
        self.covers = sorted(glob.glob(pattern))
        if len(self.covers) != 24:
            logger.warning(f"[KODAK24] Expected 24 images, found {len(self.covers)}")
        random.seed(99)
        random.shuffle(self.covers)
        logger.info(f"[KODAK24] Loaded {len(self.covers)} images.")

    def load_data(self, index: int) -> Tuple[np.ndarray, List[int]]:
        if index >= len(self.covers):
            raise IndexError(f"Index {index} out of range.")
        img_path = self.covers[index]
        img = Image.open(img_path).convert("RGB")
        img = ImageOps.fit(img, (self.im_size, self.im_size))
        cover = np.float32(img)
        random.seed(index)
        secret = [random.randint(0, 1) for _ in range(self.bit_length)]
        return cover, secret

    def get_num_covers(self) -> int:
        return len(self.covers)


class KODAK24_AND_USC_SIPI(BaseDataset):
    """
    Combined dataset: KODAK24 + USC_SIPI.
    """

    def __init__(self, im_size: int, bit_len: int, iter_num: int = 1, dataset_name: str = "KODAK24_AND_USC_SIPI", local_files_only: bool = False):
        super().__init__(im_size, bit_len, iter_num, dataset_name)
        self.im_size = im_size
        self.bit_length = bit_len
        self.covers = []

        # Load both datasets
        usc_path = USC_SIPI(im_size, iter_num, iter_num, local_files_only=local_files_only).root_path
        kodak_path = KODAK24(im_size, iter_num, iter_num, local_files_only=local_files_only).root_path

        self.load_paths([usc_path, kodak_path])

    def load_paths(self, root_paths: List[str]):
        patterns = ['*.BMP', '*.tiff']
        self.covers = []
        for path in root_paths:
            for pattern in patterns:
                full_pattern = os.path.join(path, '**', pattern)
                for img_path in glob.glob(full_pattern, recursive=True):
                    try:
                        with Image.open(img_path) as img:
                            if img.mode == 'RGB':
                                self.covers.append(img_path)
                    except Exception:
                        continue
        random.seed(99)
        random.shuffle(self.covers)
        logger.info(f"[KODAK24_AND_USC_SIPI] Loaded {len(self.covers)} RGB images.")

    def load_data(self, index: int) -> Tuple[np.ndarray, List[int]]:
        if index >= len(self.covers):
            raise IndexError(f"Index {index} out of range.")
        img_path = self.covers[index]
        img = Image.open(img_path).convert("RGB")
        img = ImageOps.fit(img, (self.im_size, self.im_size))
        cover = np.float32(img)
        random.seed(index)
        secret = [random.randint(0, 1) for _ in range(self.bit_length)]
        return cover, secret

    def get_num_covers(self) -> int:
        return len(self.covers)


class MS_COCO_2017_VAL_IMAGES(BaseDataset):
    """
    Loads images from MS-COCO 2017 validation set.
    The dataset zip contains a 'val2017' folder with ~5000 JPG images.
    Automatically downloads and extracts from Hugging Face Hub.
    """

    def __init__(self, im_size: int, bit_len: int, iter_num: int = 1, image_num: int = -1, dataset_name: str = "MS-COCO 2017 VAL IMAGES", local_files_only: bool = False):
        super().__init__(im_size, bit_len, iter_num, dataset_name)
        self.im_size = im_size
        self.image_num = image_num
        self.bit_len = bit_len
        config = _DATASET_CONFIG["mscoco2017val"]
        self.root_path = _download_and_extract_hf(
            _REPO_ID,
            config["filename"],
            config["sha256"],
            config["folder"],
            local_files_only
        )
        self.covers = []
        self.load_paths()

    def load_paths(self):
        val_folder = os.path.join(self.root_path, "val2017")
        if not os.path.exists(val_folder):
            raise RuntimeError(f"Expected 'val2017' folder not found: {val_folder}")

        patterns = ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG']
        covers = []
        for pattern in patterns:
            for img_path in glob.glob(os.path.join(val_folder, pattern), recursive=False):
                covers.append(img_path)

        if len(covers) == 0:
            raise RuntimeError(f"No valid images found in {val_folder}")

        random.seed(99)
        random.shuffle(covers)

        if 0 < self.image_num <= len(covers):
            self.covers = covers[:self.image_num]
        else:
            self.covers = covers

        logger.info(f"[MS_COCO_2017_VAL] Loaded {len(self.covers)} images from 'val2017'.")

    def load_data(self, index: int) -> Tuple[np.ndarray, List[int]]:
        if index >= len(self.covers):
            raise IndexError(f"Index {index} out of range.")
        img_path = self.covers[index]
        try:
            img = Image.open(img_path).convert("RGB")
            img = ImageOps.fit(img, (self.im_size, self.im_size))
            cover = np.float32(img)
        except Exception as e:
            logger.error(f"Failed to load image {img_path}: {e}")
            cover = np.random.rand(self.im_size, self.im_size, 3).astype(np.float32)

        random.seed(index)
        secret = [random.randint(0, 1) for _ in range(self.bit_len)]
        return cover, secret

    def get_num_covers(self) -> int:
        return len(self.covers)


class MS_COCO_2017_VAL_PROMPTS(BaseDataset):
    """
    Loads text prompts from MS-COCO val2017 captions.
    Each image has 5 captions; this class samples exactly ONE prompt per image,
    selected randomly but deterministically based on the seed.

    The dataset zip contains 'captions_val2017.json'.
    By default, loads all images (5k). Can optionally load a fixed subset.
    """

    def __init__(self, bit_len: int, iter_num: int = 1, prompts_len: int = -1,
                 dataset_name: str = "MS-COCO 2017 VAL PROMPT", seed: int = 99, local_files_only: bool = False):
        """
        Initialize the MS_COCO_VAL_PROMPTS dataset.

        Args:
            bit_length (int): Length of watermark bits.
            iter_num (int): Number of iterations.
            prompts_len (int, optional): Number of image-prompt pairs to use.
                If None or >=5000, loads all. Otherwise, selects a fixed random subset.
            dataset_name (str): Name of the dataset.
            seed (int): Seed for deterministic behavior (prompt selection and secret generation).
        """
        super().__init__(512, bit_len, iter_num, dataset_name)
        self.seed = seed
        self.bit_length = bit_len
        self.prompts_len = prompts_len
        self.prompts = []

        # Download and extract the prompts zip
        config = _DATASET_CONFIG["coco_prompts"]
        extracted_dir = _download_and_extract_hf(_REPO_ID, config["filename"], config["sha256"], config["folder"], local_files_only)

        # Locate the JSON file
        json_path = os.path.join(extracted_dir, "captions_val2017.json")
        if not os.path.exists(json_path):
            logger.error(f"Expected captions file not found: {json_path}")
            raise RuntimeError(f"Expected captions file not found: {json_path}")

        self._load_prompts_from_json(json_path)

    def _load_prompts_from_json(self, json_path: str):
        """
        Load one prompt per image from the COCO annotations JSON file.
        Uses deterministic random sampling based on self.seed.

        Args:
            json_path (str): Path to captions_val2017.json.
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Group captions by image_id
        captions_per_image = {}
        for ann in data['annotations']:
            img_id = ann['image_id']
            if img_id not in captions_per_image:
                captions_per_image[img_id] = []
            captions_per_image[img_id].append(ann['caption'].strip())

        # Use deterministic RNG
        rng = random.Random(self.seed)

        # Sample one prompt per image
        all_prompts = []
        image_ids = sorted(captions_per_image.keys())  # Deterministic order
        for img_id in image_ids:
            captions = captions_per_image[img_id]
            selected_caption = rng.choice(captions)  # Same seed → same choice
            all_prompts.append(selected_caption)

        # Shuffle image order if subset is used
        rng = random.Random(self.seed)
        if self.prompts_len <= 0 or self.prompts_len >= len(all_prompts):
            self.prompts = all_prompts
            logger.info(f"[MS_COCO 2017 VAL CAPTIONS] Loaded {len(self.prompts)} prompts (1 per image) from 'captions_val2017.json'.")
        else:
            # Select a fixed random subset of image-prompt pairs
            self.prompts = rng.sample(all_prompts, self.prompts_len)
            logger.info(f"[MS_COCO 2017 VAL CAPTIONS] Loaded {len(self.prompts)} / {len(all_prompts)} prompts (1 per image, deterministic subset).")

    def load_data(self, index: int) -> Tuple[str, List[int]]:
        """
        Return a prompt and a random secret.

        Args:
            index (int): Index of the prompt.

        Returns:
            Tuple[str, List[int]]: Prompt and binary secret.
        """
        if index < 0 or index >= len(self.prompts):
            raise IndexError(f"Prompt index {index} out of range.")
        prompt = self.prompts[index]
        # Use a different seed stream for secrets (based on self.seed but independent)
        random.seed(self.seed + 1000 + index)  # Offset to avoid interference
        secret = [random.randint(0, 1) for _ in range(self.bit_length)]
        return prompt, secret

    def get_num_covers(self) -> int:
        """
        Return the number of available prompts.

        Returns:
            int: Number of prompts.
        """
        return len(self.prompts)