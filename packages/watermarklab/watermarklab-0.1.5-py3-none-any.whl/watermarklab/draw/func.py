# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT
"""
WatermarkLab: Visualization and Analysis Module

This module provides functions to generate publication-quality plots for watermarking research,
including visual comparisons, quality metrics, and robustness analysis.
"""

import os
import json
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from typing import List, Union, Dict, Any, Tuple
from scipy.interpolate import interpolate

from watermarklab.draw.utils import (
    _extract_multi_value_metrics,
    _extract_all_psnr_values,
    _extract_fid_data,
    _extract_robustness_data,
    _get_consistent_colors,
    _get_model_type,
    _load_results,
    _resize_image,
    _save_figure,
    _save_figure_with_tight_crop,
    _base64_to_image,
    _create_stylish_plot,
    _count_valid_factors,
    _compute_auc_scores, _extract_robustness_curve_data, _is_accuracy_metric,
)
from watermarklab.metrics import ssim


def plot_stego_visualization(
        input_results: List[Union[str, Dict[str, Any]]],
        save_path: str
) -> None:
    """
    Plot stego visualization for all models in horizontal layout.

    This function generates a comprehensive horizontal visualization showing the cover/clean image,
    stego image, and residual image for each model. It intelligently handles different model types
    (PGW/IGW) and avoids duplicate cover images for PGW models.

    Args:
        input_results (List[Union[str, Dict[str, Any]]]):
            A list of file paths (str) or result dictionaries containing visual comparison data.

        save_path (str):
            Directory where the generated PDF plot will be saved.
    """
    # Load results from file paths or dictionaries
    results = _load_results(input_results)
    if not results:
        return

    # Define target image size for consistent layout
    cover_target_size = 256
    half_width = cover_target_size // 2
    half_height = cover_target_size // 2

    # Store unique cover images to avoid duplicates for PGW models
    unique_covers = []  # List of (cover_image, model_names) tuples
    cover_threshold_metric = 0.9  # SSIM threshold for duplicate detection

    # Calculate initial figure size based on number of models
    num_models = len(results)
    fig_width = max(20, num_models * 15)  # Dynamically adjust width
    fig_height = 10  # Fixed height for readability

    # Create figure and configure axes
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.set_aspect('equal')
    ax.axis('off')

    # Track content boundaries for tight cropping
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')

    # Plot each model's visualization
    current_x = 50  # Initial x offset for better layout
    for i, result in enumerate(results):
        model_name = result.get('modelname', f'Model_{i + 1}')
        model_type = _get_model_type(result)

        # Validate required data exists
        if 'visualcompare' not in result or 'stego' not in result['visualcompare']:
            continue

        stego_data = result['visualcompare']['stego']

        # Determine if we have a cover/clean image
        has_left_image = False
        left_image_type = ""
        left_image = None
        should_show_cover = True  # Flag to determine if cover should be shown

        # Handle PGW models (use cover image)
        if model_type == 'PGW' and 'cover' in stego_data:
            left_image = _base64_to_image(stego_data['cover'])
            if left_image is not None:
                has_left_image = True
                left_image_type = "Cover"

                # Check if this cover is similar to existing covers (for PGW models)
                left_image_resized = _resize_image(left_image, cover_target_size, cover_target_size)
                is_duplicate = False
                for existing_cover, existing_model_names in unique_covers:
                    metrics_value = ssim(left_image_resized, existing_cover)
                    if metrics_value > cover_threshold_metric:
                        is_duplicate = True
                        existing_model_names.append(model_name)
                        break

                if not is_duplicate:
                    unique_covers.append((left_image_resized, [model_name]))
                else:
                    should_show_cover = False  # Don't show duplicate cover

        # Handle IGW models (use clean image)
        elif model_type == 'IGW' and 'clean' in stego_data:
            left_image = _base64_to_image(stego_data['clean'])
            if left_image is not None:
                has_left_image = True
                left_image_type = "Clean"

        # Get stego and residual images
        stego_image = _base64_to_image(stego_data.get('stego'))
        residual_image = _base64_to_image(stego_data.get('residual'))

        # Resize images appropriately
        if left_image is not None and should_show_cover:
            left_image = _resize_image(left_image, cover_target_size, cover_target_size)

        # Determine stego image sizing strategy
        if stego_image is not None:
            # Special case: IGW without clean/residual - show stego at full size
            if model_type == 'IGW' and not has_left_image and residual_image is None:
                stego_image = _resize_image(stego_image, cover_target_size, cover_target_size)
            elif residual_image is not None:
                # Has both stego and residual - show both at half size (256x256)
                stego_image = _resize_image(stego_image, half_width, half_height)
                residual_image = _resize_image(residual_image, half_width, half_height)
            else:
                # Other cases - show stego at half size
                stego_image = _resize_image(stego_image, half_width, half_height)

        if residual_image is not None:
            residual_image = _resize_image(residual_image, half_width, half_height)

        # Calculate positions - ALL MODELS USE SAME LOGIC
        if has_left_image and should_show_cover:
            # Layout with left image
            left_start_x = current_x

            # Add left image type label and track bounds
            ax.text(left_start_x + cover_target_size / 2, 45, left_image_type, ha='center', va='center', fontsize=24,
                    fontweight='bold')
            min_x = min(min_x, left_start_x)
            max_x = max(max_x, left_start_x + cover_target_size)
            min_y = min(min_y, 30)
            max_y = max(max_y, 30)

            # Display left image (512x512) and track bounds
            if left_image is not None:
                ax.imshow(left_image,
                          extent=[left_start_x, left_start_x + cover_target_size, 70, 70 + cover_target_size])
                min_x = min(min_x, left_start_x)
                max_x = max(max_x, left_start_x + cover_target_size)
                min_y = min(min_y, 70)
                max_y = max(max_y, 70 + cover_target_size)

            # Right area: stego + residual vertical stack (no gaps)
            right_start_x = left_start_x + cover_target_size + 20

            # Add model name and track bounds
            ax.text(right_start_x + half_width / 2, 45, model_name, ha='center', va='center', fontsize=24,
                    fontweight='bold')
            min_x = min(min_x, right_start_x)
            max_x = max(max_x, right_start_x + half_width)
            min_y = min(min_y, 30)
            max_y = max(max_y, 30)

            # Calculate stego and residual positions (vertical stack with no gap) and track bounds
            if stego_image is not None and residual_image is not None:
                # Both images: each half height
                half_height_local = cover_target_size // 2
                # Stego on top (first half)
                ax.imshow(stego_image, extent=[right_start_x, right_start_x + half_width, 70, 70 + half_height_local])
                min_x = min(min_x, right_start_x)
                max_x = max(max_x, right_start_x + half_width)
                min_y = min(min_y, 70)
                max_y = max(max_y, 70 + half_height_local)
                # Residual on bottom (second half)
                ax.imshow(residual_image, extent=[right_start_x, right_start_x + half_width, 70 + half_height_local,
                                                  70 + cover_target_size])
                min_x = min(min_x, right_start_x)
                max_x = max(max_x, right_start_x + half_width)
                min_y = min(min_y, 70 + half_height_local)
                max_y = max(max_y, 70 + cover_target_size)
            elif stego_image is not None:
                # Only stego: full height
                ax.imshow(stego_image, extent=[right_start_x, right_start_x + half_width, 70, 70 + cover_target_size])
                min_x = min(min_x, right_start_x)
                max_x = max(max_x, right_start_x + half_width)
                min_y = min(min_y, 70)
                max_y = max(max_y, 70 + cover_target_size)
            elif residual_image is not None:
                # Only residual: full height
                ax.imshow(residual_image,
                          extent=[right_start_x, right_start_x + half_width, 70, 70 + cover_target_size])
                min_x = min(min_x, right_start_x)
                max_x = max(max_x, right_start_x + half_width)
                min_y = min(min_y, 70)
                max_y = max(max_y, 70 + cover_target_size)

            current_x += cover_target_size + half_width + 40

        elif has_left_image and not should_show_cover:
            # Layout with left image but don't show cover (duplicate)
            right_start_x = current_x

            # Add model name and track bounds
            ax.text(right_start_x + half_width / 2, 45, model_name, ha='center', va='center', fontsize=24,
                    fontweight='bold')
            min_x = min(min_x, right_start_x)
            max_x = max(max_x, right_start_x + half_width)
            min_y = min(min_y, 30)
            max_y = max(max_y, 30)

            # Calculate stego and residual positions (vertical stack with no gap) and track bounds
            if stego_image is not None and residual_image is not None:
                # Both images: each half height
                half_height_local = cover_target_size // 2
                # Stego on top (first half)
                ax.imshow(stego_image, extent=[right_start_x, right_start_x + half_width, 70, 70 + half_height_local])
                min_x = min(min_x, right_start_x)
                max_x = max(max_x, right_start_x + half_width)
                min_y = min(min_y, 70)
                max_y = max(max_y, 70 + half_height_local)
                # Residual on bottom (second half)
                ax.imshow(residual_image, extent=[right_start_x, right_start_x + half_width, 70 + half_height_local,
                                                  70 + cover_target_size])
                min_x = min(min_x, right_start_x)
                max_x = max(max_x, right_start_x + half_width)
                min_y = min(min_y, 70 + half_height_local)
                max_y = max(max_y, 70 + cover_target_size)
            elif stego_image is not None:
                # Only stego: full height
                ax.imshow(stego_image, extent=[right_start_x, right_start_x + half_width, 70, 70 + cover_target_size])
                min_x = min(min_x, right_start_x)
                max_x = max(max_x, right_start_x + half_width)
                min_y = min(min_y, 70)
                max_y = max(max_y, 70 + cover_target_size)
            elif residual_image is not None:
                # Only residual: full height
                ax.imshow(residual_image,
                          extent=[right_start_x, right_start_x + half_width, 70, 70 + cover_target_size])
                min_x = min(min_x, right_start_x)
                max_x = max(max_x, right_start_x + half_width)
                min_y = min(min_y, 70)
                max_y = max(max_y, 70 + cover_target_size)

            current_x += half_width + 20

        else:
            # Layout without left image (IGW without clean)
            # Only right area with stego + residual vertical stack
            # Add model name at the top and track bounds
            model_display_width = cover_target_size if (
                    model_type == 'IGW' and stego_image is not None and residual_image is None and not has_left_image) else half_width
            ax.text(current_x + model_display_width / 2, 45, model_name, ha='center', va='center', fontsize=24,
                    fontweight='bold')
            min_x = min(min_x, current_x)
            max_x = max(max_x, current_x + model_display_width)
            min_y = min(min_y, 30)
            max_y = max(max_y, 30)

            # Special case: IGW without clean/residual - show stego at full size
            if model_type == 'IGW' and stego_image is not None and not has_left_image and residual_image is None:
                # Show stego at full size (512x512) and track bounds
                ax.imshow(stego_image, extent=[current_x, current_x + cover_target_size, 70, 70 + cover_target_size])
                min_x = min(min_x, current_x)
                max_x = max(max_x, current_x + cover_target_size)
                min_y = min(min_y, 70)
                max_y = max(max_y, 70 + cover_target_size)

                # Add prompt for IGW models (below the stego image) and track bounds
                if 'prompt' in stego_data:
                    prompt_text = stego_data['prompt']
                    if isinstance(prompt_text, dict):
                        prompt_text = json.dumps(prompt_text)
                    elif not isinstance(prompt_text, str):
                        prompt_text = str(prompt_text)
                    prompt_start_y = 70 + cover_target_size + 20
                    # Truncate long prompt text and wrap it
                    if len(prompt_text) > 50:
                        prompt_text = prompt_text[:47] + "..."
                    ax.text(current_x + cover_target_size / 2, prompt_start_y, f"Prompt: {prompt_text}", ha='center',
                            va='center', fontsize=10, wrap=True)
                    min_x = min(min_x, current_x)
                    max_x = max(max_x, current_x + cover_target_size)
                    min_y = min(min_y, prompt_start_y - 10)
                    max_y = max(max_y, prompt_start_y + 10)

                current_x += cover_target_size + 20
            else:
                # Calculate positions for stego and residual (vertical stack with no gap) and track bounds
                if stego_image is not None and residual_image is not None:
                    # Both images: each half height
                    half_height_local = cover_target_size // 2
                    # Stego on top (first half)
                    ax.imshow(stego_image, extent=[current_x, current_x + half_width, 70, 70 + half_height_local])
                    min_x = min(min_x, current_x)
                    max_x = max(max_x, current_x + half_width)
                    min_y = min(min_y, 70)
                    max_y = max(max_y, 70 + half_height_local)
                    # Residual on bottom (second half)
                    ax.imshow(residual_image, extent=[current_x, current_x + half_width, 70 + half_height_local,
                                                      70 + cover_target_size])
                    min_x = min(min_x, current_x)
                    max_x = max(max_x, current_x + half_width)
                    min_y = min(min_y, 70 + half_height_local)
                    max_y = max(max_y, 70 + cover_target_size)
                elif stego_image is not None:
                    # Only stego: full height
                    ax.imshow(stego_image, extent=[current_x, current_x + half_width, 70, 70 + cover_target_size])
                    min_x = min(min_x, current_x)
                    max_x = max(max_x, current_x + half_width)
                    min_y = min(min_y, 70)
                    max_y = max(max_y, 70 + cover_target_size)
                elif residual_image is not None:
                    # Only residual: full height
                    ax.imshow(residual_image, extent=[current_x, current_x + half_width, 70, 70 + cover_target_size])
                    min_x = min(min_x, current_x)
                    max_x = max(max_x, current_x + half_width)
                    min_y = min(min_y, 70)
                    max_y = max(max_y, 70 + cover_target_size)

                # Add prompt for IGW models (below the images) and track bounds
                if model_type == 'IGW' and 'prompt' in stego_data:
                    prompt_text = stego_data['prompt']
                    if isinstance(prompt_text, dict):
                        prompt_text = json.dumps(prompt_text)
                    elif not isinstance(prompt_text, str):
                        prompt_text = str(prompt_text)
                    prompt_start_y = 70 + cover_target_size + 20
                    # Truncate long prompt text and wrap it
                    if len(prompt_text) > 50:
                        prompt_text = prompt_text[:47] + "..."
                    ax.text(current_x + half_width / 2, prompt_start_y, f"Prompt: {prompt_text}", ha='center',
                            va='center', fontsize=24, wrap=True)
                    min_x = min(min_x, current_x)
                    max_x = max(max_x, current_x + half_width)
                    min_y = min(min_y, prompt_start_y - 10)
                    max_y = max(max_y, prompt_start_y + 10)

                current_x += half_width + 20

    # Set final axis limits based on content bounds with small margins
    if min_x != float('inf') and max_x != float('-inf') and min_y != float('inf') and max_y != float('-inf'):
        margin = 20
        ax.set_xlim(min_x - margin, max_x + margin)
        ax.set_ylim(min_y - margin, max_y + margin)
    else:
        # Fallback if no content was plotted
        ax.set_xlim(0, current_x)
        ax.set_ylim(0, cover_target_size + 200)

    # Save plot with tight cropping
    filename = "stego_visualization.pdf"
    _save_figure_with_tight_crop(fig, save_path, filename)


