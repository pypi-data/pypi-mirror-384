"""
  Snaps CLI commands
"""
import json
from typing import Union
import requests
from requests.exceptions import RequestException
from rich.progress import Progress, SpinnerColumn, TextColumn
from snapctl.config.constants import SERVER_CALL_TIMEOUT, SNAPCTL_INPUT_ERROR, \
    SNAPCTL_SNAPS_ENUMERATE_ERROR, SNAPCTL_INTERNAL_SERVER_ERROR
from snapctl.utils.helper import snapctl_error, snapctl_success
from snapctl.utils.echo import info


class Snaps:
    """
      CLI commands exposed for Snaps
    """
    SUBCOMMANDS = ['enumerate']

    def __init__(
            self, *, subcommand: str, base_url: str, api_key: Union[str, None],
            out_path_filename: Union[str, None] = None
    ) -> None:
        self.subcommand: str = subcommand
        self.base_url: str = base_url
        self.api_key: Union[str, None] = api_key
        self.out_path_filename: Union[str, None] = out_path_filename
        # Validate input
        self.validate_input()

    def validate_input(self) -> None:
        """
          Validator
        """
        # Check API Key and Base URL
        if not self.api_key or self.base_url == '':
            snapctl_error(
                message="Missing API Key.", code=SNAPCTL_INPUT_ERROR)
        # Check subcommand
        if not self.subcommand in Snaps.SUBCOMMANDS:
            snapctl_error(
                message="Invalid command. Valid commands are " +
                f"{', '.join(Snaps.SUBCOMMANDS)}.",
                code=SNAPCTL_INPUT_ERROR)
        if self.subcommand == 'enumerate':
            if self.out_path_filename:
                if not (self.out_path_filename.endswith('.json')):
                    snapctl_error(
                        message="Output filename should end with .json",
                        code=SNAPCTL_INPUT_ERROR)
                info(f"Output will be written to {self.out_path_filename}")

    @staticmethod
    def get_snaps(base_url: str, api_key: str) -> dict:
        """
          Get snaps
        """
        response_json = {}
        try:
            url = f"{base_url}/v1/snapser-api/services"
            res = requests.get(
                url, headers={'api-key': api_key},
                timeout=SERVER_CALL_TIMEOUT
            )
            response_json = res.json()
        except RequestException as e:
            pass
        return response_json

    def enumerate(self) -> bool:
        """
          Enumerate all snaps
        """
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        )
        progress.start()
        progress.add_task(
            description='Enumerating snaps...', total=None)
        try:
            response_json = Snaps.get_snaps(self.base_url, self.api_key)
            if response_json == {}:
                snapctl_error(
                    message="Something went wrong. No snaps found. Please try again in some time.",
                    code=SNAPCTL_INTERNAL_SERVER_ERROR, progress=progress)
            if 'services' not in response_json:
                snapctl_error(
                    message="Something went wrong. No snaps found. Please try again in some time.",
                    code=SNAPCTL_SNAPS_ENUMERATE_ERROR, progress=progress)
            if self.out_path_filename:
                with open(self.out_path_filename, 'w') as out_file:
                    out_file.write(json.dumps(response_json))
                snapctl_success(
                    message=f"Output written to {self.out_path_filename}", progress=progress)
            else:
                snapctl_success(
                    message=response_json, progress=progress)
        except RequestException as e:
            snapctl_error(
                message=f"Exception: Unable to enumerate snaps {e}",
                code=SNAPCTL_SNAPS_ENUMERATE_ERROR, progress=progress)
        finally:
            progress.stop()
        snapctl_error(
            message='Failed to enumerate snaps.',
            code=SNAPCTL_SNAPS_ENUMERATE_ERROR, progress=progress)
