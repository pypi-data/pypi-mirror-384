from pydantic import BaseModel, Field

from cattle_grid.extensions.examples.simple_storage.config import determine_url_start


class HtmlDisplayConfiguration(BaseModel):
    prefix: str = Field(
        default="/html_display/object/",
        description="Path to use before the generated uuid. The protocol and domain will be extracted from the actor id. See [determine_url_start][cattle_grid.extensions.examples.simple_storage.config.determine_url_start].",
    )

    html_prefix: str = Field(
        default="/@", description="Prefix to use for the url pages"
    )

    automatically_add_users_to_group: bool = Field(
        default=False,
        description="Causes an actor that sends a html_display_name message to be added to the html_display group",
    )

    def url_start(self, actor_id):
        return determine_url_start(actor_id, self.prefix)

    def html_url_start(self, actor_id):
        """
        Determines the start of an url

        ```python
        >>> config = HtmlDisplayConfiguration()
        >>> config.html_url_start("http://actor.example/some/id")
        'http://actor.example/@'

        ```
        """
        return determine_url_start(actor_id, self.html_prefix)

    def html_url(self, actor_id, actor_name):
        """
        Determines the start of an url

        ```python
        >>> config = HtmlDisplayConfiguration()
        >>> config.html_url("http://actor.example/some/id", "john")
        'http://actor.example/@john'

        ```
        """
        return self.html_url_start(actor_id) + actor_name
