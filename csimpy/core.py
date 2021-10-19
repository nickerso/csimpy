from biosimulators_utils.combine.exec import exec_sedml_docs_in_archive
from biosimulators_utils.config import get_config, Config  # noqa: F401
from biosimulators_utils.utils.core import raise_errors_warnings
from biosimulators_utils.log.data_model import CombineArchiveLog, TaskLog, StandardOutputErrorCapturerLevel  # noqa: F401
from biosimulators_utils.viz.data_model import VizFormat  # noqa: F401
from biosimulators_utils.report.data_model import ReportFormat, VariableResults, SedDocumentResults  # noqa: F401
from biosimulators_utils.sedml import validation
from biosimulators_utils.sedml.data_model import (  # noqa: F401
    SedDocument, ModelLanguage, ModelAttributeChange, UniformTimeCourseSimulation, Algorithm, Task, RepeatedTask,
    VectorRange, SubTask, DataGenerator, Variable)
from biosimulators_utils.sedml.exec import exec_sed_doc as base_exec_sed_doc
from biosimulators_utils.sedml.utils import apply_changes_to_xml_model
import copy
import lxml.etree
import os
import tempfile
import functools

from .utils import get_csimpy_algorithm, instantiate_csimpy_model, map_csimpy_variables_to_instantiation, \
    csimpy_execute_integration_task

__all__ = [
    'exec_sedml_docs_in_combine_archive', 'exec_sed_doc', 'exec_sed_task', 'preprocess_sed_task',
]


def exec_sedml_docs_in_combine_archive(archive_filename, out_dir, config=None):
    """ Execute the SED tasks defined in a COMBINE/OMEX archive and save the outputs

    Args:
        archive_filename (:obj:`str`): path to COMBINE/OMEX archive
        out_dir (:obj:`str`): path to store the outputs of the archive

            * CSV: directory in which to save outputs to files
              ``{ out_dir }/{ relative-path-to-SED-ML-file-within-archive }/{ report.id }.csv``
            * HDF5: directory in which to save a single HDF5 file (``{ out_dir }/reports.h5``),
              with reports at keys ``{ relative-path-to-SED-ML-file-within-archive }/{ report.id }`` within the HDF5 file

        config (:obj:`Config`, optional): BioSimulators common configuration

    Returns:
        :obj:`tuple`:

            * :obj:`SedDocumentResults`: results
            * :obj:`CombineArchiveLog`: log
    """
    return exec_sedml_docs_in_archive(exec_sed_doc, archive_filename, out_dir,
                                      apply_xml_model_changes=True,
                                      log_level=StandardOutputErrorCapturerLevel.python,
                                      config=config)


def exec_sed_doc(doc, working_dir, base_out_path, rel_out_path=None,
                 apply_xml_model_changes=False,
                 log=None, indent=0, pretty_print_modified_xml_models=False,
                 log_level=StandardOutputErrorCapturerLevel.python, config=None):
    """ Execute the tasks specified in a SED document and generate the specified outputs

    Args:
        doc (:obj:`SedDocument` or :obj:`str`): SED document or a path to SED-ML file which defines a SED document
        working_dir (:obj:`str`): working directory of the SED document (path relative to which models are located)

        base_out_path (:obj:`str`): path to store the outputs

            * CSV: directory in which to save outputs to files
              ``{base_out_path}/{rel_out_path}/{report.id}.csv``
            * HDF5: directory in which to save a single HDF5 file (``{base_out_path}/reports.h5``),
              with reports at keys ``{rel_out_path}/{report.id}`` within the HDF5 file

        rel_out_path (:obj:`str`, optional): path relative to :obj:`base_out_path` to store the outputs
        apply_xml_model_changes (:obj:`bool`, optional): if :obj:`True`, apply any model changes specified in the SED-ML file before
            calling :obj:`task_executer`.
        log (:obj:`SedDocumentLog`, optional): log of the document
        indent (:obj:`int`, optional): degree to indent status messages
        pretty_print_modified_xml_models (:obj:`bool`, optional): if :obj:`True`, pretty print modified XML models
        log_level (:obj:`StandardOutputErrorCapturerLevel`, optional): level at which to log output
        config (:obj:`Config`, optional): BioSimulators common configuration

    Returns:
        :obj:`tuple`:

            * :obj:`ReportResults`: results of each report
            * :obj:`SedDocumentLog`: log of the document
    """
    simulator_config = {
        'archive-root': working_dir,
    }
    sed_task_executor = functools.partial(exec_sed_task, simulator_config=simulator_config)
    return base_exec_sed_doc(sed_task_executor, doc, working_dir, base_out_path,
                             rel_out_path=rel_out_path,
                             apply_xml_model_changes=apply_xml_model_changes,
                             log=log,
                             indent=indent,
                             pretty_print_modified_xml_models=pretty_print_modified_xml_models,
                             log_level=log_level,
                             config=config)


