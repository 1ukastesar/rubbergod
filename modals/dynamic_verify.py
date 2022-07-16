import disnake
from repository.database.verification import DynamicVerifyRule
from typing import Union, List
from features.dynamic_verify import DynamicVerifyManager

# TODO: Prepared for modal select menus
# import utils


class DynamicVerifyEditModal(disnake.ui.Modal):
    def __init__(
        self, guild: disnake.Guild, rule: Union[DynamicVerifyRule, None] = None
    ):
        self.rule = rule

        selected_roles = rule.get_role_ids() if self.is_edit() else []
        guild_roles = list(
            filter(lambda x: x.name != "@everyone" and x.is_assignable(), guild.roles)
        )

        selected_roles_data = list(
            map(
                lambda x: next((role for role in guild_roles if x == role.id), None),
                selected_roles,
            )
        )
        selected_roles_data = list(filter(lambda x: x is not None, selected_roles_data))

        # TODO: Prepared for modal select menus.
        # guild_role_groups = utils.split_to_parts(guild_roles, 25)

        components = [
            disnake.ui.TextInput(
                label="Identifikátor",
                placeholder="Identifikátor",
                custom_id="id",
                style=disnake.TextInputStyle.short,
                required=True,
                value=rule.id if self.is_edit() else None,
                min_length=2,
            ),
            disnake.ui.TextInput(
                label="Název",
                placeholder="Název",
                custom_id="name",
                style=disnake.TextInputStyle.short,
                required=True,
                value=rule.name if self.is_edit() else None,
                min_length=5,
            ),
            # TODO: Prepared for modal select menus.
            # disnake.ui.Select(
            #    custom_id="enabled",
            #    placeholder="Stav",
            #    options=[
            #        disnake.SelectOption(label="Aktivní", value=True, default=True),
            #        disnake.SelectOption(label="Neaktivní", value=False),
            #    ],
            # ),
            disnake.ui.TextInput(
                label="Stav (True/False = Zapnuto/Vypnuto)",
                placeholder="Stav (True/False = Zapnuto/Vypnuto)",
                custom_id="enabled",
                style=disnake.TextInputStyle.short,
                min_length=4,
                max_length=5,
                required=True,
                value=str(rule.enabled) if self.is_edit() else str(True),
            ),
            disnake.ui.TextInput(
                label="Role (zadávej názvy, nebo ID; odděluj čárkou)",
                placeholder="Zadej role (zadávej názvy, nebo ID; odděluj čárkou)",
                custom_id="roles",
                style=disnake.TextInputStyle.single_line,
                required=True,
                value=",".join([role.name for role in selected_roles_data]),
            ),
        ]

        # TODO: Prepared for modal select menus.
        # if self.is_edit() and not rule.enabled:
        #     # Change selected value if rule is not enabled. Otherwise keep default values.
        #     components[2].options[0].default = False
        #     components[2].options[1].default = True
        # for i in range(0, len(guild_role_groups)):
        #     role_group = guild_role_groups[i]
        #     components.append(
        #         disnake.ui.Select(
        #             custom_id=f"roles:{i}",
        #             placeholder="Výběr rolí",
        #             options=[
        #                 disnake.SelectOption(
        #                     label=role.name,
        #                     value=str(role.id),
        #                     default=role.id in selected_roles,
        #                     emoji=role.emoji,
        #                 )
        #                 for role in role_group
        #             ],
        #             min_values=0,
        #             max_values=min(25, len(guild_roles)),
        #         )
        #     )

        super().__init__(
            title="Modifikace verifikačního pravidla"
            if self.is_edit()
            else "Vytvoření verifikačního pravidla",
            custom_id="dynamic_verify_edit",
            timeout=300,
            components=components,
        )

    def is_edit(self):
        return self.rule is not None

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        manager = DynamicVerifyManager(inter.bot)
        rule_id = await self.get_rule_id(inter, manager)
        name = str(inter.text_values["name"]).strip()
        enabled = await self.get_enable_state(inter)
        roles = await self.get_roles(inter)

        if rule_id is None or enabled is None or roles is None:
            return  # Validation failed.

        rule = self.rule if self.is_edit() else DynamicVerifyRule()

        rule.id = rule_id
        rule.name = name
        rule.enabled = enabled
        rule.set_role_ids([role.id for role in roles])

        manager.verify_repo.update_rule(rule)
        await inter.response.send_message("Hotovo")  # TODO Vhodnější text. # noqa

        # TODO: Messages

    async def get_rule_id(
        self, inter: disnake.ModalInteraction, manager: DynamicVerifyManager
    ) -> Union[str, None]:
        rule_id = str(inter.text_values["id"]).strip()

        if rule_id == "None":
            await inter.response.send_message("Nebylo zadáno platné ID pravidla.")
            return None

        rule = manager.get_rule(rule_id)
        if rule is not None:
            if self.is_edit() and self.rule.id == rule_id:
                return rule_id  # Same rule ID in edit mode is valid.
            await inter.response.send_message("ID s tímto pravidlem již existuje.")
            return None

        return rule_id

    async def get_enable_state(
        self, inter: disnake.ModalInteraction
    ) -> Union[bool, None]:
        enabled = str(inter.text_values["enabled"]).strip()

        if enabled.lower() == "true":
            return True
        elif enabled.lower() == "false":
            return False
        else:
            await inter.response.send_message(
                "Nepovolený stav. Lze zadat pouze True/False"
            )
            return None

    async def get_roles(
        self, inter: disnake.ModalInteraction
    ) -> Union[List[disnake.Role], None]:
        role_data = str(inter.text_values["roles"]).strip().split(",")
        role_data = [role.strip() for role in role_data]
        roles = []

        for item in role_data:
            if item.isnumeric():
                # Search by Role ID
                role = inter.guild.get_role(int(item))
                if role is None:
                    await inter.response.send_message(f"Role s ID `{item}` neexistuje")
                    return None
                roles.append(role)
            else:
                # Search by role name
                role = disnake.utils.get(inter.guild.roles, name=item)
                if role is None:
                    await inter.response.send_message(
                        f"Role s názvem `{item}` neexistuje"
                    )
                    return None
                roles.append(role)

        if len(roles) == 0:
            await inter.response.send_message("Nebyla nalezena žádná role.")
            return None
        return list(set(roles))