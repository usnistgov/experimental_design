#-----------------------------------------------------------------------------
# Name:        experimental_designs
# Purpose:    To make design of experiments easy (DOE).
# Authors:     aric.sanders@nist.gov
# Created:     4/20/2021
# License:     MIT License
#-----------------------------------------------------------------------------
"""experimental_designs is a module that acts as a collection point for tools to create and manage
design of experiments (DOE), or statistical design of experiments. Currently, it has
functions to produce fully factorial designs, with or without a center point, and in
the whole plot /split plot methods.
"""
#-----------------------------------------------------------------------------
# Standard Imports
import sys
import os
import random
import itertools
import yaml
import pandas as pd

#-----------------------------------------------------------------------------
# Module Constants
RANDOM_SEED = 42
#-----------------------------------------------------------------------------
# Module Functions
def pretty_print_np(array):
    """prints a numpy array the way I think looks best"""
    outstring = ""
    for index, element in enumerate(array):
        if index == len(array) - 1:
            outstring += str(element) + ""
        else:
            outstring += str(element) + ", "
    return outstring


def create_factor_table(dataframe):
    """Given a dataframe prints off the unique values for the column names,
    make sure the configuration number is index."""
    out_dictionary = {}
    for column in dataframe.columns:
        out_dictionary.update({column: dataframe[column].unique()})
    return out_dictionary


def print_factor_table(dataframe):
    """Given a dataframe prints off the unique values for the column names,
    make sure the configuration number is index."""
    for column in dataframe.columns:
        print("{0} : {1}".format(column, pretty_print_np(dataframe[column].unique())))


def jupyter_print_factor_table(dataframe, column_names=["Factors", "Values"]):
    """Pretty prints a factor table in a jupyter notebook"""
    from IPython.display import display, Markdown

    output_string = r"<table>" + "\n"
    heading = r"<TR><TH>{0}</TH><TH>{1}</TH></TR>".format(*column_names)
    output_string += heading + "\n"
    for column in dataframe.columns:
        output_string += r"<TR><TD>{0}</TD><TD>{1}</TD></TR>".format(column, pretty_print_np(
            sorted(dataframe[column].unique()))) + "\n"
    ending = r"</table>"
    output_string += ending
    display(Markdown(output_string))


def get_variable_factors(dataframe):
    """Given a dataframe, returns a list of factors that vary."""
    factors = [column for column in dataframe.columns if len(dataframe[column].unique()) > 1]
    return factors

def condition_in_row (row,condition):
    """Truth function for filter.
    Determines if condition is in row, returning True if it is not and False otherwise. """
    for condition_key,condition_value in condition.items():
        if row[condition_key]!=condition_value:
            return True
    return False

def filter_rows(design,exclusions):
    """Input a design of the form [{Row_1},...{RowN}] and an exclusions of the form [{exclusion_1}..
    {exclusion_N}] and returns a filter version of design."""
    out = design
    for excluded in exclusions:
        out = list(filter(lambda x: condition_in_row(x,excluded),out))
    return out

def fully_factorial(design_dictionary, randomized=True, run_values="values",random_seed = RANDOM_SEED):
    """Given a design_dictionary in the form {'factor_name_1':{factor_level_1:factor_level_value_1}, ...
    'factor_name_N':{factor_level_N:factor_level_value_N}}
    returns a test_conditions run sheet. Optional parameters are randomized (True or False) and run_values
    ("keys" or "values"). The randomization process sets a random_seed = RANDOM_SEED to be reproducible. """
    factors = list(design_dictionary.keys())
    factor_values = []
    for factor in factors:
        factor_values_row = list(design_dictionary[factor].__getattribute__(run_values)())
        factor_values.append(factor_values_row)
    test_conditions = [dict(zip(factors, state)) for state in itertools.product(*factor_values)]
    if randomized:
        random.seed(random_seed)
        random.shuffle(test_conditions)
    return test_conditions


def fully_factorial_default(design_dictionary, default_state, default_modulo=2,
                            randomized=True, run_values="values",random_seed =42):
    """Given a design_dictionary in the form {'factor_name_1':{factor_level_1:factor_level_value_1}, ...
    'factor_name_N':{factor_level_N:factor_level_value_N}} and a default state in the same format,
    returns a test_conditions run sheet. Optional parameters are default_modulo (how often do you want the state,
    randomized (True or False) and run_values.
    ("keys" or "values"). """

    test_conditions = fully_factorial(design_dictionary,
                                      randomized=randomized,
                                      run_values=run_values,
                                      random_seed=random_seed)
    factors = list(design_dictionary.keys())
    default_condition = {}
    for factor in factors:
        default_condition[factor] = list(default_state[factor].__getattribute__(run_values)())[0]
    defaulted_test_conditions = []
    for test_index, test_condition in enumerate(test_conditions):
        if test_index % default_modulo == 0:
            defaulted_test_conditions.append(default_condition)
            defaulted_test_conditions.append(test_condition)
        else:
            defaulted_test_conditions.append(test_condition)
    return defaulted_test_conditions


