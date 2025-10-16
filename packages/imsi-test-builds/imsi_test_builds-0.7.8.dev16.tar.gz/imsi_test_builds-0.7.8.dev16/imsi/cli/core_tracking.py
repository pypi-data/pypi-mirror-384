from importlib.resources import files
import logging
from pathlib import Path
import subprocess
import sys

import imsi
from imsi.utils.general import get_active_venv
from imsi.user_interface.setup_manager import ValidatedSetupOptions


IMSI_STATEFUL_FOLDERS = ['src', 'config']

_logger_config = {
    'setup': {
        'logger_name': 'imsi-setup',
        'filename': '.imsi-setup.log',
        'hidden': True,
        'level': logging.DEBUG
    },
    'cli': {
        'logger_name': 'imsi-cli',
        'filename': '.imsi-cli.log',
        'hidden': True,
        'level': logging.INFO
    },
    'runtime': {
        'logger_name': 'imsi-runtime',
        'filename': '.imsi-cli.log',
        'hidden': True,
        'level': logging.INFO
    }
}


def _get_logger(logger_name: str=None, path: Path=None, filename: str=None,
                hidden=True, level=logging.INFO):
    # Return a logging.Logger with the name `logger_name` set at logging
    # level `level`. The log file will be written to the full path
    # constructed from `path / filename`. The `filename` must end with
    # extension `.log`. The `hidden=True` flag ensures that the filename
    # begins with a period (`.`) (conversely, ensures it is not included
    # if `hidden=False`).

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"ERROR: can't write log file to path {path}")
    if not filename.endswith('.log'):
        raise ValueError('filename must end with .log')

    logger = logging.getLogger(logger_name)
    if logger.hasHandlers():
        logger.handlers.clear()

    if hidden:
        basename = f".{filename}" if not filename.startswith('.') else filename
    else:
        basename = filename.lstrip('.')

    formatter = logging.Formatter(
        fmt='%(asctime)s - %(thread)d - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S%z'
        )

    # instantiate log config
    fh = logging.FileHandler(str(path / basename))
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.setLevel(level)

    return logger


def get_imsi_logger(name, path):
    """Return an imsi logger of name `name` written to the log file `path`."""
    logger_settings = _logger_config[name]
    logger_settings['path'] = path
    return _get_logger(**logger_settings)


def log_setup(cli_args, setup_params: ValidatedSetupOptions, with_src_status=True):
    """Log setup command and information to the setup log file."""
    setup_path = Path(setup_params.runid).resolve()

    logger = get_imsi_logger('setup', setup_path)
    logger.info(f"🚀 IMSI setup for {setup_params.runid} 🚀")
    logger.info('setup_params: {}'.format(' '.join(f"{k}={v}" for k, v in setup_params.model_dump().items())))

    if with_src_status:
        # capture the status of the git repo under /src
        s = files("imsi").joinpath("utils/repo_query_status.sh")
        src_path = setup_path / 'src'
        try:
            proc = subprocess.run([str(s)], capture_output=True, cwd=src_path)
            proc.check_returncode()
        except subprocess.CalledProcessError as e:
            src_msg = f'Could not determine status under {src_path}'
        else:
            src_msg = f'src: {proc.stdout.decode().strip()}'

        logger.info(src_msg)

    # DEV: keep this as the last setup log entry (newline)
    input_args = ' '.join(sys.argv)
    logger.info(f"Setup command used:\n{input_args}")


def imsi_log_prelude(func_name, logger):
    """Log header information (imsi metadata) to the `logger` related to
    running `func_name`. Logging is set to logging.INFO.
    """
    imsi_meta = f"imsi {imsi.__version__} {imsi.__path__[0]}"
    imsi_venv = get_active_venv()
    logger.info(f'INVOKING {func_name}')
    logger.info(' '.join(sys.argv))
    logger.info(imsi_meta)
    logger.info(f'VIRTUAL_ENV {imsi_venv}')


def imsi_log_postlude(func_name, logger):
    """Log footer information related to running `func_name`.
    Logging level is set to logging.INFO.
    """
    logger.info(f'COMPLETED {func_name}')


def imsi_state_snapshot(path, folders=None, logger=None):
    """Take a snapshot of the imsi state and return the state hash.

    This runs the snapshot tool (cli_snapshot_state.sh) for the `folders`
    specified under the `path`.

    Parameters:
        path : path to an imsi run folder
        folders : folder names (relative to `path`) on which to take the state
            snapshot. These folders must be git repos. Default list is
            ['config', 'src'].
        logger : instance of a Logger.

    Returns:
        the hash of the imsi state folder
    """

    if folders is None:
        folders = IMSI_STATEFUL_FOLDERS
    elif isinstance(folders, str):
        folders = [folders]

    tracker_script = Path(__file__).parent / 'cli_snapshot_state.sh'
    folder_args = [l for s in [['-p', p] for p in folders] for l in s]
    io_args = ['-i', path, '-o', path]

    if not tracker_script.exists():
        raise FileNotFoundError(f'ERROR missing snapshot tool: {tracker_script}')
    try:
        proc = subprocess.run([str(tracker_script)] + folder_args + io_args, capture_output=True)
        proc.check_returncode()
    except subprocess.CalledProcessError as e:
        if logger:
            logger.error(f'state snapshot failed')
            logger.error(f'HALTING')
        raise ChildProcessError("Failed call: {cmd}\n{err}".format(cmd=' '.join(proc.args), err=proc.stdout.decode())) from e

    state_sha = proc.stdout.decode().strip()
    if logger:
        logger.info(f'IMSI state:{state_sha}')

    return state_sha
