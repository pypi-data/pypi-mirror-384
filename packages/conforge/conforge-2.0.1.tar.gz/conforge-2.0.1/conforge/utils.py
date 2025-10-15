from jinja2 import Template, Environment


def deep_merge(dict1, dict2):
    for key, value in dict2.items():
        if isinstance(value, dict) and key in dict1:
            dict1[key] = deep_merge(dict1[key], value)
        else:
            dict1[key] = value
    return dict1


class DottedKeys:
    data = {}

    def __init__(self, dict_):
        self.data = self.prepare(dict_)

    def prepare(self, dict_, parents = []):
        output = {}

        for key, val in dict_.items():
            if type(val) == dict:
                output.update(self.prepare(val, parents + [key]))
            else:
                new_key = '.'.join(parents + [key])
                output[new_key] = val

        return output

    def all(self):
        return self.data

    def get(self, key):
        return self.data.get(key)

    def get_dict_field_undotted_with_value(self, key, val):
        keys = key.split('.')

        if len(keys) == 1:
            return {
                key: val
            }
        else:
            keys.reverse()
            current_key = keys.pop()
            keys.reverse()
            new_key = '.'.join(keys)

            return {
                current_key: self.get_dict_field_undotted_with_value(new_key, val)
            }

    def get_undotted(self, key):
        return self.get_dict_field_undotted_with_value(key, self.get(key))

    def set(self, key, val):
        self.data[key] = val

    def items(self):
        return self.data.items()


class UndefinedVariableException(Exception):
    pass


class CircularDependencyException(Exception):
    pass


class Interpolate:
    def __init__(self, vars):
        self.vars = vars
        self.dk = DottedKeys(vars)

    def get_deps_of_value(self, val):
        e = Environment()
        tokens = e.lex(val)

        deps = []
        within_scope = False
        name_parts = []

        for token in tokens:
            if token[1] == 'variable_begin':
                within_scope = True

            if token[1] == 'name' and within_scope:
                name_parts.append(token[2])

            if token[1] == 'variable_end' or (token[1] == 'operator' and token[2] == '|'):
                if name_parts:
                    deps.append('.'.join(name_parts))
                    name_parts = []

                within_scope = False

        return deps

    def get_deps_recursively(self, key, deps_queue = []):
        deps_queue = list(deps_queue)

        if key not in deps_queue:
            deps_queue.append(key)

        current_key_deps = self.get_deps_of_value(self.dk.get(key))

        for current_key_dep in current_key_deps:
            if current_key_dep in deps_queue:
                raise CircularDependencyException()
            else:
                current_key_deps.extend(self.get_deps_recursively(current_key_dep, deps_queue))

        return current_key_deps

    def get_deps_of_key(self, key):
        return self.get_deps_recursively(key)

    def get_dep_graph(self):
        vars = []
        vars_with_unresolved_deps = list(self.dk.all().keys())
        all_keys = list(vars_with_unresolved_deps)

        while vars_with_unresolved_deps:
            for key in vars_with_unresolved_deps:
                deps = self.get_deps_of_key(key)

                if not deps:
                    vars.append(key)
                    vars_with_unresolved_deps.remove(key)
                else:
                    for dep in deps:
                        if dep not in vars:
                            if dep not in all_keys:
                                raise UndefinedVariableException()
                            break
                    else:
                        vars.append(key)
                        vars_with_unresolved_deps.remove(key)

        return vars

    def get_interpolated(self):
        output = {}
        vars = self.get_dep_graph()

        for key in vars:
            if not type(self.dk.get(key)) == str:
                output = deep_merge(output, self.dk.get_undotted(key))
                continue

            template = Template(self.dk.get(key))
            self.dk.set(key, template.render(output))

            output = deep_merge(output, self.dk.get_undotted(key))

        return output