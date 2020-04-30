from csimpy import __main__
import csimpy
import os
import shutil
import tempfile
import unittest


class CliTestCase(unittest.TestCase):
    EXAMPLE_SEDML_FILENAME = 'tests/fixtures/sine_imports.xml'

    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_help(self):
        with self.assertRaises(SystemExit):
            with __main__.App(argv=['--help']) as app:
                app.run()

    def test_version(self):
        with __main__.App(argv=['-v']) as app:
            # need to work out how to do this on Windows...
            # with capturer.CaptureOutput(merged=False, relay=False) as captured:
            #     with self.assertRaises(SystemExit):
            #         app.run()
            #     self.assertIn(csimpy.__version__, captured.stdout.get_text())
            #     self.assertEqual(captured.stderr.get_text(), '')
            app.run()

        with __main__.App(argv=['--version']) as app:
            # need to work out how to do this on Windows...
            # with capturer.CaptureOutput(merged=False, relay=False) as captured:
            #     with self.assertRaises(SystemExit):
            #         app.run()
            #     self.assertIn(csimpy.__version__, captured.stdout.get_text())
            #     self.assertEqual(captured.stderr.get_text(), '')
            app.run()

        self.assertFalse(expr=True, msg="Testing")

    def test_sim_short_arg_names(self):
        with __main__.App(argv=['-i', self.EXAMPLE_SEDML_FILENAME, '-o', self.dirname]) as app:
            app.run()
        self.assert_outputs_created(self.dirname)

    def test_sim_long_arg_names(self):
        with __main__.App(argv=['--sedml', self.EXAMPLE_SEDML_FILENAME, '--outout-directory', self.dirname]) as app:
            app.run()
        self.assert_outputs_created(self.dirname)

    def assert_outputs_created(self, dirname):
        self.assertEqual(set(os.listdir(dirname)), set(['ex1', 'ex2']))
        self.assertEqual(set(os.listdir(os.path.join(dirname, 'ex1'))), set(['BIOMD0000000297']))
        self.assertEqual(set(os.listdir(os.path.join(dirname, 'ex2'))), set(['BIOMD0000000297']))
        self.assertEqual(set(os.listdir(os.path.join(dirname, 'ex1', 'BIOMD0000000297'))), set(['plot_1_task1.pdf', 'plot_3_task1.pdf']))
        self.assertEqual(set(os.listdir(os.path.join(dirname, 'ex2', 'BIOMD0000000297'))), set(['plot_1_task1.pdf', 'plot_3_task1.pdf']))

        files = [
            os.path.join(dirname, 'ex1', 'BIOMD0000000297', 'plot_1_task1.pdf'),
            os.path.join(dirname, 'ex1', 'BIOMD0000000297', 'plot_3_task1.pdf'),
            os.path.join(dirname, 'ex2', 'BIOMD0000000297', 'plot_1_task1.pdf'),
            os.path.join(dirname, 'ex2', 'BIOMD0000000297', 'plot_3_task1.pdf'),
        ]
