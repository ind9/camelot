from camelot.cli import read_pdf

outputs = [
    read_pdf('files/sample_files/table2.pdf', pages='all', **{'line_scale': 25}),
    # read_pdf('files/sample_files/table4.pdf', pages='1', flag_size=True, shift_text=[]),
    # read_pdf('files/sample_files/table5.pdf', pages='1', **{'line_scale': 25}),
    # read_pdf('files/sample_files/table6.pdf', pages='1,2', **{'line_scale': 25}),
    # read_pdf('files/sample_files/table9.pdf', pages='1', **{'line_scale': 10}),
    # read_pdf('files/sample_files/table10.pdf', pages='1', **{'line_scale': 10}),
    ]

for output in outputs:
    # output.to_html()
    print(output.to_html())
    print("<br><br><br><br><br>-----------<br><br><br><br><br>")