def fully_factorial_split_plot(whole_plot_design_dictionary, split_plot_design_dictionary,
                               randomized=True, run_values="values",random_seed_base = RANDOM_SEED):
    """Given a whole_plot_design_dictionary and split_plot_design_dictionary in the form {'factor_name_1':{factor_level_1:factor_level_value_1}, ...
    'factor_name_N':{factor_level_N:factor_level_value_N}} ,
    returns a test_conditions run sheet. Optional parameters are
    randomized (True or False) and run_values.
    ("keys" or "values"). """
    test_conditions = []
    whole_plot_test_conditions = fully_factorial(whole_plot_design_dictionary,
                                                 randomized=randomized,
                                                 run_values=run_values)
    for whole_plot_index,whole_plot in enumerate(whole_plot_test_conditions):
        split_plot_test_condtions = fully_factorial(split_plot_design_dictionary,
                                                    randomized=randomized,
                                                    run_values=run_values,
                                                    random_seed=random_seed_base+whole_plot_index)
        for split_plot in split_plot_test_condtions:
            new_row = dict(whole_plot)
            new_row.update(split_plot)
            test_conditions.append(new_row)
    return test_conditions


def fully_factorial_split_plot_default(whole_plot_design_dictionary, split_plot_design_dictionary,
                                       whole_plot_default_dictionary, whole_plot_default_modulo=2,
                                       randomized=True, run_values="values"):
    """Given a whole_plot_design_dictionary and split_plot_design_dictionary in the form {'factor_name_1':{factor_level_1:factor_level_value_1}, ...
    'factor_name_N':{factor_level_N:factor_level_value_N}} and a default state in the same format,
    returns a test_conditions run sheet. It assumes that the split plot design remains the same
    Optional parameters are default_modulo (how often do you want the state in whole plot iterations,
    randomized (True or False) and run_values.
    ("keys" or "values"). """
    # Build the fully factorial test and default conditions
    test_conditions = fully_factorial_split_plot(whole_plot_design_dictionary, split_plot_design_dictionary,
                                                 randomized=randomized, run_values=run_values)

    default_conditions = fully_factorial_split_plot(whole_plot_default_dictionary, split_plot_design_dictionary,
                                                    randomized=randomized, run_values=run_values)

    number_split_plot_states = 1
    for factor in split_plot_design_dictionary.keys():
        number_split_plot_states = number_split_plot_states * len(split_plot_design_dictionary[factor])
    state_modulo = int(whole_plot_default_modulo * number_split_plot_states)

    defaulted_test_conditions = []
    for test_index, test_condition in enumerate(test_conditions):
        if test_index % state_modulo == 0:
            for default_state in default_conditions:
                defaulted_test_conditions.append(default_state)
            defaulted_test_conditions.append(test_condition)
        else:
            defaulted_test_conditions.append(test_condition)
    return defaulted_test_conditions

def fully_factorial_split_plot_interleaved(whole_plot_design_dictionary, split_plot_design_dictionary,
                                       whole_plot_design_dictionary_interleaved,
                                       split_plot_design_dictionary_interleaved,
                                       interleave_modulo=2,
                                       randomized=True, run_values="values"):
    """Given whole_plot_design_dictionary, split_plot_design_dictionary,
    whole_plot_design_dictionary_interleaved, split_plot_design_dictionary_interleaved in the form {'factor_name_1':{factor_level_1:factor_level_value_1}, ...
    'factor_name_N':{factor_level_N:factor_level_value_N}},
    returns a test_conditions run sheet. It assumes that the split plot design remains the same
    Optional parameters are interleave_modulo (how often do you want the state in whole plot iterations,
    randomized (True or False) and run_values.
    ("keys" or "values"). """
    # Build the fully factorial test and default conditions
    test_conditions = fully_factorial_split_plot(whole_plot_design_dictionary, split_plot_design_dictionary,
                                                 randomized=randomized, run_values=run_values)

    # does this lead to a different randomization each time? -NO


    number_split_plot_states = 1
    for factor in split_plot_design_dictionary.keys():
        number_split_plot_states = number_split_plot_states * len(split_plot_design_dictionary[factor])
    state_modulo = int(interleave_modulo * number_split_plot_states)

    interleaved_test_conditions = []
    for test_index, test_condition in enumerate(test_conditions):
        if test_index % state_modulo == 0:
            interleave_conditions = fully_factorial_split_plot(whole_plot_design_dictionary_interleaved,
                                                               split_plot_design_dictionary_interleaved,
                                                               randomized=randomized,
                                                               run_values=run_values,
                                                               random_seed_base=test_index)
            for interleave_state in interleave_conditions:
                interleaved_test_conditions.append(interleave_state)
            interleaved_test_conditions.append(test_condition)
        else:
            interleaved_test_conditions.append(test_condition)
    return interleaved_test_conditions

