from __future__ import annotations

from typing import Any, Union

from pydantic import BaseModel, Field, field_validator

from pipelex import log
from pipelex.core.memory.working_memory import BATCH_ITEM_STUFF_NAME, MAIN_STUFF_NAME
from pipelex.exceptions import BatchParamsError
from pipelex.types import Self, StrEnum


class PipeRunParamKey(StrEnum):
    DYNAMIC_OUTPUT_CONCEPT = "_dynamic_output_concept"
    NB_OUTPUT = "_nb_output"


class PipeRunMode(StrEnum):
    LIVE = "live"
    DRY = "dry"

    @property
    def is_dry(self) -> bool:
        match self:
            case PipeRunMode.DRY:
                return True
            case PipeRunMode.LIVE:
                return False


FORCE_DRY_RUN_MODE_ENV_KEY = "PIPELEX_FORCE_DRY_RUN_MODE"

PipeOutputMultiplicity = Union[bool, int]


class OutputMultiplicityResolution(BaseModel):
    """Result of resolving output multiplicity settings between base and override values.

    This model provides a clear, structured representation of how output multiplicity
    should be applied, replacing the previous tuple-based return format.
    """

    resolved_multiplicity: PipeOutputMultiplicity | None = Field(description="The final multiplicity value to use after resolution")

    is_multiple_outputs_enabled: bool = Field(description="Whether multiple outputs should be generated")

    specific_output_count: int | None = Field(default=None, description="Exact number of outputs to generate, if specified")


def make_output_multiplicity(nb_output: int | None, multiple_output: bool | None) -> PipeOutputMultiplicity | None:
    """This function takes two mutually exclusive parameters that control how many outputs
    a pipe should generate and converts them into a single PipeOutputMultiplicity type.

    Args:
        nb_output: Specific number of outputs to generate. If provided and truthy,
                  takes precedence over multiple_output.
        multiple_output: Boolean flag indicating whether to generate multiple outputs.
                        If True, lets the LLM decide how many outputs to generate.

    Examples:
        >>> make_output_multiplicity(nb_output=3, multiple_output=None)
        3
        >>> make_output_multiplicity(nb_output=None, multiple_output=True)
        True
        >>> make_output_multiplicity(nb_output=None, multiple_output=False)
        None
        >>> make_output_multiplicity(nb_output=0, multiple_output=True)
        True

    """
    output_multiplicity: PipeOutputMultiplicity | None
    if nb_output:
        output_multiplicity = nb_output
    elif multiple_output:
        output_multiplicity = True
    else:
        output_multiplicity = None
    return output_multiplicity


def output_multiplicity_to_apply(
    base_multiplicity: PipeOutputMultiplicity | None,
    override_multiplicity: PipeOutputMultiplicity | None,
) -> OutputMultiplicityResolution:
    """Resolve output multiplicity settings by combining base configuration with override.

    This function implements a priority system where override values take precedence over
    base values, with clear logic to handle different type combinations and return
    a structured result indicating how output multiplicity should be applied.

    Args:
        base_multiplicity: Base multiplicity setting (from pipe definition).
            - None: Single output (default)
            - True: Multiple outputs (LLM decides count)
            - int: Specific number of outputs
        override_multiplicity: Override multiplicity setting (from runtime params).
            - None: Use base value
            - True: Enable multiple outputs
            - False: Force single output (disable multiplicity)
            - int: Specific number of outputs

    Returns:
        OutputMultiplicityResolution: Structured result containing:
            - resolved_multiplicity: The final multiplicity value to use
            - enable_multiple_outputs: True if multiple outputs should be generated
            - specific_output_count: Exact number of outputs if specified, None otherwise

    Resolution Logic:
        - If override is None: Use base value as-is
        - If override is False: Force single output regardless of base
        - If override is True: Enable multiple outputs, preserve base count if it's int
        - If override is int: Use override count, enable multiple outputs

    Examples:
        >>> result = output_multiplicity_to_apply(None, None)
        >>> (result.resolved_multiplicity, result.enable_multiple_outputs, result.specific_output_count)
        (None, False, None)
        >>> result = output_multiplicity_to_apply(True, None)
        >>> (result.resolved_multiplicity, result.enable_multiple_outputs, result.specific_output_count)
        (True, True, None)
        >>> result = output_multiplicity_to_apply(3, None)
        >>> (result.resolved_multiplicity, result.enable_multiple_outputs, result.specific_output_count)
        (3, True, 3)

    """
    # Case 1: No override provided - use base value as-is
    if override_multiplicity is None:
        if isinstance(base_multiplicity, bool):
            return OutputMultiplicityResolution(
                resolved_multiplicity=base_multiplicity,
                is_multiple_outputs_enabled=base_multiplicity,
                specific_output_count=None,
            )
        elif isinstance(base_multiplicity, int):
            return OutputMultiplicityResolution(
                resolved_multiplicity=base_multiplicity,
                is_multiple_outputs_enabled=True,
                specific_output_count=base_multiplicity,
            )
        else:
            return OutputMultiplicityResolution(
                resolved_multiplicity=base_multiplicity, is_multiple_outputs_enabled=False, specific_output_count=None
            )

    # Case 2: Override is a boolean
    elif isinstance(override_multiplicity, bool):
        if override_multiplicity:
            if isinstance(base_multiplicity, bool):
                return OutputMultiplicityResolution(resolved_multiplicity=True, is_multiple_outputs_enabled=True, specific_output_count=None)
            else:
                return OutputMultiplicityResolution(
                    resolved_multiplicity=base_multiplicity,
                    is_multiple_outputs_enabled=True,
                    specific_output_count=base_multiplicity if isinstance(base_multiplicity, int) else None,
                )
        else:
            return OutputMultiplicityResolution(resolved_multiplicity=False, is_multiple_outputs_enabled=False, specific_output_count=None)

    else:
        # Case 3: Override is an integer
        return OutputMultiplicityResolution(
            resolved_multiplicity=override_multiplicity,
            is_multiple_outputs_enabled=True,
            specific_output_count=override_multiplicity,
        )


