import json

from cattle_grid.model.exchange import UpdateActorMessage


model_name_to_model = {"UpdateActorMessage": UpdateActorMessage}


def json_schema_for_model(model_name: str):
    model = model_name_to_model[model_name]

    schema = model.model_json_schema()
    print(json.dumps(schema, indent=2))
