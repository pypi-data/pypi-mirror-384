import json
import os
import time
import logging
from typing import Callable, Tuple, Dict, Any
from io import BytesIO

import queue
import requests
import socketio
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Header, HTTPException, Depends

from imerit_ango.models.enums import StorageFileTypes, ExportFormats
from imerit_ango.models.export_options import ExportOptions
from imerit_ango.models.utils import merge_annotations
from imerit_ango.plugin_logger import PluginLogger
from imerit_ango.sdk import SDK

try:
    import asyncio
except ImportError:
    import trollius as asyncio

LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
logging.basicConfig(level=LOGLEVEL)

CONNECTOR = os.environ.get('CONNECTOR', 'WS').upper()
PORT = int(os.environ.get('PORT', '8080'))

class BasePlugin(socketio.ClientNamespace):
    def __init__(self, id: str, secret: str, callback: Callable):
        super().__init__('/plugin')
        self.id = id
        self.secret = secret
        self.logger = logging.getLogger("plugin")
        self.logger.setLevel(LOGLEVEL)
        self.callback = callback
        self.loop = asyncio.get_event_loop()

        if CONNECTOR == "WS":
            self.scheduler = BackgroundScheduler()
            self.scheduler.add_job(self.heartbeat, 'interval', seconds=60)
            self.scheduler.start()

    def _callback(self, data, sdk=None):
        try:
            return self.callback(data)
        except Exception as e:
            self.logger.error(e)
            response = {
                "error": True,
                "session": data.get("session", "")
            }
            if CONNECTOR == "WS":
                self.emit('response', response)
            elif sdk is not None:
                sdk._plugin_response(response)
            else:
                raise e

    def on_connect(self):
        self.heartbeat()
        self.logger.warning("Connected")

    def on_disconnect(self):
        self.logger.warning("Disconnected")
        _connect_ws(self, self.client.connection_url)

    def heartbeat(self):
        try:
            self.emit('heartbeat', {"id": self.id, "secret": self.secret})
        except Exception as e:
            self.logger.critical(e)
            os._exit(1)
        self.logger.info(f"Heartbeat at {time.time()}")

    def on_plugin(self, data):
        data["logger"] = self._get_logger(data)
        data["batches"] = data.get('batches', [])
        response = {
            "response": self._callback(data),
            "session": data.get("session", "")
        }
        if CONNECTOR != "WS":
            return response
        if response.get("response", None) is not None:
            self.emit('response', response)

    def _get_logger(self, data):
        return PluginLogger("logger", self.id, data.get("orgId", ""), data.get("apiKey", ""),
                            data.get("runBy", ""), data.get("session", ""), self, CONNECTOR, LOGLEVEL)

    def start(self, background = False):
        if not background:
            asyncio.get_event_loop().run_forever()

class ExportResponse:
    def __init__(self, file: BytesIO, file_name: str = "export.json", storage_id: str = None, bucket: str = None, options: ExportOptions = None):
        self.file = file
        self.file_name = file_name
        self.storage_id = storage_id
        self.bucket = bucket
        self.options = options

class ExportPlugin(BasePlugin):
    def __init__(self, id: str, secret: str, callback: Callable[[str, dict], Tuple[str, BytesIO]],
                 host="https://imeritapi.ango.ai", version: str = "v2"):
        super().__init__(id, secret, callback)
        self.host = host
        self.version = version

    def on_plugin(self, data):
        project_id = data.get('projectId')
        logger = super()._get_logger(data)
        api_key = data.get('apiKey')
        config = json.loads(data.get('configJSON', "{}"))
        include_key_frames_only = config.get('include_key_frames_only', False)
        sdk = SDK(api_key=api_key, host=self.host)

        try:
            export_options = ExportOptions(
                export_format=ExportFormats.NDJSON,
                stage=data.get('stage'),
                include_key_frames_only=config.get('include_key_frames_only', False),
                batches=data.get('batches'),
                doNotNotify=True
            )
            json_export, num_lines = sdk.export(project_id, export_options)
            data["numTasks"] = num_lines
        except Exception as e:
            logger.error(f"Error calling sdk.export: {e}")
            return

        data["jsonExport"] = json_export
        data["logger"] = logger

        resp = self._callback(data, sdk)

        file_name = resp.file_name
        upload_url = sdk._get_upload_url(file_name, project=project_id,
                                         file_type=StorageFileTypes.EXPORT, storage_id=resp.storage_id)
        signed_url = sdk._get_signed_url(upload_url, project=project_id,
                                         file_type=StorageFileTypes.EXPORT, storage_id=resp.storage_id)

        try:
            upload_resp = requests.put(upload_url, data=resp.file.getvalue())
            upload_resp.raise_for_status()
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
        except Exception as err:
            logger.error(f"Other error occurred: {err}")
        else:
            response = {
                "export": True,
                "response": signed_url,
                "session": data.get("session", "")
            }
            if CONNECTOR == "WS":
                self.emit('response', response)
            else:
                sdk._plugin_response(response)

