"""This module provides classes and utilities for managing configurations,
including models, experiments, machines, compilers, and their interactions.

The module includes classes for defining configuration elements such as
Model, Experiment, Machine, and Compiler. Additionally, it provides a
Configuration class for composing these elements into a complete configuration.

ConfigManager is a class used to establish configuration objects and
facilitate saving and loading configurations for later use. The module also
includes abstract classes such as ConfigDatabase for defining an abstract
interface for a configuration database and its concrete implementation JsonConfigDatabase.

   Lastly, the module contains Factory classes (eg. CompilerFactory),
   which provide methods for creating instances of analogous classes (eg. Compiler).

The module is designed to support flexibility in configuration management,
allowing configurations to be composed, serialized, and deserialized.

This module is a WIP. It is next required to create infrastructure
modules that use the configurations created here.

Neil Swart, April 2024
"""
# TODO:
#   - Add a setup / user config (selections incoming from setup / subsequent "config" calls)
#   - Perhaps represent/process shell_parameters more explicitly

from typing import Dict
import copy
import pickle
from pydantic import BaseModel
import yaml

from imsi.utils.dict_tools import (
    parse_config_inheritance,
    update,
    recursive_lookup,
    replace_curlies_in_dict,
)
from imsi.config_manager.databases import ConfigDatabase, JsonConfigDatabase, YAMLConfigDatabase
from imsi.config_manager.schema.machine import Machine
from imsi.config_manager.schema.model import Model
from imsi.config_manager.schema.experiment import Experiment
from imsi.config_manager.schema.components import Components
from imsi.config_manager.schema.compiler import Compiler
from imsi.config_manager.schema.sequencing import Sequencing
from imsi.config_manager.schema.post_processing import PostProcessing
from imsi.config_manager.schema.setup_params import SetupParams
from imsi.config_manager.schema.utilities import Utilities


def database_factory(
    imsi_config_path: str, config_type: str = "yaml"
) -> ConfigDatabase:
    """Factory function to create a ConfigDatabase instance based on the config_type"""

    config_types = {
        "json": JsonConfigDatabase(imsi_config_path),
        "yaml": YAMLConfigDatabase(imsi_config_path),
    }

    try:
        return config_types[config_type]
    except KeyError:
        raise ValueError(f"Invalid config_type: {config_type}")


class CompilerFactory:
    """Class containing methods to instantiate an instance of Compiler.
    Like for machines, several parsing functions are required and encapsulated here.
    """

    @staticmethod
    def create_from_database(
        db: ConfigDatabase, machine: Machine, compiler_name: str = None
    ):
        compiler_name = compiler_name or machine.default_compiler
        machine.validate_compiler(compiler_name=compiler_name)
        compiler_config = db.get_parsed_config("compilers", compiler_name)
        return Compiler(name=compiler_name, **compiler_config)


