"""
Manifest and metadata utilities for handling nexa.manifest files and model metadata.

This module provides utilities to:
- Load and save nexa.manifest files
- Create GGUF and MLX manifests
- Process manifest metadata (handle null fields, fetch avatars, etc.)
- Manage backward compatibility with old download_metadata.json files
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from .quantization_utils import (
    extract_quantization_from_filename, 
    detect_quantization_for_mlx
)
from .model_types import (
    PIPELINE_TO_MODEL_TYPE,
    MODEL_TYPE_TO_PIPELINE
)

MODEL_FILE_TYPE_TO_PLUGIN_ID_MAPPING = {
    'npu': 'npu',
    'mlx': 'mlx',
    'gguf': 'llama_cpp'
}

def process_manifest_metadata(manifest: Dict[str, Any], repo_id: str) -> Dict[str, Any]:
    """Process manifest metadata to handle null/missing fields."""
    # Handle pipeline_tag
    pipeline_tag = manifest.get('pipeline_tag')
    if not pipeline_tag:
        # Reverse map from ModelType if available
        model_type = manifest.get('ModelType')
        pipeline_tag = MODEL_TYPE_TO_PIPELINE.get(model_type) if model_type else None
    
    # Handle download_time - keep as null if missing
    download_time = manifest.get('download_time')
    
    # Handle avatar_url - leave it null if missing/null
    avatar_url = manifest.get('avatar_url')
    
    # Return processed metadata
    processed_manifest = manifest.copy()
    processed_manifest.update({
        'pipeline_tag': pipeline_tag,
        'download_time': download_time,
        'avatar_url': avatar_url
    })
    
    return processed_manifest


def load_nexa_manifest(directory_path: str) -> Dict[str, Any]:
    """Load manifest from nexa.manifest if it exists."""
    manifest_path = os.path.join(directory_path, 'nexa.manifest')
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def load_download_metadata(directory_path: str, repo_id: Optional[str] = None) -> Dict[str, Any]:
    """Load download metadata from nexa.manifest if it exists, fallback to old format."""
    # First try to load from new manifest format
    manifest = load_nexa_manifest(directory_path)
    if manifest and repo_id:
        # Process the manifest to handle null/missing fields
        return process_manifest_metadata(manifest, repo_id)
    elif manifest:
        # Return manifest as-is if no repo_id provided (for backward compatibility)
        return manifest
    
    # Fallback to old format for backward compatibility
    old_metadata_path = os.path.join(directory_path, 'download_metadata.json')
    if os.path.exists(old_metadata_path):
        try:
            with open(old_metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_download_metadata(directory_path: str, metadata: Dict[str, Any]) -> None:
    """Save download metadata to nexa.manifest in the new format."""
    manifest_path = os.path.join(directory_path, 'nexa.manifest')
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
    except IOError:
        # If we can't save metadata, don't fail the download
        pass


def _get_plugin_id_from_model_file_type(model_file_type: Optional[str], default: str = "llama_cpp") -> str:
    """Map model file type to PluginId."""
    return MODEL_FILE_TYPE_TO_PLUGIN_ID_MAPPING.get(model_file_type, default)


def create_gguf_manifest(repo_id: str, files: List[str], directory_path: str, old_metadata: Dict[str, Any], is_mmproj: bool = False, file_name: Optional[Union[str, List[str]]] = None, **kwargs) -> Dict[str, Any]:
    """Create GGUF format manifest."""
    
    # Load existing manifest to merge GGUF files if it exists
    existing_manifest = load_nexa_manifest(directory_path)
    
    # Check if there's a downloaded nexa.manifest from the repo
    downloaded_manifest = old_metadata.get('downloaded_manifest', {})
    
    model_files = {}
    if existing_manifest and "ModelFile" in existing_manifest:
        model_files = existing_manifest["ModelFile"].copy()
    
    # Initialize MMProjFile from existing manifest or empty
    mmproj_file = {
        "Name": "",
        "Downloaded": False,
        "Size": 0
    }
    if existing_manifest and "MMProjFile" in existing_manifest:
        mmproj_file = existing_manifest["MMProjFile"].copy()
    
    # Process GGUF files
    for current_file_name in files:
        if current_file_name.endswith('.gguf'):
            # Check if this file is an mmproj file
            is_current_mmproj = 'mmproj' in current_file_name.lower()
            
            # If we're downloading specific files and this is marked as mmproj, respect that
            if is_mmproj and file_name is not None:
                filenames_to_check = file_name if isinstance(file_name, list) else [file_name]
                is_current_mmproj = current_file_name in filenames_to_check
            
            file_path = os.path.join(directory_path, current_file_name)
            file_size = 0
            if os.path.exists(file_path):
                try:
                    file_size = os.path.getsize(file_path)
                except (OSError, IOError):
                    pass
            
            if is_current_mmproj:
                # This is an mmproj file, put it in MMProjFile
                mmproj_file = {
                    "Name": current_file_name,
                    "Downloaded": True,
                    "Size": file_size
                }
            else:
                # Regular model file, put in ModelFile
                # Use the new enum-based quantization extraction
                quantization_type = extract_quantization_from_filename(current_file_name)
                quant_level = quantization_type.value if quantization_type else "UNKNOWN"

                # FIXME: hardcode to handle the multiple mmproj files problem
                if quant_level == "UNKNOWN" and "mmproj" in current_file_name.lower():
                    pass
                else:
                    model_files[quant_level] = {
                        "Name": current_file_name,
                        "Downloaded": True,
                        "Size": file_size
                    }
    
    # Determine PluginId with priority: kwargs > downloaded_manifest > model_file_type > default
    plugin_id = kwargs.get('plugin_id')
    if not plugin_id:
        model_file_type = old_metadata.get('model_file_type')
        if downloaded_manifest.get('PluginId'):
            plugin_id = downloaded_manifest.get('PluginId')
        elif model_file_type:
            plugin_id = _get_plugin_id_from_model_file_type(model_file_type)
        else:
            plugin_id = "llama_cpp"
    
    # Determine ModelType with priority: kwargs > downloaded_manifest > pipeline_tag mapping
    model_type = kwargs.get('model_type')
    if not model_type:
        if downloaded_manifest.get('ModelType'):
            model_type = downloaded_manifest.get('ModelType')
        else:
            model_type = PIPELINE_TO_MODEL_TYPE.get(old_metadata.get('pipeline_tag'), "other")
    
    # Determine ModelName with priority: kwargs > downloaded_manifest > empty string
    model_name = kwargs.get('model_name')
    if not model_name:
        model_name = downloaded_manifest.get('ModelName', '')
    
    # Get DeviceId and MinSDKVersion from kwargs or default to empty string
    device_id = kwargs.get('device_id', '')
    min_sdk_version = kwargs.get('min_sdk_version', '')
    
    manifest = {
        "Name": repo_id,
        "ModelName": model_name,
        "ModelType": model_type,
        "PluginId": plugin_id,
        "DeviceId": device_id,
        "MinSDKVersion": min_sdk_version,
        "ModelFile": model_files,
        "MMProjFile": mmproj_file,
        "TokenizerFile": {
            "Name": "",
            "Downloaded": False,
            "Size": 0
        },
        "ExtraFiles": None,
        # Preserve old metadata fields
        "pipeline_tag": old_metadata.get('pipeline_tag') if old_metadata.get('pipeline_tag') else existing_manifest.get('pipeline_tag'),
        "download_time": old_metadata.get('download_time') if old_metadata.get('download_time') else existing_manifest.get('download_time'),
        "avatar_url": old_metadata.get('avatar_url') if old_metadata.get('avatar_url') else existing_manifest.get('avatar_url')
    }
    
    return manifest


def create_mlx_manifest(repo_id: str, files: List[str], directory_path: str, old_metadata: Dict[str, Any], is_mmproj: bool = False, file_name: Optional[Union[str, List[str]]] = None, **kwargs) -> Dict[str, Any]:
    """Create MLX format manifest."""
    
    # Load existing manifest to merge MLX files if it exists
    existing_manifest = load_nexa_manifest(directory_path)
    
    # Check if there's a downloaded nexa.manifest from the repo
    downloaded_manifest = old_metadata.get('downloaded_manifest', {})
    
    model_files = {}
    extra_files = []
    
    # Initialize MMProjFile
    mmproj_file = {
        "Name": "",
        "Downloaded": False,
        "Size": 0
    }
    
    # Try different methods to extract quantization for MLX models
    quantization_type = detect_quantization_for_mlx(repo_id, directory_path)
    
    # Use the detected quantization or default to "DEFAULT"
    quant_level = quantization_type.value if quantization_type else "DEFAULT"
    
    for current_file_name in files:
        file_path = os.path.join(directory_path, current_file_name)
        file_size = 0
        if os.path.exists(file_path):
            try:
                file_size = os.path.getsize(file_path)
            except (OSError, IOError):
                pass
        
        # Check if this file is an mmproj file
        is_current_mmproj = 'mmproj' in current_file_name.lower()
        
        # If we're downloading specific files and this is marked as mmproj, respect that
        if is_mmproj and file_name is not None:
            filenames_to_check = file_name if isinstance(file_name, list) else [file_name]
            is_current_mmproj = current_file_name in filenames_to_check
        
        if is_current_mmproj:
            # This is an mmproj file, put it in MMProjFile
            mmproj_file = {
                "Name": current_file_name,
                "Downloaded": True,
                "Size": file_size
            }
        # Check if this is a main model file (safetensors but not index files)
        elif (current_file_name.endswith('.safetensors') and not current_file_name.endswith('.index.json')):
            model_files[quant_level] = {
                "Name": current_file_name,
                "Downloaded": True,
                "Size": file_size
            }
        else:
            # Add to extra files
            extra_files.append({
                "Name": current_file_name,
                "Downloaded": True,
                "Size": file_size
            })
    
    # Determine PluginId with priority: kwargs > downloaded_manifest > model_file_type > default
    plugin_id = kwargs.get('plugin_id')
    if not plugin_id:
        model_file_type = old_metadata.get('model_file_type')
        if downloaded_manifest.get('PluginId'):
            plugin_id = downloaded_manifest.get('PluginId')
        elif model_file_type:
            plugin_id = _get_plugin_id_from_model_file_type(model_file_type)
        else:
            plugin_id = "mlx"
    
    # Determine ModelType with priority: kwargs > downloaded_manifest > pipeline_tag mapping
    model_type = kwargs.get('model_type')
    if not model_type:
        if downloaded_manifest.get('ModelType'):
            model_type = downloaded_manifest.get('ModelType')
        else:
            model_type = PIPELINE_TO_MODEL_TYPE.get(old_metadata.get('pipeline_tag'), "other")
    
    # Determine ModelName with priority: kwargs > downloaded_manifest > empty string
    model_name = kwargs.get('model_name')
    if not model_name:
        model_name = downloaded_manifest.get('ModelName', '')
    
    # Get DeviceId and MinSDKVersion from kwargs or default to empty string
    device_id = kwargs.get('device_id', '')
    min_sdk_version = kwargs.get('min_sdk_version', '')
    
    manifest = {
        "Name": repo_id,
        "ModelName": model_name,
        "ModelType": model_type,
        "PluginId": plugin_id,
        "DeviceId": device_id,
        "MinSDKVersion": min_sdk_version,
        "ModelFile": model_files,
        "MMProjFile": mmproj_file,
        "TokenizerFile": {
            "Name": "",
            "Downloaded": False,
            "Size": 0
        },
        "ExtraFiles": extra_files if extra_files else None,
        # Preserve old metadata fields
        "pipeline_tag": old_metadata.get('pipeline_tag') if old_metadata.get('pipeline_tag') else existing_manifest.get('pipeline_tag'),
        "download_time": old_metadata.get('download_time') if old_metadata.get('download_time') else existing_manifest.get('download_time'),
        "avatar_url": old_metadata.get('avatar_url') if old_metadata.get('avatar_url') else existing_manifest.get('avatar_url')
    }
    
    return manifest


def create_npu_manifest(repo_id: str, files: List[str], directory_path: str, old_metadata: Dict[str, Any], is_mmproj: bool = False, file_name: Optional[Union[str, List[str]]] = None, **kwargs) -> Dict[str, Any]:
    """Create NPU format manifest."""
    
    # Load existing manifest to merge NPU files if it exists
    existing_manifest = load_nexa_manifest(directory_path)
    
    # Check if there's a downloaded nexa.manifest from the repo
    downloaded_manifest = old_metadata.get('downloaded_manifest', {})
    
    model_files = {}
    extra_files = []
    
    # Initialize MMProjFile
    mmproj_file = {
        "Name": "",
        "Downloaded": False,
        "Size": 0
    }
    
    for current_file_name in files:
        file_path = os.path.join(directory_path, current_file_name)
        file_size = 0
        if os.path.exists(file_path):
            try:
                file_size = os.path.getsize(file_path)
            except (OSError, IOError):
                pass
        
        # Check if this file is an mmproj file
        is_current_mmproj = 'mmproj' in current_file_name.lower()
        
        # If we're downloading specific files and this is marked as mmproj, respect that
        if is_mmproj and file_name is not None:
            filenames_to_check = file_name if isinstance(file_name, list) else [file_name]
            is_current_mmproj = current_file_name in filenames_to_check
        
        if is_current_mmproj:
            # This is an mmproj file, put it in MMProjFile
            mmproj_file = {
                "Name": current_file_name,
                "Downloaded": True,
                "Size": file_size
            }
        else:
            # For NPU, all non-mmproj files go to extra_files
            extra_files.append({
                "Name": current_file_name,
                "Downloaded": True,
                "Size": file_size
            })
    
    # Pick the first file from extra_files and add it to ModelFile with key "N/A"
    if extra_files:
        first_file = extra_files[0]
        model_files["N/A"] = {
            "Name": first_file["Name"],
            "Downloaded": first_file["Downloaded"],
            "Size": first_file["Size"]
        }
    
    # Determine PluginId with priority: kwargs > downloaded_manifest > model_file_type > default
    plugin_id = kwargs.get('plugin_id')
    if not plugin_id:
        model_file_type = old_metadata.get('model_file_type')
        if downloaded_manifest.get('PluginId'):
            plugin_id = downloaded_manifest.get('PluginId')
        elif model_file_type:
            plugin_id = _get_plugin_id_from_model_file_type(model_file_type)
        else:
            plugin_id = "npu"
    
    # Determine ModelType with priority: kwargs > downloaded_manifest > pipeline_tag mapping
    model_type = kwargs.get('model_type')
    if not model_type:
        if downloaded_manifest.get('ModelType'):
            model_type = downloaded_manifest.get('ModelType')
        else:
            model_type = PIPELINE_TO_MODEL_TYPE.get(old_metadata.get('pipeline_tag'), "other")
    
    # Determine ModelName with priority: kwargs > downloaded_manifest > empty string
    model_name = kwargs.get('model_name')
    if not model_name:
        model_name = downloaded_manifest.get('ModelName', '')
    
    # Get DeviceId and MinSDKVersion from kwargs or default to empty string
    device_id = kwargs.get('device_id', '')
    min_sdk_version = kwargs.get('min_sdk_version', '')
    
    manifest = {
        "Name": repo_id,
        "ModelName": model_name,
        "ModelType": model_type,
        "PluginId": plugin_id,
        "DeviceId": device_id,
        "MinSDKVersion": min_sdk_version,
        "ModelFile": model_files,
        "MMProjFile": mmproj_file,
        "TokenizerFile": {
            "Name": "",
            "Downloaded": False,
            "Size": 0
        },
        "ExtraFiles": extra_files if extra_files else None,
        # Preserve old metadata fields
        "pipeline_tag": old_metadata.get('pipeline_tag') if old_metadata.get('pipeline_tag') else existing_manifest.get('pipeline_tag'),
        "download_time": old_metadata.get('download_time') if old_metadata.get('download_time') else existing_manifest.get('download_time'),
        "avatar_url": old_metadata.get('avatar_url') if old_metadata.get('avatar_url') else existing_manifest.get('avatar_url')
    }
    
    return manifest


def detect_model_type(files: List[str], old_metadata: Dict[str, Any] = None) -> str:
    """Detect if this is a GGUF, MLX, or NPU model based on file extensions and metadata.
    
    Args:
        files: List of files in the model directory
        old_metadata: Metadata dict that may contain 'model_file_type'
        
    Returns:
        Model type string: 'gguf', 'mlx', or 'npu'
    """
    # Check if model_file_type is explicitly set to NPU
    if old_metadata and old_metadata.get('model_file_type') == 'npu':
        return "npu"
    
    # Otherwise, detect based on file extensions
    has_gguf = any(f.endswith('.gguf') for f in files)
    has_safetensors = any(f.endswith('.safetensors') or 'safetensors' in f for f in files)
    
    if has_gguf:
        return "gguf"
    elif has_safetensors:
        return "mlx"
    else:
        # Default to mlx for other types
        return "mlx"


def create_manifest_from_files(repo_id: str, files: List[str], directory_path: str, old_metadata: Dict[str, Any], is_mmproj: bool = False, file_name: Optional[Union[str, List[str]]] = None, **kwargs) -> Dict[str, Any]:
    """
    Create appropriate manifest format based on detected model type.
    
    Args:
        repo_id: Repository ID
        files: List of files in the model directory
        directory_path: Path to the model directory
        old_metadata: Existing metadata (pipeline_tag, download_time, avatar_url, model_file_type)
        is_mmproj: Whether the downloaded file is an mmproj file
        file_name: The specific file(s) that were downloaded (None if entire repo was downloaded)
        **kwargs: Additional metadata including plugin_id, model_name, model_type, device_id, min_sdk_version
        
    Returns:
        Dict containing the appropriate manifest format
    """
    model_type = detect_model_type(files, old_metadata)
    
    if model_type == "gguf":
        return create_gguf_manifest(repo_id, files, directory_path, old_metadata, is_mmproj, file_name, **kwargs)
    elif model_type == "npu":
        return create_npu_manifest(repo_id, files, directory_path, old_metadata, is_mmproj, file_name, **kwargs)
    else:  # mlx or other
        return create_mlx_manifest(repo_id, files, directory_path, old_metadata, is_mmproj, file_name, **kwargs)


def save_manifest_with_files_metadata(repo_id: str, local_dir: str, old_metadata: Dict[str, Any], is_mmproj: bool = False, file_name: Optional[Union[str, List[str]]] = None, **kwargs) -> None:
    """
    Create and save manifest based on files found in the directory.
    
    Args:
        repo_id: Repository ID
        local_dir: Local directory containing the model files
        old_metadata: Existing metadata to preserve
        is_mmproj: Whether the downloaded file is an mmproj file
        file_name: The specific file(s) that were downloaded (None if entire repo was downloaded)
        **kwargs: Additional metadata including plugin_id, model_name, model_type, device_id, min_sdk_version
    """
    # Get list of files in the directory
    files = []
    try:
        for root, dirs, filenames in os.walk(local_dir):
            for filename in filenames:
                # Store relative path from the directory
                rel_path = os.path.relpath(os.path.join(root, filename), local_dir)
                files.append(rel_path)
    except (OSError, IOError):
        pass
    
    # Create appropriate manifest
    manifest = create_manifest_from_files(repo_id, files, local_dir, old_metadata, is_mmproj, file_name, **kwargs)
    
    # Save manifest
    save_download_metadata(local_dir, manifest)
