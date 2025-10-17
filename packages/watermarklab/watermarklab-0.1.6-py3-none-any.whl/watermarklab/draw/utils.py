# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT
import os
import json
import base64
import numpy as np
from PIL import Image
import seaborn as sns
from io import BytesIO
from scipy import integrate
from matplotlib import pyplot as plt
from typing import List, Union, Dict, Any, Tuple


def _load_results(input_results: List[Union[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Load results from file paths or dictionary objects.

    This function processes a list of inputs, where each input can be either a file path (string)
    to a JSON file or a direct dictionary containing result data. It loads the JSON from files
    and appends all results into a single list of dictionaries.

    Args:
        input_results: List of file paths (str) or result dictionaries

    Returns:
        List of result dictionaries
    """
    results = []
    for item in input_results:
        if isinstance(item, str):
            with open(item, 'r') as f:
                results.append(json.load(f))
        else:
            results.append(item)
    return results


def _is_accuracy_metric(metric: str) -> bool:
    """
    Check if the metric is an accuracy-related metric that should have y-axis limits.

    Args:
        metric (str): Metric name

    Returns:
        bool: True if it's an accuracy metric
    """
    # Convert to uppercase for comparison
    metric_upper = metric.upper()

    # Check for TPR patterns (TPR@x%FPR where x can be any number)
    if 'TPR@' in metric_upper and '%FPR' in metric_upper:
        return False

    # Check for other accuracy metrics
    accuracy_keywords = ['EA', 'ACCURACY', 'ACC']
    return any(keyword in metric_upper for keyword in accuracy_keywords)


def _get_model_type(model_data: Dict[str, Any]) -> str:
    """
    Get model type (PGW or IGW) from model data.

    This function extracts the model type from the 'modeltype' key in the model data dictionary.
    It checks for keywords 'Post-Generation' for PGW and 'In-Generation' for IGW, returning 'Unknown' otherwise.

    Args:
        model_data: Model result dictionary

    Returns:
        'PGW' or 'IGW'
    """
    model_type = model_data.get('modeltype', '')
    if 'Post-Generation' in model_type:
        return 'PGW'
    elif 'In-Generation' in model_type:
        return 'IGW'
    else:
        return 'Unknown'


def _create_stylish_plot(figsize: Tuple[int, int] = (10, 6), style: str = 'whitegrid') -> Tuple[plt.Figure, plt.Axes]:
    """
    Create a stylish plot with plotly-like appearance.

    This function sets up a Seaborn style and creates a Matplotlib figure and axes with a light blue
    background for the axes and a subtle white grid.

    Args:
        figsize: Figure size (width, height)
        style: Seaborn style ('whitegrid', 'darkgrid', 'white', 'dark', 'ticks')

    Returns:
        Tuple of (figure, axes)
    """
    sns.set_style(style)
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_facecolor('#f0f8ff')  # Light blue background for axes only
    ax.grid(True, alpha=0.3, color='white')
    return fig, ax


def _save_figure(fig: plt.Figure, save_path: str, filename: str) -> None:
    """
    Save figure as PDF without white borders.

    This function saves the Matplotlib figure as a PDF with tight bounding box to minimize borders,
    ensuring high resolution (300 DPI) and white figure background.

    Args:
        fig: Matplotlib figure
        save_path: Directory to save the file
        filename: Name of the file
    """
    full_path = os.path.join(save_path, filename)
    os.makedirs(save_path, exist_ok=True)

    fig.savefig(full_path,
                format='pdf',
                bbox_inches='tight',
                pad_inches=0.1,
                dpi=300,
                facecolor='white',
                edgecolor='none')

    plt.close(fig)


def _extract_multi_value_metrics(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[float]]]:
    metrics_data = {}
    multi_value_metrics = ['PSNR', 'SSIM', 'LPIPS']

    for result in results:
        model_name = result.get('modelname', 'Unknown')
        if 'visualqualityresult' not in result:
            continue

        vq_result = result['visualqualityresult']

        for metric in multi_value_metrics:
            if metric not in metrics_data:
                metrics_data[metric] = {}

            if metric in vq_result:
                metric_data = vq_result[metric]
                if isinstance(metric_data, list):
                    valid_values = []
                    for val in metric_data:
                        try:
                            val_float = float(val)
                            if np.isfinite(val_float):
                                valid_values.append(val_float)
                        except (ValueError, TypeError):
                            continue
                    if valid_values:
                        metrics_data[metric][model_name] = valid_values

    return metrics_data


def _extract_fid_data(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    fid_data = {}

    for result in results:
        model_name = result.get('modelname', 'Unknown')
        model_type = _get_model_type(result)

        if 'visualqualityresult' not in result:
            continue

        vq_result = result['visualqualityresult']

        if 'FID' in vq_result:
            fid_info = vq_result['FID']
            if isinstance(fid_info, dict) and 'FID' in fid_info:
                fid_values = fid_info['FID']
                dataset_name = fid_info.get('datasetname', 'Unknown')

                stego_fid = None
                clean_fid = None

                if 'stego' in fid_values:
                    try:
                        stego_val = fid_values['stego']
                        if stego_val is not None and stego_val != 'N/A':
                            stego_fid = float(stego_val)
                    except (ValueError, TypeError):
                        pass

                if 'clean' in fid_values:
                    try:
                        clean_val = fid_values['clean']
                        if clean_val is not None and clean_val != 'N/A':
                            clean_fid = float(clean_val)
                    except (ValueError, TypeError):
                        pass

                if stego_fid is not None:
                    fid_data[model_name] = {
                        'datasetname': dataset_name,
                        'stego_fid': stego_fid,
                        'clean_fid': clean_fid,
                        'model_type': model_type
                    }

    return fid_data


def _get_consistent_colors(model_names: List[str]) -> Dict[str, Tuple[float, float, float]]:
    sorted_model_names = sorted(list(set(model_names)))
    colors = sns.color_palette("husl", len(sorted_model_names))
    return {model_name: colors[i] for i, model_name in enumerate(sorted_model_names)}


def _extract_all_psnr_values(results: List[Dict[str, Any]]) -> List[float]:
    """
    Extract all PSNR values from robustness results for normalization,
    and check if 'No Attacking' data is present.

    Returns:
        Tuple[List[float], bool]: A tuple containing:
            - A list of all valid PSNR values found.
            - A boolean indicating if any 'No Attacking' PSNR data was found.
    """
    psnr_values = []

    for result in results:
        if 'robustnessresult' not in result:
            continue

        robustness_result = result['robustnessresult']

        for noise_type, noise_data in robustness_result.items():
            if 'factors' not in noise_data:
                continue

            for factor_data in noise_data['factors'].values():
                # Extract PSNR from visualquality within factors
                if 'visualquality' in factor_data and 'PSNR' in factor_data['visualquality']:
                    psnr_data = factor_data['visualquality']['PSNR']
                    if isinstance(psnr_data, list):
                        for val in psnr_data:
                            try:
                                val_float = float(val)
                                if np.isfinite(val_float):  # Check for NaN or Inf
                                    psnr_values.append(val_float)
                            except (ValueError, TypeError):
                                continue
                    else:
                        try:
                            val_float = float(psnr_data)
                            if np.isfinite(val_float):
                                psnr_values.append(val_float)
                        except (ValueError, TypeError):
                            continue

                # Also check for PSNR directly in the factor_data level (like FID structure)
                # Although less common in robustness data, good to be thorough
                # This part is less likely needed based on previous code analysis, but kept for safety
                # if 'PSNR' in factor_data and factor_data['PSNR'] is not None:
                #     try:
                #         val_float = float(factor_data['PSNR'])
                #         if np.isfinite(val_float):
                #             psnr_values.append(val_float)
                #     except (ValueError, TypeError):
                #         pass

    return psnr_values


# In draw/utils.py

def _determine_global_psnr_range_for_auc(results: List[Dict[str, Any]], assumed_no_attack_psnr: float = 60.0) -> Tuple[
    float, float]:
    """
    Determine the global PSNR range [min, max] for AUC normalization,
    incorporating the logic for handling 'No Attacking' PSNR.

    Logic:
    1. Extract all PSNR values from results.
    2. If all extracted PSNR values are < assumed_no_attack_psnr (e.g., 60):
       a. Use assumed_no_attack_psnr as the global_max_psnr.
       b. Use the actual minimum PSNR found as global_min_psnr.
    3. Else (if any PSNR >= assumed_no_attack_psnr):
       a. Use the actual maximum PSNR found as global_max_psnr.
       b. Use the actual minimum PSNR found as global_min_psnr.

    Args:
        results: List of result dictionaries.
        assumed_no_attack_psnr: The PSNR value to assume for 'No Attacking' if needed.

    Returns:
        Tuple[float, float]: (global_min_psnr, global_max_psnr)
    """
    # 1. Extract PSNR values
    psnr_values = _extract_all_psnr_values(results)

    if not psnr_values:
        # Handle edge case: no PSNR data found
        print("Warning: No PSNR values found in results for AUC range determination. Returning (0, 1).")
        return 0.0, 1.0

    actual_min_psnr = float(np.min(psnr_values))
    actual_max_psnr = float(np.max(psnr_values))

    # 2. Apply the logic
    if actual_max_psnr < assumed_no_attack_psnr:
        # Case 1: All PSNR < 60
        # Use 60 as the representative 'No Attack' PSNR for max
        global_max_psnr = assumed_no_attack_psnr
        global_min_psnr = actual_min_psnr
    else:
        # Case 2: Some PSNR >= 60
        # Use the actual max PSNR + 10. found
        global_max_psnr = actual_max_psnr + 10.
        global_min_psnr = actual_min_psnr

    return global_min_psnr, global_max_psnr


def _normalize_psnr_global(psnr_value: float, global_min: float, global_max: float) -> float:
    if global_max > global_min:
        return (psnr_value - global_min) / (global_max - global_min)
    else:
        return 0.0


def _extract_accuracy_value(factor_data: Dict[str, Any]) -> List[float]:
    for key in factor_data.keys():
        if key.startswith('TPR@') and key.endswith('%FPR'):
            tpr_data = factor_data[key]
            if isinstance(tpr_data, list):
                valid_values = []
                for val in tpr_data:
                    try:
                        val_float = (float(val) + 1) / 2.
                        if np.isfinite(val_float):
                            valid_values.append(val_float)
                    except (ValueError, TypeError):
                        continue
                return valid_values
            else:
                try:
                    val_float = (float(tpr_data) + 1) / 2.
                    if np.isfinite(val_float):
                        return [val_float]
                except (ValueError, TypeError):
                    pass
    return []


def _base64_to_image(base64_string: str) -> np.ndarray:
    if not base64_string:
        return None

    try:
        if base64_string.startswith('image'):
            base64_string = base64_string.split(',')[1]
        image_data = base64.b64decode(base64_string)
        image = Image.open(BytesIO(image_data))
        return np.uint8(image)
    except Exception as e:
        print(f"Error converting base64 to image: {e}")
        return None


def _save_figure_with_tight_crop(fig: plt.Figure, save_path: str, filename: str) -> None:
    full_path = os.path.join(save_path, filename)
    os.makedirs(save_path, exist_ok=True)

    fig.savefig(full_path,
                format='pdf',
                bbox_inches='tight',
                pad_inches=0,
                dpi=300,
                facecolor='white',
                edgecolor='none')

    plt.close(fig)


def _resize_image(image: np.ndarray, width: int, height: int) -> np.ndarray:
    if image is None:
        return None

    pil_image = Image.fromarray(np.uint8(image))
    resized_image = pil_image.resize((width, height), Image.LANCZOS)
    return np.uint8(resized_image)


def _normalize_factors(factors: List[Union[float, int, str]], inversely_related: bool) -> np.ndarray:
    numeric_factors = []
    for f in factors:
        if f is None or f == 'None':
            numeric_factors.append(0.0)
        else:
            try:
                numeric_factors.append(float(f))
            except (ValueError, TypeError):
                numeric_factors.append(0.0)

    factors_array = np.array(numeric_factors)
    max_val = np.max(factors_array)
    if max_val > 0:
        normalized = factors_array / max_val
    else:
        normalized = np.zeros_like(factors_array)

    if inversely_related:
        normalized = 1.0 - normalized

    return normalized


def _extract_robustness_data(results: List[Dict[str, Any]], metric: str) -> Dict[str, Any]:
    extracted_data = {}

    for result in results:
        model_name = result.get('modelname', 'Unknown')
        model_type = _get_model_type(result)

        if 'robustnessresult' not in result:
            continue

        robustness_result = result['robustnessresult']

        for noise_type, noise_data in robustness_result.items():
            if noise_type not in extracted_data:
                extracted_data[noise_type] = {
                    'factors': {},
                    'factor_inversely_related': noise_data.get('factor_inversely_related', False),
                    'factorsymbol': noise_data.get('factorsymbol', 'Factor'),
                    'noisename': noise_data.get('noisename', noise_type)
                }

            if 'factors' in noise_data:
                for factor_str, factor_data in noise_data['factors'].items():
                    if factor_str not in extracted_data[noise_type]['factors']:
                        extracted_data[noise_type]['factors'][factor_str] = {}

                    if metric in factor_data:
                        metric_data = factor_data[metric]
                        if isinstance(metric_data, list) and len(metric_data) > 0:
                            avg_value = np.mean(metric_data)
                            std_value = np.std(metric_data) if len(metric_data) > 1 else 0.0
                        elif isinstance(metric_data, (int, float)):
                            avg_value = float(metric_data)
                            std_value = 0.0
                        else:
                            continue

                        extracted_data[noise_type]['factors'][factor_str][model_name] = {
                            'value': avg_value,
                            'std': std_value,
                            'model_type': model_type
                        }

    return extracted_data


def _count_valid_factors(data: Dict[str, Any], model_names: List[str]) -> int:
    valid_factor_count = 0
    for factor_str in data['factors'].keys():
        has_data = any(model_name in data['factors'][factor_str] for model_name in model_names)
        if has_data:
            valid_factor_count += 1
    return valid_factor_count


# --- Add these imports at the top of draw/utils.py if not already present ---


# --- Add these new functions to draw/utils.py ---

def _extract_robustness_curve_data(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[Tuple[float, float]]]]:
    """
    Extract TPR and PSNR data points for calculating AUC.
    Returns:
        Dict[model_name, Dict[noise_type, List[Tuple[psnr, tpr]]]]
        Note: PSNR is NOT normalized here yet.
    """
    curve_data = {}

    for result in results:
        model_name = result.get('modelname', 'Unknown_Model')
        curve_data[model_name] = {}

        if 'robustnessresult' not in result:
            continue

        robustness_result = result['robustnessresult']

        for noise_type, noise_data in robustness_result.items():
            points = []
            if 'factors' not in noise_data:
                continue

            for factor_str, factor_data in noise_data['factors'].items():
                # Extract TPR@N%FPR
                tpr_value = None
                # Look for common TPR-like metrics
                for key in factor_data.keys():
                    if key.startswith('TPR@'):
                        tpr_data = factor_data[key]
                        if isinstance(tpr_data, list):
                            tpr_value = np.mean(tpr_data)
                        elif isinstance(tpr_data, (int, float)):
                            tpr_value = float(tpr_data)
                        break  # Take the first TPR-like metric found

                # Extract PSNR from visualquality
                psnr_value = None
                if 'visualquality' in factor_data and 'PSNR' in factor_data['visualquality']:
                    psnr_data = factor_data['visualquality']['PSNR']
                    if isinstance(psnr_data, list):
                        psnr_value = np.mean(psnr_data)
                    elif isinstance(psnr_data, (int, float)):
                        psnr_value = float(psnr_data)

                if tpr_value is not None and psnr_value is not None and np.isfinite(tpr_value) and np.isfinite(
                        psnr_value):
                    points.append((psnr_value, tpr_value))
            # Store points for this model-noise pair
            curve_data[model_name][noise_type] = points

    return curve_data


# Example snippet showing how to use the new range determination in AUC calculation context

def _compute_auc_scores(curve_data: Dict[str, Dict[str, List[Tuple[float, float]]]], results: List[Dict[str, Any]]) -> \
        Dict[str, Dict[str, float]]:
    """
    Compute AUC scores, but iterate over noise types first, then models.
    Output structure remains: {model_name: {noise_type: auc_score}}
    """
    # --- 1. Determine Global PSNR Range using the new logic ---
    global_min_psnr, global_max_psnr = _determine_global_psnr_range_for_auc(results)
    psnr_range = global_max_psnr - global_min_psnr

    if psnr_range <= 0:
        print("Error: Invalid PSNR range for AUC calculation. Cannot proceed.")
        return {model: {nt: np.nan for nt in nts} for model, nts in curve_data.items()}

    # Initialize auc_scores with model -> noise_type structure
    auc_scores = {model: {} for model in curve_data}

    # --- 2. Collect all unique noise types (excluding 'No Attacking' if needed) ---
    all_noise_types = set()
    for noise_dict in curve_data.values():
        for nt in noise_dict.keys():
            if nt != "No Attacking":
                all_noise_types.add(nt)
    all_noise_types = sorted(all_noise_types)  # Optional: for consistent order

    # --- 3. Outer loop: noise_type; Inner loop: model_name ---
    for noise_type in all_noise_types:
        if noise_type == "No Attacking":
            continue
        for model_name in curve_data:
            points = curve_data[model_name].get(noise_type, [])
            normalized_points = [(0, 0)]

            # Normalize PSNR and add data points from attacks
            for psnr, tpr in points:
                if np.isfinite(psnr) and np.isfinite(tpr):
                    # psnr_norm = (psnr - global_min_psnr) / psnr_range
                    # psnr_norm = np.clip(psnr_norm, 0.0, 1.0)
                    psnr_norm = psnr
                    normalized_points.append((psnr_norm, tpr))

            # --- 4. Handle 'No Attacking' TPR (same as before, per model) ---
            tpr_no_attack = None
            model_result_dict = next((r for r in results if r.get('modelname') == model_name), None)
            if model_result_dict and 'robustnessresult' in model_result_dict:
                no_attack_data = model_result_dict['robustnessresult'].get('No Attacking')
                if no_attack_data and 'factors' in no_attack_data:
                    no_attack_factors = no_attack_data['factors']
                    for factor_key, factor_data in no_attack_factors.items():
                        for key in factor_data.keys():
                            if key.startswith('TPR@'):
                                tpr_data = factor_data[key]
                                if isinstance(tpr_data, list):
                                    tpr_no_attack = float(np.mean(tpr_data))
                                elif isinstance(tpr_data, (int, float)):
                                    tpr_no_attack = float(tpr_data)
                                if tpr_no_attack is not None and np.isfinite(tpr_no_attack):
                                    break
                        if tpr_no_attack is not None and np.isfinite(tpr_no_attack):
                            break

            # Note: Currently, the 'No Attacking' point is NOT added to normalized_points
            # (as it was commented out in original). Keeping same behavior.
            normalized_points.append((1., tpr_no_attack))
            # Sort by normalized PSNR
            normalized_points.sort(key=lambda x: x[0])

            # Calculate AUC
            if len(normalized_points) >= 2:
                x_vals = np.array([p[0] for p in normalized_points])
                y_vals = np.array([p[1] for p in normalized_points])
                auc = integrate.trapz(y_vals, x_vals)
                auc_scores[model_name][noise_type] = auc
            else:
                print(f"Warning: Not enough points to calculate AUC for {model_name} - {noise_type}. AUC set to NaN.")
                auc_scores[model_name][noise_type] = np.nan

    # --- 5. Calculate total score per model (average of AUC scores across all noise types) ---
    model_total_scores = {}
    for model_name in auc_scores:
        valid_auc_scores = [auc for auc in auc_scores[model_name].values() if not np.isnan(auc)]
        if valid_auc_scores:
            model_total_scores[model_name] = np.mean(valid_auc_scores)
        else:
            model_total_scores[model_name] = np.nan  # All AUCs were NaN

    return auc_scores
