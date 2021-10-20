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
    'VodeIntegrationMethod',
    'KISAO_ALGORITHM_MAP',
]

class VodeIntegrationMethod(str, enum.Enum):
    """ VODE integration method """
    KISAO_0000288 = 'BDF'
    KISAO_0000280 = 'Adams'


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
    ('KISAO_0000535', {
        'kisao_id': 'KISAO_0000535',
        'id': 'vode',
        'name': 'VODE',
        'parameters': {
            'KISAO_0000209': {
                'id': 'RelativeToleranceId',
                'name': 'relative tolerance',
                'type': ValueType.float,
                'default': 1e-7,
            },
            'KISAO_0000211': {
                'id': 'AbsoluteToleranceId',
                'name': 'absolute tolerance',
                'type': ValueType.float,
                'default': 1e-7,
            },
            'KISAO_0000475': {
                'id': 'IntegrationMethodId',
                'name': 'integration method',
                'type': ValueType.string,
                'default': VodeIntegrationMethod.KISAO_0000288.name,
                'enum': VodeIntegrationMethod,
            },
            'KISAO_0000415': {
                'id': 'MaximumNumberOfStepsId',
                'name': 'maximum number of steps',
                'type': ValueType.integer,
                'default': 500,
            },
            'KISAO_0000467': {
                'id': 'MaximumStepId',
                'name': 'maximum step',
                'type': ValueType.float,
                'default': 0.,
            },
            'KISAO_0000485': {
                'id': 'MinimumStepId',
                'name': 'minimum step',
                'type': ValueType.float,
                'default': 0.,
            },
            'KISAO_0000484': {
                'id': 'MaximumOrderId',
                'name': 'maximum order',
                'type': ValueType.integer,
                'default': 12,
            },
        },
    }),
    ('KISAO_0000088', {
        'kisao_id': 'KISAO_0000088',
        'id': 'lsoda',
        'name': 'LSODA',
        'parameters': {
            'KISAO_0000209': {
                'id': 'RelativeToleranceId',
                'name': 'relative tolerance',
                'type': ValueType.float,
                'default': 1e-7,
            },
            'KISAO_0000211': {
                'id': 'AbsoluteToleranceId',
                'name': 'absolute tolerance',
                'type': ValueType.float,
                'default': 1e-7,
            },
            'KISAO_0000415': {
                'id': 'MaximumNumberOfStepsId',
                'name': 'maximum number of steps',
                'type': ValueType.integer,
                'default': 500,
            },
            'KISAO_0000467': {
                'id': 'MaximumStepId',
                'name': 'maximum step',
                'type': ValueType.float,
                'default': 0.,
            },
            'KISAO_0000485': {
                'id': 'MinimumStepId',
                'name': 'minimum step',
                'type': ValueType.float,
                'default': 0.,
            },
            'KISAO_0000219': {
                'id': 'MaximumAdamsOrderId',
                'name': 'maximum Adams order',
                'type': ValueType.integer,
                'default': 12,
            },
            'KISAO_0000220': {
                'id': 'MaximumBDFOrderId',
                'name': 'maximum BDF order',
                'type': ValueType.integer,
                'default': 5,
            },
        },
    }),
    ('KISAO_0000087', {
        'kisao_id': 'KISAO_0000087',
        'id': 'dopri5',
        'name': 'DOPRI5',
        'parameters': {
            'KISAO_0000209': {
                'id': 'RelativeToleranceId',
                'name': 'relative tolerance',
                'type': ValueType.float,
                'default': 1e-7,
            },
            'KISAO_0000211': {
                'id': 'AbsoluteToleranceId',
                'name': 'absolute tolerance',
                'type': ValueType.float,
                'default': 1e-7,
            },
            'KISAO_0000415': {
                'id': 'MaximumNumberOfStepsId',
                'name': 'maximum number of steps',
                'type': ValueType.integer,
                'default': 500,
            },
            'KISAO_0000467': {
                'id': 'MaximumStepId',
                'name': 'maximum step',
                'type': ValueType.float,
                'default': 0.,
            },
            'KISAO_0000541': {
                'id': 'BetaId',
                'name': 'beta parameter for stabilized step size control',
                'type': ValueType.float,
                'default': 0.,
            },
        },
    }),
    ('KISAO_0000436', {
        'kisao_id': 'KISAO_0000436',
        'id': 'dop853',
        'name': 'Dormand-Prince 8(5,3) method',
        'parameters': {
            'KISAO_0000209': {
                'id': 'RelativeToleranceId',
                'name': 'relative tolerance',
                'type': ValueType.float,
                'default': 1e-7,
            },
            'KISAO_0000211': {
                'id': 'AbsoluteToleranceId',
                'name': 'absolute tolerance',
                'type': ValueType.float,
                'default': 1e-7,
            },
            'KISAO_0000415': {
                'id': 'MaximumNumberOfStepsId',
                'name': 'maximum number of steps',
                'type': ValueType.integer,
                'default': 500,
            },
            'KISAO_0000467': {
                'id': 'MaximumStepId',
                'name': 'maximum step',
                'type': ValueType.float,
                'default': 0.,
            },
            'KISAO_0000541': {
                'id': 'BetaId',
                'name': 'beta parameter for stabilized step size control',
                'type': ValueType.float,
                'default': 0.,
            },
        },
    }),
])
