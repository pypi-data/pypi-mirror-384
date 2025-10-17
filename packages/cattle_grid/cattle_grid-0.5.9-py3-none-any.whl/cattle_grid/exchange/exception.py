from faststream import ExceptionMiddleware, Context

import logging
import json

from cattle_grid.account.account import account_for_actor
from cattle_grid.model.account import ErrorMessage
from cattle_grid.dependencies import AccountExchangePublisher, SqlSession
from cattle_grid.dependencies.processing import RoutingKey

logger = logging.getLogger(__name__)

exception_middleware = ExceptionMiddleware()


@exception_middleware.add_handler(Exception)
async def exception_handler(
    exception: Exception,
    routing_key: RoutingKey,
    session: SqlSession,
    publisher: AccountExchangePublisher,
    message=Context("message.body"),
):
    """When an exception occurs in processing, this handler will create
    an appropriate entry in `receive.NAME.error` in the account exchange"""
    try:
        data = json.loads(message)
        actor_id = data["actor"]
    except Exception:
        logger.exception(exception)
        logger.exception(message)
        return

    logger.info("Exception for %s", actor_id)
    logger.debug(exception, exc_info=True)
    account = await account_for_actor(session, actor_id)
    if not account:
        return
    name = account.name

    logger.info("Processing error occurred in exchange for account %s", name)

    await publisher(
        ErrorMessage(message=str(exception).split("\n"), routing_key=routing_key),
        routing_key=f"error.{name}",
    )
