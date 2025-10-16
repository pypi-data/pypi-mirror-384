from imsi.tools.ensemble.table_utils.data_model import (
    EnsembleLevelVars,
    MemberLevelVars,
    InputConfig,
)
from imsi.tools.ensemble.table_utils.table_model import (
    CSVTableVars,
    YAMLTableVars,
    YAMLVars,
    TextTableVars,
)

from imsi.tools.ensemble.table_utils.table_utils import replace_aliases


def load_config(cfg, show_diffs):

    ensemble_config = InputConfig(
        ensemble_level=EnsembleLevelVars(**cfg.ensemble_level),
        member_level=MemberLevelVars(config_data=cfg.member_level),
    )

    table_class_map = {
        ".csv": CSVTableVars(
            member_level=ensemble_config.member_level,
            ensemble_level=ensemble_config.ensemble_level,
        ),
        ".txt": TextTableVars(
            member_level=ensemble_config.member_level,
            ensemble_level=ensemble_config.ensemble_level,
        ),
        ".yaml": YAMLTableVars(
            member_level=ensemble_config.member_level,
            config_table=ensemble_config.ensemble_level.config_table,
        ),
        None: YAMLVars(member_level=ensemble_config.member_level),
    }

    config_table = ensemble_config.ensemble_level.config_table
    table = table_class_map.get(config_table.suffix if config_table else None)

    if table is None:
        raise ValueError(f"Unsupported file type: {config_table}")

    constructed_table = table.get_table(show_diffs=show_diffs)

    if ensemble_config.ensemble_level.aliases:
        for i, table in enumerate(constructed_table):
            # replace aliases in the table data
            constructed_table[i] = replace_aliases(
                table, ensemble_config.ensemble_level.aliases
            )
    return ensemble_config, constructed_table
