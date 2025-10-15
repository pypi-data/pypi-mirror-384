# opengate_data/test/integration/steps_definitions/step_rules.py

from pytest_bdd import scenarios, given, parsers, when
import ast

scenarios("rules/rules.feature")

#### ----- given ------

@given(parsers.parse('I want to use a code "{code}"'))
def step_with_code(builder_holder, code):
    builder_holder["instance"].with_code(code)

@given(parsers.parse('I want to use a parameters "{parameters}"'))
def step_with_parameters(builder_holder, parameters):
    builder_holder["instance"].with_parameters(ast.literal_eval(parameters))


#### ----- When ------

@when('I update parameters')
def step_update_parameters(builder_holder):
    builder_holder["instance"].update_parameters()

@when('I catalog')
def step_catalog(builder_holder):
    builder_holder["instance"].catalog()