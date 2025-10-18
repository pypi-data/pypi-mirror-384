#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import requests
from tqdm import tqdm
import appdirs


class Downloader:
    def __init__(self, cache_dir=appdirs.user_cache_dir("chromasoul")):
        self.cache_dir = cache_dir
        self.model_path = os.path.join(self.cache_dir, "model")

    def _get_download_url(self, filename, tag="latest"):
        if tag == "latest":
            return f"https://github.com/XIAODUOLU/ChromaSoul/releases/latest/download/{filename}"
        else:
            return f"https://github.com/XIAODUOLU/ChromaSoul/releases/download/{tag}/{filename}"

    def _download(self, url, path):
        """download the model with streaming"""

        response = requests.get(url, stream=True)
        response.raise_for_status()

        # get the total size
        total_size = int(response.headers.get("content-length", 0))

        with open(path, "wb") as f, tqdm(
            desc=f"Downloading the model...",
            total=total_size,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                size = f.write(chunk)
                pbar.update(size)

    def download_model(self, filename, tag="latest", force_download=False):
        """Download the model weights"""
        os.makedirs(self.model_path, exist_ok=True)
        filepath = os.path.join(self.model_path, filename)

        # download if force download or file not exists.
        if force_download or not os.path.exists(filepath):
            download_url = self._get_download_url(filename, tag)
            print(f"Downloading model from: {download_url}")
            self._download(download_url, filepath)

        return filepath


# singleton
downloader = Downloader()
