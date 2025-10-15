import json

from tempfile import NamedTemporaryFile
from datetime import datetime

import zzlog


def test_loginfo():
    with NamedTemporaryFile() as f:
        logger = zzlog.setup(
            logger_root='.',
            filename=f.name,
        )

        message = 'Hello World!'
        logger.error(message)

        with open(f.name) as f:
            lines = f.readlines()
            logs = [json.loads(l) for l in lines]
            assert len(logs) == 1

            log = logs[0]

            assert 'level' in log
            assert log['level'] == 'ERROR'

            assert 'name' in log
            assert log['name'] == '.'

            assert 'timestamp' in log
            t = datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
            assert (t - datetime.now()).total_seconds() < 1

            assert 'message' in log
            assert log['message'] == 'Hello World!'