def plot_attack_visualization(
        input_results: List[Union[str, Dict[str, Any]]],
        save_path: str
) -> None:
    """
    Plot noise visualization for each model separately.

    This function generates a separate PDF for each model, showing all available noise attack
    visualizations in a grid layout.

    Args:
        input_results (List[Union[str, Dict[str, Any]]]):
            A list of file paths (str) or result dictionaries containing noise visualization data.

        save_path (str):
            Directory where the generated PDF plots will be saved.
    """
    # Load results and create save directory
    os.makedirs(save_path, exist_ok=True)
    results = _load_results(input_results)
    if not results:
        return

    # Process each model
    for result in results:
        model_name = result.get('modelname', 'Unknown')
        if 'visualcompare' not in result or 'noise' not in result['visualcompare']:
            continue

        noise_data = result['visualcompare']['noise']

        # Get noise types and filter out None values
        noise_items = [(k, v) for k, v in noise_data.items() if v is not None]
        if not noise_items:
            continue

        # Calculate layout
        images_per_row = 8
        num_rows = (len(noise_items) + images_per_row - 1) // images_per_row

        # Calculate figure size
        fig_width = 24
        fig_height = max(12, num_rows * 4)
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        ax.set_aspect('equal')
        ax.axis('off')

        # Track content boundaries for tight cropping
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')

        # Add title and track bounds
        title_obj = ax.text(fig_width * 50, 30, f"Noise Attack Visualization - Model: {model_name}",
                            ha='center', va='center', fontsize=20, fontweight='bold')
        min_x = min(min_x, 0)
        max_x = max(max_x, fig_width * 100)
        min_y = min(min_y, 30 - 10)
        max_y = max(max_y, 30 + 10)

        # Image size and layout parameters
        image_width = 200
        image_height = 200
        label_height = 30
        spacing_x = 250
        spacing_y = 280

        # Starting positions
        start_x = 100
        start_y = 80

        # Plot noise images
        for i, (noise_type, base64_image) in enumerate(noise_items):
            row = i // images_per_row
            col = i % images_per_row

            # Calculate position
            x_pos = start_x + col * spacing_x
            y_pos = start_y + row * spacing_y

            # Add noise type label and track bounds
            ax.text(x_pos + image_width / 2, y_pos + label_height / 2, noise_type, ha='center', va='center',
                    fontsize=10, fontweight='bold')
            min_x = min(min_x, x_pos)
            max_x = max(max_x, x_pos + image_width)
            min_y = min(min_y, y_pos + label_height / 2 - 5)
            max_y = max(max_y, y_pos + label_height / 2 + 5)

            # Display image and track bounds
            image = _base64_to_image(base64_image)
            if image is not None:
                ax.imshow(image, extent=[x_pos, x_pos + image_width, y_pos + label_height,
                                         y_pos + label_height + image_height])
                min_x = min(min_x, x_pos)
                max_x = max(max_x, x_pos + image_width)
                min_y = min(min_y, y_pos + label_height)
                max_y = max(max_y, y_pos + label_height + image_height)

        # Set final axis limits based on content bounds with margins
        if min_x != float('inf') and max_x != float('-inf') and min_y != float('inf') and max_y != float('-inf'):
            margin = 30
            ax.set_xlim(min_x - margin, max_x + margin)
            ax.set_ylim(min_y - margin, max_y + margin)
        else:
            # Fallback if no content was plotted
            ax.set_xlim(0, fig_width * 100)
            ax.set_ylim(0, (num_rows + 1) * 300)

        # Save plot with tight cropping
        filename = f"{model_name}_noise_visualization.pdf"
        _save_figure_with_tight_crop(fig, save_path, filename)


def plot_visualization_comparison(
        input_results: List[Union[str, Dict[str, Any]]],
        save_path: str
) -> None:
    """
    Plot all visual comparisons including stego and noise visualizations.

    This function orchestrates the generation of both stego visualization (horizontal layout)
    and noise visualization (per-model PDFs).

    Args:
        input_results (List[Union[str, Dict[str, Any]]]):
            A list of file paths (str) or result dictionaries containing visualization data.

        save_path (str):
            Directory where the generated PDF plots will be saved.
    """
    # Create save directory
    os.makedirs(save_path, exist_ok=True)

    # Plot stego visualization
    plot_stego_visualization(input_results, save_path)

    # Plot noise visualization for each model
    plot_attack_visualization(input_results, save_path)  # Note: Function name corrected from original


def plot_multi_value_metrics(
        input_results: List[Union[str, Dict[str, Any]]],
        save_path: str,
        figsize: tuple = (6, 3),
        style: str = 'whitegrid',
        xtick_rotation: bool = True
) -> None:
    """
    Plot multi-value visual quality metrics using violin plots.

    This function generates violin plots for metrics like PSNR, SSIM, and LPIPS. Each model's
    distribution of metric values is visualized with consistent coloring across plots.

    Args:
        input_results (List[Union[str, Dict[str, Any]]]):
            A list of file paths (str) or result dictionaries containing visual quality data.

        save_path (str):
            Directory where the generated PDF plots will be saved.

        figsize (tuple, optional):
            Figure size as (width, height). Defaults to (12, 8).

        style (str, optional):
            Seaborn style for the plot appearance. Defaults to 'whitegrid'.

        xtick_rotation (bool, optional):
            Whether to rotate x-axis labels by 45 degrees for better readability. Defaults to True.
    """
    # Load results from file paths or dictionaries
    results = _load_results(input_results)

    if not results:
        return

    # Extract multi-value metrics (e.g., PSNR, SSIM, LPIPS)
    metrics_data = _extract_multi_value_metrics(results)

    if not metrics_data:
        return

    # Collect all model names for consistent color mapping
    all_model_names = []
    for metric_data in metrics_data.values():
        all_model_names.extend(metric_data.keys())
    model_colors = _get_consistent_colors(all_model_names)

    # Plot each metric
    for metric, model_data in metrics_data.items():
        if not model_data:
            continue

        # Create a new plot with specified style and size
        fig, ax = _create_stylish_plot(figsize, style)

        # Prepare data for violin plot: list of lists (one per model)
        model_names = list(model_data.keys())
        data_to_plot = [model_data[model_name] for model_name in model_names]

        # Generate violin plot with mean and median indicators
        violin_parts = ax.violinplot(
            data_to_plot,
            positions=range(len(model_names)),
            showmeans=True,
            showmedians=True
        )

        # Apply consistent colors to each violin
        for i, (pc, model_name) in enumerate(zip(violin_parts['bodies'], model_names)):
            pc.set_facecolor(model_colors[model_name])
            pc.set_alpha(0.7)

        # Label the y-axis with the metric name
        ax.set_ylabel(metric, fontsize=14, fontweight='bold')

        # Set x-axis tick labels with model names
        ax.set_xticks(range(len(model_names)))
        if xtick_rotation:
            ax.set_xticklabels(model_names, rotation=45, ha='right', fontsize=14)
        else:
            ax.set_xticklabels(model_names, ha='center', fontsize=14)

        # --- Final Styling ---
        ax.grid(True, alpha=0.7, linestyle='-', linewidth=0.8, color='#cccccc')

        ax.set_facecolor('#f0f8ff')

        for spine in ax.spines.values():
            spine.set_edgecolor('none')
            spine.set_linewidth(0)

        # Save the plot as a PDF
        filename = f"{metric}_violinplot.pdf"
        _save_figure(fig, save_path, filename)


def plot_fid_metrics(
        input_results: List[Union[str, Dict[str, Any]]],
        save_path: str,
        figsize: tuple = (6, 3),
        style: str = 'whitegrid',
        xtick_rotation: bool = True,
        show_dataset_name: bool = True,
) -> None:
    """
    Plot FID metrics using a grouped bar chart for IGW models only.

    This function creates a grouped bar chart comparing Stego FID and Clean FID scores for each IGW model.
    It uses consistent coloring and adds dataset names on the bars for clarity.

    Args:
        input_results (List[Union[str, Dict[str, Any]]]):
            A list of file paths (str) or result dictionaries containing FID data.

        save_path (str):
            Directory where the generated PDF plots will be saved.

        figsize (tuple, optional):
            Figure size as (width, height). Defaults to (14, 8).

        style (str, optional):
            Seaborn style for the plot appearance. Defaults to 'whitegrid'.

        xtick_rotation (bool, optional):
            Whether to rotate x-axis labels by 45 degrees for better readability. Defaults to True.
    """
    # Load results from file paths or dictionaries
    results = _load_results(input_results)

    if not results:
        return

    # Extract FID data from results
    fid_data = _extract_fid_data(results)

    if not fid_data:
        return

    # Filter only IGW models
    igw_fid_data = {}
    for model_name, data in fid_data.items():
        # Find the corresponding result to get model type
        model_result = None
        for result in results:
            if result.get('modelname') == model_name:
                model_result = result
                break

        if model_result and _get_model_type(model_result) == 'IGW':
            igw_fid_data[model_name] = data

    if not igw_fid_data:
        print("Warning: No IGW models found for FID plotting.")
        return

    # Prepare model names and data for plotting
    model_names = list(igw_fid_data.keys())

    if not model_names:
        return

    # Create a new plot with specified style and size
    fig, ax = _create_stylish_plot(figsize, style)

    # Define bar positions and width for grouped bars
    x_pos = np.arange(len(model_names))
    bar_width = 0.35

    # Get consistent colors for each model
    all_model_names = list(fid_data.keys())  # Use all models for consistent coloring
    model_colors = _get_consistent_colors(all_model_names)

    # Prepare data for stego and clean FID bars
    stego_fids = []
    clean_fids = []
    has_clean_data = False

    for model_name in model_names:
        stego_fids.append(igw_fid_data[model_name]['stego_fid'])
        clean_fid = igw_fid_data[model_name]['clean_fid']
        if clean_fid is not None:
            clean_fids.append(clean_fid)
            has_clean_data = True
        else:
            clean_fids.append(0)  # Placeholder for missing clean data

    # Convert to NumPy arrays for easier manipulation
    stego_fids = np.array(stego_fids)
    clean_fids = np.array(clean_fids)

    # Plot stego FID bars with consistent colors
    bars1 = ax.bar(
        x_pos,
        stego_fids,
        bar_width,
        label='Stego FID',
        color=[model_colors[model_name] for model_name in model_names],
        alpha=0.8,
        edgecolor='white',
        linewidth=0.5
    )

    # Plot clean FID bars if available
    if has_clean_data:
        # Mask zero values to avoid plotting empty bars
        masked_clean_fids = np.ma.masked_where(clean_fids == 0, clean_fids)
        bars2 = ax.bar(
            x_pos + bar_width,
            masked_clean_fids,
            bar_width,
            label='Clean FID',
            color=[model_colors[model_name] for model_name in model_names],
            alpha=0.8,
            edgecolor='white',
            linewidth=0.5,
            hatch='///'  # Hatch pattern to distinguish clean FID
        )

    # Determine text positioning threshold based on max FID value
    all_fids = list(stego_fids) + [f for f in clean_fids if f > 0]
    max_fid = max(all_fids) if all_fids else 1.0
    threshold = max_fid / 2

    # Add value labels and dataset names on bars
    for i, (bar, fid_val) in enumerate(zip(bars1, stego_fids)):
        # Add FID value above the bar
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max_fid * 0.01,
            f'{fid_val:.1f}',
            ha='center',
            va='bottom',
            fontsize=8,
            fontweight='bold'
        )

        # Add dataset name inside or above the bar (rotated vertically)
        if show_dataset_name:
            dataset_name = igw_fid_data[model_names[i]]['datasetname']
            if len(dataset_name) > 20:
                dataset_name = dataset_name[:17] + "..."

            bar_height = bar.get_height()
            if bar_height < threshold:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar_height + max_fid * 0.05,
                    dataset_name,
                    ha='center',
                    va='bottom',
                    fontsize=7,
                    color='black',
                    rotation=90
                )
            else:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar_height / 2,
                    dataset_name,
                    ha='center',
                    va='center',
                    fontsize=7,
                    color='black',
                    rotation=90
                )

    # Add value labels and dataset names for clean FID bars
    if has_clean_data:
        for i, (fid_val, stego_bar) in enumerate(zip(clean_fids, bars1)):
            if fid_val > 0:
                clean_bar_x = stego_bar.get_x() + bar_width
                clean_bar_height = fid_val

                # Add FID value above the clean bar
                ax.text(
                    clean_bar_x + bar_width / 2,
                    clean_bar_height + max_fid * 0.01,
                    f'{fid_val:.1f}',
                    ha='center',
                    va='bottom',
                    fontsize=8,
                    fontweight='bold'
                )
                if show_dataset_name:
                    # Add dataset name inside or above the clean bar
                    dataset_name = igw_fid_data[model_names[i]]['datasetname']
                    if len(dataset_name) > 20:
                        dataset_name = dataset_name[:17] + "..."

                    if clean_bar_height < threshold:
                        ax.text(
                            clean_bar_x + bar_width / 2,
                            clean_bar_height + max_fid * 0.05,
                            dataset_name,
                            ha='center',
                            va='bottom',
                            fontsize=7,
                            color='black',
                            rotation=90
                        )
                    else:
                        ax.text(
                            clean_bar_x + bar_width / 2,
                            clean_bar_height / 2,
                            dataset_name,
                            ha='center',
                            va='center',
                            fontsize=7,
                            color='black',
                            rotation=90
                        )

    # Label the y-axis and set x-axis ticks
    ax.set_ylabel('FID Score', fontsize=12, fontweight='bold')
    ax.set_xticks(x_pos + bar_width / 2)
    if xtick_rotation:
        ax.set_xticklabels(model_names, rotation=45, ha='right', fontsize=10)
    else:
        ax.set_xticklabels(model_names, ha='center', fontsize=10)

    # --- Final Styling ---
    ax.grid(True, alpha=0.7, linestyle='-', linewidth=0.8, color='#cccccc')

    ax.set_facecolor('#f0f8ff')

    for spine in ax.spines.values():
        spine.set_edgecolor('none')
        spine.set_linewidth(0)

    # Add legend for clarity
    ax.legend(loc='best', frameon=True, fancybox=True, shadow=True)

    # Save the plot as a PDF
    filename = "IGW_FID_metrics.pdf"  # Changed filename to indicate IGW only
    _save_figure(fig, save_path, filename)