class SequencingFactory:
    """Class containing methods to instantiate an instance of Sequencing.
    Like for machines, several parsing functions are required and encapsulated here.
    """

    @staticmethod
    def create_from_database(
        db: ConfigDatabase,
        machine: Machine,
        sequencer_name: str,
        flow_name: str = None,
        model_type: str = None,
    ):
        """Create a sequencing instance given the config db, the machine, sequencer and flow names"""

        sequencing_config = {}  # To build up here
        sequencing_configs = db.get_config("sequencing")  # Everything from the DB
        # Validity checks
        SequencingFactory.verify_sequencing_structure(sequencing_configs)

        # Run dates
        sequencing_config["run_dates"] = sequencing_configs["run_dates"]

        # This is the sequencer specific content (encapsulate in a function)
        sequencing_config["sequencer"] = SequencingFactory.set_sequencer_config(
            sequencer_name=sequencer_name,
            sequencers=sequencing_configs["sequencers"],
            machine_name=machine.name,
        )

        # Set default flow if it is not defined
        flow_name = flow_name or SequencingFactory.determine_default_flow(
            model_type,
            sequencer_name,
            sequencing_config["sequencer"].get("baseflows"),
            flows=sequencing_configs["sequencing_flow"],
            machine=machine,
        )

        sequencing_config["sequencing_flow"] = SequencingFactory.set_flow_config(
            flow_name=flow_name,
            flows=sequencing_configs["sequencing_flow"],
            sequencer_name=sequencer_name,
            sequencer_config=sequencing_config["sequencer"],
            machine=machine,
            model_type=model_type,
        )

        # Resolve sequencer config. It is a bit messy at there is some iterative dependency resolving between sequencer and flow
        #  flow_name.split('-')[0] is extracting the baseflow using the name convention for flows.
        try:
            sequencing_config["sequencer"]["baseflows"] = sequencing_config[
                "sequencer"
            ]["baseflows"][model_type][flow_name.split("-")[0]]
        except:
            raise KeyError(
                "Error is setting sequencer_config, using the flow name: {flow_name}. Is the flow_name valid?"
            )
        return Sequencing(**sequencing_config)

    @staticmethod
    def verify_sequencing_structure(sequencing_config: dict):
        """
        Checks what we got from the db includes mandatory sections
        (replaceable by schema validation?)
        """
        required_keys = ["run_dates", "sequencing_flow", "sequencers"]
        for key in required_keys:
            if key not in sequencing_config.keys():
                raise KeyError(
                    f"The key {key} is not in the 'sequencing' configuration "
                    "provided, but is a required element"
                )

    @staticmethod
    def determine_default_flow(
        model_type: str,
        sequencer_name: str,
        sequencer_baseflows: dict,
        flows,
        machine: Machine,
    ):
        """Get the default sequencing flow, which handles the selected model_type, and
        also has configuration support for the selected sequencer and machine.

        Parameters:
         model_type (str): The model configuration, e.g. ESM, AMIP or OMIP
        """
        if model_type not in sequencer_baseflows:
            supported_model_type = ", ".join(sequencer_baseflows.keys())
            raise KeyError(
                f"The selected model configuration: {model_type} is not supported by "
                f"available workflows of the selected sequencer: {sequencer_name}. "
                f"Supported model configurations are: {supported_model_type}"
            )

        # All baseflows for this sequencer, and this model_type
        base_flows = sequencer_baseflows[model_type].keys()

        # The platform/machine specific implementation of baseflows is denoted with a suffix on baseflow
        # This will return the first baseflow/machine specific flow in the list (which is constrain to be
        # only those suppoting the specific model_type)
        for baseflow in base_flows:
            machine_specific_flow = f"{baseflow}-{machine.default_sequencing_suffix}"  # convention for the naming
            if machine_specific_flow in flows:
                return machine_specific_flow
        supported_base_flows = ", ".join(base_flows)
        raise KeyError(
            f"Could not determine a default sequencing flow for sequencer: {sequencer_name} "
            f"on machine: {machine.name}/{machine.default_sequencing_suffix} that supports model_type: {model_type}. "
            f"Support baseflows found for {model_type} are: {supported_base_flows}. "
            f"Machine specific version(s) for {machine.default_sequencing_suffix} are "
            "not implemented but required."
        )

    @staticmethod
    def set_sequencer_config(sequencer_name: str, sequencers: dict, machine_name: str):
        # This is the sequencer specific content (encapsulate in a function)
        if sequencer_name not in sequencers:
            supported_sequencers = ", ".join(sequencers.keys())
            raise KeyError(
                f"Selected sequencer {sequencer_name} not in list of configured sequencers {supported_sequencers}"
            )

        sequencer_config = parse_config_inheritance(sequencers, sequencer_name)

        # Validation
        if "supported_machines" not in sequencer_config:
            raise KeyError(
                f"No 'supported_machines' field in sequencer definition for {sequencer_name}"
            )
        if machine_name not in sequencer_config.get("supported_machines"):
            supported_machines = ", ".join(sequencer_config.get("supported_machines"))
            raise KeyError(
                f"Machine {machine_name} not listed as supported by sequencer {sequencer_name}. "
                f"Supported machines for {sequencer_name} are {supported_machines}. "
                "Either change machine or sequencer."
            )
        if not sequencer_config or "baseflows" not in sequencer_config:
            raise ValueError(
                f"The sequencer config for {sequencer_name} does not contain a 'baseflows' definition"
            )

        return sequencer_config

    @staticmethod
    def set_flow_config(
        flow_name: str,
        flows: dict,
        sequencer_name: str,
        sequencer_config: dict,
        machine: Machine,
        model_type: str,
    ):
        if flow_name not in flows:
            supported_flows = ", ".join(flows.keys())
            raise KeyError(
                f"Selected sequencing flow {flow_name} not in list of configured flows:"
                f"{supported_flows}"
            )
        flow_config = parse_config_inheritance(flows, flow_name)

        # Validation
        if not flow_config and "base_flow" in flow_config:
            raise ValueError(
                "The flow configuration for flow {flow_name} is not valid "
                "or does not contain the required 'base_flow'"
            )
        base_flow = flow_config.get("base_flow")

        if base_flow not in sequencer_config["baseflows"][model_type]:
            supported_base_flows = ", ".join(
                sequencer_config["baseflows"][model_type].keys()
            )
            raise ValueError(
                f"The sequencer config for {sequencer_name} does not contain a "
                f"flow definition for flow: {flow_name}. Supported (base) flows are: {supported_base_flows}"
            )
        return flow_config


