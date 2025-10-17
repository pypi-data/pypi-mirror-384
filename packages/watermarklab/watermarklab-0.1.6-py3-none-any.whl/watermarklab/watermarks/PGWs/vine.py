# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT
import os
import gc
import torch
import numpy as np
from PIL import Image
import torch.nn as nn
from typing import List
from numpy import ndarray
from peft import LoraConfig
from torchvision import models
from torchvision import transforms
from accelerate.utils import set_seed
from huggingface_hub import PyTorchModelHubMixin
from transformers import AutoTokenizer, CLIPTextModel
from watermarklab.utils.basemodel import BaseWatermarkModel, Result
from diffusers import AutoencoderKL, UNet2DConditionModel, DDPMScheduler

__all__ = ["VINE"]

from watermarklab.utils.logger import logger


def make_1step_sched(device):
    noise_scheduler_1step = DDPMScheduler.from_pretrained("stabilityai/sd-turbo", subfolder="scheduler")
    noise_scheduler_1step.set_timesteps(1, device=device)
    noise_scheduler_1step.alphas_cumprod = noise_scheduler_1step.alphas_cumprod.to(device)
    return noise_scheduler_1step


def my_vae_encoder_fwd(self, sample):
    sample = self.conv_in(sample)
    l_blocks = []
    for down_block in self.down_blocks:
        l_blocks.append(sample)
        sample = down_block(sample)
    sample = self.mid_block(sample)
    sample = self.conv_norm_out(sample)
    sample = self.conv_act(sample)
    sample = self.conv_out(sample)
    self.current_down_blocks = l_blocks
    return sample


def my_vae_decoder_fwd(self, sample, latent_embeds=None):
    sample = self.conv_in(sample)
    upscale_dtype = next(iter(self.up_blocks.parameters())).dtype
    # middle
    sample = self.mid_block(sample, latent_embeds)
    sample = sample.to(upscale_dtype)
    if not self.ignore_skip:
        skip_convs = [self.skip_conv_1, self.skip_conv_2, self.skip_conv_3, self.skip_conv_4]
        # up
        for idx, up_block in enumerate(self.up_blocks):
            skip_in = skip_convs[idx](self.incoming_skip_acts[::-1][idx] * self.gamma)
            # add skip
            sample = sample + skip_in
            sample = up_block(sample, latent_embeds)
    else:
        for idx, up_block in enumerate(self.up_blocks):
            sample = up_block(sample, latent_embeds)
    # post-process
    if latent_embeds is None:
        sample = self.conv_norm_out(sample)
    else:
        sample = self.conv_norm_out(sample, latent_embeds)
    sample = self.conv_act(sample)
    sample = self.conv_out(sample)
    return sample


class Dense(nn.Module):
    def __init__(self, in_features, out_features, activation='relu', kernel_initializer='he_normal'):
        super(Dense, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.activation = activation
        self.kernel_initializer = kernel_initializer

        self.linear = nn.Linear(in_features, out_features)
        # initialization
        if kernel_initializer == 'he_normal':
            nn.init.kaiming_normal_(self.linear.weight)
        else:
            raise NotImplementedError

    def forward(self, inputs):
        outputs = self.linear(inputs)
        if self.activation is not None:
            if self.activation == 'relu':
                outputs = nn.ReLU(inplace=True)(outputs)
        return outputs


class Conv2D(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size=3, activation='relu', strides=1):
        super(Conv2D, self).__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.activation = activation
        self.strides = strides

        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size, strides, int((kernel_size - 1) / 2))
        # default: using he_normal as the kernel initializer
        nn.init.kaiming_normal_(self.conv.weight)

    def forward(self, inputs):
        outputs = self.conv(inputs)
        if self.activation is not None:
            if self.activation == 'relu':
                outputs = nn.ReLU(inplace=True)(outputs)
            else:
                raise NotImplementedError
        return outputs


class ConditionAdaptor(nn.Module):
    def __init__(self):
        super(ConditionAdaptor, self).__init__()

        self.secret_dense1 = Dense(100, 64 * 64, activation='relu')
        self.secret_dense2 = Dense(64 * 64, 3 * 64 * 64, activation='relu')
        self.conv1 = Conv2D(6, 6, 3, activation='relu')
        self.conv2 = Conv2D(6, 3, 3, activation=None)

    def forward(self, secrect, img_feature):
        secrect = 2 * (secrect - .5)
        secrect = self.secret_dense1(secrect)
        secrect = self.secret_dense2(secrect)
        secrect = secrect.reshape(-1, 3, 64, 64)

        secrect_enlarged = nn.Upsample(scale_factor=(4, 4))(secrect)
        inputs = torch.cat([secrect_enlarged, img_feature], dim=1)
        conv1 = self.conv1(inputs)
        conv2 = self.conv2(conv1)

        return conv2


