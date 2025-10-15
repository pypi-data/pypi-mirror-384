# opengate_data/test/integration/steps_definitions/step_ia.py

from pytest_bdd import scenarios, given, parsers, when, then
import ast
import time
import os
from opengate_data.test.utils.path_resolver import resolve_test_path

# Se dejan comentados debido a que en backend actualmente se ha quitado el soporte de IA devuelve un 503
# scenarios("ia/model.feature")
# scenarios("ia/transformers.feature")
# scenarios("ia/pipelines.feature")


# ---- Given ----

@given(parsers.parse('I want to use an artificial intelligence file "{file}"'))
def step_file(builder_holder, file):
    file_path = resolve_test_path(file)
    builder_holder["instance"].add_file(str(file_path))

@given(parsers.parse('I want to download with name "{name}"'))
def step_save_outuput_file(builder_holder, name):
    out_path = resolve_test_path(name)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    builder_holder["instance"].with_output_file_path(str(out_path))

@given(parsers.parse('I want to use a prediction "{prediction}"'))
def step_prediction_code(builder_holder, prediction):
    predic = ast.literal_eval(prediction)
    builder_holder["instance"].with_prediction(predic)

@given(parsers.parse('I want to use a file name download transform "{file_name}"'))
def step_file_name(builder_holder, file_name):
    file_path = resolve_test_path(file_name)
    builder_holder["instance"].with_file_name(str(file_path))

@given(parsers.parse('I want add action "{add_action}"'))
def step_add_action(builder_holder, add_action):
    builder_holder["instance"].add_action(add_action)

# ---- When ----

@when('I validate')
def step_validate(builder_holder):
    builder_holder["instance"].validate()
    time.sleep(2)

@when('I prediction')
def step_prediction(builder_holder):
    builder_holder["instance"].prediction()
    time.sleep(2)

@when('I download')
def step_download(builder_holder):
    builder_holder["instance"].download().build().execute()
    time.sleep(2)

@when('I save')
def step_save(builder_holder):
    builder_holder["instance"].save()
    time.sleep(2)

@when(parsers.parse('I want to remove with name "{name}"'))
def step_remove_outuput_file(name):
    current_file = resolve_test_path(name)
    if current_file.exists():
        os.remove(current_file)


# ---- Then ----

@then(parsers.parse('The prediction should be {prediction}'))
def step_prediction_result(builder_holder, prediction):
    response = builder_holder["instance"].build().execute()
    predic = ast.literal_eval(prediction)
    builder_holder["instance"].with_prediction(predic)
    assert response['data'] == predic
    time.sleep(2)
