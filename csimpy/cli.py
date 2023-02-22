from csimpy import get_simulator_version, exec_sedml_docs_in_combine_archive
from biosimulators_utils.simulator.cli import build_cli

App = build_cli('csimpy', '0.1',
                'CSimPy', get_simulator_version(), 'https://github.com/nickerso/csimpy',
                exec_sedml_docs_in_combine_archive)


def main():
    with App() as app:
        app.run()


if __name__ == "__main__":
    main()
