import sys
import unittest
from io import StringIO
from tabletools import table_paste_col

class TestTablePasteCol(unittest.TestCase):
    def test_parser(self):
        parser = table_paste_col.parse_args(['--table', 'foo', '--col-name', 
            'bar', '--col-value', 'baz', '--at-end'])
        self.assertEqual(parser.table, 'foo')
        self.assertEqual(parser.col_name, 'bar')
        self.assertEqual(parser.col_value, 'baz')
        self.assertTrue(parser.at_end)

        parser = table_paste_col.parse_args(['--table', 'foo', '--col-name', 
            'bar', '--col-value', 'baz'])
        self.assertEqual(parser.table, 'foo')
        self.assertEqual(parser.col_name, 'bar')
        self.assertEqual(parser.col_value, 'baz')
        self.assertFalse(parser.at_end)
        
    def test_add_col(self):
        table = StringIO("A\tB\tC\nD\tE\tF\nG\tH\tI\n")
        expected = "foo\tA\tB\tC\nbar\tD\tE\tF\nbar\tG\tH\tI\n"       
        out = StringIO()
        table_paste_col.add_col(table, "\t", "foo", "bar", False, out)
        out.seek(0)
        self.assertEqual(out.read(), expected)

    def test_add_col_at_end(self):
        table = StringIO("A\tB\tC\nD\tE\tF\nG\tH\tI\n")
        expected = "A\tB\tC\tfoo\nD\tE\tF\tbar\nG\tH\tI\tbar\n"       
        out = StringIO()
        table_paste_col.add_col(table, "\t", "foo", "bar", True, out)
        out.seek(0)
        self.assertEqual(out.read(), expected)

if __name__ == '__main__':
    unittest.main()
