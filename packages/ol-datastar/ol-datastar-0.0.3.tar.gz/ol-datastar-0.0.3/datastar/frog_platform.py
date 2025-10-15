"""
Functions to facilitate interactions with Optilogic platform using 'optilogic' library
"""

import os
import json
import logging
import time
from typing import Tuple
import optilogic


class OptilogicClient:
    """
    Wrapper for optilogic module for consumption in Cosmic Frog services
    """

    def __init__(self, username=None, appkey=None, logger=logging.getLogger()):
        # Detect if being run in Andromeda
        job_app_key = os.environ.get("OPTILOGIC_JOB_APPKEY")

        if appkey and not username:
            # Use supplied key
            self.api = optilogic.pioneer.Api(auth_legacy=False, appkey=appkey)
        elif appkey and username:
            # Use supplied key & name
            self.api = optilogic.pioneer.Api(
                auth_legacy=False, appkey=appkey, un=username
            )
        elif job_app_key:
            # Running on Andromeda
            self.api = optilogic.pioneer.Api(auth_legacy=False)
        else:
            raise ValueError("OptilogicClient could not authenticate")

        self.logger = logger

    def get_connection_string(self, model_name: str) -> Tuple[bool, str]:

        max_retries = int(os.getenv("CFLIB_DEFAULT_MAX_RETRIES", "3"))
        max_timeout = int(os.getenv("CFLIB_DEFAULT_RETRY_DELAY", "5"))

        request_attempts = 0

        for number_of_attempts in range(max_retries):

            try:
                self.logger.info("Getting connection string")
                rv = {"message": "error getting connection string"}
                if not self.api.storagename_database_exists(model_name):
                    return False, ""

                connection_info = self.api.sql_connection_info(model_name)

                if connection_info:
                    self.logger.info("connection information retrieved")

                return True, connection_info["connectionStrings"]["url"]

            except Exception as e:
                self.logger.error(f"Exception in cosmicfrog: {e}")
                self.logger.error(f"attempt {number_of_attempts} out of {max_retries}")
                request_attempts = number_of_attempts + 1
                time.sleep(max_timeout)

        if request_attempts >= max_retries:
            self.logger.error("Getting connection failed. Too many attempts")
            return False, ""
