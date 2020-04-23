import logging
from collections import namedtuple

import discord

from const import WHITE_CHECKMARK
from util import get_embed_with_title, create_lecture_embed, add_role_to_member, remove_role_from_member, \
    create_overview_info_embed

logging.basicConfig(level=logging.INFO)


class BotClient(discord.Client):

    def __init__(self, config=None, **options):
        super().__init__(**options)
        self.config = config
        self.lecture_message_tuples = []
        self.guild = None

    async def on_ready(self):
        """Executed when bot is logged in and ready."""
        print('Logged in as %s with id %s' % (self.user.name, self.user.id))

    @staticmethod
    async def on_member_join(member):
        """Greets new member."""
        guild = member.guild
        if guild.system_channel is not None:
            greeting = discord.Embed(
                title="{}, willkommen auf {}!".format(str(member), str(guild))
            )
            await guild.system_channel.send(greeting)

    async def on_raw_reaction_add(self, raw_reaction):
        """Handles users adding reactions to messages.
        If an user reacted appropriately to an lecture embed, the user is assigned the role associated with the lecture.
        """
        # check if the reaction belongs to an lecture embed
        lecture = self._get_lecture_of_message_id(raw_reaction.message_id)
        if lecture is not None:
            # check if reaction was the one we expect to assign the role
            if raw_reaction.emoji.name == WHITE_CHECKMARK:
                lecture_role_id = lecture['role']
                member = raw_reaction.member
                await add_role_to_member(member, lecture_role_id)

    # TODO this code is very similar to the one in `on_raw_reaction_add`
    async def on_raw_reaction_remove(self, raw_reaction):
        """Handles users removing reactions from messages.
        If an user removed his previous reaction from a lecture embed, the associated role is removed."""
        # check if the reaction belongs to an lecture embed
        lecture = self._get_lecture_of_message_id(raw_reaction.message_id)
        if lecture is not None:
            # check if reaction was the one we expect to assign the role
            if raw_reaction.emoji.name == '\u2705':  # \u2705 is :white_check_mark:
                lecture_role_id = lecture['role']
                guild = self.get_guild(raw_reaction.guild_id)
                member = guild.get_member(raw_reaction.user_id)
                await remove_role_from_member(member, lecture_role_id)

    def _get_lecture_of_message_id(self, message_id):
        """Returns the lecture associated with this message if there is one. Else returns None."""
        for tuples in self.lecture_message_tuples:
            if tuples.message_id == message_id:
                return tuples.lecture
        return None

    @staticmethod
    async def _init_lecture_embed(channel, lecture):
        """Returns the message for this lecture in the given channel.
        If it does not exist yet, it will be created."""
        message = await get_embed_with_title(channel, lecture['embed_title'])
        if message is None:
            embed = create_lecture_embed(lecture)
            message = await channel.send(embed=embed)
            await message.add_reaction(WHITE_CHECKMARK)
        return message

    async def _guild(self):
        """Returns the guild instance for which the config of this bot instance is written for.
        Also caches the result so we won't have to fetch again."""
        if self.guild is None:
            self.guild = self.get_guild(int(self.config['guild']))
        return self.guild

    async def _init_overview_embed(self, channel):
        """Creates the overview embed in the given channel.
        The overview embed lists all available lectures and has some user information in it."""
        guild = await self._guild()
        embed = await create_overview_info_embed(guild, self.config['lectures'])
        message = await get_embed_with_title(channel, embed.title)
        if message is None:
            await channel.send(embed=embed)
        return message

    async def init_overview_channel(self):
        """Initializes the overview channel.
        Makes sure that an embed for every lecture exists such that users can react to it and
        the role can be assigned."""
        lecture_tuple = namedtuple('LectureMessage', 'lecture message_id')
        await self.wait_until_ready()
        overview_channel = await self.fetch_channel(self.config['overview'])
        await self._init_overview_embed(overview_channel)
        for lecture in self.config['lectures']:
            message = await self._init_lecture_embed(overview_channel, lecture)
            self.lecture_message_tuples.append(lecture_tuple(lecture=lecture, message_id=message.id))
