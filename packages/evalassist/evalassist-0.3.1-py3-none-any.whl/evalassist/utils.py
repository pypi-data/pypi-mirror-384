import functools
import json
import logging
import math
import os
import re
import time
import traceback
from enum import Enum
from typing import Any, cast

from botocore.exceptions import NoCredentialsError
from datasets import IterableDataset
from evalassist.judges import Criteria, CriteriaOption
from fastapi import HTTPException
from ibm_watsonx_ai.wml_client_error import (
    ApiRequestFailure,
    CannotSetProjectOrSpace,
    WMLClientError,
)
from langchain_core.exceptions import OutputParserException
from openai import AuthenticationError, NotFoundError
from unitxt.inference import (
    CrossProviderInferenceEngine,
    HFAutoModelInferenceEngine,
    InferenceEngine,
    LiteLLMInferenceEngine,
    WMLInferenceEngineChat,
    WMLInferenceEngineGeneration,
)
from unitxt.llm_as_judge import EvaluatorNameEnum, ModelProviderEnum

from .api_types import CriteriaWithOptionsDTO
from .const import CUSTOM_MODELS_PATH, EVAL_ASSIST_DIR
from .extended_unitxt import (
    EXTENDED_EVALUATOR_TO_MODEL_ID,
    EXTENDED_EVALUATORS_METADATA,
    ExtendedEvaluatorMetadata,
    ExtendedEvaluatorNameEnum,
    ExtendedModelProviderEnum,
)
from .judges.types import DirectInstance

logger = logging.getLogger(__name__)


def fill_unknown_template(template: str, value: str) -> str:
    # Case 1: Unnamed placeholder(s) like "hello {}"
    if "{}" in template:
        return template.format(value)

    # Case 2: Named placeholder like "hello {world}"
    match = re.search(r"\{(\w+)\}", template)
    if match:
        var_name = match.group(1)
        return template.format(**{var_name: value})

    # Case 3: No placeholder
    return template


def get_custom_models():
    if os.path.exists(CUSTOM_MODELS_PATH):
        with open(CUSTOM_MODELS_PATH, "r", encoding="utf-8") as file:
            try:
                custom_models = json.load(file)
                from . import root_pkg_logger

                root_pkg_logger.debug(
                    "Loaded the following custom models",
                    json.dumps(custom_models, indent=2),
                )
                return custom_models
            except Exception:
                raise ValueError("${CUSTOM_MODELS_PATH} must be a valid json file")
    else:
        return []


def convert_model_name_wx_to_hf(wx_model_name):
    model_map = {
        "ibm/granite-guardian-3-2b": "ibm-granite/granite-guardian-3.1-2b",
        "ibm/granite-guardian-3-8b": "ibm-granite/granite-guardian-3.1-8b",
    }
    try:
        return model_map[wx_model_name]
    except KeyError:
        return wx_model_name


def get_enum_by_value(value: str, enum: type[Enum]) -> Enum | None:
    for enum_member in enum:
        if enum_member.value == value:
            return enum_member
    return None


def get_local_hf_inference_engine_params(
    model_name: str,
):
    return {
        "model_name": convert_model_name_wx_to_hf(model_name),
        "max_new_tokens": 1024,
        "device": get_default_torch_device(),
    }


def get_cross_inference_engine_params(
    credentials: dict,
    provider: ModelProviderEnum,
    model_name: str,
    custom_params: dict | None = None,
    provider_specific_params: dict | None = None,
):
    provider_specific_args = {}
    inference_engine_params = {
        "max_tokens": 1024,
        "credentials": credentials.copy(),
        "provider": provider,
    }
    if provider == ModelProviderEnum.WATSONX:
        provider_specific_args[ModelProviderEnum.WATSONX.value] = {
            "max_requests_per_second": 7
        }

    if (
        provider == ModelProviderEnum.AZURE
        or provider == ExtendedModelProviderEnum.OPENAI_LIKE
    ):
        inference_engine_params["credentials"]["api_base"] = fill_unknown_template(
            credentials["api_base"], model_name
        )

    is_model_supported_by_cross_inference = (
        provider.value in CrossProviderInferenceEngine.provider_model_map
        and model_name
        in CrossProviderInferenceEngine.provider_model_map[provider.value]
    )

    cross_inference_litellm_keys = [
        provider
        for provider, klass in CrossProviderInferenceEngine._provider_to_base_class.items()
        if klass == LiteLLMInferenceEngine
    ]

    if (
        not is_model_supported_by_cross_inference
        and provider.value in cross_inference_litellm_keys
        and not model_name.startswith(provider.value)
    ):
        # LiteLLM expects the model_name to start with the provider
        # If the user provided a custom model_name that uses litellm, adapt it to start with the provider
        model_name = provider.value + "/" + model_name

    elif provider == ExtendedModelProviderEnum.OPENAI_LIKE:
        provider = ModelProviderEnum.OPENAI

    if custom_params is not None:
        inference_engine_params.update(custom_params)
    if provider_specific_params is not None:
        provider_specific_args.update(provider_specific_params)
    inference_engine_params["model"] = model_name
    inference_engine_params["provider"] = provider.value
    inference_engine_params["provider_specific_args"] = provider_specific_args

    if provider == ExtendedModelProviderEnum.HF_LOCAL:
        if "seed" in inference_engine_params:
            del inference_engine_params["seed"]
        if "credentials" in inference_engine_params:
            del inference_engine_params["credentials"]

    return inference_engine_params


