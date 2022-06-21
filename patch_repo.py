import logging
import re
from collections import Counter
from pathlib import Path

from box import Box

from text import configuration_patch, \
    sentry_main_tf, serverless_custom, serverless_env, sentry_module, import_sentry, variable_tf_appendage, \
    requirements_txt_appendage

input_repo = '/Users/gvesztergombi/projects/twitter-profile-source'

CONFIGURATION_FILE_LOCATIONS = ['src/configuration.py',
                                'config/configuration.py',
                                'src/config/configuration.py',
                                'src/configuration/configuration.py',
                                'dlq/configuration/configuration.py',
                                'src/config.py']


def append_to_file(target, text):
    logging.info(f'Append to {target}')
    assert target.exists()
    lines = read_lines(target)

    with open(target, 'ta') as f:
        if not lines[-1].endswith('\n'):
            f.write('\n')
        f.write(text)


def prepend_to_file(target, text):
    logging.info(f'Prepend to {target}')
    with open(target, 'tr') as f:
        data = f.read()
    with open(target, 'tw') as f:
        f.write(text)
        f.write(data)


def create_file(target, text):
    logging.info(f'Create {target}')
    with open(target, 'tw') as f:
        f.write(text)


def find_after(lines, index, text):
    for i, line in enumerate(lines[index:]):
        m = re.search(text, line)
        if m:
            return index + i, line
    return None, None


def find_in(lines, index, index_end, text):
    for i, line in enumerate(lines[index:]):
        if text in line:
            if i + index > index_end:
                return None, None
            return index + i, line
    return None, None


def find_env_var_function(lines):
    i, config_line = find_after(lines, 0, 'class Config|class ApplicationConfig')
    i, _ = find_after(lines, i, 'def __init__')
    i, env_var_line = find_after(lines, i, 'env_var')
    m = re.search(r'(=|return)\s+([.\w]+)\(', env_var_line)
    if m:
        logging.info(f'env_var function {m.group(2)}')
        return m.group(2)
    else:
        raise ValueError('Could not find env_var function')


def find_env_var_insertion_point(lines):
    i, config_line = find_after(lines, 0, 'class Config|class ApplicationConfig')
    i, _ = find_after(lines, i, 'def __init__')
    if not i:
        raise ValueError('Could not find insertion point for __init__')
    n = re.search(r'(\s+)', lines[i+1])
    if n:
        logging.info(f'indentation={n.group(1)}', '***')
        return Box({
            'index': i+1,
            'env_var_function': find_env_var_function(lines),
            'indent': n.group(1)
        })
    else:
        raise ValueError('Could not find insertion point')


def read_lines(target):
    with open(target, 'rt') as f:
        return f.readlines()


def write_lines(target, lines):
    with open(target, 'w') as f:
        f.writelines(lines)


def splice(lines, index, patch):
    return lines[:index] + patch + lines[index:]


def find_target_in(repo, targets):
    files = map(lambda x: Path(repo)/x, targets)
    return next(filter(lambda x: x.exists(), files), None)


def find_subdirectory_in(repo, subdirs):
    files = map(lambda x: (Path(repo)/x, x), subdirs)
    a = next(filter(lambda x: x[0].exists(), files), None)
    if not a:
        raise FileNotFoundError(f'Could not find config dir in {repo}')
    else:
        return a[1]


def patch_configuration(repo):
    target = find_target_in(repo, CONFIGURATION_FILE_LOCATIONS)
    if not target:
        raise FileNotFoundError(f'Could not find config file in {repo}')

    lines = read_lines(target)

    m = find_env_var_insertion_point(lines)
    if m.index:
        logging.info(m)
    patch = configuration_patch(m.indent, m.env_var_function)
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
    m = re.search(r'([a-zA-Z]+)_', key)
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
        logging.info(f'find resource {i}-{j}')
        if i:
            acc.append([i, j])
            i = j + 1
    return acc


def find_first(lines, resources, text='error_log_count'):
    for i, j in resources:
        k, _ = find_in(lines, i, j, text)
        if k:
            logging.info(f'Found error_log_count in {i}-{j}')
            return i, j
    return None, None


def erase_error_log_count_from_alarms(repo):
    target = find_target_in(repo, ['alarms.tf', 'alerts.tf', '../alerts.tf'])
    if not target:
        logging.warning(f'No alerting configured for {repo}')
        return
    lines = read_lines(target)
    resources = find_resources(lines)
    logging.info(f' resource {resources}')
    i, j = find_first(lines, resources)
    if i:
        cut_lines = lines[:i] + lines[j+1:]
        write_lines(target, cut_lines)


def find_config_name(config_file):
    pattern = r'([_\w]+)(: \w+)? = (Configuration|ApplicationConfig)\(\)'
    lines = read_lines(config_file)
    for line in lines:
        m = re.search(pattern, line)
        if m:
            return m.group(1)
    raise ValueError(f'Could not find config name in {config_file}')


def add_sentry_module(repo):
    buf = sentry_module[:]
    config_path = find_subdirectory_in(repo, CONFIGURATION_FILE_LOCATIONS)
    config_name = find_config_name(repo / config_path)
    create_file(repo/'src/sentry.py',
                buf.format(config_path.replace('/', '.')[:-3],
                           config_name))


def edit_repo(repo_path):
    repo = Path(repo_path)
    erase_error_log_count_from_alarms(repo)
    try:
        patch_configuration(repo)
    except (ValueError, FileNotFoundError) as e:
        logging.warning(f'Could not patch configuration for {repo}')
    patch_main_tf(repo)
    patch_serverless_custom(repo)
    patch_serverless_environment(repo)
    add_sentry_module(repo)
    prepend_to_file(repo / 'src/handler.py', import_sentry)
    append_to_file(repo / 'variables.tf', variable_tf_appendage)
    append_to_file(repo / 'requirements.txt', requirements_txt_appendage)


# def patch sentry_enable(repo_path):
#     add_sentry_function()
#     patch serverless()
#     patch_main_tf()
#     patch_config()

def main(input_repo_path):
    edit_repo(input_repo_path)


if __name__ == '__main__':
    main('/Users/gvesztergombi/sentry_repos/twitter-profile-source')
