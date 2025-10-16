from buddy.api.api import api
from buddy.api.routes import ApiRoutes
from buddy.api.schemas.evals import EvalRunCreate
from buddy.cli.settings import BUDDY_cli_settings
from buddy.utils.log import log_debug


def create_eval_run(eval_run: EvalRunCreate) -> None:
    """Call the API to create an evaluation run."""
    if not BUDDY_cli_settings.api_enabled:
        return

    log_debug("Calling the API to create an evaluation run")
    with api.AuthenticatedClient() as api_client:
        try:
            api_client.post(ApiRoutes.EVAL_RUN_CREATE, json={"eval_run": eval_run.model_dump(exclude_none=True)})
        except Exception as e:
            log_debug(f"Could not create evaluation run: {e}")
    return


async def async_create_eval_run(eval_run: EvalRunCreate) -> None:
    """Call the API to create an evaluation run."""
    if not BUDDY_cli_settings.api_enabled:
        return

    log_debug("Calling the API to create an evaluation run")
    async with api.AuthenticatedAsyncClient() as api_client:
        try:
            await api_client.post(ApiRoutes.EVAL_RUN_CREATE, json={"eval_run": eval_run.model_dump(exclude_none=True)})
        except Exception as e:
            log_debug(f"Could not create evaluation run: {e}")
    return


