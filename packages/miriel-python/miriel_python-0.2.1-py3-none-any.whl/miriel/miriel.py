import json
import logging
import os
import re
import time
from contextlib import ExitStack
from urllib.parse import urlparse

import requests
from requests.exceptions import HTTPError

COMMON_FILE_EXTENSIONS = [
    # Documents
    '.doc',
    '.docx',
    '.markdown',
    '.md',
    '.odt',
    '.pdf',
    '.rtf',
    '.tex',
    '.txt',
    # Spreadsheets / Data
    '.csv',
    '.json',
    '.ods',
    '.parquet',
    '.tsv',
    '.xls',
    '.xlsx',
    '.xml',
    '.yaml',
    '.yml',
    # Presentations
    '.odp',
    '.ppt',
    '.pptx',
    # Code / Config
    '.bat',
    '.c',
    '.cfg',
    '.cpp',
    '.cs',
    '.css',
    '.env',
    '.go',
    '.html',
    '.ini',
    '.ipynb',
    '.java',
    '.js',
    '.py',
    '.rb',
    '.sh',
    '.toml',
    '.ts',
    # Images
    '.bmp',
    '.gif',
    '.ico',
    '.jpeg',
    '.jpg',
    '.png',
    '.svg',
    '.tiff',
    '.webp',
    # Archives / Compressed
    '.7z',
    '.gz',
    '.rar',
    '.tar',
    '.xz',
    '.zip',
    # Audio / Video
    '.aac',
    '.avi',
    '.flac',
    '.mkv',
    '.mov',
    '.mp3',
    '.mp4',
    '.ogg',
    '.wav',
    '.webm',
    # Misc
    '.bin',
    '.db',
    '.exe',
    '.log',
    '.sqlite',
]
MAX_POLLING_INTERVAL = 60

_logger = logging.getLogger(__name__)


def _looks_like_path(s):
    s = s.strip()
    return (
        s.startswith(('~', '.', '..', os.sep))
        or os.name == 'nt'
        and re.match(r'^[a-zA-Z]:[\\/]', s)
        or os.path.sep in s
        or any(s.lower().endswith(ext) for ext in COMMON_FILE_EXTENSIONS)
    )


def _is_uri(s):
    """Return True if s is an HTTP/S (or other supported) URI."""
    p = urlparse(s)
    return p.scheme in (
        'dir',
        'directory',
        'discord',
        'file',
        'folder',
        'gcalendar',
        'http',
        'https',
        'rtsp',
        's3',
        'string',
    ) and (p.netloc or p.path)


class UnauthorizedError(Exception):
    pass


