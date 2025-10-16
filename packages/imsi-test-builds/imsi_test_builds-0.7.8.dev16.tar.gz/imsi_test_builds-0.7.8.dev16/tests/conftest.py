import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env.test'))


def pytest_addoption(parser):
    parser.addoption(
        '--target-repo',
        action='store',
        default=os.environ.get("TEST_EXT_REPO", "git@gitlab.science.gc.ca:CanESM/CanESM5.git"),
        help='Git repository that contains configs to test with.'
    )
    parser.addoption(
        '--target-branch',
        action='store',
        default=os.environ.get("TEST_VERSION", "develop_canesm"),
        help='Branch in git repository to test with.'
    )
    parser.addoption(
        '--target-model',
        action='store',
        default=os.environ.get("TEST_MODEL", "canesm"),
        help='Model to use in unit tests'
    )
    parser.addoption(
        '--target-exp',
        action='store',
        default=os.environ.get("TEST_EXP", "cmip6-piControl"),
        help='Experiment to use in unit tests'
    )
    parser.addoption(
        '--target-machine',
        action='store',
        default=os.environ.get("TEST_MACHINE", "ppp6"),
        help='Machine to use in unit tests'
    )
    parser.addoption(
        '--target-sequencer',
        action='store',
        default=os.environ.get("TEST_SEQ", "iss"),
        help='Sequencer to use in unit tests'
    )