def plot_visual_quality(
        input_results: List[Union[str, Dict[str, Any]]],
        save_path: str,
        figsize: tuple = (6, 2),
        style: str = 'whitegrid',
        xtick_rotation: bool = True,
        show_dataset_name: bool = True,
) -> None:
    """
    Plot all visual quality metrics.

    This function orchestrates the generation of two types of plots:
    1. Violin plots for multi-value metrics (PSNR, SSIM, LPIPS)
    2. Grouped bar chart for FID metrics

    Args:
        input_results (List[Union[str, Dict[str, Any]]]):
            A list of file paths (str) or result dictionaries containing visual quality data.

        save_path (str):
            Directory where the generated PDF plots will be saved.

        figsize (tuple, optional):
            Figure size as (width, height). Defaults to (12, 8).

        style (str, optional):
            Seaborn style for the plot appearance. Defaults to 'whitegrid'.

        xtick_rotation (bool, optional):
            Whether to rotate x-axis labels by 45 degrees for better readability. Defaults to True.
    """
    # Ensure the save directory exists
    os.makedirs(save_path, exist_ok=True)

    # Plot multi-value metrics (violin plots)
    plot_multi_value_metrics(input_results, save_path, figsize, style, xtick_rotation)

    # Plot FID metrics (grouped bar chart)
    plot_fid_metrics(input_results, save_path, figsize, style, xtick_rotation, show_dataset_name)


def plot_model_robustness_under_single_attack(
        input_results: List[Union[str, Dict[str, Any]]],
        save_path: str,
        figsize: tuple = (5, 4),
        style: str = 'darkgrid',
        shadow: bool = False,
        rotation_45: bool = True,
        columnspacing: float = 4.
) -> None:
    """
    Plot robustness comparison for watermark models.

    This function creates two types of plots:
    1. For each noise type with multiple factors: line plots comparing models
       - PGW models use solid lines, IGW models use dashed lines
       - One PDF per noise type and metric
    2. For noise types with single factor: bar charts comparing models
       - One PDF per noise type and metric

    Args:
        input_results (List[Union[str, Dict[str, Any]]]):
            A list of file paths (str) or result dictionaries containing robustness data.

        save_path (str):
            Directory where the generated PDF plots will be saved.

        figsize (tuple, optional):
            Figure size as (width, height) tuple. Defaults to (8, 6).

        style (str, optional):
            Seaborn style ('whitegrid', 'darkgrid', 'white', 'dark', 'ticks'). Defaults to 'darkgrid'.

        shadow (bool, optional):
            Whether to add variance shadow to lines. Defaults to False.

        rotation_45 (bool, optional):
            Whether to rotate x-axis labels 45 degrees for bar charts. Defaults to True.

        need_legend (bool, optional):
            Whether to include legend in individual plots. Defaults to False.

        columnspacing (tuple, optional):
            Figure size for legend PDF as width. Defaults to 2..

        y_lim (tuple, optional):
            Y-axis limits for accuracy metrics. Defaults to (45, 105).
    """
    # Load results
    os.makedirs(save_path, exist_ok=True)
    results = _load_results(input_results)
    if not results:
        return

    # Get all metrics from results
    metrics = set()
    for result in results:
        if 'testrobustnessmetrics' in result:
            metrics.update(result['testrobustnessmetrics'])

    model_names = [result.get('modelname', f'Model_{i}') for i, result in enumerate(results)]

    # Collect all legend information for separate legend plot
    legend_info = []

    # Process each metric
    for metric in metrics:
        # Extract robustness data for this metric
        robustness_data = _extract_robustness_data(results, metric)

        # Plot 1 & 2: Per noise type plots
        for noise_type, noise_data in robustness_data.items():
            # Count valid factors for this noise type
            valid_factor_count = _count_valid_factors(noise_data, model_names)
            if valid_factor_count > 1:
                # Multi-factor: line plot
                legend_items = _plot_multi_factor_robustness(
                    noise_data, noise_type, metric, model_names,
                    save_path, figsize, style, shadow, False
                )
                if legend_items:
                    legend_info.extend(legend_items)
            elif valid_factor_count == 1:
                # Single-factor: bar chart
                legend_items = _plot_single_factor_robustness(
                    noise_data, noise_type, metric, model_names,
                    save_path, figsize, style, rotation_45
                )
                if legend_items:
                    legend_info.extend(legend_items)

    # Create separate legend plot if legend_info is not empty
    if legend_info:
        _create_separate_legend(legend_info, save_path, columnspacing)


def _plot_multi_factor_robustness(
        data: Dict[str, Any],
        noise_type: str,
        metric: str,
        model_names: List[str],
        save_path: str,
        figsize: Tuple[int, int] = (10, 6),
        style: str = 'whitegrid',
        shadow: bool = False,
        need_legend: bool = False
) -> List[Dict[str, Any]]:
    """
    Plot robustness comparison for multi-factor noise types.

    This function creates line plots for multi-factor noise types, comparing models.
    It sorts factors numerically, plots lines with markers, and optionally adds variance shadows.
    Shadows are skipped for 'No Attacking' and scaled for visibility.

    Args:
        data (Dict[str, Any]):
            Noise type data containing factors and their values.

        noise_type (str):
            Name of the noise type being plotted.

        metric (str):
            Robustness metric name (e.g., 'BER', 'EA').

        model_names (List[str]):
            List of model names to include in the plot.

        save_path (str):
            Directory to save the plot.

        figsize (Tuple[int, int], optional):
            Figure size. Defaults to (10, 6).

        style (str, optional):
            Seaborn style. Defaults to 'whitegrid'.

        shadow (bool, optional):
            Whether to add variance shadow to lines. Defaults to False.

        need_legend (bool, optional):
            Whether to include legend in the plot. Defaults to False.

        y_lim (tuple, optional):
            Y-axis limits for accuracy metrics. Defaults to (45, 105).

    Returns:
        List[Dict[str, Any]]: Legend information for separate legend plot
    """
    # Count valid factors first
    valid_factor_count = _count_valid_factors(data, model_names)
    if valid_factor_count <= 1:
        return []  # Skip if not multi-factor - THIS IS THE KEY FIX

    # Filter factors that have data for at least one model
    valid_factors = []
    factor_labels = []
    for factor_str in data['factors'].keys():
        has_data = any(model_name in data['factors'][factor_str] for model_name in model_names)
        if has_data:
            valid_factors.append(factor_str)
            factor_labels.append(str(factor_str))

    if len(valid_factors) <= 1:
        return []  # Skip if not multi-factor - DOUBLE CHECK

    # Convert factors to numeric values for sorting
    factor_values = []
    for f in valid_factors:
        if f is None or f == 'None':
            factor_values.append(0.0)
        else:
            try:
                factor_values.append(float(f))
            except (ValueError, TypeError):
                factor_values.append(0.0)

    # Sort factors by their numeric values
    sorted_indices = np.argsort(factor_values)
    sorted_factors = [valid_factors[i] for i in sorted_indices]
    sorted_factor_labels = [factor_labels[i] for i in sorted_indices]

    # Create plot
    fig, ax = _create_stylish_plot(figsize, style)

    # Get color palette
    colors = sns.color_palette("husl", len(model_names))

    # Marker styles for different models
    markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h', 'H', '+', 'x', 'X', '8', 'P']

    # Plot each model
    has_data_to_plot = False
    legend_info = []
    plotted_models = []

    for i, model_name in enumerate(model_names):
        model_values = []
        model_std_values = []
        has_model_data = False
        for factor in sorted_factors:
            if model_name in data['factors'][factor]:
                model_values.append(data['factors'][factor][model_name]['value'])
                model_std_values.append(data['factors'][factor][model_name]['std'])
                has_model_data = True
            else:
                model_values.append(np.nan)
                model_std_values.append(np.nan)

        if has_model_data:
            has_data_to_plot = True
            plotted_models.append(model_name)
            # Determine line style based on model type
            model_type = data['factors'][sorted_factors[0]][model_name]['model_type']
            line_style = '-' if model_type == 'PGW' else '--' if model_type == 'IGW' else '-'  # PGW=solid, IGW=dashed

            # Get marker for this model
            marker = markers[i % len(markers)]

            # Plot line
            x_vals = range(len(sorted_factors))
            line = ax.plot(x_vals,
                           model_values,
                           linestyle=line_style,
                           marker=marker,
                           markersize=6,
                           linewidth=2,
                           color=colors[i],
                           label=model_name,
                           alpha=0.8)

            # Store legend information
            legend_info.append({
                'label': model_name,
                'color': colors[i],
                'linestyle': line_style,
                'marker': marker
            })

            # Add variance shadow if requested and we have variance data
            if shadow and any(std > 0 for std in model_std_values):
                ax.fill_between(x_vals,
                                np.array(model_values) - np.array(model_std_values) * 2,
                                np.array(model_values) + np.array(model_std_values) * 2,
                                color=colors[i],
                                alpha=0.3)

    if not has_data_to_plot:
        plt.close(fig)
        return []

    # Customize plot
    ax.set_xlabel(data.get('factorsymbol', 'Factor'), fontsize=14)
    ax.set_ylabel(metric, fontsize=14)
    ax.set_title(f'{noise_type}', fontsize=14)

    # # Set y-axis limits for accuracy metrics
    # if _is_accuracy_metric(metric):
    #     ax.set_ylim(y_lim)

    # Set x-axis ticks and labels (horizontal to save space)
    ax.set_xticks(range(len(sorted_factors)))
    ax.set_xticklabels(sorted_factor_labels, rotation=0, ha='center')
    ax.grid(True, alpha=0.7, linestyle='-', linewidth=0.8, color='#cccccc')

    if need_legend:
        # Add legend
        ax.legend(loc='best', frameon=True, fancybox=True, shadow=True)

    # Save plot
    filename = f"{noise_type}_{metric.replace('%', 'P')}_robustness.pdf"
    _save_figure(fig, save_path, filename)

    return legend_info


def _plot_single_factor_robustness(
        data: Dict[str, Any],
        noise_type: str,
        metric: str,
        model_names: List[str],
        save_path: str,
        figsize: Tuple[int, int] = (10, 6),
        style: str = 'whitegrid',
        rotation_45: bool = True
) -> List[Dict[str, Any]]:
    """
    Plot robustness comparison for single-factor noise types using bar chart.

    This function creates bar charts for single-factor noise types, comparing models.
    It adds value labels on bars for clarity.

    Args:
        data (Dict[str, Any]):
            Noise type data containing factors and their values.

        noise_type (str):
            Name of the noise type being plotted.

        metric (str):
            Robustness metric name (e.g., 'BER', 'EA').

        model_names (List[str]):
            List of model names to include in the plot.

        save_path (str):
            Directory to save the plot.

        figsize (Tuple[int, int], optional):
            Figure size. Defaults to (10, 6).

        style (str, optional):
            Seaborn style. Defaults to 'whitegrid'.

        rotation_45 (bool, optional):
            Whether to rotate x-axis labels 45 degrees. Defaults to True.

        y_lim (tuple, optional):
            Y-axis limits for accuracy metrics. Defaults to (45, 105).

    Returns:
        List[Dict[str, Any]]: Legend information for separate legend plot
    """
    # Count valid factors first
    valid_factor_count = _count_valid_factors(data, model_names)
    if valid_factor_count != 1:
        return []  # Skip if not single-factor

    # Filter factors that have data for at least one model
    valid_factors = []
    for factor_str in data['factors'].keys():
        has_data = any(model_name in data['factors'][factor_str] for model_name in model_names)
        if has_data:
            valid_factors.append(factor_str)

    if len(valid_factors) != 1:
        return []  # Skip if not single-factor

    factor = valid_factors[0]
    factor_data = data['factors'][factor]

    # Extract values for each model that has data
    model_names_with_data = []
    model_values = []
    for model_name in model_names:
        if model_name in factor_data:
            model_names_with_data.append(model_name)
            model_values.append(factor_data[model_name]['value'])

    if not model_names_with_data:
        return []

    # Create plot
    fig, ax = _create_stylish_plot(figsize, style)

    # Create bar chart
    x_pos = np.arange(len(model_names_with_data))
    colors = sns.color_palette("husl", len(model_names_with_data))
    bars = ax.bar(x_pos, model_values, color=colors, alpha=0.8, edgecolor='white', linewidth=0.5)

    # Store legend information
    legend_info = []
    for i, model_name in enumerate(model_names_with_data):
        legend_info.append({
            'label': model_name,
            'color': colors[i],
            'type': 'bar'
        })

    # Customize plot
    ax.set_ylabel(metric, fontsize=12)
    ax.set_title(f'{data.get("noisename", noise_type)} - {metric} Robustness', fontsize=14)

    # Remove xlabel for bar charts
    # Set x-axis ticks and labels (horizontal to save space)
    ax.set_xticks(x_pos)
    if rotation_45:
        ax.set_xticklabels(model_names_with_data, rotation=45, ha='right')
    else:
        ax.set_xticklabels(model_names_with_data, rotation=0, ha='center')

    # Add value labels on bars
    for i, (bar, value) in enumerate(zip(bars, model_values)):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(model_values) * 0.01,
                f'{value:.2f}', ha='center', va='bottom', fontsize=9)

    ax.grid(True, alpha=0.7, linestyle='-', linewidth=0.8, color='#cccccc')

    # Save plot
    filename = f"{noise_type}_{metric.replace('%', 'P')}_robustness.pdf"
    _save_figure(fig, save_path, filename)

    return legend_info


