import unittest
import pandas as pd
import pandas.testing as pd_testing

from tabletools import table_group_summarize


class TestGroupSummarize(unittest.TestCase):
    def test_parser(self):
        parser = table_group_summarize.parse_args(
                ['--table', 'foo',
                 '--groupby', 'foo', 'bar',
                 '--summarize', 'col1', 'col2',
                 '--func', 'mean', 'median'])
        self.assertEqual(parser.table, 'foo')
        self.assertEqual(parser.groupby, ['foo', 'bar'])
        self.assertEqual(parser.summarize, ['col1', 'col2'])
        self.assertEqual(parser.func, ['mean', 'median'])

    def test_group_summarize(self):
        tests = [
                {
                    'name': 'Simple',
                    'input': pd.DataFrame(
                        [[1, 1], [1, 2], [2, 3], [2, 4], [2, 5], [3, 6]],
                        columns=['id', 'column']
                    ),
                    'groupby': ["id"],
                    'functions': ['mean'],
                    'summarize_cols': ['column'],
                    'expected': pd.DataFrame(
                        [[1, 1.5], [2, 4.0], [3, 6.]],
                        columns=['id', 'column_mean']
                    ),
                },
                {
                    'name': 'MultiFunc',
                    'input': pd.DataFrame(
                        [[2, 3], [2, 4], [2, 8]],
                        columns=['id', 'column']
                    ),
                    'groupby': ["id"],
                    'functions': ['mean', 'median'],
                    'summarize_cols': ['column'],
                    'expected': pd.DataFrame(
                        [[2, 5., 4.]],
                        columns=['id', 'column_mean', 'column_median']
                    ),
                },
                {
                    'name': 'MultiCol',
                    'input': pd.DataFrame(
                        [[1, 1, 2],
                         [1, 2, 3],
                         [2, 3, 4],
                         [2, 4, 5],
                         [2, 5, 6]],
                        columns=['id', 'column1', 'column2']
                    ),
                    'groupby': ["id"],
                    'functions': ['median'],
                    'summarize_cols': ['column1', 'column2'],
                    'expected': pd.DataFrame(
                        [[1, 1.5, 2.5], [2, 4, 5]],
                        columns=['id', 'column1_median', 'column2_median']
                    ),
                },
                {
                    'name': 'Complex',
                    'input': pd.DataFrame(
                        [['a', 1, 1, 2, 'foo'],
                         ['b', 1, 0, 0, 'foo'],
                         ['b', 1, 2, 3, 'foo'],
                         ['b', 1, 7, 6, 'foo'],
                         ['a', 2, 3, 4, 'foo'],
                         ['a', 2, 4, 5, 'foo'],
                         ['b', 2, 5, 6, 'foo']],
                        columns=['id1', 'id2', 'col1', 'col2', 'unused']
                    ),
                    'groupby': ["id1", "id2"],
                    'functions': ['mean', 'median'],
                    'summarize_cols': ['col1', 'col2'],
                    'expected': pd.DataFrame(
                        [['a', 1, 1.0, 1.0, 2.0, 2.0],
                         ['a', 2, 3.5, 3.5, 4.5, 4.5],
                         ['b', 1, 3.0, 2.0, 3.0, 3.0],
                         ['b', 2, 5.0, 5.0, 6.0, 6.0]],
                        columns=['id1', 'id2',
                                 'col1_mean', 'col1_median',
                                 'col2_mean', 'col2_median']
                    ),
                },
        ]

        for t in tests:
            df = table_group_summarize.group_summarize(
                    t['input'], t['groupby'], t['functions'],
                    t['summarize_cols'],)
            pd_testing.assert_frame_equal(df, t['expected'], obj=t['name'])


if __name__ == '__main__':
    unittest.main()
