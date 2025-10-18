from __future__ import annotations
import os
import io
import zipfile
import mimetypes
from contextlib import contextmanager
from loguru import logger
from hypothesis_jsonschema import from_schema
from typing import TYPE_CHECKING, Sequence, Any
from pathlib import Path

from adaptive_sdk.graphql_client.fragments import JobData
from adaptive_sdk.graphql_client.input_types import JobInput

from .base_resource import SyncAPIResource, AsyncAPIResource, UseCaseResource
from adaptive_sdk.graphql_client import (
    CustomRecipeData,
    CustomRecipeFilterInput,
    CreateRecipeInput,
    UpdateRecipeInput,
    LabelInput,
    Upload,
)

if TYPE_CHECKING:
    from adaptive_sdk.client import Adaptive, AsyncAdaptive


class Recipes(SyncAPIResource, UseCaseResource):  # type: ignore[misc]
    """
    Resource to interact with custom scripts.
    """

    def __init__(self, client: Adaptive) -> None:
        SyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    def list(self, use_case: str | None = None) -> Sequence[CustomRecipeData]:
        filter = CustomRecipeFilterInput()
        return self._gql_client.list_custom_recipes(use_case=self.use_case_key(use_case), filter=filter).custom_recipes

    def upload(
        self,
        path: str,
        recipe_key: str,
        name: str | None = None,
        description: str | None = None,
        labels: dict[str, str] | None = None,
        use_case: str | None = None,
    ) -> CustomRecipeData:
        """
        Upload a recipe from either a single Python file or a directory (path).
        If a directory is provided, it must contain a 'main.py' and will be zipped in-memory before upload.
        """
        inferred_name = name or recipe_key
        label_inputs = [LabelInput(key=k, value=v) for k, v in labels.items()] if labels else None
        input = CreateRecipeInput(
            key=recipe_key,
            name=inferred_name,
            description=description,
            labels=label_inputs,
        )
        with _upload_from_path(path) as file_upload:
            return self._gql_client.create_custom_recipe(
                use_case=self.use_case_key(use_case), input=input, file=file_upload
            ).create_custom_recipe

    def get(
        self,
        recipe_key: str,
        use_case: str | None = None,
    ) -> CustomRecipeData | None:
        return self._gql_client.get_custom_recipe(
            id_or_key=recipe_key, use_case=self.use_case_key(use_case)
        ).custom_recipe

    def update(
        self,
        recipe_key: str,
        path: str | None = None,
        name: str | None = None,
        description: str | None = None,
        labels: Sequence[tuple[str, str]] | None = None,
        use_case: str | None = None,
    ) -> CustomRecipeData:
        label_inputs = [LabelInput(key=k, value=v) for k, v in labels] if labels else None
        input = UpdateRecipeInput(
            name=name,
            description=description,
            labels=label_inputs,
        )

        if path:
            with _upload_from_path(path) as file_upload:
                return self._gql_client.update_custom_recipe(
                    use_case=self.use_case_key(use_case),
                    id=recipe_key,
                    input=input,
                    file=file_upload,
                ).update_custom_recipe
        else:
            return self._gql_client.update_custom_recipe(
                use_case=self.use_case_key(use_case),
                id=recipe_key,
                input=input,
                file=None,
            ).update_custom_recipe

    def delete(
        self,
        recipe_key: str,
        use_case: str | None = None,
    ) -> bool:
        return self._gql_client.delete_custom_recipe(
            use_case=self.use_case_key(use_case), id=recipe_key
        ).delete_custom_recipe

    def generate_sample_input(self, recipe_key: str, use_case: str | None = None) -> dict:
        recipe_details = self.get(recipe_key=recipe_key, use_case=self.use_case_key(use_case))
        if recipe_details is None:
            raise ValueError(f"Recipe {recipe_key} was not found")
        strategy = from_schema(recipe_details.json_schema)

        best_example = None
        max_key_count = -1

        for _ in range(10):
            try:
                example = strategy.example()
                current_key_count = _count_keys_recursively(example)

                if current_key_count > max_key_count:
                    max_key_count = current_key_count
                    best_example = example
            except Exception as e:
                print(f"Warning: Failed to generate an example due to: {e}")
                # Continue to next iteration even if one example fails

        if best_example is None:
            print("A valid sample could not be generated. Returning an empty dict.")
            best_example = {}
        return dict(best_example)  # type: ignore


