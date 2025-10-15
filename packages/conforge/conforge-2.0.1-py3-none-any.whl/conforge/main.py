from jinja2 import Template


class TemplateFileNotFoundException(Exception):
    def __init__(self, path):
        self.path = path


class CouldNotWriteOutputFileException(Exception):
    def __init__(self, path):
        self.path = path


class InvalidVaribleFileParserException(Exception):
    def __init__(self, type):
        self.type = type


class VariableFileParserProvider:
    parsers = {}

    def add_parser(self, type, parser):
        self.parsers[type] = parser

    def get_parser_for(self, type, file):
        try:
            return self.parsers[type].get_for_file(file)
        except KeyError:
            raise InvalidVaribleFileParserException(type)

    def get_supported_variable_file_types(self):
        return self.parsers.keys()


class ConfigFileParserProvider:
    parsers = {}

    def add_parser(self, type, parser):
        self.parsers[type] = parser

    def get_parser_for(self, type, file, variable_file_parser_provider):
        return self.parsers[type].get_for_file(file, variable_file_parser_provider)

    def get_supported_config_file_types(self):
        return self.parsers.keys()


class TemplateRenderer:
    def __init__(self, template_content, variables):
        template = Template(template_content)
        self.rendered_content = template.render(variables)

    def write_to(self, output):
        try:
            with open(output, 'w') as output_fp:
                output_fp.write(self.rendered_content)
        except PermissionError:
            raise CouldNotWriteOutputFileException(output)


class Conforge:
    def __init__(self, config_file_parser_provider, variable_file_parser_provider):
        self.config_file_parser_provider = config_file_parser_provider
        self.variable_file_parser_provider = variable_file_parser_provider

    def make_config_files(self, config_file_type, config_file_path):
        config_file_parser = self.config_file_parser_provider.get_parser_for(config_file_type, config_file_path, self.variable_file_parser_provider)

        variables = config_file_parser.get_variables_expanded()

        template_specs = config_file_parser.get_template_specs()

        for template_spec in template_specs:
            try:
                with open(template_spec['template'], 'r') as template_fp:
                    template_renderer = TemplateRenderer(template_fp.read(), variables)

                    for output in template_spec['outputs']:
                        template_renderer.write_to(output)
            except FileNotFoundError:
                raise TemplateFileNotFoundException(template_spec['template'])
