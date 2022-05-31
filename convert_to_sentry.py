import re
from collections import Counter
from pathlib import Path

from box import Box

from text import configuration_patch, \
    sentry_main_tf, serverless_custom, serverless_env, sentry_module, import_sentry, variable_tf_appendage, \
    requirements_txt_appendage

input_repo = '/Users/gvesztergombi/projects/twitter-profile-source'


def append_to_file(target, text):
    print(f'Append to {target}')
    assert target.exists()
    with open(target, 'ta') as f:
        f.write(text)


def prepend_to_file(target, text):
    print(f'Prepend to {target}')
    with open(target, 'tr') as f:
        data = f.read()
    with open(target, 'tw') as f:
        f.write(text)
        f.write(data)


def create_file(target, text):
    print(f'Create {target}')
    with open(target, 'tw') as f:
        f.write(text)


def find_after(lines, index, text):
    for i, line in enumerate(lines[index:]):
        if text in line:
            return index + i, line
    return None, None


def find_in(lines, index, index_end, text):
    for i, line in enumerate(lines[index:]):
        if text in line:
            if i + index > index_end:
                return None, None
            return index + i, line
    return None, None


def find_env_var_insertion_point(lines):
    i, config_line = find_after(lines, 0, 'class Config')
    i, _ = find_after(lines, i, 'def __init__')
    i, env_var_line = find_after(lines, i, 'env_var')
    m = re.search(r'=\s+([.\w]+)\(', env_var_line)
    if m:
        print(m.group(1))
    n = re.search(r'(\s+)', env_var_line)
    if n:
        print(n.group(1), '***')
    return Box({
        'index': i,
        'env_var_function': m.group(1),
        'indent': n.group(1)
    })


def read_lines(target):
    with open(target, 'rt') as f:
        return f.readlines()


def write_lines(target, lines):
    with open(target, 'w') as f:
        f.writelines(lines)


def splice(lines, index, patch):
    return lines[:index] + patch + lines[index:]


def patch_configuration(repo):
    target = repo / 'src/configuration.py'
    assert target.exists()

    lines = read_lines(target)

    m = find_env_var_insertion_point(lines)
    if m.index:
        print(m)
    patch = configuration_patch(m.indent, m.env_var_function)
    # patched_lines = lines[:m.index] + patch + lines[m.index:]
    patched_lines = splice(lines, m.index, patch)
    write_lines(target, patched_lines)


def patch_main_tf(repo):
    target = repo / 'main.tf'
    lines = read_lines(target)
    i, _ = find_after(lines, 0, '--')
    patched_lines = splice(lines, i, sentry_main_tf)
    write_lines(target, patched_lines)


def patch_serverless_custom(repo):
    target = repo / 'serverless.yml'
    lines = read_lines(target)
    i, _ = find_after(lines, 0, 'custom')
    patched_lines = splice(lines, i+1, serverless_custom)
    write_lines(target, patched_lines)


def patch_serverless_environment(repo):
    target = repo / 'serverless.yml'
    lines = read_lines(target)
    i, _ = find_after(lines, 0, 'environment')
    i, key = find_after(lines, i, '_')
    m = re.search(r'(\w+_)', key)
    assert m
    prefix = m.group(1)
    patched_lines = splice(lines, i+1, serverless_env(prefix))
    write_lines(target, patched_lines)


def find_resource_after_index(lines, index):
    i, start_resource = find_after(lines, index, 'resource')
    if i is None:
        return None, None
    c = Counter()
    for index, line in enumerate(lines[i:]):
        c.update(line)
        if c['{'] and c['{'] == c['}']:
            return i, i + index
    return None, None


def find_resources(lines):
    i = 0
    acc = []
    while i is not None:
        i, j = find_resource_after_index(lines, i)
        print(f'find resource {i}-{j}')
        if i:
            acc.append([i, j])
            i = j + 1
    return acc


def find_first(lines, resources, text='error_log_count'):
    for i, j in resources:
        k, _ = find_in(lines, i, j, text)
        if k:
            print(f'Found error_log_count in {i}-{j}')
            return i, j
    return None, None


def erase_error_log_count_from_alarms(repo):
    target = repo / 'alarms.tf'
    lines = read_lines(target)
    resources = find_resources(lines)
    print(f' resource {resources}')
    i, j = find_first(lines, resources)
    if i:
        cut_lines = lines[:i] + lines[j+1:]
        write_lines(target, cut_lines)


def edit_repo(repo_path):
    repo = Path(repo_path)
    erase_error_log_count_from_alarms(repo)
    erase_error_log_count_from_alarms(repo)
    patch_configuration(repo)
    patch_main_tf(repo)
    patch_serverless_custom(repo)
    patch_serverless_environment(repo)
    create_file(repo / 'src/sentry.py', sentry_module)
    prepend_to_file(repo / 'src/handler.py', import_sentry)
    append_to_file(repo / 'variables.tf', variable_tf_appendage)
    append_to_file(repo / 'requirements.txt', requirements_txt_appendage)


def main(input_repo_path):
    edit_repo(input_repo_path)


main(input_repo)
