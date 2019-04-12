import pandas as pd
from tabulate import tabulate
import io
from itertools import islice
from xml.sax import saxutils as su
import re
import json

pd.set_option('display.max_colwidth', -1)


class Output(object):
    def __init__(self, jurisdiction, tax_type, tax_rate, effective_date):
        self.jurisdiction = jurisdiction
        self.tax_type = tax_type
        self.tax_rate = tax_rate
        self.effective_date = effective_date


class Result(object):
    def __init__(self, output):
        self.output = output
        mapping = {
            'jurisdiction': 'county|city|municipality|district|spd|boundaries',
            'taxrate': 'rate'
        }
        self.regexes = {}
        for r in mapping:
            self.regexes[r] = re.compile(mapping[r])
        pass

    def __str__(self):
        result = ''
        for i in self.output:
            if isinstance(i, pd.DataFrame):
                result = result + '\n' + tabulate(i)
            else:
                result = result + '\n' + i
        return result

    def regex_entity(self, value, regexes):
        found = False
        for r in regexes:
            match = regexes[r].findall(str(value).lower())
            if (len(match) > 0):
                found = True
                ans = r
        if found:
            return ans
        else:
            return ''

    def is_header(self, columns):
        columns = list(map(lambda x: ' '.join(str(x).replace('\n', '<br>').split()), columns))
        c = 0
        for j in columns:
            if (self.regex_entity(j, self.regexes) != ''):
                c = c + 1
        if(c >= 2):
            return True
        return False

    def header(self, columns):
        columns = list(map(lambda x: ' '.join(str(x).replace('\n', '<br>').split()), columns))
        return list(map(lambda j: (j, self.regex_entity(j, self.regexes)), columns))

    def convert_first_row_to_header(self, df):
        if(df.shape[0] > 0):
            headers = df.iloc[0]
            return pd.DataFrame(df.values[1:], columns=headers)
        return df

    def create_df_html(self, df, header):
        # TODO: check whether the first row is the header before converting it to header,
        #  once implemented, change header=True in to_html
        # df = self.convert_first_row_to_header(df)
        if df.shape[0] > 0:
            str_io = io.StringIO()
            df = df.applymap(lambda x: str(x).replace('\n', '<br>'))
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
        top_header = df.iloc[0]

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
            data = df.iloc[start + 1:end].values

            if(len(data) == 0):
                pass
            else:
                data_df = pd.DataFrame(data)

                data_df = data_df.dropna(axis=1, how='all')

                df_values = data_df.values
                new_df = []
                for i in df_values:
                    new_row = []
                    for j in i:
                        if j == '':
                            j = float('nan')
                        new_row.append(j)
                    new_df.append(new_row)

                data_df = pd.DataFrame(new_df).dropna(axis=1, how='all')

                first_row = list(data_df.iloc[0])
                if self.is_header(first_row) and len(list(filter(lambda x: x == '', list(first_row)))) == 0:
                    headers = data_df.iloc[0]
                elif self.is_header(top_header):
                    headers = top_header
                else:
                    headers = None

                if headers is None or len(list(filter(lambda x: x != '', list(headers)))) != data_df.shape[1]:
                    dfs.append(data_df)
                else:
                    data_df.columns = headers
                    dfs.append(data_df.iloc[1:])
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
                    or self.is_new_line(i, max_length) or self.is_new_line(j, max_length) or j[0].isupper():
                output = output + '\n' + j
            else:
                output = output + ' ' + j
        return output

    def to_html_util(self, data):
        html = ''
        if isinstance(data, pd.DataFrame):
            header = list(data.columns)
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

    def to_json(self):
        output = []
        for i in self.output:
            if isinstance(i, pd.DataFrame):
                for df in self.split_tables(i):
                    if isinstance(df, pd.DataFrame):
                        header = list(df.columns)
                        std_headers = self.header(header)
                        entity_headers = list(map(lambda y: y[0], (filter(lambda x: x[1] != '', std_headers))))
                        new_columns = list(map(lambda y: y[1] + '(' + y[0] + ')', (filter(lambda x: x[1] != '', std_headers))))
                        if(len(entity_headers) > 0):
                            new_df = df[entity_headers]
                            new_df.columns = new_columns
                            output.extend(new_df.to_dict('records'))
        return json.dumps(output)
