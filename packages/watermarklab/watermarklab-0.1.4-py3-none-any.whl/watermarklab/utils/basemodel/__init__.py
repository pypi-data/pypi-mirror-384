# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT
import torch
import timeit
from torch import nn
from numpy import ndarray
from abc import ABC, abstractmethod
from typing import List, Tuple, Any, Dict, Optional

__all__ = [
    'Result',
    'BaseWatermarkModel',
    'BaseDataset',
    'AttackerWithFactors',
    'BaseDiffAttackModel',
    'BaseTestAttackModel',
    'BaseMetric'
]


class Result:
    """
    Container class for storing results of watermarking operations.

    This class holds outputs from embedding, extraction, and recovery processes,
    including processed images, extracted bits, and auxiliary metrics.
    Designed for structured return values across the framework.

    Attributes:
        stego_img (Optional[List[Any]]): Watermarked images (output of embedding).
        clean_img (Optional[List[Any]]): Original unwatermarked images (for IGW models).
        emb_bits (Optional[List[List[Any]]]): Embedded secret bits (before embedding).
        ext_bits (Optional[List[List[Any]]]): Extracted secret bits (after decoding).
        rec_img (Optional[List[Any]]): Recovered cover images (if model supports reversible watermarking).
        other_result (Dict[str, Any]): Additional metadata (e.g., timing, intermediate outputs).
    """

    def __init__(self,
                 stego_img: Optional[List[Any]] = None,
                 clean_img: Optional[List[Any]] = None,
                 emb_bits: Optional[List[List[Any]]] = None,
                 ext_bits: Optional[List[List[Any]]] = None,
                 rec_img: Optional[List[Any]] = None,
                 other_result: Optional[Dict[str, Any]] = None):
        """
        Initializes the Result container.

        Args:
            stego_img (Optional[List[Any]]): List of stego images.
            clean_img (Optional[List[Any]]): List of clean (generated) images (IGW only).
            emb_bits (Optional[List[List[Any]]]): Embedded bit sequences.
            ext_bits (Optional[List[List[Any]]]): Extracted bit sequences.
            rec_img (Optional[List[Any]]): Recovered cover images (for reversible watermarking).
            other_result (Optional[Dict[str, Any]]): Additional key-value data (e.g., timing, losses).
        """
        self.stego_img = stego_img
        self.clean_img = clean_img
        self.emb_bits = emb_bits
        self.ext_bits = ext_bits
        self.rec_img = rec_img
        self.other_result = other_result or {}


def timing_decorator(func):
    """
    Decorator to automatically measure and record execution time of a method.

    Adds a timing entry to `result.other_result` using the method name as the key.
    Useful for profiling embedding, extraction, and recovery performance.

    Example:
        @timing_decorator
        def embed(...):
            ...

        result = model.embed(...)
        # result.other_result['embed'] = 0.123  # seconds

    Args:
        func (callable): Method to time (must return a Result object).

    Returns:
        callable: Wrapped function with timing instrumentation.
    """

    def wrapper(self, *args, **kwargs):
        start_time = timeit.default_timer()
        result = func(self, *args, **kwargs)
        end_time = timeit.default_timer()

        # Ensure result has other_result dict
        if not hasattr(result, 'other_result'):
            result.other_result = {}
        result.other_result[func.__name__] = end_time - start_time

        return result

    return wrapper



