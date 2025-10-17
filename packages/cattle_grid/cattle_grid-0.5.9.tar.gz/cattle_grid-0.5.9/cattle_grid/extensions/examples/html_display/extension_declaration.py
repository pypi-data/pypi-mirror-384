from cattle_grid.extensions import Extension
from cattle_grid.extensions.util import lifespan_for_sql_alchemy_base_class

from .config import HtmlDisplayConfiguration
from .database import Base

extension = Extension(
    name="simple html display",
    module=__name__,
    lifespan=lifespan_for_sql_alchemy_base_class(Base),
    config_class=HtmlDisplayConfiguration,
)
extension.rewrite_group_name = "html_display"
extension.rewrite_rules = {"publish_object": "html_display_publish_object"}
