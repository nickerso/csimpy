import sys
import os.path
import libsedml
import libcellml
from lxml import etree

from .utils import get_xpath_namespaces

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

    if doc.getErrorLog().getNumFailsWithSeverity(libsedml.LIBSEDML_SEV_ERROR) > 0:
        print(doc.getErrorLog().toString())
        sys.exit(2)

    print('The document has {0} simulation(s).'.format(doc.getNumSimulations()))
    for i in range(0, doc.getNumSimulations()):
        current = doc.getSimulation(i)
        if current.getTypeCode() == libsedml.SEDML_SIMULATION_UNIFORMTIMECOURSE:
            tc = current
            kisaoid = "none"
            if tc.isSetAlgorithm():
                kisaoid = tc.getAlgorithm().getKisaoID()
            print("\tTimecourse id=", tc.getId(), " start=", tc.getOutputStartTime(), " end=", tc.getOutputEndTime(),
                  " numPoints=", tc.getNumberOfPoints(), " kisao=", kisaoid, "\n")
        else:
            print("\tUncountered unknown simulation. ", current.getId(), "\n")

    print("\n")
    print("The document has ", doc.getNumModels(), " model(s).", "\n")
    for i in range(0, doc.getNumModels()):
        current = doc.getModel(i)
        print("\tModel id=", current.getId(), " language=", current.getLanguage(), " source=", current.getSource(),
              " numChanges=", current.getNumChanges(), "\n")

        model_base = os.path.abspath(os.path.dirname(sedml_file))
        model_file = os.path.join(model_base, current.getSource())
        print("Model file: " + model_file)
        model_tree = etree.parse(model_file)

        # handle changes
        for c in range(0, current.getNumChanges()):
            change = current.getChange(c)
            target = change.getTarget()
            print("Change target: " + target)
            xmlns = get_xpath_namespaces(change)
            if change.getTypeCode() == libsedml.SEDML_CHANGE_ATTRIBUTE:
                new_value = change.getNewValue()
                print("Change attribute, new value: " + str(new_value))
                result = model_tree.xpath(target, namespaces=xmlns)
                attribute = result[0]
                attribute.getparent().attrib[attribute.attrname] = new_value

        model_string = str(etree.tostring(model_tree, pretty_print=True), 'utf-8')

        parser = libcellml.Parser()
        model = parser.parseModel(model_string)
        if parser.errorCount():
            for e in range(0, parser.errorCount()):
                print(parser.error(e).description())
                print(parser.error(e).referenceHeading())
        else:
            print("No errors parsing: " + model_file)

    print("\n")
    print("The document has %d task(s)." % doc.getNumTasks())
    for i in range(0, doc.getNumTasks()):
        current = doc.getTask(i)
        print("Type code: " + libsedml.SedTypeCode_toString(current.getTypeCode()))
        print("\tTask id=", current.getId(), " model=", current.getModelReference(), " sim=",
              current.getSimulationReference(), "\n")

    print("\n")
    print("The document has ", doc.getNumDataGenerators(), " datagenerators(s).", "\n")
    for i in range(0, doc.getNumDataGenerators()):
        current = doc.getDataGenerator(i)
        print("\tDG id=", current.getId(), " math=", libsedml.formulaToString(current.getMath()), "\n")

    print("\n")
    print("The document has ", doc.getNumOutputs(), " output(s).", "\n")
    for i in range(0, doc.getNumOutputs()):
        current = doc.getOutput(i)
        tc = current.getTypeCode()
        if tc == libsedml.SEDML_OUTPUT_REPORT:
            r = current
            print("\tReport id=", current.getId(), " numDataSets=", r.getNumDataSets(), "\n")
        elif tc == libsedml.SEDML_OUTPUT_PLOT2D:
            p = current
            print("\tPlot2d id=", current.getId(), " numCurves=", p.getNumCurves(), "\n")
        elif tc == libsedml.SEDML_OUTPUT_PLOT3D:
            p = current
            print("\tPlot3d id=", current.getId(), " numSurfaces=", p.getNumSurfaces(), "\n")
        else:
            print("\tEncountered unknown output ", current.getId(), "\n")