def get_cross_inference_engine(
    credentials: dict[str, str],
    provider: ModelProviderEnum,
    model_name: EvaluatorNameEnum,
    custom_params: dict | None = None,
    provider_specific_params: dict | None = None,
):
    inference_engine_params = get_cross_inference_engine_params(
        credentials=credentials,
        provider=provider,
        model_name=model_name,
        custom_params=custom_params,
        provider_specific_params=provider_specific_params,
    )

    return CrossProviderInferenceEngine(**inference_engine_params)


def get_watsonx_inference_engine(
    credentials: dict[str, str],
    provider: ModelProviderEnum,
    model_name: EvaluatorNameEnum,
    custom_params: dict | None = None,
    use_chat: bool = True,
):
    converted_model_name = "/".join(
        CrossProviderInferenceEngine.provider_model_map["watsonx"][model_name].split(
            "/"
        )[1:]
    )
    inference_engine_params = {
        "max_tokens": 1024,
        "credentials": {
            "api_key": credentials["api_key"],
            "url": credentials["api_base"],
        },
        "model_name": converted_model_name,
    }

    if custom_params is not None:
        inference_engine_params.update(custom_params)

    if "project_id" in credentials and credentials["project_id"] is not None:
        inference_engine_params["credentials"]["project_id"] = credentials["project_id"]
    elif "space_id" in credentials and credentials["space_id"] is not None:
        inference_engine_params["credentials"]["space_id"] = credentials["space_id"]
    else:
        raise ValueError("Must provide either project_id or space_id")

    if "seed" in inference_engine_params and not use_chat:
        inference_engine_params["random_seed"] = inference_engine_params["seed"]
        del inference_engine_params["seed"]

    if not use_chat:
        if "seed" in inference_engine_params:
            inference_engine_params["random_seed"] = inference_engine_params["seed"]
            del inference_engine_params["seed"]
        if "max_tokens" in inference_engine_params:
            inference_engine_params["max_new_tokens"] = inference_engine_params[
                "max_tokens"
            ]
            del inference_engine_params["max_tokens"]

    return (
        WMLInferenceEngineChat(**inference_engine_params)
        if use_chat
        else WMLInferenceEngineGeneration(**inference_engine_params)
    )


preloaded_hf_models = {}


def get_hf_inference_engine(
    model_name: str,
    custom_params: dict | None = None,
):
    global preloaded_hf_models
    if model_name in preloaded_hf_models:
        logger.debug(f"Using preloaded HF model {model_name}")
        return preloaded_hf_models[model_name]
    else:
        logger.debug(f"Loading model {model_name}")
        params = get_local_hf_inference_engine_params(model_name)
        if custom_params is not None:
            params.update(custom_params)
        if "seed" in params:
            del params["seed"]
        hf_model = HFAutoModelInferenceEngine(**params)
        preloaded_hf_models[model_name] = hf_model
        return hf_model


def get_inference_engine(
    credentials: dict[str, str | None],
    provider: ModelProviderEnum | ExtendedModelProviderEnum,
    model_name: str,
    custom_params: dict | None = None,
    provider_specific_params: dict | None = None,
) -> InferenceEngine:
    # if provider == ExtendedModelProviderEnum.LOCAL_HF:
    #     return get_hf_inference_engine(model_name, custom_params)
    if provider == ModelProviderEnum.WATSONX and (
        "granite-guardian" in model_name
        or ("space_id" in credentials and credentials["space_id"])
    ):
        use_chat = "granite-guardian" not in model_name  # uses probs
        return get_watsonx_inference_engine(
            credentials, provider, model_name, custom_params, use_chat
        )
    return get_cross_inference_engine(
        credentials, provider, model_name, custom_params, provider_specific_params
    )


