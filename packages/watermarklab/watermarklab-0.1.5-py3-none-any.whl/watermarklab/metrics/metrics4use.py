# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT
import numpy as np
from PIL import Image
import lpips as pip_lpips
from torchvision import transforms
from scipy.ndimage import uniform_filter

__all__ = ['ssim', 'psnr', 'neb', 'ber', 'extraction_accuracy', 'normalized_correlation', 'lpips']


def ssim(img1, img2, window_size=11, data_range=255):
    """
    Compute the Structural Similarity Index (SSIM) between two images.

    :param img1: First image (numpy array).
    :param img2: Second image (numpy array).
    :param window_size: Size of the sliding window.
    :param data_range: Range of pixel values (default 255).
    :param metric_name: Name of the metric (default "ssim").
    :return: SSIM value.
    """
    if img1.shape != img2.shape:
        raise ValueError("Input images must have the same shape.")

    k1 = 0.01
    k2 = 0.03
    C1 = (k1 * data_range) ** 2
    C2 = (k2 * data_range) ** 2

    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)

    mu1 = uniform_filter(img1, size=window_size, mode='constant')
    mu2 = uniform_filter(img2, size=window_size, mode='constant')

    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = uniform_filter(img1 ** 2, size=window_size, mode='constant') - mu1_sq
    sigma2_sq = uniform_filter(img2 ** 2, size=window_size, mode='constant') - mu2_sq
    sigma12 = uniform_filter(img1 * img2, size=window_size, mode='constant') - mu1_mu2

    numerator = (2 * mu1_mu2 + C1) * (2 * sigma12 + C2)
    denominator = (mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2)
    ssim_map = numerator / denominator

    return np.mean(ssim_map)


def psnr(img1, img2, data_range=255):
    """
    Calculate the Peak Signal-to-Noise Ratio (PSNR)

    :param img1: Input image
    :param img2: Target image
    :param data_range: Range of pixel values (default 255).
    :return: PSNR value in decibels (dB)
    """
    if img1.shape != img2.shape:
        raise ValueError("Input image and target image must have the same dimensions")

    mse = np.mean((img1 - img2) ** 2)
    if mse == 0:
        return float('inf')

    psnr_value = 20 * np.log10(data_range / np.sqrt(mse))
    return psnr_value


def lpips(img1, img2, device="cpu", net_stype="alex"):
    """
    Calculate the Learned Perceptual Image Patch Similarity (LPIPS)

    :param img1: Input image
    :param img2: Target image
    :param device: Device to run the computation on (default "cpu").
    :param net_stype: Network type for LPIPS (default "alex").
    :return: LPIPS value
    """
    loss_fn = pip_lpips.LPIPS(net=net_stype)

    if isinstance(img1, np.ndarray):
        img1 = Image.fromarray(img1)
    if isinstance(img2, np.ndarray):
        img2 = Image.fromarray(img2)

    if img1.size != img2.size:
        raise ValueError("Input image and target image must have the same dimensions")

    img1_tensor = transforms.ToTensor()(img1).unsqueeze(0).to(device)
    img2_tensor = transforms.ToTensor()(img2).unsqueeze(0).to(device)

    lpips_value = loss_fn(img1_tensor, img2_tensor)
    return lpips_value.item()


def neb(ext_bits, target_bits):
    """
    Calculate the Number of Error Bits (NEB)

    :param ext_bits: List of extracted bits
    :param target_bits: List of target bits
    :return: Number of error bits
    """
    if len(ext_bits) != len(target_bits):
        raise ValueError("The lengths of the bit lists must be the same")

    error_bits = np.sum(np.array(ext_bits) != np.array(target_bits))
    return error_bits


def ber(ext_bits, target_bits):
    """
    Calculate the overall Bit Error Rate (BER) between the extracted watermarks and the target watermarks.

    This function flattens both 1D and 2D inputs and computes a single, global BER value.

    Args:
        ext_bits: The extracted watermark bits. Can be:
                  - 1D: A single list of bits (e.g., [1, 0, 1]).
                  - 2D: A list of bit lists (e.g., [[1,0], [1,1]]).
        target_bits: The target watermark bits. Must match the shape of `ext_bits`.

    Returns:
        float: The overall Bit Error Rate across all bits.
    """
    if not isinstance(ext_bits, list) or not isinstance(target_bits, list):
        raise TypeError("Both ext_bits and target_bits must be lists.")

    ext_2d = [ext_bits] if (ext_bits and not isinstance(ext_bits[0], list)) else ext_bits
    tgt_2d = [target_bits] if (target_bits and not isinstance(target_bits[0], list)) else target_bits

    if len(ext_2d) != len(tgt_2d):
        raise ValueError(f"Batch size mismatch. ext_bits: {len(ext_2d)}, target_bits: {len(tgt_2d)}")

    total_errors = 0
    total_bits = 0

    for e_seq, t_seq in zip(ext_2d, tgt_2d):
        if len(e_seq) != len(t_seq):
            raise ValueError(f"Sequence length mismatch. Got {len(e_seq)} and {len(t_seq)}.")
        total_errors += sum(e != t for e, t in zip(e_seq, t_seq))
        total_bits += len(t_seq)

    ber_value = float(total_errors) / total_bits if total_bits > 0 else 0.0
    return ber_value


def normalized_correlation(ext_bits, target_bits):
    """
    Normalized Correlation (NC, Normalized Correlation)

    :param ext_bits: List of extracted bits
    :param target_bits: List of target bits
    :return: NC
    """
    if len(ext_bits) != len(target_bits):
        raise ValueError("The lengths of the bit lists must be the same")

    ext_bits = np.array(ext_bits, dtype=np.float32)
    target_bits = np.array(target_bits, dtype=np.float32)

    numerator = np.sum(ext_bits * target_bits)
    denominator = np.sqrt(np.sum(target_bits ** 2) * np.sum(ext_bits ** 2))

    if denominator == 0:
        return 0.0

    nc_value = numerator / denominator
    return nc_value


def extraction_accuracy(ext_bits, target_bits):
    """
    Calculate extraction accuracy

    :param ext_bits: List of extracted bits
    :param target_bits: List of target bits
    :return: Extraction accuracy as the ratio of correct bits
    """
    if len(ext_bits) != len(target_bits):
        raise ValueError("The lengths of the bit lists must be the same")

    correct_bits = np.sum(np.array(ext_bits) == np.array(target_bits))
    accuracy = correct_bits / len(ext_bits) * 100.
    return accuracy