class CustomConvNeXt(nn.Module, PyTorchModelHubMixin):
    def __init__(self, secret_size, ckpt_path=None, device=None):
        super(CustomConvNeXt, self).__init__()
        self.convnext = models.convnext_base()
        self.convnext.classifier.append(nn.Linear(in_features=1000, out_features=secret_size, bias=True))
        self.convnext.classifier.append(nn.Sigmoid())

        if ckpt_path is not None:
            self.load_ckpt_from_state_dict(ckpt_path, device)

    def load_ckpt_from_state_dict(self, ckpt_path, device):
        self.convnext.load_state_dict(torch.load(os.path.join(ckpt_path, 'CustomConvNeXt.pth')))
        self.convnext.to(device)

    def forward(self, x):
        x = self.convnext(x)
        return x


class VAE_encode(nn.Module):
    def __init__(self, vae, vae_b2a=None):
        super(VAE_encode, self).__init__()
        self.vae = vae
        self.vae_b2a = vae_b2a

    def forward(self, x, direction):
        assert direction in ["a2b", "b2a"]
        if direction == "a2b":
            _vae = self.vae
        else:
            _vae = self.vae_b2a
        return _vae.encode(x).latent_dist.mode() * _vae.config.scaling_factor


class VAE_decode(nn.Module):
    def __init__(self, vae, vae_b2a=None):
        super(VAE_decode, self).__init__()
        self.vae = vae
        self.vae_b2a = vae_b2a

    def forward(self, x, direction):
        assert direction in ["a2b", "b2a"]
        if direction == "a2b":
            _vae = self.vae
        else:
            _vae = self.vae_b2a
        assert _vae.encoder.current_down_blocks is not None
        _vae.decoder.incoming_skip_acts = _vae.encoder.current_down_blocks
        x_decoded = (_vae.decode(x / _vae.config.scaling_factor).sample).clamp(-1, 1)
        return x_decoded


def initialize_unet(rank, return_lora_module_names=False):
    unet = UNet2DConditionModel.from_pretrained("stabilityai/sd-turbo", subfolder="unet")
    unet.requires_grad_(False)
    unet.train()
    l_target_modules_encoder, l_target_modules_decoder, l_modules_others = [], [], []
    l_grep = ["to_k", "to_q", "to_v", "to_out.0", "conv", "conv1", "conv2", "conv_in", "conv_shortcut", "conv_out",
              "proj_out", "proj_in", "ff.net.2", "ff.net.0.proj"]
    for n, p in unet.named_parameters():
        if "bias" in n or "norm" in n: continue
        for pattern in l_grep:
            if pattern in n and ("down_blocks" in n or "conv_in" in n):
                l_target_modules_encoder.append(n.replace(".weight", ""))
                break
            elif pattern in n and "up_blocks" in n:
                l_target_modules_decoder.append(n.replace(".weight", ""))
                break
            elif pattern in n:
                l_modules_others.append(n.replace(".weight", ""))
                break
    lora_conf_encoder = LoraConfig(r=rank, init_lora_weights="gaussian", target_modules=l_target_modules_encoder,
                                   lora_alpha=rank)
    lora_conf_decoder = LoraConfig(r=rank, init_lora_weights="gaussian", target_modules=l_target_modules_decoder,
                                   lora_alpha=rank)
    lora_conf_others = LoraConfig(r=rank, init_lora_weights="gaussian", target_modules=l_modules_others,
                                  lora_alpha=rank)
    unet.add_adapter(lora_conf_encoder, adapter_name="default_encoder")
    unet.add_adapter(lora_conf_decoder, adapter_name="default_decoder")
    unet.add_adapter(lora_conf_others, adapter_name="default_others")
    unet.set_adapters(["default_encoder", "default_decoder", "default_others"])
    if return_lora_module_names:
        return unet, l_target_modules_encoder, l_target_modules_decoder, l_modules_others
    else:
        return unet


