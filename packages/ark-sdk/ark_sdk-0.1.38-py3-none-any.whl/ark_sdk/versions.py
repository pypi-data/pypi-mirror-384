#!/usr/bin/env python3
"""
Generated ARK Kubernetes Client Classes

This module provides typed client classes for interacting with ARK custom resources.
Auto-generated from OpenAPI schema - do not edit manually.
"""

import os
import functools
import logging
import asyncio
from typing import List, Optional, Dict, Any, TypeVar, Generic, Type
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from ark_sdk.k8s import get_context
import yaml
import json

T = TypeVar('T')

# Configure logger
logger = logging.getLogger(__name__)

def async_compat(async_method):
    """Decorator that makes async methods work in both sync and async contexts"""
    @functools.wraps(async_method)
    def wrapper(*args, **kwargs):
        try:
            # Check if we're in an async context
            loop = asyncio.get_running_loop()
            # Return the coroutine for the caller to await
            return async_method(*args, **kwargs)
        except RuntimeError:
            # No event loop, run it synchronously
            return asyncio.run(async_method(*args, **kwargs))
    return wrapper

@functools.lru_cache(maxsize=1)
def init_k8s():
    # Initialize Kubernetes client
    try:
        config.load_incluster_config()
        logger.info("Loaded in-cluster Kubernetes configuration")
    except (config.ConfigException, Exception) as e:
        logger.warning(f"Failed to load in-cluster config: {e}. Falling back to kubeconfig")
        try:
            config.load_kube_config()
            logger.info("Loaded Kubernetes configuration from kubeconfig")
        except (config.ConfigException, Exception) as e:
            logger.error(f"Failed to load Kubernetes configuration: {e}")
            raise

class ARKResourceClient(Generic[T]):
    """Generic client for ARK custom resources"""
    
    def __init__(
        self,
        api_version: str,
        kind: str,
        plural: str,
        model_class: Type[T],
        namespace: str = "default"
    ):
        self.api_version = api_version
        self.kind = kind
        self.plural = plural
        self.model_class = model_class
        self.namespace = namespace
        self.group, self.version = api_version.split('/')
       
        init_k8s()

        self.api_client = client.ApiClient()
        self.custom_api = client.CustomObjectsApi(self.api_client)
    
    def create(self, resource: T, namespace: Optional[str] = None) -> T:
        """Create a new resource"""
        ns = namespace or self.namespace
        
        # Convert the typed model to dict
        body = self._model_to_dict(resource)
        
        # Ensure required fields are set
        body['apiVersion'] = self.api_version
        body['kind'] = self.kind
        
        try:
            result = self.custom_api.create_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=ns,
                plural=self.plural,
                body=body
            )
            return self._dict_to_model(result)
        except ApiException as e:
            raise Exception(f"Failed to create {self.kind}: {e}")
    
    def get(self, name: str, namespace: Optional[str] = None) -> T:
        """Get a resource by name"""
        ns = namespace or self.namespace
        
        try:
            result = self.custom_api.get_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=ns,
                plural=self.plural,
                name=name
            )
            return self._dict_to_model(result)
        except ApiException as e:
            if e.status == 404:
                raise Exception(f"{self.kind} '{name}' not found in namespace '{ns}'")
            raise Exception(f"Failed to get {self.kind}: {e}")
    
    def list(self, namespace: Optional[str] = None, label_selector: Optional[str] = None) -> List[T]:
        """List all resources"""
        ns = namespace or self.namespace
        
        try:
            kwargs = {}
            if label_selector:
                kwargs['label_selector'] = label_selector
            
            result = self.custom_api.list_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=ns,
                plural=self.plural,
                **kwargs
            )
            
            items = result.get('items', [])
            return [self._dict_to_model(item) for item in items]
        except ApiException as e:
            raise Exception(f"Failed to list {self.kind}s: {e}")
    
    def update(self, resource: T, namespace: Optional[str] = None) -> T:
        """Update an existing resource"""
        ns = namespace or self.namespace
        
        # Convert the typed model to dict
        body = self._model_to_dict(resource)
        
        # Ensure required fields are set
        body['apiVersion'] = self.api_version
        body['kind'] = self.kind
        
        # Extract name from metadata
        name = body.get('metadata', {}).get('name')
        if not name:
            raise ValueError("Resource must have metadata.name for update")
        
        try:
            result = self.custom_api.replace_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=ns,
                plural=self.plural,
                name=name,
                body=body
            )
            return self._dict_to_model(result)
        except ApiException as e:
            raise Exception(f"Failed to update {self.kind}: {e}")
    
    def patch(self, name: str, patch_data: Dict[str, Any], namespace: Optional[str] = None) -> T:
        """Patch a resource"""
        ns = namespace or self.namespace
        
        try:
            result = self.custom_api.patch_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=ns,
                plural=self.plural,
                name=name,
                body=patch_data
            )
            return self._dict_to_model(result)
        except ApiException as e:
            raise Exception(f"Failed to patch {self.kind}: {e}")
    
    def delete(self, name: str, namespace: Optional[str] = None) -> None:
        """Delete a resource"""
        ns = namespace or self.namespace
        
        try:
            self.custom_api.delete_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=ns,
                plural=self.plural,
                name=name
            )
        except ApiException as e:
            if e.status == 404:
                raise Exception(f"{self.kind} '{name}' not found in namespace '{ns}'")
            raise Exception(f"Failed to delete {self.kind}: {e}")
    
    def _model_to_dict(self, model: T) -> Dict[str, Any]:
        """Convert a typed model to a dictionary"""
        if hasattr(model, 'model_dump'):
            # Pydantic v2
            return model.model_dump(by_alias=True, exclude_unset=True)
        elif hasattr(model, 'dict'):
            # Pydantic v1
            return model.dict(by_alias=True, exclude_unset=True)
        else:
            raise ValueError(f"Cannot convert {type(model)} to dict")
    
    def _dict_to_model(self, data: Dict[str, Any]) -> T:
        """Convert a dictionary to a typed model"""
        return self.model_class(**data)
    
    # Async versions of all public methods
    @async_compat
    async def a_create(self, resource: T, namespace: Optional[str] = None) -> T:
        """Async version of create - works in both sync and async contexts"""
        return await asyncio.to_thread(self.create, resource, namespace)
    
    @async_compat
    async def a_get(self, name: str, namespace: Optional[str] = None) -> T:
        """Async version of get - works in both sync and async contexts"""
        return await asyncio.to_thread(self.get, name, namespace)
    
    @async_compat
    async def a_list(self, namespace: Optional[str] = None, label_selector: Optional[str] = None) -> List[T]:
        """Async version of list - works in both sync and async contexts"""
        return await asyncio.to_thread(self.list, namespace, label_selector)
    
    @async_compat
    async def a_update(self, resource: T, namespace: Optional[str] = None) -> T:
        """Async version of update - works in both sync and async contexts"""
        return await asyncio.to_thread(self.update, resource, namespace)
    
    @async_compat
    async def a_patch(self, name: str, patch_data: Dict[str, Any], namespace: Optional[str] = None) -> T:
        """Async version of patch - works in both sync and async contexts"""
        return await asyncio.to_thread(self.patch, name, patch_data, namespace)
    
    @async_compat
    async def a_delete(self, name: str, namespace: Optional[str] = None) -> None:
        """Async version of delete - works in both sync and async contexts"""
        return await asyncio.to_thread(self.delete, name, namespace)


