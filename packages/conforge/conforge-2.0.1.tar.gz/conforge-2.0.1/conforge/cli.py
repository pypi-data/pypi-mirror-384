#!/usr/bin/env python3

import sys
import argparse

from . import main, configs


class ExitCodes:
    CONFIG_FILE_DOES_NOT_EXIST = 129
    VARIABLE_FILE_DOES_NOT_EXIST = 130
    INVALID_SYNTAX = 131
    INVALID_CONFIG = 132
    MISSING_TEMPLATE_FILE = 133
    OUTPUT_WRITE_ERROR = 134
    INVALID_VARIABLE_FILE_TYPE = 135


def run_app():
    config_file_parser_provider = main.ConfigFileParserProvider()
    config_file_parser_provider.add_parser('json', configs.JsonConfigFile)
    config_file_parser_provider.add_parser('yaml', configs.YamlConfigFile)

    variable_file_parser_provider = main.VariableFileParserProvider()
    variable_file_parser_provider.add_parser('json', configs.JsonVariableFile)
    variable_file_parser_provider.add_parser('yaml', configs.YamlVariableFile)

    parser = argparse.ArgumentParser(description='Conforge: Generate config files from given templates and variables')

    parser.add_argument(
        '-t',
        '--config-type',
        type=str,
        choices=config_file_parser_provider.get_supported_config_file_types(),
        required=True,
        help='Type of config file')
    parser.add_argument(
        'config',
        type=str,
        help='The path to the configuration file.')

    args = parser.parse_args()

    try:
        conforge = main.Conforge(config_file_parser_provider, variable_file_parser_provider)
        conforge.make_config_files(args.config_type, args.config)
    except configs.ConfigFileNotExistsException as e:
        print('Config file {} does not exist!'.format(e.path), file=sys.stderr)
        sys.exit(ExitCodes.CONFIG_FILE_DOES_NOT_EXIST)
    except configs.VariableFileNotExistsException as e:
        print('Variable file {} does not exist!'.format(e.path), file=sys.stderr)
        sys.exit(ExitCodes.VARIABLE_FILE_DOES_NOT_EXIST)
    except configs.InvalidSyntaxException as e:
        print('Invalid syntax error in {}:\n\n{}'.format(e.path, e.message))
        sys.exit(ExitCodes.INVALID_SYNTAX)
    except configs.InvalidConfigFileException as e:
        print(e.message)
        sys.exit(ExitCodes.INVALID_CONFIG)
    except main.TemplateFileNotFoundException as e:
        print('Template file {} not found!'.format(e.path))
        sys.exit(ExitCodes.MISSING_TEMPLATE_FILE)
    except main.CouldNotWriteOutputFileException as e:
        print('Could not write output file {}!'.format(e.path))
        sys.exit(ExitCodes.OUTPUT_WRITE_ERROR)
    except main.InvalidVaribleFileParserException as e:
        print('Invalid variable file type \'{}\' is given.'.format(e.type))
        sys.exit(ExitCodes.INVALID_VARIABLE_FILE_TYPE)

if __name__ == "__main__":
    run_app()