def _create_separate_legend(legend_info: List[Dict[str, Any]], save_path: str, columnspacing: float = 3.0) -> None:
    """
    Create a separate legend PDF with all legend items distributed evenly.

    Args:
        legend_info (List[Dict[str, Any]]): List of legend information
        save_path (str): Directory to save the legend
        figsize (tuple): Figure size for legend PDF
    """
    # Remove duplicates while preserving order
    unique_legend_info = []
    seen_labels = set()
    for item in legend_info:
        if item['label'] not in seen_labels:
            unique_legend_info.append(item)
            seen_labels.add(item['label'])

    if not unique_legend_info:
        return

    # Create figure for legend
    fig, ax = plt.subplots(figsize=(12, 2))
    ax.axis('off')  # Hide axes

    # Set white background
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    # Create legend handles
    handles = []
    labels = []

    for item in unique_legend_info:
        if 'type' in item and item['type'] == 'bar':
            # Bar chart legend item
            handle = plt.Rectangle((0, 0), 1, 1, facecolor=item['color'], edgecolor='white', linewidth=0.5)
        else:
            # Line plot legend item
            handle = plt.Line2D([0], [0],
                                color=item['color'],
                                linestyle=item.get('linestyle', '-'),
                                marker=item.get('marker', 'o'),
                                markersize=6,
                                linewidth=2)

        handles.append(handle)
        labels.append(item['label'])

    # Create legend with even distribution
    ncol = len(labels) if len(labels) > 0 else 1
    legend = ax.legend(handles, labels,
                       loc='center',
                       ncol=ncol,
                       frameon=False,  # Remove frame/box around legend
                       fancybox=True,
                       shadow=True,
                       bbox_to_anchor=(0.5, 0.5),
                       columnspacing=columnspacing,
                       handletextpad=0.5)

    # Adjust legend properties for better appearance
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_alpha(0.9)
    legend.get_frame().set_edgecolor('gray')

    # Save legend with tight cropping - this is the key fix
    filename = "legend.pdf"
    full_path = os.path.join(save_path, filename)
    os.makedirs(save_path, exist_ok=True)

    # Alternative approach: manually calculate bounding box
    fig.canvas.draw()
    bbox = legend.get_window_extent()
    bbox = bbox.transformed(fig.dpi_scale_trans.inverted())

    fig.savefig(full_path,
                format='pdf',
                bbox_inches=bbox,
                dpi=300,
                facecolor='white',
                edgecolor='none')

    plt.close(fig)


def plot_model_robustness_under_all_attack(
        input_results: List[Union[str, Dict[str, Any]]],
        save_path: str,
        figsize: tuple = (5, 4),
        style: str = 'whitegrid',
        max_legend_per_row: int = 8,
) -> None:
    """
    Plot attacker performance visualization for watermark models.

    This function creates line plots showing the trade-off between visual quality (PSNR)
    and robustness metrics (TPR@N%FPR, Extraction Accuracy) for different attack types.
    For each model and each combination of visual quality and robustness metrics, a separate PDF is generated.
    Each PDF contains multiple lines, one for each noise type.

    The plots help visualize the attacker performance curve - how much visual quality is sacrificed
    for a given level of robustness degradation across different attack types.

    Args:
        input_results (List[Union[str, Dict[str, Any]]]):
            A list of file paths (str) or result dictionaries containing robustness and visual quality data.

        save_path (str):
            Directory where the generated PDF plots will be saved.

        figsize (tuple, optional):
            Figure size as (width, height) tuple. Defaults to (12, 10).

        style (str, optional):
            Seaborn style ('whitegrid', 'darkgrid', 'white', 'dark', 'ticks'). Defaults to 'darkgrid'.
    """
    # Load results
    os.makedirs(save_path, exist_ok=True)
    results = _load_results(input_results)
    if not results:
        return

    def _get_custom_high_contrast_colors(n_colors):
        CUSTOM_HIGH_CONTRAST_COLORS = [
            '#e6194B', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
            '#911eb4', '#42d4f4', '#f032e6', '#bfef45', '#fabed4',
            '#469990', '#dcbeff', '#9A6324', '#800000', '#aaffc3',
            '#808000', '#ffd8b1', '#000075', '#a9a9a9', '#000000',
            '#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00',
            '#ffff33', '#a65628', '#f781bf', '#999999', '#66c2a5',
            '#8dd3c7', '#bebada', '#fb8072', '#80b1d3', '#fdb462',
            '#b3de69', '#fccde5', '#d9d9d9', '#bc80bd', '#ccebc5',
            '#6a3d69', '#ffff99', '#b15928', '#cab2d6', '#ffed6f',
            '#1f78b4', '#b2df8a', '#fb9a99', '#fdbf6f', '#a6cee3'
        ]

        if n_colors <= len(CUSTOM_HIGH_CONTRAST_COLORS):
            return CUSTOM_HIGH_CONTRAST_COLORS[:n_colors]

        result = []
        for i in range(n_colors):
            result.append(CUSTOM_HIGH_CONTRAST_COLORS[i % len(CUSTOM_HIGH_CONTRAST_COLORS)])
        return result

    # Get all metrics from results
    visual_quality_metrics = set()
    robustness_metrics = set()
    for result in results:
        if 'testvisualqualitymetrics' in result:
            visual_quality_metrics.update(result['testvisualqualitymetrics'])
        if 'testrobustnessmetrics' in result:
            robustness_metrics.update(result['testrobustnessmetrics'])

    # Remove SSIM from visual quality metrics
    if 'SSIM' in visual_quality_metrics:
        visual_quality_metrics.remove('SSIM')
    if 'ssim' in visual_quality_metrics:
        visual_quality_metrics.remove('ssim')

    if not visual_quality_metrics or not robustness_metrics:
        return

    # Collect all legend information across all models and metrics
    all_legend_info = []

    # Process each model
    for result in results:
        model_name = result.get('modelname', 'Unknown')

        # Extract robustness data
        if 'robustnessresult' not in result:
            continue
        robustness_data = result['robustnessresult']

        # Create plots for each combination of visual quality and robustness metrics
        for vq_metric in visual_quality_metrics:
            for robust_metric in robustness_metrics:
                # Create plot
                fig, ax = _create_stylish_plot(figsize, style)

                # Get color palette for different noise types with higher contrast
                # Filter out No Attacking and Combined noise types
                filtered_noise_types = [nt for nt in robustness_data.keys()
                                        if nt not in ['No Attacking']]

                # Use a highly distinct color palette for better differentiation
                num_noise_types = len(filtered_noise_types)
                colors = _get_custom_high_contrast_colors(num_noise_types)

                markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h', 'H', '+', 'x', 'X', '8', 'P']

                # Process each noise type (excluding No Attacking and Combined)
                has_data_to_plot = False
                noise_type_index = 0
                for i, (noise_type, noise_data) in enumerate(robustness_data.items()):
                    # Skip No Attacking and Combined noise types
                    if noise_type in ['No Attacking']:
                        continue
                    if 'factors' not in noise_data:
                        continue

                    # Collect data points for this noise type
                    x_values = []  # Visual quality values
                    y_values = []  # Robustness values
                    factor_labels = []

                    # Extract data for each factor
                    for factor_str, factor_data in noise_data['factors'].items():
                        # Skip 'visualquality' factor as it's not an attack factor
                        if factor_str == 'visualquality':
                            continue
                        # Extract robustness metric
                        if robust_metric not in factor_data:
                            continue
                        # Extract visual quality metric
                        if 'visualquality' not in factor_data or vq_metric not in factor_data['visualquality']:
                            continue

                        robust_data = factor_data[robust_metric]
                        vq_data = factor_data['visualquality'][vq_metric]

                        # Get mean values
                        if isinstance(robust_data, list):
                            robust_value = np.mean(robust_data)
                        else:
                            robust_value = float(robust_data)
                        if isinstance(vq_data, list):
                            vq_value = np.mean(vq_data)
                        else:
                            vq_value = float(vq_data)

                        x_values.append(vq_value)
                        y_values.append(robust_value)
                        factor_labels.append(factor_str)

                    if not x_values or not y_values:
                        continue

                    # Sort by x values (visual quality) for proper line plotting
                    sorted_indices = np.argsort(x_values)
                    x_sorted = [x_values[j] for j in sorted_indices]
                    y_sorted = [y_values[j] for j in sorted_indices]
                    labels_sorted = [factor_labels[j] for j in sorted_indices]

                    # Plot line for this noise type
                    ax.plot(x_sorted, y_sorted,
                            marker=markers[noise_type_index % len(markers)],
                            markersize=6,
                            linewidth=2,
                            color=colors[noise_type_index],
                            label=noise_data.get('noisename', noise_type),
                            alpha=0.8)

                    # Collect legend information
                    legend_info = {
                        'label': noise_data.get('noisename', noise_type),
                        'color': colors[noise_type_index],
                        'marker': markers[noise_type_index % len(markers)]
                    }
                    if legend_info not in all_legend_info:
                        all_legend_info.append(legend_info)

                    noise_type_index += 1
                    has_data_to_plot = True

                if not has_data_to_plot:
                    plt.close(fig)
                    continue

                # Customize plot with better styling
                ax.set_xlabel(vq_metric, fontsize=12)
                ax.set_ylabel(robust_metric, fontsize=12)
                ax.set_title(f'{model_name}', fontsize=14, pad=15, wrap=True)

                # Add major and minor ticks for both axes
                ax.minorticks_on()
                ax.tick_params(axis='both', which='major', labelsize=10, length=6, width=1.2, direction='out')
                ax.tick_params(axis='both', which='minor', labelsize=8, length=3, width=0.8, direction='out')

                # --- Final Styling ---
                ax.grid(True, alpha=0.7, linestyle='-', linewidth=0.8, color='#cccccc')
                ax.set_facecolor('#f0f8ff')

                for spine in ax.spines.values():
                    spine.set_edgecolor('none')
                    spine.set_linewidth(0)

                # Save plot without legend
                filename = f"{model_name}_{vq_metric}_{robust_metric.replace('%', 'P')}_attacker_performance.pdf"
                _save_figure(fig, save_path, filename)

    # Create separate legend if there's legend information
    if all_legend_info:
        _create_attacker_legend(all_legend_info, save_path, max_items_per_row=max_legend_per_row)


def _create_attacker_legend(legend_info: List[Dict[str, Any]], save_path: str, max_items_per_row: int = 8) -> None:
    """
    Create a separate legend PDF for attacker performance plots.

    Args:
        legend_info (List[Dict[str, Any]]): List of legend information
        save_path (str): Directory to save the legend
        max_items_per_row (int): Maximum number of items per row in legend
    """
    # Remove duplicates while preserving order
    unique_legend_info = []
    seen_labels = set()
    for item in legend_info:
        if item['label'] not in seen_labels:
            unique_legend_info.append(item)
            seen_labels.add(item['label'])

    if not unique_legend_info:
        return

    # Calculate figure size based on number of items
    num_items = len(unique_legend_info)
    ncol = min(num_items, max_items_per_row)
    nrow = (num_items + max_items_per_row - 1) // max_items_per_row

    # Set figure size based on number of rows and columns
    figsize = (ncol * 1.5, nrow * 0.8)

    # Create figure for legend with white background
    fig, ax = plt.subplots(figsize=figsize)
    ax.axis('off')  # Hide axes

    # Set white background
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    # Create legend handles
    handles = []
    labels = []

    for item in unique_legend_info:
        # Line plot legend item
        handle = plt.Line2D([0], [0],
                            color=item['color'],
                            marker=item.get('marker', 'o'),
                            markersize=6,
                            linewidth=2)

        handles.append(handle)
        labels.append(item['label'])

    # Create legend with multiple rows if needed
    legend = ax.legend(handles, labels,
                       loc='center',
                       ncol=ncol,
                       frameon=False,
                       fancybox=False,
                       shadow=False,
                       bbox_to_anchor=(0.5, 0.5),
                       columnspacing=1.0,
                       handletextpad=0.5,
                       fontsize=10)

    # Adjust legend properties for better appearance
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_alpha(1.0)
    legend.get_frame().set_edgecolor('none')
    legend.get_frame().set_linewidth(0)

    # Save legend
    filename = "attacker_legend.pdf"
    full_path = os.path.join(save_path, filename)
    os.makedirs(save_path, exist_ok=True)

    fig.canvas.draw()
    bbox = legend.get_window_extent()
    bbox = bbox.transformed(fig.dpi_scale_trans.inverted())

    fig.savefig(full_path,
                format='pdf',
                bbox_inches=bbox,
                dpi=300,
                facecolor='white',
                edgecolor='none')

    plt.close(fig)


