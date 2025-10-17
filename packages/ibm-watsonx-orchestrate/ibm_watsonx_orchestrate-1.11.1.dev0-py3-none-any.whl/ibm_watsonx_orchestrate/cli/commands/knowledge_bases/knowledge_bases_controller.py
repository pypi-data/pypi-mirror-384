import sys
import json
import rich
import requests
import logging
import importlib
import inspect
from pathlib import Path
from typing import List

from ibm_watsonx_orchestrate.agent_builder.knowledge_bases.knowledge_base import KnowledgeBase
from ibm_watsonx_orchestrate.client.knowledge_bases.knowledge_base_client import KnowledgeBaseClient
from ibm_watsonx_orchestrate.client.base_api_client import ClientAPIException
from ibm_watsonx_orchestrate.client.connections import get_connections_client
from ibm_watsonx_orchestrate.client.utils import instantiate_client
from ibm_watsonx_orchestrate.agent_builder.knowledge_bases.types import FileUpload

logger = logging.getLogger(__name__)

def import_python_knowledge_base(file: str) -> List[KnowledgeBase]:
    file_path = Path(file)
    file_directory = file_path.parent
    file_name = file_path.stem
    sys.path.append(str(file_directory))
    module = importlib.import_module(file_name)
    del sys.path[-1]

    knowledge_bases = []
    for _, obj in inspect.getmembers(module):
        if isinstance(obj, KnowledgeBase):
            knowledge_bases.append(obj)
    return knowledge_bases

def parse_file(file: str) -> List[KnowledgeBase]:
    if file.endswith('.yaml') or file.endswith('.yml') or file.endswith(".json"):
        knowledge_base = KnowledgeBase.from_spec(file=file)
        return [knowledge_base]
    elif file.endswith('.py'):
        knowledge_bases = import_python_knowledge_base(file)
        return knowledge_bases
    else:
        raise ValueError("file must end in .json, .yaml, .yml or .py")

def to_column_name(col: str):
    return " ".join([word.capitalize() if not word[0].isupper() else word for word in col.split("_")])

def get_file_name(file: str | FileUpload):
    path = file.path if isinstance(file, FileUpload) else file
    # This name prettifying currently screws up file type detection on ingestion
    # return to_column_name(path.split("/")[-1].split(".")[0]) 
    return path.split("/")[-1]

def get_relative_file_path(path, dir):
    if path.startswith("/"):
        return path
    elif path.startswith("./"):
        return f"{dir}{path.removeprefix('.')}"
    else:
        return f"{dir}/{path}"
    
def build_file_object(file_dir: str, file: str | FileUpload):
    if isinstance(file, FileUpload):
        return ('files', (get_file_name(file.path), open(get_relative_file_path(file.path, file_dir), 'rb')))
    return ('files', (get_file_name(file), open(get_relative_file_path(file, file_dir), 'rb')))

