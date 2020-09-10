from enum import Enum
from math import *
from scipy import integrate
import matplotlib.pyplot as plt
from libcellml import *
import lxml.etree as ET

__version__ = "0.1.0"
LIBCELLML_VERSION = "0.2.0"

STATE_COUNT = 1
VARIABLE_COUNT = 29


class VariableType(Enum):
    CONSTANT = 1
    COMPUTED_CONSTANT = 2
    ALGEBRAIC = 3


VOI_INFO = {"name": "time", "units": "second", "component": "environment"}

STATE_INFO = [
    {"name": "pH_ext", "units": "dimensionless", "component": "Concentrations"}
]

VARIABLE_INFO = [
    {"name": "C_ext_NH4", "units": "mM", "component": "Concentrations", "type": VariableType.CONSTANT},
    {"name": "C_ext_Na", "units": "mM", "component": "Concentrations", "type": VariableType.CONSTANT},
    {"name": "C_int_H", "units": "mM", "component": "Concentrations", "type": VariableType.CONSTANT},
    {"name": "C_int_NH4", "units": "mM", "component": "Concentrations", "type": VariableType.CONSTANT},
    {"name": "C_int_Na", "units": "mM", "component": "Concentrations", "type": VariableType.CONSTANT},
    {"name": "K_NHE3_H", "units": "mM", "component": "NHE3_Parameters", "type": VariableType.CONSTANT},
    {"name": "K_NHE3_NH4", "units": "mM", "component": "NHE3_Parameters", "type": VariableType.CONSTANT},
    {"name": "K_NHE3_Na", "units": "mM", "component": "NHE3_Parameters", "type": VariableType.CONSTANT},
    {"name": "XTxP0_NHE3_H", "units": "nmol_per_s_per_cm2", "component": "NHE3_Parameters", "type": VariableType.CONSTANT},
    {"name": "XTxP0_NHE3_NH4", "units": "nmol_per_s_per_cm2", "component": "NHE3_Parameters", "type": VariableType.CONSTANT},
    {"name": "XTxP0_NHE3_Na", "units": "nmol_per_s_per_cm2", "component": "NHE3_Parameters", "type": VariableType.CONSTANT},
    {"name": "C_ext_H", "units": "mM", "component": "Concentrations", "type": VariableType.ALGEBRAIC},
    {"name": "alpha_ext_Na", "units": "dimensionless", "component": "NHE3", "type": VariableType.COMPUTED_CONSTANT},
    {"name": "beta_ext_H", "units": "dimensionless", "component": "NHE3", "type": VariableType.ALGEBRAIC},
    {"name": "gamma_ext_NH4", "units": "dimensionless", "component": "NHE3", "type": VariableType.COMPUTED_CONSTANT},
    {"name": "alpha_int_Na", "units": "dimensionless", "component": "NHE3", "type": VariableType.COMPUTED_CONSTANT},
    {"name": "beta_int_H", "units": "dimensionless", "component": "NHE3", "type": VariableType.COMPUTED_CONSTANT},
    {"name": "gamma_int_NH4", "units": "dimensionless", "component": "NHE3", "type": VariableType.COMPUTED_CONSTANT},
    {"name": "XTxP_NHE_Na", "units": "nmol_per_s_per_cm2", "component": "NHE3", "type": VariableType.COMPUTED_CONSTANT},
    {"name": "XTxP_NHE_H", "units": "nmol_per_s_per_cm2", "component": "NHE3", "type": VariableType.COMPUTED_CONSTANT},
    {"name": "XTxP_NHE_NH4", "units": "nmol_per_s_per_cm2", "component": "NHE3", "type": VariableType.COMPUTED_CONSTANT},
    {"name": "sum_NHE3", "units": "nmol_per_s_per_cm2", "component": "NHE3", "type": VariableType.ALGEBRAIC},
    {"name": "J_NHE3_Na", "units": "nmol_per_s_per_cm2", "component": "NHE3", "type": VariableType.ALGEBRAIC},
    {"name": "J_NHE3_H", "units": "nmol_per_s_per_cm2", "component": "NHE3", "type": VariableType.ALGEBRAIC},
    {"name": "J_NHE3_NH4", "units": "nmol_per_s_per_cm2", "component": "NHE3", "type": VariableType.ALGEBRAIC},
    {"name": "J_NHE3_Na_Max", "units": "nmol_per_s_per_cm2", "component": "NHE3", "type": VariableType.COMPUTED_CONSTANT},
    {"name": "plot_a", "units": "dimensionless", "component": "NHE3", "type": VariableType.ALGEBRAIC},
    {"name": "plot_b", "units": "dimensionless", "component": "NHE3", "type": VariableType.ALGEBRAIC},
    {"name": "K_H", "units": "dimensionless", "component": "NHE3", "type": VariableType.COMPUTED_CONSTANT}
]


def create_states_array():
    return [nan]*STATE_COUNT


def create_variables_array():
    return [nan]*VARIABLE_COUNT