def plot_model_robustness_ranking_by_attacker_group(
        input_results: List[Union[str, Dict[str, Any]]],
        save_path: str,
        attacker_groups: Dict[str, List[str]],
        model_names: List[str] = None,
        figsize: tuple = (10, 6),
        style: str = 'whitegrid',
        xtick_rotation: bool = True
) -> None:
    """
    Plot model robustness ranking for each attacker group based on AUC of TPR-PSNR curves.
    Generates two plots for each group: one using sum of AUC, one using ranking points.
    """
    os.makedirs(save_path, exist_ok=True)

    # --- 1. Load and Prepare Data ---
    results = _load_results(input_results)
    if not results:
        print("Warning: No results loaded.")
        return

    # Extract model names from results if not provided
    if model_names is None:
        model_names = [result.get('modelname', f'Unknown_Model_{i}') for i, result in enumerate(results)]

    # Filter results if specific model names are provided
    if model_names is not None:
        filtered_results = []
        model_name_to_result = {result.get('modelname', f'Unknown_Model_{i}'): result
                                for i, result in enumerate(results)}
        for model_name in model_names:
            if model_name in model_name_to_result:
                filtered_results.append(model_name_to_result[model_name])
        results = filtered_results
        if not results:
            print("Warning: No matching models found.")
            return

    # Update model_names based on filtered results
    model_names = [result.get('modelname', f'Unknown_Model_{i}') for i, result in enumerate(results)]

    # --- 2. Extract TPR-PSNR Curve Data ---
    try:
        curve_data = _extract_robustness_curve_data(results)
    except NameError:
        print("Error: '_extract_robustness_curve_data' function not found in utils.")
        return

    # --- 3. Compute AUC Scores ---
    try:
        auc_scores_dict = _compute_auc_scores(curve_data, results)
    except NameError as e:
        print(f"Error: '_compute_auc_scores' function not found in utils or failed. Details: {e}")
        return
    except Exception as e:
        print(f"Error during AUC computation: {e}")
        return

    # --- 4. Process Each Attacker Group ---
    for group_name, group_attackers in attacker_groups.items():
        print(f"Processing attacker group: {group_name}")

        # --- 4.1 Filter AUC scores for this group's attackers ---
        available_noise_types = set()
        for model_name in model_names:
            if model_name in auc_scores_dict:
                for noise_type in auc_scores_dict[model_name].keys():
                    if noise_type in group_attackers and noise_type != 'No Attacking':
                        available_noise_types.add(noise_type)

        valid_noise_types = list(available_noise_types)

        if not valid_noise_types:
            print(f"Warning: No valid noise types found for group '{group_name}'. Skipping plot.")
            continue

        print(f"  Valid noise types in group: {valid_noise_types}")

        # --- 4.2 Compute Both Scoring Methods for This Group ---
        model_participation = {model_name: 0 for model_name in model_names}

        # --- Method 1: Sum of AUC Scores ---
        model_total_auc = {model_name: 0.0 for model_name in model_names}
        for model_name in model_names:
            model_aucs = []
            for noise_type in valid_noise_types:
                if (model_name in auc_scores_dict and
                        noise_type in auc_scores_dict[model_name] and
                        np.isfinite(auc_scores_dict[model_name][noise_type])):
                    model_aucs.append(auc_scores_dict[model_name][noise_type])
                    model_participation[model_name] += 1

            model_total_auc[model_name] = np.sum(model_aucs) if model_aucs else 0.0

        # --- Method 2: Ranking Points (N - r + 1) ---
        model_total_points = {model_name: 0.0 for model_name in model_names}

        for noise_type in valid_noise_types:
            # Collect valid models and their AUC scores for this noise type
            auc_values = []
            valid_models = []
            for model_name in model_names:
                if (model_name in auc_scores_dict and
                        noise_type in auc_scores_dict[model_name] and
                        np.isfinite(auc_scores_dict[model_name][noise_type])):
                    auc_values.append(auc_scores_dict[model_name][noise_type])
                    valid_models.append(model_name)

            if len(valid_models) > 0:
                # Sort by AUC descending (highest AUC = best = rank 1)
                sorted_indices = np.argsort(auc_values)[::-1]
                sorted_models = [valid_models[i] for i in sorted_indices]

                # Assign points: N, N-1, N-2, ..., 1
                num_valid_models = len(sorted_models)
                for rank_idx, model in enumerate(sorted_models):
                    points = num_valid_models - rank_idx
                    model_total_points[model] += points

        # --- 4.3 Generate Plots for Both Methods ---
        for method_name, scores_dict, y_label, score_format_func in [
            ('sum', model_total_auc, 'cumulative RQ-AUC', lambda s: f'{s:.2f}'),
            ('point', model_total_points, 'Ranking Points', lambda s: f'{int(s)}')
        ]:
            # Filter models with data
            models_with_data = [model_name for model_name in model_names
                                if model_participation[model_name] > 0]

            if not models_with_data:
                print(
                    f"Warning: No models participated in any valid noise type for group '{group_name}' using {method_name} method.")
                continue

            # Get scores and participation count for models with data
            final_scores = [scores_dict[model_name] for model_name in models_with_data]
            participation = [model_participation[model_name] for model_name in models_with_data]

            # Sort by scores (descending for both methods)
            sorted_indices = np.argsort(final_scores)[::-1]
            sorted_models = [models_with_data[i] for i in sorted_indices]
            sorted_scores = [final_scores[i] for i in sorted_indices]
            sorted_participation = [participation[i] for i in sorted_indices]
            rankings = np.arange(1, len(sorted_models) + 1)

            # --- 4.4 Create and Customize Plot ---
            fig, ax = _create_stylish_plot(figsize, style)

            x_pos = np.arange(len(sorted_models))
            # Use consistent colors if possible
            try:
                model_colors = _get_consistent_colors(model_names)
                colors = [model_colors[model_name] for model_name in sorted_models]
            except (NameError, KeyError):
                # Fallback if consistent colors are not available
                palette_name = "viridis" if len(sorted_models) <= 10 else "husl"
                colors = sns.color_palette(palette_name, len(sorted_models))

            bars = ax.bar(x_pos, sorted_scores, color=colors, alpha=0.8,
                          edgecolor='white', linewidth=1.5)

            ax.set_ylabel(y_label, fontsize=14, fontweight='bold')
            ax.set_title(f'{group_name} - Model Robustness Ranking ({method_name.upper()})', fontsize=16,
                         fontweight='bold')

            ax.set_xticks(x_pos)
            # Include participation count in x-tick labels
            xtick_labels = [f'{model} ({part})' for model, part in zip(sorted_models, sorted_participation)]
            if xtick_rotation:
                ax.set_xticklabels(xtick_labels, fontsize=10, rotation=45, ha='right')
            else:
                ax.set_xticklabels(xtick_labels, fontsize=10, ha='center')

            # --- 4.5 Add Score Values and Rankings ---
            max_score = max(sorted_scores) if sorted_scores else 1.0

            # Add score values above bars
            for i, (bar, value) in enumerate(zip(bars, sorted_scores)):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max_score * 0.01,
                        score_format_func(value), ha='center', va='bottom', fontsize=9, fontweight='bold',
                        color='#2c3e50')

            # Add ranking numbers (#1, #2, ...) on/in bars
            for i, (bar, rank) in enumerate(zip(bars, rankings)):
                x_pos_text = bar.get_x() + bar.get_width() / 2
                bar_height = bar.get_height()
                if bar_height > max_score * 0.15:  # Place inside if bar is tall enough
                    y_pos_text = bar_height / 2
                    ax.text(x_pos_text, y_pos_text, f'#{rank}',
                            ha='center', va='center', fontsize=11, fontweight='bold',
                            color='white', bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.7))
                else:  # Place outside
                    y_pos_text = bar_height + max_score * 0.05
                    ax.text(x_pos_text, y_pos_text, f'#{rank}',
                            ha='center', va='bottom', fontsize=11, fontweight='bold',
                            color='#e74c3c')

            # --- 4.6 Final Styling ---
            ax.grid(True, alpha=0.7, linestyle='-', linewidth=0.8, color='#cccccc')
            ax.set_facecolor('#f0f8ff')

            for spine in ax.spines.values():
                spine.set_edgecolor('none')
                spine.set_linewidth(0)

            # Add info text
            info_text = f"Available noise types: {len(valid_noise_types)}, Method: {method_name}"
            ax.text(0.98, 0.98, info_text, transform=ax.transAxes, fontsize=9,
                    verticalalignment='top', horizontalalignment='right',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))

            # --- 4.7 Save Plot ---
            safe_group_name = group_name.replace('/', '_').replace('\\', '_').replace(':', '_').replace(' ', '_')
            filename = f"{safe_group_name}_model_robustness_ranking_{method_name}.pdf"
            _save_figure(fig, save_path, filename)

            print(f"  Saved {method_name} ranking plot for group '{group_name}' to {filename}")


def plot_model_robustness_scores_under_all_attacks(
        input_results: List[Union[str, Dict[str, Any]]],
        save_path: str,
        figsize: tuple = (12, 5),
        style: str = 'whitegrid',
        xtick_rotation: bool = True,
        max_items_per_row: int = 8
) -> None:
    """
    Plot single model robustness across all attack types based on RQ-AUC scores.
    For each model, creates a bar chart showing AUC scores for different noise types.
    Shows ranking numbers inside bars and scores above bars.

    Args:
        input_results (List[Union[str, Dict[str, Any]]]):
            A list of file paths (str) or result dictionaries containing robustness data.
        save_path (str):
            Directory where the generated PDF plots will be saved.
        figsize (tuple, optional):
            Figure size as (width, height) tuple. Defaults to (12, 6).
        style (str, optional):
            Seaborn style. Defaults to 'whitegrid'.
        xtick_rotation (bool, optional):
            Whether to rotate x-axis labels 45 degrees. Defaults to True.
        max_items_per_row (int, optional):
            Maximum number of items per row in legend. Defaults to 6.
    """
    os.makedirs(save_path, exist_ok=True)

    def _get_custom_color(n_colors):
        CUSTOM_HIGH_CONTRAST_COLORS = [
            '#e6194B', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
            '#911eb4', '#42d4f4', '#f032e6', '#bfef45', '#fabed4',
            '#469990', '#dcbeff', '#9A6324', '#800000', '#aaffc3',
            '#808000', '#ffd8b1', '#000075', '#a9a9a9', '#000000',
            '#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00',
            '#ffff33', '#a65628', '#f781bf', '#999999', '#66c2a5',
            '#8dd3c7', '#bebada', '#fb8072', '#80b1d3', '#fdb462',
            '#b3de69', '#fccde5', '#d9d9d9', '#bc80bd', '#ccebc5',
            '#6a3d69', '#ffff99', '#b15928', '#cab2d6', '#ffed6f',
            '#1f78b4', '#b2df8a', '#fb9a99', '#fdbf6f', '#a6cee3'
        ]

        if n_colors <= len(CUSTOM_HIGH_CONTRAST_COLORS):
            return CUSTOM_HIGH_CONTRAST_COLORS[:n_colors]
        else:
            # If more colors needed, extend with seaborn palette
            additional_colors = sns.color_palette("husl", n_colors - len(CUSTOM_HIGH_CONTRAST_COLORS))
            additional_colors_hex = [f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
                                     for r, g, b in additional_colors]
            return CUSTOM_HIGH_CONTRAST_COLORS + additional_colors_hex

    # --- 1. Load and Prepare Data ---
    results = _load_results(input_results)
    if not results:
        return

    # --- 2. Extract Global PSNR Range for Normalization ---
    all_psnr_values = _extract_all_psnr_values(results)
    if not all_psnr_values:
        print("Warning: No PSNR values found for normalization.")
        return
    global_min_psnr = np.min(all_psnr_values)
    global_max_psnr = np.max(all_psnr_values)
    psnr_range = global_max_psnr - global_min_psnr
    if psnr_range == 0:
        print("Warning: All PSNR values are the same. Cannot normalize.")
        return

    # --- 3. Extract TPR-PSNR Curve Data ---
    try:
        curve_data = _extract_robustness_curve_data(results)
    except NameError:
        print("Error: '_extract_robustness_curve_data' function not found in utils. Please implement it.")
        return

    # --- 4. Compute AUC Scores ---
    try:
        auc_scores = _compute_auc_scores(curve_data, results)
    except NameError:
        print("Error: '_compute_auc_scores' function not found in utils. Please implement it.")
        return

    # --- 5. Collect legend information ---
    all_noise_types = set()
    for model_data in auc_scores.values():
        all_noise_types.update(model_data.keys())
    all_noise_types = sorted([nt for nt in all_noise_types if nt != 'No Attacking'])

    # Generate consistent colors for noise types using custom high contrast colors
    noise_colors = _get_custom_color(len(all_noise_types))
    noise_color_map = dict(zip(all_noise_types, noise_colors))

    # Save legend as a separate figure
    legend_info = [{'label': noise_type, 'color': color} for noise_type, color in noise_color_map.items()]
    _create_attacker_legend(legend_info, save_path, max_items_per_row)

    # --- 6. Plot for Each Model ---
    for model_name, model_data in auc_scores.items():
        # --- 6.1 Collect AUC scores for this model across all noise types ---
        noise_types_with_data = []
        scores_for_model = []

        for noise_type in all_noise_types:
            # Check if noise_type exists for this model and has a valid AUC score
            if noise_type in model_data and np.isfinite(model_data[noise_type]):
                noise_types_with_data.append(noise_type)
                scores_for_model.append(model_data[noise_type])

        if not noise_types_with_data:
            print(f"Warning: No valid AUC data found for model '{model_name}'. Skipping plot.")
            continue

        # --- 6.2 Sort Noise Types by AUC Score (Higher is Better) ---
        sorted_indices = np.argsort(scores_for_model)[::-1]  # Descending order
        sorted_noise_types = [noise_types_with_data[i] for i in sorted_indices]
        sorted_scores = [scores_for_model[i] for i in sorted_indices]
        rankings = np.arange(1, len(sorted_noise_types) + 1)  # 1, 2, 3, ...

        # --- 6.3 Create and Customize Plot ---
        fig, ax = _create_stylish_plot(figsize, style)

        x_pos = np.arange(len(sorted_noise_types))

        # Use consistent colors for noise types
        colors = [noise_color_map[noise_type] for noise_type in sorted_noise_types]

        bars = ax.bar(x_pos, sorted_scores, color=colors, width=0.8, alpha=0.8, edgecolor='white', linewidth=0.5)

        ax.set_ylabel('RQ-AUC', fontsize=12, fontweight='bold')
        ax.set_title(f'Robustness of {model_name} Across Different Attacks', fontsize=14, pad=20)

        ax.set_xticks(x_pos)
        if xtick_rotation:
            ax.set_xticklabels(sorted_noise_types, fontsize=10, rotation=45, ha='right')
        else:
            ax.set_xticklabels(sorted_noise_types, fontsize=10, ha='center')

        # --- 6.4 Add Score Values and Rankings ---
        max_score = max(sorted_scores) if sorted_scores else 1.0

        # Add some padding at the top for score labels
        ax.set_ylim(top=max_score * 1.15)

        # Add score values above bars
        for i, (bar, value) in enumerate(zip(bars, sorted_scores)):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max_score * 0.02,
                    f'{value:.2f}', ha='center', va='bottom', fontsize=6, fontweight='normal')

        # Add ranking numbers inside or above bars
        for i, (bar, rank) in enumerate(zip(bars, rankings)):
            x_pos_text = bar.get_x() + bar.get_width() / 2
            bar_height = bar.get_height()
            text_height_est = 0.03 * max_score  # Estimate text height
            if text_height_est < bar_height * 0.6:  # Only put inside if bar is tall enough
                y_pos_text = bar_height / 2
                ax.text(x_pos_text, y_pos_text, f'#{rank}',
                        ha='center', va='center', fontsize=6, color='white',
                        bbox=dict(boxstyle="round,pad=0.2", facecolor='black', alpha=0.7))
            else:
                y_pos_text = bar_height + max_score * 0.05
                ax.text(x_pos_text, y_pos_text, f'#{rank}',
                        ha='center', va='bottom', fontsize=9, color='black')

        # --- 6.5 Final Styling ---
        ax.grid(True, alpha=0.7, linestyle='-', linewidth=0.8, color='#cccccc')
        ax.set_facecolor('#f0f8ff')

        for spine in ax.spines.values():
            spine.set_edgecolor('none')
            spine.set_linewidth(0)

        # Adjust layout to prevent label cutoff
        plt.tight_layout()

        # --- 6.6 Save Plot ---
        safe_model_name = model_name.replace('/', '_').replace('\\', '_').replace(':', '_').replace(' ', '_')
        filename = f"{safe_model_name}_robustness_across_attacks.pdf"
        _save_figure(fig, save_path, filename)


