from typing import OrderedDict

import configparser


def get_config_dict(config_path: str, section_key: str = None) -> OrderedDict:
    """ Reads a configuration file using configparser.

        See https://docs.python.org/3/library/configparser.html#quick-start to learn more about the
            structure of the configuration file.

        Args:
            config_path: The path to the configuration file.
            section_key: If specified the function will return only the specific section of the
                configuration specified by the <section_key>.

        Returns:
            An OrderedDict that maps the name of each section of the configuration file to an
                OrderedDict object that includes a mapping of each configuration variable name to
                its value.

                If <section_key> is specified, only one section of the configuration is returned.
     """
    cfg = configparser.ConfigParser()
    cfg.read(config_path)
    cfg_dict = cfg.__dict__['_sections']
    if section_key:
        return cfg_dict[section_key]
    return cfg_dict


def get_text_from_file(path: str) -> str:
    """ Reads an entire text file into a string variable and returns its value. """
    with open(path, 'r') as fp:
        return fp.read()
