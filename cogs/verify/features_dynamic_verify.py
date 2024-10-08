import disnake

import utils
from config.app_config import config
from database.verification import DynamicVerifyDB
from features.base_feature import BaseFeature
from features.verify_helper import VerifyHelper
from rubbergod import Rubbergod

from .messages_cz import MessagesCZ
from .views_dynamic_verify import DynamicVerifyRequestView


class DynamicVerifyManager(BaseFeature):
    def __init__(self, bot: Rubbergod) -> None:
        super().__init__(bot)
        self.verify_db = DynamicVerifyDB()
        self.helper = VerifyHelper(bot)

    async def can_apply_rule(self, user: disnake.User | disnake.Member, rule_id: str) -> bool:
        return self.verify_db.exists_rule(rule_id) and not await self.helper.has_role(
            user, config.verification_role
        )

    async def request_access(self, rule_id: str, inter: disnake.AppCommandInteraction) -> None:
        rule = self.verify_db.get_rule(rule_id)
        if rule is None:
            return None
        if rule.mod_check:
            await self.request_verification(rule, inter)
            await inter.send(MessagesCZ.dynamic_verify_requested, ephemeral=True)
        else:
            await self.apply_rule(rule_id, inter.author.id, inter)

    async def apply_rule(self, rule_id: str, user_id: int, inter: disnake.MessageInteraction) -> None:
        guild = inter.guild if inter.guild is not None else await self.bot.get_guild(config.guild_id)
        rule = self.verify_db.get_rule(rule_id)
        if rule is None:
            return None
        role_ids = rule.get_role_ids()
        roles = [guild.get_role(role_id) for role_id in role_ids]
        await self.log_attempt(rule, inter, user_id)
        member = await guild.get_or_fetch_member(user_id)
        newbie = guild.get_role(config.newbie_role)
        await member.remove_roles(newbie)
        for role in list(filter(lambda x: x is not None, roles)):
            await member.add_roles(role, reason=f"Dynamic verification - Rule {rule.name} ({rule.id})")

        try:
            await member.send(MessagesCZ.verify_verify_success(user=user_id))
            await member.send(MessagesCZ.verify_post_verify_info)
        except disnake.HTTPException:
            pass  # User maybe have disabled communication with bots.

        if inter.channel.type is not disnake.ChannelType.private:
            await inter.send(MessagesCZ.verify_verify_success(user=user_id))

    async def request_verification(
        self, rule: DynamicVerifyDB, inter: disnake.ApplicationCommandInteraction
    ) -> None:
        embed = disnake.Embed(title="Žádost o dynamickou verifikaci", color=disnake.Colour.yellow())
        embed.add_field("Pravidlo", f"{rule.name} ({rule.id})")
        embed.add_field(
            "Uživatel",
            f"{inter.user.display_name} ({inter.author.mention}))",
        )

        channel = self.bot.get_channel(config.mod_room)
        view = DynamicVerifyRequestView(rule.id, inter.user.id)
        view.message = await channel.send(embed=embed, view=view)

    async def log_attempt(
        self,
        rule: DynamicVerifyDB,
        inter: disnake.ApplicationCommandInteraction,
        target_id: int,
    ) -> None:
        embed = disnake.Embed(title="Dynamická verifikace", color=disnake.Colour.yellow())
        embed.add_field("Pravidlo", f"{rule.name} ({rule.id})")
        embed.add_field("Potvrdil", inter.author.mention)
        embed.add_field("Uživatel", utils.user.generate_mention(target_id))

        channel = self.bot.get_channel(config.log_channel)
        await channel.send(embed=embed)

    def get_rules_list(self) -> dict[str, str]:
        rules = self.verify_db.get_rules(25)
        return {rule.name: rule.id for rule in rules}

    def get_rule(self, rule_id: str) -> DynamicVerifyDB | None:
        return self.verify_db.get_rule(rule_id)
