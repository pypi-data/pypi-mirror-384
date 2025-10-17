# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT
import lpips
import torch
import numpy as np
from PIL import Image
from sklearn import metrics
from typing import Union, List
from torchvision import transforms
from scipy.ndimage import uniform_filter
from watermarklab.utils.basemodel import BaseMetric

__all__ = [
    'SSIM', 'RMSE', 'LPIPS', 'MAE', 'PSNR',
    'NEB', 'BER', 'EA', 'NC', 'TPR_AT_N_PERCENT_FPR'
]


class SSIM(BaseMetric):
    """
    Structural Similarity Index Measure (SSIM) for image quality assessment.

    SSIM evaluates the perceived quality of images by comparing luminance, contrast, and structure
    between two images (e.g., original vs. distorted). Values range from -1 to 1, where 1 indicates perfect similarity.

    Reference:
        Wang, Z., Bovik, A. C., Sheikh, H. R., & Simoncelli, E. P. (2004).
        Image quality assessment: From error visibility to structural similarity.
        IEEE Transactions on Image Processing, 13(4), 600–612.
    """

    def __init__(self, window_size: int = 11, data_range: float = 255.0, metric_name: str = "SSIM"):
        """
        Initializes the SSIM metric.

        Args:
            window_size (int): Size of the sliding window for local statistics (must be odd).
            data_range (float): Dynamic range of pixel values (e.g., 255 for uint8 images).
            metric_name (str): Name of the metric for reporting.
        """
        super().__init__(metric_name)
        self.window_size = window_size
        self.data_range = data_range

    def test(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        Computes the mean SSIM index between two images.

        Args:
            img1 (np.ndarray): Reference image (H, W, C) or (H, W).
            img2 (np.ndarray): Distorted image, same shape as img1.

        Returns:
            float: Mean SSIM value across the image.

        Raises:
            ValueError: If input images have different shapes.
        """
        if img1.shape != img2.shape:
            raise ValueError("Input images must have the same shape.")

        k1 = 0.01
        k2 = 0.03
        C1 = (k1 * self.data_range) ** 2
        C2 = (k2 * self.data_range) ** 2

        img1 = img1.astype(np.float64)
        img2 = img2.astype(np.float64)

        mu1 = uniform_filter(img1, size=self.window_size, mode='constant')
        mu2 = uniform_filter(img2, size=self.window_size, mode='constant')

        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2

        sigma1_sq = uniform_filter(img1 ** 2, self.window_size, mode='constant') - mu1_sq
        sigma2_sq = uniform_filter(img2 ** 2, self.window_size, mode='constant') - mu2_sq
        sigma12 = uniform_filter(img1 * img2, self.window_size, mode='constant') - mu1_mu2

        numerator = (2 * mu1_mu2 + C1) * (2 * sigma12 + C2)
        denominator = (mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2)
        ssim_map = numerator / (denominator + 1e-12)  # Avoid division by zero

        return float(np.mean(ssim_map))


class RMSE(BaseMetric):
    """
    Root Mean Squared Error (RMSE) measures the standard deviation of pixel-wise differences.

    Lower RMSE indicates higher similarity. Commonly used in regression and image reconstruction tasks.
    """

    def __init__(self, metric_name: str = "RMSE"):
        """
        Initializes the RMSE metric.

        Args:
            metric_name (str): Name of the metric for reporting.
        """
        super().__init__(metric_name)

    def test(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        Computes RMSE between two images.

        Args:
            img1 (np.ndarray): First image.
            img2 (np.ndarray): Second image, same shape.

        Returns:
            float: RMSE value.

        Raises:
            ValueError: If image dimensions do not match.
        """
        if img1.shape != img2.shape:
            raise ValueError("Input images must have the same dimensions.")

        mse = np.mean((img1 - img2) ** 2)
        return float(np.sqrt(mse))


class MAE(BaseMetric):
    """
    Mean Absolute Error (MAE) measures average absolute pixel differences.

    Less sensitive to outliers than RMSE. Useful for detecting small but consistent distortions.
    """

    def __init__(self, metric_name: str = "MAE"):
        """
        Initializes the MAE metric.

        Args:
            metric_name (str): Name of the metric for reporting.
        """
        super().__init__(metric_name)

    def test(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        Computes MAE between two images.

        Args:
            img1 (np.ndarray): First image.
            img2 (np.ndarray): Second image, same shape.

        Returns:
            float: MAE value.

        Raises:
            ValueError: If image dimensions do not match.
        """
        if img1.shape != img2.shape:
            raise ValueError("Input images must have the same dimensions.")

        return float(np.mean(np.abs(img1 - img2)))


class PSNR(BaseMetric):
    """
    Peak Signal-to-Noise Ratio (PSNR) measures image fidelity in decibels (dB).

    Higher PSNR indicates less distortion. Assumes known maximum pixel value (e.g., 255).
    """

    def __init__(self, data_range: float = 255.0, metric_name: str = "PSNR"):
        """
        Initializes the PSNR metric.

        Args:
            data_range (float): Maximum possible pixel value (e.g., 255 for uint8).
            metric_name (str): Name of the metric for reporting.
        """
        super().__init__(metric_name)
        self.data_range = data_range

    def test(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        Computes PSNR between two images.

        Args:
            img1 (np.ndarray): Reference image.
            img2 (np.ndarray): Distorted image.

        Returns:
            float: PSNR value in dB. Returns `inf` if images are identical.

        Raises:
            ValueError: If image dimensions do not match.
        """
        if img1.shape != img2.shape:
            raise ValueError("Input images must have the same dimensions.")

        mse = np.mean((img1 - img2) ** 2)
        if mse == 0:
            return float('inf')

        return float(20 * np.log10(self.data_range / np.sqrt(mse)))


class LPIPS(BaseMetric):
    """
    Learned Perceptual Image Patch Similarity (LPIPS) uses deep features to measure perceptual similarity.

    Lower values indicate higher similarity. More aligned with human perception than PSNR/SSIM.

    Reference:
        Zhang, R., Isola, P., Efros, A. A., Shechtman, E., & Wang, O. (2018).
        The Unreasonable Effectiveness of Deep Features as a Perceptual Metric.
        CVPR.
    """

    def __init__(self, device: str = "cpu", metric_name: str = "LPIPS", net_stype: str = "alex"):
        """
        Initializes the LPIPS metric.

        Args:
            device (str): Device to run computation ('cpu' or 'cuda').
            metric_name (str): Name of the metric for reporting.
            net_stype (str): Feature extractor network ('alex', 'vgg', 'squeeze').
        """
        super().__init__(metric_name)
        self.device = device
        self.loss_fn = lpips.LPIPS(net=net_stype).to(device)

    @torch.inference_mode()
    def test(self, img1: Union[np.ndarray, Image.Image], img2: Union[np.ndarray, Image.Image]) -> float:
        """
        Computes LPIPS distance between two images.

        Args:
            img1 (Union[np.ndarray, Image.Image]): First image.
            img2 (Union[np.ndarray, Image.Image]): Second image.

        Returns:
            float: LPIPS score (lower is better).

        Raises:
            ValueError: If image sizes differ.
        """
        if isinstance(img1, np.ndarray):
            img1 = Image.fromarray(np.uint8(img1))
        if isinstance(img2, np.ndarray):
            img2 = Image.fromarray(np.uint8(img2))

        if img1.size != img2.size:
            raise ValueError("Input images must have the same dimensions.")

        img1_tensor = transforms.ToTensor()(img1).unsqueeze(0).to(self.device)
        img2_tensor = transforms.ToTensor()(img2).unsqueeze(0).to(self.device)
        lpips_value = self.loss_fn(img1_tensor, img2_tensor).item()
        return lpips_value


class NEB(BaseMetric):
    """
    Number of Error Bits (NEB) counts the total number of mismatched bits in watermark extraction.

    Used to quantify absolute error in binary watermark retrieval.
    """

    def __init__(self, metric_name: str = "NEB"):
        """
        Initializes the NEB metric.

        Args:
            metric_name (str): Name of the metric for reporting.
        """
        super().__init__(metric_name)

    def test(self, ext_bits: List[int], target_bits: List[int]) -> int:
        """
        Computes the number of erroneous bits.

        Args:
            ext_bits (List[int]): Extracted watermark bits.
            target_bits (List[int]): Ground truth watermark bits.

        Returns:
            int: Number of differing bits.

        Raises:
            ValueError: If bit list lengths differ.
        """
        if len(ext_bits) != len(target_bits):
            raise ValueError("The lengths of the bit lists must be the same.")

        return int(np.sum(np.array(ext_bits) != np.array(target_bits)))


class BER(BaseMetric):
    """
    Bit Error Rate (BER) measures the ratio of incorrectly extracted bits.

    BER = (Number of Error Bits) / (Total Number of Bits)
    Lower BER indicates better robustness.
    """

    def __init__(self, metric_name: str = "BER"):
        """
        Initializes the BER metric.

        Args:
            metric_name (str): Name of the metric for reporting.
        """
        super().__init__(metric_name)

    def test(self, ext_bits: List[int], target_bits: List[int]) -> float:
        """
        Computes BER between extracted and target watermark bits.

        Args:
            ext_bits (List[int]): Extracted bits.
            target_bits (List[int]): Original embedded bits.

        Returns:
            float: BER in range [0, 1].

        Raises:
            ValueError: If list lengths differ.
        """
        if len(ext_bits) != len(target_bits):
            raise ValueError("The lengths of the extracted and target bits must be the same.")

        error_bits = sum(1 for e, t in zip(ext_bits, target_bits) if e != t)
        return error_bits / len(target_bits) if len(target_bits) > 0 else 0.0


class TPR_AT_N_PERCENT_FPR(BaseMetric):
    """
    True Positive Rate at N% False Positive Rate (TPR@N%FPR).

    Evaluates watermark detector performance under low false alarm constraints.
    - Higher TPR@1%FPR = better detection reliability.
    - Used when security demands low false positives.

    Input:
        - scores_attacked: Detection scores on attacked watermarked images (lower = less confident)
        - scores_clean_stego: Detection scores on clean stego images (unattacked, should be high)

    Assumption: Higher score = more likely to contain watermark.
    """

    def __init__(self, N: float = 0.1, metric_name: str = "TPR@1%FPR"):
        """
        Initializes the TPR@N%FPR metric.

        Args:
            N (float): Target FPR threshold in percent (e.g., 1 → 1% FPR).
            metric_name (str): Name of the metric (will replace '1' with N).
        """
        super().__init__(metric_name.replace('1', f'{N}'))
        self.N = N  # N percent (e.g., 1 for 1%)

    def test(
            self,
            scores_clean: List[float],
            scores_attacked: List[float]
    ) -> float:
        """
        Computes TPR at N% FPR using ROC curve interpolation.

        Args:
            scores_clean (List[float]): Detection scores on clean stego images.
            scores_attacked (List[float]): Detection scores on attacked stego images.

        Returns:
            float: TPR at N% FPR. Range [0, 1].

        Raises:
            ValueError: If either list is empty.
        """
        if not scores_clean:
            raise ValueError("scores_clean must be non-empty.")
        if not scores_attacked:
            raise ValueError("scores_attacked must be non-empty.")

        # Labels: 0 = attacked (negative), 1 = clean stego (positive)
        y_true = [0] * len(scores_clean) + [1] * len(scores_attacked)
        y_scores = np.array(scores_clean + scores_attacked)

        return self._compute_tpr_at_nfpr(y_true, y_scores)

    def _compute_tpr_at_nfpr(self, y_true: List[int], y_scores: np.ndarray) -> float:
        """
        Internal method to compute TPR at N% FPR via ROC curve.

        Interpolates TPR at FPR = N/100.

        Args:
            y_true (List[int]): Binary labels (0=negative, 1=positive).
            y_scores (np.ndarray): Prediction scores.

        Returns:
            float: Interpolated TPR at N% FPR.
        """
        try:
            fpr, tpr, _ = metrics.roc_curve(y_true, y_scores, pos_label=1)
            target_fpr = self.N / 100.0  # Convert percent to ratio

            if fpr[0] >= target_fpr:
                return float(tpr[0])  # Conservative threshold
            if fpr[-1] < target_fpr:
                return float(tpr[-1])  # Max achievable TPR

            return float(np.interp(target_fpr, fpr, tpr))

        except Exception as e:
            raise RuntimeError(f"Failed to compute TPR@{self.N}%FPR: {e}")


class NC(BaseMetric):
    """
    Normalized Correlation (NC) measures similarity between two binary sequences.

    NC = (A • B) / (||A|| ||B||)
    Values close to 1 indicate strong correlation. Used in spread-spectrum watermarking.
    """

    def __init__(self, metric_name: str = "Normalized Correlation"):
        """
        Initializes the NC metric.

        Args:
            metric_name (str): Name of the metric for reporting.
        """
        super().__init__(metric_name)

    def test(self, ext_bits: List[int], target_bits: List[int]) -> float:
        """
        Computes normalized correlation between extracted and target bits.

        Args:
            ext_bits (List[int]): Extracted watermark.
            target_bits (List[int]): Original watermark.

        Returns:
            float: NC value in range [-1, 1]. 1 = perfect match.

        Raises:
            ValueError: If list lengths differ.
        """
        if len(ext_bits) != len(target_bits):
            raise ValueError("The lengths of the bit lists must be the same.")

        ext = np.array(ext_bits, dtype=np.float32)
        tgt = np.array(target_bits, dtype=np.float32)

        numerator = np.sum(ext * tgt)
        denominator = np.sqrt(np.sum(tgt ** 2) * np.sum(ext ** 2))

        return 0.0 if denominator == 0 else float(numerator / denominator)


class EA(BaseMetric):
    """
    Extraction Accuracy (EA) measures the percentage of correctly extracted bits.

    EA = (Correct Bits) / (Total Bits) * 100%
    Often used interchangeably with (1 - BER) * 100.
    """

    def __init__(self, metric_name: str = "Extract Accuracy"):
        """
        Initializes the EA metric.

        Args:
            metric_name (str): Name of the metric for reporting.
        """
        super().__init__(metric_name)

    def test(self, ext_bits: List[int], target_bits: List[int]) -> float:
        """
        Computes extraction accuracy as percentage.

        Args:
            ext_bits (List[int]): Extracted bits.
            target_bits (List[int]): Original bits.

        Returns:
            float: Accuracy in range [0, 100].

        Raises:
            ValueError: If list lengths differ.
        """
        if len(ext_bits) != len(target_bits):
            raise ValueError("The lengths of the bit lists must be the same.")

        correct = np.sum(np.array(ext_bits) == np.array(target_bits))
        return float(correct / len(ext_bits) * 100.0)
