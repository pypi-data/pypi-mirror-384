import unittest
import pandas as pd
import pandas.testing as pd_testing
from io import StringIO

from tabletools import table_join


class TestTableJoin(unittest.TestCase):
    def test_parser(self):
        some_opts = [
            '--table1', 'foo',
            '--table2', 'bar',
            '--key1', 'foo_id',
            '--key2', 'bar_id',
            '--suffix1', 'foo_suf',
            '--suffix2', 'bar_suf',
            '--delim', 'fancy_delim',
            ]

        parser = table_join.parse_args(some_opts)
        self.assertEqual(parser.table1, 'foo')
        self.assertEqual(parser.table2, 'bar')
        self.assertEqual(parser.key1, ['foo_id'])
        self.assertEqual(parser.key2, ['bar_id'])
        self.assertEqual(parser.suffix1, 'foo_suf')
        self.assertEqual(parser.suffix2, 'bar_suf')
        self.assertEqual(parser.delim, 'fancy_delim')
        self.assertEqual(parser.how, 'inner')

        for h in ['left', 'right', 'outer', 'inner', 'cross']:
            parser = table_join.parse_args(some_opts + ['--how', h])
            self.assertEqual(parser.how, h)

    def test_join(self):

        tests = [
                {
                    'name': 'Join with overlapping column names',
                    'file1': StringIO("A\tB\nid1\t4\nid2\t5"),
                    'file2': StringIO("A\tB\nid1\t14\nid2\t15"),
                    'expected': pd.DataFrame(
                        [['id1', 4, 14], ['id2', 5, 15]],
                        columns=['A', 'B_x', 'B_y']),
                    'key1': 'A',
                    'key2': 'A',
                    'suffixes': ('_x', '_y'),
                    'how': 'inner',
                },
                {
                    'name': 'Join with non-overlapping column names',
                    'file1': StringIO("A\tC\nid1\t4\nid2\t5"),
                    'file2': StringIO("A\tB\nid1\t14\nid2\t15"),
                    'expected': pd.DataFrame(
                        [['id1', 4, 14], ['id2', 5, 15]],
                        columns=['A', 'C', 'B']),
                    'key1': 'A',
                    'key2': 'A',
                    'suffixes': ('_x', '_y'),
                    'how': 'inner',
                },
                {
                    'name': 'Outer join',
                    'file1': StringIO("A\tC\nid1\t4\nid2\t5"),
                    'file2': StringIO("A\tB\nid1\t14\nid3\t15"),
                    'expected': pd.DataFrame(
                        [['id1', 4., 14.], ['id2', 5., None], ['id3', None, 15]],
                        columns=['A', 'C', 'B']),
                    'key1': 'A',
                    'key2': 'A',
                    'suffixes': ('_x', '_y'),
                    'how': 'outer',
                },
        ]

        for t in tests:
            df = table_join.join(t['file1'], t['file2'], t['key1'], t['key2'],
                                 t['suffixes'], t['how'])
            pd_testing.assert_frame_equal(df, t['expected'])


if __name__ == '__main__':
    unittest.main()
