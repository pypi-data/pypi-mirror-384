# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

from abc import ABC, abstractmethod


class PlatformInfo(ABC):
    """
    Interface for platform specific diagnostics dependencies
    This needs to be implemented for each supported platform (Linux, Mac, etc.)
    """

    @abstractmethod
    def get_hardware_info(self) -> str:
        """
        Abstract method for extracting Hardware information (Platform specific)
        NOTE: This method should not throw any exceptions !
        """
        pass

    @abstractmethod
    def get_os_info(self) -> str:
        """
        Abstract method for extracting OS information (Platform specific)
        NOTE: This method should not throw any exceptions !
        """
        pass

    @abstractmethod
    def get_usb_info(self) -> str:
        """
        Abstract method for extracting USB information (Platform specific)
        NOTE: This method should not throw any exceptions !
        """
        pass

    @abstractmethod
    def get_network_info(self) -> str:
        """
        Abstract method for extracting Network information (Platform specific)
        NOTE: This method should not throw any exceptions !
        """
        pass

    @abstractmethod
    def get_aria_folder_structure(self) -> str:
        """
        Abstract method for extracting Aria folder structure (Platform specific)
        NOTE: This method should not throw any exceptions !
        """
        pass
