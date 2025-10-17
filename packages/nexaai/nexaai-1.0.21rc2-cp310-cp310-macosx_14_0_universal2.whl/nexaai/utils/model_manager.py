import os
import shutil
import json
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Callable, Dict, Any, List, Union
import functools
from enum import Enum
from tqdm.auto import tqdm
from huggingface_hub import HfApi
from huggingface_hub.utils import HfHubHTTPError, RepositoryNotFoundError

from .progress_tracker import CustomProgressTqdm, DownloadProgressTracker
from .manifest_utils import (
    load_download_metadata,
    save_download_metadata,
    save_manifest_with_files_metadata,
)

# Default path for model storage
DEFAULT_MODEL_SAVING_PATH = "~/.cache/nexa.ai/nexa_sdk/models/"


@dataclass
class MMProjInfo:
    """Data class for mmproj file information."""
    mmproj_path: Optional[str] = None
    size: int = 0

@dataclass
class DownloadedModel:
    """Data class representing a downloaded model with all its metadata."""
    repo_id: str
    files: List[str]
    folder_type: str  # 'owner_repo' or 'direct_repo'
    local_path: str
    size_bytes: int
    file_count: int
    full_repo_download_complete: bool = True  # True if no incomplete downloads detected
    pipeline_tag: Optional[str] = None  # Pipeline tag from HuggingFace model info
    download_time: Optional[str] = None  # ISO format timestamp of download
    avatar_url: Optional[str] = None  # Avatar URL for the model author
    mmproj_info: Optional[MMProjInfo] = None  # mmproj file information
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for backward compatibility."""
        result = {
            'repo_id': self.repo_id,
            'files': self.files,
            'folder_type': self.folder_type,
            'local_path': self.local_path,
            'size_bytes': self.size_bytes,
            'file_count': self.file_count,
            'full_repo_download_complete': self.full_repo_download_complete,
            'pipeline_tag': self.pipeline_tag,
            'download_time': self.download_time,
            'avatar_url': self.avatar_url,
            'mmproj_info': {
                'mmproj_path': self.mmproj_info.mmproj_path,
                'size': self.mmproj_info.size
            } if self.mmproj_info else None
        }
        return result


##########################################################################
#                        List downloaded models                          #
##########################################################################


def _check_for_incomplete_downloads(directory_path: str) -> bool:
    """
    Check if there are incomplete downloads in the model directory.
    
    This function checks for the presence of .incomplete or .lock files
    in the .cache/huggingface/download directory within the model folder,
    which indicates that the model download has not completed.
    
    Args:
        directory_path: Path to the model directory
        
    Returns:
        bool: True if download is complete (no incomplete files found), 
              False if incomplete downloads are detected
    """
    # Check for .cache/huggingface/download directory
    cache_dir = os.path.join(directory_path, '.cache', 'huggingface', 'download')
    
    # If the cache directory doesn't exist, assume download is complete
    if not os.path.exists(cache_dir):
        return True
    
    try:
        # Walk through the cache directory to find incomplete or lock files
        for root, dirs, files in os.walk(cache_dir):
            for filename in files:
                # Check for .incomplete or .lock files
                if filename.endswith('.incomplete'):
                    return False  # Found incomplete download
        
        # No incomplete files found
        return True
    except (OSError, IOError):
        # If we can't access the directory, assume download is complete
        return True

def _get_directory_size_and_files(directory_path: str) -> tuple[int, List[str]]:
    """Get total size and list of files in a directory."""
    total_size = 0
    files = []
    
    try:
        for root, dirs, filenames in os.walk(directory_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                try:
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    # Store relative path from the directory
                    rel_path = os.path.relpath(file_path, directory_path)
                    files.append(rel_path)
                except (OSError, IOError):
                    # Skip files that can't be accessed
                    continue
    except (OSError, IOError):
        # Skip directories that can't be accessed
        pass
    
    return total_size, files


def _has_valid_metadata(directory_path: str) -> bool:
    """Check if directory has either nexa.manifest or download_metadata.json (for backward compatibility)."""
    manifest_path = os.path.join(directory_path, 'nexa.manifest')
    old_metadata_path = os.path.join(directory_path, 'download_metadata.json')
    return os.path.exists(manifest_path) or os.path.exists(old_metadata_path)


def _extract_mmproj_info(manifest: Dict[str, Any], local_path: str) -> Optional[MMProjInfo]:
    """
    Extract mmproj information from manifest data.
    
    Args:
        manifest: Dictionary containing manifest data
        local_path: Local path to the model directory
        
    Returns:
        MMProjInfo object if mmproj file exists, None otherwise
    """
    # Check if manifest has MMProjFile information
    mmproj_file_info = manifest.get('MMProjFile')
    if not mmproj_file_info or not mmproj_file_info.get('Downloaded') or not mmproj_file_info.get('Name'):
        return None
    
    mmproj_filename = mmproj_file_info.get('Name', '')
    if not mmproj_filename:
        return None
    
    # Construct full path to mmproj file
    mmproj_path = os.path.join(local_path, mmproj_filename)
    
    # Get size from manifest, but verify file exists
    mmproj_size = mmproj_file_info.get('Size', 0)
    if os.path.exists(mmproj_path):
        try:
            # Verify size matches actual file size
            actual_size = os.path.getsize(mmproj_path)
            mmproj_size = actual_size  # Use actual size if different
        except (OSError, IOError):
            # If we can't get actual size, use size from manifest
            pass
    else:
        # File doesn't exist, don't include mmproj info
        return None
    
    return MMProjInfo(mmproj_path=mmproj_path, size=mmproj_size)


def _scan_for_repo_folders(base_path: str) -> List[DownloadedModel]:
    """Scan a directory for repository folders and return model information."""
    models = []
    
    try:
        if not os.path.exists(base_path):
            return models
        
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            
            # Skip non-directory items
            if not os.path.isdir(item_path):
                continue
            
            # Check if this might be an owner folder by looking for subdirectories
            has_subdirs = False
            direct_files = []
            
            try:
                for subitem in os.listdir(item_path):
                    subitem_path = os.path.join(item_path, subitem)
                    if os.path.isdir(subitem_path):
                        has_subdirs = True
                        # This looks like owner/repo structure
                        # Only include if nexa.manifest or download_metadata.json exists (backward compatibility)
                        if _has_valid_metadata(subitem_path):
                            size_bytes, files = _get_directory_size_and_files(subitem_path)
                            if files:  # Only include if there are files
                                # Check if the download is complete
                                download_complete = _check_for_incomplete_downloads(subitem_path)
                                # Load metadata if it exists
                                repo_id = f"{item}/{subitem}"
                                metadata = load_download_metadata(subitem_path, repo_id)
                                
                                # Extract mmproj information
                                mmproj_info = _extract_mmproj_info(metadata, subitem_path)
                                
                                models.append(DownloadedModel(
                                    repo_id=repo_id,
                                    files=files,
                                    folder_type='owner_repo',
                                    local_path=subitem_path,
                                    size_bytes=size_bytes,
                                    file_count=len(files),
                                    full_repo_download_complete=download_complete,
                                    pipeline_tag=metadata.get('pipeline_tag'),
                                    download_time=metadata.get('download_time'),
                                    avatar_url=metadata.get('avatar_url'),
                                    mmproj_info=mmproj_info
                                ))
                    else:
                        direct_files.append(subitem)
            except (OSError, IOError):
                # Skip directories that can't be accessed
                continue
            
            # Direct repo folder (no owner structure)
            if not has_subdirs and direct_files:
                # Only include if nexa.manifest or download_metadata.json exists (backward compatibility)
                if _has_valid_metadata(item_path):
                    size_bytes, files = _get_directory_size_and_files(item_path)
                    if files:  # Only include if there are files
                        # Check if the download is complete
                        download_complete = _check_for_incomplete_downloads(item_path)
                        # Load metadata if it exists
                        repo_id = item
                        metadata = load_download_metadata(item_path, repo_id)
                        
                        # Extract mmproj information
                        mmproj_info = _extract_mmproj_info(metadata, item_path)
                        
                        models.append(DownloadedModel(
                            repo_id=repo_id,
                            files=files,
                            folder_type='direct_repo',
                            local_path=item_path,
                            size_bytes=size_bytes,
                            file_count=len(files),
                            full_repo_download_complete=download_complete,
                            pipeline_tag=metadata.get('pipeline_tag'),
                            download_time=metadata.get('download_time'),
                            avatar_url=metadata.get('avatar_url'),
                            mmproj_info=mmproj_info
                        ))
    
    except (OSError, IOError):
        # Skip if base path can't be accessed
        pass
    
    return models


def list_downloaded_models(local_dir: Optional[str] = None) -> List[DownloadedModel]:
    """
    List all downloaded models in the specified directory.
    
    This function scans the local directory for downloaded models and returns
    information about each repository including files, size, and folder structure.
    
    It handles different folder naming conventions:
    - Owner/repo structure (e.g., "microsoft/DialoGPT-small")
    - Direct repo folders (repos without owner prefix)
    
    Args:
        local_dir (str, optional): Directory to scan for downloaded models.
                                  If None, uses DEFAULT_MODEL_SAVING_PATH.
    
    Returns:
        List[DownloadedModel]: List of DownloadedModel objects with attributes:
            - repo_id: str - Repository ID (e.g., "owner/repo")
            - files: List[str] - List of relative file paths in the repository
            - folder_type: str - 'owner_repo' or 'direct_repo'
            - local_path: str - Full path to the model directory
            - size_bytes: int - Total size of all files in bytes
            - file_count: int - Number of files in the repository
            - full_repo_download_complete: bool - True if no incomplete downloads detected, 
                                                  False if .incomplete or .lock files exist
            - pipeline_tag: Optional[str] - Pipeline tag from HuggingFace model info
            - download_time: Optional[str] - ISO format timestamp when the model was downloaded
            - avatar_url: Optional[str] - Avatar URL for the model author
            - mmproj_info: Optional[MMProjInfo] - mmproj file information with mmproj_path and size
    """
    
    # Set up local directory
    if local_dir is None:
        local_dir = os.path.expanduser(DEFAULT_MODEL_SAVING_PATH)
    
    local_dir = os.path.abspath(local_dir)
    
    if not os.path.exists(local_dir):
        return []
    
    # Scan for repository folders
    models = _scan_for_repo_folders(local_dir)
    
    # Sort by repo_id for consistent output
    models.sort(key=lambda x: x.repo_id)
    
    return models


##########################################################################
#                        Remove model functions                          #
##########################################################################


def _parse_model_path(model_path: str) -> tuple[str, str | None]:
    """
    Parse model_path to extract repo_id and optional filename.
    
    Examples:
        "microsoft/DialoGPT-small" -> ("microsoft/DialoGPT-small", None)
        "microsoft/DialoGPT-small/pytorch_model.bin" -> ("microsoft/DialoGPT-small", "pytorch_model.bin") 
        "Qwen/Qwen3-4B-GGUF/Qwen3-4B-Q4_K_M.gguf" -> ("Qwen/Qwen3-4B-GGUF", "Qwen3-4B-Q4_K_M.gguf")
    
    Args:
        model_path: The model path string
        
    Returns:
        Tuple of (repo_id, filename) where filename can be None
    """
    parts = model_path.strip().split('/')
    
    if len(parts) < 2:
        # Invalid format, assume it's just a repo name without owner
        return model_path, None
    elif len(parts) == 2:
        # Format: "owner/repo"
        return model_path, None
    else:
        # Format: "owner/repo/file" or "owner/repo/subdir/file"
        repo_id = f"{parts[0]}/{parts[1]}"
        filename = '/'.join(parts[2:])
        return repo_id, filename


def _validate_and_parse_input(model_path: str) -> tuple[str, Optional[str]]:
    """Validate input and parse model path."""
    if not model_path or not isinstance(model_path, str) or not model_path.strip():
        raise ValueError("model_path is required and must be a non-empty string")
    
    model_path = model_path.strip()
    return _parse_model_path(model_path)


def _find_target_model(repo_id: str, local_dir: str) -> DownloadedModel:
    """Find and validate the target model exists."""
    downloaded_models = list_downloaded_models(local_dir)
    
    for model in downloaded_models:
        if model.repo_id == repo_id:
            return model
    
    available_repos = [model.repo_id for model in downloaded_models]
    raise FileNotFoundError(
        f"Repository '{repo_id}' not found in downloaded models. "
        f"Available repositories: {available_repos}"
    )


def _clean_empty_owner_directory(target_model: DownloadedModel) -> None:
    """Remove empty owner directory if applicable."""
    if target_model.folder_type != 'owner_repo':
        return
    
    parent_dir = os.path.dirname(target_model.local_path)
    try:
        if os.path.exists(parent_dir) and not os.listdir(parent_dir):
            os.rmdir(parent_dir)
    except OSError:
        pass


def _remove_specific_file(target_model: DownloadedModel, file_name: str, local_dir: str) -> DownloadedModel:
    """Remove a specific file from the repository."""
    # Validate file exists in model
    if file_name not in target_model.files:
        raise FileNotFoundError(
            f"File '{file_name}' not found in repository '{target_model.repo_id}'. "
            f"Available files: {target_model.files[:10]}{'...' if len(target_model.files) > 10 else ''}"
        )
    
    # Construct full file path and validate it exists on disk
    file_path = os.path.join(target_model.local_path, file_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File does not exist on disk: {file_path}")
    
    # Get file size before removal
    try:
        file_size = os.path.getsize(file_path)
    except OSError:
        file_size = 0
    
    # Check if we should remove entire folder instead (for .gguf files)
    # If removing a .gguf file and no other non-mmproj .gguf files remain, remove entire folder
    if file_name.endswith('.gguf'):
        updated_files = [f for f in target_model.files if f != file_name]
        # Find remaining .gguf files that don't contain "mmproj" in filename
        remaining_non_mmproj_gguf = [
            f for f in updated_files 
            if f.endswith('.gguf') and 'mmproj' not in f.lower()
        ]
        
        # If no non-mmproj .gguf files remain, remove entire repository
        if len(remaining_non_mmproj_gguf) == 0:
            return _remove_entire_repository(target_model, local_dir)
    
    # Remove the file
    try:
        os.remove(file_path)
    except OSError as e:
        raise OSError(f"Failed to remove file '{file_path}': {e}")
    
    # Create updated model object
    updated_files = [f for f in target_model.files if f != file_name]
    updated_size = target_model.size_bytes - file_size
    # Re-check download completeness after file removal
    download_complete = _check_for_incomplete_downloads(target_model.local_path)
    updated_model = DownloadedModel(
        repo_id=target_model.repo_id,
        files=updated_files,
        folder_type=target_model.folder_type,
        local_path=target_model.local_path,
        size_bytes=updated_size,
        file_count=len(updated_files),
        full_repo_download_complete=download_complete
    )
    
    # If no files left, remove the entire directory
    if len(updated_files) == 0:
        try:
            shutil.rmtree(target_model.local_path)
            _clean_empty_owner_directory(target_model)
        except OSError:
            pass
    
    return updated_model


def _remove_entire_repository(target_model: DownloadedModel, local_dir: str) -> DownloadedModel:
    """Remove the entire repository and clean up."""
    # Remove the directory and all its contents
    try:
        shutil.rmtree(target_model.local_path)
    except OSError as e:
        raise OSError(f"Failed to remove directory '{target_model.local_path}': {e}")
    
    # Clean up associated resources
    _clean_empty_owner_directory(target_model)
    
    return target_model


def remove_model_or_file(
    model_path: str,
    local_dir: Optional[str] = None
) -> DownloadedModel:
    """
    Remove a downloaded model or specific file by repository ID or file path.
    
    This function supports two modes:
    1. Remove entire repository: "microsoft/DialoGPT-small" 
    2. Remove specific file: "Qwen/Qwen3-4B-GGUF/Qwen3-4B-Q4_K_M.gguf"
    
    For entire repository removal, it removes the directory and all files. For specific file removal, it only
    removes that file and updates the repository metadata.
    
    Args:
        model_path (str): Required. Either:
                         - Repository ID (e.g., "microsoft/DialoGPT-small") - removes entire repo
                         - File path (e.g., "Qwen/Qwen3-4B-GGUF/model.gguf") - removes specific file
        local_dir (str, optional): Directory to search for downloaded models.
                                  If None, uses DEFAULT_MODEL_SAVING_PATH.
    
    Returns:
        DownloadedModel: The model object representing what was removed from disk.
                        For file removal, returns updated model info after file removal.
        
    Raises:
        ValueError: If model_path is invalid (empty or None)
        FileNotFoundError: If the repository or file is not found in downloaded models
        OSError: If there's an error removing files from disk
    """
    # Validate input and parse path
    repo_id, file_name = _validate_and_parse_input(model_path)
    
    # Set up local directory
    if local_dir is None:
        local_dir = os.path.expanduser(DEFAULT_MODEL_SAVING_PATH)
    
    local_dir = os.path.abspath(local_dir)
    
    if not os.path.exists(local_dir):
        raise FileNotFoundError(f"Local directory does not exist: {local_dir}")
    
    # Find the target model
    target_model = _find_target_model(repo_id, local_dir)
    
    # Delegate to appropriate removal function
    if file_name:
        return _remove_specific_file(target_model, file_name, local_dir)
    else:
        return _remove_entire_repository(target_model, local_dir)


##########################################################################
#                        Check model existence functions                #
##########################################################################


def check_model_existence(
    model_path: str,
    local_dir: Optional[str] = None
) -> bool:
    """
    Check if a downloaded model or specific file exists locally.
    
    This function supports two modes:
    1. Check entire repository: "microsoft/DialoGPT-small" 
    2. Check specific file: "Qwen/Qwen3-4B-GGUF/Qwen3-4B-Q4_K_M.gguf"
    
    Args:
        model_path (str): Required. Either:
                         - Repository ID (e.g., "microsoft/DialoGPT-small") - checks entire repo
                         - File path (e.g., "Qwen/Qwen3-4B-GGUF/model.gguf") - checks specific file
        local_dir (str, optional): Directory to search for downloaded models.
                                  If None, uses DEFAULT_MODEL_SAVING_PATH.
    
    Returns:
        bool: True if the requested item exists, False otherwise
        
    Raises:
        ValueError: If model_path is invalid (empty or None)
    """
    # Validate input and parse path
    repo_id, file_name = _validate_and_parse_input(model_path)
    
    # Set up local directory
    if local_dir is None:
        local_dir = os.path.expanduser(DEFAULT_MODEL_SAVING_PATH)
    
    local_dir = os.path.abspath(local_dir)
    
    # Return False if local directory doesn't exist
    if not os.path.exists(local_dir):
        return False
    
    # Get all downloaded models
    downloaded_models = list_downloaded_models(local_dir)
    
    # Find the target model
    for model in downloaded_models:
        if model.repo_id == repo_id:
            # If no specific file requested, repository existence is sufficient
            if file_name is None:
                return True
            else:
                # Check specific file existence
                return file_name in model.files
    
    return False


##########################################################################
#                  HuggingFace Downloader Class                         #
##########################################################################


class HuggingFaceDownloader:
    """Class to handle downloads from HuggingFace Hub with unified API usage."""
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        token: Union[bool, str, None] = None,
        enable_transfer: bool = True
    ):
        """
        Initialize the downloader with HuggingFace API.
        
        Args:
            endpoint: Custom endpoint URL (e.g., "https://hf-mirror.com"). 
                     If None, uses default HuggingFace Hub.
            token: Authentication token for private repositories.
            enable_transfer: Whether to enable HF transfer for faster downloads.
        """
        # Always create an HfApi instance - either with custom endpoint or default
        self.token = token if isinstance(token, str) else False # False means disable authentication
        self.api = HfApi(endpoint=endpoint, token=self.token) if endpoint else HfApi(token=self.token)
        self.enable_transfer = enable_transfer
        self.original_hf_transfer = None
        self.endpoint = endpoint  # Store endpoint for avatar fetching
        self._model_info_cache: Dict[str, Any] = {}  # Cache for model_info results
        
    def _create_repo_directory(self, local_dir: str, repo_id: str) -> str:
        """Create a directory structure for the repository following HF convention."""
        if '/' in repo_id:
            # Standard format: owner/repo
            owner, repo = repo_id.split('/', 1)
            repo_dir = os.path.join(local_dir, owner, repo)
        else:
            # Direct repo name without owner
            repo_dir = os.path.join(local_dir, repo_id)
        
        os.makedirs(repo_dir, exist_ok=True)
        return repo_dir
    
    def _created_dir_if_not_exists(self, local_dir: Optional[str]) -> str:
        """Create directory if it doesn't exist and return the expanded path."""
        if local_dir is None:
            local_dir = DEFAULT_MODEL_SAVING_PATH
        
        local_dir = os.path.expanduser(local_dir)
        os.makedirs(local_dir, exist_ok=True)
        return local_dir
    
    def _get_model_info_cached(self, repo_id: str, files_metadata: bool = False):
        """Get model info with caching to avoid rate limiting.
        
        Args:
            repo_id: Repository ID
            files_metadata: Whether to include files metadata
            
        Returns:
            Model info object from HuggingFace API
        """
        # Create cache key based on repo_id and files_metadata flag
        cache_key = f"{repo_id}:files={files_metadata}"
        
        # Return cached result if available
        if cache_key in self._model_info_cache:
            return self._model_info_cache[cache_key]
        
        # Fetch from API and cache the result
        try:
            info = self.api.model_info(repo_id, files_metadata=files_metadata, token=self.token)
            self._model_info_cache[cache_key] = info
            return info
        except Exception:
            # Don't cache errors, re-raise
            raise
    
    def _get_repo_info_for_progress(
        self,
        repo_id: str,
        file_name: Optional[Union[str, List[str]]] = None
    ) -> tuple[int, int]:
        """Get total repository size and file count for progress tracking."""
        try:
            info = self._get_model_info_cached(repo_id, files_metadata=True)
            
            total_size = 0
            file_count = 0
            
            if info.siblings:
                for sibling in info.siblings:
                    # Handle different file_name types
                    if file_name is not None:
                        if isinstance(file_name, str):
                            # Single file - only count if it matches
                            if sibling.rfilename != file_name:
                                continue
                        elif isinstance(file_name, list):
                            # Multiple files - only count if in the list
                            if sibling.rfilename not in file_name:
                                continue
                    
                    # For all matching files (or all files if file_name is None)
                    if hasattr(sibling, 'size') and sibling.size is not None:
                        total_size += sibling.size
                        file_count += 1
                    else:
                        # Count files without size info
                        file_count += 1
            
            return total_size, file_count if file_count > 0 else 1
        except Exception:
            # If we can't get info, return defaults
            return 0, 1
    
    def _validate_and_setup_params(
        self,
        repo_id: str,
        file_name: Optional[Union[str, List[str]]]
    ) -> tuple[str, Optional[Union[str, List[str]]]]:
        """Validate and normalize input parameters."""
        if not repo_id:
            raise ValueError("repo_id is required")
        
        repo_id = repo_id.strip()
        
        # Handle file_name parameter
        if file_name is not None:
            if isinstance(file_name, str):
                file_name = file_name.strip()
                if not file_name:
                    file_name = None
            elif isinstance(file_name, list):
                # Filter out empty strings and strip whitespace
                file_name = [f.strip() for f in file_name if f and f.strip()]
                if not file_name:
                    file_name = None
            else:
                raise ValueError("file_name must be a string, list of strings, or None")
        
        return repo_id, file_name
    
    def _setup_progress_tracker(
        self,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]],
        show_progress: bool,
        repo_id: str,
        file_name: Optional[Union[str, List[str]]]
    ) -> Optional[DownloadProgressTracker]:
        """Initialize progress tracker if callback is provided."""
        if not progress_callback:
            return None
        
        progress_tracker = DownloadProgressTracker(progress_callback, show_progress)
        # Get repo info for progress tracking - now handles all cases
        total_size, file_count = self._get_repo_info_for_progress(repo_id, file_name)
        progress_tracker.set_repo_info(total_size, file_count)
        return progress_tracker
    
    def _setup_hf_transfer_env(self) -> None:
        """Set up HF transfer environment."""
        self.original_hf_transfer = os.environ.get("HF_HUB_ENABLE_HF_TRANSFER")
        if self.enable_transfer:
            os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
    
    def _cleanup_hf_transfer_env(self) -> None:
        """Restore original HF transfer environment."""
        if self.original_hf_transfer is not None:
            os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = self.original_hf_transfer
        else:
            os.environ.pop("HF_HUB_ENABLE_HF_TRANSFER", None)
    
    def _validate_repository_and_get_info(
        self,
        repo_id: str,
        progress_tracker: Optional[DownloadProgressTracker]
    ):
        """Validate repository exists and get info."""
        try:
            info = self._get_model_info_cached(repo_id, files_metadata=False)
            return info
        except RepositoryNotFoundError:
            error_msg = f"Repository '{repo_id}' not found. Please check the repository ID."
            if progress_tracker:
                progress_tracker.set_error(error_msg)
            raise RepositoryNotFoundError(error_msg)
        except HfHubHTTPError as e:
            if e.response.status_code == 404:
                error_msg = f"Repository '{repo_id}' not found. Please check the repository ID."
                if progress_tracker:
                    progress_tracker.set_error(error_msg)
                raise RepositoryNotFoundError(error_msg)
            else:
                error_msg = f"HTTP error while accessing repository '{repo_id}': {e}"
                if progress_tracker:
                    progress_tracker.set_error(error_msg)
                raise HfHubHTTPError(error_msg)
    
    def _validate_file_exists_in_repo(
        self,
        file_name: str,
        info,
        repo_id: str,
        progress_tracker: Optional[DownloadProgressTracker]
    ) -> None:
        """Validate that the file exists in the repository."""
        file_exists = False
        if info.siblings:
            for sibling in info.siblings:
                if sibling.rfilename == file_name:
                    file_exists = True
                    break
        
        if not file_exists:
            available_files = [sibling.rfilename for sibling in info.siblings] if info.siblings else []
            error_msg = (
                f"File '{file_name}' not found in repository '{repo_id}'. "
                f"Available files: {available_files[:10]}{'...' if len(available_files) > 10 else ''}"
            )
            if progress_tracker:
                progress_tracker.set_error(error_msg)
                progress_tracker.stop_tracking()
            raise ValueError(error_msg)
    
    def _check_file_exists_and_valid(
        self,
        file_path: str,
        expected_size: Optional[int] = None
    ) -> bool:
        """Check if a file exists and is valid (non-empty, correct size if known)."""
        if not os.path.exists(file_path):
            return False
        
        # Check file is not empty
        try:
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False
        except (OSError, IOError):
            return False
        
        # If we have expected size, check it matches
        if expected_size is not None and file_size != expected_size:
            return False
        
        # If no expected size, just check that file is not empty
        return os.path.getsize(file_path) > 0
    
    def _extract_model_file_type_from_tags(self, repo_id: str) -> Optional[str]:
        """Extract model file type from repo tags with priority: NPU > MLX > GGUF."""
        try:
            info = self._get_model_info_cached(repo_id, files_metadata=False)
            if hasattr(info, 'tags') and info.tags:
                # Convert tags to lowercase for case-insensitive matching
                tags_lower = [tag.lower() for tag in info.tags]
                
                # Check with priority: NPU > MLX > GGUF
                if 'npu' in tags_lower:
                    return 'npu'
                elif 'mlx' in tags_lower:
                    return 'mlx'
                elif 'gguf' in tags_lower:
                    return 'gguf'
        except Exception:
            pass
        return None
    
    def _load_downloaded_manifest(self, local_dir: str) -> Dict[str, Any]:
        """Load nexa.manifest from the downloaded repository if it exists."""
        manifest_path = os.path.join(local_dir, 'nexa.manifest')
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    def _download_manifest_if_needed(self, repo_id: str, local_dir: str) -> bool:
        """
        Download nexa.manifest from the repository if it doesn't exist locally.
        
        Args:
            repo_id: Repository ID
            local_dir: Local directory where the manifest should be saved
            
        Returns:
            bool: True if manifest was downloaded or already exists, False if not found in repo
        """
        manifest_path = os.path.join(local_dir, 'nexa.manifest')
        
        # Check if manifest already exists locally
        if os.path.exists(manifest_path):
            return True
        
        # Try to download nexa.manifest from the repository
        try:
            print(f"[INFO] Attempting to download nexa.manifest from {repo_id}...")
            self.api.hf_hub_download(
                repo_id=repo_id,
                filename='nexa.manifest',
                local_dir=local_dir,
                local_dir_use_symlinks=False,
                token=self.token,
                force_download=False
            )
            print(f"[OK] Successfully downloaded nexa.manifest from {repo_id}")
            return True
        except Exception as e:
            # Manifest doesn't exist in repo or other error - this is fine, we'll create it
            print(f"[INFO] nexa.manifest not found in {repo_id}, will create locally")
            return False
    
    def _fetch_and_save_metadata(self, repo_id: str, local_dir: str, is_mmproj: bool = False, file_name: Optional[Union[str, List[str]]] = None, **kwargs) -> None:
        """Fetch model info and save metadata after successful download."""
        # Initialize metadata with defaults to ensure manifest is always created
        old_metadata = {
            'pipeline_tag': "text-generation", # Default to text-generation pipeline-tag
            'download_time': datetime.now().isoformat(),
            'avatar_url': None
        }
        
        # Try to fetch additional metadata, but don't let failures prevent manifest creation
        try:
            # Fetch model info to get pipeline_tag (using cache)
            info = self._get_model_info_cached(repo_id, files_metadata=False)
            if hasattr(info, 'pipeline_tag') and info.pipeline_tag:
                old_metadata['pipeline_tag'] = info.pipeline_tag
        except Exception as e:
            # Log the error but continue with manifest creation
            print(f"Warning: Could not fetch model info for {repo_id}: {e}")
        
        # Use input avater url if provided
        old_metadata['avatar_url'] = kwargs.get('avatar_url')
        
        # Extract model file type from tags
        model_file_type = self._extract_model_file_type_from_tags(repo_id)
        if model_file_type:
            old_metadata['model_file_type'] = model_file_type
        
        # Load existing nexa.manifest from downloaded repo (if exists)
        downloaded_manifest = self._load_downloaded_manifest(local_dir)
        if downloaded_manifest:
            old_metadata['downloaded_manifest'] = downloaded_manifest

        
        # CRITICAL: Always create the manifest file, regardless of metadata fetch failures
        try:
            save_manifest_with_files_metadata(repo_id, local_dir, old_metadata, is_mmproj, file_name, **kwargs)
            print(f"[OK] Successfully created nexa.manifest for {repo_id}")
        except Exception as e:
            # This is critical - if manifest creation fails, we should know about it
            print(f"ERROR: Failed to create nexa.manifest for {repo_id}: {e}")
            # Try a fallback approach - create a minimal manifest
            try:
                minimal_manifest = {
                    "Name": repo_id,
                    "ModelName": kwargs.get('model_name', ''),
                    "ModelType": kwargs.get('model_type', 'other'),
                    "PluginId": kwargs.get('plugin_id', 'unknown'),
                    "DeviceId": kwargs.get('device_id', ''),
                    "MinSDKVersion": kwargs.get('min_sdk_version', ''),
                    "ModelFile": {},
                    "MMProjFile": {"Name": "", "Downloaded": False, "Size": 0},
                    "TokenizerFile": {"Name": "", "Downloaded": False, "Size": 0},
                    "ExtraFiles": None,
                    "pipeline_tag": old_metadata.get('pipeline_tag'),
                    "download_time": old_metadata.get('download_time'),
                    "avatar_url": old_metadata.get('avatar_url')
                }
                save_download_metadata(local_dir, minimal_manifest)
                print(f"[OK] Created minimal nexa.manifest for {repo_id} as fallback")
            except Exception as fallback_error:
                print(f"CRITICAL ERROR: Could not create even minimal manifest for {repo_id}: {fallback_error}")
    
    def _download_single_file(
        self,
        repo_id: str,
        file_name: str,
        local_dir: str,
        progress_tracker: Optional[DownloadProgressTracker],
        force_download: bool = False,
        **kwargs
    ) -> str:
        """Download a single file from the repository using HuggingFace Hub API."""
        # Create repo-specific directory for the single file
        file_local_dir = self._create_repo_directory(local_dir, repo_id)
        
        # Check if file already exists
        local_file_path = os.path.join(file_local_dir, file_name)
        if not force_download and self._check_file_exists_and_valid(local_file_path):
            print(f"[SKIP] File already exists: {file_name}")
            # Stop progress tracking
            if progress_tracker:
                progress_tracker.stop_tracking()
            return local_file_path
        
        try:
            # Note: hf_hub_download doesn't support tqdm_class parameter
            # Progress tracking works through the global tqdm monkey patching
            downloaded_path = self.api.hf_hub_download(
                repo_id=repo_id,
                filename=file_name,
                local_dir=file_local_dir,
                local_dir_use_symlinks=False,
                token=self.token,
                force_download=force_download
            )
            
            # Stop progress tracking
            if progress_tracker:
                progress_tracker.stop_tracking()
            
            # Download nexa.manifest from repo if it doesn't exist locally
            self._download_manifest_if_needed(repo_id, file_local_dir)
            
            # Save metadata after successful download
            self._fetch_and_save_metadata(repo_id, file_local_dir, self._current_is_mmproj, self._current_file_name, **kwargs)
            
            return downloaded_path
            
        except HfHubHTTPError as e:
            error_msg = f"Error downloading file '{file_name}': {e}"
            if progress_tracker:
                progress_tracker.set_error(error_msg)
                progress_tracker.stop_tracking()
            if e.response.status_code == 404:
                raise ValueError(f"File '{file_name}' not found in repository '{repo_id}'")
            else:
                raise HfHubHTTPError(error_msg)
    
    def _download_entire_repository(
        self,
        repo_id: str,
        local_dir: str,
        progress_tracker: Optional[DownloadProgressTracker],
        force_download: bool = False,
        **kwargs
    ) -> str:
        """Download the entire repository."""
        # Create a subdirectory for this specific repo
        repo_local_dir = self._create_repo_directory(local_dir, repo_id)
        
        try:
            download_kwargs = {
                'repo_id': repo_id,
                'local_dir': repo_local_dir,
                'local_dir_use_symlinks': False,
                'token': self.token,
                'force_download': force_download
            }
            
            # Add tqdm_class if progress tracking is enabled
            if progress_tracker:
                download_kwargs['tqdm_class'] = CustomProgressTqdm
            
            downloaded_path = self.api.snapshot_download(**download_kwargs)
            
            # Stop progress tracking
            if progress_tracker:
                progress_tracker.stop_tracking()
            
            # Save metadata after successful download
            self._fetch_and_save_metadata(repo_id, repo_local_dir, self._current_is_mmproj, self._current_file_name, **kwargs)
            
            return downloaded_path
            
        except HfHubHTTPError as e:
            error_msg = f"Error downloading repository '{repo_id}': {e}"
            if progress_tracker:
                progress_tracker.set_error(error_msg)
                progress_tracker.stop_tracking()
            raise HfHubHTTPError(error_msg)
    
    def _download_multiple_files_from_hf(
        self,
        repo_id: str,
        file_names: List[str],
        local_dir: str,
        progress_tracker: Optional[DownloadProgressTracker],
        force_download: bool = False,
        **kwargs
    ) -> str:
        """Download multiple specific files from HuggingFace Hub."""
        # Create repo-specific directory
        repo_local_dir = self._create_repo_directory(local_dir, repo_id)
        
        # Create overall progress bar for multiple files
        overall_progress = tqdm(
            total=len(file_names),
            unit='file',
            desc=f"Downloading {len(file_names)} files from {repo_id}",
            position=0,
            leave=True
        )
        
        try:
            for file_name in file_names:
                overall_progress.set_postfix_str(f"Current: {os.path.basename(file_name)}")
                
                # Check if file already exists
                local_file_path = os.path.join(repo_local_dir, file_name)
                if not force_download and self._check_file_exists_and_valid(local_file_path):
                    print(f"[SKIP] File already exists: {file_name}")
                    overall_progress.update(1)
                    continue
                
                # Download each file using hf_hub_download
                self.api.hf_hub_download(
                    repo_id=repo_id,
                    filename=file_name,
                    local_dir=repo_local_dir,
                    local_dir_use_symlinks=False,
                    token=self.token,
                    force_download=force_download
                )
                
                overall_progress.update(1)
            
            overall_progress.close()
            
            # Stop progress tracking
            if progress_tracker:
                progress_tracker.stop_tracking()
            
            # Download nexa.manifest from repo if it doesn't exist locally
            self._download_manifest_if_needed(repo_id, repo_local_dir)
            
            # Save metadata after successful download
            self._fetch_and_save_metadata(repo_id, repo_local_dir, self._current_is_mmproj, self._current_file_name, **kwargs)
            
            return repo_local_dir
            
        except HfHubHTTPError as e:
            overall_progress.close()
            error_msg = f"Error downloading files from '{repo_id}': {e}"
            if progress_tracker:
                progress_tracker.set_error(error_msg)
                progress_tracker.stop_tracking()
            raise HfHubHTTPError(error_msg)
        except Exception as e:
            overall_progress.close()
            if progress_tracker:
                progress_tracker.set_error(str(e))
                progress_tracker.stop_tracking()
            raise
    
    def download(
        self,
        repo_id: str,
        file_name: Optional[Union[str, List[str]]] = None,
        local_dir: Optional[str] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        show_progress: bool = True,
        force_download: bool = False,
        is_mmproj: bool = False,
        **kwargs
    ) -> str:
        """
        Main download method that handles all download scenarios.
        
        Args:
            repo_id: Repository ID to download from
            file_name: Optional file name(s) to download
            local_dir: Local directory to save files
            progress_callback: Callback for progress updates
            show_progress: Whether to show progress bar
            force_download: Force re-download even if files exist
            
        Returns:
            Path to downloaded file or directory
        """
        # Validate and normalize parameters
        repo_id, file_name = self._validate_and_setup_params(repo_id, file_name)
        
        # Store parameters as instance variables for use in _fetch_and_save_metadata
        self._current_is_mmproj = is_mmproj
        self._current_file_name = file_name
        
        # Set up local directory
        local_dir = self._created_dir_if_not_exists(local_dir)
        
        # Set up progress tracker
        file_name_for_progress = file_name if isinstance(file_name, str) else None
        progress_tracker = self._setup_progress_tracker(
            progress_callback, show_progress, repo_id, file_name_for_progress
        )
        
        # Set up HF transfer environment
        self._setup_hf_transfer_env()
        
        try:
            # Validate repository and get info
            info = self._validate_repository_and_get_info(repo_id, progress_tracker)
            
            # Start progress tracking
            if progress_tracker:
                progress_tracker.start_tracking()
            
            # Choose download strategy based on file_name
            if file_name is None:
                # Download entire repository
                return self._download_entire_repository(
                    repo_id, local_dir, progress_tracker, force_download, **kwargs
                )
            elif isinstance(file_name, str):
                # Download specific single file
                self._validate_file_exists_in_repo(file_name, info, repo_id, progress_tracker)
                return self._download_single_file(
                    repo_id, file_name, local_dir, progress_tracker, force_download, **kwargs
                )
            else:  # file_name is a list
                # Download multiple specific files
                # Validate all files exist
                for fname in file_name:
                    self._validate_file_exists_in_repo(fname, info, repo_id, progress_tracker)
                
                return self._download_multiple_files_from_hf(
                    repo_id, file_name, local_dir, progress_tracker, force_download, **kwargs
                )
        
        except Exception as e:
            # Handle any unexpected errors
            if progress_tracker and progress_tracker.download_status != "error":
                progress_tracker.set_error(str(e))
                progress_tracker.stop_tracking()
            raise
        
        finally:
            # Restore original HF transfer setting
            self._cleanup_hf_transfer_env()


