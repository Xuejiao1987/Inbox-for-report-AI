import io
import unittest
import pandas as pd
from report_core import SAMPLE_CSV, read_table, read_tables, combine_tables, make_report, safe_csv

class Reports(unittest.TestCase):
    def test_batch_rejects_valid_plus_invalid_upload(self):
        with self.assertRaisesRegex(ValueError, 'bad.csv'):
            read_tables([('good.csv', SAMPLE_CSV.encode()), ('bad.csv', b'')])

    def test_header_only_upload(self):
        with self.assertRaisesRegex(ValueError, 'no data rows'):
            read_table('empty.csv', b'amount,region\n')

    def test_sample(self):
        data = read_table('sample.csv', SAMPLE_CSV.encode())
        summary, total, excluded, report = make_report(data, 'revenue', 'region')
        self.assertEqual(total, 2950)
        self.assertEqual(excluded, 0)
        self.assertEqual(dict(zip(summary.region, summary.Total)), {'North':2100, 'South':850})
        self.assertIn('Valid rows: 3', report)

    def test_excel_numeric_headers(self):
        out = io.BytesIO()
        pd.DataFrame({2026:[10,20]}).to_excel(out,index=False)
        data = read_table('test.xlsx',out.getvalue())
        self.assertEqual(make_report(data,'2026',None)[1],30)

    def test_reserved_columns_preserved(self):
        original = pd.DataFrame({'source_file':['a','b'], '_value':['X','Y'], 'amount':[10,20]})
        data, source = combine_tables([('test.csv', original)])
        self.assertEqual(source, '_source_file')
        self.assertEqual(data.source_file.tolist(), ['a','b'])
        self.assertEqual(make_report(data,'amount','_value')[0].iloc[:,0].tolist(), ['X','Y'])
        self.assertEqual(original.columns.tolist(), ['source_file','_value','amount'])

    def test_invalid_and_infinite_values_excluded(self):
        data = pd.DataFrame({'amount':['1,200','bad',None,'inf','-inf','50']})
        summary,total,excluded,_ = make_report(data,'amount',None)
        self.assertEqual((total,excluded),(1250,4))
        self.assertEqual(summary.Records.iloc[0],2)

    def test_group_total_name_collision(self):
        data=pd.DataFrame({'Total':['A','B'], 'amount':[10,20]})
        summary,_,_,_=make_report(data,'amount','Total')
        self.assertEqual(summary.columns.tolist(),['Total (group)','Records','Total'])

    def test_csv_formula_safety(self):
        data=pd.DataFrame({'=header':['=1+1','  @SUM(A1)', 'safe'], 'Total':[1,2,3]})
        result=safe_csv(data).decode('utf-8-sig')
        self.assertIn("'=header",result)
        self.assertIn("'=1+1",result)
        self.assertIn("'  @SUM(A1)",result)

    def test_size_limit(self):
        with self.assertRaisesRegex(ValueError,'10MB'):
            read_table('large.csv',b'x'*10_000_001)

if __name__=='__main__': unittest.main()
