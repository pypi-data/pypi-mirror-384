import os
import math
import json
from typing import Any, Dict, List

import torch
import shutil
import base64
import threading
import numpy as np
from PIL import Image
from io import BytesIO

from numpy import ndarray

from watermarklab.utils.basemodel import AttackerWithFactors
from watermarklab.utils.logger import logger

__all__ = ["lightweight_json_result"]


def _normalize_secret(secret):
    """
    Normalizes a list of secret bits to the range [0, 1] for consistent visualization.

    This function scales the input values linearly so that:
    - Minimum value maps to 0.0
    - Maximum value maps to 1.0
    - Constant inputs (e.g., all zeros) are mapped to 0.5

    Used primarily for generating grayscale or color visualizations of watermark patterns.

    Args:
        secret (list or array-like): Sequence of numeric values (e.g., binary bits or continuous values).

    Returns:
        List[float]: Normalized values in the range [0.0, 1.0], as a Python list.
                     Returns empty list if input is empty.
    """
    secret = np.array(secret, dtype=np.float32)
    if secret.size == 0:
        return secret.tolist()
    min_val = np.min(secret)
    max_val = np.max(secret)
    if min_val == max_val:
        secret.fill(0.5)  # Avoid division by zero; use neutral gray
    else:
        secret = (secret - min_val) / (max_val - min_val)
    return secret.tolist()


def _remove_evaluated_attacker(result_json: dict, noise_models: List[AttackerWithFactors]) -> List[
    AttackerWithFactors]:
    """
    Remove evaluated attackers, return filtered attacker list
    For each attacker, check if all its factors are completed (non-empty dict)
    If all factors are completed, completely remove the attacker
    If some factors are completed, remove completed factors, keep uncompleted factors
    """
    filtered_noise_models = []

    for noise_model in noise_models:
        noise_type = noise_model.attackername
        factors_dict = result_json["robustnessresult"][noise_type]["factors"]

        # Get completed factors (non-empty dict factors)
        completed_factors_str = []
        for factor_key, factor_value in factors_dict.items():
            # If factor_value is not empty dict, this factor is completed
            if factor_value:  # non-empty dict
                completed_factors_str.append(factor_key)

        # Check if all original factors in this attacker are completed
        all_original_factors_completed = True
        for original_factor in noise_model.factors:
            original_factor_str = str(original_factor)
            if original_factor_str not in completed_factors_str:
                all_original_factors_completed = False
                break

        if all_original_factors_completed:
            # All original factors are completed, completely skip this attacker
            continue
        else:
            # Some factors are completed, only keep uncompleted factors
            remaining_factors = []
            for factor in noise_model.factors:
                factor_str = str(factor)
                if factor_str not in completed_factors_str:
                    remaining_factors.append(factor)

            # Create new attacker object, only include uncompleted factors
            if remaining_factors:  # Ensure there are remaining factors
                new_noise_model = AttackerWithFactors(
                    attacker=noise_model.attacker,
                    attackername=noise_model.attackername,
                    factors=remaining_factors,
                    factorsymbol=noise_model.factorsymbol
                )
                filtered_noise_models.append(new_noise_model)

    return filtered_noise_models


def _remove_empty_lists(d: dict) -> dict:
    """
    Recursively removes all keys with empty list values from a nested dictionary.

    This is useful for cleaning up JSON-serializable result structures before saving,
    eliminating clutter from unused metric entries or failed experiments.

    Example:
        Input:  {"a": [], "b": {"c": [1,2], "d": []}, "e": "value"}
        Output: {"b": {"c": [1,2]}, "e": "value"}

    Args:
        d (dict): Input dictionary, possibly deeply nested.

    Returns:
        dict: A new dictionary with all key-value pairs removed where the value is an empty list.
              Nested dictionaries are cleaned recursively. Keys with non-list values are preserved.
    """
    if not isinstance(d, dict):
        return d

    result = {}
    for key, value in d.items():
        if isinstance(value, list):
            if len(value) == 0:
                continue  # Skip keys with empty lists
            else:
                result[key] = value  # Keep keys with non-empty lists
        elif isinstance(value, dict):
            # Recursively clean nested dictionary
            cleaned = _remove_empty_lists(value)
            if cleaned:  # Only include if not empty after cleaning
                result[key] = cleaned
        else:
            result[key] = value  # Preserve all other types (str, int, float, etc.)
    return result


