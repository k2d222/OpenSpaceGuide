#!/usr/bin/env python3

import argparse
import json


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='path to this file: https://github.com/OpenSpace/OpenSpace-Docs/blob/master/json/scriptingApi.json')
    parser.add_argument('output', help='output file path')
    args = parser.parse_args()
    return args


def replace(value, replacements, default):
    return replacements[value] if value in replacements else default

def process_input(input_path):
    with open(input_path, 'r') as file:
        data = json.load(file)

    res = []

    for lib in data:
        lib_name = lib['fullName']

        for fn in lib['functions']:
            fn_name = fn['name']
            fn_name = f'{lib_name}.{fn_name}'
            fn_desc = fn['help'].replace('\\\\', '\\').replace('\\"', '"') # remove double-escaping
            fn_props = {}
            fn_required = []
        
            for param in fn['arguments']:
                param_name = param['name'] or 'value'
                param_type = param['type']
                param_desc = ''

                fn_props[param_name] = {}

                if param_type.endswith('?'):
                    param_type = param_type[:-1]
                else:
                    fn_required.append(param_name)

                replacements = {
                    'String': 'string',
                    'Table': 'object',
                    'Number': 'number',
                    'Integer': 'number', # apparently, OpenAI does support 'integer'
                    'Boolean': 'boolean',
                    'Path': 'string',
                    'vec3': 'array',
                }

                print(param_type, end=" -> ")

                if param_type.find('|') != -1: # json schema doesn't support union types afaik
                    param_type = ''
                elif param_type.endswith('[]'):
                    array_type = param_type[:-2]
                    param_type = 'array'
                    array_type = replace(array_type, replacements, '')
                    if array_type:
                        fn_props[param_name]['items'] = { "type": array_type }
                else:
                    param_type = replace(param_type, replacements, '')

                if param_desc:
                    fn_props[param_name]['description'] = param_desc
                if param_type:
                    fn_props[param_name]['type'] = param_type

                print(param_type)

            fn_schema = {
                'type': 'function',
                'function': {
                    'name': fn_name,
                    'description': fn_desc,
                    'parameters': {
                        'type': 'object',
                        'properties': fn_props,
                        'required': fn_required
                    }
                }
            }
            res.append(fn_schema)

    return res


def save_output(data, output_path):
    with open(output_path, 'w') as file:
        json.dump(data, file, indent=4)


if __name__ == '__main__':
    args = parse_args()
    data = process_input(args.input)
    save_output(data, args.output)
    print('done')
