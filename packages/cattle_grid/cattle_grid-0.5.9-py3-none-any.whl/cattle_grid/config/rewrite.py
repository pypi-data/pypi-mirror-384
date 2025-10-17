from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class RewriteRules(BaseModel):
    """Describes the rewrite rules"""

    rules: dict[str, str] = Field(description="Mapping from old rule to new rule")


@dataclass
class RewriteConfiguration:
    """Configuration of the rewrite process"""

    ruleset: dict[str, RewriteRules] = field(
        metadata={"description": "mapping between group names and rewrite rules"}
    )

    def rewrite(self, method_name: str, group_names: list[str]) -> str:
        """rewrites the method_name"""
        for group_name in group_names:
            rules = self.ruleset.get(group_name)

            if rules and method_name in rules.rules:
                return rules.rules[method_name]

        return method_name

    def add_rules(
        self, group_name: str, rules: dict[str, str], overwrite: bool = False
    ):
        """Adds new rules to the ruleset"""
        if not overwrite and group_name in self.ruleset:
            return

        self.ruleset[group_name] = RewriteRules.model_validate({"rules": rules})

    @staticmethod
    def from_rules(rules: dict[str, dict[str, str]] | None):
        """
        Constructs the RewriteConfiguration

        ```
        >>> rules = {"old": "new"}
        >>> config = RewriteConfiguration.from_rules({"group": rules})
        >>> config
        RewriteConfiguration(ruleset={'group': RewriteRules(rules={'old': 'new'})})

        >>> group_names = ["group"]
        >>> config.rewrite("unchanged", group_names)
        'unchanged'

        >>> config.rewrite("old", group_names)
        'new'

        ```
        """
        if rules:
            mapped = {
                group: RewriteRules.model_validate({"rules": rule})
                for group, rule in rules.items()
            }
        else:
            mapped = {}

        return RewriteConfiguration(ruleset=mapped)