def _composite_image_with_secret(base_img, secret_img) -> str:
    """
    Composites the extracted binary secret watermark onto the bottom-right corner of the base image.

    The secret image is resized to 1/4 of the original image's width and height (1/16 area)
    using nearest-neighbor interpolation to preserve sharp edges (important for binary patterns).
    It is then pasted with full opacity onto the base image.

    This function operates entirely in memory and does not require file paths.

    Args:
        base_img: The base image (e.g., noised stego image). Can be a PIL Image, numpy array, or file path string.
        secret_img: The extracted secret image. Can be a PIL Image, numpy array, or file path string.
                                                          Can be None.

    Returns:
        str: Base64-encoded composite image.
              If `secret_img` is None, returns the base image as Base64.
    """
    from PIL import Image
    import numpy as np
    import base64
    import os
    from io import BytesIO

    def to_pil(img):
        """Converts input to PIL.Image, assuming RGB if 3D, grayscale if 2D."""
        if isinstance(img, Image.Image):
            return img
        elif isinstance(img, np.ndarray):
            if img.ndim == 3 and img.shape[2] == 3:
                return Image.fromarray(img.astype(np.uint8), mode='RGB')
            elif img.ndim == 2:
                return Image.fromarray(img.astype(np.uint8), mode='L')
            else:
                raise ValueError(f"Unsupported numpy array shape: {img.shape}")
        elif isinstance(img, str):
            # Check if the file path exists
            if not os.path.exists(img):
                raise FileNotFoundError(f"Image file not found: {img}")
            # Assume it's a file path
            img = np.uint8(Image.open(img))
            if img.ndim == 3 and img.shape[2] == 3:
                return Image.fromarray(img.astype(np.uint8), mode='RGB')
            elif img.ndim == 2:
                return Image.fromarray(img.astype(np.uint8), mode='L')
            else:
                raise ValueError(f"Unsupported numpy array shape: {img.shape}")
        else:
            raise ValueError(f"Unsupported image type: {type(img)}")

    # Convert inputs to PIL
    base_pil = to_pil(base_img)
    width, height = base_pil.size

    # If no secret, return base64 of base image
    if secret_img is None:
        buffer = BytesIO()
        base_pil.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()
        return img_base64

    secret_pil = to_pil(secret_img)

    # Resize secret to 1/4 width and height → area = 1/16
    new_secret_width = width // 4
    new_secret_height = height // 4
    secret_resized = secret_pil.resize((new_secret_width, new_secret_height), Image.NEAREST)

    # Position: bottom-right corner
    x = width - secret_resized.width
    y = height - secret_resized.height

    # Create a blank RGBA image for the secret overlay (to control opacity)
    secret_rgba = Image.new("RGBA", base_pil.size, (0, 0, 0, 0))
    # Paste the resized secret onto the overlay at the calculated position
    secret_rgba.paste(secret_resized, (x, y))

    # Convert base image to RGBA for alpha compositing
    base_rgba = base_pil.convert("RGBA")

    # Composite: base + secret overlay
    # Use the secret's own alpha or treat it as full opacity
    composite = Image.alpha_composite(base_rgba, secret_rgba)

    # Convert back to RGB (remove alpha)
    composite = composite.convert("RGB")

    # Encode to Base64
    buffer = BytesIO()
    composite.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    return img_base64


def _reshape_secret(secret):
    """
    Reshapes a secret bit sequence into a 2D square array for visual representation.

    Supports two input types:
    1. List of bits (e.g., [1,0,1,...]) → Pads and reshapes into square grid
    2. Pre-shaped numpy array → Validates and returns directly

    Generates a color-coded image where:
    - 0 → Black
    - 1 → White
    - Padded values (2) → Red (for visibility)

    Used in result reporting to visualize embedded watermark patterns.

    Args:
        secret (list or np.ndarray): Secret data to visualize.

    Returns:
        Tuple[List, np.ndarray]:
            - First element: The reshaped secret as a nested list (JSON-serializable).
            - Second element: A 2D or 3D numpy array suitable for image rendering.

    Raises:
        TypeError: If input is neither list nor numpy array.
        ValueError: If ndarray has unsupported shape (not 2D or 3D).
    """
    if isinstance(secret, list):
        L = len(secret)
        secret = _normalize_secret(secret)
        side = int(math.ceil(math.sqrt(L)))
        padded_list = np.pad(secret, (0, side * side - L), mode='constant', constant_values=2)
        array_2d = padded_list.reshape((side, side))
        watermark_visual = np.zeros((side, side, 3), dtype=np.uint8)
        watermark_visual[array_2d == 0] = [0, 0, 0]  # Black
        watermark_visual[array_2d == 1] = [255, 255, 255]  # White
        watermark_visual[array_2d == 2] = [255, 0, 0]  # Red (padding)
        return secret, watermark_visual
    elif isinstance(secret, np.ndarray):
        if secret.ndim == 2:
            return secret.tolist(), secret
        elif secret.ndim == 3:
            if secret.shape[2] == 3:
                return secret.tolist(), secret  # RGB image
            elif secret.shape[2] == 1:
                return secret.tolist(), secret[:, :, 0]  # Grayscale
            else:
                raise ValueError("Unsupported ndarray shape: expected 2D or 3D array with 1 or 3 channels")
        else:
            raise ValueError("Unsupported ndarray shape: expected 2D or 3D array")
    else:
        raise TypeError("secret must be list or numpy.ndarray")


