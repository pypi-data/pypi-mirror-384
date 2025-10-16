import time
import pytest
import logging

LOGGER = logging.getLogger(__name__)


def retry_operation(operation, max_retries, retry_interval, *args, **kwargs):
    retry_count = 0
    LOGGER.info("Retry count: %s", retry_count)
    while retry_count < max_retries:
        try:
            LOGGER.info("Executing operation...")
            result = operation(*args, **kwargs)
            LOGGER.info(f"Operation result: {result}")
            assert result is not None
            return result
        except Exception as e:
            LOGGER.error(str(e))
            retry_count += 1
            if retry_count < max_retries:
                retry_interval_minutes = retry_interval // 60
                LOGGER.info(f"Retrying in {retry_interval_minutes} minutes...")
                time.sleep(retry_interval)
            else:
                pytest.fail("Operation failed after multiple retries.")
    return None