def get_model_name_from_evaluator(
    evaluator_metadata: ExtendedEvaluatorMetadata,
    provider: str,
) -> str:
    model_name = EXTENDED_EVALUATOR_TO_MODEL_ID.get(evaluator_metadata.name, None)
    return (
        evaluator_metadata.custom_model_path
        if evaluator_metadata.custom_model_path is not None
        else model_name
    )


def get_enum_values(e: type[Enum]):
    return [member.value for member in e]


def get_evaluator_metadata_wrapper(
    evaluator_name: EvaluatorNameEnum | ExtendedEvaluatorNameEnum,
    custom_model_name: str | None = None,
) -> ExtendedEvaluatorMetadata:
    if evaluator_name.name != ExtendedEvaluatorNameEnum.CUSTOM.name:
        evaluator_search = [
            e
            for e in EXTENDED_EVALUATORS_METADATA
            if e.name.name == evaluator_name.name
        ]
        if len(evaluator_search) == 0:
            raise ValueError(f"An evaluator with id {evaluator_name} does not exist.")
        if len(evaluator_search) > 1:
            raise ValueError(
                f"An evaluator with id {evaluator_name} matched several models."
            )
        return evaluator_search[0]
    else:
        custom_models = get_custom_models()
        if custom_model_name not in [
            custom_model["name"] for custom_model in custom_models
        ]:
            raise ValueError("The specified custom model was not found")

        custom_model = [
            custom_model
            for custom_model in custom_models
            if custom_model["name"] == custom_model_name
        ][0]
        providers: list[ModelProviderEnum | ExtendedModelProviderEnum] = []
        for p in providers:
            try:
                providers.append(
                    ExtendedModelProviderEnum(p)
                    if get_enum_values(ExtendedModelProviderEnum)
                    else ModelProviderEnum(p)
                )
            except Exception as e:
                print(e)

        return ExtendedEvaluatorMetadata(
            name=evaluator_name,
            custom_model_name=custom_model["name"],
            custom_model_path=custom_model["path"],
            providers=providers,
        )


def get_default_torch_device(avoid_mps: bool = False):
    try:
        from unitxt.inference import TorchDeviceMixin

        device = TorchDeviceMixin().get_device_id()
        return device
    except Exception:
        raise ImportError(
            'torch is not installed -by default-. Make sure you installed local inference dependencies with pip install "evalassist[local-inference]"'
        )
    logger.debug(f"Detected device: {device}")


def init_evaluator_name(
    evaluator_name: EvaluatorNameEnum | ExtendedEvaluatorNameEnum | str,
) -> tuple[ExtendedEvaluatorNameEnum, str | None]:
    evaluator_name_as_enum = get_enum_by_value(evaluator_name, EvaluatorNameEnum)
    if evaluator_name_as_enum is None:
        evaluator_name_as_enum = get_enum_by_value(
            evaluator_name, ExtendedEvaluatorNameEnum
        )

    if evaluator_name_as_enum is not None:
        return (evaluator_name_as_enum, None)

    custom_model_name = evaluator_name
    evaluator_name = ExtendedEvaluatorNameEnum.CUSTOM
    return (evaluator_name, custom_model_name)


def log_runtime(function):
    """
    Usage: wrap a function call with the log_runtime function to log its runtime
    """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        res = function(*args, **kwargs)

        end_time = time.time()
        total_time = round(end_time - start_time, 2)

        logger.debug(
            f"{function.__name__} took {total_time} seconds, {round(total_time / 60, 2)} minutes"
        )

        return res

    return wrapper


def to_snake_case(name: str) -> str:
    return name.replace(" ", "_").lower()


def parse_exception_message(e: Exception) -> str:
    error_message = e.message if hasattr(e, "message") else None
    if error_message is None:
        return str(e)
    result = error_message.split(" - ", 1)
    if len(result) == 1:
        return result[0]
    try:
        result = json.loads(result[1])
    except json.JSONDecodeError:
        return result[1]
    if "errorMessage" in result:
        return result["errorMessage"]
    elif (
        "errors" in result
        and len(result["errors"]) > 0
        and "message" in result["errors"][0]
    ):
        return result["errors"][0]["message"]
    elif "title" in result:
        return result["detail"]
    else:
        return str(result)


