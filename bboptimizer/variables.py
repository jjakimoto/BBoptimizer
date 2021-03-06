# -*- coding: utf-8 -*-
# @Author: tom-hydrogen
# @Date:   2018-03-02 14:11:04
# @Last Modified by:   tom-hydrogen
# @Last Modified time: 2018-03-07 12:07:59
import numpy as np
import math
from copy import deepcopy


class Variable(object):
    def __init__(self, name, var_type, domain, dimensionality):
        self.name = name
        self.domain = domain
        self.type = var_type
        self.dimensionality = dimensionality

    def is_continuous(self):
        return False

    def expand(self):
        """
        Builds a list of single dimensional variables representing current variable.
        Examples:
        For single dimensional variable, it is returned as is
        discrete of (0,2,4) -> discrete of (0,2,4)
        For multi dimensional variable, a list of variables is returned, each representing a single dimension
        continuous {0<=x<=1, 2<=y<=3} -> continuous {0<=x<=1}, continuous {2<=y<=3}
        """
        expanded_variables = []
        for i in range(self.dimensionality):
            one_d_variable = deepcopy(self)
            one_d_variable.dimensionality = 1
            if self.dimensionality > 1:
                one_d_variable.name = '{}_{}'.format(self.name, i + 1)
            else:
                one_d_variable.name = self.name
            one_d_variable.dimensionality_in_model = 1
            expanded_variables.append(one_d_variable)
        return expanded_variables

    def objective_to_model(self, x_objective):
        """
        Translates objective input to model input
        with respect to current variable
        """
        return [x_objective]

    def model_to_objective(self, x_model, index_in_model):
        """
        Translates model input to objective input
        with respect to current variable
        """
        return self.round([x_model[0][index_in_model]])

    def get_bounds(self):
        """
        Returns a list of tuples representing bounds of the variable
        """
        raise NotImplementedError()

    def get_possible_values(self):
        """
        Returns a list of possible variable values
        """
        raise NotImplementedError()

    def set_index_in_objective(self, index):
        """
        Allows to set the index of this variable in the objective space
        """
        self.index_in_objective = index

    def set_index_in_model(self, index):
        """
        Allows to set the index of this variable in the model space
        """
        self.index_in_model = index

    def round(self, value_array):
        """
        Rounds the given value to the variable's domain.
        Value is assumed to be in a 1x[variable dimentionality] numpy array
        """
        raise NotImplementedError()

    @property
    def model_dimensionality(self):
        return self.dimensionality


class NumericalVariable(Variable):
    def __init__(self, name, var_type, domain, dimensionality, scale=None):
        super(NumericalVariable, self).__init__(name, var_type, domain, dimensionality)
        if scale == 'log':
            self._domain = (math.log10(domain[0]), math.log10(domain[1]))
        else:
            self._domain = domain
        self.scale = scale

    def get_bounds(self):
        return [self._domain] * self.dimensionality

    def is_continuous(self):
        return True

    def get_possible_values(self):
        raise AttributeError("Impossible to produce a list of values for continuous variable " + self.name)

    def objective_to_model(self, x_objective):
        """
        Translates objective input to model input
        with respect to current variable
        """
        if self.scale == "log":
            x_objective = math.log10(x_objective)
        return [x_objective]

    def model_to_objective(self, x_model, index_in_model):
        """
        Translates model input to objective input
        with respect to current variable
        """

        val = x_model[0][index_in_model]
        if self.scale == 'log':
            val = 10 ** val
        return self.round([val])

    def round(self, value_array):
        """
        If value falls within bounds, just return it
        otherwise return min or max, whichever is closer to the value
        Assumes an 1d array with a single element as an input.
        """

        min_value = self.domain[0]
        max_value = self.domain[1]

        rounded_value = value_array[0]
        if rounded_value < min_value:
            rounded_value = min_value
        elif rounded_value > max_value:
            rounded_value = max_value
        return [rounded_value]


class ContinuousVariable(NumericalVariable):
    def __init__(self, name, domain, dimensionality=1, scale=None):
        super(ContinuousVariable, self).__init__(name, 'continuous', domain, dimensionality, scale)


