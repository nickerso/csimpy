""" Data model for OpenCOR algorithms and their parameters

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-28
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from biosimulators_utils.data_model import ValueType
import collections
import enum

__all__ = [
    'KISAO_ALGORITHM_MAP',
]


KISAO_ALGORITHM_MAP = collections.OrderedDict([
    ('KISAO_0000030', {
        'kisao_id': 'KISAO_0000030',
        'id': 'forward-euler',
        'name': 'Forward Euler method',
        'parameters': {
            'KISAO_0000483': {
                'id': 'step',
                'name': 'step',
                'type': ValueType.float,
                'default': 1.,
            },
        },
    }),
])
