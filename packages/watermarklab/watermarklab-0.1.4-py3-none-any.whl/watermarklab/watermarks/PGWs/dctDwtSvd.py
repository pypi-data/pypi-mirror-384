# Copyright (c) 2025 Jiale Chen <chenoly@outlook.com>. All rights reserved.
# SPDX-License-Identifier: MIT
import cv2
import pywt
import numpy as np
from numpy import ndarray
from typing import List, Any
from watermarklab.utils.basemodel import BaseWatermarkModel, Result

__all__ = ["dctDwtSvd"]


class EmbedDwtDctSvd(object):
    def __init__(self, watermarks=[], wmLen=8, scales=[0, 36, 36], block=4):
        self._watermarks = watermarks
        self._wmLen = wmLen
        self._scales = scales
        self._block = block

    def encode(self, bgr):
        (row, col, channels) = bgr.shape

        yuv = cv2.cvtColor(bgr, cv2.COLOR_BGR2YUV)

        for channel in range(2):
            if self._scales[channel] <= 0:
                continue

            ca1, (h1, v1, d1) = pywt.dwt2(yuv[:row // 4 * 4, :col // 4 * 4, channel], 'haar')
            self.encode_frame(ca1, self._scales[channel])

            yuv[:row // 4 * 4, :col // 4 * 4, channel] = pywt.idwt2((ca1, (v1, h1, d1)), 'haar')

        bgr_encoded = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
        return bgr_encoded

    def decode(self, bgr):
        (row, col, channels) = bgr.shape

        yuv = cv2.cvtColor(bgr, cv2.COLOR_BGR2YUV)

        scores = [[] for i in range(self._wmLen)]
        for channel in range(2):
            if self._scales[channel] <= 0:
                continue

            ca1, (h1, v1, d1) = pywt.dwt2(yuv[:row // 4 * 4, :col // 4 * 4, channel], 'haar')

            scores = self.decode_frame(ca1, self._scales[channel], scores)

        avgScores = list(map(lambda l: np.array(l).mean(), scores))

        bits = (np.array(avgScores) * 255 > 127).astype(int).tolist()
        return bits

    def decode_frame(self, frame, scale, scores):
        (row, col) = frame.shape
        num = 0

        for i in range(row // self._block):
            for j in range(col // self._block):
                block = frame[i * self._block: i * self._block + self._block,
                        j * self._block: j * self._block + self._block]

                score = self.infer_dct_svd(block, scale)
                wmBit = num % self._wmLen
                scores[wmBit].append(score)
                num = num + 1

        return scores

    def diffuse_dct_svd(self, block, wmBit, scale):
        u, s, v = np.linalg.svd(cv2.dct(block))

        s[0] = (s[0] // scale + 0.25 + 0.5 * wmBit) * scale
        return cv2.idct(np.dot(u, np.dot(np.diag(s), v)))

    def infer_dct_svd(self, block, scale):
        u, s, v = np.linalg.svd(cv2.dct(block))

        score = 0
        score = int((s[0] % scale) > scale * 0.5)
        return score
        if score >= 0.5:
            return 1.0
        else:
            return 0.0

    def encode_frame(self, frame, scale):
        '''
        frame is a matrix (M, N)

        we get K (watermark bits size) blocks (self._block x self._block)

        For i-th block, we encode watermark[i] bit into it
        '''
        (row, col) = frame.shape
        num = 0
        for i in range(row // self._block):
            for j in range(col // self._block):
                block = frame[i * self._block: i * self._block + self._block,
                        j * self._block: j * self._block + self._block]
                wmBit = self._watermarks[(num % self._wmLen)]

                diffusedBlock = self.diffuse_dct_svd(block, wmBit, scale)
                frame[i * self._block: i * self._block + self._block,
                j * self._block: j * self._block + self._block] = diffusedBlock

                num = num + 1


RED = "\033[91m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"


class dctDwtSvd(BaseWatermarkModel):
    """
    The DWT-DCT-SVD watermarking algorithm.

    Reference:
        Ingemar Cox, Matthew Miller, Jeffrey Bloom, Jessica Fridrich, and Ton Kalker. Digital watermarking and steganography. Morgan kaufmann, 2007.
    """

    def __init__(self, bits_len: int, img_size: int, modelname: str = "dctDwtSvd", scales=[0, 36, 36]):
        """
        Initialize the model.

        Args:
            bits_len (int): Length of the watermark.
            img_size (int): Expected image size (not used in this method).
            modelname (str): Name of the model.
            scales (List[float]): Embedding strengths for Y, U, V channels.
        """
        super().__init__(bits_len, img_size, modelname)
        self.bits_len = bits_len
        self.scales = scales
        self.model = EmbedDwtDctSvd(watermarks=[], wmLen=bits_len, scales=scales, block=4)

        print(f"[{GREEN}WatermarkLab{RESET} INFO] dctDwt is already!")

    def embed(self, cover_list: List[Any], secrets: List[List]) -> Result:
        """
        Embed watermarks into a batch of cover images.

        Args:
            cover_list (List[np.ndarray]): List of RGB images.
            secrets (List[List]): List of binary watermarks (each length = bits_len).

        Returns:
            Result: Contains the list of watermarked RGB images.
        """
        stego_list = []
        for cover, secret in zip(cover_list, secrets):
            cover = cover.astype(np.uint8)
            self.model = EmbedDwtDctSvd(watermarks=secret, wmLen=len(secret), scales=self.scales, block=4)
            bgr = cv2.cvtColor(cover, cv2.COLOR_RGB2BGR)
            stego = self.model.encode(bgr)
            stego_rgb = cv2.cvtColor(stego, cv2.COLOR_BGR2RGB)
            stego_list.append(stego_rgb)
        return Result(stego_img=stego_list, emb_bits=secrets)

    def extract(self, stego_list: List[ndarray]) -> Result:
        """
        Extract watermarks from a batch of watermarked images.

        Args:
            stego_list (List[np.ndarray]): List of watermarked RGB images.

        Returns:
            Result: Contains the list of extracted binary watermarks.
        """
        ext_secret_list = []
        for stego in stego_list:
            stego = stego.astype(np.uint8)
            stego = cv2.cvtColor(stego, cv2.COLOR_RGB2BGR)
            ext_secret = self.model.decode(stego)
            ext_secret_list.append(ext_secret)
        result = Result(ext_bits=ext_secret_list)
        return result

    def recover(self, stego_list: List[ndarray]) -> Result:
        """
        Recover the original image from the watermarked image.
        Not supported in this method.

        Args:
            stego_list (List[np.ndarray]): Watermarked images.

        Returns:
            Result: NotImplemented.
        """
        pass
