## efficax

Simple tool for text extraction from pdf files and conversion 
to table format. This package features extraction from a defined
rectangle, start and end keywords for the extraction process as
well as automatic chapter identification by numbers. The result
is copied to the clipboard and a .csv file is saved to an output 
folder. Additionally a pdf with an overlay corresponding to the
extraction rectangle will be saved.


### Installation

```
pip install efficax
```


### Usage

```
from efficax import extract_text_with_overlay

extract_text_with_overlay(
    pdf_path="path/to/your/file.pdf,
    output_folder="folder/for/output",
    start_keyword="TITLE",
    end_keyword="The End",
    upper_border=0.2,
    lower_border=0.1,
    left_border=0.05,
    right_border=0.15
)
```