def initialize_states_and_constants(states, variables):
    variables[0] = 0.0
    variables[1] = 0.1
    variables[2] = 1.0e-3
    variables[3] = 0.0
    variables[4] = 0.0
    variables[5] = 72.0e-6
    variables[6] = 0.027e3
    variables[7] = 30.0
    variables[8] = 0.48e-3
    variables[9] = 1.6e-3
    variables[10] = 1.6e-3
    states[0] = 6.0


def compute_computed_constants(variables):
    variables[12] = variables[1]/variables[7]
    variables[14] = variables[0]/variables[6]
    variables[15] = variables[4]/variables[7]
    variables[16] = variables[2]/variables[5]
    variables[17] = variables[3]/variables[6]
    variables[18] = variables[10]*2.0*variables[2]/(variables[2]+1.0e-6)
    variables[19] = variables[8]*2.0*variables[2]/(variables[2]+1.0e-6)
    variables[20] = variables[9]*2.0*variables[2]/(variables[2]+1.0e-6)
    variables[25] = variables[18]*variables[19]/(variables[18]+variables[19])
    variables[28] = ((1.0+variables[12])*variables[16]+(1.0+variables[16])*variables[12]*variables[18]/variables[19])/(1.0+2.0*variables[16])


def compute_rates(voi, states, rates, variables):
    rates[0] = 2.0


def compute_variables(voi, states, rates, variables):
    variables[11] = 1.0e3*pow(10.0, -states[0])
    variables[13] = variables[11]/variables[5]
    variables[21] = (1.0+variables[12]+variables[13]+variables[14])*(variables[18]*variables[15]+variables[19]*variables[16]+variables[20]*variables[17])+(1.0+variables[15]+variables[16]+variables[17])*(variables[18]*variables[12]+variables[19]*variables[13]+variables
[20]*variables[14])
    variables[22] = variables[18]*variables[19]/variables[21]*(variables[12]*variables[16]-variables[15]*variables[13])+variables[18]*variables[20]/variables[21]*(variables[12]*variables[17]-variables[15]*variables[14])
    variables[23] = variables[18]*variables[19]/variables[21]*(variables[15]*variables[13]-variables[12]*variables[16])+variables[19]*variables[20]/variables[21]*(variables[13]*variables[17]-variables[16]*variables[14])
    variables[24] = variables[18]*variables[20]/variables[21]*(variables[15]*variables[14]-variables[12]*variables[17])+variables[19]*variables[20]/variables[21]*(variables[14]*variables[16]-variables[13]*variables[17])
    variables[26] = variables[22]/variables[25]
    variables[27] = 1.0/variables[26]


# LSODA
start = 0.0
end = 1
numpoints = 1000

stepsize = (end - start) / numpoints
print(start, end, numpoints, stepsize)

states = create_states_array()
variables = create_variables_array()
initialize_states_and_constants(states, variables)

compute_computed_constants(variables) # added this line

temp = []
def func(t, y):
    rates = create_states_array()
    compute_rates(t, y, rates, variables)

    compute_variables(t, y, rates, variables) # added this line
    print("variables[22]: ", variables[22])
    temp.append(variables[22])

    return rates

print("start: ", start)
print("end: ", end)
print("states: ", states)
solution = integrate.solve_ivp(func,[start, end], states, method='LSODA', max_step=stepsize, atol=1e-4, rtol=1e-6)

print(solution.t)
print(solution.y)

# graph
fig, ax = plt.subplots()
ax.plot(solution.y[0], temp, label='Line 1')
ax.set_xlabel('t')
ax.set_ylabel('y')
ax.set_title('Some Title')
ax.legend()

fig.savefig('test.png')

# # test
# def exponential_decay(t, y):
#     return -0.5 * y
#
# sol = integrate.solve_ivp(exponential_decay, [0, 10], [2, 4, 8])
#
# print(sol.t)
# print(sol.y)
#
# fig2, ax2 = plt.subplots()
# ax2.plot(sol.t, sol.y[0], label='Line 1')
# ax2.plot(sol.t, sol.y[1], label='Line 2')
# ax2.plot(sol.t, sol.y[2], label='Line 3')
# ax2.set_xlabel('x label')
# ax2.set_ylabel('y label')
# ax2.set_title('Simple Plot')
# ax2.legend()
# fig2.savefig('test.png')

# convert cellml1.0 or 1.1 to 2.0
# with open('../tests/fixtures/chang_fujita_1999.xml') as f:
#     read_data = f.read()
# f.close()
#
# p = Parser()
# importedModel = p.parseModel(read_data)
#
# # parsing cellml 1.0 or 1.1 to 2.0
# dom = ET.fromstring(read_data.encode("utf-8"))
# xslt = ET.parse("../tests/fixtures/cellml1to2.xsl")
# transform = ET.XSLT(xslt)
# newdom = transform(dom)
#
# mstr = ET.tostring(newdom, pretty_print=True)
# mstr = mstr.decode("utf-8")
#
# # parse the string representation of the model to access by libcellml
# importedModel = p.parseModel(mstr)
#
# f = open('../tests/fixtures/chang_fujita_1999.xml', 'w')
# f.write(mstr)