class BaseWatermarkModel(ABC, nn.Module):
    """
    Abstract base class for all watermarking models (both PGW and IGW).

    Defines the core interface:
    - `embed`: Embed secret bits into image/prompt
    - `extract`: Decode watermark from stego image
    - `recover`: Reconstruct cover (optional, for reversible watermarking)

    All methods are decorated with `@timing_decorator` to auto-record execution time.
    """

    def __init__(self, bits_len: int, img_size: int, modelname: str, description: str = None):
        """
        Initializes the watermarking model.

        Args:
            bits_len (int): Number of bits in the watermark payload.
            img_size (int): Input image resolution (assumed square: img_size × img_size).
            modelname (str): Unique name for the model (e.g., "HiNet", "StegaStamp").
        """
        super().__init__()
        self.bits_len = bits_len
        self.img_size = img_size
        self.modelname = modelname
        self.description = description

    @timing_decorator
    @abstractmethod
    def embed(self, cover_list: List[Any], secrets: List[Any]) -> Result:
        """
        Embeds a secret watermark into cover content, which can be either existing images (PGW)
        or text prompts (IGW). This is the core method for watermark insertion.

        The framework automatically distinguishes between PGW and IGW based on the type of elements
        in `cover_list`:
          - If elements are image-like (e.g., numpy.ndarray) → PGW
          - If elements are strings (text prompts) → IGW

        The returned `Result` object must contain specific fields depending on the model type:

        For PGW (Post-Generation Watermarking):
          - Operates on pre-existing cover images.
          - Does not generate new clean images; the input images are already available to the caller.
          - Required fields in `Result`:
              - `stego_img`: List of watermarked images (same length as `cover_list`).
              - `emb_bits`: List of bit sequences that were embedded.
          - The `clean_img` field is optional and typically omitted (the framework already has the cover images).

        For IGW (In-Generation Watermarking):
          - Generates images from text prompts, producing both clean and stego versions.
          - Must return the generated clean images to enable detection evaluation (e.g., TPR@x%FPR).
          - Required fields in `Result`:
              - `stego_img`: List of stego images.
              - `clean_img`: List of corresponding clean images generated from the same prompts.
              - `emb_bits`: List of bit sequences that were embedded.
          - Omitting `clean_img` will raise a runtime validation error.

        Args:
            cover_list (List[Any]):
                - For PGW: List of existing images (e.g., List[numpy.ndarray] or List[torch.Tensor]).
                - For IGW: List of text prompts (List[str]).
            secrets (List[Any]): List of secret bit sequences to embed (e.g., List[List[int]] of 0s and 1s).

        Returns:
            Result: A structured container with the following guaranteed fields based on model type:
                - `stego_img` (List[Any]): Watermarked output images (required for both PGW and IGW).
                - `clean_img` (List[Any], required only for IGW): Generated clean images.
                - `emb_bits` (List[List[Any]]): The actual bit sequences embedded (required for both).
                - `other_result` (Dict[str, Any], optional): Additional metadata (e.g., losses, intermediate tensors).

        Examples:
            # PGW example: watermarking existing images
            cover_images = [img1, img2]  # each is ndarray or Tensor
            secrets = [[1,0,1], [0,1,0]]
            result = model.embed(cover_images, secrets)
            # result must have: stego_img, emb_bits
            # result.clean_img is ignored (usually None)

            # IGW example: generating watermarked images from prompts
            prompts = ["a red apple", "a blue car"]
            secrets = [[1,1,0], [0,0,1]]
            result = model.embed(prompts, secrets)
            # result must have: stego_img, clean_img, emb_bits
        """
        pass

    @timing_decorator
    @abstractmethod
    def extract(self, stego_list: List[ndarray]) -> Result:
        """
        Extracts watermark bits from stego images.

        Decodes the embedded secret from one or more watermarked images.

        Args:
            stego_list (List[ndarray]): List of stego images (H×W×C, float32).

        Returns:
            Result: Object containing:
                - ext_bits: Extracted bit sequences
                - other_result: Timing, confidence scores, etc.
        """
        pass

    @timing_decorator
    @abstractmethod
    def recover(self, stego_list: List[ndarray]) -> Result:
        """
        Recovers the original cover image from a stego image (reversible watermarking).

        Only applicable to reversible or semi-reversible watermarking schemes.
        For irreversible methods, this may return the stego image or raise NotImplementedError.

        Args:
            stego_list (List[ndarray]): List of stego images.

        Returns:
            Result: Object containing:
                - rec_img: Reconstructed cover images
        """
        pass


