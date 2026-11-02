from pathlib import Path
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / 'app.py')

class PreviewUI(unittest.TestCase):
    def test_sample_report_survives_rerun_and_clears_on_change(self):
        app = AppTest.from_file(APP).run()
        self.assertEqual(len(app.exception),0)
        app.checkbox[0].check().run()
        app.selectbox[1].select('region').run()
        app.button[0].click().run()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(app.metric[0].value,'2,950.00')
        self.assertEqual(len(app.get('download_button')),2)
        app.run()  # Simulate the rerun caused by a download or another widget.
        self.assertEqual(len(app.exception),0)
        self.assertEqual(app.metric[0].value,'2,950.00')
        self.assertEqual(len(app.get('download_button')),2)
        app.selectbox[1].select('date').run()
        self.assertEqual(len(app.metric),0)
        app.button[0].click().run()
        self.assertEqual(app.metric[0].value,'2,950.00')
        app.checkbox[0].uncheck().run()
        self.assertEqual(len(app.metric),0)
        self.assertEqual(len(app.get('download_button')),0)
        self.assertEqual(len(app.exception),0)

    def test_parse_error_clears_previous_report(self):
        app=AppTest.from_file(APP).run()
        app.checkbox[0].check().run()
        app.button[0].click().run()
        self.assertEqual(app.metric[0].value,'2,950.00')
        with patch('report_core.read_tables', side_effect=ValueError('bad.csv: invalid file')):
            app.run()
        self.assertEqual(len(app.metric),0)
        self.assertEqual(len(app.get('download_button')),0)
        self.assertIn('bad.csv', app.error[0].value)
        app.run()
        self.assertEqual(len(app.metric),0)
        self.assertEqual(len(app.exception),0)

    def test_repeated_generation(self):
        app=AppTest.from_file(APP).run()
        app.checkbox[0].check().run()
        for _ in range(2):
            app.button[0].click().run()
            self.assertEqual(len(app.exception),0)
            self.assertEqual(app.metric[0].value,'2,950.00')
            self.assertEqual(len(app.get('download_button')),2)

if __name__=='__main__': unittest.main()