def initialize_unet_no_lora(path="stabilityai/sd-turbo"):
    unet = UNet2DConditionModel.from_pretrained(path, subfolder="unet")
    unet.requires_grad_(True)
    unet.train()
    return unet


def initialize_vae(rank=4, return_lora_module_names=False):
    vae = AutoencoderKL.from_pretrained("stabilityai/sd-turbo", subfolder="vae")
    vae.requires_grad_(False)
    vae.encoder.forward = my_vae_encoder_fwd.__get__(vae.encoder, vae.encoder.__class__)
    vae.decoder.forward = my_vae_decoder_fwd.__get__(vae.decoder, vae.decoder.__class__)
    vae.requires_grad_(True)
    vae.train()
    # add the skip connection convs
    vae.decoder.skip_conv_1 = torch.nn.Conv2d(512, 512, kernel_size=(1, 1), stride=(1, 1),
                                              bias=False).cuda().requires_grad_(True)
    vae.decoder.skip_conv_2 = torch.nn.Conv2d(256, 512, kernel_size=(1, 1), stride=(1, 1),
                                              bias=False).cuda().requires_grad_(True)
    vae.decoder.skip_conv_3 = torch.nn.Conv2d(128, 512, kernel_size=(1, 1), stride=(1, 1),
                                              bias=False).cuda().requires_grad_(True)
    vae.decoder.skip_conv_4 = torch.nn.Conv2d(128, 256, kernel_size=(1, 1), stride=(1, 1),
                                              bias=False).cuda().requires_grad_(True)
    torch.nn.init.constant_(vae.decoder.skip_conv_1.weight, 1e-5)
    torch.nn.init.constant_(vae.decoder.skip_conv_2.weight, 1e-5)
    torch.nn.init.constant_(vae.decoder.skip_conv_3.weight, 1e-5)
    torch.nn.init.constant_(vae.decoder.skip_conv_4.weight, 1e-5)
    vae.decoder.ignore_skip = False
    vae.decoder.gamma = 1
    l_vae_target_modules = ["conv1", "conv2", "conv_in", "conv_shortcut",
                            "conv", "conv_out", "skip_conv_1", "skip_conv_2", "skip_conv_3",
                            "skip_conv_4", "to_k", "to_q", "to_v", "to_out.0",
                            ]
    vae_lora_config = LoraConfig(r=rank, init_lora_weights="gaussian", target_modules=l_vae_target_modules)
    vae.add_adapter(vae_lora_config, adapter_name="vae_skip")
    if return_lora_module_names:
        return vae, l_vae_target_modules
    else:
        return vae


def initialize_vae_no_lora(path="stabilityai/sd-turbo"):
    vae = AutoencoderKL.from_pretrained(path, subfolder="vae")
    vae.encoder.forward = my_vae_encoder_fwd.__get__(vae.encoder, vae.encoder.__class__)
    vae.decoder.forward = my_vae_decoder_fwd.__get__(vae.decoder, vae.decoder.__class__)
    vae.requires_grad_(True)
    vae.train()
    # add the skip connection convs
    vae.decoder.skip_conv_1 = torch.nn.Conv2d(512, 512, kernel_size=(3, 3), stride=(1, 1), padding=1,
                                              bias=True).cuda().requires_grad_(True)
    vae.decoder.skip_conv_2 = torch.nn.Conv2d(256, 512, kernel_size=(3, 3), stride=(1, 1), padding=1,
                                              bias=True).cuda().requires_grad_(True)
    vae.decoder.skip_conv_3 = torch.nn.Conv2d(128, 512, kernel_size=(3, 3), stride=(1, 1), padding=1,
                                              bias=True).cuda().requires_grad_(True)
    vae.decoder.skip_conv_4 = torch.nn.Conv2d(128, 256, kernel_size=(3, 3), stride=(1, 1), padding=1,
                                              bias=True).cuda().requires_grad_(True)
    torch.nn.init.constant_(vae.decoder.skip_conv_1.weight, 1e-5)
    torch.nn.init.constant_(vae.decoder.skip_conv_2.weight, 1e-5)
    torch.nn.init.constant_(vae.decoder.skip_conv_3.weight, 1e-5)
    torch.nn.init.constant_(vae.decoder.skip_conv_4.weight, 1e-5)
    vae.decoder.ignore_skip = False
    vae.decoder.gamma = 1

    return vae