class BaseDataset(ABC):
    """
    Abstract base class for datasets used in watermarking evaluation.

    Provides a unified interface for loading:
    - Cover images (PGW) or text prompts (IGW)
    - Secret bit sequences

    Supports multiple iterations per cover/prompt (e.g., test robustness across N runs).
    """

    def __init__(self, img_size: int, bit_len: int, iter_num: int, dataset_name: str):
        """
        Initializes the dataset.

        Args:
            iter_num (int): Number of times to reuse each cover/prompt (e.g., 3 runs per image).
            dataset_name (str): Name of the dataset (e.g., "KODAK24", "MS-COCO-2017-VAL").
        """
        assert iter_num > 0, "iter_num must be positive"
        self.bit_len = bit_len
        self.img_size = img_size
        self.iter_num = iter_num
        self.dataset_name = dataset_name

    @abstractmethod
    def load_data(self, index: int) -> Tuple[Any, List[int]]:
        """
        Loads a single cover/prompt and generates a secret bit sequence.

        Must be implemented by subclasses.

        Args:
            index (int): Index of the cover/prompt (not experiment).

        Returns:
            Tuple[Any, List[int]]: (cover/prompt, secret_bits)
        """
        pass

    def __getitem__(self, index: int) -> Tuple[Any, List[int], int, int]:
        """
        Returns a cover/prompt and secret for a specific experiment.

        Flattens the dataset: total length = num_covers × iter_num.
        Maps linear index to (cover_index, iter_index).

        Args:
            index (int): Global experiment index (0 to len(dataset)-1).

        Returns:
            Tuple[Any, List[int], int, int]:
                - cover/prompt
                - secret bits
                - cover_index (which image/prompt)
                - iter_index (which iteration of that image)
        """
        cover_index = index // self.iter_num
        iter_index = index % self.iter_num
        cover_prompt, secret = self.load_data(cover_index)
        return cover_prompt, secret, cover_index, iter_index

    def __len__(self) -> int:
        """
        Total number of experiments (covers × iterations).

        Used by DataLoader for batching.

        Returns:
            int: Total number of experiment runs.
        """
        return self.get_num_covers() * self.iter_num

    @abstractmethod
    def get_num_covers(self) -> int:
        """
        Gets the number of unique covers/prompts in the dataset.

        Required for __len__ and indexing.

        Returns:
            int: Number of cover images or prompts.
        """
        pass


class BaseDiffAttackModel(nn.Module):
    """
    Base class for attacker models used in diffusion-based watermarking (IGW).

    These models modify the denoising process in diffusion models (e.g., Stable Diffusion).
    Not used in standard PGW evaluation.
    """

    def __init__(self, noise_name: str):
        """
        Initializes the diffusion noise model.

        Args:
            noise_name (str): Descriptive name of the noise type.
        """
        super().__init__()
        self.noise_name = noise_name

    @abstractmethod
    def forward(self, stego_img: torch.Tensor, cover_img: torch.Tensor, now_step: int = 0) -> torch.Tensor:
        """
        Applies noise during the diffusion process.

        Args:
            stego_img (torch.Tensor): Current noisy latent.
            cover_img (torch.Tensor): Original latent (reference).
            now_step (int): Current denoising step.

        Returns:
            torch.Tensor: Modified latent.
        """
        pass


