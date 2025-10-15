from __future__ import annotations

import inspect
import logging
from functools import wraps

from .contexts import ContextType, OperationType
from .sdk import VerseSDK
from .utils import to_json


def lazily(verse: VerseSDK, decorator_name: str):
    """Create a lazy decorator that evaluates at call time."""

    def decorator(*args, **kwargs):
        try:
            verse_decorator = getattr(verse, decorator_name)
            return verse_decorator(*args, **kwargs)
        except Exception:

            def noop_decorator(fn):
                return fn

            return noop_decorator

    return decorator


def with_decorators(sdk: VerseSDK) -> VerseSDK:
    """A higher-order function for dropping decorators onto the SDK."""

    def create_observation_decorator(
        span_type: ContextType, operation_type: OperationType | None = None
    ):
        def observe_wrapper(
            name: str | None = None,
            capture_input: bool = True,
            capture_metadata: bool = True,
            capture_output: bool = True,
            **attrs,
        ):
            """
            Context decorator for any arbitrary function.

            Parameters:
                - name: str | None
                    The name of the observation.
                - capture_input: bool
                    Whether to capture the input of the function.
                - capture_metadata: bool
                    Whether to capture the metadata of the function.
                - capture_output: bool
                    Whether to capture the output of the function.
                - attrs: dict
                    Additional attributes to set on the observation.

            Returns:
                A decorator function.
            """

            def decorator(fn):
                @wraps(fn)
                def observer(*args, **kwargs):
                    """
                    For both sync and async functions,
                    We need to allow applications to observe all types of contexts (e.g. generation, span, trace)

                    Parameters:
                        - args: tuple
                            The arguments to pass to the original function.
                        - kwargs: dict
                            The keyword arguments to pass to the original function.

                    Returns:
                        The result of the original function.
                    """
                    try:
                        observation_method = getattr(sdk, span_type)
                        observation_name = name or fn.__name__

                        # note: currently we only support operation type for span
                        if span_type == "span" and operation_type:
                            attrs["op"] = operation_type

                        with observation_method(
                            observation_name, **attrs
                        ) as observation:
                            if capture_input:
                                observation.input(
                                    to_json({"args": args, "kwargs": kwargs})
                                )
                            if capture_metadata and "metadata" in kwargs:
                                observation.metadata(metadata=kwargs["metadata"])

                            observation.set_attributes(**attrs)

                            try:
                                if inspect.iscoroutinefunction(fn):

                                    async def async_observer():
                                        result = await fn(*args, **kwargs)
                                        if capture_output:
                                            observation.output(to_json(result))
                                        return result

                                    return async_observer()
                                else:
                                    result = fn(*args, **kwargs)
                                    if capture_output:
                                        observation.output(to_json(result))
                                    return result
                            except Exception as e:
                                observation.error(e)
                                raise e
                    except Exception as e:
                        logging.warning(
                            "Failed to instrument function",
                            fn=fn.__name__,
                            exc_info=e,
                        )

                        return fn(*args, **kwargs)

                return observer

            return decorator

        return observe_wrapper

    sdk.observe = create_observation_decorator("span")
    sdk.observe_generation = create_observation_decorator("generation")
    sdk.observe_span = sdk.observe
    sdk.observe_tool = create_observation_decorator("span", "tool")
    sdk.observe_trace = create_observation_decorator("trace")
    return sdk