class VINE_Turbo(torch.nn.Module, PyTorchModelHubMixin):
    def __init__(self, device='cpu'):
        super().__init__()
        tokenizer = AutoTokenizer.from_pretrained("stabilityai/sd-turbo", subfolder="tokenizer", use_fast=False, )
        text_encoder = CLIPTextModel.from_pretrained("stabilityai/sd-turbo", subfolder="text_encoder")
        text_encoder.requires_grad_(False)
        text_encoder.to(device)

        fixed_a2b_tokens = tokenizer("", max_length=tokenizer.model_max_length, padding="max_length", truncation=True,
                                     return_tensors="pt").input_ids[0]
        self.fixed_a2b_emb_base = text_encoder(fixed_a2b_tokens.unsqueeze(0).to(device))[0].detach()
        del text_encoder, tokenizer, fixed_a2b_tokens  # free up some memory
        gc.collect()
        torch.cuda.empty_cache()

        self.sec_encoder = ConditionAdaptor()
        self.unet = initialize_unet_no_lora()
        self.vae_a2b = initialize_vae_no_lora()
        self.vae_enc = VAE_encode(self.vae_a2b)
        self.vae_dec = VAE_decode(self.vae_a2b)
        self.sched = make_1step_sched(device)
        self.timesteps = torch.tensor([self.sched.config.num_train_timesteps - 1] * 1, device=device).long()

    def forward(self, x, secret=None, timesteps=None):
        if timesteps == None:
            timesteps = self.timesteps
        B = x.shape[0]
        x_sec = self.sec_encoder(secret, x)
        x_enc = self.vae_enc(x_sec, direction="a2b").to(x.dtype)
        model_pred = self.unet(x_enc, timesteps, encoder_hidden_states=self.fixed_a2b_emb_base, ).sample.to(x.dtype)
        x_out = torch.stack(
            [self.sched.step(model_pred[i], timesteps[i], x_enc[i], return_dict=True).prev_sample for i in range(B)])
        x_out_decoded = self.vae_dec(x_out, direction="a2b").to(x.dtype)
        return x_out_decoded


