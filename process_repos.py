import os
import shutil
import sys
from pathlib import Path

import config
from cli import cli
from patch_repo import edit_repo
import logging


def process_repo(repo):
    try:
        logging.info(f'Processing {repo}')
        os.chdir(config.work_dir)
        repo_dir = Path(config.work_dir)/repo
        if repo_dir.exists():
            logging.info(f'Skipping. {repo} already processed')
            return
        cli(f'git clone git@github.com:hearsaycorp/{repo}.git')
        os.chdir(repo)
        cli('git checkout -b feature/HSS-24517-report-to-sentry')
        edit_repo(os.getcwd())
        logging.info(f'Successfully processed {repo}')
    except:
        logging.exception('Aborted because of exception')
        logging.error(f'Could not process {repo}')
        repo_dir = Path(config.work_dir) / repo
        if repo_dir.exists():
            shutil.rmtree(repo_dir)
        logging.info('Removed directory')


def process_repos(repos):
    list(map(process_repo, repos))


if __name__ == '__main__':
    logging.basicConfig(filename='work.log', encoding='utf-8', level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    try:
        process_repos(config.repos)
    except:
        logging.exception('Aborted processing run')