def handle_exception(e: Exception) -> None:
    error_message = parse_exception_message(e)
    if isinstance(e, OutputParserException):
        raise HTTPException(
            status_code=400,
            detail=error_message,
        ) from e
    elif isinstance(e, NotFoundError):
        raise HTTPException(status_code=400, detail=error_message)
    elif isinstance(e, ValueError):
        raise HTTPException(status_code=400, detail=error_message)
    elif isinstance(e, ApiRequestFailure):
        raise HTTPException(status_code=400, detail=error_message)
    elif isinstance(e, NoCredentialsError):
        raise HTTPException(
            status_code=400,
            detail=error_message,
        )
    elif isinstance(e, AuthenticationError):
        raise HTTPException(status_code=400, detail=error_message)
    elif isinstance(e, CannotSetProjectOrSpace):
        raise HTTPException(status_code=400, detail=error_message)
    elif isinstance(e, WMLClientError):
        raise HTTPException(status_code=400, detail=error_message)
    elif isinstance(e, AssertionError):
        raise HTTPException(status_code=400, detail=error_message)
    elif isinstance(e, RuntimeError):
        if e.__cause__:
            handle_exception(e.__cause__)
        else:
            raise HTTPException(400, error_message)
    else:
        raise HTTPException(
            status_code=400,
            detail=error_message,
        )


def handle_llm_generation_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            handle_exception(e)
        finally:
            traceback.print_exc()

    return wrapper


def clean_object(results: dict | list):
    """Cleans the object by removing `None` values and empty lists and dictionaries.

    Args:
        results (Union[dict, list]): The results to clean.

    Returns:
        Union[dict, list]: The cleaned results.
    """
    if isinstance(results, list):
        cleaned_list = [
            clean_object(x)
            for x in results
            if x is not None and not (isinstance(x, (list, dict)) and len(x) == 0)
        ]
        return cleaned_list
    elif isinstance(results, dict):
        cleaned = {
            k: (v if not isinstance(v, dict) else clean_object(v))
            for k, v in results.items()
            if v is not None and not (isinstance(v, (list, dict)) and len(v) == 0)
        }
        # Remove the dictionary itself if it becomes empty
        return {
            k: v
            for k, v in cleaned.items()
            if not (isinstance(v, dict) and len(v) == 0)
        }
    else:
        return results


def get_system_version():
    try:
        # git is a dev dependency so import may fail
        try:
            import git
        except ImportError as e:
            logger.error(
                "Make sure you installed EvalAssist's dev dependencies with poetry install --with dev"
            )
            raise e
        repo = git.repo.Repo(EVAL_ASSIST_DIR.parent.parent.parent)
        version = repo.git.describe(tags=True)
        source = "git"
    except Exception:
        try:
            from importlib.metadata import version

            version = version("evalassist")
            source = "pypi"

            if version == "0.0.0":
                # version is 0.0.0 in the toml only when
                # evalassist is executed using poetry
                # and the .git folder is not present in the root directory
                raise ValueError("Invalid version")
        except Exception as e:
            version = None
            source = None
            print(e)
            logging.warning("Could not get EvalAssist version")

    return {"version": version, "source": source}


def unitxt_dataset_to_evalassist_instances(
    dataset: IterableDataset,
    criteria: list[Criteria],
) -> list[DirectInstance]:
    if any(
        criterion.prediction_field is None or criterion.context_fields is None
        for criterion in criteria
    ):
        raise ValueError(
            "The criteria.prediction_field is None. It must be set to retrieve the response to evaluate from the task_data"
        )
    task_data_list = [json.loads(d["task_data"]) for d in dataset]
    return [
        DirectInstance(
            context={k: task_data[k] for k in cast(list, criterion.context_fields)},
            response=task_data[criterion.prediction_field],
        )
        for task_data, criterion in zip(task_data_list, criteria)
    ]


def get_inference_engine_from_judge_metadata(
    evaluator_name: ExtendedEvaluatorNameEnum,
    custom_model_name: str | None,
    provider: ModelProviderEnum | ExtendedModelProviderEnum,
    llm_provider_credentials: dict[str, str | None],
    custom_params: dict[str, Any] | None = None,
):
    """
    Get an inference engine from evaluator's data.
    """
    evaluator_metadata = get_evaluator_metadata_wrapper(
        evaluator_name,
        custom_model_name,
    )
    model_name = get_model_name_from_evaluator(
        evaluator_metadata,
        provider,
    )
    return get_inference_engine(
        credentials=llm_provider_credentials,
        provider=provider,
        model_name=model_name,
        custom_params=custom_params,
    )


def criteria_with_options_DTO_to_BO_mapper(
    criteria: CriteriaWithOptionsDTO,
) -> Criteria:
    return Criteria(
        name=criteria.name,
        description=criteria.description,
        options=[
            CriteriaOption(name=o.name, description=o.description)
            for o in criteria.options
        ],
        prediction_field=criteria.prediction_field,
        context_fields=criteria.context_fields,
    )


def convert_nan_to_none(obj):
    if isinstance(obj, float) and math.isnan(obj):
        return None
    elif isinstance(obj, dict):
        return {k: convert_nan_to_none(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_nan_to_none(v) for v in obj]
    return obj