class VINE(BaseWatermarkModel):
    """
    Wrapper for VINE (R/B) PyTorch models.
    Supports embedding and extraction of watermarks using separate PyTorch models.
    Supports two model variants: R (Robust), B (Base).

    Reference:
        Robust Watermarking Using Generative Priors Against Image Editing: From Benchmarking to Advances
        Shilin Lu, Zihan Zhou, Jiayou Lu, Yuanzhi Zhu, and Adams Wai-Kin Kong
        ICLR 2025
    """

    def __init__(self, img_size: int = 256, bits_len: int = 100, model_type: str = 'R', device: str = "cuda",
                 local_files_only: bool = False):
        """
        Initialize the VINE model.

        Args:
            img_size (int): Input image size for the encoder (256 for R/B).
            bits_len (int): Length of watermark (must be 100 for R/B).
            model_type (str): Model variant ('R' or 'B').
            device (str): Device to run on ('cpu' or 'cuda').
            local_files_only (bool): If True, avoid downloading the model. Requires model to be present locally.
        """
        model_type = model_type.upper()
        if model_type not in ['R', 'B']:
            raise ValueError(f"model_type must be 'R' or 'B', got {model_type}")

        modelname = f"VINE-{model_type}"
        # Call the parent class constructor
        super().__init__(bits_len, img_size, modelname)

        self.local_files_only = local_files_only
        self.model_type = model_type
        self.device = torch.device(device if torch.cuda.is_available() or device != "cuda" else "cpu")
        set_seed(42)  # For reproducibility if needed by underlying models

        # --- Model Loading ---
        try:
            repo_id_enc = f"Shilin-LU/VINE-{model_type}-Enc"
            logger.info(f"Loading {self.modelname} encoder from '{repo_id_enc}'...")
            self.encoder = VINE_Turbo.from_pretrained(repo_id_enc, local_files_only=self.local_files_only)
            self.encoder.to(self.device).eval()
            logger.info(f"{self.modelname} encoder loaded.")

            repo_id_dec = f"Shilin-LU/VINE-{model_type}-Dec"
            logger.info(f"Loading {self.modelname} decoder from '{repo_id_dec}'...")
            self.decoder = CustomConvNeXt.from_pretrained(repo_id_dec, local_files_only=self.local_files_only)
            self.decoder.to(self.device).eval()
            logger.info(f"{self.modelname} decoder loaded.")

        except Exception as e:
            raise RuntimeError(f"Failed to load VINE models: {e}") from e
        # --- End of Model Loading ---

        # Define preprocessing transform for encoder input (256x256)
        self.transform_256 = transforms.Compose([
            transforms.Resize((256, 256), interpolation=transforms.InterpolationMode.BICUBIC),
            transforms.ToTensor()
        ])

    @torch.inference_mode()
    def embed(self, cover_list: List[ndarray], secrets: List[List[int]]) -> Result:
        """
        Embed 100-bit watermarks into cover images one by one (to avoid batch size issues).

        Args:
            cover_list (List[ndarray]): List of RGB images [H, W, 3], uint8 [0, 255] or float.
            secrets (List[List[int]]): List of 100-bit binary watermarks.

        Returns:
            Result: Watermarked images and embedded bits.
        """
        if len(cover_list) != len(secrets):
            raise ValueError("Number of cover images must match number of secrets.")
        stego_list = []
        # Process images one by one
        for i, (cover_img, secret_bits) in enumerate(zip(cover_list, secrets)):
            cover_img_uint8 = np.clip(cover_img, 0, 255).astype(np.uint8)
            pil_img = Image.fromarray(cover_img_uint8)
            resized_tensor = self.transform_256(pil_img).unsqueeze(0).to(self.device)  # [1, 3, 256, 256]
            cover_normalized = resized_tensor * 2.0 - 1.0  # [-1, 1]
            # 2. Prepare single secret tensor
            secret_tensor = torch.tensor(secret_bits, dtype=torch.float32).unsqueeze(0).to(self.device)  # [1, 100]
            # --- Single Image Encoding ---
            encoded_img = self.encoder(cover_normalized, secret_tensor)  # [1, 3, 256, 256]
            # The model outputs the watermarked image directly (normalized [-1, 1])
            # Convert back to [0, 255] uint8 HWC
            stego_np = encoded_img.squeeze(0).cpu().numpy()  # [3, 256, 256]
            stego_np = np.clip((stego_np + 1.0) * 127.5, 0, 255).astype(np.uint8)  # [0, 255]
            stego_img = np.transpose(stego_np, (1, 2, 0))  # [256, 256, 3]
            stego_list.append(stego_img)
        return Result(stego_img=stego_list, emb_bits=secrets)


    @torch.inference_mode()
    def extract(self, stego_list: List[ndarray]) -> Result:
        """
        Extract 100-bit watermarks from stego images in batch (assumes images are 256x256).

        Args:
            stego_list (List[ndarray]): Watermarked images [H, W, 3], uint8 [0, 255]. Expected to be 256x256.

        Returns:
            Result: Extracted binary watermarks.
        """
        batch_size = len(stego_list)

        # 1. Preprocess stego images: Check size, convert to tensor, normalize
        processed_tensors = []
        for i, stego_img in enumerate(stego_list):
            # Ensure the image is 256x256
            stego_img = np.float32(Image.fromarray(stego_img.astype(np.uint8)).resize((256, 256), Image.BICUBIC))
            stego_tensor = torch.from_numpy(stego_img).float().permute(2, 0, 1) / 255.0  # [3, 256, 256]
            stego_tensor_normalized = stego_tensor * 2.0 - 1.0  # [-1, 1]
            processed_tensors.append(stego_tensor_normalized)

        # Stack tensors to form a batch
        stego_batch_tensor = torch.stack(processed_tensors).to(self.device)  # [B, 3, 256, 256]

        # --- Batch Decoding ---
        decoded_bits_batch = self.decoder(stego_batch_tensor)  # Output shape depends on decoder, e.g., [B, 100]
        decoded_bits_batch = torch.round(decoded_bits_batch)  # [B, 100]
        # Convert probabilities to binary bits
        extracted_bits_batch = (decoded_bits_batch > 0.5).cpu().detach().numpy().astype(int)  # [B, 100]
        # Convert batch back to list of lists
        extracted_bits_list = [extracted_bits_batch[i].tolist() for i in range(batch_size)]
        return Result(ext_bits=extracted_bits_list)

    # Note: The provided VINE code snippet does not include a 'recover' or 'remover' model.
    # Therefore, the `recover` method raises NotImplementedError.
    def recover(self, stego_list: List[ndarray]) -> Result:
        """
        Recover original images from watermarked images.
        Note: VINE-R/B models as provided do not include a recovery/remover component.
        This method is not implemented.
        """
        raise NotImplementedError(f"{self.modelname} does not support image recovery.")