class KnowledgeBaseController:
    def __init__(self):
        self.client = None
        self.connections_client = None

    def get_client(self):
        if not self.client:
            self.client = instantiate_client(KnowledgeBaseClient)
        return self.client
    
    def import_knowledge_base(self, file: str, app_id: str):
        client = self.get_client()

        knowledge_bases = parse_file(file=file)
        
        if app_id:
            connections_client = get_connections_client()
            connection_id = None
                
            connections = connections_client.get_draft_by_app_id(app_id=app_id)
            if not connections:
                logger.error(f"No connection exists with the app-id '{app_id}'")
                exit(1)

            connection_id = connections.connection_id

            for kb in knowledge_bases:
                if kb.conversational_search_tool and kb.conversational_search_tool.index_config and len(kb.conversational_search_tool.index_config) > 0:
                    kb.conversational_search_tool.index_config[0].connection_id = connection_id
        
        existing_knowledge_bases = client.get_by_names([kb.name for kb in knowledge_bases])
        
        for kb in knowledge_bases:
            try:
                file_dir = "/".join(file.split("/")[:-1])

                existing = list(filter(lambda ex: ex.get('name') == kb.name, existing_knowledge_bases))
                if len(existing) > 0:
                    logger.info(f"Existing knowledge base '{kb.name}' found. Updating...")
                    self.update_knowledge_base(existing[0].get("id"), kb=kb, file_dir=file_dir)
                    continue

                kb.validate_documents_or_index_exists()
                if kb.documents:
                    files = [build_file_object(file_dir, file) for file in kb.documents]
                    file_urls = { get_file_name(file): file.url for file in kb.documents if isinstance(file, FileUpload) and file.url }
                    
                    kb.prioritize_built_in_index = True
                    payload = kb.model_dump(exclude_none=True);
                    payload.pop('documents');

                    data = {
                        'knowledge_base': json.dumps(payload),
                        'file_urls': json.dumps(file_urls)
                    }

                    client.create_built_in(payload=data, files=files)
                else:
                    if len(kb.conversational_search_tool.index_config) != 1:
                        raise ValueError(f"Must provide exactly one conversational_search_tool.index_config. Provided {len(kb.conversational_search_tool.index_config)}.")
                    
                    if (kb.conversational_search_tool.index_config[0].milvus or \
                        kb.conversational_search_tool.index_config[0].elastic_search) and \
                            not kb.conversational_search_tool.index_config[0].connection_id:
                        raise ValueError(f"Must provide credentials (via --app-id) when using milvus or elastic_search.")

                    kb.prioritize_built_in_index = False
                    data = { 'knowledge_base': json.dumps(kb.model_dump(exclude_none=True)) }

                    client.create(payload=data)
                
                logger.info(f"Successfully imported knowledge base '{kb.name}'")
            except ClientAPIException as e:
                logger.error(f"Error importing knowledge base '{kb.name}\n' {e.response.text}")
    
    def get_id(
        self, id: str, name: str
    ) -> str:
        if id:
            return id
        
        if not name:
            logger.error("Either 'id' or 'name' is required")
            sys.exit(1)

        response = self.get_client().get_by_name(name)

        if not response:
            logger.warning(f"No knowledge base '{name}' found")
            sys.exit(1)

        return response.get('id')


    def update_knowledge_base(
        self, knowledge_base_id: str, kb: KnowledgeBase, file_dir: str
    ) -> None:        
        if kb.documents:
            status = self.get_client().status(knowledge_base_id)
            existing_docs = [doc.get("metadata", {}).get("original_file_name", "") for doc in status.get("documents", [])]
            
            removed_docs = existing_docs[:]
            for file in kb.documents:
                filename = get_file_name(file)

                if filename in existing_docs:
                    logger.warning(f'Document \"{filename}\" already exists in knowledge base. Updating...')
                    removed_docs.remove(filename)

            for filename in removed_docs:
                logger.warning(f'Document \"{filename}\" removed from knowledge base.')


            files = [build_file_object(file_dir, file) for file in kb.documents]
            file_urls = { get_file_name(file): file.url for file in kb.documents if isinstance(file, FileUpload) and file.url }
            
            kb.prioritize_built_in_index = True
            payload = kb.model_dump(exclude_none=True);
            payload.pop('documents');

            data = {
                'knowledge_base': json.dumps(payload),
                'file_urls': json.dumps(file_urls)
            }

            self.get_client().update_with_documents(knowledge_base_id, payload=data, files=files)
        else:
            if kb.conversational_search_tool and kb.conversational_search_tool.index_config:
                kb.prioritize_built_in_index = False

            data = { 'knowledge_base': json.dumps(kb.model_dump(exclude_none=True)) }
            self.get_client().update(knowledge_base_id, payload=data)

        logger.info(f"Knowledge base '{kb.name}' updated successfully")


    def knowledge_base_status( self, id: str, name: str) -> None:
        knowledge_base_id = self.get_id(id, name)
        response = self.get_client().status(knowledge_base_id)

        if 'documents' in response:
            response[f"documents ({len(response['documents'])})"] = ", ".join([str(doc.get('metadata', {}).get('original_file_name', '<Unnamed File>')) for doc in response['documents']])
            response.pop('documents')

        table = rich.table.Table(
            show_header=True, 
            header_style="bold white", 
            show_lines=True
        )

        if "id" in response:
            kbID = response["id"]
            del response["id"]

            response["id"] = kbID
        
        [table.add_column(to_column_name(col), {}) for col in response.keys()]
        table.add_row(*[str(val) for val in response.values()])
        
        rich.print(table)


    def list_knowledge_bases(self, verbose: bool=False):
        response = self.get_client().get()
        knowledge_bases = [KnowledgeBase.model_validate(knowledge_base) for knowledge_base in response]

        knowledge_base_list = []
        if verbose:
            for kb in knowledge_bases:
                knowledge_base_list.append(json.loads(kb.model_dump_json(exclude_none=True)))
            rich.print(rich.json.JSON(json.dumps(knowledge_base_list, indent=4)))
        else:
            table = rich.table.Table(
                show_header=True, 
                header_style="bold white", 
                show_lines=True
            )

            column_args = {
                "Name": {"overflow": "fold"},
                "Description": {},
                "App ID": {},
                "ID": {"overflow": "fold"}
            }
            
            for column in column_args:
                table.add_column(column, **column_args[column])
            
            for kb in knowledge_bases:
                app_id = ""
                
                if kb.conversational_search_tool is not None \
                   and kb.conversational_search_tool.index_config is not None \
                   and len(kb.conversational_search_tool.index_config) > 0 \
                   and kb.conversational_search_tool.index_config[0].connection_id is not None:
                    connections_client = get_connections_client()
                    app_id = str(connections_client.get_draft_by_id(kb.conversational_search_tool.index_config[0].connection_id))

                table.add_row(
                    kb.name,
                    kb.description,
                    app_id,
                    str(kb.id)
                )

            rich.print(table)
        

    def remove_knowledge_base(self, id: str, name: str):
        knowledge_base_id = self.get_id(id, name)      
        logEnding = f"with ID '{id}'" if id else f"'{name}'"

        try:
            self.get_client().delete(knowledge_base_id=knowledge_base_id)
            logger.info(f"Successfully removed knowledge base {logEnding}")
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"No knowledge base {logEnding} found")
            logger.error(e.response.text)
            exit(1)

