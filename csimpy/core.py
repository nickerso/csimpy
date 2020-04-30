import os

__all__ = ['execute_simulation_experiment']


def execute_simulation_experiment(sedml_file, output_directory):
    """ Execute the simulation experiment defined in the given SED-ML document and save the outputs.

    Args:
        sedml_file (:obj:`str`): path to SED-ML document
        output_directory (:obj:`str`): directory to store the outputs of the experiment
    """
    print("Executing the simulation experiment: " + sedml_file +
          "; with output stored in the directory: " + output_directory)
