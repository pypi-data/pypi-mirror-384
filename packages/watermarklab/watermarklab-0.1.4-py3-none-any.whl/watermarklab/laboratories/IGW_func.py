# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT
import time
import json
import torch
import shutil
import os.path
import numpy as np
from PIL import Image
from tqdm import tqdm
from typing import List
from cleanfid import fid

# Import core components from the watermarking framework
from watermarklab.utils.basemodel import *
from watermarklab.laboratories.utils import (
    _reshape_secret,
    _delete_in_thread,
    _get_system_info,
    _get_base64_images,
    _remove_empty_lists,
    _composite_image_with_secret, replace_infinity, _remove_evaluated_attacker
)
from watermarklab.metrics.metrics4test import *
from watermarklab.attackers.testattackers import Identity
from watermarklab.datasets.datasets import _download_and_extract_hf, MS_COCO_2017_VAL_IMAGES, MS_COCO_2017_VAL_PROMPTS
from watermarklab.utils.data import (
    DataLoader,
    DecodeCleanCoverDataLoader,
    AttackTestRobustnessDataLoader,
    AttackedImageDataLoader
)


class IGWLab:
    """
    Evaluation laboratory for In-Generation Watermarking (IGW) models.

    This class orchestrates a comprehensive evaluation pipeline for watermarking models
    that embed watermarks during image generation (e.g., diffusion models, GANs).

    Key capabilities:
      - Watermark embedding during image generation
      - Visual quality assessment (PSNR, SSIM, LPIPS, FID)
      - Robustness testing under various noise attacks
      - Baseline extraction performance on clean images
      - Structured JSON reporting with Base64 visualizations
      - Support for both text-to-image and image-to-image watermarking

    Designed for research, benchmarking, and reproducible evaluation of IGW techniques.
    """

    def __init__(self,
                 save_path: str,
                 noise_models: List[AttackerWithFactors],
                 vqmetrics: List[BaseMetric] = None,
                 robustnessmetrics: List[BaseMetric] = None,
                 noise_save: bool = False):
        """
        Initialize the IGW evaluation lab.

        Args:
            save_path (str): Root directory for saving all experiment outputs.
            noise_models (List[AttackerWithFactors]): List of noise attack configurations to test robustness.
            vqmetrics (List[BaseMetric], optional): Visual quality metrics. Defaults to [PSNR(), SSIM(), LPIPS()].
            robustnessmetrics (List[BaseMetric], optional): Robustness metrics. Defaults to [BER(), EA()].
            noise_save (bool, optional): If True, preserves intermediate noised images. Otherwise, deletes them after decoding. Defaults to False.

        Note:
            Automatically appends an "Identity" attacker to establish a "No Attacking" baseline.
        """
        self.vqmetrics = vqmetrics or [PSNR(), SSIM(), LPIPS()]
        self.robustnessmetrics = robustnessmetrics or [BER(), EA()]
        self.save_path = save_path
        self.noise_save = noise_save

        # Add "No Attacking" baseline using Identity attacker
        self.noise_models = noise_models + [
            AttackerWithFactors(
                attacker=Identity(),
                attackername="No Attacking",
                factors=[None],
                factorsymbol="None"
            )
        ]

    def _encode_and_test(self,
                         watermark_model: BaseWatermarkModel,
                         dataloader: DataLoader,
                         fid_dataloader: DataLoader,
                         result_json: dict,
                         fid_batchsize: int = 64,
                         device: torch.device = "cuda",
                         need_cover: bool = False) -> dict:
        """
        Embed watermarks during image generation and evaluate visual quality.

        This method:
          - Generates images with embedded watermarks using provided prompts and secrets.
          - Saves clean (if available), stego, and residual images.
          - Computes per-image visual quality metrics (PSNR, SSIM, LPIPS).
          - Computes FID scores between generated images and a real reference dataset.

        Args:
            watermark_model (BaseWatermarkModel): IGW model to evaluate.
            dataloader (DataLoader): Provides prompts and secret bits for watermarking.
            fid_dataloader (DataLoader): Provides prompts for FID computation (typically larger dataset).
            fid_batchsize (int, optional): Batch size for FID computation. Default: 64.
            device (torch.device, optional): Device for FID computation. Default: "cuda".
            need_cover (bool, optional): If True, computes metrics using clean images as reference. Default: False.

        Returns:
            tuple: (
                visual_quality_result (Dict[str, List[float]]): Per-image metric values,
                embedding_time_cost (List[float]): Embedding time per image (seconds)
            )
        """
        if result_json["visualqualityresult"]:
            return result_json

        # Initialize metric storage for visual quality assessment
        visual_quality_result = {metric.metric_name: [] for metric in self.vqmetrics}

        # Define output directories for generated images
        model_save_path = os.path.join(self.save_path, f"{watermark_model.modelname}/images")
        os.makedirs(model_save_path, exist_ok=True)

        embedding_time_cost = []
        clean_images_unavailable = False

        # Progress bar for generation and embedding (main evaluation dataset)
        progress = tqdm(enumerate(dataloader),
                        desc=f"[\033[92mWatermarkLab\033[0m IGW] Model {watermark_model.modelname} Encoding",
                        ncols=shutil.get_terminal_size().columns,
                        total=len(dataloader))

        for batch_idx, (prompts, secrets, img_indices, iter_indices) in progress:
            progress.set_description(
                f"[\033[92mWatermarkLab\033[0m IGW] Model {watermark_model.modelname} Encoding - batch {batch_idx + 1}")

            # Generate watermarked images and measure time
            start_time = time.time()
            result = watermark_model.embed(prompts, secrets)
            end_time = time.time()

            batch_size = len(prompts)
            embedding_time_cost.append((end_time - start_time) / batch_size)

            # Process each generated image in the batch
            for clean_img, stego_img, prompt, secret_bits, img_idx, iter_idx in zip(
                    result.clean_img, result.stego_img, prompts, result.emb_bits, img_indices, iter_indices):

                # Create output directory for this specific image and iteration
                iter_path = os.path.join(model_save_path, f"image_{img_idx + 1}", f"iter_{iter_idx + 1}")
                os.makedirs(iter_path, exist_ok=True)

                # Save clean image and compute residual (if clean image is available)
                if clean_img is not None:
                    # Compute normalized residual for better visualization (amplified difference)
                    residual = (clean_img - stego_img) + 127.5
                    residual_normalized = np.round(np.clip(residual, 0, 255))
                    Image.fromarray(residual_normalized.astype(np.uint8)).save(os.path.join(iter_path, "residual.png"))
                    Image.fromarray(clean_img.astype(np.uint8)).save(os.path.join(iter_path, "clean.png"))
                else:
                    clean_images_unavailable = True

                # Save stego image (watermarked output)
                Image.fromarray(stego_img.astype(np.uint8)).save(os.path.join(iter_path, "stego.png"))

                # Save generation prompt for reference
                with open(os.path.join(iter_path, "prompt.json"), 'w') as f:
                    json.dump(prompt, f)

                # Save secret bits (handle both single and multi-bit cases)
                if len(secret_bits) > 1:
                    # Multi-bit watermark: save both visual and JSON representations
                    secret_list, secret_visual = _reshape_secret(secret_bits)
                    Image.fromarray(secret_visual.astype(np.uint8)).save(os.path.join(iter_path, "secret.png"))
                    with open(os.path.join(iter_path, "secret.json"), 'w') as f:
                        json.dump(secret_list, f)
                else:
                    # Single-bit watermark: save as JSON
                    with open(os.path.join(iter_path, "secret.json"), 'w') as f:
                        json.dump(secret_bits, f)

                # Compute visual quality metrics if clean image available and needed
                if clean_img is not None and need_cover:
                    for metric in self.vqmetrics:
                        metric_value = metric.test(clean_img, stego_img)
                        visual_quality_result[metric.metric_name].append(float(metric_value))

        # Directories for FID computation (separate from visualization images)
        fid_clean_dir = os.path.join(self.save_path, f"{watermark_model.modelname}/fid_cleans")
        fid_stego_dir = os.path.join(self.save_path, f"{watermark_model.modelname}/fid_stegos")
        real_dir = os.path.join(self.save_path, f"{watermark_model.modelname}/reals")
        os.makedirs(fid_clean_dir, exist_ok=True)
        os.makedirs(fid_stego_dir, exist_ok=True)
        os.makedirs(real_dir, exist_ok=True)

        # Progress bar for generation and embedding (FID dataset)
        progress = tqdm(enumerate(fid_dataloader),
                        desc=f"[\033[92mWatermarkLab\033[0m IGW] Model {watermark_model.modelname} FID Generation",
                        ncols=shutil.get_terminal_size().columns,
                        total=len(fid_dataloader))

        for batch_idx, (prompts, secrets, img_indices, iter_indices) in progress:
            progress.set_description(
                f"[\033[92mWatermarkLab\033[0m IGW] Model {watermark_model.modelname} FID Generation - batch {batch_idx + 1}")

            # Generate images for FID computation
            result = watermark_model.embed(prompts, secrets)

            # Process each generated image for FID
            for clean_img, stego_img, img_idx, iter_idx in zip(
                    result.clean_img, result.stego_img, img_indices, iter_indices):
                # Save clean and stego images for FID computation
                clean_img_path = os.path.join(fid_clean_dir, f"clean_{img_idx + 1}_{iter_idx + 1}.png")
                stego_img_path = os.path.join(fid_stego_dir, f"stego_{img_idx + 1}_{iter_idx + 1}.png")

                # Create directories and save images
                os.makedirs(os.path.dirname(clean_img_path), exist_ok=True)
                os.makedirs(os.path.dirname(stego_img_path), exist_ok=True)

                Image.fromarray(clean_img.astype(np.uint8)).save(clean_img_path)
                Image.fromarray(stego_img.astype(np.uint8)).save(stego_img_path)

        # Download and prepare real dataset for FID computation
        mscoco2017val_path = _download_and_extract_hf(
            "chenoly/watermarklab",
            "datasets/MSCOCO2017VAL.zip",
            "4f7e2ccb2866ec5041993c9cf2a952bbed69647b115d0f74da7ce8f4bef82f05",
            "MS-COCO-2017-VAL",
            local_files_only=True
        )
        real_images_folder = os.path.join(mscoco2017val_path, "val2017")

        # Sample real images to match generated dataset size for fair FID comparison
        real_image_files = [
            f for f in os.listdir(real_images_folder)
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))
        ]
        total_samples = int(len(dataloader.dataset) * dataloader.dataset.iter_num)
        np.random.seed(99)  # Fixed seed for reproducibility
        selected_files = np.random.choice(real_image_files, size=total_samples, replace=False)

        # Copy selected real images to comparison directory
        for filename in selected_files:
            shutil.copy2(os.path.join(real_images_folder, filename), os.path.join(real_dir, filename))

        # Compute FID scores between real images and generated images
        fid_clean = fid.compute_fid(real_dir, fid_clean_dir, batch_size=fid_batchsize, device=device) if not clean_images_unavailable else 'N/A'
        fid_stego = fid.compute_fid(real_dir, fid_stego_dir, batch_size=fid_batchsize, device=device)

        # Store FID results in the visual quality metrics dictionary
        visual_quality_result["FID"] = {
            "datasetname": fid_dataloader.dataset.dataset_name,
            "FID": {"stego": fid_stego, "clean": fid_clean}
        }

        result_json["time_cost"]["embed"] = embedding_time_cost
        result_json["visualcompare"]["stego"] = _get_base64_images(model_save_path, is_pgw=True),
        result_json["visualqualityresult"] = visual_quality_result
        result_file = os.path.join(model_save_path, f"result_{watermark_model.modelname}.json")
        with open(result_file, 'w') as f:
            json.dump(result_json, f, indent=4)
        return result_json

    def _decode_clean_cover(self, watermark_model: BaseWatermarkModel, batch_size: int, result_json: dict) -> dict:
        """
        Evaluate watermark extraction performance on clean (unattacked) cover images.

        This establishes a baseline for False Positive Rate (FPR):
          - A robust watermark decoder should achieve high accuracy on clean watermarked images.
          - Used later for TPR@FPR calculations.

        Args:
            watermark_model (BaseWatermarkModel): Watermark model to evaluate.
            batch_size (int): Batch size for decoding operations.

        Returns:
            tuple: (
                org_metric_w (List[float]): List of extraction accuracy scores on clean images,
                extract_time_cost (List[float]): Extraction time per image (seconds)
            )
        """
        if len(result_json["time_cost"]["extract"]) > 0:
            return result_json

        # Determine dataset structure from saved images
        model_path = os.path.join(self.save_path, f"{watermark_model.modelname}")
        images_path = os.path.join(model_path, "images")

        # Count images and iterations to configure data loader
        img_count = len([d for d in os.listdir(images_path) if os.path.isdir(os.path.join(images_path, d))])
        iter_path = os.path.join(images_path, "image_1")
        iter_count = len([d for d in os.listdir(iter_path) if os.path.isdir(os.path.join(iter_path, d))])

        # Create data loader for clean images (loads previously generated clean images)
        decode_loader = DecodeCleanCoverDataLoader(images_path, img_count, iter_count, batch_size)

        # Progress bar for decoding clean images
        progress = tqdm(decode_loader,
                        desc=f"[\033[92mWatermarkLab\033[0m IGW] {watermark_model.modelname}: Decode (Clean)",
                        ncols=shutil.get_terminal_size().columns,
                        leave=False)

        org_metric_w = []
        extract_time_cost = []

        if len(decode_loader) > 0:
            for secrets, clean_images in progress:
                # Extract watermarks from clean images and measure time
                start_time = time.time()
                extraction_result = watermark_model.extract(clean_images)
                end_time = time.time()

                batch_size_actual = len(clean_images)
                extract_time_cost.append((end_time - start_time) / batch_size_actual)

                # Compute extraction accuracy for each image
                if len(extraction_result.ext_bits[0]) > 1:
                    # Multi-bit watermark: compute accuracy per image
                    for original_secret, extracted_secret in zip(secrets, extraction_result.ext_bits):
                        accuracy = EA().test(original_secret, extracted_secret)
                        org_metric_w.append(accuracy)
                else:
                    # Single-bit watermark: flatten list of bits
                    for bit in extraction_result.ext_bits:
                        org_metric_w += bit

                progress.set_description(
                    f"[\033[92mWatermarkLab\033[0m IGW] {watermark_model.modelname}: Decode (Clean)")

        result_json["org_metric_w"] = org_metric_w
        result_json["time_cost"]["extract"] = extract_time_cost
        result_file = os.path.join(model_path, f"result_{watermark_model.modelname}.json")
        with open(result_file, 'w') as f:
            json.dump(result_json, f, indent=4)
        return result_json

    def _attack_decode_test(self, watermark_model: BaseWatermarkModel,
                            batch_size_noise_decode: int,
                            result_json: dict) -> dict:
        """
        Evaluate watermark robustness under various noise attacks.

        For each attack type and intensity:
          1. Load clean stego images
          2. Apply noise attack
          3. Extract watermark from attacked images
          4. Compute visual quality and robustness metrics
          5. Generate Base64 visualization for representative samples

        Args:
            watermark_model (BaseWatermarkModel): Watermark model to test.
            batch_size_noise_decode (int): Batch size for decoding operations.
            result_json: Current result dictionary

        Returns:
            dict: Updated result_json
        """
        model_path = os.path.join(self.save_path, f"{watermark_model.modelname}")
        noise_output_path = os.path.join(model_path, "noise")
        os.makedirs(noise_output_path, exist_ok=True)
        org_metric_w = result_json["org_metric_w"]

        robustness_result = {}

        total_factors = sum(len(noise_model.factors) for noise_model in self.noise_models)

        with tqdm(total=total_factors,
                  desc=f"[\033[92mWatermarkLab\033[0m PGW] {watermark_model.modelname} Robustness Testing",
                  ncols=shutil.get_terminal_size().columns) as pbar:

            # Process each noise model
            for noise_model in self.noise_models:
                noise_type = noise_model.attackername

                if noise_type not in robustness_result:
                    robustness_result[noise_type] = {
                        "factors": {},
                        "noisename": noise_type,
                        "factor_inversely_related": noise_model.attacker.factor_inversely_related,
                        "factorsymbol": noise_model.factorsymbol
                    }

                # Test each attack intensity
                for factor in noise_model.factors:
                    factor_str = str(factor)
                    ext_metric_w = []  # Collect extraction metrics for TPR@FPR
                    save_dir = os.path.join(noise_output_path, noise_type, factor_str)
                    os.makedirs(save_dir, exist_ok=True)

                    # Initialize metric storage for this factor
                    if factor_str not in robustness_result[noise_type]["factors"]:
                        robustness_result[noise_type]["factors"][factor_str] = {
                            metric.metric_name: [] for metric in self.robustnessmetrics
                        }
                        robustness_result[noise_type]["factors"][factor_str]["visualquality"] = {
                            metric.metric_name: [] for metric in self.vqmetrics
                        }

                    # Load clean stego images
                    images_dir = os.path.join(model_path, "images")
                    attack_loader = AttackTestRobustnessDataLoader(save_dir, images_dir, batch_size_noise_decode)

                    # Apply attacks
                    attack_progress = tqdm(attack_loader,
                                           desc=f"Attacking: {noise_type} ({noise_model.factorsymbol}={factor})",
                                           ncols=shutil.get_terminal_size().columns,
                                           total=len(attack_loader),
                                           leave=False)

                    for cover_images, stego_images, secrets, output_paths in attack_progress:
                        # Apply noise attack
                        noised_images = noise_model.attacker.attack(stego_images, cover_images, factor)

                        # Save noised images and compute visual quality metrics
                        for cover_img, stego_img, noised_img, output_path in zip(
                                cover_images, stego_images, noised_images, output_paths):

                            os.makedirs(output_path, exist_ok=True)

                            # Save noised image
                            Image.fromarray(np.uint8(np.clip(noised_img, 0., 255.))).save(
                                os.path.join(output_path, "noised.png"))

                            # Save residual (difference between stego and noised)
                            residual = (noised_img - stego_img) * 10. + 127.5
                            Image.fromarray(np.uint8(np.clip(residual, 0., 255.))).save(
                                os.path.join(output_path, "residual.png"))

                            # Compute visual quality metrics (skip for "No Attacking")
                            if noise_type != "No Attacking":
                                for metric in self.vqmetrics:
                                    metric_value = metric.test(noised_img, stego_img)
                                    robustness_result[noise_type]["factors"][factor_str]["visualquality"][
                                        metric.metric_name].append(float(metric_value))

                    # Load attacked images and extract watermarks
                    decode_loader = AttackedImageDataLoader(save_dir, images_dir, batch_size_noise_decode)
                    decode_progress = tqdm(decode_loader,
                                           desc=f"Decoding: {noise_type} ({noise_model.factorsymbol}={factor})",
                                           ncols=int(shutil.get_terminal_size().columns),
                                           total=len(attack_loader),
                                           leave=False)

                    for secrets, attacked_images, output_paths in decode_progress:
                        # Extract watermarks
                        extraction_result = watermark_model.extract(attacked_images)
                        # Process each extraction result
                        for original_secret, extracted_secret, output_path in zip(
                                secrets, extraction_result.ext_bits, output_paths):

                            if len(original_secret) > 1:
                                # Multi-bit watermark: save visualization and compute metrics
                                secret_json, secret_png = _reshape_secret(extracted_secret)
                                Image.fromarray(secret_png.astype(np.uint8)).save(
                                    os.path.join(output_path, "ext_secret.png"))
                                with open(os.path.join(output_path, "ext_secret.json"), 'w') as f:
                                    json.dump(extracted_secret, f, indent=4)

                                # Compute robustness metrics
                                for metric in self.robustnessmetrics:
                                    if not isinstance(metric, TPR_AT_N_PERCENT_FPR):
                                        metric_value = metric.test(original_secret, extracted_secret)
                                        robustness_result[noise_type]["factors"][factor_str][metric.metric_name].append(
                                            float(metric_value))
                                        if metric.metric_name == "Extract Accuracy":
                                            ext_metric_w.append(float(metric_value))
                            else:
                                # Single-bit watermark
                                ext_metric_w += extracted_secret

                    # Compute TPR@FPR if applicable
                    for metric in self.robustnessmetrics:
                        if isinstance(metric, TPR_AT_N_PERCENT_FPR) and len(org_metric_w) > 0:
                            robustness_result[noise_type]["factors"][factor_str]['clean_detected_value'] = org_metric_w
                            robustness_result[noise_type]["factors"][factor_str]['stego_detected_value'] = ext_metric_w
                            robustness_result[noise_type]["factors"][str(factor)][metric.metric_name] = metric.test(
                                org_metric_w, ext_metric_w)
                            break

                    # Generate Base64 visualization for medium-intensity attack
                    if str(factor) == result_json["visualcompare"]["noisefactor"][noise_type]:
                        secret_png_path = os.path.join(save_dir, "image_1", "iter_1", "ext_secret.png")
                        attacked_stego_path = os.path.join(save_dir, "image_1", "iter_1", "noised.png")
                        if os.path.exists(secret_png_path):
                            secret_png = Image.open(secret_png_path)
                        else:
                            secret_png = None
                        attacked_stego = Image.open(attacked_stego_path)
                        result_json["visualcompare"]["noise"][noise_type] = _composite_image_with_secret(attacked_stego,
                                                                                                         secret_png)

                    # Clean up if not saving noise images
                    if not self.noise_save:
                        _delete_in_thread(save_dir)

                    result_json["robustnessresult"][noise_type]["factors"][factor_str] = \
                        robustness_result[noise_type]["factors"][factor_str]
                    result_file = os.path.join(model_path, f"result_{watermark_model.modelname}.json")
                    with open(result_file, 'w') as f:
                        json.dump(result_json, f, indent=4)

                    pbar.update(1)
                    pbar.set_postfix({"Attack": noise_type, "Factor": str(factor)})

        return result_json

    def test(self, watermark_model: BaseWatermarkModel,
             dataloader: DataLoader,
             fid_dataset: str = "MS-COCO-2017-VAL",
             fid_batchsize: int = 32,
             device: torch.device = "cuda",
             need_cover: bool = False) -> dict:
        """
        Execute full evaluation pipeline for PGW model.
        Generates comprehensive JSON report with all metrics and visualizations.

        Args:
            watermark_model (BaseWatermarkModel): Model to evaluate.
            dataloader (DataLoader): Data provider.
            fid_batchsize (int, optional): Batch size for FID computation. Default: 32.
            device (torch.device, optional): Device for computations. Default: "cpu".

        Returns:
            dict: Comprehensive evaluation results including:
                - Model metadata
                - Dataset and environment info
                - Timing statistics
                - Visual quality metrics
                - Robustness metrics
                - Base64 visualizations
        """
        assert fid_dataset in ["MS-COCO-2017-VAL"]

        model_save_path = os.path.join(self.save_path, f"{watermark_model.modelname}")
        result_file_path = os.path.join(model_save_path, f"result_{watermark_model.modelname}.json")
        if os.path.exists(result_file_path):
            with open(result_file_path, 'r') as f:
                result_json = json.load(f)
        else:
            # Compile final report
            result_json = {
                "modelname": watermark_model.modelname,
                "modeltype": 'In-Generation Watermark',
                "description": watermark_model.description,
                "imagesize": watermark_model.img_size,
                "payload": watermark_model.bits_len,
                "testdataset": dataloader.dataset.dataset_name,
                "testvisualqualitymetrics": [metric.metric_name for metric in self.vqmetrics],
                "testrobustnessmetrics": [metric.metric_name for metric in self.robustnessmetrics],
                "envinfo": _get_system_info(),
                "time_cost": {
                    'embed': [],
                    'extract': []
                },
                "visualqualityresult": {},
                "robustnessresult": {
                    attacker.attackername: {"factors": {str(factor): {} for factor in attacker.factors}} for attacker in
                    self.noise_models},
                "visualcompare": {
                    "stego": {},
                    "noise": {},
                    "noisefactor": {
                        attacker.attackername: [str(factor) for factor in attacker.factors][len(attacker.factors) // 2]
                        for attacker in self.noise_models}
                }
            }

        # Initialize FID dataset for evaluation
        if fid_dataset == "MS-COCO-2017-VAL":
            fid_dataset = MS_COCO_2017_VAL_PROMPTS(dataloader.dataset.bit_len, dataloader.dataset.iter_num)
            fid_dataloader = DataLoader(fid_dataset, batch_size=dataloader.batch_size)
        else:
            # This branch will never execute due to the assert above, but kept for completeness
            fid_dataset = MS_COCO_2017_VAL_PROMPTS(dataloader.dataset.bit_len, dataloader.dataset.iter_num)
            fid_dataloader = DataLoader(fid_dataset, batch_size=dataloader.batch_size)

        # Encoding and visual quality assessment
        result_json = self._encode_and_test(
            watermark_model, dataloader, fid_dataloader, result_json, fid_batchsize, device, need_cover
        )
        # Evaluate baseline performance on clean images
        result_json = self._decode_clean_cover(
            watermark_model, dataloader.batch_size, result_json
        )

        # Evaluate robustness under noise attacks
        self.noise_models = _remove_evaluated_attacker(result_json, self.noise_models)
        result_json = self._attack_decode_test(
            watermark_model, dataloader.batch_size, result_json
        )
        result_json = _remove_empty_lists(result_json)
        final_report = replace_infinity(result_json)
        result_file = os.path.join(model_save_path, f"result_{watermark_model.modelname}.json")
        with open(result_file, 'w') as f:
            json.dump(final_report, f, indent=4)
        return final_report