class ModelPlugin(BasePlugin):
    def __init__(self, id: str, secret: str, callback: Callable, host="https://imeritapi.ango.ai", concurrency=1):
        super().__init__(id, secret, callback)
        self.host = host
        self.concurrency = concurrency
        self.queue = queue.Queue()

    def work(self):
        while True:
            data = self.queue.get()
            data["batches"] = data.get('batches', [])
            api_key = data.get('apiKey')
            task_id = data.get('taskId')
            overwrite = data.get('overwrite', True)
            sdk = SDK(api_key=api_key, host=self.host)
            payload = self._callback(data, sdk)
            # Hint SDK about project id so it can upload brush arrays if provided
            try:
                setattr(payload, 'project_id', data.get('projectId'))
            except Exception:
                pass
            sdk._annotate_task(task_id, payload, overwrite, send_to_next_stage=True, is_plugin=True)

    def on_plugin(self, data):
        workflow = data.get('workflow')
        data["logger"] = self._get_logger(data)
        data["batches"] = data.get('batches', [])
        if not workflow:
            overwrite = data.get('overwrite', True)
            api_key = data.get('apiKey')
            sdk = SDK(api_key=api_key, host=self.host)
            payload = self._callback(data)
            if not overwrite:
                task_id = data.get('taskId')
                existing = sdk.get_task(task_id).get("data").get("task").get("answer")
                payload.answer = merge_annotations(existing, payload.answer)
            # Also attach project id for potential brush handling by consumers
            try:
                setattr(payload, 'project_id', data.get('projectId'))
            except Exception:
                pass
            response = {
                "response": payload.answer.toDict(),
                "session": data.get("session", "")
            }
            if CONNECTOR != "WS":
                return response
            if response.get("response", None) is not None:
                self.emit('response', response)
        else:
            self.queue.put(data)

    def start(self, background=False):
        if background:
            # Schedule the tasks without waiting for completion
            self.loop.run_in_executor(None, self.work)
        else:
            tasks = [self.work() for _ in range(self.concurrency)]
            future = asyncio.gather(*tasks)
            self.loop.run_until_complete(future)


class FileExplorerPlugin(BasePlugin):
    pass

class BatchModelPlugin(BasePlugin):
    pass

class InputPlugin(BasePlugin):
    def on_plugin(self, data):
        data["logger"] = self._get_logger(data)
        data["batches"] = data.get('batches', [])
        file_explorer_options = data.get('fileExplorerOptions', [])

        response = {
            "response": self._callback(data),
            "session": data.get("session", "")
        }
        if CONNECTOR != "WS":
            return response
        if response.get("response", None) is not None:
            self.emit('response', response)

class MarkdownPlugin(BasePlugin):
    pass

def connect_rest(plugin):
    import uvicorn
    app = FastAPI()

    def get_authorization_info(Secret: str = Header(None)):
        if Secret != plugin.secret:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return True

    @app.post("/plugin")
    def plugin_query(payload: Dict[Any, Any], auth=Depends(get_authorization_info)):
        return plugin.on_plugin(payload)

    @app.get("/heartbeat")
    def heartbeat(auth=Depends(get_authorization_info)):
        return "ok"

    if CONNECTOR == "REST":
        uvicorn.run(app, host="0.0.0.0", port=PORT)
    else:
        raise Exception("Expecting CONNECTOR Environment variable")

def _connect_ws(plugin, host):
    try:
        sio = socketio.Client(logger=logging.getLogger("plugin"), reconnection=False)
        sio.register_namespace(plugin)
        sio.connect(host, namespaces=["/plugin"], transports=["websocket"], wait=True)
    except Exception as e:
        logging.getLogger().critical(e)
        os._exit(1)

def run(plugin, host="https://eu-api.ango.ai"):
    try:
        if CONNECTOR == "WS":
            _connect_ws(plugin, host)
            plugin.start()
        else:
            plugin.start(background=True)
            connect_rest(plugin)
    except (KeyboardInterrupt, SystemExit):
        logging.getLogger().warning("Plugin Stopped")
        os._exit(1)