class BatchParams(BaseModel):
    input_list_stuff_name: str
    input_item_stuff_name: str

    @classmethod
    def make_optional_batch_params(
        cls,
        input_list_name: str | None,
        input_item_name: str | None,
    ) -> BatchParams | None:
        if input_list_name:
            input_item_stuff_name = input_item_name or BATCH_ITEM_STUFF_NAME
            return BatchParams(
                input_list_stuff_name=input_list_name,
                input_item_stuff_name=input_item_stuff_name,
            )
        elif input_item_name:
            msg = "input_item_name is required when input_list_name is not provided"
            raise BatchParamsError(msg)
        else:
            return None

    @classmethod
    def make_default(cls) -> BatchParams:
        return BatchParams(
            input_list_stuff_name=MAIN_STUFF_NAME,
            input_item_stuff_name=BATCH_ITEM_STUFF_NAME,
        )


class PipeRunParams(BaseModel):
    run_mode: PipeRunMode = PipeRunMode.LIVE
    final_stuff_code: str | None = None
    is_with_preliminary_text: bool | None = None
    output_multiplicity: PipeOutputMultiplicity | None = None
    dynamic_output_concept_code: str | None = None
    batch_params: BatchParams | None = None
    params: dict[str, Any] = Field(default_factory=dict)

    pipe_stack_limit: int
    pipe_stack: list[str] = Field(default_factory=list)
    pipe_layers: list[str] = Field(default_factory=list)

    @field_validator("params")
    @classmethod
    def validate_param_keys(cls, value: dict[str, Any]) -> dict[str, Any]:
        for key in value:
            if key == PipeRunParamKey.DYNAMIC_OUTPUT_CONCEPT:
                # TODO: validate the concept code
                pass
            if not key.startswith("_"):
                msg = f"Parameter key '{key}' must start with an underscore '_'"
                raise ValueError(msg)
        return value

    def make_deep_copy(self) -> Self:
        return self.model_copy(deep=True)

    def deep_copy_with_final_stuff_code(self, final_stuff_code: str) -> Self:
        return self.model_copy(deep=True, update={"final_stuff_code": final_stuff_code})

    @classmethod
    def copy_by_injecting_multiplicity(
        cls,
        pipe_run_params: Self,
        applied_output_multiplicity: PipeOutputMultiplicity | None,
        is_with_preliminary_text: bool | None = None,
    ) -> Self:
        """Copy the run params the nb_output into the params, and remove the attribute.
        This is useful to make a single prompt with multiple outputs.
        """
        new_run_params = pipe_run_params.model_copy()

        # inject the nb_output into the params, and remove the attribute
        if isinstance(applied_output_multiplicity, bool):
            new_run_params.output_multiplicity = applied_output_multiplicity
        elif isinstance(applied_output_multiplicity, int):
            new_run_params.output_multiplicity = False
            new_run_params.params[PipeRunParamKey.NB_OUTPUT] = applied_output_multiplicity
        if is_with_preliminary_text is not None:
            new_run_params.is_with_preliminary_text = is_with_preliminary_text
        return new_run_params

    @property
    def is_multiple_output_required(self) -> bool:
        return isinstance(self.output_multiplicity, int) and self.output_multiplicity > 1  # pyright: ignore[reportUnnecessaryIsInstance]

    def push_pipe_to_stack(self, pipe_code: str) -> None:
        self.pipe_stack.append(pipe_code)

    def pop_pipe_from_stack(self, pipe_code: str) -> None:
        popped_pipe_code = self.pipe_stack.pop()
        if popped_pipe_code != pipe_code:
            # raise PipeRunError(f"Pipe code '{pipe_code}' was not the last pipe in the stack, it was '{popped_pipe_code}'")
            log.error(f"Pipe code '{pipe_code}' was not the last pipe in the stack, it was '{popped_pipe_code}'")
            # TODO: investigate how this can happen, maybe due to a shared object between branches of PipeBatch or PipeParallel
            # (which should be copied instead)

    def push_pipe_layer(self, pipe_code: str) -> None:
        if self.pipe_layers and self.pipe_layers[-1] == pipe_code:
            return
        self.pipe_layers.append(pipe_code)

    def pop_pipe_code(self) -> str:
        return self.pipe_layers.pop()
