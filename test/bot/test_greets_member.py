from unittest import mock

import aiounittest
from aiounittest import futurized
from discord import Embed

# noinspection PyUnresolvedReferences
import test.context
from src.bot import BotClient
from src.event.on_member_join import on_member_join


class TestGreetsMember(aiounittest.AsyncTestCase):

    @classmethod
    def setUpClass(cls):
        cls.bot = BotClient()

    @mock.patch('discord.Guild')
    @mock.patch('discord.Member')
    async def test_greets_member_with_embed_if_guild_has_system_channel(self, member, guild):
        guild.system_channel.send = mock.Mock(futurized(None))
        member.guild = guild
        # could also do `self.bot.on_member_join(member)` here but I want to stay consistent across tests.
        await on_member_join(self.bot)(member)
        guild.system_channel.send.assert_called_once()
        # first argument of first call
        embed = guild.system_channel.send.call_args[0][0]
        self.assertIsInstance(embed, Embed)

    @mock.patch('discord.Guild')
    @mock.patch('discord.Member')
    async def test_greets_member_raises_runtime_warning_if_guild_has_no_system_channel(self, member, guild):
        guild.system_channel = None
        member.guild = guild
        # TODO when you figured out testing logging, add here test for warning log
        with self.assertRaises(RuntimeWarning):
            await on_member_join(self.bot)(member)
