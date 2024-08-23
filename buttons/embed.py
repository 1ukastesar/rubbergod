import disnake

import utils
from buttons.base import BaseView
from config.messages import Messages
from features.leaderboard import LeaderboardPageSource


class ViewRowFull(Exception):
    """Adding a Item to already filled row"""

    pass


class PaginationView(BaseView):
    message: disnake.Message

    def __init__(
        self,
        author: disnake.User,
        embeds: list[disnake.Embed],
        row: int = 0,
        perma_lock: bool = False,
        roll_around: bool = True,
        end_arrow: bool = True,
        page_source: LeaderboardPageSource = None,
        timeout: int = 300,
        page: int = 1,
        show_page: bool = False,
    ):
        """Embed pagination view

        :param disnake.User author: command author, used for locking pagination.
        :param List[disnake.Embed] embeds: List of embeds to be paginated.
        :param int row: On which row should the buttons be added, defaults to the first row.
        :param bool perma_lock: If True, only the message author can change pages without the dynamic lock button.
        :param bool roll_around: If True, after reaching the last page, roll around to the first page.
        :param bool end_arrow: If True, use the '⏩' button as well.
        :param LeaderboardPageSource page_source: Used for long leaderboards, where embeds should contain one embed.
        :param int timeout: Seconds until disabling interaction, use None for always enabled.
        :param int page: Starting page.
        :param bool show_page: Show the page number at the bottom of the embed, e.g.: 2/4.
        """
        self.page = page
        self.author = author
        self.locked = False
        self.page_source = page_source
        self.roll_around = roll_around
        self.perma_lock = perma_lock
        if not page_source:
            self.max_page = len(embeds)
        else:
            self.max_page = page_source.get_max_pages()
            end_arrow = False
        self.embeds = embeds
        super().__init__(timeout=timeout)
        if self.max_page <= 1:
            return
        if show_page:
            self.add_page_numbers()
        self.add_item(
            disnake.ui.Button(
                emoji="⏪", custom_id="embed:start_page", row=row, style=disnake.ButtonStyle.primary
            )
        )
        self.add_item(
            disnake.ui.Button(
                emoji="◀", custom_id="embed:prev_page", row=row, style=disnake.ButtonStyle.primary
            )
        )
        self.add_item(
            disnake.ui.Button(
                emoji="▶", custom_id="embed:next_page", row=row, style=disnake.ButtonStyle.primary
            )
        )
        if end_arrow:
            self.add_item(
                disnake.ui.Button(
                    emoji="⏩", custom_id="embed:end_page", row=row, style=disnake.ButtonStyle.primary
                )
            )
        if not perma_lock:
            # if permanent lock is applied, dynamic lock is removed from buttons
            self.lock_button = disnake.ui.Button(
                emoji="🔓", custom_id="embed:lock", row=0, style=disnake.ButtonStyle.success
            )
            self.add_item(self.lock_button)

    @property
    def embed(self):
        if self.page_source is None:
            return self.embeds[self.page - 1]
        else:
            page = self.page_source.get_page(self.page - 1)
            return self.page_source.format_page(page)

    @embed.setter
    def embed(self, value):
        self.embeds[self.page - 1] = value

    def add_item(self, item: disnake.ui.Item) -> None:
        row_cnt = 0
        for child in self.children:
            if item.emoji == child.emoji:
                child.disabled = False
                return
            if item.row == child.row:
                row_cnt += 1
        if row_cnt >= 5:
            # we are trying to add new button to already filled row
            raise ViewRowFull
        super().add_item(item)

    def add_page_numbers(self):
        """Set footers with page numbers for each embed in list"""
        for page, embed in enumerate(self.embeds):
            utils.embed.add_author_footer(
                embed, self.author, additional_text=[f"Page {page+1}/{self.max_page}"]
            )

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if interaction.data.custom_id == "embed:lock":
            if interaction.author.id == self.author.id:
                self.locked = not self.locked
                if self.locked:
                    self.lock_button.style = disnake.ButtonStyle.danger
                    self.lock_button.emoji = "🔒"
                else:
                    self.lock_button.style = disnake.ButtonStyle.success
                    self.lock_button.emoji = "🔓"
                await interaction.response.edit_message(view=self)
            else:
                await interaction.send(Messages.embed_not_author, ephemeral=True)
            return False
        ids = ["embed:start_page", "embed:prev_page", "embed:next_page", "embed:end_page"]
        if interaction.data.custom_id not in ids or self.max_page <= 1:
            return False
        if (self.perma_lock or self.locked) and interaction.author.id != self.author.id:
            await interaction.send(Messages.embed_not_author, ephemeral=True)
            return False

        self.page = utils.embed.pagination_next(
            interaction.data.custom_id, self.page, self.max_page, self.roll_around
        )
        await interaction.response.edit_message(embed=self.embed)
        return True

    async def on_timeout(self):
        await self.message.edit(view=None)