#-----------------------------------------------------------------------------
# Module Scripts
def test_fully_factorial():
    """Tests the fully_factorial design"""
    test_design = {'one': {0: 'LOW', 1: 'HIGH', 2: 'zest'}, 'two': {0: 'FAST', 1: 'SLOW'}, 'three': {0: 'ON'}}
    print("*"*80)
    print("Testing the fully_factorial function")
    print(f"The test design is {yaml.dump(test_design)}")
    test_condtions  = pd.DataFrame(fully_factorial(test_design, randomized=False))
    test_condtions_keys = pd.DataFrame(fully_factorial(test_design, randomized=False, run_values="keys"))
    random_test_condtions = pd.DataFrame(fully_factorial(test_design, randomized=True))
    print("The test_conditions or design when not randomized is:")
    print(test_condtions)
    print("*"*80)
    print("The test_conditions or design in state numbers when not randomized is:")
    print(test_condtions_keys)
    print("*" * 80)
    print("The test_conditions or design randomized is:")
    print(random_test_condtions)
    print("*" * 80)

def test_fully_factorial_default():
    """Tests the fully_factorial_default design"""
    test_design = {'one': {0: 'LOW', 1: 'HIGH', 2: 'zest'}, 'two': {0: 'FAST', 1: 'SLOW'}, 'three': {0: 'ON'}}
    default = {'one': {-1: 'default'}, 'two': {-1: 'MEDIUM'}, 'three': {-1: 'OFF'}}
    print("*"*80)
    print("Testing the fully_factorial_default function")
    print(f"The test design is {yaml.dump(test_design)}")
    print(f"The default is {yaml.dump(default)}")
    test_condtions  = pd.DataFrame(fully_factorial_default(test_design, default , randomized=False))
    test_condtions_keys = pd.DataFrame(fully_factorial_default(test_design, default, randomized=False, run_values="keys"))
    random_test_condtions = pd.DataFrame(fully_factorial_default(test_design, default, randomized=True))
    print("The test_conditions or design when not randomized is:")
    print(test_condtions)
    print("*"*80)
    print("The test_conditions or design in state numbers when not randomized is:")
    print(test_condtions_keys)
    print("*" * 80)
    print("The test_conditions or design randomized is:")
    print(random_test_condtions)
    print("*" * 80)

def test_fully_factorial_split_plot():
    """Tests the fully_factorial_split_plot_default design"""
    test_design = {'one': {0: 'LOW', 1: 'HIGH', 2: 'zest'}, 'two': {0: 'FAST', 1: 'SLOW'}, 'three': {0: 'ON'}}
    wp = {'whole_plot_1': {-1: "in my shoe", 0: 'In my Head'}, 'whole_plot_2': {0: 'WP OFF', 1: "WP ON"}}
    print("*"*80)
    print("Testing the test_fully_factorial_split_plot_default function")
    print(f"The test design is {yaml.dump(test_design)}")
    print(f"The whole plot design is {yaml.dump(wp)}")

    test_condtions  = pd.DataFrame(fully_factorial_split_plot(whole_plot_design_dictionary=wp,
                                                                      split_plot_design_dictionary = test_design,
                                                                      randomized=False))
    test_condtions_keys = pd.DataFrame(fully_factorial_split_plot(whole_plot_design_dictionary=wp,
                                                                      split_plot_design_dictionary = test_design,
                                                                      randomized=False,
                                                                      run_values="keys"))
    random_test_condtions = pd.DataFrame(fully_factorial_split_plot(whole_plot_design_dictionary=wp,
                                                                      split_plot_design_dictionary = test_design,
                                                                      randomized=True,
                                                                      run_values="values"))
    print("The test_conditions or design when not randomized is:")
    print(test_condtions)
    print("*"*80)
    print("The test_conditions or design in state numbers when not randomized is:")
    print(test_condtions_keys)
    print("*" * 80)
    print("The test_conditions or design randomized is:")
    print(random_test_condtions)
    print("*" * 80)

