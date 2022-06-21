import logging
import os
import sys
from pathlib import Path

import config
from cli import cli


def commit_and_pr(directory):
    logging.info(f'Commit and create PR for {directory}')
    os.chdir(directory)
    cli('git add src/sentry.py')
    cli('git commit -am"add sentry"')
    cli('git push -u origin head --force')
    cli('gh pr create --title "[HSS-24517] Connect to Sentry" '
        '--body "Remove superfluous PagerDuty alerts and use Sentry for reporting instead."')


def main(work_dir):
    _, directories, _ = next(os.walk(work_dir))
    logging.info(directories)
    dirs = map(lambda x: Path(work_dir)/x, directories)
    list(map(commit_and_pr, dirs))


if __name__ == '__main__':
    logging.basicConfig(filename='work.log', encoding='utf-8', level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    main(config.work_dir)