##########################################################################
#                    Public Download Function                           #
##########################################################################


def download_from_huggingface(
    repo_id: str,
    file_name: Optional[Union[str, List[str]]] = None,
    local_dir: Optional[str] = None,
    enable_transfer: bool = True,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    show_progress: bool = True,
    token: Union[bool, str, None] = None,
    custom_endpoint: Optional[str] = None,
    force_download: bool = False,
    is_mmproj: Optional[bool] = None,
    **kwargs
) -> str:
    """
    Download models or files from HuggingFace Hub or custom mirror endpoints.
    
    Args:
        repo_id (str): Required. The repository ID to download from (e.g., "microsoft/DialoGPT-medium")
        file_name (Union[str, List[str]], optional): Single filename or list of filenames to download.
                                                     If None, downloads entire repo.
        local_dir (str, optional): Local directory to save files. If None, uses DEFAULT_MODEL_SAVING_PATH.
        enable_transfer (bool, optional): Whether to enable HF transfer for faster downloads. Default True.
        progress_callback (Callable, optional): Callback function to receive progress updates. 
                                               Function receives a dict with progress information.
        show_progress (bool, optional): Whether to show a unified progress bar in the terminal. Default True.
                                       Only works when progress_callback is provided.
        token (Union[bool, str, None], optional): A token to be used for the download.
                                                 - If True, the token is read from the HuggingFace config folder.
                                                 - If a string, it's used as the authentication token.
                                                 - If None, uses default behavior.
        custom_endpoint (str, optional): A custom HuggingFace-compatible endpoint URL.
                                        Should be ONLY the base endpoint without any paths.
                                        Examples:
                                        - "https://hf-mirror.com"
                                        - "https://huggingface.co" (default)
                                        The endpoint will be used to initialize HfApi for all downloads.
        force_download (bool, optional): If True, download files even if they already exist locally.
                                        Default False (skip existing files).
        is_mmproj (bool, optional): Whether the file being downloaded is an mmproj file. Only used when
                                   file_name is not None. If None, defaults to True if 'mmproj' is in 
                                   the filename, False otherwise.
        **kwargs: Additional parameters including:
            - plugin_id (str): Override PluginId in nexa.manifest (highest priority)
            - model_name (str): Override ModelName in nexa.manifest (highest priority)
            - model_type (str): Override ModelType in nexa.manifest (highest priority)
            - device_id (str): Set DeviceId in nexa.manifest (highest priority)
            - min_sdk_version (str): Set MinSDKVersion in nexa.manifest (highest priority)
    
    Returns:
        str: Path to the downloaded file or directory
        
    Raises:
        ValueError: If repo_id is invalid or file_name doesn't exist in the repo
        RepositoryNotFoundError: If the repository doesn't exist
        HfHubHTTPError: If there's an HTTP error during download
        
    Progress Callback Data Format:
        {
            'status': str,  # 'idle', 'downloading', 'completed', 'error'
            'error_message': str,  # Only present if status is 'error'
            'progress': {
                'total_downloaded': int,  # Bytes downloaded
                'total_size': int,       # Total bytes to download
                'percentage': float,     # Progress percentage (0-100)
                'files_active': int,     # Number of files currently downloading
                'files_total': int,      # Total number of files
                'known_total': bool      # Whether total size is known
            },
            'speed': {
                'bytes_per_second': float,  # Download speed in bytes/sec
                'formatted': str            # Human readable speed (e.g., "1.2 MB/s")
            },
            'formatting': {
                'downloaded': str,  # Human readable downloaded size
                'total_size': str   # Human readable total size
            },
            'timing': {
                'elapsed_seconds': float,  # Time since download started
                'eta_seconds': float,      # Estimated time remaining
                'start_time': float        # Download start timestamp
            }
        }
    """
    # Set default value for is_mmproj based on filename if not explicitly provided
    if is_mmproj is None and file_name is not None:
        # Check if any filename contains 'mmproj'
        filenames_to_check = file_name if isinstance(file_name, list) else [file_name]
        is_mmproj = any('mmproj' in filename.lower() for filename in filenames_to_check)
    elif is_mmproj is None:
        # Default to False if no file_name is provided
        is_mmproj = False
    
    # Create downloader instance with custom endpoint if provided
    downloader = HuggingFaceDownloader(
        endpoint=custom_endpoint, 
        token=token, 
        enable_transfer=enable_transfer
    )
    
    # Use the downloader to perform the download
    return downloader.download(
        repo_id=repo_id,
        file_name=file_name,
        local_dir=local_dir,
        progress_callback=progress_callback,
        show_progress=show_progress,
        force_download=force_download,
        is_mmproj=is_mmproj,
        **kwargs
    )


