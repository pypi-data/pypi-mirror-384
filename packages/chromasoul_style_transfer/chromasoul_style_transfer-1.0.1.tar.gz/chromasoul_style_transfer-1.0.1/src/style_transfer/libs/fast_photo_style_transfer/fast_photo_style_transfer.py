#!/usr/bin/env python
# -*- coding: utf-8 -*-

from style_transfer.libs.base_transfer import BaseTransfer
from style_transfer.utils.downloader import downloader
from style_transfer.libs.fast_photo_style_transfer.photo_wct import PhotoWCT
from style_transfer.libs.fast_photo_style_transfer.gif_smoothing import GIFSmoothing
import torch
import torchvision.transforms as transforms
import torchvision.utils as utils
import numpy as np
import cv2


def memory_limit_image_resize(img: np.ndarray) -> np.ndarray:
    """prevent too small or too big images
    img: Image array with BGR format.
    """
    MINSIZE = 256
    MAXSIZE = 960

    img_array = img

    orig_height, orig_width = img_array.shape[:2]

    if max(orig_width, orig_height) < MINSIZE:
        if orig_width > orig_height:
            new_width = int(orig_width * 1.0 / orig_height * MINSIZE)
            new_height = MINSIZE
        else:
            new_width = MINSIZE
            new_height = int(orig_height * 1.0 / orig_width * MINSIZE)
        img_array = cv2.resize(
            img_array, (new_width, new_height), interpolation=cv2.INTER_CUBIC
        )

    current_height, current_width = img_array.shape[:2]

    if min(current_width, current_height) > MAXSIZE:
        if current_width > current_height:
            new_width = MAXSIZE
            new_height = int(current_height * 1.0 / current_width * MAXSIZE)
        else:
            new_width = int(current_width * 1.0 / current_height * MAXSIZE)
            new_height = MAXSIZE
        img_array = cv2.resize(
            img_array, (new_width, new_height), interpolation=cv2.INTER_CUBIC
        )

    final_height, final_width = img_array.shape[:2]
    print(
        "Resize image: (%d,%d)->(%d,%d)"
        % (orig_width, orig_height, final_width, final_height)
    )

    return final_width, final_height, img_array


class FastPhotoStyleTransfer(BaseTransfer):
    """Transfer reference image's style to input image's style with FastPhotoStyle Algorithm."""

    def __init__(self):
        super().__init__()
        self.model_weights = "photo_wct.pth"
        model_weights_path = downloader.download_model(self.model_weights)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        p_wct = PhotoWCT()
        p_wct.load_state_dict(torch.load(model_weights_path))
        p_wct.to(self.device)
        self.p_wct = p_wct
        self.smooth_module = GIFSmoothing(r=35, eps=0.001)

    def extract(self, img_ref: np.ndarray):
        """Extract reference style.
        Args:
            img_ref: bgr numpy array of reference image.
        """
        try:
            _, _, img_ref = memory_limit_image_resize(img_ref)
            styl_img = img_ref[:, :, ::-1].copy()

            styl_img = transforms.ToTensor()(styl_img).unsqueeze(0)

            styl_img = styl_img.to(self.device)

            self.p_wct.extract_reference_feature(styl_img)
        except Exception as e:
            raise e

    def transfer(self, img: np.ndarray) -> np.ndarray:
        """Transfer the target image's style.
        Args:
            img: bgr numpy array of input image.
        Returns:
            img_tgt: bgr numpy array of target image.
        """
        cont_copy = img.copy()
        ch, cw = cont_copy.shape[:2]
        _, _, img = memory_limit_image_resize(img)

        cont_img = img[:, :, ::-1].copy()
        cont_img = transforms.ToTensor()(cont_img).unsqueeze(0)
        cont_img = cont_img.to(self.device)

        stylized_img = self.p_wct.transfer(cont_img)

        stylized_img: torch.Tensor = torch.nn.functional.interpolate(
            stylized_img, size=(ch, cw), mode="bilinear"
        )
        grid = utils.make_grid(stylized_img.data, nrow=1, padding=0)
        output_img = grid.mul(255).clamp(0, 255).byte().permute(1, 2, 0).cpu().numpy()
        output_img = output_img[:, :, ::-1]
        output_img = self.smooth_module.process(output_img, cont_copy)

        img_tgt = np.array(np.clip(output_img, 0, 255), dtype=np.uint8)
        return img_tgt
