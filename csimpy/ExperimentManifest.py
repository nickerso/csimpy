import sys
import csv
import os.path
import libsedml
import libcellml
from lxml import etree
from scipy import integrate
import matplotlib.pyplot as plt

from .utils import \
    get_xpath_namespaces, \
    module_from_string, \
    get_array_index_for_variable, \
    get_array_index_for_equivalent_variable


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
                    attribute = result[0] # NEED TO UNDERSTAND
                    attribute.getparent().attrib[attribute.attrname] = new_value # NEED TO UNDERSTAND
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
                    'location': model_file,
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
                    'component': variable_element.getparent().attrib['name'],
                    'task': t
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
            importer.flattenModel(model)
            # generate Python code for the flattened model
            generator = libcellml.Generator()
            profile = libcellml.GeneratorProfile(libcellml.GeneratorProfile.Profile.PYTHON)
            generator.setProfile(profile)
            generator.processModel(model)
            if generator.errorCount():
                for e in range(0, generator.errorCount()):
                    print(generator.error(e).description())
                return False
            implementation_code = generator.implementationCode()
            module = module_from_string(implementation_code)

            print(implementation_code)
            print("module: ", module)
            print("module function: ", module.compute_rates)

            #
            # Andre: Need to take different modules for variables into account...
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

            # accessing python code
            start = self._simulations['simulation1']['start']
            end = self._simulations['simulation1']['end']
            numpoints = self._simulations['simulation1']['numPoints']

            stepsize = (end - start) / numpoints
            print(start, end, numpoints, stepsize)

            states = module.create_states_array()
            variables = module.create_variables_array()
            module.initialize_states_and_constants(states, variables)

            def func(t, y):
                rates = module.create_states_array()
                module.compute_rates(t, y, rates, variables)
                return rates

            solution = integrate.solve_ivp(func, [start, end], states, method='LSODA', max_step=stepsize, atol=1e-4,
                                           rtol=1e-6)
            print(solution.t)
            print(solution.y)

            # saving data in a csv
            with open('./csimpy/data.csv', 'w', newline='') as csvfile:
                spamwriter = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                for i in range(0, len(solution.t)):
                    spamwriter.writerow([solution.t[i], solution.y[0][i]])

            # plotting a graph
            fig, ax = plt.subplots()
            ax.plot(solution.t, solution.y[0], label='Line 1')
            ax.set_xlabel('t')
            ax.set_ylabel('y')
            ax.set_title('Some Title')
            ax.legend()

            fig.savefig('./csimpy/figure.png')

        return True