class PostprocFactory:
    """Class containing methods to instantiate an instance of Postprocessing.
    Fetch default from Experiment object (preferred) or Model object (backup)
    if postproc is not set by the user.
    """

    @staticmethod
    def create_from_database(
        db: ConfigDatabase,
        model: Model,
        experiment: Experiment,
        postproc_name: str = None,
    ):
        if (
            postproc_name is None or postproc_name == ""
        ):
            postproc_name = PostprocFactory.get_default_postproc(model, experiment)

        postproc_config = db.get_parsed_config("post-processing", postproc_name)

        return PostProcessing(**postproc_config)

    @staticmethod
    def get_default_postproc(model, experiment) -> str:
        """Retrieve the default postproc_profile"""
        if "postproc_profile" in experiment.model_dump():
            return experiment.postproc_profile
        elif "postproc_profile" in model.model_dump():
            return model.postproc_profile
        else:
            raise ValueError(
                f"No default postproc_profile defined for {experiment.name} or {model.name}"
            )


class ExperimentFactory:
    """Class containing methods to instantiate an instance of Experiment.
    On particular check that the model and experiment are consistent
    """

    @staticmethod
    def create_from_database(db: ConfigDatabase, experiment_name: str, model_name: str):
        """Create a sequencing instance given the config db, the machine, sequencer and flow names"""

        # An issue with this check here is that if a users changes the model and does
        # imsi config, this will not be triggered, but it could be invalid (should only be done
        # via imsi set)

        experiment_data = db.get_parsed_config("experiments", experiment_name)
        experiment = Experiment(name=experiment_name, **experiment_data)
        experiment.validate_model_name(model_name)
        return experiment


class Configuration(BaseModel):
    """Container class that combines sub-configurations and serves as the goto reference
    defining the configuration of a simulation.

    """

    # maybe better to include model (header), experiment (header) and a new component object (merged)??
    model: Model
    experiment: Experiment
    components: Components
    machine: Machine
    compiler: Compiler
    postproc: PostProcessing
    setup_params: SetupParams
    utilities: Utilities
    sequencing: Sequencing
    # Add "output templates" of which "shell_params" could be one?
    # This would avoid needing the DB downstream in shell_interface, and make the
    # Configuration complete.

    def model_post_init(self, __context):
        """
        Used to specifically update defaults only for specific configs
        """
        # For sequencing, we know we want to fill default time parameters
        # with those from experiment.
        # We are handling similar replacements in shell_parameters in the shell
        # config. However, generalizing templates might be important (see #22)

        sequencing_dict = self.sequencing.model_dump()
        sequencing_dict = replace_curlies_in_dict(sequencing_dict, self.model_dump())
        self.sequencing = Sequencing(**sequencing_dict)

        # after model is validated, instantiate without components
        self.model = Model(
            **self.model.model_dump(exclude={"components"})
        )

        # after experiment is validated, instantiate without components
        self.experiment = Experiment(
            **self.experiment.model_dump(exclude={"components"})
        )

    def get_unique_key_value(self, key: str):
        """Search recursively through the nested dicts of the configuration to try and find a specified key
        and return its value if the key is unique. If mulitple instances of they key exist, return an error.
        """
        # This is searching the whole imsi config for a match for key (variable)
        result = set(list(recursive_lookup(key, self.model_dump())))
        if len(result) != 1:
            # No results or no unique results
            # No unique results is a major challenge. But resolving this would require specifying more information
            # than just {{variable}}. For example, something like "input_files" which appears in the configs for
            # each model would not be unique. So far, we only need to search for uniquely defined values.
            raise ValueError(f"Could not find a unique imsi definition of {key}")
        else:
            return result.pop()


