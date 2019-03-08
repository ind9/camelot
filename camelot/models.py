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

    def is_header(self, columns):
        pass

    def convert_first_row_to_header(self, df):
        headers = df.iloc[0]
        return pd.DataFrame(df.values[1:], columns=headers)

    def create_df_html(self, df, header = False):
        # TODO: check whether the first row is the header before converting it to header,
        #  once implemented, change header=True in to_html
        # df = self.convert_first_row_to_header(df)
        if df.shape[0] > 0:
            str_io = io.StringIO()
            df = df.applymap(lambda x: x.replace('\n', ''))
            df.to_html(buf=str_io, index=False, header=header, classes='table')
            html_str = str_io.getvalue()
            return su.unescape(html_str)
        else:
            return ''

    @staticmethod
    def window(seq, n=2):
        it = iter(seq)
        result = tuple(islice(it, n))
        if len(result) == n:
            yield result
        for elem in it:
            result = result[1:] + (elem,)
            yield result

    def split_tables_vertically(self, df):
        dfs = []
        split_column_indices = [-1]
        for col in df.columns:
            if ''.join(df[col]) == '':
                split_column_indices.append(col)
        split_column_indices.append(len(df.columns))
        for index in self.window(split_column_indices):
            start = list(index)[0]
            end = list(index)[1]
            dfs.append(df.iloc[:, start + 1:end])
        return dfs

    # TODO: Replicate header across all sub tables if the first row is a header
    def split_tables_horizontally(self, df):
        headers = df.iloc[0]
        df = df.drop(df.index[0]).reset_index(drop=True)
        nr_of_cols = []
        for row in df.iterrows():
            index, data = row
            nr_of_cols.append(len(list(filter(lambda x: x != '', data))))

        split_rows_indices = [-1]

        for row in df.iterrows():
            index, data = row
            if len(list(filter(lambda x: x != '', data))) == 1:
                split_rows_indices.append(index)

        split_rows_indices.append(df.shape[0])

        dfs = []
        for index in self.window(split_rows_indices):
            start = list(index)[0]
            end = list(index)[1]
            if df.iloc[start:start + 1].shape[0] > 0:
                dfs.append(df.iloc[start:start + 1].iat[0, 0])
            dfs.append(pd.DataFrame(df.iloc[start + 1:end].values, columns=headers))

        return dfs

    def split_tables(self, data):
        dfs = []
        for i in self.split_tables_vertically(data):
            for j in self.split_tables_horizontally(i):
                dfs.append(j)
        return dfs

    @staticmethod
    def is_new_line(line, max_length):
        return len(line) > 0 and not line.startswith(' ') and line[0].isupper() and len(line) < max_length / 4

    def generate_paragraphs(self, data):
        lines = data.split('\n')
        sliding = list(self.window(lines, 2))
        data_list_with_length = map(lambda x: (len(x), x), lines)
        max_length = sorted(data_list_with_length, key=lambda x: -1 * x[0])[0][0]
        output = lines[0]
        for (i, j) in sliding:
            if (i.endswith('.') and (len(j) == 0 or j[0].isupper())) or j.startswith(u'\u2022')\
                    or self.is_new_line(i, max_length) or self.is_new_line(j, max_length):
                output = output + '\n' + j
            else:
                output = output + ' ' + j
        return output

    def to_html_util(self, data):
        html = ''
        if isinstance(data, pd.DataFrame):
            header = list(data.columns)
            # dict_output = [dict(zip(header, i)) for i in data.as_matrix(header)]
            data = pd.DataFrame(list(filter(lambda i: ''.join(map(lambda x: str(x), i)) != '', data.as_matrix(header))), columns=header)
            html = html + self.create_df_html(data, True)
        else:
            paragraphs = self.generate_paragraphs(data)
            for paragraph in paragraphs.split('\n'):
                html = html + '<p>' + paragraph + '</p>'
        return html

    def to_html(self):
        html = ''
        for i in self.output:
            if isinstance(i, pd.DataFrame):
                for df in self.split_tables(i):
                    html = html + self.to_html_util(df)
            else:
                html = html + self.to_html_util(i)
        return html
