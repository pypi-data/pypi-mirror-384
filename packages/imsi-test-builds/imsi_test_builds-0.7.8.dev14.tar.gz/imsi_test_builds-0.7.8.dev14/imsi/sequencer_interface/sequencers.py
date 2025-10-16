"""
sequencers
===========

Provide a generic sequencer class, as an interface for dedicated sequencer
sub-classes. This allows imsi to interface with multiple underlying sequencers.
"""
from abc import ABC, abstractmethod
from imsi.config_manager.config_manager import Configuration

def create_sequencer(seq_name):
    """
    Create and return a sequencer object
    """
    if seq_name == 'iss':
        from imsi.sequencer_interface.iss_cap import IMSISimpleSequencerInterface
        return IMSISimpleSequencerInterface()
    elif seq_name == 'maestro':
        from imsi.sequencer_interface.maestro_cap import MaestroSequencerInterface
        return MaestroSequencerInterface()
    else:
        raise ValueError(f"Specified sequencer {seq_name} not supported in imsi.")

class Sequencer(ABC):
    """
    A class that absracts the definition of a sequencer cap for imsi.

    Sub-classes for specific sequencers will provide the concerete
    implementations of the methods below, using the imsi Configuration
    information, and using their own specifically required methods.

    The sequencer specific implementation must expose back, through this
    interface, all the methods below.
    """
    @abstractmethod
    def setup(self, configuration: Configuration):
        """
        Any steps needed to setup the sequencer, including
        cloning source and creating any directories
        """
        raise NotImplementedError("sequencer config method must be defined")

    @abstractmethod
    def config(self, configuration: Configuration):
        """
        Steps needed to configure sequencer files based on updated imsi
        input. Examples might include editing resource files.
        """
        raise NotImplementedError("sequencer config method must be defined")

    @abstractmethod
    def submit(self, configuration: Configuration):
        """
        Steps needed to configure sequencer files based on updated imsi
        input. Examples might include editing resource files.
        """
        raise NotImplementedError("sequencer submit method must be defined")

    @abstractmethod
    def status(self, configuration: Configuration):
        """
        Steps needed to configure sequencer files based on updated imsi
        input. Examples might include editing resource files.
        """
        raise NotImplementedError("sequencer status method must be defined")
