"""
Phenomenal script for automatic text extraction from pdf
"""

import os
from pathlib import Path
import pymupdf
import pandas as pd
import re


def extract_text_with_overlay(
        pdf_path:str,
        output_folder:str,
        start_keyword:str,
        end_keyword:str,
        upper_border:float = 0.0,
        lower_border:float = 0.0,
        left_border:float = 0.0,
        right_border:float = 0.0
) -> None:

    """
    Function for automatic text extraction from pdf

    :param pdf_path: path to pdf file
    :param output_folder: output path str without extension
    :param start_keyword: keyword to start extraction
    :param end_keyword: keyword to end extraction
    :param upper_border: upper border of text as fraction of page height
    :param lower_border: lower border of text as fraction of page height
    :param left_border: left border of text as fraction of page width
    :param right_border: right border of text as fraction of page width
    :return: None
    """

    # get file name
    name = Path(pdf_path).stem

    # create output folder and define file names
    os.makedirs(output_folder, exist_ok=True)
    output_pdf = f"{output_folder}/{name}_overlay.pdf"
    output_csv = f"{output_folder}/{name}.csv"

    # variables for text extraction
    text_out = []
    start_flag, end_flag = False, False

    # open pdf with pymupdf
    with pymupdf.open(pdf_path) as doc:
        for page in doc:

            # page dimensions
            page_height = page.rect.height
            page_width = page.rect.width

            # text area to extract
            x0, x1 = left_border * page_width, (1 - right_border) * page_width
            y0, y1 = upper_border * page_height, (1 - lower_border) * page_height
            rect = [x0, y0, x1, y1]

            # draw overlay
            overlay = page.new_shape()
            overlay.draw_rect(rect)
            overlay.finish(color=(1, 0, 0), fill=(1, 0, 0), fill_opacity=0.3, width=2)
            overlay.commit()

            # get text blocks
            blocks = page.get_text("blocks", clip=rect)

            # iterate through blocks and filter by start and end keyword
            for b in blocks:
                x0, y0, x1, y1, text, *_ = b

                if end_keyword in text:
                    end_flag = True
                    break

                if start_keyword in text:
                    start_flag = True

                if start_flag:
                    text_out.append(text)

            if end_flag: break

        # save pdf with overlay
        doc.save(output_pdf)

    # join text blocks
    text_out = "\n".join(text_out)

    # split into chapters
    chapters = re.split(r'\b(?=\d+\s)', text_out)

    # create DataFrame and copy to clipboard
    df = pd.DataFrame(data=chapters, columns=["Text"])
    df.to_csv(output_csv, index=False)
    df.to_clipboard(index=False, sep="\t")

    print("\n✅ Table successfully copied to clipboard. Copy into google "
          "sheets and copy the resulting table to google docs.")