##########################################################################
#                       Auto-download decorator                         #
##########################################################################


def _download_model_if_needed(
    model_path: str,
    param_name: str,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    token: Union[bool, str, None] = None,
    is_mmproj: bool = False,
    **kwargs
) -> str:
    """
    Helper function to download a model from HuggingFace if it doesn't exist locally.
    
    Args:
        model_path: The model path that may be local or remote
        param_name: Name of the parameter (for error messages)
        progress_callback: Callback function for download progress updates
        token: HuggingFace authentication token for private repositories
        
    Returns:
        str: Local path to the model (either existing or downloaded)
        
    Raises:
        RuntimeError: If download fails
    """
    # Check if model_path exists locally (file or directory)
    if os.path.exists(model_path):
        # Local path exists, return as-is
        return model_path
    
    # Model path doesn't exist locally, try to download from HuggingFace
    try:
        # Parse model_path to extract repo_id and filename
        repo_id, file_name = _parse_model_path(model_path)
        
        # Download the model
        downloaded_path = download_from_huggingface(
            repo_id=repo_id,
            file_name=file_name,
            local_dir=None,  # Use default cache directory
            enable_transfer=True,
            progress_callback=progress_callback,
            show_progress=True,
            token=token,
            is_mmproj=is_mmproj,
            **kwargs
        )
        
        return downloaded_path
        
    except Exception as e:
        # Only handle download-related errors
        raise RuntimeError(f"Could not load model from '{param_name}={model_path}': {e}")


