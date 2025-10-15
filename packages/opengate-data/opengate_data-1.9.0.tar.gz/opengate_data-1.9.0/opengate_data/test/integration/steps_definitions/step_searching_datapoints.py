# opengate_data/test/integration/steps_definitions/step_searching_datapoints.py

from pytest_bdd import scenarios, given, parsers

scenarios("searching/searching_datapoints.feature")

@given(parsers.parse('I want to use a transpose'))
def given_device_identifier(builder_holder):
    builder_holder["instance"].with_transpose()


    