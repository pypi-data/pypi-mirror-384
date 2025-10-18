import time
import os

def wait_for_file(file_path, timeout=15):
    """
    Wait for a file to appear.

    :param file_path: The path to the file to wait for.
    :param timeout: The number of seconds to wait before timing out.
    :return: True if the file exists, False otherwise.
    """
    start_time = time.time()
    elapsed_time = 0
    to_seconds = 0.200
    retry_interval = 1

    while not os.path.exists(file_path) and elapsed_time < timeout:
        print("Waiting for file: {}".format(file_path))
        time.sleep(retry_interval*to_seconds)
        elapsed_time = time.time() - start_time
        retry_interval *= 2  # Exponential backoff
        
    return os.path.exists(file_path)