def test_compute_overall_robustness_scores(
        input_results: List[Union[str, Dict[str, Any]]]
) -> Dict[str, float]:
    """
    Test function to compute and print overall robustness scores (sum of RQ-AUCs)
    for each model across all valid noise types, mirroring the logic in
    plot_model_overall_robustness_ranking.

    This function loads results, computes AUCs, sums them per model, and prints
    the results in descending order of the total score.

    Args:
        input_results (List[Union[str, Dict[str, Any]]]):
            A list of file paths (str) or result dictionaries containing robustness data.

    Returns:
        Dict[str, float]: A dictionary of {model_name: total_auc_score}.
    """
    print("--- Starting Overall Robustness Score Calculation Test ---")

    # --- 1. Load and Prepare Data ---
    print("1. Loading results...")
    results = _load_results(input_results)
    if not results:
        print("Warning: No results loaded.")
        return {}

    # --- 2. Extract TPR-PSNR Curve Data ---
    print("2. Extracting TPR-PSNR curve data...")
    try:
        curve_data = _extract_robustness_curve_data(results)
    except NameError:
        print("Error: '_extract_robustness_curve_data' function not found in utils.")
        return {}

    # --- 3. Compute AUC Scores ---
    print("3. Computing AUC scores for each (model, noise_type) pair...")
    try:
        auc_scores_dict = _compute_auc_scores(curve_data, results)
    except NameError as e:
        print(f"Error: '_compute_auc_scores' function not found in utils or failed. Details: {e}")
        return {}
    except Exception as e:
        print(f"Error during AUC computation: {e}")
        return {}

    # --- 4. Determine Valid Noise Types and Models ---
    print("4. Determining valid noise types and models...")
    if not auc_scores_dict:
        print("Warning: No AUC scores computed.")
        return {}

    all_model_names = list(auc_scores_dict.keys())
    # Get noise types from the first model's data, assuming consistency
    first_model_data = next(iter(auc_scores_dict.values()), {})
    # Exclude 'No Attacking' from valid noise types
    valid_noise_types = [nt for nt in first_model_data.keys() if nt != 'No Attacking']

    if not valid_noise_types:
        print("Warning: No valid noise types found for overall ranking.")
        return {}

    print(f"   - Found {len(all_model_names)} models: {all_model_names}")
    print(f"   - Found {len(valid_noise_types)} valid noise types: {valid_noise_types}")

    # --- 5. Compute Overall Scores (Sum of AUCs) ---
    print("\n5. Calculating total AUC scores for each model...")
    model_total_auc = {model_name: 0.0 for model_name in all_model_names}
    model_noise_participation = {model_name: 0 for model_name in all_model_names}

    for model_name in all_model_names:
        model_aucs = []
        for noise_type in valid_noise_types:
            if (noise_type in auc_scores_dict.get(model_name, {}) and np.isfinite(
                    auc_scores_dict[model_name][noise_type])):
                model_aucs.append(auc_scores_dict[model_name][noise_type])
                model_noise_participation[model_name] += 1

        if model_aucs:
            model_total_auc[model_name] = np.sum(model_aucs)
        # If no valid AUCs, score remains 0.0

    # --- 6. Filter and Sort Models ---
    print("6. Filtering and sorting models based on total scores...")
    # Filter out models with zero participation (no valid AUC in any noise type)
    models_with_data = [model_name for model_name in all_model_names
                        if model_noise_participation[model_name] > 0]

    if not models_with_data:
        print("Warning: No models participated in any valid noise type for overall ranking.")
        return {}

    # Get scores and participation count for models with data
    final_scores = [model_total_auc[model_name] for model_name in models_with_data]
    participation = [model_noise_participation[model_name] for model_name in models_with_data]

    # Sort by overall scores (higher is better for sum method)
    sorted_indices = np.argsort(final_scores)[::-1]  # Descending order
    sorted_models = [models_with_data[i] for i in sorted_indices]
    sorted_scores = [final_scores[i] for i in sorted_indices]
    sorted_participation = [participation[i] for i in sorted_indices]
    rankings = np.arange(1, len(sorted_models) + 1)  # 1, 2, 3, ...

    # --- 7. Print Results ---
    print("\n--- Overall Model Robustness Scores (Sum of RQ-AUCs) ---")
    print(f"{'Rank':<6} {'Model Name':<30} {'Total RQ-AUC':<15} {'# Attacks':<10}")
    print("-" * 65)
    for rank, (model, score, num_attacks) in zip(rankings, zip(sorted_models, sorted_scores, sorted_participation)):
        print(f"{rank:<6} {model:<30} {score:<15.4f} {num_attacks:<10}")

    print("\n--- Calculation Summary ---")
    print(f"Total valid noise types considered: {len(valid_noise_types)}")
    print(f"Models included in ranking: {len(sorted_models)}")
    print(f"Scoring method: Sum of RQ-AUC across all valid noise types.")
    print(f"Models with no data for any valid noise type were excluded.")
    print("---------------------------\n")

    # Return the sorted results as a dictionary
    return {model: score for model, score in zip(sorted_models, sorted_scores)}


def plot_model_robustness_ranking_under_single_attack(
        input_results: List[Union[str, Dict[str, Any]]],
        save_path: str,
        figsize: tuple = (5, 4),
        style: str = 'whitegrid',
        xtick_rotation: bool = True
) -> None:
    """
    Plot model robustness ranking for each noise type based on AUC of TPR-PSNR curves.
    For each noise type (excluding 'No Attacking'), creates a bar chart showing AUC scores for different models.
    The AUC is calculated from the TPR-PSNR curve, including baseline points (0,0) and (1, TPR_NoAttack).
    Shows ranking numbers inside bars and scores above bars.
    Args:
        input_results (List[Union[str, Dict[str, Any]]]):
            A list of file paths (str) or result dictionaries containing robustness data.
        save_path (str):
            Directory where the generated PDF plots will be saved.
        figsize (tuple, optional):
            Figure size as (width, height) tuple. Defaults to (12, 8).
        style (str, optional):
            Seaborn style. Defaults to 'whitegrid'.
        xtick_rotation (bool, optional):
            Whether to rotate x-axis labels 45 degrees. Defaults to True.
    """
    os.makedirs(save_path, exist_ok=True)
    # --- 1. Load and Prepare Data ---
    results = _load_results(input_results)
    if not results:
        return

    # --- 2. Extract Global PSNR Range for Normalization ---
    # Ensure _extract_all_psnr_values includes PSNR from 'No Attacking' if needed
    all_psnr_values = _extract_all_psnr_values(results)
    if not all_psnr_values:
        print("Warning: No PSNR values found for normalization.")
        return
    global_min_psnr = np.min(all_psnr_values)
    global_max_psnr = np.max(all_psnr_values)
    psnr_range = global_max_psnr - global_min_psnr
    if psnr_range == 0:
        print("Warning: All PSNR values are the same. Cannot normalize.")
        return

    # --- 3. Extract TPR-PSNR Curve Data ---
    # This function needs to be implemented in draw/utils.py
    # It should return {model_name: {noise_type: [(psnr_norm, tpr), ...]}}
    try:
        curve_data = _extract_robustness_curve_data(results)
    except NameError:
        print("Error: '_extract_robustness_curve_data' function not found in utils. Please implement it.")
        return

    # --- 4. Compute AUC Scores ---
    # This function needs to be implemented in draw/utils.py
    # It should compute AUC for each model-noise pair using the curve data and global PSNR range
    try:
        auc_scores = _compute_auc_scores(curve_data, results)
    except NameError:
        print("Error: '_compute_auc_scores' function not found in utils. Please implement it.")
        return

    # --- 5. Collect legend information ---
    all_model_names = list(auc_scores.keys())
    legend_info = []

    # --- 6. Plot for Each Noise Type ---
    for noise_type, _ in next(iter(auc_scores.values())).items():  # Iterate through noise types from first model
        # --- 6.1 Skip 'No Attacking' ---
        if noise_type == 'No Attacking':
            continue

        # --- 6.2 Collect AUC scores for this noise type ---
        models_with_data = []
        scores_for_noise = []
        for model_name in all_model_names:
            # Check if noise_type exists for this model and has a valid AUC score
            if noise_type in auc_scores.get(model_name, {}) and np.isfinite(auc_scores[model_name][noise_type]):
                models_with_data.append(model_name)
                scores_for_noise.append(auc_scores[model_name][noise_type])

        if not models_with_data:
            print(f"Warning: No valid AUC data found for noise type '{noise_type}'. Skipping plot.")
            continue

        # --- 6.3 Sort Models by AUC Score (Higher is Better) ---
        sorted_indices = np.argsort(scores_for_noise)[::-1]  # Descending order
        sorted_models = [models_with_data[i] for i in sorted_indices]
        sorted_scores = [scores_for_noise[i] for i in sorted_indices]
        rankings = np.arange(1, len(sorted_models) + 1)  # 1, 2, 3, ...

        # --- 6.4 Create and Customize Plot ---
        fig, ax = _create_stylish_plot(figsize, style)

        x_pos = np.arange(len(sorted_models))
        # Use consistent colors if _get_consistent_colors is available and suitable
        try:
            model_colors = _get_consistent_colors(all_model_names)
            colors = [model_colors[model_name] for model_name in sorted_models]
        except (NameError, KeyError):
            # Fallback if consistent colors are not available
            colors = sns.color_palette("husl", len(sorted_models))

        # Collect legend information
        for model_name, color in zip(sorted_models, colors):
            legend_info.append({
                'label': model_name,
                'color': color
            })

        bars = ax.bar(x_pos, sorted_scores, color=colors, alpha=0.8, edgecolor='white', linewidth=0.5)

        ax.set_ylabel('RQ-AUC', fontsize=12, fontweight='bold')  # Changed to bold RQ-AUC
        ax.set_title(f'{noise_type}', fontsize=14)

        ax.set_xticks(x_pos)
        if xtick_rotation:
            ax.set_xticklabels(sorted_models, fontsize=12, rotation=45, ha='right')
        else:
            ax.set_xticklabels(sorted_models, fontsize=12, ha='center')

        # --- 6.5 Add Score Values and Rankings ---
        max_score = max(sorted_scores) if sorted_scores else 1.0
        # Add score values above bars
        for i, (bar, value) in enumerate(zip(bars, sorted_scores)):
            # Format AUC score to 3 decimal places
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max_score * 0.01,
                    f'{value:.2f}', ha='center', va='bottom', fontsize=10)

        # Add ranking numbers inside or above bars
        for i, (bar, rank) in enumerate(zip(bars, rankings)):
            x_pos_text = bar.get_x() + bar.get_width() / 2
            bar_height = bar.get_height()
            text_height_est = 0.05 * max_score  # Estimate text height
            if text_height_est < bar_height:
                y_pos_text = bar_height / 2
                ax.text(x_pos_text, y_pos_text, f'#{rank}',
                        ha='center', va='center', fontsize=10, color='white',
                        bbox=dict(boxstyle="round,pad=0.2", facecolor='black', alpha=0.7))
            else:
                y_pos_text = bar_height + max_score * 0.05
                ax.text(x_pos_text, y_pos_text, f'#{rank}',
                        ha='center', va='bottom', fontsize=10, color='black')

        # --- 6.6 Final Styling ---
        ax.grid(True, alpha=0.7, linestyle='-', linewidth=0.8, color='#cccccc')

        ax.set_facecolor('#f0f8ff')

        for spine in ax.spines.values():
            spine.set_edgecolor('none')
            spine.set_linewidth(0)

        # --- 6.7 Save Plot ---
        safe_noise_type_name = noise_type.replace('/', '_').replace('\\', '_').replace(':', '_')
        filename = f"{safe_noise_type_name}_model_robustness_ranking_auc.pdf"
        _save_figure(fig, save_path, filename)


