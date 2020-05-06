import sys
import os.path
import libsedml
import libcellml
from lxml import etree

from .utils import get_xpath_namespaces


class ExperimentManifest:

    def __init__(self):
        self._simulations = {}
        self._models = {}
        self._tasks = {}
        self._data_generators = {}
        self._outputs = {}

    def build(self, sedml, base_location):
        """
        Build this experiment manifest from the provided SED-ML document. We assume that the SED-ML document
        has been checked for errors prior to its use here.

        :param sedml: The SED-ML document as parsed by libsedml.
        :param base_location: The base location to use in resolving relative model locations.
        """

        for i in range(0, sedml.getNumSimulations()):
            current = sedml.getSimulation(i)
            if current.getTypeCode() == libsedml.SEDML_SIMULATION_UNIFORMTIMECOURSE:
                tc = current
                kisaoid = "none"
                if tc.isSetAlgorithm():
                    kisaoid = tc.getAlgorithm().getKisaoID()
                self._simulations[tc.getId()] = {
                    'type': libsedml.SEDML_SIMULATION_UNIFORMTIMECOURSE,
                    'start': tc.getOutputStartTime(),
                    'end': tc.getOutputEndTime(),
                    'numPoints': tc.getNumberOfPoints(),
                    'kisao': kisaoid
                }
            else:
                print("\tEncountered unknown simulation. ", current.getId(), "\n")

        for i in range(0, sedml.getNumModels()):
            current = sedml.getModel(i)
            if current.getLanguage() != 'urn:sedml:language:cellml.2_0':
                print("\tEncountered unknown model format (" + current.getLanguage() + ") for model: " +
                      current.getId())
                continue  # assume there are other useful models so continue?
            # resolve the model file name
            model_file = os.path.join(base_location, current.getSource())
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
                    continue  # ignore for now...

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
                self._models[current.getId()] = {
                    'file': model_file,
                    'tree': model_tree,
                    'cellml': model_string
                }

        for i in range(0, sedml.getNumTasks()):
            current = sedml.getTask(i)
            if current.getTypeCode() != libsedml.SEDML_TASK:
                print("\tEncountered unknown task type: " + libsedml.SedTypeCode_toString(current.getTypeCode())
                      + "; for task: " + current.getId())
                continue
            m = current.getModelReference()
            s = current.getSimulationReference()
            if not m in self._models:
                print("\tEncountered a non-existing model reference: " + m + "; for task: " + current.getId())
                continue
            if not s in self._simulations:
                print("\tEncountered a non-existing simulation reference: " + s + "; for task: " + current.getId())
                continue
            self._tasks[current.getId()] = {
                'model': m,
                'simulation': s
            }

        for i in range(0, sedml.getNumDataGenerators()):
            current = sedml.getDataGenerator(i)
            variables = {}
            for v in range(0, current.getNumVariables()):
                cv = current.getVariable(v)
                t = cv.getTaskReference()
                if not t in self._tasks:
                    print("\tEncountered a non-existing task reference: " + t + "; for data generator: " +
                          current.getId())
                    continue
                xmlns = get_xpath_namespaces(cv)
                model_tree = self._models[self._tasks[t]['model']]['tree']
                variable_element = model_tree.xpath(cv.getTarget(), namespaces=xmlns)[0]
                variables[cv.getId()] = {
                    'name': variable_element.attrib['name'],
                    'component': variable_element.getparent().attrib['name']
                }
            self._data_generators[current.getId()] = {
                'variables': variables,
                'math': libsedml.formulaToString(current.getMath())
            }

        for i in range(0, sedml.getNumOutputs()):
            current = sedml.getOutput(i)
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
                    if not dg in self._data_generators:
                        print("\tEncountered a non-existing dataGenerator reference: " + dg + "; for data set: " +
                              ds.getId())
                        continue
                    dss.append({
                        'label': label,
                        'dg': dg
                    })
                self._outputs[r.getId()] = {
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
                    if not dgX in self._data_generators:
                        print("\tEncountered a non-existing X dataGenerator reference: " + dgX + "; for curve: " +
                              curve.getId())
                        continue
                    dgY = curve.getYDataReference()
                    if not dgY in self._data_generators:
                        print("\tEncountered a non-existing Y dataGenerator reference: " + dgY + "; for curve: " +
                              curve.getId())
                        continue
                    curves.append({
                        'label': label,
                        'dgX': dgX,
                        'dgY': dgY
                    })
                self._outputs[p.getId()] = {
                    'type': libsedml.SEDML_OUTPUT_PLOT2D,
                    'curves': curves
                }
            else:
                print("\tEncountered unknown output ", current.getId(), "\n")