class IntegerVariable(NumericalVariable):
    def __init__(self, name, domain, dimensionality=1, scale=None):
        super(IntegerVariable, self).__init__(name, 'integer', domain, dimensionality, scale)

    def round(self, value_array):
        """
        If value falls within bounds, just return it
        otherwise return min or max, whichever is closer to the value
        Assumes an 1d array with a single element as an input.
        """
        val = super(IntegerVariable, self).round(value_array)[0]
        return [int(round(val))]


class DiscreteVariable(Variable):
    def __init__(self, name, domain, dimensionality=1):
        super(DiscreteVariable, self).__init__(name, 'discrete', domain, dimensionality)

    def get_bounds(self):
        return [(min(self.domain), max(self.domain))]

    def get_possible_values(self):
        return self.domain

    def round(self, value_array):
        """
        Rounds a discrete variable by selecting the closest point in the domain
        Assumes an 1d array with a single element as an input.
        """
        value = value_array[0]
        rounded_value = self.domain[0]

        for domain_value in self.domain:
            if np.abs(domain_value - value) < np.abs(rounded_value - value):
                rounded_value = domain_value

        return [rounded_value]


class CategoricalVariable(Variable):
    def __init__(self, name, domain, dimensionality=1):
        super(CategoricalVariable, self).__init__(name, 'categorical', domain, dimensionality)
        self.scale = 1.

    def expand(self):
        expanded_variables = super(CategoricalVariable, self).expand()
        for v in expanded_variables:
            v.dimensionality_in_model = len(self.domain)
        return expanded_variables

    def objective_to_model(self, x_objective):
        entry = [0] * self.dimensionality_in_model
        idx = list(self.domain).index(x_objective)
        entry[int(idx)] = self.scale
        return entry

    def model_to_objective(self, x_model, index_in_model):
        vardim = self.dimensionality_in_model
        original_entry = np.array(x_model[0][index_in_model:(index_in_model + vardim)])
        original_entry = self.round([original_entry])
        entry = sum(x * y for x, y in zip(range(vardim), original_entry))
        entry = self.domain[int(entry)]
        return [entry]

    def get_bounds(self):
        return [(0.0, self.scale)] * self.dimensionality_in_model

    def get_possible_values(self):
        return np.eye(len(self.domain))

    def round(self, value_array):
        """
        Rounds a categorical variable by setting to one the max of the given vector and to zero the rest of the entries.
        Assumes an 1x[number of categories] array (due to one-hot encoding) as an input
        """
        value_array = value_array[0]
        rounded_values = np.zeros(value_array.shape)
        rounded_values[np.argmax(value_array)] = 1.
        return rounded_values

    @property
    def model_dimensionality(self):
        return self.dimensionality * len(self.domain)


class FixedVariable(Variable):
    def __init__(self, name, domain, dimensionality):
        super(FixedVariable, self).__init__(name, "fixed", domain, dimensionality)

    def get_bounds(self):
        return (self.domain,)


def create_variable(descriptor):
    """
    Creates a variable from a dictionary descriptor
    """
    if descriptor['type'] == 'continuous':
        return ContinuousVariable(descriptor['name'], descriptor['domain'], descriptor.get('dimensionality', 1), descriptor.get('scale', None))
    elif descriptor['type'] == 'integer':
        return IntegerVariable(descriptor['name'], descriptor['domain'], descriptor.get('dimensionality', 1), descriptor.get('scale', None))
    elif descriptor['type'] == 'discrete':
        return DiscreteVariable(descriptor['name'], descriptor['domain'], descriptor.get('dimensionality', 1))
    elif descriptor['type'] == 'categorical':
        return CategoricalVariable(descriptor['name'], descriptor['domain'], descriptor.get('dimensionality', 1))
    elif descriptor['type'] == 'fixed':
        return FixedVariable(descriptor['name'], descriptor['domain'], descriptor.get('dimensionality', 1))
    else:
        raise ValueError('Unknown variable type ' + descriptor['type'])
