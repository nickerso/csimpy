import sys
import os.path
import libsedml

from .ExperimentManifest import ExperimentManifest


__all__ = ['execute_simulation_experiment']


def execute_simulation_experiment(sedml_file, output_directory):
    """ Execute the simulation experiment defined in the given SED-ML document and save the outputs.

    Args:
        sedml_file (:obj:`str`): path to SED-ML document
        output_directory (:obj:`str`): directory to store the outputs of the experiment
    """
    print("Executing the simulation experiment: " + sedml_file +
          "; with output stored in the directory: " + output_directory)

    doc = libsedml.readSedML(sedml_file)

    if doc.getErrorLog().getNumFailsWithSeverity(libsedml.LIBSEDML_SEV_WARNING) > 0:
        print(doc.getErrorLog().toString())
        sys.exit(2)

    # The base location to use when resolving relative locations
    model_base = os.path.abspath(os.path.dirname(sedml_file))

    manifest = ExperimentManifest()
    manifest.build(doc, model_base)
    if not manifest.instantiate():
        print("There was an error instantiating the experiment manifest.")
        sys.exit(3)
