import pandas as pd
from tabulate import tabulate
import io
from itertools import islice
from xml.sax import saxutils as su

pd.set_option('display.max_colwidth', -1)


class Result(object):
    def __init__(self, output):
        self.output = output
        pass

    def __str__(self):
        result = ''
        for i in self.output:
            if isinstance(i, pd.DataFrame):
                result = result + '\n' + tabulate(i)
            else:
                result = result + '\n' + i
        return result

    def convert_first_row_to_header(self, df):
        headers = df.iloc[0]
        return pd.DataFrame(df.values[1:], columns=headers)

    def create_df_html(self, df):
        # TODO check whether the first row is the header before converting it to header, once implemented, change header=True in to_html
        # df = self.convert_first_row_to_header(df)
        str_io = io.StringIO()
        df = df.applymap(lambda x: x.replace("\n", '<br>'))
        df.to_html(buf=str_io, index=False, header=False, classes='table')
        html_str = str_io.getvalue()
        return su.unescape(html_str)

    def window(self, seq, n=2):
        it = iter(seq)
        result = tuple(islice(it, n))
        if len(result) == n:
            yield result
        for elem in it:
            result = result[1:] + (elem,)
            yield result

    def split_tables(self, df):
        dfs = []
        split_column_indices = [-1]
        for col in df.columns:
            if ''.join(df[col]) == '':
                split_column_indices.append(col)
        split_column_indices.append(len(df.columns))
        for index in self.window(split_column_indices):
            start = list(index)[0]
            end = list(index)[1]
            dfs.append(df.iloc[:, start+1:end])
        return dfs

    def to_html(self):
        html = ''
        for i in self.output:
            if isinstance(i, pd.DataFrame):
                for df in self.split_tables(i):
                    html = html + self.create_df_html(df)
            else:
                lines = i.split('\n')
                for line in lines:
                    html = html + '<p>' + line + '</p>'
        return html
