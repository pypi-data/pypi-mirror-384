import unittest
import io

from tabletools import table_cat


class TestTableCat(unittest.TestCase):
    def test_parser(self):
        parser = table_cat.parse_args(['foo', '-z'])
        self.assertEqual(parser.tables, ['foo'])
        self.assertTrue(parser.gunzip)

        parser = table_cat.parse_args(['foo', 'bar', '-z'])
        self.assertEqual(parser.tables, ['foo', 'bar'])
        self.assertTrue(parser.gunzip)

        parser = table_cat.parse_args(['foo', 'bar'])
        self.assertEqual(parser.tables, ['foo', 'bar'])
        self.assertFalse(parser.gunzip)

    def test_cat_tables(self):
        tests = [
                {
                    'name': 'Simple',
                    'input': [
                        io.StringIO('A\tB\n0\t0\n0\t0\n'),
                        io.StringIO('A\tB\n1\t1\n1\t1\n')],
                    'expected': 'A\tB\n0\t0\n0\t0\n1\t1\n1\t1\n',
                    'err': None,
                    'gunzip': False,
                },
                {
                    'name': 'Trailing tab',
                    'input': [
                        io.StringIO('\tA\tB\n0\t0\n0\t0\n'),
                        io.StringIO('\tA\tB\n1\t1\n1\t1\n')],
                    'expected': '\tA\tB\n0\t0\n0\t0\n1\t1\n1\t1\n',
                    'err': None,
                    'gunzip': False,
                },
                {
                    'name': 'Bad headers',
                    'input': [
                        io.StringIO('A\tB\n0\t0\n0\t0\n'),
                        io.StringIO('A\tC\n1\t1\n1\t1\n')],
                    'expected': '',
                    'err': 'File headers are not the same in all input files',
                    'gunzip': False,
                },
        ]

        for t in tests:
            out = io.StringIO()
            err = table_cat.cat_tables(t['input'], t['gunzip'], out)
            out.seek(0)
            self.assertEqual(err, t['err'], msg=t['name'])
            self.assertEqual(out.read(), t['expected'], msg=t['name'])


if __name__ == '__main__':
    unittest.main()
