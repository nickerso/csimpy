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

    simulations = {}
    for i in range(0, doc.getNumSimulations()):
        current = doc.getSimulation(i)
        if current.getTypeCode() == libsedml.SEDML_SIMULATION_UNIFORMTIMECOURSE:
            tc = current
            kisaoid = "none"
            if tc.isSetAlgorithm():
                kisaoid = tc.getAlgorithm().getKisaoID()
            simulations[tc.getId()] = {
                'type': libsedml.SEDML_SIMULATION_UNIFORMTIMECOURSE,
                'start': tc.getOutputStartTime(),
                'end': tc.getOutputEndTime(),
                'numPoints': tc.getNumberOfPoints(),
                'kisao': kisaoid
            }
        else:
            print("\tEncountered unknown simulation. ", current.getId(), "\n")

    models = {}
    for i in range(0, doc.getNumModels()):
        current = doc.getModel(i)
        if current.getLanguage() != 'urn:sedml:language:cellml.2_0':
            print("\tEncountered unknowm model format (" + current.getLanguage() + ") for model: " +
                  current.getId())
            continue # assume there are other useful models so continue?
        # resolve the model file name
        model_base = os.path.abspath(os.path.dirname(sedml_file))
        model_file = os.path.join(model_base, current.getSource())
        model_tree = etree.parse(model_file)
        # handle changes
        for c in range(0, current.getNumChanges()):
            change = current.getChange(c)
            target = change.getTarget()
            xmlns = get_xpath_namespaces(change)
            if change.getTypeCode() == libsedml.SEDML_CHANGE_ATTRIBUTE:
                new_value = change.getNewValue()
                result = model_tree.xpath(target, namespaces=xmlns)
                attribute = result[0]
                attribute.getparent().attrib[attribute.attrname] = new_value
            else:
                print("\tEncountered unknown model change for model: " + current.getId())
                continue # ignore for now...

        # the final string representation of the model
        model_string = str(etree.tostring(model_tree, pretty_print=True), 'utf-8')

        # quick test to make sure we can use this model - should be removed.
        parser = libcellml.Parser()
        parser.parseModel(model_string)
        if parser.errorCount():
            for e in range(0, parser.errorCount()):
                print(parser.error(e).description())
                print(parser.error(e).referenceHeading())
        else:
            models[current.getId()] = {
                'file': model_file,
                'tree': model_tree,
                'cellml': model_string
            }

    tasks = {}
    for i in range(0, doc.getNumTasks()):
        current = doc.getTask(i)
        if current.getTypeCode() != libsedml.SEDML_TASK:
            print("\tEncountered unknown task type: " + libsedml.SedTypeCode_toString(current.getTypeCode())
                  + "; for task: " + current.getId())
            continue
        m = current.getModelReference()
        s = current.getSimulationReference()
        if not m in models:
            print("\tEncountered a non-existing model reference: " + m + "; for task: " + current.getId())
            continue
        if not s in simulations:
            print("\tEncountered a non-existing simulation reference: " + s + "; for task: " + current.getId())
            continue
        tasks[current.getId()] = {
            'model': m,
            'simulation': s
        }

    data_generators = {}
    for i in range(0, doc.getNumDataGenerators()):
        current = doc.getDataGenerator(i)
        variables = {}
        for v in range(0, current.getNumVariables()):
            cv = current.getVariable(v)
            t = cv.getTaskReference()
            if not t in tasks:
                print("\tEncountered a non-existing task reference: " + t + "; for data generator: " + current.getId())
                continue
            xmlns = get_xpath_namespaces(cv)
            variable_element = models[tasks[t]['model']]['tree'].xpath(cv.getTarget(), namespaces=xmlns)[0]
            variables[cv.getId()] = {
                'name': variable_element.attrib['name'],
                'component': variable_element.getparent().attrib['name']
            }
        data_generators[current.getId()] = {
            'variables': variables,
            'math': libsedml.formulaToString(current.getMath())
        }

    outputs = {}
    for i in range(0, doc.getNumOutputs()):
        current = doc.getOutput(i)
        tc = current.getTypeCode()
        if tc == libsedml.SEDML_OUTPUT_REPORT:
            r = current
            dss = []
            for d in range(0, r.getNumDataSets()):
                ds = r.getDataSet(d)
                label = ds.getLabel()
                if label == '':
                    label = ds.getId()
                dg = r.getDataReference()
                if not dg in data_generators:
                    print("\tEncountered a non-existing dataGenerator reference: " + dg + "; for data set: " +
                          ds.getId())
                    continue
                dss.append({
                    'label': label,
                    'dg': dg
                })
            outputs[r.getId()] = {
                'type': libsedml.SEDML_OUTPUT_REPORT,
                'data-sets': dss
            }
        elif tc == libsedml.SEDML_OUTPUT_PLOT2D:
            p = current
            curves = []
            for c in range(0, p.getNumCurves()):
                curve = p.getCurve(c)
                label = curve.getName()
                if label == '':
                    label = curve.getId()
                dgX = curve.getXDataReference()
                if not dgX in data_generators:
                    print("\tEncountered a non-existing X dataGenerator reference: " + dgX + "; for curve: " +
                          curve.getId())
                    continue
                dgY = curve.getYDataReference()
                if not dgY in data_generators:
                    print("\tEncountered a non-existing Y dataGenerator reference: " + dgY + "; for curve: " +
                          curve.getId())
                    continue
                curves.append({
                    'label': label,
                    'dgX': dgX,
                    'dgY': dgY
                })
            outputs[p.getId()] = {
                'type': libsedml.SEDML_OUTPUT_PLOT2D,
                'curves': curves
            }
        else:
            print("\tEncountered unknown output ", current.getId(), "\n")

    print(outputs)
