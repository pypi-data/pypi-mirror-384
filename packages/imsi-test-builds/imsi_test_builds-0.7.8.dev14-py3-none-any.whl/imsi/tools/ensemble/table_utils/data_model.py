from pydantic import BaseModel, Field, FilePath, DirectoryPath, ConfigDict
from omegaconf import DictConfig, ListConfig
from typing import Any, Dict, List, Tuple, Optional, Annotated
from imsi.tools.ensemble.table_utils.table_utils import colour, replace_aliases


def _extract_lists(
    data: Dict[str, Any], parent_keys: List[str] = None
) -> Dict[Tuple[str, ...], List[Any]]:
    """Recursively extract lists from a nested dictionary."""
    if parent_keys is None:
        parent_keys = []

    listed_vars = {}
    for key, value in data.items():
        current_keys = parent_keys + [key]
        if isinstance(value, (ListConfig, list)):
            listed_vars[tuple(current_keys)] = value
        elif isinstance(value, (DictConfig, dict)):
            # Recurse into nested dictionaries
            nested_lists = _extract_lists(value, current_keys)
            listed_vars.update(nested_lists)
    return listed_vars


def validate_list_lengths(config_dict: dict):
    """Ensure all list values in a flat dictionary have the same length."""
    list_lengths = {key: len(val) for key, val in config_dict.items()}

    if not list_lengths:
        return

    expected_len = next(iter(list_lengths.values()))
    mismatched = {k: v for k, v in list_lengths.items() if v != expected_len}

    if mismatched:
        print(colour("❌ Inconsistent list lengths found:", "red"))
        for key, length in mismatched.items():
            print(f"  {key}: length {length} (expected {expected_len})")
        raise ValueError("All list values must have the same length.")


class EnsembleLevelVars(BaseModel):
    """Class with config variables -- logically configure so that
    they only require one definition for a given ensemble run."""

    user: Annotated[str, Field(..., description="User ID")]
    run_directory: Optional[DirectoryPath] = "."
    config_table: Optional[FilePath] = None
    aliases: Optional[dict] = None
    share_repo: Optional[bool] = False


class MemberLevelVars(BaseModel):
    """Class provides main interaction with entry config data."""
    model_config: Optional[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)
    config_data: DictConfig = Field(..., description="Configuration data for the ensemble")

    @classmethod
    def get_listed_vars(cls, config_data) -> Dict[Tuple[str, ...], List[Any]]:
        """Get all lists from the configuration data, including nested ones."""
        listed_vars = _extract_lists(config_data)
        # check that all lists in the dictionary are the same length
        validate_list_lengths(listed_vars)

        return listed_vars

    @property
    def ensemble_size(self) -> int:
        """Return the size of the ensemble, assuming all lists have the same size."""
        varlist = self.get_listed_vars(self.config_data)
        return len(list(varlist.values())[0]) if varlist else None


class InputConfig(BaseModel):
    ensemble_level: EnsembleLevelVars
    member_level: MemberLevelVars

    def model_post_init(self, __context):

        listed_vars = MemberLevelVars.get_listed_vars(self.member_level.config_data)
        sizes = [
            len(value) for value in listed_vars.values() if not isinstance(value, str)
        ]
        listed_vars_size = {
            tuple(key): len(value)
            for key, value in listed_vars.items()
            if not isinstance(value, str)
        }

        if self.member_level.config_data and not self.ensemble_level.config_table:
            if not sizes:
                raise ValueError(
                    "No lists found in config. For a single ensemble member, use 'name: [var]' in the config."
                )

            if len(set(sizes)) != 1:
                size_report = {":".join(key): val for key, val in listed_vars_size.items()}

                v = {}
                for key, value in sorted(size_report.items()):
                    v.setdefault(value, []).append(key)

                raise ValueError(
                    f"All lists in the configuration data must have the same size.\n"
                    f"Sizes are {v}"
                )

        # replace aliases in member_level if they exist and are provided
        if self.ensemble_level.aliases:
            self.member_level.config_data = replace_aliases(
                self.member_level.config_data, self.ensemble_level.aliases
            )