def auto_download_model(func: Callable) -> Callable:
    """
    Decorator that automatically downloads models from HuggingFace if they don't exist locally.
    
    This decorator should be applied to __init__ methods that take a name_or_path parameter
    and optionally an mmproj_path parameter. If these paths don't exist as local files/directories,
    it will attempt to download them from HuggingFace Hub using the download_from_huggingface function.
    
    The name_or_path and mmproj_path can be in formats like:
    - "microsoft/DialoGPT-small" (downloads entire repo)  
    - "microsoft/DialoGPT-small/pytorch_model.bin" (downloads specific file)
    - "Qwen/Qwen3-4B-GGUF/Qwen3-4B-Q4_K_M.gguf" (downloads specific file)
    
    Optional kwargs that are extracted and passed to download_from_huggingface:
    - progress_callback: Callback function for download progress updates
    - token: HuggingFace authentication token for private repositories
    
    Args:
        func: The __init__ method to wrap
        
    Returns:
        Wrapped function that handles automatic model downloading
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract progress_callback and token from arguments
        progress_callback = None
        if 'progress_callback' in kwargs:
            progress_callback = kwargs.pop('progress_callback')  # Remove from kwargs to avoid passing to original func
        
        token = None
        if 'token' in kwargs:
            token = kwargs.pop('token')  # Remove from kwargs to avoid passing to original func
        
        # Handle name_or_path parameter
        name_or_path = None
        name_path_index = None
        is_name_positional = False
        
        # Find name_or_path in arguments
        # Assuming name_or_path is the first argument after self
        if len(args) >= 2:
            name_or_path = args[1]
            args_list = list(args)
            name_path_index = 1
            is_name_positional = True
        elif 'name_or_path' in kwargs:
            name_or_path = kwargs['name_or_path']
            is_name_positional = False
        
        # Handle mmproj_path parameter
        mmproj_path = None
        if 'mmproj_path' in kwargs:
            mmproj_path = kwargs['mmproj_path']
        
        # If neither parameter is found, call original function
        if name_or_path is None and mmproj_path is None:
            return func(*args, **kwargs)
        
        # Download name_or_path if needed
        if name_or_path is not None:
            try:
                downloaded_name_path = _download_model_if_needed(
                    name_or_path, 'name_or_path', progress_callback, token, **kwargs
                )
                
                # Replace name_or_path with downloaded path
                if is_name_positional:
                    if name_path_index is not None:
                        args_list[name_path_index] = downloaded_name_path
                        args = tuple(args_list)
                else:
                    kwargs['name_or_path'] = downloaded_name_path
                    
            except Exception as e:
                raise e  # Re-raise the error from _download_model_if_needed
        
        # Download mmproj_path if needed
        if mmproj_path is not None:
            try:
                downloaded_mmproj_path = _download_model_if_needed(
                    mmproj_path, 'mmproj_path', progress_callback, token, is_mmproj=True, **kwargs
                )
                
                # Replace mmproj_path with downloaded path
                kwargs['mmproj_path'] = downloaded_mmproj_path
                
            except Exception as e:
                raise e  # Re-raise the error from _download_model_if_needed
        
        # Call original function with updated paths (outside try-catch to let model creation errors bubble up)
        return func(*args, **kwargs)
    
    return wrapper