class ConfigManager:
    """This class is used to establish configuration objects, as well as save/load them for later use"""

    # Injecting the DB is good, but it might be useful to initialize it inline.
    def __init__(self, db: ConfigDatabase = None):
        self.db = db

    def create_configuration(
        self,
        model_name: str,
        experiment_name: str,
        machine_name: str = "",
        compiler_name: str = "",
        sequencer_name: str = "",
        flow_name: str = "",
        postproc_profile: str = "",
        **kwargs,
    ):
        """Create the individual instances of config elements and return a configuration composed of these"""
        # Capture all key=value pairs passed, filtering out "self" and kwargs (else it would be nested below a kwargs key)
        setup_params = {
            key: value
            for key, value in locals().items()
            if key != "self" and key != "kwargs"
        }
        # Merge kwargs into setup_params, without being nested
        setup_params.update(kwargs)

        if self.db is None:
            raise RuntimeError("imsi ConfigManager has no database")

        experiment = self.create_experiment(experiment_name, model_name)
        model = self.create_model(model_name)
        machine = self.create_machine(machine_name)
        components = self.create_components(model, experiment)
        compiler = self.create_compiler(machine, compiler_name)
        setup_params = self.create_SetupParams(setup_params, machine)  # improvable
        utilities = self.create_utilities()
        sequencing = self.create_sequencing(
            machine, setup_params.sequencer_name, flow_name, experiment
        )
        postproc = self.create_postproc(model, experiment, postproc_profile)

        return Configuration(
            model=model,
            experiment=experiment,
            components=components,
            machine=machine,
            compiler=compiler,
            postproc=postproc,
            setup_params=setup_params,
            utilities=utilities,
            sequencing=sequencing,
        )

    def create_experiment(self, experiment_name: str, model_name: str) -> Experiment:
        return ExperimentFactory.create_from_database(
            self.db, experiment_name, model_name
        )

    def create_model(self, model_name: str) -> Model:
        model_data = self.db.get_parsed_config("models", model_name)
        return Model(name=model_name, **model_data)

    def create_components(
        self, model: Model, experiment: Experiment
    ) -> Components:
        # deep merge the components of the experiment and model
        # experiment overrides model when params are shared
        components = update(model.components, experiment.components)
        # Create the merged components object
        return Components(**components)

    def create_machine(self, machine_name: str = None) -> Machine:
        return Machine.create_from_database(self.db, machine_name)

    def create_compiler(self, machine: Machine, compiler_name: str = None) -> Compiler:
        return CompilerFactory.create_from_database(self.db, machine, compiler_name)

    def create_postproc(
        self, model: Model, experiment: Experiment, postproc_profile: str
    ) -> PostProcessing:
        return PostprocFactory.create_from_database(
            self.db, model, experiment, postproc_profile
        )

    def create_SetupParams(self, setup_params: Dict, machine: Machine) -> SetupParams:
        if "sequencer_name" in setup_params:
            if not setup_params["sequencer_name"]:  # It is empty
                setup_params["sequencer_name"] = machine.get_default_sequencer()
        return SetupParams(**setup_params)

    def create_utilities(self) -> Utilities:
        utilities_data = copy.deepcopy(self.db.get_config("utility_config"))
        return Utilities(**utilities_data)

    def create_sequencing(
        self,
        machine: Machine,
        sequencer_name: str,
        flow_name: str,
        experiment: Experiment,
    ) -> Sequencing:
        return SequencingFactory.create_from_database(
            self.db,
            machine=machine,
            sequencer_name=sequencer_name,
            flow_name=flow_name,
            model_type=experiment.model_type,
        )

    @classmethod
    def save_configuration(self, configuration: Configuration, filepath: str):
        """Save the configuration to a file"""

        dumped = configuration.model_dump()
        if not dumped:
            raise ValueError("Configuration is empty, nothing to save")

        with open(filepath, 'w') as f:
            # preserve order with sort_keys=False
            yaml.dump(dumped, f, default_flow_style=False, sort_keys=False)

    def load_state(self, filepath) -> Configuration:
        """Load the configuration state from a file"""
        with open(filepath, "rb") as file:
            return pickle.load(file)

    @classmethod
    def save_state(self, configuration: Configuration, filepath: str):
        """Pickle the configuration object"""
        with open(filepath, 'wb') as f:
            pickle.dump(configuration, f)

    # Simple de-serialization
    def load_configuration(self, filepath) -> Configuration:
        """Load the configuration from a file"""
        with open(filepath, 'rb') as f:
            cfg = yaml.safe_load(f)
        return Configuration(**cfg)