def plot_model_overall_robustness_ranking(
        input_results: List[Union[str, Dict[str, Any]]],
        save_path: str,
        figsize: tuple = (9, 3),
        style: str = 'whitegrid',
        xtick_rotation: bool = True
) -> None:
    """
    Plot overall model robustness ranking using two methods:
    1. Sum of AUC across all noise types
    2. Ranking-based points (N - r + 1 for each noise type)
    """
    os.makedirs(save_path, exist_ok=True)

    # --- 1. Load and Prepare Data ---
    results = _load_results(input_results)
    if not results:
        print("Warning: No results loaded.")
        return

    # --- 2. Extract TPR-PSNR Curve Data ---
    try:
        curve_data = _extract_robustness_curve_data(results)
    except NameError:
        print("Error: '_extract_robustness_curve_data' function not found in utils.")
        return

    # --- 3. Compute AUC Scores ---
    try:
        auc_scores_dict = _compute_auc_scores(curve_data, results)
    except NameError as e:
        print(f"Error: '_compute_auc_scores' function not found in utils or failed. Details: {e}")
        return
    except Exception as e:
        print(f"Error during AUC computation: {e}")
        return

    # --- 4. Determine Valid Noise Types and Models ---
    if not auc_scores_dict:
        print("Warning: No AUC scores computed.")
        return

    all_model_names = list(auc_scores_dict.keys())
    first_model_data = next(iter(auc_scores_dict.values()), {})
    valid_noise_types = [nt for nt in first_model_data.keys() if nt != 'No Attacking']

    if not valid_noise_types:
        print("Warning: No valid noise types found for overall ranking.")
        return

    # --- 5. Compute Both Scoring Methods ---
    model_noise_participation = {model_name: 0 for model_name in all_model_names}

    # --- Method 1: Sum of AUC Scores ---
    model_total_auc = {model_name: 0.0 for model_name in all_model_names}
    for model_name in all_model_names:
        model_aucs = []
        for noise_type in valid_noise_types:
            if (noise_type in auc_scores_dict.get(model_name, {}) and np.isfinite(
                    auc_scores_dict[model_name][noise_type])):
                model_aucs.append(auc_scores_dict[model_name][noise_type])
                model_noise_participation[model_name] += 1

        if model_aucs:
            model_total_auc[model_name] = np.sum(model_aucs)

    # --- Method 2: Ranking Points (N - r + 1) ---
    model_total_points = {model_name: 0.0 for model_name in all_model_names}

    for noise_type in valid_noise_types:
        # Collect valid models and their AUC scores for this noise type
        auc_values = []
        valid_models = []
        for model_name in all_model_names:
            if noise_type in auc_scores_dict.get(model_name, {}) and np.isfinite(
                    auc_scores_dict[model_name][noise_type]):
                auc_values.append(auc_scores_dict[model_name][noise_type])
                valid_models.append(model_name)

        if len(valid_models) > 0:
            # Sort by AUC descending (highest AUC = best = rank 1)
            sorted_indices = np.argsort(auc_values)[::-1]  # Descending order
            sorted_models = [valid_models[i] for i in sorted_indices]

            # Assign points: N, N-1, N-2, ..., 1
            num_valid_models = len(sorted_models)
            for rank_idx, model in enumerate(sorted_models):
                # rank_idx is 0-based, so rank is rank_idx + 1
                # Points = N - rank + 1 = N - (rank_idx + 1) + 1 = N - rank_idx
                points = num_valid_models - rank_idx
                model_total_points[model] += points

    # --- 6. Create Plots for Both Methods ---
    for method_name, scores_dict, y_label, score_format_func in [
        ('sum', model_total_auc, 'cumulative RQ-AUC', lambda s: f'{s:.3f}'),
        ('point', model_total_points, 'Ranking Points', lambda s: f'{int(s)}')
    ]:
        # Filter models with data
        models_with_data = [model_name for model_name in all_model_names
                            if model_noise_participation[model_name] > 0]

        if not models_with_data:
            print(f"Warning: No models participated in any valid noise type for {method_name} method.")
            continue

        final_scores = [scores_dict[model_name] for model_name in models_with_data]
        participation = [model_noise_participation[model_name] for model_name in models_with_data]

        # Sort by scores (descending for both methods)
        sorted_indices = np.argsort(final_scores)[::-1]
        sorted_models = [models_with_data[i] for i in sorted_indices]
        sorted_scores = [final_scores[i] for i in sorted_indices]
        sorted_participation = [participation[i] for i in sorted_indices]
        rankings = np.arange(1, len(sorted_models) + 1)

        # --- 7. Create and Customize Plot ---
        fig, ax = _create_stylish_plot(figsize, style)

        x_pos = np.arange(len(sorted_models))
        try:
            model_colors = _get_consistent_colors(all_model_names)
            colors = [model_colors[model_name] for model_name in sorted_models]
        except (NameError, KeyError):
            palette_name = "viridis" if len(sorted_models) <= 10 else "husl"
            colors = sns.color_palette(palette_name, len(sorted_models))

        bars = ax.bar(x_pos, sorted_scores, color=colors, alpha=0.8,
                      edgecolor='white', linewidth=1.5)

        ax.set_ylabel(y_label, fontsize=14, fontweight='bold')

        ax.set_xticks(x_pos)
        xtick_labels = [f'{model} ({part})' for model, part in zip(sorted_models, sorted_participation)]
        if xtick_rotation:
            ax.set_xticklabels(xtick_labels, fontsize=10, rotation=45, ha='right')
        else:
            ax.set_xticklabels(xtick_labels, fontsize=10, ha='center')

        # Add score values and rankings
        max_score = max(sorted_scores) if sorted_scores else 1.0
        for i, (bar, value) in enumerate(zip(bars, sorted_scores)):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max_score * 0.01,
                    f"{score_format_func(value)}", ha='center', va='bottom', fontsize=8, fontweight='bold',
                    color='#2c3e50')

        for i, (bar, rank) in enumerate(zip(bars, rankings)):
            x_pos_text = bar.get_x() + bar.get_width() / 2
            bar_height = bar.get_height()
            if bar_height > max_score * 0.15:
                y_pos_text = bar_height / 2
                ax.text(x_pos_text, y_pos_text, f'#{rank}',
                        ha='center', va='center', fontsize=10, fontweight='bold',
                        color='white', bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.7))
            else:
                y_pos_text = bar_height + max_score * 0.05
                ax.text(x_pos_text, y_pos_text, f'#{rank}',
                        ha='center', va='bottom', fontsize=10, fontweight='bold',
                        color='#e74c3c')

        # Final styling
        ax.grid(True, alpha=0.7, linestyle='-', linewidth=0.8, color='#cccccc')
        ax.set_facecolor('#f0f8ff')

        for spine in ax.spines.values():
            spine.set_edgecolor('none')
            spine.set_linewidth(0)

        info_text = f"Total valid noise types: {len(valid_noise_types)}, Method: {method_name}"
        ax.text(0.98, 0.98, info_text, transform=ax.transAxes, fontsize=9,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))

        # Save with method name
        filename = f"Overall_model_robustness_ranking_{method_name}.pdf"
        _save_figure(fig, save_path, filename)

        print(f"Saved {method_name} ranking plot to {os.path.join(save_path, filename)}")


def plot_all_attack_ranking(
        input_results: List[Union[str, Dict[str, Any]]],
        save_path: str,
        figsize: tuple = (10, 3),  # Match figsize from plot_model_robustness_scores_under_all_attacks
        style: str = 'whitegrid',
) -> None:
    """
    Plot attack effectiveness ranking (vertical bar chart) based on ARQ-AUC metric.

    Effectiveness is measured by ARQ-AUC: for each noise type (attack), we sum its RQ-AUC
    values across all models. LOWER ARQ-AUC indicates a STRONGER attack (more effective
    at reducing watermark robustness across models).

    Args:
        input_results (List[Union[str, Dict[str, Any]]]):
            A list of file paths (str) or result dictionaries containing robustness data.
        save_path (str):
            Directory where the generated PDF plots will be saved.
        figsize (tuple, optional):
            Figure size as (width, height) tuple. Defaults to (12, 5).
        style (str, optional):
            Seaborn style. Defaults to 'whitegrid'.
    """
    os.makedirs(save_path, exist_ok=True)

    def _get_custom_color(n_colors):
        CUSTOM_HIGH_CONTRAST_COLORS = [
            '#e6194B', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
            '#911eb4', '#42d4f4', '#f032e6', '#bfef45', '#fabed4',
            '#469990', '#dcbeff', '#9A6324', '#800000', '#aaffc3',
            '#808000', '#ffd8b1', '#000075', '#a9a9a9', '#000000',
            '#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00',
            '#ffff33', '#a65628', '#f781bf', '#999999', '#66c2a5',
            '#8dd3c7', '#bebada', '#fb8072', '#80b1d3', '#fdb462',
            '#b3de69', '#fccde5', '#d9d9d9', '#bc80bd', '#ccebc5',
            '#6a3d69', '#ffff99', '#b15928', '#cab2d6', '#ffed6f',
            '#1f78b4', '#b2df8a', '#fb9a99', '#fdbf6f', '#a6cee3'
        ]

        if n_colors <= len(CUSTOM_HIGH_CONTRAST_COLORS):
            return CUSTOM_HIGH_CONTRAST_COLORS[:n_colors]
        else:
            # If more colors needed, extend with seaborn palette
            additional_colors = sns.color_palette("husl", n_colors - len(CUSTOM_HIGH_CONTRAST_COLORS))
            additional_colors_hex = [f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
                                     for r, g, b in additional_colors]
            return CUSTOM_HIGH_CONTRAST_COLORS + additional_colors_hex

    # --- 1. Load and Prepare Data ---
    results = _load_results(input_results)
    if not results:
        print("Warning: No results loaded. Skipping plot_all_attack_ranking.")
        return

    # --- 2. Extract Global PSNR Range for Normalization ---
    all_psnr_values = _extract_all_psnr_values(results)
    if not all_psnr_values:
        print("Warning: No PSNR values found for normalization.")
        return
    global_min_psnr = np.min(all_psnr_values)
    global_max_psnr = np.max(all_psnr_values)
    psnr_range = global_max_psnr - global_min_psnr
    if psnr_range == 0:
        print("Warning: All PSNR values are the same. Cannot normalize.")
        return

    # --- 3. Extract TPR-PSNR Curve Data ---
    try:
        curve_data = _extract_robustness_curve_data(results)
    except NameError:
        print("Error: '_extract_robustness_curve_data' function not found in utils. Please implement it.")
        return

    # --- 4. Compute RQ-AUC Scores ---
    try:
        auc_scores = _compute_auc_scores(curve_data, results)
    except NameError:
        print("Error: '_compute_auc_scores' function not found in utils. Please implement it.")
        return

    # --- 5. Compute ARQ-AUC (Attack-based RQ-AUC ranking) ---
    arq_auc_scores = {}
    model_count_per_noise = {}

    # Collect all noise types (excluding 'No Attacking')
    all_noise_types = set()
    for model_data in auc_scores.values():
        all_noise_types.update(model_data.keys())
    all_noise_types = sorted([nt for nt in all_noise_types if nt != 'No Attacking'])

    # Calculate ARQ-AUC for each noise type
    for noise_type in all_noise_types:
        total_auc = 0.0
        valid_model_count = 0

        for model_name, model_data in auc_scores.items():
            if noise_type in model_data and np.isfinite(model_data[noise_type]):
                total_auc += model_data[noise_type]
                valid_model_count += 1

        if valid_model_count > 0:
            arq_auc_scores[noise_type] = total_auc
            model_count_per_noise[noise_type] = valid_model_count

    if not arq_auc_scores:
        print("Warning: No valid ARQ-AUC scores computed.")
        return

    # --- 6. Sort Attacks by ARQ-AUC (Lower is Better) ---
    sorted_noise_types = sorted(arq_auc_scores.keys(), key=lambda x: arq_auc_scores[x])
    sorted_scores = [arq_auc_scores[nt] for nt in sorted_noise_types]
    rankings = np.arange(1, len(sorted_noise_types) + 1)  # 1, 2, 3, ...

    # --- 7. Create and Customize Plot ---
    fig, ax = _create_stylish_plot(figsize, style)

    x_pos = np.arange(len(sorted_noise_types))

    # Use custom high contrast colors
    noise_colors = _get_custom_color(len(sorted_noise_types))
    noise_color_map = dict(zip(sorted_noise_types, noise_colors))

    # Use consistent colors for noise types, matching plot_model_robustness_scores_under_all_attacks
    colors = [noise_color_map[noise_type] for noise_type in sorted_noise_types]

    # Create vertical bar chart with width parameter, matching plot_model_robustness_scores_under_all_attacks
    bars = ax.bar(x_pos, sorted_scores, color=colors, width=0.8, alpha=0.8, edgecolor='white', linewidth=0.5)

    ax.set_ylabel('cumulative RQ-AUC', fontsize=12, fontweight='bold')  # Simplified ylabel

    ax.set_xticks(x_pos)
    # Rotate x-axis labels for better readability, matching plot_model_robustness_scores_under_all_attacks default
    ax.set_xticklabels(sorted_noise_types, fontsize=8, rotation=45, ha='right')

    # --- 8. Add Score Values and Rankings ---
    max_score = max(sorted_scores) if sorted_scores else 1.0

    # Add some padding at the top for score labels, matching plot_model_robustness_scores_under_all_attacks
    ax.set_ylim(top=max_score * 1.15)

    # Add score values above bars, matching style from plot_model_robustness_scores_under_all_attacks
    for i, (bar, value) in enumerate(zip(bars, sorted_scores)):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max_score * 0.02,
                f'{value:.1f}', ha='center', va='bottom', fontsize=4)  # Slightly larger font than previous version

    # Add ranking numbers inside or above bars, matching style from plot_model_robustness_scores_under_all_attacks
    for i, (bar, rank) in enumerate(zip(bars, rankings)):
        x_pos_text = bar.get_x() + bar.get_width() / 2
        bar_height = bar.get_height()
        text_height_est = 0.03 * max_score  # Estimate text height
        if text_height_est < bar_height * 0.6:  # Only put inside if bar is tall enough
            y_pos_text = bar_height / 2
            ax.text(x_pos_text, y_pos_text, f'#{rank}',
                    ha='center', va='center', fontsize=6, color='white',  # Slightly larger font
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='black', alpha=0.7))
        else:
            y_pos_text = bar_height + max_score * 0.05
            ax.text(x_pos_text, y_pos_text, f'#{rank}',
                    ha='center', va='bottom', fontsize=6, color='black')  # Slightly larger font

    # --- 9. Final Styling ---
    # Match grid style from plot_model_robustness_scores_under_all_attacks
    ax.grid(True, alpha=0.7, linestyle='-', linewidth=0.8, color='#cccccc')
    ax.set_facecolor('#f0f8ff')

    for spine in ax.spines.values():
        spine.set_edgecolor('none')
        spine.set_linewidth(0)
        spine.set_visible(False)

    # Adjust layout to prevent label cutoff, matching plot_model_robustness_scores_under_all_attacks
    plt.tight_layout()

    # --- 10. Save Plot ---
    filename = "attack_ranking_ARQ_AUC.pdf"  # Simplified filename
    _save_figure(fig, save_path, filename)


