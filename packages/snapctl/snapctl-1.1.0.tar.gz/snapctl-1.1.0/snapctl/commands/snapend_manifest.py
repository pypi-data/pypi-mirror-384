"""
  Snapend manifest CLI commands
"""
import os
from typing import Union
import json
from requests.exceptions import RequestException
from rich.progress import Progress, SpinnerColumn, TextColumn
from snapctl.config.constants import SNAPCTL_SNAPEND_MANIFEST_UPGRADE_ERROR, SNAPCTL_INPUT_ERROR, \
    SNAPCTL_SNAPEND_MANIFEST_CREATE_ERROR, SNAPCTL_SNAPEND_MANIFEST_UPDATE_ERROR, \
    SNAPCTL_INTERNAL_SERVER_ERROR
from snapctl.commands.snaps import Snaps
from snapctl.utils.helper import snapctl_error, snapctl_success
from snapctl.utils.echo import info, warning, success


class SnapendManifest:
    """
      CLI commands exposed for Snapend manifest
    """
    SUBCOMMANDS = ['create', 'update', 'upgrade']
    ENVIRONMENTS = ['DEVELOPMENT', 'STAGING', 'PRODUCTION']
    FEATURES = ['WEB_SOCKETS']
    AUTH_SNAP_ID = 'auth'

    def __init__(
            self, *, subcommand: str, base_url: str, api_key: Union[str, None],
            name: str = 'my-snapend',
            environment: str = 'DEVELOPMENT',
            manifest_path_filename: Union[str, None] = None,
            snaps: Union[str, None] = None,
            features: Union[str, None] = None,
            out_path_filename: Union[str, None] = None,
    ) -> None:
        self.subcommand: str = subcommand
        self.base_url: str = base_url
        self.api_key: Union[str, None] = api_key
        self.name: str = name
        self.environment: str = environment
        self.manifest_path_filename: Union[str, None] = manifest_path_filename
        self.manifest: Union[dict, None] = None
        self.out_path_filename: Union[str, None] = out_path_filename
        self.snaps = snaps
        self.features = features
        self.remote_snaps: list = self.load_snaps()
        # Setup
        self.setup_manifest()
        # Validate input
        self.validate_input()

    def setup_manifest(self) -> bool:
        """
        Read a manifest (JSON or YAML) and saves it
        Supports extensions: .json, .yaml, .yml
        If the extension is unknown, tries JSON then YAML.
        """
        def parse_json(s: str):
            return json.loads(s)

        def parse_yaml(s: str):
            try:
                import yaml  # type: ignore
            except ImportError as e:
                raise RuntimeError(
                    "YAML file provided but PyYAML is not installed. "
                    "Install with: pip install pyyaml"
                ) from e
            return yaml.safe_load(s)

        if not self.manifest_path_filename:
            return False
        with open(self.manifest_path_filename, "r", encoding="utf-8") as f:
            text = f.read()

        ext = os.path.splitext(self.manifest_path_filename)[1].lower()
        if ext == ".json":
            parsers = (parse_json, parse_yaml)
        elif ext in (".yaml", ".yml"):
            parsers = (parse_yaml, parse_json)
        else:
            parsers = (parse_json, parse_yaml)

        last_err = None
        data = None
        for parser in parsers:
            try:
                data = parser(text)
                break
            except Exception as e:
                last_err = e

        if data is None:
            return False
        if not isinstance(data, dict):
            return False

        try:
            self.manifest = data
        except KeyError as e:
            pass
        return False

    def load_snaps(self) -> list:
        """
          Load snaps from the Snapser portal
        """
        snaps_response = Snaps.get_snaps(self.base_url, self.api_key)
        if 'services' in snaps_response:
            return snaps_response['services']
        return []

    def validate_input(self) -> None:
        """
          Validator
        """
        # Check API Key and Base URL
        if not self.api_key or self.base_url == '':
            snapctl_error(
                message="Missing API Key.", code=SNAPCTL_INPUT_ERROR)
        # Check subcommand
        if not self.subcommand in SnapendManifest.SUBCOMMANDS:
            snapctl_error(
                message="Invalid command. Valid commands are " +
                f"{', '.join(SnapendManifest.SUBCOMMANDS)}.",
                code=SNAPCTL_INPUT_ERROR)
        if len(self.remote_snaps) == 0:
            snapctl_error(
                message="Something went wrong. No snaps found. Please try again in some time.",
                code=SNAPCTL_INTERNAL_SERVER_ERROR)
        if self.subcommand == 'create':
            if not self.name or not self.environment:
                snapctl_error(
                    message="Name and environment are required for create command.",
                    code=SNAPCTL_INPUT_ERROR)
            if self.environment not in SnapendManifest.ENVIRONMENTS:
                snapctl_error(
                    message="Environment must be one of " +
                    f"{', '.join(SnapendManifest.ENVIRONMENTS)}.",
                    code=SNAPCTL_INPUT_ERROR)
            if not self.out_path_filename:
                snapctl_error(
                    message="Output path is required for create command.",
                    code=SNAPCTL_INPUT_ERROR)
            if self.out_path_filename and not (self.out_path_filename.endswith('.json') or
                                               self.out_path_filename.endswith('.yaml') or
                                               self.out_path_filename.endswith('.yml')):
                snapctl_error(
                    message="Output path must end with .json, .yaml or .yml",
                    code=SNAPCTL_INPUT_ERROR)
            if not self.snaps or self.snaps == '':
                snapctl_error(
                    message="At least one snap ID is required to create a " +
                    "snapend manifest.",
                    code=SNAPCTL_INPUT_ERROR)
            if self.features:
                for feature in self.features.split(','):
                    feature = feature.strip()
                    if feature.upper() not in SnapendManifest.FEATURES:
                        snapctl_error(
                            message="-add-features must be one of " +
                            f"{', '.join(SnapendManifest.FEATURES)}.",
                            code=SNAPCTL_INPUT_ERROR)
        elif self.subcommand == 'update':
            if not self.manifest_path_filename:
                snapctl_error(
                    message="Manifest path is required for update command.",
                    code=SNAPCTL_INPUT_ERROR)
            if (not self.snaps or self.snaps == '') and \
                    (not self.features or self.features == ''):
                snapctl_error(
                    message="At least one of snaps or features " +
                    "is required to update a snapend manifest.",
                    code=SNAPCTL_INPUT_ERROR)
            if not self.out_path_filename:
                snapctl_error(
                    message="Output path is required for update command.",
                    code=SNAPCTL_INPUT_ERROR)
            if self.out_path_filename and not (self.out_path_filename.endswith('.json') or
                                               self.out_path_filename.endswith('.yaml') or
                                               self.out_path_filename.endswith('.yml')):
                snapctl_error(
                    message="Output path must end with .json, .yaml or .yml",
                    code=SNAPCTL_INPUT_ERROR)
            if not self.manifest:
                snapctl_error(
                    message="Unable to read the manifest file. " +
                    "Please check the file and try again.",
                    code=SNAPCTL_INPUT_ERROR)
            if 'service_definitions' not in self.manifest:
                snapctl_error(
                    message="Invalid manifest file. Need service_definitions. " +
                    "Please check the file and try again.",
                    code=SNAPCTL_INPUT_ERROR)
        elif self.subcommand == 'upgrade':
            if not self.manifest_path_filename:
                snapctl_error(
                    message="Manifest path is required for update command.",
                    code=SNAPCTL_INPUT_ERROR)
            if not self.out_path_filename:
                snapctl_error(
                    message="Output path is required for update command.",
                    code=SNAPCTL_INPUT_ERROR)
            if self.out_path_filename and not (self.out_path_filename.endswith('.json') or
                                               self.out_path_filename.endswith('.yaml') or
                                               self.out_path_filename.endswith('.yml')):
                snapctl_error(
                    message="Output path must end with .json, .yaml or .yml",
                    code=SNAPCTL_INPUT_ERROR)
            if not self.manifest:
                snapctl_error(
                    message="Unable to read the manifest file. " +
                    "Please check the file and try again.",
                    code=SNAPCTL_INPUT_ERROR)
            if 'service_definitions' not in self.manifest:
                snapctl_error(
                    message="Invalid manifest file. Need service_definitions. " +
                    "Please check the file and try again.",
                    code=SNAPCTL_INPUT_ERROR)
        elif self.subcommand == 'validate':
            if not self.manifest_path_filename:
                snapctl_error(
                    message="Manifest path is required for validate command.",
                    code=SNAPCTL_INPUT_ERROR)

    def _get_snap_sd(self, snap_id) -> dict:
        """
          Get snap service definition
        """
        for snap in self.remote_snaps:
            if snap['id'] == snap_id:
                snap_sd = {
                    "id": snap['id'],
                    "language": snap['language'],
                    "version": snap['latest_version'],
                    "author_id": snap['author_id'],
                    "category": snap['category'],
                    "subcategory": snap['subcategory'],
                    "data_dependencies": [],
                }
                for versions in snap['versions']:
                    if versions['version'] == snap['latest_version']:
                        snap_sd['data_dependencies'] = \
                            versions['data_dependencies']
                return snap_sd
        raise ValueError(
            f"Snap service definition with id '{snap_id}' not found")

    # Commands
    def create(self) -> bool:
        """
          Create a snapend manifest
          @test -
          `python -m snapctl snapend-manifest create --name my-dev-snapend --env DEVELOPMENT --snaps auth,analytics --out-path-filename ./snapend-manifest.json`
        """
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        )
        progress.start()
        progress.add_task(
            description='Enumerating all your games...', total=None)
        try:
            new_manifest = {
                "version": "v1",
                "name": self.name,
                "environment": self.environment,
                "service_definitions": [],
                "feature_definitions": [],
                "external_endpoints": [],
                "settings": []
            }
            snap_ids = [snap_id.strip()
                        for snap_id in self.snaps.split(',')]
            for snap_id in snap_ids:
                snap_found = False
                for snap in self.remote_snaps:
                    if snap['id'] == snap_id:
                        snap_sd = self._get_snap_sd(snap_id)
                        new_manifest['service_definitions'].append(snap_sd)
                        snap_found = True
                        break
                if not snap_found:
                    snapctl_error(
                        message=f"Snap ID {snap_id} not found in your snaps.",
                        code=SNAPCTL_INPUT_ERROR,
                        progress=progress)
            found_auth = False
            for final_snap in new_manifest['service_definitions']:
                if final_snap['id'] == SnapendManifest.AUTH_SNAP_ID:
                    found_auth = True
                    break
            if not found_auth:
                auth_sd = self._get_snap_sd(SnapendManifest.AUTH_SNAP_ID)
                new_manifest['service_definitions'].append(auth_sd)
                warning(
                    'Auth snap is required for snapend. Added auth snap to the manifest.')
            new_manifest['service_definitions'].sort(key=lambda x: x["id"])
            if self.features and self.features != '':
                features = [feature.strip()
                            for feature in self.features.split(',')]
                for feature in features:
                    if feature.upper() not in new_manifest['feature_definitions']:
                        new_manifest['feature_definitions'].append(
                            feature.upper())
            if self.out_path_filename:
                # Based on the out-path extension, write JSON or YAML
                if self.out_path_filename.endswith('.yaml') or self.out_path_filename.endswith('.yml'):
                    try:
                        import yaml  # type: ignore
                    except ImportError as e:
                        snapctl_error(
                            message="YAML output requested but PyYAML is not installed. "
                            "Install with: pip install pyyaml",
                            code=SNAPCTL_INPUT_ERROR,
                            progress=progress)
                    with open(self.out_path_filename, 'w') as out_file:
                        yaml.dump(new_manifest, out_file, sort_keys=False)
                else:
                    with open(self.out_path_filename, 'w') as out_file:
                        out_file.write(json.dumps(new_manifest, indent=4))
                info(f"Output written to {self.out_path_filename}")
                success("You can now use this manifest to create a snapend " +
                        "environment using the command 'snapend create " +
                        "--manifest-path-filename $fullPathToManifest --application-id $appId --blocking'")
                snapctl_success(
                    message="Snapend manifest created successfully.",
                    progress=progress)
            else:
                snapctl_success(
                    message=new_manifest, progress=progress)
        except ValueError as e:
            snapctl_error(
                message=f"Exception: {e}",
                code=SNAPCTL_INTERNAL_SERVER_ERROR, progress=progress)
        except RequestException as e:
            snapctl_error(
                message=f"Exception: Unable to create snapend manifest {e}",
                code=SNAPCTL_SNAPEND_MANIFEST_CREATE_ERROR, progress=progress)
        finally:
            progress.stop()
        snapctl_error(
            message='Failed to create snapend manifest.',
            code=SNAPCTL_SNAPEND_MANIFEST_CREATE_ERROR, progress=progress)

    def update(self) -> bool:
        """
          Update a snapend manifest
          @test -
          `python -m snapctl snapend-manifest update --manifest-path-filename ./snapend-manifest.json --features WEB_SOCKETS  --out-path-filename ./snapend-updated-manifest.json`
        """
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        )
        progress.start()
        progress.add_task(
            description='Updating snapend manifest...', total=None)
        try:
            if 'applied_configuration' in self.manifest:
                info('Applied configuration found in the manifest. ')
                warning(
                    'You need to ensure you have synced the manifest from remote. ' +
                    'Else if you try applying the newly generated manifest it may not work.')

            current_snaps = self.manifest['service_definitions']
            current_snap_ids = [snap['id'] for snap in current_snaps]
            final_snaps = []
            if self.snaps and self.snaps != '':
                for snap_id in self.snaps.split(','):
                    snap_id = snap_id.strip()
                    if snap_id == '':
                        continue
                    if snap_id in current_snap_ids:
                        warning(
                            f"Snap {snap_id} already exists in the manifest. Skipping...")
                        final_snaps.append(
                            current_snaps[current_snap_ids.index(snap_id)])
                        continue
                    snap_found = False
                    for snap in self.remote_snaps:
                        if snap['id'] == snap_id:
                            snap_found = True
                            snap_sd = self._get_snap_sd(snap_id)
                            final_snaps.append(snap_sd)
                            info(f"Added snap {snap_id} to the manifest.")
                            break
                    if not snap_found:
                        snapctl_error(
                            message=f"Snap ID {snap_id} not found in your snaps.",
                            code=SNAPCTL_INPUT_ERROR,
                            progress=progress)
            found_auth = False
            for final_snap in final_snaps:
                if final_snap['id'] == SnapendManifest.AUTH_SNAP_ID:
                    found_auth = True
                    break
            if not found_auth:
                auth_sd = self._get_snap_sd(SnapendManifest.AUTH_SNAP_ID)
                final_snaps.append(auth_sd)
                warning(
                    'Auth snap is required for snapend. Added auth snap to the manifest.')
            warning(
                f'Old snaps list "{",".join(current_snap_ids)}" will be ' +
                f'replaced with new snaps list "{",".join([snap['id'] for snap in final_snaps])}"')
            self.manifest['service_definitions'] = final_snaps

            final_features = []
            if self.features and self.features != '':
                current_features = self.manifest['feature_definitions']
                for feature in self.features.split(','):
                    feature = feature.strip()
                    if feature == '':
                        continue
                    if feature.upper() in current_features:
                        warning(
                            f"Feature {feature} already exists in the manifest. Skipping...")
                    final_features.append(feature.upper())
            warning(
                f'Old features list: "{",".join(self.manifest["feature_definitions"])}" will ' +
                f'be replaced with new features list: "{",".join([feature for feature in final_features])}"')
            final_features.sort()
            self.manifest['feature_definitions'] = final_features

            # Write output
            # Based on the out-path extension, write JSON or YAML
            if self.out_path_filename.endswith('.yaml') or self.out_path_filename.endswith('.yml'):
                try:
                    import yaml  # type: ignore
                except ImportError as e:
                    snapctl_error(
                        message="YAML output requested but PyYAML is not installed. "
                        "Install with: pip install pyyaml",
                        code=SNAPCTL_INPUT_ERROR,
                        progress=progress)
                with open(self.out_path_filename, 'w') as out_file:
                    yaml.dump(self.manifest, out_file, sort_keys=False)
            else:
                with open(self.out_path_filename, 'w') as out_file:
                    out_file.write(json.dumps(self.manifest, indent=4))
            info(f"Output written to {self.out_path_filename}")
            snapctl_success(
                message="Snapend manifest updated successfully.",
                progress=progress)
        except ValueError as e:
            snapctl_error(
                message=f"Exception: {e}",
                code=SNAPCTL_INTERNAL_SERVER_ERROR, progress=progress)
        except RequestException as e:
            snapctl_error(
                message=f"Exception: Unable to update snapend manifest {e}",
                code=SNAPCTL_SNAPEND_MANIFEST_UPDATE_ERROR, progress=progress)
        finally:
            progress.stop()
        snapctl_error(
            message='Failed to update the snapend manifest.',
            code=SNAPCTL_SNAPEND_MANIFEST_UPDATE_ERROR, progress=progress)

    def upgrade(self) -> bool:
        """
          Upgrade all Snap versions to the latest in a snapend manifest
          @test -
          `python -m snapctl snapend-manifest upgrade --manifest-path-filename ./snapser-upgrade-manifest.json --snaps auth,analytics --out-path-filename ./snapend-upgraded-manifest.json`
          `python -m snapctl snapend-manifest upgrade --manifest-path-filename ./snapser-upgrade-manifest.json --out-path-filename ./snapend-upgraded-manifest.json`
        """
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        )
        progress.start()
        progress.add_task(
            description='Updating snapend manifest...', total=None)
        try:
            if 'applied_configuration' in self.manifest:
                info('Applied configuration found in the manifest. ')
                warning(
                    'You need to ensure you have synced the manifest from remote. ' +
                    'Else if you try applying the newly generated manifest it may not work.')

            current_snaps = self.manifest['service_definitions']
            force_snaps_upgrade = []
            if self.snaps and self.snaps != '':
                force_snaps_upgrade = [snap_id.strip()
                                       for snap_id in self.snaps.split(',')]
            # Look at self.remote_snaps, get the latest version for each snap
            for i, snap in enumerate(current_snaps):
                for remote_snap in self.remote_snaps:
                    if remote_snap['id'] == snap['id']:
                        if len(force_snaps_upgrade) > 0 and \
                                snap['id'] not in force_snaps_upgrade:
                            info(
                                f"Skipping snap {snap['id']} as it's not in the " +
                                f"--snaps list {','.join(force_snaps_upgrade)}")
                            break
                        if remote_snap['latest_version'] != snap['version']:
                            current_snaps[i] = self._get_snap_sd(snap['id'])
                            info(
                                f"Upgraded snap {snap['id']} from version " +
                                f"{snap['version']} to {remote_snap['latest_version']}.")
                        else:
                            info(
                                f"Snap {snap['id']} is already at the latest " +
                                f"version {snap['version']}. Skipping...")
                        break
            self.manifest['service_definitions'] = current_snaps

            # Write output
            # Based on the out-path extension, write JSON or YAML
            if self.out_path_filename.endswith('.yaml') or self.out_path_filename.endswith('.yml'):
                try:
                    import yaml  # type: ignore
                except ImportError as e:
                    snapctl_error(
                        message="YAML output requested but PyYAML is not installed. "
                        "Install with: pip install pyyaml",
                        code=SNAPCTL_INPUT_ERROR,
                        progress=progress)
                with open(self.out_path_filename, 'w') as out_file:
                    yaml.dump(self.manifest, out_file, sort_keys=False)
            else:
                with open(self.out_path_filename, 'w') as out_file:
                    out_file.write(json.dumps(self.manifest, indent=4))
            info(f"Output written to {self.out_path_filename}")
            snapctl_success(
                message="Snapend manifest upgraded successfully.",
                progress=progress)
        except ValueError as e:
            snapctl_error(
                message=f"Exception: {e}",
                code=SNAPCTL_INTERNAL_SERVER_ERROR, progress=progress)
        except RequestException as e:
            snapctl_error(
                message=f"Exception: Unable to upgrade the snapend manifest {e}",
                code=SNAPCTL_SNAPEND_MANIFEST_UPGRADE_ERROR, progress=progress)
        finally:
            progress.stop()
        snapctl_error(
            message='Failed to upgrade the snapend manifest.',
            code=SNAPCTL_SNAPEND_MANIFEST_UPGRADE_ERROR, progress=progress)