class BaseTestAttackModel(ABC):
    """
    Abstract base class for image noise and distortion models used in watermark robustness evaluation.

    This class defines a standardized interface for applying various real-world image degradations
    (e.g., compression, noise, geometric transforms) to stego images. It enables systematic testing
    of how well a watermark survives common signal processing operations.

    Subclasses must implement the `test` method to define the specific distortion behavior.
    The class supports both intensity-proportional and inverse-intensity distortions via the
    `factor_inversely_related` flag.

    Examples of supported distortions:
        - Lossy compression (JPEG, WebP)
        - Additive noise (Gaussian, Poisson)
        - Filtering (Blur, Median)
        - Geometric attacks (Resize, Rotate)
        - Learned attacks (Neural compression, Diffusion regeneration)

    Attributes:
        noisename (str): Human-readable name of the noise model (e.g., "Gaussian Blur").
        factor_inversely_related (bool): Indicates the relationship between `factor` and distortion strength.
            - True: Higher factor → less distortion (e.g., JPEG quality: 90 > 30 → less compression)
            - False: Higher factor → more distortion (e.g., noise σ: 10 > 1 → more noise)
    """

    def __init__(self, noisename: str, factor_inversely_related: bool = False):
        """
        Initializes the noise model with a display name and distortion semantics.

        Args:
            noisename (str): The name used in reports and logs (e.g., "Salt & Pepper Noise").
            factor_inversely_related (bool, optional): Whether a higher factor value corresponds to
                weaker distortion. Defaults to False. Used for sorting and visualization.
        """
        self.noisename = noisename
        self.factor_inversely_related = factor_inversely_related

    @abstractmethod
    def attack(self, stego_img: List[ndarray], cover_img: List[ndarray], factor: float) -> List[ndarray]:
        """
        Alias for the `test` method, provided for semantic clarity in robustness testing pipelines.

        Some frameworks prefer the term "attack" over "test" when evaluating watermark resilience.
        This method delegates directly to `test`.

        Args:
            stego_img (List[ndarray]): Watermarked image(s) to be attacked.
            cover_img (List[ndarray]): Original cover image(s), if required by the attack.
            factor (float): Intensity or quality parameter of the attack.

        Returns:
            List[ndarray]: Attacked (distorted) stego image(s).

        Note:
            This method exists solely for API convenience and readability. It does not add new logic.
        """
        pass

    def print_params(self) -> Dict[str, Any]:
        """
        Returns a dictionary representation of the instance's attributes for logging and debugging.

        This is useful for recording experimental configurations in JSON reports or logs.

        Returns:
            Dict[str, Any]: A nested dictionary with the class name as the key and all instance
            attributes (including `noisename`, `factor_inversely_related`) as values.

        Example:
            >>> model = Jpeg(noisename="JPEG Compression", factor_inversely_related=True)
            >>> model.print_params()
            {'Jpeg': {'noisename': 'JPEG Compression', 'factor_inversely_related': True}}
        """
        return {self.__class__.__name__: vars(self)}



class BaseMetric(ABC):
    """
    Abstract base class for all evaluation metrics in WatermarkLab.

    Includes:
    - Visual quality metrics (PSNR, SSIM, LPIPS, FID)
    - Robustness metrics (BER, EA, TPR@FPR)
    - Structural similarity and correlation measures
    """

    def __init__(self, metric_name: str):
        """
        Initializes the metric.

        Args:
            metric_name (str): Human-readable name (e.g., "PSNR", "BER").
        """
        self.metric_name = metric_name

    @abstractmethod
    def test(self, cover, stego) -> float:
        """
        Computes the metric value by comparing two images.

        Args:
            cover: Original image (cover).
            stego: Watermarked/distorted image.

        Returns:
            float: Metric value (range depends on metric).
        """
        pass

    def get_params(self) -> Dict[str, Any]:
        """
        Returns a copy of all instance attributes.

        Used for logging and reproducibility.

        Returns:
            Dict[str, Any]: Parameter dictionary.
        """
        return vars(self).copy()

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Returns:
            str: Formatted class name and parameters.
        """
        params = ', '.join(f"{k}={v!r}" for k, v in self.get_params().items())
        return f"{self.__class__.__name__}({params})"


class AttackerWithFactors:
    """
    Wrapper that combines a noise model with its test factors and display symbol.

    Used to define a full attack configuration for robustness testing.
    """

    def __init__(self,
                 attacker: BaseTestAttackModel,
                 attackername: str,
                 factors: List[Any],
                 factorsymbol: str):
        """
        Initializes the noise model wrapper.

        Args:
            attacker (BaseTestAttackModel): Instance of a noise model.
            attackername (str): Display name (e.g., "JPEG").
            factors (List[float]): List of distortion levels to test (e.g., [75, 50, 25]).
            factorsymbol (str): LaTeX-style symbol for plotting (e.g., "$Q$", "$\sigma$").
        """
        self.attacker = attacker
        self.attackername = attackername
        self.factorsymbol = factorsymbol
        self.factors = factors