def test_fully_factorial_split_plot_default():
    """Tests the fully_factorial_split_plot_default design"""

    test_design = {'one': {0: 'LOW', 1: 'HIGH', 2: 'zest'}, 'two': {0: 'FAST', 1: 'SLOW'}, 'three': {0: 'ON'}}
    wp = {'whole_plot_1': {-1: "in my shoe", 0: 'In my Head'}, 'whole_plot_2': {0: 'WP OFF', 1: "WP ON"}}
    wp_default = {'whole_plot_1': {3: "default"}, 'whole_plot_2': {0: 'wp_2 default'}}
    print("*"*80)
    print("Testing the test_fully_factorial_split_plot_default function")
    print(f"The test design is {yaml.dump(test_design)}")
    print(f"The whole plot design is {yaml.dump(wp)}")
    print(f"The whole plot default is {yaml.dump(wp_default)}")

    test_condtions  = pd.DataFrame(fully_factorial_split_plot_default(whole_plot_design_dictionary=wp,
                                                                      split_plot_design_dictionary = test_design,
                                                                      whole_plot_default_dictionary=wp_default ,
                                                                      randomized=False))
    test_condtions_keys = pd.DataFrame(fully_factorial_split_plot_default(whole_plot_design_dictionary=wp,
                                                                      split_plot_design_dictionary = test_design,
                                                                      whole_plot_default_dictionary=wp_default ,
                                                                      randomized=False,
                                                                      run_values="keys"))
    random_test_condtions = pd.DataFrame(fully_factorial_split_plot_default(whole_plot_design_dictionary=wp,
                                                                      split_plot_design_dictionary = test_design,
                                                                      whole_plot_default_dictionary=wp_default ,
                                                                      randomized=True,
                                                                      run_values="values"))
    print("The test_conditions or design when not randomized is:")
    print(test_condtions)
    print("*"*80)
    print("The test_conditions or design in state numbers when not randomized is:")
    print(test_condtions_keys)
    print("*" * 80)
    print("The test_conditions or design randomized is:")
    print(random_test_condtions)
    print("*" * 80)

def test_fully_factorial_split_plot_interleave():
    """Tests the fully_factorial_split_plot_default design"""
    sp = {'one': {0: 'LOW', 1: 'HIGH', 2: 'zest'}, 'two': {0: 'FAST', 1: 'SLOW'}, 'three': {0: 'ON'}}
    wp = {'whole_plot_1': {-1: "in my shoe", 0: 'In my Head'}, 'whole_plot_2': {0: 'WP OFF', 1: "WP ON"}}
    wp_2 = {'whole_plot_1': {3: "default"}, 'whole_plot_2': {0: 'wp_2 default'}}
    sp_2 = {'Atten': {0: 0, 1: 20, 2: 40}, 'two': {0: 'NEW', 1: 'OLD'}, 'three': {0: 'OFF'}}
    print("*"*80)
    print("Testing the test_fully_factorial_split_plot_default function")
    print(f"The whole plot design is {yaml.dump(wp)}")
    print(f"The split plot design is {yaml.dump(sp)}")

    print(f"The second whole plot default is {yaml.dump(wp_2)}")
    print(f"The second split plot default is {yaml.dump(sp_2)}")

    test_condtions  = pd.DataFrame(fully_factorial_split_plot_interleaved(whole_plot_design_dictionary=wp,
                                                                      split_plot_design_dictionary = sp,
                                                                      whole_plot_design_dictionary_interleaved= wp_2 ,
                                                                      split_plot_design_dictionary_interleaved = sp_2,
                                                                      randomized=False))
    test_condtions_keys = pd.DataFrame(fully_factorial_split_plot_interleaved(whole_plot_design_dictionary=wp,
                                                                      split_plot_design_dictionary = sp,
                                                                      whole_plot_design_dictionary_interleaved= wp_2 ,
                                                                      split_plot_design_dictionary_interleaved = sp_2,
                                                                      randomized=False,
                                                                      run_values='keys'))
    random_test_condtions = pd.DataFrame(fully_factorial_split_plot_interleaved(whole_plot_design_dictionary=wp,
                                                                      split_plot_design_dictionary = sp,
                                                                      whole_plot_design_dictionary_interleaved= wp_2 ,
                                                                      split_plot_design_dictionary_interleaved = sp_2,
                                                                      randomized=True,
                                                                      run_values='values'))
    print("The test_conditions or design when not randomized is:")
    print(test_condtions)
    print("*"*80)
    print("The test_conditions or design in state numbers when not randomized is:")
    print(test_condtions_keys)
    print("*" * 80)
    print("The test_conditions or design randomized is:")
    print(random_test_condtions)
    print("*" * 80)

#-----------------------------------------------------------------------------
# Module Runner
if __name__ == '__main__':
    test_fully_factorial()
    test_fully_factorial_default()
    test_fully_factorial_split_plot()
    test_fully_factorial_split_plot_interleave()
 