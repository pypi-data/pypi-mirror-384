from imsi.tools.ensemble.table_utils.data_model import (
    EnsembleLevelVars,
    MemberLevelVars,
)
from imsi.tools.ensemble.table_utils.table_utils import (
    add_nested_key,
    colour,
    validate_table_data,
    warn_on_overlapping_keys,
)

from pydantic import BaseModel, FilePath
from omegaconf import DictConfig, OmegaConf
from typing import Any, Dict, List, Tuple, Optional
import copy
import pandas as pd
import warnings

warnings.simplefilter("always", DeprecationWarning)


def validate_list_lengths(member_level_size: int, table_length: int):
    """Ensure all list values in a flat dictionary have the same length."""

    # check that broadcasted_members and table have the same length
    if member_level_size is not None and member_level_size != table_length:
        raise ValueError(
            colour(
                f"\n❌  The number of broadcasted members ({member_level_size}) does not match the number of table entries ({table_length}). ",
                "red"
            )
        )


class YAMLVars(BaseModel):
    member_level: MemberLevelVars

    def get_table(self, show_diffs):
        broadcasted_members = BroadcastedConfigList(member_level=self.member_level)
        cfg_list = broadcasted_members.expand_config()
        cfg_list = validate_table_data(cfg_list)
        return cfg_list


class CSVTableVars(BaseModel):
    """Class with supporting functions to read and process an ensemble text file."""

    ensemble_level: EnsembleLevelVars
    member_level: MemberLevelVars

    def read_table(self) -> DictConfig:
        """Load csv as pandas dataframe and inject heirarchy into configuration object"""
        data = pd.read_csv(
            self.ensemble_level.config_table,
            comment="#",
            sep=r"\s*,\s*",
            engine="python",
            dtype_backend="pyarrow"  # preserves atual integer types instead of converting to float
        )
        # replace missing values to be explicit None
        data = data.replace({float("nan"): None})
        data_dict = OmegaConf.create({col: data[col].tolist() for col in data.columns})
        config_dict = OmegaConf.create({})

        for key in data_dict.keys():
            if ":" in key:
                # traverse key to add to nested dictionary
                try:
                    add_nested_key(config_dict, key, data_dict[key])
                except Exception:
                    raise ValueError(
                        f"Error adding key {key} to data_dict. This is likely caused by conflicting definitions of key paths provided as both a parameter and nested key."
                    )
            else:
                # Directly assign the list if it's not a nested key
                config_dict[key] = data_dict[key]
        
        return config_dict

    def get_table(self, show_diffs):
        """Combine the csv and member level config data to produce a list of configurations."""
        # create and resulve the table
        table = self.read_table()
        table_length = len(list(MemberLevelVars.get_listed_vars(table).values())[0])
        # update the member level data with the table data
        validate_list_lengths(self.member_level.ensemble_size, table_length)

        warn_on_overlapping_keys(
            self.member_level.config_data, table
        )

        member_data = OmegaConf.merge(self.member_level.config_data, table)
        # expand to list of configurations
        cfg_list = BroadcastedConfigList(
            member_level=MemberLevelVars(config_data=member_data)
        ).expand_config(ensemble_size=table_length)

        # remove any keys with explicit None values
        cfg_list = validate_table_data(cfg_list, show_diffs)

        return cfg_list


class TextTableVars(CSVTableVars):

    """Inherit same functionality from CSVTableVars but with different read_table method."""

    def read_table(self):
        """Load text table as pandas dataframe and inject heirarchy into configuration object"""

        warnings.warn(
            colour(
                "\n⚠️  Text files are a legacy ensemble tool input and will be deprecated. Please provide a csv table instead.",
                "yellow"
            ),
            DeprecationWarning,
        )

        data = pd.read_csv(
            self.ensemble_level.config_table,
            sep=r"\s+",
            comment="#",
        )
        data_dict = {col: data[col].tolist() for col in data.columns}
        data_dict = OmegaConf.create(data_dict)
        config_dict = OmegaConf.create({})

        for key in data_dict.keys():
            if ":" in key:
                add_nested_key(config_dict, key, data_dict[key])
            else:
                # Directly assign the list if it's not a nested key
                config_dict[key] = data_dict[key]

        return config_dict


class BroadcastedConfigList(BaseModel):
    """Takes information from the broadcasted vars and expands into a list of configurations"""

    member_level: MemberLevelVars

    def _set_nested_value(
        self, data: Dict[str, Any], keys: Tuple[str, ...], value: Any
    ):
        """Recursively set a value in a nested dictionary."""
        for key in keys[:-1]:
            data = data[key]
        data[keys[-1]] = value

    def expand_config(self, ensemble_size=None) -> List[Dict[str, Any]]:
        """Expand the configuration to produce a list of configurations, one for each ensemble member."""

        if not self.member_level.config_data:
            return []
        
        ensemble_size = self.member_level.ensemble_size if ensemble_size is None else ensemble_size
        base_config = self.member_level.config_data
        listed_vars = MemberLevelVars.get_listed_vars(base_config)

        config_list = []
        for i in range(ensemble_size):
            member_config = copy.deepcopy(base_config)
            for keys, value in listed_vars.items():
                self._set_nested_value(member_config, keys, value[i])
            config_list.append(member_config)

        return OmegaConf.create(config_list)


class YAMLTableVars(BaseModel):
    member_level: MemberLevelVars
    config_table: Optional[FilePath] = None

    def get_table(
        self,
        show_diffs
    ):
        if self.config_table is not None:
            table = OmegaConf.load(self.config_table)
        else:
            raise ValueError("No config table provided.")

        validate_list_lengths(self.member_level.ensemble_size, len(table))

        # create a broadcasted config list from the member level data
        broadcasted_members = BroadcastedConfigList(
            member_level=MemberLevelVars(config_data=self.member_level.config_data)
        ).expand_config(ensemble_size=len(table))

        if broadcasted_members:
            for i in range(len(table)):
                warn_on_overlapping_keys(
                    broadcasted_members[i], table[i]
                )
                table[i] = OmegaConf.merge(
                    broadcasted_members[i], table[i]
                )

        table = validate_table_data(table, show_diffs=show_diffs)

        return table
