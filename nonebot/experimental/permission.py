'''
This module replicates the standard permission module already defined
in Nonebot. This, yet another implementation, is experimental and may
be easier or harder to use than the standard one.
'''

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional, Union

from aiocache.decorators import cached
from aiocqhttp.event import Event as CQEvent
from nonebot import NoneBot
from nonebot.exceptions import CQHttpError
from nonebot.permission import _get_minevent_from_event, _MinEvent


@dataclass
class SenderRoles:
    """
    A high level agent object to assess a message sender's permissions
    such as message type, sender's group role, etc. If any groups are
    involved, such as group messages and direct private messages from
    a group member, that group number is consistent across all methods
    """

    bot: NoneBot
    _min_event: _MinEvent
    _sender: Optional[Dict[str, Any]]

    @staticmethod
    async def create(bot: NoneBot, event: CQEvent) -> 'SenderRoles':
        '''constructor to create a SenderRoles object'''
        min_event = _get_minevent_from_event(event)
        sender_info = await _get_member_info(bot, min_event)
        return SenderRoles(bot, min_event, sender_info)

    @staticmethod
    async def test(bot: NoneBot, policy: 'RoleCheckPolicy',
                   event: CQEvent) -> bool:
        '''
        check whether the message sender has permission required defined
        by the policy
        '''
        sender_roles = await SenderRoles.create(bot, event)
        res = policy(sender_roles)
        if isinstance(res, Awaitable):
            return await res
        return res

    # builtin components:

    @property
    def is_groupchat(self) -> bool:
        return self._min_event.message_type == 'group'

    @property
    def is_anonymous(self) -> bool:
        return self._min_event.sub_type == 'anonymous'

    @property
    def is_admin(self) -> bool:
        return self._sender is not None and self._sender.get('role') == 'admin'

    @property
    def is_owner(self) -> bool:
        return self._sender is not None and self._sender.get('role') == 'owner'

    @property
    def is_privatechat(self) -> bool:
        return self._min_event.message_type == 'private'

    @property
    def is_private_friend(self) -> bool:
        return self.is_privatechat and self._min_event.sub_type == 'friend'

    @property
    def is_private_group(self) -> bool:
        return self.is_privatechat and self._min_event.sub_type == 'group'

    @property
    def is_discusschat(self) -> bool:
        return self._min_event.message_type == 'discuss'

    def from_group(self, group_id: int) -> bool:
        return self._min_event.group_id == group_id

    def sent_by(self, sender_id: int) -> bool:
        return self._min_event.sender_id == sender_id


@cached(ttl=2 * 60)
async def _get_member_info(bot: NoneBot,
                           min_event: _MinEvent) -> Optional[Dict[str, Any]]:
    try:
        return await bot.get_group_member_info(
                    self_id=min_event.self_id,
                    group_id=min_event.group_id,
                    user_id=min_event.user_id,
                    no_cache=True)
    except CQHttpError:
        return None


RoleCheckPolicy = Callable[['SenderRoles'], Union[bool, Awaitable[bool]]]
