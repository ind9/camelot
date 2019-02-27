import pandas as pd
from tabulate import tabulate


class Result(object):
    def __init__(self, output):
        self.output = output
        pass

    def __str__(self):
        result = ''
        for i in self.output:
            if (isinstance(i, pd.DataFrame)):
                result = result + '\n' + tabulate(i)
            else:
                result = result + '\n' + i
        return result

    def to_html(self):
        pass
