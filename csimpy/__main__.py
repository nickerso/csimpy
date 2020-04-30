import cement
import csimpy
from .core import execute_simulation_experiment

class BaseController(cement.Controller):
    """ Base controller for command line application """

    class Meta:
        label = 'base'
        description = ("CSimPy simulation program <https://github.com/nickerso/csimpy>.")
        help = "csimpy"
        arguments = [
            (['-i', '--sedml'], dict(type=str,
                                      required=True,
                                      help='Path to SED-ML encoded description of the simulation experiment to perform.')),
            (['-o', '--output-directory'], dict(type=str,
                                                default='.',
                                                help='Directory to save outputs')),
            (['-v', '--version'], dict(action='version',
                                       version=csimpy.__version__)),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        execute_simulation_experiment(args.sedml, args.output_directory)

class App(cement.App):
    """ Command line application """
    class Meta:
        label = 'csimpy'
        base_controller = 'base'
        handlers = [
            BaseController,
        ]


if __name__ == "__main__":
    with App() as app:
        app.run()
