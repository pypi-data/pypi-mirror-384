import argparse
import os
import sys
import time
from multiprocessing import Manager, Pool, Process

import cv2
import numpy as np
import pymupdf

from qrgrader.code import Code
from qrgrader.code_set import CodeSet, PageCodeSet
from qrgrader.utils import pix2np, get_patches, threshold, get_codes, compute_similarity_transform, \
    get_similarity_transform


class PageProcessor(Process):

    def __init__(self, semaphore, filename, index, generated, result, **kwargs):
        super().__init__()
        self.filename = filename
        self.index = index
        self.generated = generated
        self.result = result
        self.semaphore = semaphore

        self.dpi = kwargs.get("dpi", 400)
        self.thresholds = kwargs.get("thresholds", [50, 55, 60, 65, 70, 75, 80])
        self.matrix = pymupdf.Matrix(self.dpi / 72, self.dpi / 72)
        self.show_patches = kwargs.get("show_patches", False)
        self.resize = kwargs.get("resize", 1.0)
        self.dir_images = kwargs.get("dir_images", "../..")

        self.ppm = self.dpi / 25.4

    def run(self):

        # Render the image
        doc = pymupdf.open(self.filename)
        page = doc[self.index]
        image = pix2np(page.get_pixmap(matrix=self.matrix))  # noqa
        doc.close()

        # Find page, orientation and rotate page
        rotation = None
        detected = PageCodeSet()
        h, w = image.shape[:2]

        for th in self.thresholds:

            ne = threshold(image[0:500, w - 500:w], th)
            for text, cx, cy, cw, ch in get_codes(ne):
                if text.startswith("P"):
                    rotation = -1
                elif text.startswith("Q"):
                    rotation = cv2.ROTATE_180
                detected.append(Code(text, cx, cy, cw, ch))

            if rotation is None:
                nw = threshold(image[0:500, 0:500], th)
                for text, cx, cy, cw, ch in get_codes(nw):
                    if text.startswith("P"):
                        rotation = cv2.ROTATE_90_CLOCKWISE
                    elif text.startswith("Q"):
                        rotation = cv2.ROTATE_90_COUNTERCLOCKWISE
                    detected.append(Code(text, cx, cy, cw, ch))

            if rotation is None:
                sw = threshold(image[h - 500:h, 0:500], th)
                for text, cx, cy, cw, ch in get_codes(sw):
                    if text.startswith("P"):
                        rotation = cv2.ROTATE_180
                    elif text.startswith("Q"):
                        rotation = -1
                    detected.append(Code(text, cx, cy, cw, ch))

            if rotation is None:
                se = threshold(image[h - 500:h, w - 500:w], th)
                for text, cx, cy, cw, ch in get_codes(se):
                    if text.startswith("P"):
                        rotation = cv2.ROTATE_90_COUNTERCLOCKWISE
                    elif text.startswith("Q"):
                        rotation = cv2.ROTATE_90_CLOCKWISE
                    detected.append(Code(text, cx, cy, cw, ch))

            if rotation is not None:
                break

        if rotation is not None and rotation != -1:
            image = cv2.rotate(image, rotation)

        # Get the page number if we got it
        page = detected.get_page() if detected.get_page() is not None else 0

        # Clear the detected because the
        # page may have been rotated
        detected.clear()

        # Process the page and extract the detected
        for th in self.thresholds:
            th_image = threshold(image, th)
            patches = get_patches(th_image, self.ppm, 8)

            for px, py, pw, ph in patches:
                patch = image[py:py + ph, px:px + pw]

                if self.show_patches:
                    cv2.rectangle(image, (px, py), (px + pw, py + ph), (0, 0, 255), 1)

                for text, cx, cy, cw, ch in get_codes(patch):
                    detected.append(Code(text, px + cx, py + cy, cw, ch, page, self.index))

        # Try again with the whole page
        page = detected.get_page()
        exam = detected.get_exam_id()

        # If we did not find the page number, try to find it in the generated detected
        if page is None:
            for code in detected:
                code = self.generated.get(code)
                if code := self.generated.get(code):
                    page = code.get_page()
                    exam = code.get_exam_id()
                    break
            for code in detected:
                code.set_page(page)

        if self.resize != 1.0:
            image = cv2.resize(image, (int(image.shape[1] * self.resize), int(image.shape[0] * self.resize)),
                               interpolation=cv2.INTER_AREA)

        if detected.get_page() is not None:
            cv2.imwrite(self.dir_images + os.sep + "page-{}-{}-{:03d}.jpg".format(detected.get_date(), detected.get_exam_id(), detected.get_page()), image)
        elif detected.get_exam_id():
            cv2.imwrite(self.dir_images + os.sep + "page-{}-{}-{:03d}.jpg".format(detected.get_date(), detected.get_exam_id(), 0), image)
        else:
            cv2.imwrite(self.dir_images + os.sep + "{}-{:03d}.jpg".format(self.filename, self.index), image)

        # # Compute the transformation
        generated_page_codeset = PageCodeSet(self.generated.select(exam=exam, page=page))

        # Compute the transformation
        if detected.get_p() is not None and detected.get_q() is not None:
            p11 = generated_page_codeset.get_p().get_pos()
            p12 = generated_page_codeset.get_q().get_pos()
            p21 = detected.get_p().get_pos()
            p22 = detected.get_q().get_pos()
            #scale, rot, delta = compute_similarity_transform(p21, p22, p11, p12)
            transform = get_similarity_transform([p11, p12], [p21, p22]) # noqa
        elif detected.get_p() is not None:
            x1, y1 = detected.get_p().get_pos()
            x2, y2 = generated_page_codeset.get_p().get_pos()
            transform = lambda pt: (pt[0] + x2 - x1, pt[1] + y2 - y1) # noqa
        elif detected.get_q() is not None:
            x1, y1 = detected.get_q().get_pos()
            x2, y2 = generated_page_codeset.get_q().get_pos()
            transform = lambda pt: (pt[0] + x2 - x1, pt[1] + y2 - y1) # noqa
        else:
            transform = lambda pt: (pt[0], pt[1]) # noqa # No transformation needed

        for code in generated_page_codeset:

            new_pose = transform(code.get_pos())
            code.set_pos(new_pose)  # Note: OpenCV uses (y, x) order
            code.set_size(120, 120)
            code.scale(72.0 / self.dpi)
            code.set_marked(detected.get(code) is None)
            self.result.append(code)

        #print(f"Processed {os.path.basename(self.filename)} page {self.index} ({len(generated_page_codeset)} codes detected)")
        self.semaphore.release()
