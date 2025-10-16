import asyncio
import base64
import functools
import logging
import tempfile
import uuid
from typing import Any

from codemie_tools.data_management.file_system.jupyter import (
    Jupyter,
    RuntimeOutput,
)

logger = logging.getLogger(__name__)


def timeout(timeout: int):
    def decorator(coroutine_func):
        @functools.wraps(coroutine_func)
        async def wrapper(*args, **kwargs):
            return await asyncio.wait_for(coroutine_func(*args, **kwargs), timeout=timeout)

        return wrapper

    return decorator



class CodeExecutor:
    """
    The CodeExecutor class abstracts communication with code interpreters and runtimes.
    It currently supports executing Python code, with potential to expand for other languages in the future.
    """

    file_repository: Any = None

    def __init__(self, file_repository: Any):
        """
        Initializes the CodeExecutor instance.
        """
        self.file_repository = file_repository

    def execute_python(self, code: str, user_id: str):
        return self._execute_code(code=code, user_id=user_id, language="python")

    def _execute_code(self, code: str, user_id: str, language):
        """
        Executes code in the specified language.

        Parameters:
        - code (str): The code snippet to be executed.
        - language (str): The programming language of the code.

        Returns:
        The result of the code execution if the language is supported.

        Raises:
        - UnsupportedLanguageException: If the specified language is not supported.
        """
        if language.lower() == "python":
            return asyncio.run(self._run_in_sandbox(code, user_id))
        else:
            raise ValueError(f"{language} language is not supported. Only Python is supported.")

    @timeout(60*2)
    async def _run_code(self, code: str):
        try:
            with tempfile.TemporaryDirectory(prefix="jupyter_") as jupyter_dir:
                async with Jupyter(jupyter_dir, is_tcp=True) as jupyter:
                    if not jupyter.kc:
                        raise RuntimeError("jupyter client could not be started")

                    return await jupyter.arun(code)
        except Exception as e:
            raise RuntimeError(f"Cannot start or execute jupyter kernel. Err: {str(e)}")

    async def _run_in_sandbox(self, code: str, user_id: str):
        try:
            result = await self._run_code(code)
        except RuntimeError:
            raise
        except asyncio.TimeoutError:
            raise RuntimeError(
                RuntimeOutput(
                    type="error", content="Code execution reach a timeout"
                ).model_dump_json()
            )
        except Exception as e:
            raise RuntimeError(
                RuntimeOutput(
                    type="error",
                    content=f"Code execution got unexpected error: {str(e)}",
                ).model_dump_json(),
            )

        if not result:
            return ""

        if result.type == "image/png":
            if self.file_repository:
                stored_file = self.file_repository.write_file(
                    name=f"{uuid.uuid4()}.png",
                    mime_type=result.type,
                    content=base64.b64decode(result.content),
                    owner=user_id,
                )
                return f"This 'sandbox:/v1/files/{stored_file.to_encoded_url()}' is image URL. You MUST not transform it. Return as it is"
            else:
                return f"This 'sandbox:/v1/files/{result.content}' is image URL. You MUST not transform it. Return as it is"

        return result

