import json
import logging
import os

import tornado
from jupyter_server.base.handlers import APIHandler
from jupyter_server.extension.handler import ExtensionHandlerMixin

logger = logging.getLogger(__name__)

class SageMakerEnvHandler(ExtensionHandlerMixin, APIHandler):
    @tornado.web.authenticated
    def get(self):
        try:
            response = self.read_metadata()

            self.finish(json.dumps(response))

        except Exception as e:
            logger.exception("An error occurred:", e)

    @classmethod
    def read_metadata(cls):
        aws_region = os.getenv('AWS_REGION')
        dz_region = aws_region

        user_identifier = os.environ.get("DataZoneUserId", "")
        domain_id = os.environ.get("DataZoneDomainId", "")
        project_id = os.environ.get("DataZoneProjectId", "")
        env_id = os.environ.get("DataZoneEnvironmentId", "")
        dz_endpoint = os.environ.get("DataZoneEndpoint", "")
        dz_stage = os.environ.get("DataZoneStage", "")

        home = os.environ.get('HOME', '')
        data = cls.read_metadata_file()

        project_path = None
        # Attempt to retrieve the project path from the metadata
        if data and 'AdditionalMetadata' in data and 'ProjectSharedDirectory' in data['AdditionalMetadata']:
            project_path = data['AdditionalMetadata']['ProjectSharedDirectory']

        # If project_path is still None, try to retrieve the project path from the storage metadata file
        if not project_path:
            storage_data = cls.read_storage_metadata_file()
            project_path = storage_data["smusProjectDirectory"] if storage_data and 'smusProjectDirectory' in storage_data else None

        # Create a relative path by removing the home directory prefix, if project_path exists
        # If project_path is None, relative_path will also be None
        relative_path = project_path.replace(f"{home}/", "") if project_path else None

        if data and data['AdditionalMetadata']:
            if 'DataZoneDomainRegion' in data['AdditionalMetadata']:
                dz_region = data['AdditionalMetadata']['DataZoneDomainRegion']
            response = {
                "project_id": data['AdditionalMetadata']['DataZoneProjectId'],
                "domain_id": data['AdditionalMetadata']['DataZoneDomainId'],
                "user_id": data['AdditionalMetadata']['DataZoneUserId'],
                "environment_id": data['AdditionalMetadata']['DataZoneEnvironmentId'],
                "dz_endpoint": data['AdditionalMetadata']['DataZoneEndpoint'],
                "dz_stage": data['AdditionalMetadata']['DataZoneStage'],
                'dz_region': dz_region,
                "aws_region": aws_region,
                "sm_domain_id": data['DomainId'],
                "sm_space_name": data['SpaceName'],
                "sm_user_profile_name": data['AdditionalMetadata']['DataZoneUserId'],
                "sm_project_path": relative_path
            }
        else:
            response = {
                "project_id": project_id,
                "domain_id": domain_id,
                "user_id": user_identifier,
                "environment_id": env_id,
                "dz_endpoint": dz_endpoint,
                "dz_stage": dz_stage,
                "aws_region": aws_region,
                'dz_region': dz_region,
                "sm_project_path": relative_path
            }

        enabled_features_path = os.path.expanduser('~/.aws/enabled_features/enabled_features.json')
        if os.path.isfile(enabled_features_path):
            try:
                with open(enabled_features_path) as features_file:
                    features_data = json.load(features_file)
                    response['enabled_features'] = features_data.get('enabled_features', [])
            except Exception as e:
                logger.exception("An error occurred loading enabled_features:", e)
                response['enabled_features'] = []

        return response

    @classmethod
    def read_metadata_file(cls):
        try:
            with open('/opt/ml/metadata/resource-metadata.json') as json_file:
                data = json.load(json_file)
            return data
        except Exception as e:
            logger.exception("An error occurred reading metadata file:", e)
            return None

    @classmethod
    def read_storage_metadata_file(cls):
        try:
            with open('/home/sagemaker-user/.config/smus-storage-metadata.json') as json_file:
                data = json.load(json_file)
            return data
        except Exception as e:
            logger.exception("An error occurred reading metadata file:", e)
            return None