def plot_attack_effectiveness_at_tpr_levels(
        input_results: List[Union[str, Dict[str, Any]]],
        save_path: str,
        figsize: tuple = (6, 5),
        style: str = 'whitegrid',
        tpr_levels: List[float] = None
) -> None:
    if tpr_levels is None:
        tpr_levels = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]

    # 1. Load and Prepare Data
    results = _load_results(input_results)
    if not results:
        print("Warning: No results loaded. Skipping plot_attack_performance_at_tpr_levels.")
        return

    # 2. Process each model separately
    for result in results:
        model_name = result.get('modelname', 'Unknown_Model')
        base_dir = os.path.join(save_path, model_name)
        os.makedirs(base_dir, exist_ok=True)
        tprxfpr = "TPR@$x\%$FPR"
        if 'robustnessresult' not in result:
            continue

        robustness_result = result['robustnessresult']

        # Collect legend information for this model
        model_legend_info = []

        # 3. Process each TPR level for this model
        for target_tpr in tpr_levels:
            assert 0.0 < target_tpr < 1.0, "The target TPR must be between 0.0 and 1.0."
            # Collect PSNR values for each noise type for this specific model and TPR level
            # Structure: {noise_type: psnr_value_or_zero}
            noise_psnr_at_tpr = {}

            for noise_type, noise_data in robustness_result.items():
                # Skip 'No Attacking'
                if noise_type == 'No Attacking':
                    continue

                if 'factors' not in noise_data:
                    continue

                psnr_values = []
                tpr_values = []

                # Collect data points for this noise type
                for factor_str, factor_data in noise_data['factors'].items():
                    # Extract TPR@N%FPR (take the first one found)
                    tpr_value = None
                    for key in factor_data.keys():
                        if key.startswith('TPR@') and key.endswith('%FPR'):
                            tprxfpr = key
                            tpr_data = factor_data[key]
                            if isinstance(tpr_data, list):
                                tpr_value = float(np.mean(tpr_data))
                            elif isinstance(tpr_data, (int, float)):
                                tpr_value = float(tpr_data)
                            break

                    # Extract PSNR from visualquality
                    psnr_value = None
                    if 'visualquality' in factor_data and 'PSNR' in factor_data['visualquality']:
                        psnr_data = factor_data['visualquality']['PSNR']
                        if isinstance(psnr_data, list):
                            psnr_value = float(np.mean(psnr_data))
                        elif isinstance(psnr_data, (int, float)):
                            psnr_value = float(psnr_data)

                    # Store valid data points
                    if (tpr_value is not None and psnr_value is not None and
                            np.isfinite(tpr_value) and np.isfinite(psnr_value)):
                        psnr_values.append(psnr_value)
                        tpr_values.append(tpr_value)

                # Process this noise type if we have data
                if psnr_values and tpr_values:
                    # Sort by PSNR for consistent interpolation (descending order - higher PSNR first)
                    sorted_indices = np.argsort(psnr_values)[::-1]  # Descending order
                    sorted_psnr = [psnr_values[i] for i in sorted_indices]
                    sorted_tpr = [tpr_values[i] for i in sorted_indices]

                    # Remove duplicates in PSNR
                    unique_psnr, unique_indices = np.unique(sorted_psnr, return_index=True)
                    unique_tpr = [sorted_tpr[i] for i in unique_indices]

                    # Find PSNR at target TPR
                    psnr_at_target = _find_psnr_at_tpr(unique_psnr, unique_tpr, target_tpr)

                    if psnr_at_target is not None and np.isfinite(psnr_at_target):
                        noise_psnr_at_tpr[noise_type] = psnr_at_target
                        # Collect legend information
                        if noise_type not in [item['label'] for item in model_legend_info]:
                            model_legend_info.append({
                                'label': noise_type,
                                'color': None  # Will be set later
                            })
                    # Skip if not achievable (don't add to noise_psnr_at_tpr)

            # Filter out noise types that cannot achieve the target TPR
            # Only keep noise types with PSNR > 0 (achievable)
            achievable_noise_psnr_at_tpr = {k: v for k, v in noise_psnr_at_tpr.items() if v > 0}

            if not achievable_noise_psnr_at_tpr:
                print(f"Warning: No achievable PSNR data for {model_name} at TPR level {target_tpr}. Skipping plot.")
                continue

            # 4. Sort noise types by PSNR (Descending - Higher PSNR is better)
            sorted_noise_types = sorted(achievable_noise_psnr_at_tpr.keys(),
                                        key=lambda x: achievable_noise_psnr_at_tpr[x], reverse=True)
            psnr_values = [achievable_noise_psnr_at_tpr[nt] for nt in sorted_noise_types]
            rankings = list(range(1, len(sorted_noise_types) + 1))

            # 5. Create and Customize Plot
            fig, ax = _create_stylish_plot(figsize, style)

            y_pos = np.arange(len(sorted_noise_types))

            # Use a more elegant color palette with better contrast
            if len(sorted_noise_types) <= 10:
                colors = sns.color_palette("tab10", len(sorted_noise_types))
            elif len(sorted_noise_types) <= 20:
                colors = sns.color_palette("tab20", len(sorted_noise_types))
            else:
                # For many categories, use a continuous palette
                colors = sns.color_palette("husl", len(sorted_noise_types))

            # Update legend information with colors
            for i, noise_type in enumerate(sorted_noise_types):
                for legend_item in model_legend_info:
                    if legend_item['label'] == noise_type:
                        legend_item['color'] = colors[i]
                        break

            # Create horizontal bar chart
            bars = ax.barh(y_pos, psnr_values, color=colors, alpha=0.85, edgecolor='white', linewidth=0.8)

            ax.set_xlabel('PSNR (dB)', fontsize=12, fontweight='bold')
            ax.set_ylabel('Ranking', fontsize=12, fontweight='bold')
            ax.set_title(f'{model_name} - {tprxfpr}={target_tpr}', fontsize=12, fontweight='bold')

            # Set y-axis ticks and labels
            ax.set_yticks(y_pos)
            ax.set_yticklabels([f'#{rank}' for rank in rankings], fontsize=9)

            # Add PSNR values and noise type names on bars
            max_psnr = max(psnr_values) if psnr_values else 1.0
            min_psnr = min(psnr_values) if psnr_values else 0.0
            psnr_range = max_psnr - min_psnr if max_psnr != min_psnr else 1.0

            for i, (bar, psnr_val, noise_type) in enumerate(zip(bars, psnr_values, sorted_noise_types)):
                bar_width = bar.get_width()
                bar_y_center = bar.get_y() + bar.get_height() / 2

                # Add PSNR value to the right of the bar
                ax.text(bar_width + psnr_range * 0.01, bar_y_center,
                        f'{psnr_val:.2f}', ha='left', va='center', fontsize=8, fontweight='bold')

                # Add noise type name on the bar (try inside first, truncate if too long)
                display_name = noise_type
                if len(display_name) > 25:
                    display_name = noise_type[:22] + "..."

                required_width = len(display_name) * 0.012 * psnr_range  # Estimate space needed
                if bar_width >= required_width:
                    ax.text(bar_width / 2, bar_y_center,
                            display_name, ha='center', va='center', fontsize=7, color='white', weight='bold')
                else:
                    # If bar is too narrow, put text to the left of the bar
                    ax.text(max(bar_width - psnr_range * 0.05, 0), bar_y_center,
                            display_name, ha='right', va='center', fontsize=7, color='black')

            # Invert y-axis so that rank 1 (highest PSNR) is at the top
            ax.invert_yaxis()
            # Match grid style from plot_model_robustness_scores_under_all_attacks
            ax.grid(True, alpha=0.7, linestyle='-', linewidth=0.8, color='#cccccc')
            ax.set_facecolor('#f0f8ff')

            # Adjust layout
            plt.tight_layout()

            # 6. Save Plot
            safe_model_name = model_name.replace('/', '_').replace('\\', '_').replace(':', '_')
            filename = f"{safe_model_name}_attack_performance_at_tpr_{target_tpr:.2f}.pdf"
            _save_figure(fig, base_dir, filename)

        # 7. Create separate legend for this model
        if model_legend_info:
            _create_attack_effectiveness_legend(model_legend_info, save_path)


def _create_attack_effectiveness_legend(legend_info: List[Dict[str, Any]], save_path: str) -> None:
    """
    Create a separate legend PDF for attack effectiveness plots.

    Args:
        legend_info (List[Dict[str, Any]]): List of legend information
        save_path (str): Directory to save the legend
    """
    # Remove duplicates while preserving order
    unique_legend_info = []
    seen_labels = set()
    for item in legend_info:
        if item['label'] not in seen_labels:
            unique_legend_info.append(item)
            seen_labels.add(item['label'])

    if not unique_legend_info:
        return

    # Calculate figure size based on number of items
    num_items = len(unique_legend_info)
    ncol = min(num_items, 8)  # Maximum 8 items per row
    nrow = (num_items + 7) // 8  # Calculate number of rows needed

    # Set figure size based on number of rows and columns
    figsize = (ncol * 1.8, nrow * 0.9)

    # Create figure for legend
    fig, ax = plt.subplots(figsize=figsize)
    ax.axis('off')  # Hide axes

    # Create legend handles
    handles = []
    labels = []

    for item in unique_legend_info:
        # Bar chart legend item
        handle = plt.Rectangle((0, 0), 1, 1, facecolor=item['color'], edgecolor='white', linewidth=1.0)
        handles.append(handle)
        labels.append(item['label'])

    # Create legend with multiple rows if needed
    legend = ax.legend(handles, labels,
                       loc='center',
                       ncol=ncol,
                       frameon=True,
                       fancybox=True,
                       shadow=True,
                       bbox_to_anchor=(0.5, 0.5),
                       columnspacing=1.2,
                       handletextpad=0.6,
                       fontsize=10)

    # Adjust legend properties for better appearance
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_alpha(0.95)
    legend.get_frame().set_edgecolor('gray')

    # Save legend with manual bounding box calculation
    filename = "attack_effectiveness_legend.pdf"
    full_path = os.path.join(save_path, filename)
    os.makedirs(save_path, exist_ok=True)

    # Alternative approach: manually calculate bounding box
    fig.canvas.draw()
    bbox = legend.get_window_extent()
    bbox = bbox.transformed(fig.dpi_scale_trans.inverted())

    fig.savefig(full_path,
                format='pdf',
                bbox_inches=bbox,
                dpi=300,
                facecolor='white',
                edgecolor='none')

    plt.close(fig)


def _find_psnr_at_tpr(psnr_vals: np.ndarray, tpr_vals: np.ndarray, target_tpr: float):
    """
    Find PSNR value at given TPR level using linear interpolation.
    This function finds ALL intersection points and returns the one with maximum PSNR.
    """
    # Ensure arrays are numpy arrays
    psnr_vals = np.array(psnr_vals)
    tpr_vals = np.array(tpr_vals)

    # Check if target_tpr is within achievable range
    min_tpr = np.min(tpr_vals)
    max_tpr = np.max(tpr_vals)

    if target_tpr < min_tpr or target_tpr > max_tpr:
        return None

    # Find ALL intersection points between consecutive points
    all_intersections = []

    for i in range(len(tpr_vals) - 1):
        t0, t1 = tpr_vals[i], tpr_vals[i + 1]
        p0, p1 = psnr_vals[i], psnr_vals[i + 1]

        # Check if target_tpr is between t0 and t1 (handles both increasing and decreasing segments)
        if (t0 <= target_tpr <= t1) or (t1 <= target_tpr <= t0):
            # Avoid division by zero
            if abs(t1 - t0) < 1e-10:
                # If t0 == t1, we have a horizontal segment
                # In this case, any PSNR between p0 and p1 is valid at target_tpr
                # We'll return the average or one of the values
                all_intersections.append((p0 + p1) / 2)
                continue

            # Linear interpolation
            alpha = (target_tpr - t0) / (t1 - t0)
            psnr_at_target = p0 + alpha * (p1 - p0)

            if np.isfinite(psnr_at_target):
                all_intersections.append(psnr_at_target)

    # Return the maximum PSNR among all intersections
    if all_intersections:
        return max(all_intersections)

    # Fallback to scipy interpolation if no intersections found
    try:
        from scipy import interpolate
        # Use monotonic interpolation if available for better results with non-monotonic data
        from scipy.interpolate import PchipInterpolator

        # Sort by TPR to ensure proper interpolation
        sorted_indices = np.argsort(tpr_vals)
        sorted_tpr = tpr_vals[sorted_indices]
        sorted_psnr = psnr_vals[sorted_indices]

        # Use monotonic interpolation to avoid overshoots
        f_interp = PchipInterpolator(sorted_tpr, sorted_psnr, extrapolate=True)
        psnr_at_target = float(f_interp(target_tpr))

        if np.isfinite(psnr_at_target):
            return psnr_at_target
    except Exception:
        pass

    return None
