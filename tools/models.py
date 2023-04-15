import os

from datamodel_code_generator import __main__ as dcg_main
from loguru import logger

JSON_RESPONSE_PATH = "./json/models"
OUTPUT_MODELS_PATH = "./govtech_data/models/resources/"


def generate_models():
    models = [
        os.path.join(JSON_RESPONSE_PATH, file)
        for file in os.listdir(JSON_RESPONSE_PATH)
        if file.endswith(".json")
    ]
    for model in models:
        filename, fileext = os.path.splitext(os.path.basename(model))
        model_classname = f'{"".join(i.capitalize() for i in filename.split("_"))}Model'
        output_filename = os.path.join(OUTPUT_MODELS_PATH, f"{filename}.py")
        logger.info(f"Generating {output_filename} from {model}...")
        dcg_main.main(
            args=[
                "--input",
                model,
                "--input-file-type",
                "json",
                "--output",
                output_filename,
                "--allow-extra-fields",
                "--use-default",
                "--force-optional",
                "--class-name",
                model_classname,
            ]
        )