class Miriel:
    def __init__(
        self,
        api_key=None,
        base_url='https://api.prod.miriel.ai',
        verify=True,
        api_version='v2',
    ):
        """
        api_key: Your Miriel API key. Get one at https://miriel.ai
        base_url: Base URL for the Miriel API
        verify: Whether to verify SSL certificates
        api_version: API version to use
        """
        if not api_key:
            raise UnauthorizedError('API key is required. Please visit https://miriel.ai to sign up.')
        self.api_key = api_key
        self.api_version = api_version
        self.base_url = base_url
        self.verify = verify

    def serialize_payload_for_form(self, payload):
        """Convert all nested dicts/lists in the payload to JSON strings."""
        serialized = {}
        for key, value in payload.items():
            if isinstance(value, (dict, list)):
                serialized[key] = json.dumps(value)
            else:
                serialized[key] = value
        return serialized

    def make_post_request(self, route, payload=None, files=None):
        """
        Makes a POST request to the given URL.

        - If 'files' is provided, sends a multipart/form-data request:
        - The 'payload' is included as regular form fields via the 'data=' parameter.
        - Otherwise, sends a JSON body using the 'json=' parameter.
        """
        request_kwargs = {
            'verify': self.verify,
        }
        if files:
            # For file uploads (multipart/form-data)
            # 'payload' is sent as form fields in data=
            # Don't set 'Content-Type' here, requests does it automatically
            # when using files= parameter
            headers = {
                'Accept': 'application/json',
            }
            payload = self.serialize_payload_for_form(payload)
            request_kwargs = {
                'headers': headers,
                'data': payload,
                'files': files,
                **request_kwargs,
            }
        else:
            # For JSON-based requests
            headers = {
                'Content-Type': 'application/json',
            }
            request_kwargs = {
                'headers': headers,
                'json': payload,
                **request_kwargs,
            }

        return self._make_request(requests.post, route, **request_kwargs)

    def _make_request(self, method, route, **kwargs):
        try:
            # add auth header
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            kwargs['headers']['x-access-token'] = self.api_key

            # construct final url
            url = f'{self.base_url}/api/{self.api_version}/{route}'
            response = method(url, **kwargs)
            response.raise_for_status()
            try:
                return response.json()
            except ValueError:
                _logger.error(f'Error parsing JSON response: {response.text=}')
                raise
        except HTTPError as err:
            code = err.response.status_code
            if code == 401:
                raise UnauthorizedError('Invalid API key. Please visit https://miriel.ai to sign up.')
            else:
                _logger.error(f'Miriel request error ({code}): {response.text}')
                raise

    def query(self, query, **params):
        """
        required: query
        optional: input_images, response_format, user_id, project, metadata_query, num_results, want_llm, want_vector, want_graph, mock_response
        """
        route = 'query'
        payload = {'query': query, **{k: v for k, v in params.items() if v is not None}}
        return self.make_post_request(route, payload=payload)

    def wait_for_jobs(self, job_ids, polling_interval=None, user_id=None):
        """
        Poll the API for specific job_ids until all are 'completed'.
        """
        if not job_ids:
            return

        route = 'get_job_status'
        headers = {
            'Content-Type': 'application/json',
        }

        exponential_backoff = False
        if not polling_interval:
            exponential_backoff = True
            polling_interval = 1

        while True:
            payload = {'job_ids': job_ids}
            if user_id is not None:
                payload['user_id'] = user_id

            try:
                response = self._make_request(
                    requests.post,
                    route,
                    headers=headers,
                    json=payload,
                    verify=self.verify,
                )
            except (ValueError, HTTPError):
                time.sleep(polling_interval or 1)
                if exponential_backoff:
                    polling_interval = min(polling_interval * 2, MAX_POLLING_INTERVAL)
                continue

            statuses = response.get('jobs', {})
            pending_left = [jid for jid, st in statuses.items() if st != 'completed']

            if not pending_left:
                return  # all done

            _logger.info(f'Waiting on {len(pending_left)} job(s): {", ".join(pending_left)}')
            time.sleep(polling_interval or 1)
            if exponential_backoff:
                polling_interval = min(polling_interval * 2, MAX_POLLING_INTERVAL)

    def learn(
        self,
        input,
        user_id=None,
        metadata=None,
        force_string=False,
        discoverable=True,
        grant_ids=['*'],
        domain_restrictions=None,
        recursion_depth=0,
        priority=100,
        project=None,
        wait_for_complete=False,
        chunk_size=None,
        polling_interval=None,
        command=None,
        upsert_ids=None,
    ):
        """
        Add a string, URL, or file to the Miriel AI system for learning.
        If input is a valid path to a file or directory, uploads its contents.
        If the input looks like a path but doesn't exist, raises FileNotFoundError.
        Otherwise, input is treated as a literal string.

        force_string: True will always treat input as a string .
        upsert_id: optional dict of resource id to upsert documents. <filename or url>: resource_id
          if input is a literal string, the first upsert id in the dict will be used.
        command: add, upsert, or append. upsert and append require upsert_id.
        polling_interval: seconds between polling for job status when wait_for_complete=True.
          if not provided, uses exponential backoff starting at 1 second, capped at MAX_POLLING_INTERVAL.
        """
        # Handle file/directory path resolution
        if isinstance(input, str):
            expanded_path = os.path.expanduser(input)
            resolved_path = os.path.abspath(expanded_path)

            if os.path.exists(resolved_path):
                if not _looks_like_path(input):
                    _logger.info(
                        f"Input '{input}' did not look like a path, but a file was found and will be uploaded."
                    )
                input = resolved_path
                is_file = True
                is_directory = os.path.isdir(resolved_path)
            elif _is_uri(input) and not force_string:
                is_file = False
                is_directory = False
            elif _looks_like_path(input) and not force_string:
                raise FileNotFoundError(
                    f"Input '{input}' looks like a file or path, but no file was found at: {resolved_path}.\n"
                    'Hint: If this was meant to be a text string, use force_string=True.'
                )
            else:
                is_file = False
                is_directory = False
        else:
            if not force_string:
                raise TypeError(
                    f'Unsupported input type: {type(input)}. Provide a string path or literal string. '
                    'Use force_string=True to override.'
                )
            is_file = False
            is_directory = False

        # convert string priorities to integers
        if isinstance(priority, str):
            if priority == 'norank':
                priority = -1
            elif priority == 'pin':
                priority = -2
        payload = {
            'user_id': user_id,
            'metadata': metadata,
            'force_string': force_string,
            'discoverable': discoverable,
            'grant_ids': grant_ids,
            'domain_restrictions': domain_restrictions,
            'recursion_depth': recursion_depth,
            'priority': priority,
            'chunk_size': chunk_size,
            'polling_interval': polling_interval,
        }
        if project is not None:
            payload['project'] = project

        route = 'learn'
        files_list = None
        upsert_ids = upsert_ids or {}
        if is_file:
            files_list = []
            file_inputs = []
            # don't leave all the file handles open, use ExitStack to
            # automagically handle n open contexts...
            with ExitStack() as stack:
                if is_directory:
                    # Walk through directory and add all files
                    for dirpath, _, filenames in os.walk(input):
                        for filename in filenames:
                            filepath = os.path.join(dirpath, filename)
                            handle = stack.enter_context(open(filepath, 'rb'))
                            files_list.append(
                                (
                                    'files',  # send every file under the same field name
                                    (
                                        filename,
                                        handle,
                                        'application/octet-stream',
                                    ),
                                )
                            )
                            # new (2015.10) learn contract to support append
                            # and other options per-file
                            file_inputs.append(
                                {
                                    'value': filename,
                                    'upsert_id': upsert_ids.get(filename),
                                    'command': command,
                                }
                            )
                else:
                    # Single file
                    filename = os.path.basename(input)
                    handle = stack.enter_context(open(input, 'rb'))
                    files_list.append(('files', (filename, handle, 'application/octet-stream')))
                    file_inputs.append(
                        {
                            'value': filename,
                            'upsert_id': upsert_ids.get(filename),
                            'command': command,
                        }
                    )

                payload['input'] = file_inputs
                _logger.info(f'Uploading {len(payload["input"])} items, {len(files_list)} files...')
                _logger.debug(f'{payload=}')
                response = self.make_post_request(route, payload=payload, files=files_list)
        else:
            first_upsert_id = None
            if upsert_ids:
                # get first upsert id in dict
                first_upsert_id = next(iter(upsert_ids.values()))
            payload['input'] = [
                {
                    'value': input,
                    'upsert_id': first_upsert_id,
                    'command': command,
                }
            ]
            _logger.info(f'Uploading {len(payload["input"])} items...')
            _logger.debug(f'{payload=}')
            response = self.make_post_request(route, payload=payload)

        if wait_for_complete:
            # Use the actual job_ids we just enqueued
            job_ids = (response or {}).get('job_ids', [])

            if job_ids:
                self.wait_for_jobs(job_ids, polling_interval=polling_interval, user_id=user_id)
            else:
                # Fallback: if API didn't return job_ids, preserve legacy behavior
                if not polling_interval:
                    polling_interval = 1
                    exponential_backoff = True
                while self.count_non_completed_learning_jobs() > 0:
                    _logger.info('Waiting for all learning jobs to complete...')
                    time.sleep(polling_interval or 1)
                    if exponential_backoff:
                        polling_interval = min(polling_interval * 2, MAX_POLLING_INTERVAL)
        return response

    def get_learning_jobs(self):
        get_job_status_route = 'get_monitor_jobs'
        return self.make_post_request(get_job_status_route, payload={'job_status': 'all'})

    def count_non_completed_learning_jobs(self):
        jobs = self.get_learning_jobs()
        if not jobs:
            return 0
        pending_count = sum(len(group.get('job_list', [])) for group in jobs.get('pending_jobs', []))
        queued_count = len(jobs.get('queued_items', []))
        return pending_count + queued_count

    def update_document(
        self,
        document_id,
        user_id=None,
        metadata=None,
        discoverable=True,
        grant_ids=['*'],
        chunk_size=None,
    ):
        update_document_route = 'update_document'
        return self.make_post_request(
            update_document_route,
            payload={
                'user_id': user_id,
                'document_id': document_id,
                'metadata': metadata,
                'discoverable': discoverable,
                'grant_ids': grant_ids,
                'chunk_size': chunk_size,
            },
        )

    def create_user(self):
        create_user_route = 'create_user'
        return self.make_post_request(create_user_route, payload={})

    def set_document_access(self, user_id, document_id, grant_ids):
        set_document_access_route = 'set_document_access'
        return self.make_post_request(
            set_document_access_route,
            payload={
                'user_id': user_id,
                'document_id': document_id,
                'grant_ids': grant_ids,
            },
        )

    def get_document_by_id(self, document_id, user_id=None):
        get_document_by_id_route = 'get_document_by_id'
        return self.make_post_request(
            get_document_by_id_route,
            payload={'user_id': user_id, 'document_id': document_id},
        )

    def get_monitor_sources(self, user_id=None):
        get_monitor_sources_route = 'get_monitor_sources'
        return self.make_post_request(get_monitor_sources_route, payload={'user_id': user_id})

    def remove_all_documents(self, user_id=None, project=None):
        """
        removes all the user's documents

        project: optional project name. if provided, only removes documents in that project.
          otherwise, ALL documents are removed.
        """
        remove_all_documents_route = 'remove_all_documents'
        return self.make_post_request(remove_all_documents_route, payload={'user_id': user_id, 'project': project})

    def get_users(self):
        get_users_route = 'get_users'
        return self.make_post_request(get_users_route, payload={})

    def delete_user(self, user_id):
        delete_user_route = 'delete_user'
        return self.make_post_request(delete_user_route, payload={'user_id': user_id})

    def get_projects(self):
        """Get all projects belonging to the authenticated user"""
        get_projects_route = 'get_projects'
        return self.make_post_request(get_projects_route, payload={})

    def create_project(self, name):
        """Create a new project with the specified name"""
        create_project_route = 'create_project'
        return self.make_post_request(create_project_route, payload={'name': name})

    def delete_project(self, project_name):
        """Delete a project with the specified name"""
        delete_project_route = 'delete_project'
        return self.make_post_request(delete_project_route, payload={'name': project_name})

    def get_document_count(self):
        """Get the count of documents for the authenticated user"""
        get_document_count_route = 'get_document_count'
        return self.make_post_request(get_document_count_route, payload={})

    def get_user_policies(self):
        """Get all policies for the authenticated user"""
        get_user_policies_route = 'get_user_policies'
        return self.make_post_request(get_user_policies_route, payload={})

    def add_user_policy(self, policy, project_id=None):
        """Add a policy for the authenticated user, optionally associated with a project"""
        add_user_policy_route = 'add_user_policy'
        payload = {'policy': policy}
        if project_id is not None:
            payload['project_id'] = project_id
        return self.make_post_request(add_user_policy_route, payload=payload)

    def delete_user_policy(self, policy_id, project_id=None):
        """Delete a policy for the authenticated user by its ID, optionally associated with a project"""
        delete_user_policy_route = 'delete_user_policy'
        payload = {'policy_id': policy_id}
        if project_id is not None:
            payload['project_id'] = project_id
        return self.make_post_request(delete_user_policy_route, payload=payload)

    def remove_document(self, document_id, user_id=None):
        """Remove a specific document by its ID"""
        remove_document_route = 'remove_document'
        return self.make_post_request(
            remove_document_route,
            payload={'document_id': document_id, 'user_id': user_id},
        )

    def get_all_documents(self, user_id=None, project=None, metadata_query=None):
        """Get all documents, optionally filtered by project, user_id, or metadata query"""
        get_all_documents_route = 'get_all_documents'
        payload = {}
        if user_id is not None:
            payload['user_id'] = user_id
        if project is not None:
            payload['project'] = project
        if metadata_query is not None:
            payload['metadata_query'] = metadata_query
        return self.make_post_request(get_all_documents_route, payload=payload)

    def remove_resource(self, resource_id, user_id=None):
        """Remove a specific resource by its ID"""
        remove_resource_route = 'remove_resource'
        payload = {'resource_id': resource_id}
        if user_id is not None:
            payload['user_id'] = user_id
        return self.make_post_request(remove_resource_route, payload=payload)
