# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT

import torch
import pyfiglet
from typing import List
from colorama import init, Fore, Style
from watermarklab.utils.data import DataLoader
from watermarklab.metrics.metrics4test import *
from watermarklab.laboratories.utils import _is_igw
from watermarklab.laboratories.PGW_func import PGWLab
from watermarklab.laboratories.IGW_func import IGWLab
from watermarklab.utils.basemodel import BaseWatermarkModel, BaseMetric, AttackerWithFactors

__all__ = ['evaluate', 'WLab']


def evaluate(save_path: str,
             watermark_model: BaseWatermarkModel,
             noise_models: List[AttackerWithFactors],
             dataloader: DataLoader,
             vqmetrics: List[BaseMetric] = None,
             robustnessmetrics: List[BaseMetric] = None,
             fid_dataset: str = "MS-COCO-2017-VAL",
             fid_batchsize: int = 32,
             fid_device: str = "cuda",
             noise_save: bool = False,
             need_cover: bool = False) -> dict:
    """
    Unified entry point for evaluating both Post-Generation (PGW) and In-Generation (IGW) watermarking models.

    This function:
      - Automatically detects whether the model is PGW or IGW based on dataloader input type.
      - Initializes the appropriate evaluation lab (PGWLab or IGWLab).
      - Executes the full evaluation pipeline: embedding → visual quality → noise attacks → extraction → metrics.
      - Generates stylized terminal banner for user experience.
      - Returns structured, JSON-serializable results with embedded Base64 visualizations.

    Ideal for benchmarking, research reproducibility, and automated testing pipelines.

    Args:
        save_path (str): Root directory to save all evaluation outputs (organized by model name).
        watermark_model (BaseWatermarkModel): Watermarking model to evaluate.
        noise_models (List[AttackerWithFactors]): List of noise attack configurations with intensity factors.
        dataloader (DataLoader): Provides input data — images for PGW, prompts for IGW — and secret bits.
        vqmetrics (List[BaseMetric], optional): Visual quality metrics. Defaults to [PSNR(), SSIM()].
        robustnessmetrics (List[BaseMetric], optional): Robustness metrics. Defaults to [TPR_AT_N_PERCENT_FPR(), EA()].
        fid_dataset (str, optional): Name of real image dataset for FID comparison (IGW only). Default: "MS-COCO-2017-VAL".
        fid_batchsize (int, optional): Batch size for FID computation. Larger = faster but more VRAM. Default: 32.
        fid_device (str, optional): Device for FID computation ("cuda" or "cpu"). Default: "cuda".
        noise_save (bool, optional): If True, preserves intermediate noised images. Otherwise, deletes them after extraction. Default: False.
        need_cover (bool, optional): If True, uses clean images as reference for visual metrics in IGW. Default: False.

    Returns:
        dict: Comprehensive evaluation report with keys:
            - modelname, modeltype, imagesize, payload
            - testdataset, envinfo (hardware/software environment)
            - time_cost: {'embed': [...], 'extract': [...]}
            - visualqualityresult: PSNR, SSIM, LPIPS, FID scores
            - robustnessresult: BER, EA, TPR@FPR per attack type/factor
            - visualcompare: Base64-encoded images for stego and noise samples
    """

    # Validate mode argument
    assert fid_dataset in ["MS-COCO-2017-VAL"]

    # Initialize colorama for cross-platform colored terminal output
    init()

    # Generate and print stylized ASCII banner for visual feedback
    banner = pyfiglet.figlet_format("WatermarkLab", font="slant")
    model_info = f" (Test {Fore.BLUE}{watermark_model.modelname}{Style.RESET_ALL})"
    description = (
        f"WatermarkLab is a comprehensive toolkit for the development and evaluation \n"
        f"of robust image watermarking.{model_info}"
    )
    print(Fore.CYAN + banner + Style.RESET_ALL + description + "\n")

    # Initialize unified evaluation orchestrator
    wlab = WLab(
        save_path=save_path,
        noise_models=noise_models,
        vqmetrics=vqmetrics,
        robustnessmetrics=robustnessmetrics,
        noise_save=noise_save
    )

    device = torch.device(fid_device)

    # Execute evaluation pipeline
    result = wlab.test(
        watermark_model=watermark_model,
        dataloader=dataloader,
        fid_dataset=fid_dataset,
        fid_batchsize=fid_batchsize,
        device=device,
        need_cover=need_cover
    )

    return result


