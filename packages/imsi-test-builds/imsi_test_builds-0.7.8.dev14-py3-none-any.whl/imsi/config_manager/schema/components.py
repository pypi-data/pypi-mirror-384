from pydantic import BaseModel, RootModel, Field, ConfigDict, field_validator
from typing import Dict, Optional, Any
from pathlib import Path


def get_imsi_config_directory() -> Path:
    """Determine the imsi configuration directory from assumptions.
    Either you're in a setup directory or your cwd is src/imsi-config."""
    src_dir_exists = Path('src', 'imsi-config').exists()
    # this is how I need to check if the cwd is a valid imsi config dir
    is_cwd_valid_config = Path("version_requirements.yaml").exists()

    if not src_dir_exists and not is_cwd_valid_config:
        raise FileNotFoundError(
            'Neither src/imsi-config exists nor is the current working directory a valid imsi configuration directory.'
        )

    if src_dir_exists:
        return Path('src', 'imsi-config')
    elif is_cwd_valid_config:
        return Path.cwd()
    

class ComponentResources(BaseModel):
    model_config = ConfigDict(extra='allow')
    mpiprocs: int = Field(..., description='Required number of MPI processes.')
    ompthreads: int = Field(..., description='Required number of OpenMP threads.')


class Component(BaseModel):
    model_config = ConfigDict(extra='allow')
    exec: str = Field(..., description='Executable name.')
    resources: ComponentResources
    config_dir: Path = Field(..., description='Path to configuration directory.')
    # namelists are an option nested dictionaries
    namelists: Optional[Dict[str, dict]] = {}
    compilation: Optional[Dict[str, dict]] = {}
    input_files: Optional[Dict[str, str]] = None
    output_files: Optional[Dict[str, str]] = None
    directory_packing: Optional[Any] = None

    @classmethod
    def check_each_path(self, paths: Dict[str, str], values: Dict[str, str]) -> None:
        """Check if each path in the dictionary exists."""
        # check if the cwd is a valid imsi config directory using uim

        if not values.data.get('config_dir'):
            raise FileNotFoundError(
                f'Config directory {values.data.get("config_dir")} does not exist.'
            )

        full_path_base = get_imsi_config_directory()

        for filename in paths:
            full_path = Path(full_path_base, values.data.get('config_dir'), filename)
            if not full_path.exists():
                raise FileNotFoundError(
                    f'File {filename} expected at {full_path} does not exist.'
                )

    @field_validator('config_dir')
    def config_dir_must_exist(cls, config_dir: Path) -> str:
        """This modifies config_dir to be at the defined subconfig."""
        full_path_base = get_imsi_config_directory()
        if not Path(full_path_base, config_dir).exists():
            raise FileNotFoundError(f'Config directory {config_dir} does not exist.')
        # important: return plain string
        return str(config_dir)

    @field_validator('namelists')
    def namelist_files_must_exist(
        cls, namelist_paths: Optional[Dict[str, Path]], values
    ):
        cls.check_each_path(namelist_paths, values) if namelist_paths else None
        return namelist_paths

    @field_validator('compilation')
    def compilation_file_must_exist(
        cls, compilation: Optional[Dict[str, Path]], values
    ):
        cls.check_each_path(compilation, values) if compilation else None
        return compilation


class Components(RootModel[Dict[str, Component]]):
    """Dictionary-like container of Components."""
    pass