class _ARKClient:
    """Base ARK client class"""

    def __init__(self, namespace: Optional[str] = None):
        if namespace is None:
            namespace = get_context()["namespace"]
        self.namespace = namespace

from .models.agent_v1alpha1 import AgentV1alpha1
from .models.evaluation_v1alpha1 import EvaluationV1alpha1
from .models.evaluator_v1alpha1 import EvaluatorV1alpha1
from .models.mcp_server_v1alpha1 import MCPServerV1alpha1
from .models.memory_v1alpha1 import MemoryV1alpha1
from .models.model_v1alpha1 import ModelV1alpha1
from .models.query_v1alpha1 import QueryV1alpha1
from .models.team_v1alpha1 import TeamV1alpha1
from .models.tool_v1alpha1 import ToolV1alpha1


class ARKClientV1alpha1(_ARKClient):
    """ARK client for API version ark.mckinsey.com/v1alpha1"""

    def __init__(self, namespace: Optional[str] = None):
        super().__init__(namespace)
        
        self.agents = ARKResourceClient(
            api_version="ark.mckinsey.com/v1alpha1",
            kind="Agent",
            plural="agents",
            model_class=AgentV1alpha1,
            namespace=namespace
        )

        self.evaluations = ARKResourceClient(
            api_version="ark.mckinsey.com/v1alpha1",
            kind="Evaluation",
            plural="evaluations",
            model_class=EvaluationV1alpha1,
            namespace=namespace
        )

        self.evaluators = ARKResourceClient(
            api_version="ark.mckinsey.com/v1alpha1",
            kind="Evaluator",
            plural="evaluators",
            model_class=EvaluatorV1alpha1,
            namespace=namespace
        )

        self.mcpservers = ARKResourceClient(
            api_version="ark.mckinsey.com/v1alpha1",
            kind="MCPServer",
            plural="mcpservers",
            model_class=MCPServerV1alpha1,
            namespace=namespace
        )

        self.memories = ARKResourceClient(
            api_version="ark.mckinsey.com/v1alpha1",
            kind="Memory",
            plural="memories",
            model_class=MemoryV1alpha1,
            namespace=namespace
        )

        self.models = ARKResourceClient(
            api_version="ark.mckinsey.com/v1alpha1",
            kind="Model",
            plural="models",
            model_class=ModelV1alpha1,
            namespace=namespace
        )

        self.queries = ARKResourceClient(
            api_version="ark.mckinsey.com/v1alpha1",
            kind="Query",
            plural="queries",
            model_class=QueryV1alpha1,
            namespace=namespace
        )

        self.teams = ARKResourceClient(
            api_version="ark.mckinsey.com/v1alpha1",
            kind="Team",
            plural="teams",
            model_class=TeamV1alpha1,
            namespace=namespace
        )

        self.tools = ARKResourceClient(
            api_version="ark.mckinsey.com/v1alpha1",
            kind="Tool",
            plural="tools",
            model_class=ToolV1alpha1,
            namespace=namespace
        )
        
        # Add secret client
        from .k8s import SecretClient
        self.secrets = SecretClient(namespace)


from .models.a2_a_server_v1prealpha1 import A2AServerV1prealpha1
from .models.execution_engine_v1prealpha1 import ExecutionEngineV1prealpha1


class ARKClientV1prealpha1(_ARKClient):
    """ARK client for API version ark.mckinsey.com/v1prealpha1"""

    def __init__(self, namespace: Optional[str] = None):
        super().__init__(namespace)
        
        self.a2aservers = ARKResourceClient(
            api_version="ark.mckinsey.com/v1prealpha1",
            kind="A2AServer",
            plural="a2aservers",
            model_class=A2AServerV1prealpha1,
            namespace=namespace
        )

        self.executionengines = ARKResourceClient(
            api_version="ark.mckinsey.com/v1prealpha1",
            kind="ExecutionEngine",
            plural="executionengines",
            model_class=ExecutionEngineV1prealpha1,
            namespace=namespace
        )
        
        # Add secret client
        from .k8s import SecretClient
        self.secrets = SecretClient(namespace)
