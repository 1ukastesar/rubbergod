import disnake

from buttons.embed import EmbedView
from config.messages import Messages
from repository import review_repo
from features.review import ReviewManager
import utils


class ReviewView(EmbedView):

    def __init__(self, bot, embeds):
        self.manager = ReviewManager(bot)
        self.repo = review_repo.ReviewRepository()
        self.total_pages = len(embeds)
        super().__init__(embeds, row=2, end_arrow=False, timeout=300)
        self.check_text_pages()
        # if there aren't any reviews remove buttons
        if len(self.embed.fields) < 1:
            to_remove = []
            for child in self.children:
                to_remove.append(child)
            for button in to_remove:
                self.remove_item(button)

    def check_text_pages(self):
        if len(self.embed.fields) > 3 and self.embed.fields[3].name == "Text page":
            self.add_item(
                disnake.ui.Button(
                    emoji="🔽",
                    custom_id="review:next_text",
                    style=disnake.ButtonStyle.primary,
                    row=2
                )
            )
            self.add_item(
                disnake.ui.Button(
                    emoji="🔼",
                    custom_id="review:prev_text",
                    style=disnake.ButtonStyle.primary,
                    row=2
                )
            )
        else:
            to_remove = []
            for child in self.children:
                if "text" in child.custom_id:
                    to_remove.append(child)
            for button in to_remove:
                self.remove_item(button)

    def add_item(self, item: disnake.ui.Item) -> None:
        for child in self.children:
            if item.custom_id in child.custom_id:
                return
        return super().add_item(item)

    @property
    def review_id(self):
        return self.embed.footer.text.split("|")[2][5:]

    async def handle_vote(self, interaction: disnake.MessageInteraction, vote: bool = None):
        review = self.repo.get_review_by_id(self.review_id)
        if review:
            member_id = str(interaction.author.id)
            if member_id == review.member_ID:
                await interaction.send(Messages.review_vote_own, ephemeral=True)
                return
            if vote is not None:
                self.manager.add_vote(self.review_id, vote, member_id)
            else:
                self.repo.remove_vote(self.review_id, member_id)
            self.embed = self.manager.update_embed(self.embed, review)
            await interaction.response.edit_message(embed=self.embed)

    @disnake.ui.button(emoji="👍", custom_id="review:like", style=disnake.ButtonStyle.success)
    async def like(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await self.handle_vote(interaction, True)

    @disnake.ui.button(emoji="🛑", custom_id="review:vote_remove")
    async def vote_remove(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await self.handle_vote(interaction)

    @disnake.ui.button(emoji="👎", custom_id="review:dislike", style=disnake.ButtonStyle.danger)
    async def dislike(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await self.handle_vote(interaction, False)

    @disnake.ui.button(emoji="❔", custom_id="review:help", style=disnake.ButtonStyle.primary)
    async def help(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.send(Messages.reviews_reaction_help, ephemeral=True)
        return

    async def interaction_check(self, interaction: disnake.Interaction) -> None:
        if "review" not in interaction.data.custom_id:
            # interaction from super class
            await super().interaction_check(interaction)
            self.check_text_pages()
            # update view
            await interaction.edit_original_message(view=self)
            return False
        if "text" in interaction.data.custom_id and self.embed.fields[3].name == "Text page":
            # text page pagination
            review = self.repo.get_review_by_id(self.review_id)
            if review:
                pages = self.embed.fields[3].value.split("/")
                text_page = int(pages[0])
                max_text_page = int(pages[1])
                next_text_page = utils.pagination_next(interaction.data.custom_id, text_page, max_text_page)
                if next_text_page:
                    self.embed = self.manager.update_embed(self.embed, review, next_text_page)
                    await interaction.response.edit_message(embed=self.embed)
            return False
        # fallback to buttons callbacks
        return True