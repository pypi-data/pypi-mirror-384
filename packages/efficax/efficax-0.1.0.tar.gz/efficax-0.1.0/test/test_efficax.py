from src.efficax.main import extract_text_with_overlay

#----------------------------------------------------------#

input:str = "input/Cicero_De_finibus_Liber_tertius.pdf"
output:str = "output"

upper_border = 0.1
lower_border = 0.1
left_border = 0.1
right_border = 0.3

start_keyword = "LIBER"
end_keyword = "NOTES"

#----------------------------------------------------------#

extract_text_with_overlay(
    pdf_path=input,
    output_folder=output,
    start_keyword=start_keyword,
    end_keyword=end_keyword,
    upper_border=upper_border,
    lower_border=lower_border,
    left_border=left_border,
    right_border=right_border
)