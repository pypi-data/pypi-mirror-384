import uuid
import json
import zipfile
import logging
import os
from datetime import datetime
from io import BytesIO

import requests
import urllib.request
from tqdm import tqdm
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlencode

from imerit_ango.models.annotate import AnnotationPayload
from imerit_ango.models.chat_asset_creation_config import ChatAssetCreationConfig
from imerit_ango.models.export_options import ExportOptions
from imerit_ango.models.storage import Storage
from imerit_ango.models.invite import Invitation, RoleUpdate, ProjectMember
from imerit_ango.models.enums import Metrics, StorageFileTypes, ProjectRoles, ExportFormats
from imerit_ango.models.label_category import ToolCategory, ClassificationCategory, RelationCategory
from imerit_ango.models.utils import merge_annotations
from imerit_ango.models.asset_builder_template import AssetBuilderTemplate
from imerit_ango.modules.asset_builder_uploader import AssetBuilderUploader

DEFAULT_HOST = "https://imeritapi.ango.ai"
HEADERS = {'Content-Type': 'application/json'}


class SDK:
    def __init__(self, api_key: str, host: str = DEFAULT_HOST):
        self.api_key = api_key
        self.host = host
        self.session = requests.Session()
        self.setup_logger()

    def setup_logger(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        # Configure logger as needed
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def make_request(self, method: str, endpoint: str, payload: Optional[Dict] = None) -> Any:
        """
        Make a network request and handle exceptions.
        :param method: HTTP method
        :param endpoint: API endpoint
        :param payload: Request payload
        :return: JSON response
        """
        url = self.host + endpoint
        headers = {**HEADERS, 'apikey': self.api_key}
        try:
            response = self.session.request(method, url, headers=headers, json=payload)
            try:
                response.raise_for_status()
            except Exception as e:
                self.logger.error(response.text)
                raise Exception(response.text)
            return response.json()
        except Exception as e:
            self.logger.error(f"Error during request: {e}")
            raise e

    # ------------------------------------------------------------------------------------------------------------------
    # Project Level SDK Functions
    # ------------------------------------------------------------------------------------------------------------------
    def add_members_to_project(self, project_id: str, members: List[str], role: ProjectRoles) -> Dict:
        """
        Add a member to a project.
        """
        endpoint = f"/v2/project/{project_id}/assigned"
        payload = {"assignees": members, "role": role.value}

        return self.make_request("POST", endpoint, payload)

    def assign_batches(self, project_id: str, asset_ids: List[str], batches: List[str]) -> Dict:
        """
        Assign batches to assets in a project.
        """
        endpoint = "/v2/assignBatches"
        payload = {"assets": asset_ids, "batches": batches, "projectId": project_id}
        return self.make_request("POST", endpoint, payload)

    def assign_task(self, project_id: str, task_ids: List[str], stage_filter: str, email: str) -> Dict:
        """
        Assign a task to a user.
        :param project_id: Project ID
        :param task_ids: List of task IDs
        :param stage_filter: Stage of the task
        :param email: Email of the user to whom the task is assigned
        :return: JSON response
        """
        endpoint = "/v2/task/assign"
        payload = {"project": project_id, "tasks": task_ids, "user": email, "stage": stage_filter}
        return self.make_request("POST", endpoint, payload)

    def create_attachment(self, project_id: str, attachments: List[dict]) -> Dict:
        """
        Create attachments for a project.
        """
        endpoint = "/v2/attachments"
        payload = {"project": project_id, "attachments": attachments}
        return self.make_request("POST", endpoint, payload)

    def create_batch(self, project_id: str, batch_name: str) -> List[Dict]:
        """
        Create a new batch in a project.
        """
        endpoint = f"/v2/batches/{project_id}"
        batches = self.get_batches(project_id)
        payload = {"batches": batches + [{'name': batch_name}]}
        return self.make_request("POST", endpoint, payload)

    def create_batches(self, project_id: str, batch_names: List[str]) -> List[Dict]:
        """
        Create batches in bulk in a project, skipping those that already exist
        """
        endpoint = f"/v2/batches/{project_id}"
        existing_batches = self.get_batches(project_id)
        existing_batch_names = {batch['name'] for batch in existing_batches}

        new_batches = [{'name': batch_name} for batch_name in batch_names if batch_name not in existing_batch_names]
        if not new_batches:
            return []

        final_batches = existing_batches + new_batches
        payload = {"batches": final_batches}
        return self.make_request("POST", endpoint, payload)

    def create_issue(self, task_id: str, content: str, position: List[int] = None) -> Dict:
        """
        Create an issue for a task.
        """
        endpoint = "/v2/issues"
        payload = {"content": content, "labelTask": str(task_id)}
        if position:
            payload['position'] = str(position)
        return self.make_request("POST", endpoint, payload)

    def create_label_set(self, project_id: str, tools: List[ToolCategory] = [],
                         classifications: List[ClassificationCategory] = [],
                         relations: List[RelationCategory] = [],
                         raw_category_schema: Dict = None) -> Dict:
        """
        Create a label set for a project.
        """
        endpoint = f"/v2/project/{project_id}"
        payload = {
            "categorySchema": {
                "tools": [t.toDict() for t in tools],
                "classifications": [c.toDict() for c in classifications],
                "relations": [r.toDict() for r in relations]
            }
        }
        if raw_category_schema:
            payload["categorySchema"] = raw_category_schema

        return self.make_request("POST", endpoint, payload)

    def create_project(self, name: str, description: str = "") -> Dict:
        """
        Create a new project.
        """
        endpoint = "/v2/project"
        payload = {"name": name, "description": description}
        return self.make_request("POST", endpoint, payload)

    def delete_issue(self, project_id: str, issue_id: str) -> Dict:
        """
        Create an issue for a task.
        """
        endpoint = f"/v2/issues/{issue_id}?project={project_id}"
        return self.make_request("DELETE", endpoint)

    def delete_project(self, project_id: str) -> Dict:
        """
        Soft delete a project and all related data.

        This calls the v2 API route that performs a soft delete (marks project, assets,
        label tasks, issues, and histories as deleted) without purging storage files.
        """
        endpoint = f"/v2/project/{project_id}"
        return self.make_request("DELETE", endpoint)

    def export(self, project_id: str, options: ExportOptions = ExportOptions(), zip_file_path=None) -> Any:
        return self.exportV3(project_id, options, zip_file_path)

    def exportV3(self, project_id: str, options: ExportOptions = ExportOptions(), zip_file_path=None):
        """
        Export tasks from a project.
        """
        params = options.toDict()
        params['project'] = project_id

        url = f"{self.host}/v2/export?{urlencode(params)}"
        headers = {'apikey': self.api_key}

        response = self.session.get(url, headers=headers)
        response.raise_for_status()  # raises an HTTPError if the response was an HTTP 4xx or 5xx

        link = response.json()['data']['exportPath']
        filehandle, _ = urllib.request.urlretrieve(link)

        if zip_file_path:
            urllib.request.urlretrieve(link, zip_file_path)
            pass
        else:
            with zipfile.ZipFile(filehandle, 'r') as zip_file_object:
                first_file = zip_file_object.namelist()[0]
                with zip_file_object.open(first_file) as file:
                    content = file.read()
                    if options.export_format == ExportFormats.NDJSON:
                        json_response = self.__generate_ndjson_iterator(content), content.count(b'\n') + 1
                    else:
                        json_response = json.loads(content)

            return json_response

    def get_assets(self, project_id: str, page: int = 1, limit: int = 10, filters: Dict = {}) -> Dict:
        """
        Retrieve assets for a project with optional filters.

        :param project_id: The ID of the project to retrieve assets from.
        :param page: The page number of the assets list.
        :param limit: The number of assets to return per page.
        :param filters: Additional filters as keyword arguments.
            possible filters are:
            {
                _id : str,
                externalId: str,
                isPreLabeled: bool,
                batches: ["<batch_id_1>", "<batch_id_2>"] #assets should have both this is not any query
            }
        :return: A dictionary representing the response from the API.
        """
        endpoint = f"/v2/project/{project_id}/assets?page={page}&limit={limit}&filters={json.dumps(filters)}"
        return self.make_request("GET", endpoint)

    def get_batches(self, project_id: str) -> List[Dict]:
        """
        Get batches for a project.
        """
        project_data = self.get_project(project_id)
        if 'data' in project_data:
            return project_data.get("data", {}).get("project", {}).get("batches", [])
        else:
            self.logger.error('Invalid Project Id!')
            return []

    def get_issues(self, project_id: str, asset_id: str = None, task_id: str = None, stage_id: str = None,
                   created_by: str = None) -> Dict:
        """
        Retrieve issues for a project, optionally filtered by asset, task, stage, or creator.
        """
        # Base endpoint with required project_id
        endpoint = f"/v2/issues?project={project_id}"

        # Append additional parameters if they are not None
        if asset_id is not None:
            endpoint += f"&asset={asset_id}"
        if task_id is not None:
            endpoint += f"&labelTask={task_id}"
        if stage_id is not None:
            endpoint += f"&stage={stage_id}"
        if created_by is not None:
            endpoint += f"&createdBy={created_by}"

        # Make the HTTP GET request with the constructed endpoint
        return self.make_request("GET", endpoint)

    def get_metrics(self, project_id: str, metric: Metrics) -> Dict:
        """
        Retrieve metrics for a project.
        """
        endpoint = f"/v2/{project_id}/overview/{metric.value}"
        return self.make_request("GET", endpoint)

    def get_project(self, project_id: str) -> Dict:
        """
        Get a specific project by ID.
        :param project_id: ID of the project
        :return: JSON response of the project
        """
        endpoint = f"/v2/project/{project_id}"
        return self.make_request("GET", endpoint)

    def get_task(self, task_id: str) -> Dict:
        """
        Retrieve a specific task by its ID.
        :param task_id: ID of the task
        :return: JSON response of the task
        """
        endpoint = f"/v2/task/{task_id}"
        return self.make_request("GET", endpoint)

    def get_tasks(self, project_id: str, page: int = 1, limit: int = 10, status: Optional[str] = None,
                  stage: Optional[str] = None, batches: Optional[List[str]] = None, include_answer=False) -> Dict:
        """
        Get tasks for a specific project.
        :param include_answer: Selection of answer data in the response or not
        :param project_id: ID of the project
        :param page: Page number
        :param limit: Number of items per page
        :param status: Filter tasks by status
        :param stage: Filter tasks by stage
        :param batches: Filter tasks by batches
        :return: JSON response of tasks
        """
        endpoint = f"/v2/project/{project_id}/tasks?page={page}&limit={limit}&includeAnswer={include_answer}"
        if status:
            endpoint += f"&status[eq]={status}"
        if batches:
            endpoint += f"&batches={json.dumps(batches)}"
        if stage:
            endpoint += f"&stage={stage}"
        return self.make_request("GET", endpoint)

    def get_task_history(self, task_history_id: Optional[str] = None, task_id: Optional[str] = None) -> Dict:
        """
        Retrieve the history of a task.
        """
        if task_history_id:
            endpoint = f"/v2/taskHistory/{task_history_id}"
        elif task_id:
            endpoint = f"/v2/task/{task_id}/history"
        else:
            self.logger.error("id or task_id should be specified!")
            return {}
        return self.make_request("GET", endpoint)
    

    def import_labels(self, project_id: str, labels: List[dict]) -> Dict:
        """
        Import labels into a project.
        """
        endpoint = "/v2/import/labels"
        payload = {"project": project_id, "jsonContent": labels}
        return self.make_request("POST", endpoint, payload)

    def list_projects(self, page: int = 1, limit: int = 10) -> Dict:
        """
        List projects with pagination.
        :param page: Page number
        :param limit: Number of items per page
        :return: JSON response of projects list
        """
        endpoint = f"/v2/listProjects?page={page}&limit={limit}"
        return self.make_request("GET", endpoint)

    def update_workflow_stages(self, project_id: str, stages: List[dict]) -> Dict:
        """
        Update the workflow stages of a project.
        """
        endpoint = f"/v2/project/{project_id}"
        payload = {"stages": stages}
        return self.make_request("POST", endpoint, payload)

    def upload_files(self, project_id: str, file_paths: List, storage_id: str = None, batches: List[str] = None, priority: int = 0):
        if storage_id and not self.__check_storages(storage_id):
            raise "Storage ID is Invalid!"
        assets = []
        for path in tqdm(file_paths):
            uid = uuid.uuid4().hex
            context_data = None
            metadata = None
            if isinstance(path, str):
                data = path
                external_id = None
            else:
                data = path.get("data")
                external_id = path.get("externalId", None)
                context_data = path.get("contextData", None)
                metadata = path.get("metadata", None)
            file = open(data, 'rb')
            fname = uid + '.' + file.name.split('.')[-1]
            if external_id is None:
                external_id = file.name
            url = self._get_upload_url(file_name=fname, project=project_id,
                                       file_type=StorageFileTypes.ASSET, storage_id=storage_id)
            requests.put(url, data=file.read())
            asset = {'data': url.split('?')[0],
                     'externalId': external_id,
                     'contextData': context_data,
                     'metadata': metadata}
            assets.append(asset)

        response = self.upload_files_cloud(project_id, assets, storage_id, batches, priority=priority, upload_local="true")
        return response

    def upload_files_cloud(self, project_id: str, assets, storage_id: str = None, batches: List[str] = None,
                           priority: int = 0, upload_local=None):
        if storage_id and not self.__check_storages(storage_id):
            raise "Storage ID is Invalid!"
        url = "%s/v2/project/%s/cloud" % (self.host, project_id)

        for a in assets:
            if storage_id:
                a['storage'] = storage_id
            if "batches" in a:
                a['batches'] = self.__switch_batch_names_with_ids(project_id, a['batches'])

        if batches:
            batch_ids = self.__switch_batch_names_with_ids(project_id, batches)
            url += "?batches=%s" % json.dumps(batch_ids)

        payload = json.dumps({"assets": assets, "uploadLocal": upload_local, "priority": priority})
        headers = {
            'Content-Type': 'application/json',
            'apikey': self.api_key
        }

        response = self.session.post(url, headers=headers, data=payload)
        return response.json()

    def delete_assets(self, project_id: str, asset_ids: List[str]) -> Dict:
        """
        Soft delete multiple assets in a project.

        :param project_id: The project identifier
        :param asset_ids: List of asset IDs to soft delete
        :return: JSON response from the server
        """
        endpoint = f"/v2/project/{project_id}/assets"
        payload = {"project": project_id, "assets": asset_ids}
        return self.make_request("DELETE", endpoint, payload)

    def upload_chat_assets(
            self,
            project_id: str,
            chat_asset_creation_config: ChatAssetCreationConfig,
            priority: int = 0
    ):
        """
        Upload chat assets to a project, optionally using a pre-created conversation file and by connecting to an LLM.

        :param chat_asset_creation_config: Configuration for chat asset creation, including project ID,
            number of assets, storage details, LLM config (for dynamic/static behavior), and naming strategy.
            - If `storage_id` is not provided, assets will be uploaded to iMerit's private S3 bucket.
            - If `llm_config` is provided, assets will be dynamic (LLM-enabled). If not, they will be static.
        :param conversations_json: Optional path to a JSON file containing conversation data.
            - If provided, the file will be used to create assets from the given conversations and
            'number_of_assets' field will be ignored. Instead number of conversations in the JSON will be used to determine
            the number of assets to be creeated.
            - If not provided, empty chat assets will be created.
        :return: JSON response from the server, including the number of assets created or error details if the request fails.
        """
        request_url = f"{self.host}/v2/project/{project_id}/chat"
        headers = {"apikey": self.api_key}

        # Warnings for missing optional fields
        if chat_asset_creation_config.storage_id is None:
            self.logger.warning("'storage_id' field is not set, uploading to iMerit's private S3 bucket.")
        if chat_asset_creation_config.llm_config is None:
            self.logger.warning("'llm_config' field is not set, created assets will be 'static'")

        # Base request data
        data = {
            "projectId": project_id,
            "priority": priority,
            "storageId": chat_asset_creation_config.storage_id,
            "bucket": chat_asset_creation_config.bucket_name,
            "numberOfConversations": str(chat_asset_creation_config.number_of_assets),
            "namingStrategy": json.dumps({
                "type": chat_asset_creation_config.naming_strategy.type
            })
        }
        # Optional LLM config
        if chat_asset_creation_config.llm_config:
            data["llmConfig"] = json.dumps({
                "id": chat_asset_creation_config.llm_config.id,
            })

        # POST request with or without file
        if chat_asset_creation_config.conversation_json:
            with open(chat_asset_creation_config.conversation_json, "rb") as f:
                files = {"file": f}
                response = self.session.post(request_url, headers=headers, data=data, files=files)
        else:
            response = self.session.post(request_url, headers=headers, data=data)

        # Response handling
        response_json = response.json()
        error = response_json.get("error")
        if error:
            message = response_json.get("message", "Something went wrong")
            status_code = error.get("statusCode", 500)
            self.logger.error(f"{status_code} - {message}")
        else:
            assets_created = response_json.get("data", {}).get("assets", {}).get("assetsCreated", 0)
            self.logger.info(f"Created {assets_created} chat assets successfully.")

        return response_json

    def requeue_tasks(self, project_id: str, to_stage_id: str, filters: Optional[Dict] = None,
                      options: Optional[Dict] = None) -> Dict:
        """
        Requeue tasks in a specific project.

        :param project_id: ID of the project
        :param to_stage_id: ID of the stage to requeue tasks to
        :param filters: Optional dictionary of filters (taskIds, externalIds, assetIds, fromStageIds)
        :param options: Optional dictionary of options (removeAnnotations, removeAssignee, removeStageHistory)
        :return: JSON response of the requeue operation
        """
        endpoint = f"/v2/project/{project_id}/requeueTasks"

        payload = {
            "toStageId": to_stage_id,
            "filters": filters or {},
            "options": options or {}
        }

        response = self.make_request("POST", endpoint, payload)
        return response

    def update_tasks_priority(self, project_id: str, priority: int, filters: Optional[Dict] = None) -> Dict:
        """
        Update priotiy of tasks in a specific project.

        :param project_id: ID of the project
        :param to_stage_id: ID of the stage to requeue tasks to
        :param filters: Optional dictionary of filters (taskIds, externalIds, assetIds, fromStageIds)
        :param options: Optional dictionary of options (removeAnnotations, removeAssignee, removeStageHistory)
        :return: JSON response of the requeue operation
        """
        endpoint = f"/v2/project/{project_id}/updatePriority"

        payload = {
            "filters": filters or {},
            "priority": priority
        }

        response = self.make_request("POST", endpoint, payload)
        return response

    def get_project_performance(self, project_id: str, interval: List[datetime] = None,
                                batches: List[str] = None) -> Dict:
        """
        Export performance data for a project.
        """
        endpoint = f"/v2/performance/{project_id}"
        payload = {}
        if interval:
            payload["interval"] = [interval[0].strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                                   interval[1].strftime('%Y-%m-%dT%H:%M:%S.%fZ')]
        if batches:
            payload["batches"] = self.__switch_batch_names_with_ids(project_id, batches)
        return self.make_request("POST", endpoint, payload)

    # ------------------------------------------------------------------------------------------------------------------
    # Organization Level SDK Functions
    # ------------------------------------------------------------------------------------------------------------------
    def create_storage(self, storage_data: Storage) -> Dict:
        """
        Create a new storage.
        """
        endpoint = "/v2/storages/"
        return self.make_request("POST", endpoint, storage_data.to_dict())

    def delete_organization_invites(self, organization_id: str, invite_emails: List[str]) -> Dict:
        """
        Delete invites from an organization with email.
        """
        endpoint = f"/v2/organization/{organization_id}/invites"
        payload = {"invites": invite_emails}
        return self.make_request("DELETE", endpoint, payload)

    def delete_organization_members(self, organization_id: str, member_emails: List[str]) -> Dict:
        """
        Delete members from an organization.
        """
        endpoint = f"/v2/organization/{organization_id}/users"
        payload = {"users": member_emails}
        return self.make_request("DELETE", endpoint, payload)

    def delete_storage(self, storage_id: str) -> Dict:
        """
        Delete a specific storage.
        """
        endpoint = f"/v2/storages/{storage_id}"
        return self.make_request("DELETE", endpoint)

    def get_organization_invites(self, organization_id: str) -> Dict:
        """
        Get invites of an organization.
        """
        endpoint = f"/v2/organization/{organization_id}/invites?status=pending"
        return self.make_request("GET", endpoint)

    def get_organization_members(self, organization_id: str) -> Dict:
        """
        Get members of an organization.
        """
        endpoint = f"/v2/organization/{organization_id}/users"
        return self.make_request("GET", endpoint)

    def get_storages(self, storage_id: Optional[str] = None) -> Dict:
        """
        Retrieve storage information.
        """
        endpoint = "/v2/storages"
        if storage_id:
            endpoint += f"?_id={storage_id}"
        response = self.make_request("GET", endpoint)
        if storage_id:
            for i in response.get('data', {}).get("storages", []):
                if i["_id"] == storage_id:
                    return i
        return response

    def invite_members_to_org(self, organization_id: str, invite_data: Invitation) -> Dict:
        """
        Invite a member to the organization.
        """
        endpoint = f"/v2/organization/{organization_id}/invites"
        return self.make_request("POST", endpoint, invite_data.toDict())

    def update_organization_members_role(self, organization_id: str, role_updates: List[RoleUpdate]) -> Dict:
        """
        Update organization members in bulk.
        """
        endpoint = f"/v2/organization/{organization_id}/users"
        members_dict = [member.toDict() for member in role_updates]
        payload = {"users": members_dict}
        return self.make_request("POST", endpoint, payload)
    
    def get_asset_builder_templates(self, project_id: str) -> Dict:
        """
        Get all asset builder templates for a project. 
        
        A convenience function to get the templates from the project object.
        """
        project = self.get_project(project_id)
        return project.get("data", {}).get("project", {}).get("assetBuilderTemplates", [])

    def create_asset_builder_template(self, project_id: str, template: AssetBuilderTemplate) -> Dict:
        """
        Create an asset builder template.
        
        :param project_id: ID of the project to create the template in
        :param template: AssetBuilderTemplate object containing the template configuration
        :return: JSON response from the server
        
        Example template structure:
        {
            "batchColumn": "doc1",
            "data_config": {
                "column1": {
                    "type": "img",
                    "storage": "Public",
                    "include_in_export": false
                }
            },
            "description": "abc",
            "name": "hey",
            "external_id_column": "column1",
            "template": "abc",
            "pre_label_config": {
                "cla_schema_id": {
                    "cla": {
                        "schemaId": "123",
                    },
                    "value": "column1"
                }
            }
        }
        """
        try:
            template.validate()
        except Exception as e:
            self.logger.error(f"Invalid template: {e}")
            raise Exception(f"Invalid template: {e}")
        
        endpoint = f"/v2/project/{project_id}/assetBuilderTemplates"
        payload = template.to_dict()
        return self.make_request("POST", endpoint, payload)

    def upload_files_with_asset_builder(self, project_id, template_id, input_file_path, parse_config={}, priority = 0):
        # Get project information
        try:
            project = self.get_project(project_id)
        except:
            self.logger.error(f"Couldn't find project (id={project_id})")
            raise Exception("Project with given ID does not exist.")

        # Get template information from project
        project_templates = project.get("data", {}).get("project", {}).get("assetBuilderTemplates", [])
        project_classifications = project.get("categorySchema", {}).get("classifications", {})
        if not project_templates or len(project_templates) == 0:
            self.logger.warning(f"Project (id={project_id}) does not have templates.")
            raise Exception(f"Project {project_id} does not have any Asset Builder templates.")

        # Find target template
        target_template = None
        for template in project_templates:
            if template["_id"] == template_id:
                target_template = template
                break
        if not target_template:
            self.logger.error(f"Template (id={template_id}) in project (id={project_id}) can't be found.")
            raise Exception(f"Template with  given ID does not exist.")

        # Parse the input file, prepare the assets, and start upload
        asset_builder = AssetBuilderUploader()
        asset_builder.read_file(input_file_path, parse_config)
        assets, new_batches = asset_builder.prepare_assets(target_template, project_classifications)
        batch_ids = self.create_batches(project_id, list(new_batches))
        assets = asset_builder.replace_batch_names_with_batch_ids(batch_ids)

        # Upload via upload_files_cloud function
        self.upload_files_cloud(project_id, assets, None, None, priority=priority, upload_local='true')
        self.logger.info(f"Successfully uploaded {len(assets)} assets to project {project_id}")

    def upload_instructions(self, project_id: str, file_path: str, storage_id: str = None, bucket: str = None) -> Dict:
        """
        Upload instructions file to a project.

        :param project_id: ID of the project to upload instructions to
        :param file_path: Path to the instructions file to upload
        :param storage_id: Optional storage ID for custom storage
        :param bucket: Optional bucket name for storage
        :return: JSON response from the server
        """
        endpoint = f"/v2/project/{project_id}/instructions"

        # Construct query parameters
        params = {}
        if storage_id:
            params['storageId'] = storage_id
        if bucket:
            params['bucket'] = bucket

        # Build URL with query parameters
        url = f"{self.host}{endpoint}"
        if params:
            url += f"?{urlencode(params)}"

        headers = {'apikey': self.api_key}

        try:
            # Open and upload the file
            with open(file_path, 'rb') as file:
                # Extract the original filename to preserve file type
                filename = os.path.basename(file_path)
                files = {'file': (filename, file)}
                response = self.session.post(url, headers=headers, files=files)
                response.raise_for_status()

                self.logger.info(f"Successfully uploaded instructions file to project {project_id}")
                return response.json()

        except FileNotFoundError:
            self.logger.error(f"Instructions file not found: {file_path}")
            raise Exception(f"File not found: {file_path}")
        except Exception as e:
            self.logger.error(f"Error uploading instructions: {e}")
            raise e

    def annotate_task(self, task_id: str, payload: AnnotationPayload, overwrite=False, send_to_next_stage=False) -> bool:
        return self._annotate_task(task_id, payload, overwrite, send_to_next_stage)

    # ------------------------------------------------------------------------------------------------------------------
    # Private Functions
    # ------------------------------------------------------------------------------------------------------------------
    def _annotate_task(self, task_id: str, payload: AnnotationPayload, overwrite=False, send_to_next_stage=False,
                       is_plugin=False) -> bool:
        """
        Annotate a task with a given answer.
        """
        # If brush arrays are provided, upload them and populate URLs before sending
        try:
            payload = self.__ensure_brush_data_uploaded(task_id, payload, overwrite)
        except Exception as e:
            self.logger.error(f"Failed to upload brush data: {e}")

        if not overwrite:
            existing = self.get_task(task_id).get("data").get("task").get("answer")
            payload.answer = merge_annotations(existing, payload.answer)
        endpoint = f"/v2/annotate/{task_id}?nextStage={str(send_to_next_stage).lower()}&isPlugin={str(is_plugin).lower()}"

        response = self.make_request("POST", endpoint, payload.toDict())
        return response is not None

    def __check_storages(self, storage_id):
        resp = self.get_storages()
        storages_list = resp['data']['storages']
        storage_exists = False
        for t1 in storages_list:
            if '_id' in t1 and t1['_id'] == storage_id:
                storage_exists = True
        return storage_exists

    def __generate_ndjson_iterator(self, content):
        """
        :param content: NDJSON content as a string
        :return: Iterator yielding each JSON object
        """
        for line in content.splitlines():
            if line:  # skip empty lines
                yield json.loads(line)

    def __get_batches(self, project_id, batches):
        project_batches = self.get_batches(project_id)
        resp = []
        for b1 in batches:
            batch_exist = False
            for b2 in project_batches:
                if b1 == b2["_id"] or b1 == b2["name"]:
                    resp.append(b2["_id"])
                    batch_exist = True
            if not batch_exist:
                raise Exception("Batch %s not found" % b1)
        return resp

    def _get_upload_url(self, file_name: str, project: str, file_type: StorageFileTypes, storage_id: str = None):
        url = "%s/v2/getUploadUrl?name=%s&project=%s&type=%s" % (self.host, file_name, project, file_type.value)
        if storage_id:
            url += "&storageId=%s" % storage_id
        headers = {
            'apikey': self.api_key
        }
        r = self.session.get(url, headers=headers).json()
        url = r["data"]["uploadUrl"]
        return url

    def _get_signed_url(self, asset_url: str, project: str, file_type: StorageFileTypes, storage_id: str = None):

        url = "%s/v2/getSignedUrl?name=%s&project=%s&type=%s" % (self.host, asset_url, project, file_type.value)
        if storage_id:
            url += "&storageId=%s" % storage_id
        headers = {
            'apikey': self.api_key
        }
        r = self.session.get(url, headers=headers).json()
        url = r["data"]["signedUrl"]
        return url

    def _plugin_log(self, log):
        endpoint = "/v2/pluginLog"
        return self.make_request("POST", endpoint, log)

    def _plugin_response(self, response: Dict) -> Dict:
        """
        Handle plugin response.
        """
        endpoint = "/v2/pluginResponse"
        return self.make_request("POST", endpoint, response)

    def __switch_batch_names_with_ids(self, project_id, batch_list):
        project_batches = self.get_batches(project_id)

        resp = []
        for b1 in batch_list:
            batch_exist = False
            for b2 in project_batches:
                if b1 == b2["_id"] or b1 == b2["name"]:
                    resp.append(b2["_id"])
                    batch_exist = True
            if not batch_exist:
                raise Exception("Batch %s not found" % b1)
        return resp

    # ------------------------------------------------------------------------------------------------------------------
    # Brush Upload Helpers
    # ------------------------------------------------------------------------------------------------------------------
    def __ensure_brush_data_uploaded(self, task_id: str, payload: AnnotationPayload, overwrite: bool) -> AnnotationPayload:
        """
        If payload contains raw brush arrays (numpy array or list), encode and upload them.
        When overwrite is False and an existing mask exists, merge new into existing.
        """
        if payload is None:
            return payload

        # Determine needs
        has_brush = getattr(payload, 'brush_data', None) is not None
        has_med = getattr(payload, 'medical_brush_data', None) is not None
        need_merge_brush = has_brush and not overwrite
        need_merge_med = has_med and not overwrite

        # Determine project id and existing mask URLs only if required
        project_id = getattr(payload, 'project_id', None)
        existing_brush_url = None
        existing_med_brush_url = None
        if project_id is None or need_merge_brush or need_merge_med:
            task = None
            try:
                task = self.get_task(task_id)
            except Exception:
                task = None
            if task:
                if project_id is None:
                    project_id = task.get('data', {}).get('task', {}).get('project')
                try:
                    t = task.get('data', {}).get('task', {})
                    existing_brush_url = t.get('brushDataUrl')
                    existing_med_brush_url = t.get('medicalBrushDataUrl')
                except Exception:
                    pass

        # No project id means we cannot upload; just return
        if not project_id:
            return payload

        # Upload standard brush
        if getattr(payload, 'brush_data_url', None) is None and has_brush:
            # If overwrite is False and an existing mask exists, merge the images
            if existing_brush_url and need_merge_brush:
                try:
                    import numpy as np
                    from PIL import Image
                except Exception as e:
                    raise Exception("numpy and Pillow are required to merge brush arrays") from e

                np_arr = np.array(payload.brush_data)
                # Build RGBA from provided array
                if np_arr.ndim == 2:
                    data = np.where(np_arr > 0, 255, 0).astype('uint8')
                    rgb = np.stack([data, data, data], axis=-1)
                    alpha = (data > 0).astype('uint8') * 255
                    rgba = np.concatenate([rgb, alpha[..., None]], axis=-1)
                elif np_arr.ndim == 3 and np_arr.shape[2] == 3:
                    rgb = np_arr.astype('uint8')
                    non_black = (rgb.sum(axis=2) > 0).astype('uint8') * 255
                    alpha = non_black
                    rgba = np.concatenate([rgb, alpha[..., None]], axis=-1)
                elif np_arr.ndim == 3 and np_arr.shape[2] == 4:
                    rgba = np_arr.astype('uint8')
                else:
                    raise Exception(f"Unsupported brush array shape: {np_arr.shape}")

                # Download existing mask and composite: new over existing
                try:
                    signed = self._get_signed_url(existing_brush_url, project=project_id, file_type=StorageFileTypes.BRUSH)
                    existing_resp = self.session.get(signed)
                    existing_resp.raise_for_status()
                    existing_img = Image.open(BytesIO(existing_resp.content)).convert('RGBA')
                    new_img = Image.fromarray(rgba, mode='RGBA')
                    if existing_img.size == new_img.size:
                        existing_np = np.array(existing_img)
                        new_np = np.array(new_img)
                        new_alpha = new_np[..., 3] > 0
                        out_np = np.where(new_alpha[..., None], new_np, existing_np)
                        image = Image.fromarray(out_np.astype('uint8'), mode='RGBA')
                    else:
                        image = new_img
                except Exception:
                    image = Image.fromarray(rgba, mode='RGBA')

                buf = BytesIO()
                image.save(buf, format='PNG')
                png_bytes = buf.getvalue()
                fname = f"{uuid.uuid4().hex}.png"
                upload_url = self._get_upload_url(file_name=fname, project=project_id, file_type=StorageFileTypes.BRUSH)
                resp = requests.put(upload_url, data=png_bytes)
                resp.raise_for_status()
                payload.brush_data_url = upload_url.split('?')[0]
            else:
                url = self.upload_brush_array(project_id, payload.brush_data, medical=False)
                payload.brush_data_url = url

        # Upload medical brush if provided
        if getattr(payload, 'medical_brush_data_url', None) is None and has_med:
            if existing_med_brush_url and need_merge_med:
                try:
                    med_url = self.__merge_nrrd_and_upload(project_id, existing_med_brush_url, payload.medical_brush_data)
                except Exception as e:
                    self.logger.warning(f"NRRD merge failed, uploading new volume instead: {e}")
                    med_url = self.upload_brush_array(project_id, payload.medical_brush_data, medical=True)
            else:
                med_url = self.upload_brush_array(project_id, payload.medical_brush_data, medical=True)
            payload.medical_brush_data_url = med_url

        return payload

    def upload_brush_array(self, project_id: str, arr, medical: bool = False) -> str:
        """
        Encode the given numpy/list array into a PNG and upload it. Returns the storage URL (without query).
        Supported inputs:
          - 2D array (H, W): binary/float/int mask → white (255) where non-zero else transparent
          - 3D array (H, W, 3): RGB → alpha 255 if non-black else 0
          - 3D array (H, W, 4): RGBA used as-is
        """
        import numpy as np
        # For medical volumetric arrays, encode NRRD; otherwise encode as PNG mask
        np_arr = np.array(arr)

        if medical and np_arr.ndim == 3 and (np_arr.shape[-1] not in (3, 4)):
            nrrd_bytes, ext = self.__encode_nrrd(np_arr)
            fname = f"{uuid.uuid4().hex}{ext}"
            file_type = StorageFileTypes.MEDICAL_BRUSH
            upload_url = self._get_upload_url(file_name=fname, project=project_id, file_type=file_type)
            resp = requests.put(upload_url, data=nrrd_bytes)
            resp.raise_for_status()
            return upload_url.split('?')[0]

        # Fallback/standard: 2D or 3-channel/4-channel RGBA as PNG
        try:
            from PIL import Image
        except Exception as e:
            raise Exception("Pillow is required to upload brush arrays as PNG") from e

        if np_arr.ndim == 2:
            data = np.where(np_arr > 0, 255, 0).astype('uint8')
            rgb = np.stack([data, data, data], axis=-1)
            alpha = (data > 0).astype('uint8') * 255
            rgba = np.concatenate([rgb, alpha[..., None]], axis=-1)
        elif np_arr.ndim == 3 and np_arr.shape[2] == 3:
            rgb = np_arr.astype('uint8')
            non_black = (rgb.sum(axis=2) > 0).astype('uint8') * 255
            alpha = non_black
            rgba = np.concatenate([rgb, alpha[..., None]], axis=-1)
        elif np_arr.ndim == 3 and np_arr.shape[2] == 4:
            rgba = np_arr.astype('uint8')
        else:
            raise Exception(f"Unsupported brush array shape: {np_arr.shape}")

        image = Image.fromarray(rgba, mode='RGBA')
        buf = BytesIO()
        image.save(buf, format='PNG')
        png_bytes = buf.getvalue()
        fname = f"{uuid.uuid4().hex}.png"
        file_type = StorageFileTypes.MEDICAL_BRUSH if medical else StorageFileTypes.BRUSH
        upload_url = self._get_upload_url(file_name=fname, project=project_id, file_type=file_type)
        resp = requests.put(upload_url, data=png_bytes)
        resp.raise_for_status()
        return upload_url.split('?')[0]

    def __encode_nrrd(self, volume) -> Tuple[bytes, str]:
        """
        Minimal NRRD writer for uint8 3D volume. Returns (bytes, extension)
        """
        import numpy as np
        import gzip

        vol = np.array(volume)
        if vol.ndim != 3:
            raise Exception("NRRD encoding expects a 3D volume")
        vol = vol.astype(np.uint8)

        # NRRD expects sizes in X Y Z. If volume shape is (Z, Y, X), reverse it for header
        z, y, x = vol.shape
        sizes = f"{x} {y} {z}"
        header_lines = [
            "NRRD0005",
            "type: uint8",
            "encoding: gzip",
            "dimension: 3",
            f"sizes: {sizes}",
            # keep optional fields minimal; viewers may still accept
        ]
        header = "\n".join(header_lines) + "\n\n"
        compressed = gzip.compress(vol.tobytes(order='C'))
        return header.encode('utf-8') + compressed, ".seg.nrrd"

    def __merge_nrrd_and_upload(self, project_id: str, existing_url: str, new_volume) -> str:
        """
        Merge a new uint8 3D mask volume into an existing NRRD mask and upload result.
        Merge rule: new voxel value replaces existing if new != 0, otherwise keep existing.
        Only supports dimension=3 uint8. If format is unsupported or sizes mismatch, falls back by raising.
        """
        import numpy as np
        import gzip

        # Download existing NRRD
        signed = self._get_signed_url(existing_url, project=project_id, file_type=StorageFileTypes.MEDICAL_BRUSH)
        resp = self.session.get(signed)
        resp.raise_for_status()
        blob = resp.content

        # Split header and data (supports CRLF and LF)
        sep_pos = blob.find(b"\n\n")
        sep_len = 2
        if sep_pos == -1:
            sep_pos = blob.find(b"\r\n\r\n")
            sep_len = 4 if sep_pos != -1 else sep_len
        if sep_pos == -1:
            raise Exception("Invalid NRRD: could not find header terminator")

        header_bytes = blob[:sep_pos]
        data_bytes = blob[sep_pos + sep_len:]
        header_text = header_bytes.decode('utf-8', errors='ignore')

        # Parse minimal header fields
        lines = [ln.strip() for ln in header_text.splitlines() if ln.strip()]
        if not lines or not lines[0].startswith('NRRD'):
            raise Exception("Invalid NRRD header")
        header_map = {}
        for line in lines[1:]:
            if ':' in line:
                k, v = line.split(':', 1)
                header_map[k.strip().lower()] = v.strip()

        encoding = header_map.get('encoding', 'gzip').lower()
        dimension = int(header_map.get('dimension', '3'))
        sizes_tokens = header_map.get('sizes', '').split()
        sizes = [int(x) for x in sizes_tokens if x.isdigit()]

        if dimension != 3 or not sizes:
            raise Exception("NRRD merge supports only dimension=3 with valid sizes")

        # Decompress existing data according to encoding
        if encoding == 'gzip':
            existing_raw = gzip.decompress(data_bytes)
        elif encoding == 'raw':
            existing_raw = data_bytes
        else:
            # Try gzip as a common case
            try:
                existing_raw = gzip.decompress(data_bytes)
            except Exception as e:
                raise Exception(f"Unsupported NRRD encoding: {encoding}") from e

        total = sizes[0] * sizes[1] * sizes[2]
        existing = np.frombuffer(existing_raw, dtype=np.uint8, count=total)

        new_arr = np.array(new_volume, dtype=np.uint8)
        if new_arr.size != total:
            raise Exception("New volume shape does not match existing NRRD size")
        new_flat = new_arr.ravel(order='C')

        out = np.where(new_flat != 0, new_flat, existing).astype(np.uint8)
        if encoding == 'gzip':
            out_bytes = gzip.compress(out.tobytes(order='C'))
        else:
            out_bytes = out.tobytes(order='C')

        # Reuse original header bytes for max compatibility
        merged_blob = header_bytes + (b"\n\n" if sep_len == 2 else b"\r\n\r\n") + out_bytes

        # Upload merged NRRD
        fname = f"{uuid.uuid4().hex}.seg.nrrd"
        upload_url = self._get_upload_url(file_name=fname, project=project_id, file_type=StorageFileTypes.MEDICAL_BRUSH)
        up = requests.put(upload_url, data=merged_blob)
        up.raise_for_status()
        return upload_url.split('?')[0]

    # ------------------------------------------------------------------------------------------------------------------
    # Other Functions
    # ------------------------------------------------------------------------------------------------------------------
    def file_explorer(self, bucket: str, storage_id: str, options: Dict = {}) -> Dict:
        """
        options = {
            folder: 'path/to/folder',
            files: ['file1.txt', 'file2.jpg'],
            upload: false,
            projectId: 'your-project-id',
            scrollToken: null,
            batches: []
            extensions: []
            }
            """
        endpoint = f"/v2/file-explorer"

        body = options
        body['bucket'] = bucket
        body['storageId'] = storage_id

        return self.make_request("POST", endpoint, body)

    def rerun_webhook(self, project_id: str, webhook_stage_id: str) -> Dict:

        endpoint = f"/v2//project/{project_id}/rerun-webhook"
        body = {"stageId": webhook_stage_id}

        return self.make_request("POST", endpoint, body)