class AsyncRecipes(AsyncAPIResource, UseCaseResource):  # type: ignore[misc]
    """
    Resource to interact with custom scripts.
    """

    def __init__(self, client: AsyncAdaptive) -> None:
        AsyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    async def list(self, use_case: str | None = None) -> Sequence[CustomRecipeData]:
        filter = CustomRecipeFilterInput()
        return (
            await self._gql_client.list_custom_recipes(use_case=self.use_case_key(use_case), filter=filter)
        ).custom_recipes

    async def upload(
        self,
        path: str,
        recipe_key: str,
        name: str | None = None,
        description: str | None = None,
        labels: Sequence[tuple[str, str]] | None = None,
        use_case: str | None = None,
    ) -> CustomRecipeData:
        inferred_name = name or recipe_key
        label_inputs = [LabelInput(key=k, value=v) for k, v in labels] if labels else None
        input = CreateRecipeInput(
            key=recipe_key,
            name=inferred_name,
            description=description,
            labels=label_inputs,
        )
        with _upload_from_path(path) as file_upload:
            return (
                await self._gql_client.create_custom_recipe(
                    use_case=self.use_case_key(use_case), input=input, file=file_upload
                )
            ).create_custom_recipe

    async def get(
        self,
        recipe_key: str,
        use_case: str | None = None,
    ) -> CustomRecipeData | None:
        return (
            await self._gql_client.get_custom_recipe(id_or_key=recipe_key, use_case=self.use_case_key(use_case))
        ).custom_recipe

    async def update(
        self,
        recipe_key: str,
        path: str | None = None,
        name: str | None = None,
        description: str | None = None,
        labels: Sequence[tuple[str, str]] | None = None,
        use_case: str | None = None,
    ) -> CustomRecipeData:
        label_inputs = [LabelInput(key=k, value=v) for k, v in labels] if labels else None
        input = UpdateRecipeInput(
            name=name,
            description=description,
            labels=label_inputs,
        )

        if path:
            with _upload_from_path(path) as file_upload:
                return (
                    await self._gql_client.update_custom_recipe(
                        use_case=self.use_case_key(use_case),
                        id=recipe_key,
                        input=input,
                        file=file_upload,
                    )
                ).update_custom_recipe
        else:
            return (
                await self._gql_client.update_custom_recipe(
                    use_case=self.use_case_key(use_case),
                    id=recipe_key,
                    input=input,
                    file=None,
                )
            ).update_custom_recipe

    async def delete(
        self,
        recipe_key: str,
        use_case: str | None = None,
    ) -> bool:
        return (
            await self._gql_client.delete_custom_recipe(use_case=self.use_case_key(use_case), id=recipe_key)
        ).delete_custom_recipe

    async def generate_sample_input(self, recipe_key: str, use_case: str | None = None) -> dict:
        recipe_details = await self.get(recipe_key=recipe_key, use_case=self.use_case_key(use_case))
        if recipe_details is None:
            raise ValueError(f"Recipe {recipe_key} was not found")
        strategy = from_schema(recipe_details.json_schema)

        best_example = None
        max_key_count = -1

        for _ in range(10):
            try:
                example = strategy.example()
                current_key_count = _count_keys_recursively(example)

                if current_key_count > max_key_count:
                    max_key_count = current_key_count
                    best_example = example
            except Exception as e:
                print(f"Warning: Failed to generate an example due to: {e}")
                # Continue to next iteration even if one example fails

        if best_example is None:
            print("A valid sample could not be generated. Returning an empty dict.")
            best_example = {}
        return dict(best_example)  # type: ignore


def _count_keys_recursively(data: Any) -> int:
    """Recursively counts the total number of keys in dictionaries within the data."""
    count = 0
    if isinstance(data, dict):
        count += len(data)
        for value in data.values():
            count += _count_keys_recursively(value)
    elif isinstance(data, list):
        for item in data:
            count += _count_keys_recursively(item)
    return count


def _validate_python_file(path: Path) -> None:
    """Validate that the path exists, is a file and has a .py extension."""
    if not path.exists():
        raise FileNotFoundError(f"Python file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Expected a file path, got a directory or non-file: {path}")
    if path.suffix.lower() != ".py":
        raise ValueError(f"Expected a Python file with .py extension, got: {path}")


def _validate_recipe_directory(dir_path: Path) -> None:
    """Validate that the directory exists and contains a main.py file."""
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    if not dir_path.is_dir():
        raise ValueError(f"Expected a directory path, got a file: {dir_path}")
    main_py = dir_path / "main.py"
    if not main_py.exists() or not main_py.is_file():
        raise FileNotFoundError(f"Directory must contain a 'main.py' file: {dir_path}")


def _zip_directory_to_bytes_io(dir_path: Path) -> io.BytesIO:
    """Zip the contents of a directory into an in-memory BytesIO buffer."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(dir_path):
            for file_name in files:
                file_path = Path(root) / file_name
                arcname = file_path.relative_to(dir_path)
                zf.write(file_path, arcname.as_posix())
    buffer.seek(0)
    return buffer


@contextmanager
def _upload_from_path(path: str):
    """
    Context manager yielding an Upload object for a Python file or a directory.

    - If path is a .py file, validates and opens it for upload.
    - If path is a directory, validates it contains main.py, zips contents in-memory.
    """
    p = Path(path)
    if p.is_file():
        _validate_python_file(p)
        filename = p.name
        content_type = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
        f = open(p, "rb")
        try:
            yield Upload(filename=filename, content=f, content_type=content_type)
        finally:
            f.close()
    elif p.is_dir():
        _validate_recipe_directory(p)
        # Ensure __init__.py exists at the root of the directory before zipping
        created_init = False
        root_init = p / "__init__.py"
        zip_buffer = None
        try:
            if not root_init.exists():
                root_init.touch()
                created_init = True
                logger.info(f"Added __init__.py to your directory, as it is required for proper execution of recipe")
            zip_buffer = _zip_directory_to_bytes_io(p)
        finally:
            if created_init:
                try:
                    root_init.unlink()
                    logger.info(f"Cleaned up __init__.py from your directory")
                except Exception:
                    logger.error(f"Failed to remove __init__.py from your directory")
                    pass
        if zip_buffer is None:
            raise RuntimeError("Failed to create in-memory zip for directory upload")

        filename = f"{p.name}.zip"
        try:
            yield Upload(filename=filename, content=zip_buffer, content_type="application/zip")
        finally:
            zip_buffer.close()
    else:
        if not p.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        raise ValueError(f"Path must be a Python file or a directory: {path}")