def exec_sed_task(task, variables, preprocessed_task=None, log=None, config=None, simulator_config=None):
    ''' Execute a task and save its results

    Args:
        task (:obj:`Task`): task
        variables (:obj:`list` of :obj:`Variable`): variables that should be recorded
        preprocessed_task (:obj:`dict`, optional): preprocessed information about the task, including possible
            model changes and variables. This can be used to avoid repeatedly executing the same initialization
            for repeated calls to this method.
        log (:obj:`TaskLog`, optional): log for the task
        config (:obj:`Config`, optional): BioSimulators common configuration

    Returns:
        :obj:`tuple`:

            :obj:`VariableResults`: results of variables
            :obj:`TaskLog`: log

    Raises:
        :obj:`ValueError`: if the task or an aspect of the task is not valid, or the requested output variables
            could not be recorded
        :obj:`NotImplementedError`: if the task is not of a supported type or involves an unsupported feature
    '''
    if not config:
        config = get_config()

    # initialize a log of the execution of this task
    if config.LOG and not log:
        log = TaskLog()

    if preprocessed_task is None:
        preprocessed_task = preprocess_sed_task(task, variables, config=config)

    # modify model
    if task.model.changes:
        raise_errors_warnings(validation.validate_model_change_types(task.model.changes, (ModelAttributeChange,)),
                              error_summary='Changes for model `{}` are not supported.'.format(task.model.id))

        model_etree = preprocessed_task['model_etree']

        model = copy.deepcopy(task.model)
        for change in model.changes:
            change.new_value = str(change.new_value)

        apply_changes_to_xml_model(model, model_etree, sed_doc=None, working_dir=None)

        model_file, model_filename = tempfile.mkstemp(suffix='.xml')
        os.close(model_file)

        model_etree.write(model_filename,
                          xml_declaration=True,
                          encoding="utf-8",
                          standalone=False,
                          pretty_print=False)
    else:
        model_filename = task.model.source

    # instantiate CSimPy simulation
    instantiated_model = instantiate_csimpy_model(model_filename, simulator_config['archive-root'])

    if not instantiated_model:
        raise RuntimeError('CSimPy failed to instaniate model.')

    # Map variables to report
    mapped_variables = map_csimpy_variables_to_instantiation(preprocessed_task['variables'], instantiated_model)
    if not mapped_variables:
        raise RuntimeError('CSimPy failed to map observables.')

    # clean up temporary model
    if task.model.changes:
        os.remove(model_filename)

    # execute the simulation
    variable_results = csimpy_execute_integration_task(instantiated_model, preprocessed_task['task'],
                                                       preprocessed_task['variables'])

    # log action
    if config.LOG:
        log.algorithm = preprocessed_task['task'].simulation.algorithm.kisao_id
        log.simulator_details = {
            'method': 'CSimPy.do_cool_stuff',
            'algorithmParameters': [
                {'kisaoID': change.kisao_id, 'value': change.new_value}
                for change in preprocessed_task['task'].simulation.algorithm.changes
            ],
        }

    # return results and log
    return variable_results, log


def preprocess_sed_task(task, variables, config=None):
    """ Preprocess a SED task, including its possible model changes and variables. This is useful for avoiding
    repeatedly initializing tasks on repeated calls of :obj:`exec_sed_task`.

    Args:
        task (:obj:`Task`): task
        variables (:obj:`list` of :obj:`Variable`): variables that should be recorded
        config (:obj:`Config`, optional): BioSimulators common configuration

    Returns:
        :obj:`dict`: preprocessed information about the task
    """
    if not config:
        config = get_config()

    model = task.model
    sim = task.simulation

    if config.VALIDATE_SEDML:
        raise_errors_warnings(validation.validate_task(task),
                              error_summary='Task `{}` is invalid.'.format(task.id))
        raise_errors_warnings(validation.validate_model_language(model.language, ModelLanguage.CellML),
                              error_summary='Language for model `{}` is not supported.'.format(model.id))
        raise_errors_warnings(validation.validate_model_change_types(model.changes, (ModelAttributeChange,)),
                              error_summary='Changes for model `{}` are not supported.'.format(model.id))
        raise_errors_warnings(*validation.validate_model_changes(model),
                              error_summary='Changes for model `{}` are invalid.'.format(model.id))
        raise_errors_warnings(validation.validate_simulation_type(sim, (UniformTimeCourseSimulation, )),
                              error_summary='{} `{}` is not supported.'.format(sim.__class__.__name__, sim.id))
        raise_errors_warnings(*validation.validate_simulation(sim),
                              error_summary='Simulation `{}` is invalid.'.format(sim.id))
        raise_errors_warnings(*validation.validate_data_generator_variables(variables),
                              error_summary='Data generator variables for task `{}` are invalid.'.format(task.id))

    # read model
    model_etree = lxml.etree.parse(model.source)

    # get the variables that we need to record
    csimpy_variables = {}
    for v in variables:
        namespaces = copy.copy(v.target_namespaces)
        namespaces.pop(None, None)

        variable_element = model_etree.xpath(v.target, namespaces=namespaces)[0]
        csimpy_variables[v.id] = {
            'name': variable_element.attrib['name'],
            'component': variable_element.getparent().attrib['name'],
            'array': -1,
            'index': 0
        }

    # check that CSimPy can execute the requested algorithm (or a similar one)
    csimpy_algorithm = get_csimpy_algorithm(task.simulation.algorithm, config=config)

    # create new task to manage configuration for CSimPy
    csimpy_task = copy.deepcopy(task)
    csimpy_task.simulation = copy.deepcopy(sim)
    csimpy_task.simulation.algorithm = csimpy_algorithm

    # return preprocessed information
    return {
        'task': csimpy_task,
        'model_etree': model_etree,
        'variables': csimpy_variables,
    }
