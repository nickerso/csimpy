import sys
import os.path
import libsedml
import libcellml
from lxml import etree

from .utils import \
    get_xpath_namespaces, \
    module_from_string, \
    get_array_index_for_variable, \
    get_array_index_for_equivalent_variable

# convenience methods to help keep track of what each of these objects have in them...
def print_simulation(id, s):
    print("*# Simulation: " + id)
    print("*#  type: " + libsedml.SedTypeCode_toString(s['type']))
    print("*#  simulation algorithm: {}".format(s['kisao']))
    print("*#  interval: {} .. [ {} --output--> {} ]; {} points".format(s['initial'], s['start'], s['end'],
                                                                   s['numPoints']))

def print_model(id, m):
    print("*# Model: " + id)
    print("*#   location: " + m['location'])
    print("*#   ((model['tree']: XML DOM tree))")
    print("*#   ((model['cellml']: string representation of the CellML XML))")

def print_task(id, t):
    print("*# Task: " + id)
    print("*#   model reference: " + t['model'])
    print("*#   simulation reference: " + t['simulation'])

def print_datagenerator(id, dg):
    print("*# Data generator: " + id)
    print("*#   Formula: " + dg['math'])
    print("*#   Variables:")
    variables = dg['variables']
    for vId, v in variables.items():
        print("*#     Variable: " + vId)
        print("*#       From task: " + v['task'])
        print("*#       CellML variable: {} // {}".format(v['component'], v['name']))

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
                sId = tc.getId()
                self._simulations[sId] = {
                    'type': libsedml.SEDML_SIMULATION_UNIFORMTIMECOURSE,
                    'initial': tc.getInitialTime(),
                    'start': tc.getOutputStartTime(),
                    'end': tc.getOutputEndTime(),
                    'numPoints': tc.getNumberOfPoints(),
                    'kisao': kisaoid
                }
                print_simulation(sId, self._simulations[sId])
            else:
                print("\tEncountered unknown simulation type. ", current.getId(), "\n")

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
                mId = current.getId()
                self._models[mId] = {
                    'location': model_file,
                    'tree': model_tree,
                    'cellml': model_string
                }
                print_model(mId, self._models[mId])

        for i in range(0, sedml.getNumTasks()):
            current = sedml.getTask(i)
            if current.getTypeCode() != libsedml.SEDML_TASK:
                print("\tEncountered unknown task type: " + libsedml.SedTypeCode_toString(current.getTypeCode())
                      + "; for task: " + current.getId())
                continue
            tId = current.getId()
            m = current.getModelReference()
            s = current.getSimulationReference()
            if not m in self._models:
                print("\tEncountered a non-existing model reference: " + m + "; for task: " + tId)
                continue
            if not s in self._simulations:
                print("\tEncountered a non-existing simulation reference: " + s + "; for task: " + tId)
                continue
            self._tasks[tId] = {
                'model': m,
                'simulation': s
            }
            print_task(tId, self._tasks[tId])

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
                    'component': variable_element.getparent().attrib['name'],
                    'task': t
                }
            dgId = current.getId()
            self._data_generators[dgId] = {
                'variables': variables,
                'math': libsedml.formulaToString(current.getMath())
            }
            print_datagenerator(dgId, self._data_generators[dgId])

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

    def instantiate(self):
        """
        Instantiate the code required to execute this experiment. Will generate code for the CellML models
        as well as the supporting code to pull out the data generators.
        """
        for id, m in self._models.items():
            print("Instantiating model: " + id + "; with original source location: " + m['location'])
            parser = libcellml.Parser()
            model = parser.parseModel(m['cellml'])
            # need to flatten before generating code
            # see https://github.com/cellml/libcellml/issues/592 as to why the '/' is required
            model_base = os.path.dirname(m['location']) + '/'
            importer = libcellml.Importer()
            importer.resolveImports(model, model_base)
            if model.hasUnresolvedImports():
                print("Model still has unresolved imports.")
                return False
            flat_model = importer.flattenModel(model)
            # fix up duplicate id's to avoid errors in analysing the model
            annotator = libcellml.Annotator()
            annotator.setModel(flat_model)
            annotator.clearAllIds()
            # generate Python code for the flattened model
            analyser = libcellml.Analyser()
            analyser.analyseModel(flat_model)
            if analyser.errorCount():
                for e in range(0, analyser.errorCount()):
                    print(analyser.error(e).description())
                return False

            analyser_model = analyser.model();
            generator = libcellml.Generator()
            generator.setModel(analyser_model)
            profile = libcellml.GeneratorProfile(libcellml.GeneratorProfile.Profile.PYTHON)
            generator.setProfile(profile)
            implementation_code = generator.implementationCode()
            module = module_from_string(implementation_code)
            # test module is valid
            if module.__version__:
                if module.__version__ != "0.1.0":
                    print("Unexpected instantiated module version: " + module.__version__)
                    return False
            else:
                print("Unable to determine instantiated module version")
                return False
            # store the CellML model and the instantiated implementation
            m['instantiated-cellml'] = model
            m['instantiated-module'] = module

            #
            # Need to take different modules for variables into account...
            #

            # Generate the method for getting the data generator values
            # map the data generators to variables in the generated code
            arrays = ["dummy", "voi", "state", "variable"]
            for dgid, dg in self._data_generators.items():
                print("Mapping data generator: {}".format(dgid))
                for vid, v in dg['variables'].items():
                    print("Mapping variable {}: {} / {}".format(vid, v['component'], v['name']))
                    index, array = get_array_index_for_variable(module, v['component'], v['name'])
                    if array > 0:
                        print("Found at index: {}; in array: {}".format(index, arrays[array]))
                    if array < 0:
                        # search for equivalent variables in the flattened model
                        component = model.component(v['component'], True)
                        variable = component.variable(v['name'])
                        index, array = get_array_index_for_equivalent_variable(module, variable)
                        if array > 0:
                            print("Found equivalent variable at index: {}; in array: {}".format(index, arrays[array]))


        return True