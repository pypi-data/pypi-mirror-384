#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cv2.ximgproc import guidedFilter


class GIFSmoothing:

    def __init__(self, r, eps):
        super(GIFSmoothing, self).__init__()
        self.r = r
        self.eps = eps

    def process(self, initImg, contentImg):
        """
        :param initImg: intermediate output
        :param contentImg: content image output
        :return: stylized output image
        """
        output_img = guidedFilter(
            guide=contentImg, src=initImg, radius=self.r, eps=self.eps
        )

        return output_img
