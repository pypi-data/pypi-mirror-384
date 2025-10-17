from dataclasses import dataclass
from typing import Callable, Literal
import logging


from bovine import BovineActor
from bovine.crypto.types import CryptographicIdentifier
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from cattle_grid.database.auth import RemoteIdentity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def result_for_identity(identity: RemoteIdentity):
    if identity.controller == "gone":
        return None

    return CryptographicIdentifier.from_tuple(identity.controller, identity.public_key)


def find_with_item(dict_list, key_id):
    """Given a list of dictionaries, finds the dictionary with
    id = key_id"""
    for key in dict_list:
        if key.get("id") == key_id:
            return key
    return None


def public_key_owner_from_dict(
    actor: dict, key_id: str
) -> tuple[str | None, str | None]:
    """Given an actor and key_id returns the public_key and the owner. This method directly checks the key `publicKey`"""

    public_key_data = actor.get("publicKey", {})

    if isinstance(public_key_data, list):
        if len(public_key_data) == 1:
            public_key_data = public_key_data[0]
        else:
            public_key_data = find_with_item(public_key_data, key_id)

    if not public_key_data:
        return None, None

    public_key = public_key_data.get("publicKeyPem")
    owner = public_key_data.get("owner")

    return public_key, owner


@dataclass
class PublicKeyCache:
    """Caches public keys in the database and fetches them
    using bovine_actor"""

    bovine_actor: BovineActor
    """used to fetch the public key"""

    session_maker: Callable[[], AsyncSession] | None = None
    """sql session maker"""

    async def cryptographic_identifier(
        self, key_id: str
    ) -> CryptographicIdentifier | Literal["gone"] | None:
        """Returns "gone" if Tombstone

        :param key_id: URI of the public key to fetch
        :returns:
        """

        try:
            result = await self.bovine_actor.get(key_id)

            if result is None:
                return "gone"

            if result.get("type") == "Tombstone":
                logger.info("Got Tombstone for %s", key_id)
                return "gone"

            public_key, owner = public_key_owner_from_dict(result, key_id)

            if public_key is None or owner is None:
                return None

            return CryptographicIdentifier.from_pem(public_key, owner)
        except Exception as e:
            logger.info("Failed to fetch public key for %s with %s", key_id, repr(e))
            logger.debug(e)
            return None

    async def from_cache(self, key_id: str) -> CryptographicIdentifier | None:
        if not self.session_maker:
            raise Exception("Sql session must be set")

        async with self.session_maker() as session:
            try:
                identity = await session.scalar(
                    select(RemoteIdentity).where(RemoteIdentity.key_id == key_id)
                )
            except Exception as e:
                logger.debug(e)
                identity = None

            if identity:
                return result_for_identity(identity)

            identifier = await self.cryptographic_identifier(key_id)
            if identifier is None:
                return None

            if identifier == "gone":
                session.add(
                    RemoteIdentity(key_id=key_id, public_key="gone", controller="gone")
                )
                await session.commit()
                return None

            try:
                controller, public_key = identifier.as_tuple()

                session.add(
                    RemoteIdentity(
                        key_id=key_id, public_key=public_key, controller=controller
                    )
                )
                await session.commit()
            except Exception as e:
                logger.exception(e)
            return identifier