class WLab:
    """
    Unified orchestrator for evaluating both Post-Generation (PGW) and In-Generation (IGW) watermarking models.

    This class:
      - Abstracts away the differences between PGW and IGW evaluation pipelines.
      - Automatically selects the correct lab (PGWLab or IGWLab) based on input data type.
      - Ensures consistent configuration (metrics, noise models, save paths) across evaluations.
      - Returns standardized result format regardless of model type.

    Enables a single, clean interface for evaluating any watermarking model in the framework.
    """

    def __init__(self,
                 save_path: str,
                 noise_models: List[AttackerWithFactors],
                 vqmetrics: List[BaseMetric] = None,
                 robustnessmetrics: List[BaseMetric] = None,
                 noise_save: bool = False):
        """
        Initialize the unified watermarking evaluation framework.

        Sets up both PGW and IGW evaluation labs with shared configuration. The correct lab
        is selected automatically at runtime based on the input dataloader's data type.

        Args:
            save_path (str): Root directory for saving all evaluation results.
            noise_models (List[AttackerWithFactors]): List of noise attack configurations to test robustness.
            vqmetrics (List[BaseMetric], optional): Visual quality metrics. Defaults to [PSNR(), SSIM()].
            robustnessmetrics (List[BaseMetric], optional): Robustness metrics. Defaults to [TPR_AT_N_PERCENT_FPR(), EA()].
            noise_save (bool, optional): If True, preserves intermediate noised images after extraction. Defaults to False.
        """
        self.save_path = save_path
        self.noise_save = noise_save

        # Set default visual quality metrics if not provided
        self.vqmetrics = vqmetrics or [PSNR(), SSIM()]

        # Set default robustness metrics if not provided
        self.robustnessmetrics = robustnessmetrics or [TPR_AT_N_PERCENT_FPR(), EA()]

        # Initialize both evaluation labs with shared configuration
        self.pgw_lab = PGWLab(
            save_path=save_path,
            noise_models=noise_models,
            vqmetrics=self.vqmetrics,
            robustnessmetrics=self.robustnessmetrics,
            noise_save=noise_save
        )

        self.igw_lab = IGWLab(
            save_path=save_path,
            noise_models=noise_models,
            vqmetrics=self.vqmetrics,
            robustnessmetrics=self.robustnessmetrics,
            noise_save=noise_save
        )

    def test(self,
             watermark_model: BaseWatermarkModel,
             dataloader: DataLoader,
             fid_dataset: str = "MS-COCO-2017-VAL",
             fid_batchsize: int = 32,
             device: torch.device = "cuda",
             need_cover: bool = False) -> dict:
        """
        Execute full evaluation pipeline for the specified watermarking model.

        Automatically determines whether the model is PGW or IGW by inspecting the first batch
        from the dataloader, then delegates evaluation to the appropriate lab.

        Args:
            watermark_model (BaseWatermarkModel): Watermarking model to evaluate.
            dataloader (DataLoader): Provides input data (images for PGW, prompts for IGW) and secret bits.
            fid_dataset (str, optional): Name of real dataset for FID comparison (IGW only). Default: "MS-COCO-2017-VAL".
            fid_batchsize (int, optional): Batch size for FID computation. Default: 32.
            device (torch.device, optional): Device for metric computations (e.g., CUDA for FID). Default: "cuda".
            need_cover (bool, optional): If True, uses clean images as reference for visual metrics in IGW. Default: False.

        Returns:
            dict: Standardized evaluation report containing:
                - Model metadata (name, type, image size, payload)
                - Dataset and environment information
                - Timing statistics (embedding and extraction)
                - Visual quality results (PSNR, SSIM, LPIPS, FID)
                - Robustness results under various attacks
                - Base64-encoded visual comparisons

        Raises:
            RuntimeError: If dataloader type cannot be determined (neither image nor prompt detected).
            AssertionError: If mode is not "encode" or "decode".
        """
        # Route to appropriate evaluation lab based on input data type
        assert fid_dataset in ["MS-COCO-2017-VAL"]
        if _is_igw(dataloader):
            # Input contains prompts → In-Generation Watermarking
            combined_result = self.igw_lab.test(
                watermark_model=watermark_model,
                dataloader=dataloader,
                fid_dataset=fid_dataset,
                fid_batchsize=fid_batchsize,
                device=device,
                need_cover=need_cover
            )
        else:
            # Input contains images → Post-Generation Watermarking
            combined_result = self.pgw_lab.test(
                watermark_model=watermark_model,
                dataloader=dataloader,
                fid_dataset=fid_dataset,
                fid_batchsize=fid_batchsize,
                device=device
            )

        return combined_result
