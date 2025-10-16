from typing import Annotated

import typer
from dotenv import load_dotenv
from langsmith import Client

from evals.dataset import load_dataset

load_dotenv()

app = typer.Typer()


@app.command("upload-runs")
def upload_runs_to_dataset(
    project_name: Annotated[str, typer.Option("--project-name", help="The LangSmith project name.")],
    dataset_name: Annotated[str, typer.Option("--dataset-name", help="The target dataset name.")],
    dataset_description: Annotated[
        str,
        typer.Option("--dataset-description", help="Description for the dataset."),
    ] = "Dataset from project runs.",
):
    """
    Uploads runs from a LangSmith project to a dataset.
    """
    client = Client()
    try:
        dataset = client.create_dataset(dataset_name, description=dataset_description)
    except Exception:
        dataset = client.read_dataset(dataset_name=dataset_name)

    runs = client.list_runs(project_name=project_name)

    for run in runs:
        client.create_example(
            inputs=run.inputs,
            outputs=run.outputs,
            dataset_id=dataset.id,
        )


@app.command("upload-file")
def upload_dataset_from_file(
    file_path: Annotated[
        str,
        typer.Option("--file-path", help="Path to the local dataset file (CSV or JSONL)."),
    ],
    dataset_name: Annotated[
        str,
        typer.Option("--dataset-name", help="The name for the dataset in LangSmith."),
    ],
    input_keys: Annotated[
        list[str],
        typer.Option("--input-keys", help="Comma-separated list of input column names."),
    ],
    output_keys: Annotated[
        list[str],
        typer.Option("--output-keys", help="Comma-separated list of output column names."),
    ],
    dataset_description: Annotated[
        str,
        typer.Option("--dataset-description", help="Description for the dataset."),
    ] = "Dataset uploaded from file.",
):
    """
    Uploads a dataset from a local file (CSV or JSONL) to LangSmith.
    """
    client = Client()
    examples = load_dataset(file_path)

    try:
        dataset = client.create_dataset(dataset_name, description=dataset_description)
    except Exception:
        dataset = client.read_dataset(dataset_name=dataset_name)

    for example in examples:
        inputs = {key: example[key] for key in input_keys if key in example}
        outputs = {key: example[key] for key in output_keys if key in example}
        client.create_example(inputs=inputs, outputs=outputs, dataset_id=dataset.id)


if __name__ == "__main__":
    app()
