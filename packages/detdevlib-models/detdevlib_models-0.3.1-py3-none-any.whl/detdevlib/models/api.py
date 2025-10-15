# packages/detdevlib-models/src/detdevlib/models/api.py

import json
import logging
import os
import shutil
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, Iterable, Type, TypeVar

import httpx
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from pydantic import BaseModel, create_model

FILENAME_PLACEHOLDER = "__PLACEHOLDER_FILENAME__"
logger = logging.getLogger(__name__)
ModelSettings = TypeVar("ModelSettings", bound=BaseModel)


class OutputModel(BaseModel):
    """A structured object for defining a single output file."""

    data: Any
    filename: str
    file_type: str
    path: str = ""

    def get_blob_dir(self):
        if self.path == "":
            return ""
        # Ensure no leading slash, and single trailing slash
        return f"{self.path.strip('/')}/"

    def get_blob_name(self):
        return f"{self.get_blob_dir()}{self.filename}.{self.file_type}"


class OutputFileHandler:
    """Class to handle output files for a model"""

    def __init__(self) -> None:
        logger.warning(
            "This class is deprecated and will be removed in a future version. Use temporary directories and Path data OutputModels instead."
        )
        self.base_path = Path("outputs") / datetime.now().strftime("%H_%M_%S")
        self.base_path.mkdir(parents=True, exist_ok=True)

    def __enter__(self):
        """Called when entering the 'with' block."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Called when exiting the 'with' block. Cleans up the directory."""
        self.delete_output_dir()

    def get_files(self) -> list[Path]:
        """Get a list of all files in the base_path directory."""
        return list(f for f in self.base_path.rglob("*") if f.is_file())

    def get_model_outputs(self) -> list[OutputModel]:
        """
        Get the model outputs as a list of OutputModel instances.
        All files are read as raw bytes.
        """
        output_models = []
        for file in self.get_files():
            relative_dir = file.parent.relative_to(self.base_path)
            output_model = OutputModel(
                data=file.read_bytes(),  # Read file content directly as bytes
                filename=file.stem,  # Filename without extension
                file_type=file.suffix.lstrip("."),  # File extension
                path=str(relative_dir) if str(relative_dir) != "." else "",  # Directory path
            )
            output_models.append(output_model)
        return output_models

    def delete_output_dir(self) -> None:
        """
        Delete the output directory and all its contents
        """
        if self.base_path.is_dir():
            shutil.rmtree(self.base_path)

    @staticmethod
    def split_away_first_dir(path: str) -> str:
        """Remove the first directory from the file path."""
        logger.warning("This method is deprecated and will be removed in a future version.")
        parts = path.split(os.sep)
        if len(parts) > 1:
            return os.sep.join(parts[1:])
        return path

    @staticmethod
    def read_data(path: str, type: str) -> Any:
        """Read data from a file based on its type"""
        logger.warning("This method is deprecated and will be removed in a future version.")
        if type == "csv":
            return pd.read_csv(path)
        elif type == "json":
            with open(path, "r") as f:
                return json.load(f)
        elif type == "html":
            with open(path, "r") as f:
                return f.read()
        elif type == "npz":
            with np.load(path) as data:
                return data["data"]
        raise NotImplementedError(f"File type {type} is not supported")


def _serialize(output: OutputModel) -> bytes:
    """Get the raw payload bytes"""
    if isinstance(output.data, bytes):
        return output.data
    if output.file_type == "csv" and isinstance(output.data, pd.DataFrame):
        return output.data.to_csv(index=False).encode("utf-8")
    if output.file_type == "json" and isinstance(output.data, dict):
        return json.dumps(output.data, indent=2).encode("utf-8")
    if output.file_type == "html" and isinstance(output.data, go.Figure):
        return output.data.to_html().encode("utf-8")
    if output.file_type == "npz" and isinstance(output.data, np.ndarray):
        buffer = BytesIO()
        np.savez_compressed(buffer, data=output.data)  # type: ignore
        buffer.seek(0)
        return buffer.read()
    if output.file_type == "parquet" and isinstance(output.data, pd.DataFrame):
        buffer = BytesIO()
        output.data.to_parquet(buffer, index=False)  # type: ignore
        buffer.seek(0)
        return buffer.read()
    raise NotImplementedError(
        f"serialization of type {type(output.data)} given file_type ({output.file_type}) is not supported"
    )


def _upload(sas_url: str, payload: bytes, blob_name: str) -> None:
    # Construct the full path and upload
    if FILENAME_PLACEHOLDER not in sas_url:
        raise ValueError(
            f"sas_url {sas_url} is missing filename placeholder {FILENAME_PLACEHOLDER}"
        )
    final_url = sas_url.replace(FILENAME_PLACEHOLDER, blob_name)

    # Upload the data to the sas url.
    response = httpx.put(final_url, content=payload, headers={"x-ms-blob-type": "BlockBlob"})
    response.raise_for_status()


def _process_output(sas_url: str, output: OutputModel) -> None:

    if isinstance(output.data, Path):
        if output.data.is_file():
            _upload(sas_url, output.data.read_bytes(), output.get_blob_name())
        elif output.data.is_dir():
            blob_dir = output.get_blob_dir()
            for file in output.data.rglob("*"):
                if file.is_file():
                    relative_path = file.relative_to(output.data)
                    blob_name = f"{blob_dir}{relative_path.as_posix()}"
                    _upload(sas_url, file.read_bytes(), blob_name)
        else:
            raise FileNotFoundError("File or directory not found")
    else:
        data = _serialize(output)
        _upload(sas_url, data, output.get_blob_name())


def create_model_api(
    model_function: Callable[[ModelSettings], Iterable[OutputModel]],
    settings_class: Type[ModelSettings],
    endpoint_path: str,
):
    """Factory to create a FastAPI app that handles model execution and output uploads."""
    from fastapi import BackgroundTasks, FastAPI, Response, status

    app = FastAPI(title=model_function.__name__)

    ConfigModel = create_model(
        "ConfigModel",
        task_id=(str, ...),
        output_sas_url=(str, ...),
        callback_url=(str, ...),
        model_settings=(settings_class, ...),
    )

    def _run_task_and_callback(config: ConfigModel):
        """Internal wrapper that runs the model, uploads the result, and handles callbacks."""
        try:
            for item in model_function(config.model_settings):
                _process_output(config.output_sas_url, item)

            message = f"Task finished."
            status = "COMPLETED"
        except Exception as e:
            message = f"An error occurred: {e}"
            status = "FAILED"

        callback_data = {"task_id": config.task_id, "status": status, "message": message}
        try:
            response = httpx.post(config.callback_url, json=callback_data)
            response.raise_for_status()
        except httpx.RequestError as e:
            # This catches network errors (e.g., connection refused, DNS failure)
            logger.warning(
                f"Callback for task {config.task_id} failed. Could not connect to {e.request.url!r}."
            )
        except httpx.HTTPStatusError as e:
            # This catches non-2xx server responses
            logger.warning(
                f"Callback for task {config.task_id} received an error response "
                f"{e.response.status_code} from server: {e.response.text}"
            )

    @app.post(endpoint_path, description=model_function.__doc__)
    async def main_endpoint(config: ConfigModel, background_tasks: BackgroundTasks):
        """Starts the model asynchronously, and respond with 202 to signal tasks have been started."""
        background_tasks.add_task(_run_task_and_callback, config)
        return Response(status_code=status.HTTP_202_ACCEPTED)

    @app.get("/healthcheck")
    async def healthcheck():
        """Used to verify if the app is available."""
        return {"status": "ok"}

    return app