def _delete_in_thread(path):
    """
    Deletes a file or directory asynchronously in a separate thread.

    This prevents blocking the main evaluation pipeline during cleanup of large temporary folders
    (e.g., noisy image directories after decoding).

    Note: This is a fire-and-forget operation. No error handling is performed in the thread.

    Args:
        path (str): Path to the file or directory to delete.

    Returns:
        threading.Thread: The started thread object. Caller may choose to `.join()` it later.
    """

    def delete_path():
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.exists(path):
                os.remove(path)
        except Exception as e:
            logger.warning(f"Failed to delete {path}: {e}")

    thread = threading.Thread(target=delete_path)
    thread.start()
    return thread


def _image_to_base64(file_path):
    """
    Converts an image file to a Base64-encoded string.

    The resulting string can be embedded directly into JSON or HTML (e.g., `data:image/png;base64,...`)
    for lightweight reporting and web visualization.

    Args:
        file_path (str/Path): Path to the image file (e.g., PNG, JPG).

    Returns:
        str: Base64-encoded string of the image content.

    Raises:
        FileNotFoundError: If the file does not exist.
        OSError: If the file cannot be read.
    """
    with open(file_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')


def _get_base64_images(base_dir: str, is_pgw: bool) -> dict:
    """
    Retrieves Base64-encoded visual data for the first generated image (image_1/iter_1),
    with the extracted secret watermark composited onto the stego image.

    This function:
    - Loads stego, cover/clean, residual images
    - Overlays the 'secret.png' onto 'stego.png' at bottom-right (1/4 size, sharp)
    - Returns a flat dictionary for web visualization

    For PGW models:
        - cover, stego (with secret overlay), residual
    For IGW models:
        - clean, stego (with secret overlay), residual, prompt

    Args:
        base_dir (str): Root directory containing the 'images' subfolder.
        is_pgw (bool): If True, loads PGW-specific files; otherwise, IGW files.

    Returns:
        Dict[str, Union[str, list]]: A flat dictionary containing:
            - 'stego': Base64 of stego image with secret overlaid
            - 'cover' or 'clean': Base64 of cover image
            - 'residual': Base64 of residual
            - 'prompt': JSON string (IGW only)
            - Skips any missing files.
    """
    result = {}
    image_dir = os.path.join(base_dir, "image_1", "iter_1")

    # Paths
    stego_path = os.path.join(image_dir, "stego.png")
    secret_path = os.path.join(image_dir, "secret.png")  # embedded secret (ground truth)
    residual_path = os.path.join(image_dir, "residual.png")

    # --- 1. Process stego with secret overlay ---
    if os.path.exists(stego_path):
        try:
            # Composite stego + secret
            if os.path.exists(stego_path):
                stego = np.float32(Image.open(stego_path))
            else:
                stego = None
            if os.path.exists(secret_path):
                secret = np.float32(Image.open(secret_path))
            else:
                secret = None
            result["stego"] = _composite_image_with_secret(stego, secret)
        except Exception as e:
            logger.warning(f"Failed to composite stego with secret: {e}")
            result["stego"] = _image_to_base64(stego_path)  # fallback
    else:
        logger.warning(f"Stego image not found: {stego_path}")

    # --- 2. Load residual ---
    if os.path.exists(residual_path):
        try:
            result["residual"] = _image_to_base64(residual_path)
        except Exception as e:
            logger.warning(f"Failed to load residual: {e}")

    # --- 3. Load cover (PGW) or clean (IGW) ---
    if is_pgw:
        cover_path = os.path.join(image_dir, "cover.png")
        if os.path.exists(cover_path):
            try:
                result["cover"] = _image_to_base64(cover_path)
            except Exception as e:
                logger.warning(f"Failed to load cover: {e}")
    else:
        clean_path = os.path.join(image_dir, "clean.png")
        if os.path.exists(clean_path):
            try:
                result["clean"] = _image_to_base64(clean_path)
            except Exception as e:
                logger.warning(f"Failed to load clean: {e}")

        prompt_path = os.path.join(image_dir, "prompt.json")
        if os.path.exists(prompt_path):
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    result["prompt"] = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load prompt: {e}")

    return result


def _get_system_info():
    """
    Returns a dictionary containing detailed system information including CPU, GPU, OS, and software versions.
    Uses 'cpuinfo' for accurate CPU model detection across platforms.

    This information is useful for experiment reproducibility and performance analysis.

    Returns:
        Dict[str, Any]: System information with the following keys:
            - cpu: model, cores_physical, cores_logical, frequency_current, frequency_max
            - gpus: list of GPU dicts (name, memory_total, memory_used) or error message
            - os: OS name and version
            - python_version: Python version string
            - torch_version: PyTorch version string
            - cuda_available: Boolean indicating CUDA availability
            - cuda_version: CUDA version (if available)
            - gpu_name: Name of the primary CUDA GPU (if available)
    """
    import platform
    import psutil
    import torch
    try:
        import cpuinfo  # pip install py-cpuinfo
    except ImportError:
        cpuinfo = None

    system_info = {}

    # === CPU Information ===
    cpu_data = {}
    if cpuinfo:
        try:
            cpu_info = cpuinfo.get_cpu_info()
            cpu_data["model"] = cpu_info.get("brand_raw", "N/A")  # e.g., "Intel(R) Core(TM) i7-11800H"
        except Exception as e:
            cpu_data["model"] = f"Error reading CPU info: {e}"
    else:
        # Fallback to platform.processor() if cpuinfo not available
        cpu_data["model"] = platform.processor() or "N/A (install 'py-cpuinfo' for full info)"

    cpu_data["cores_physical"] = psutil.cpu_count(logical=False) or "N/A"
    cpu_data["cores_logical"] = psutil.cpu_count(logical=True) or "N/A"
    cpu_data["frequency_current"] = f"{psutil.cpu_freq().current:.2f} MHz" if psutil.cpu_freq() else "N/A"
    cpu_data["frequency_max"] = f"{psutil.cpu_freq().max:.2f} MHz" if psutil.cpu_freq() else "N/A"

    system_info["cpu"] = cpu_data

    # === GPU Information ===
    try:
        import pynvml
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        gpus = []
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            gpu_info = {
                "name": pynvml.nvmlDeviceGetName(handle).decode('utf-8') if isinstance(pynvml.nvmlDeviceGetName(handle),
                                                                                       bytes) else pynvml.nvmlDeviceGetName(
                    handle),
                "memory_total": f"{mem_info.total / 1024 ** 3:.2f} GB",
                "memory_used": f"{mem_info.used / 1024 ** 3:.2f} GB",
            }
            gpus.append(gpu_info)
        system_info["gpus"] = gpus
        pynvml.nvmlShutdown()
    except (ImportError, NameError):
        system_info["gpus"] = "pynvml not installed (pip install pynvml)"
    except Exception as e:
        system_info["gpus"] = f"GPU detection failed: {e}"

    # === OS & Software ===
    system_info["os"] = f"{platform.system()} {platform.release()}"
    system_info["python_version"] = platform.python_version()
    system_info["torch_version"] = torch.__version__
    system_info["cuda_available"] = torch.cuda.is_available()
    if torch.cuda.is_available():
        system_info["cuda_version"] = torch.version.cuda
        system_info["gpu_name"] = torch.cuda.get_device_name(0)  # First GPU

    return system_info


def _is_igw(dataloader):
    """
    Determines if a DataLoader is for In-Generation Watermarking (IGW) or Post-Generation Watermarking (PGW).

    This heuristic inspects the type of the first data element:
    - IGW: First element is a string (text prompt used in diffusion models)
    - PGW: First element is an image (numpy array or torch tensor)

    This is critical for routing data correctly in evaluation pipelines and visualization.

    Args:
        dataloader (DataLoader): The dataloader to inspect.

    Returns:
        bool: True if the dataloader provides text prompts (IGW), False if it provides images (PGW).

    Raises:
        RuntimeError: If the dataloader is empty or the data type is unrecognized.
    """
    try:
        # Get one batch from the dataloader
        first_batch = next(iter(dataloader))

        # The batch structure is: (data_list, secret_list, img_indexes, iter_indexes)
        data_list = first_batch[0]

        if not data_list:
            raise RuntimeError("DataLoader's data_list is empty.")

        # Check type of the first data item
        first_data = data_list[0]

        # IGW: text prompt (str)
        if isinstance(first_data, str):
            return True

        # PGW: image (numpy array or torch tensor)
        if isinstance(first_data, (np.ndarray, torch.Tensor)):
            return False

        # Fallback: check common image-like properties
        if hasattr(first_data, 'shape') and len(first_data.shape) >= 2:
            return False

        raise RuntimeError(f"Unknown data type in dataloader: {type(first_data)}")

    except StopIteration:
        raise RuntimeError("Dataloader is empty.")
    except Exception as e:
        raise RuntimeError(f"Failed to determine dataloader type: {e}")


def replace_infinity(data):
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            result[key] = replace_infinity(value)
        return result

    elif isinstance(data, list):
        result = []
        for item in data:
            result.append(replace_infinity(item))
        return result

    elif isinstance(data, (int, float)) and (math.isinf(data) or math.isnan(data)):
        return 60.0

    else:
        return data


def lightweight_json_result(final_report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process the complete evaluation report to lightweight format by converting
    all numeric lists in robustness results to mean values.

    This function takes the complete evaluation report and transforms the robustness
    results section by replacing all numeric value lists with their mean values
    in single-element lists. This significantly reduces file size while preserving
    the essential statistical information.

    Args:
        final_report (Dict[str, Any]): Complete evaluation report dictionary
            containing model metadata, visual quality results, robustness results,
            and other evaluation metrics.

    Returns:
        Dict[str, Any]: Lightweight evaluation report with robustness results
            converted to mean values format, reducing file size significantly.
    """
    # Create a copy of the final report to avoid modifying the original
    lightweight_report = final_report.copy()

    # Process robustness results if they exist
    if "robustnessresult" in lightweight_report:
        robustness_result = lightweight_report["robustnessresult"]
        processed_robustness = {}

        # Process each noise attack type (e.g., "JPEG", "Gaussian Blur", etc.)
        for noise_type, noise_data in robustness_result.items():
            processed_robustness[noise_type] = {}

            # Copy non-factors fields directly (metadata like noisename, factorsymbol, etc.)
            for key, value in noise_data.items():
                if key != "factors":
                    processed_robustness[noise_type][key] = value

            # Process factors (attack intensities like quality=50, sigma=2.0, etc.)
            if "factors" in noise_data:
                processed_robustness[noise_type]["factors"] = {}

                # Process each factor/intensity level
                for factor, factor_data in noise_data["factors"].items():
                    processed_robustness[noise_type]["factors"][factor] = {}

                    # Process each metric - convert all numeric lists to mean values
                    for key, value in factor_data.items():
                        # Handle visual quality metrics dictionary (PSNR, SSIM, LPIPS)
                        if key == "visualquality" and isinstance(value, dict):
                            processed_robustness[noise_type]["factors"][factor][key] = {}
                            # Process each visual quality metric
                            for metric_name, metric_values in value.items():
                                if isinstance(metric_values, list) and len(metric_values) > 0:
                                    # Calculate mean and convert to single-element list
                                    mean_value = float(np.mean(metric_values))
                                    processed_robustness[noise_type]["factors"][factor][key][metric_name] = [mean_value]
                                else:
                                    # If no values, set to [0.0]
                                    processed_robustness[noise_type]["factors"][factor][key][metric_name] = [0.0]

                        # Handle regular numeric list metrics (BER, Extract Accuracy, detection values, etc.)
                        elif isinstance(value, list) and len(value) > 0:
                            # Calculate mean and convert to single-element list
                            mean_value = float(np.mean(value))
                            processed_robustness[noise_type]["factors"][factor][key] = [mean_value]

                        # Copy non-list values directly (strings, booleans, numbers, etc.)
                        else:
                            processed_robustness[noise_type]["factors"][factor][key] = value
            else:
                # If no factors field, copy the entire noise data directly
                processed_robustness[noise_type] = noise_data

        # Update the lightweight report with processed robustness results
        lightweight_report["robustnessresult"] = processed_robustness

    return lightweight_report
