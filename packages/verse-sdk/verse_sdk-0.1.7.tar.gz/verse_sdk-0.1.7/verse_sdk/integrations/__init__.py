import logging

from ..sdk import VerseSDK


def apply_integrations(sdk: VerseSDK, vendor: str):
    try:
        if vendor == "pydantic_ai":
            from .pydantic_ai import patch_pydantic_ai

            patch_pydantic_ai(sdk)
            logging.info("`pydantic_ai` integration applied to `VerseSDK`")
        elif vendor == "litellm":
            from .litellm import configure_litellm

            configure_litellm(sdk)
            logging.info("`litellm` integration applied to `VerseSDK`")
    except Exception as e:
        logging.warning(f"Error applying `{vendor}` integration", exc_info=e)


__all__ = ["apply_integrations"]
