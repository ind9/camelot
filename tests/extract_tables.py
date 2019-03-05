from camelot.cli import read_pdf

outputs = [
    read_pdf('files/sample_files/table1.pdf', pages='all', flavor='stream'),
    read_pdf('files/sample_files/table2.pdf', pages='all', **{'line_scale': 25 }),
    read_pdf('files/sample_files/table3.pdf', pages='1', flavor='stream',
             table_areas=["171.58060681818182,535.4643457792209,294.29658625541134,12.863536796536778"],
             layout_kwargs={'char_margin': 0.1}
             ),
    read_pdf('files/sample_files/table4.pdf', pages='all', flag_size=True, shift_text=[])
    ]

for output in outputs:
    print(output.to_html())
