from jsoneditor.forms import JSONEditor

default_json_editor_widget = JSONEditor(
    init_options={"mode": "code", "modes": ["view", "code", "tree"]},
)
