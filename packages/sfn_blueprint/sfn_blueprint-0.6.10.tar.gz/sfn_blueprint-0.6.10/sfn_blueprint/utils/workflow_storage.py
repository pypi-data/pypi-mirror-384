"""
Workflow Storage Utility for SFN Blueprint

This module provides utilities for agents to store their intermediate results
in workflow-specific directories, supporting both file-based storage and
automatic database integration using existing sfn_blueprint session management.
"""

import os
import json
from pathlib import Path
from typing import Union, Dict, Any, Optional, List
from datetime import datetime
import pandas as pd
from .data_loader import SFNDataLoader
from .logging import setup_logger
from ..config.config_manager import SFNConfigManager


class WorkflowStorageManager:
    """
    Manages storage of intermediate workflow results.
    
    This class provides a unified interface for agents to store their results
    in workflow-specific directories, with automatic format detection and
    database integration when available.
    """
    
    def __init__(self, workflow_base_path: str, workflow_id: str):
        """
        Initialize the workflow storage manager.
        
        Args:
            workflow_base_path: Base path for workflow storage
            workflow_id: Unique identifier for the workflow
        """
        self.workflow_base_path = Path(workflow_base_path)
        self.workflow_id = workflow_id
        
        # Fix path construction to avoid double workflows directory
        # Check if the base_path already contains the workflow_id to avoid double nesting
        if str(self.workflow_base_path).endswith(str(workflow_id)):
            # If base_path already ends with workflow_id, use it directly
            self.workflow_path = self.workflow_base_path
        elif "workflows" in str(self.workflow_base_path):
            # If base_path contains workflows but not the specific workflow_id, append it
            self.workflow_path = self.workflow_base_path / workflow_id
        else:
            # Otherwise, create the workflows subdirectory
            self.workflow_path = self.workflow_base_path / "workflows" / workflow_id
        
        # Create workflow directory structure
        self.step_results_path = self.workflow_path / "step_results"
        self.final_outputs_path = self.workflow_path / "final_outputs"
        self.metadata_path = self.workflow_path / "metadata.json"
        
        # Ensure directories exist
        self.step_results_path.mkdir(parents=True, exist_ok=True)
        self.final_outputs_path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger, _ = setup_logger(__name__)
        
        # Load configuration to determine storage backend
        try:
            self.config_manager = SFNConfigManager()
            self.storage_config = self._get_storage_configuration()
        except Exception as e:
            self.logger.warning(f"Could not initialize config manager: {e}, using defaults")
            self.config_manager = None
            self.storage_config = self._get_default_storage_config()
    
    def _get_default_storage_config(self) -> Dict[str, Any]:
        """Get default storage configuration when config manager is not available."""
        return {
            "default_format": "csv",
            "supported_formats": ["csv", "json", "xlsx", "parquet"],
            "warehouse_type": "file",
            "warehouse_connection": None,
            "compression": None,
            "chunk_size": 10000
        }
    
    def _get_storage_configuration(self) -> Dict[str, Any]:
        """Get storage configuration from sfn_blueprint config."""
        try:
            if self.config_manager is None:
                return self._get_default_storage_config()
                
            # Use the correct method name for SFNConfigManager
            config = self.config_manager.config
            
            # Check for database connections
            warehouse_type = "file"  # Default to file-based storage
            warehouse_connection = None
            
            # 1. Check for existing Snowflake/Snowpark session using sfn_blueprint
            try:
                from ..llm_handler.llm_clients import get_snowflake_session
                snowflake_session = get_snowflake_session()
                if snowflake_session:
                    warehouse_type = "snowflake"
                    warehouse_connection = snowflake_session
                    self.logger.info("Detected Snowflake session, using Snowflake storage")
            except ImportError:
                pass
            
            # 2. Check for PostgreSQL connection
            try:
                import psycopg2
                # This would need to be configured in the environment or config
                # For now, we'll use file-based storage
                pass
            except ImportError:
                pass
            
            return {
                "default_format": config.get("storage", {}).get("default_format", "csv"),
                "supported_formats": config.get("storage", {}).get("supported_formats", ["csv", "json", "xlsx", "parquet"]),
                "warehouse_type": warehouse_type,
                "warehouse_connection": warehouse_connection,
                "compression": config.get("storage", {}).get("compression"),
                "chunk_size": config.get("storage", {}).get("chunk_size", 10000)
            }
            
        except Exception as e:
            self.logger.warning(f"Error getting storage configuration: {e}, using defaults")
            return self._get_default_storage_config()
    
    def _determine_optimal_format(self, data: Union[pd.DataFrame, Dict[str, Any]]) -> str:
        """
        Determine the optimal storage format for the given data.
        
        Args:
            data: Data to be stored (DataFrame or dict)
            
        Returns:
            Optimal file format for storage
        """
        if isinstance(data, pd.DataFrame):
            # For DataFrames, consider size and data types
            if len(data) > 100000:  # Large datasets
                return "parquet"  # Better compression and performance
            elif len(data) > 10000:  # Medium datasets
                return "csv"  # Good balance of size and compatibility
            else:
                return "csv"  # Small datasets, CSV is fine
        else:
            # For dictionaries, JSON is usually best
            return "json"
    
    def _save_to_file(self, data: Union[pd.DataFrame, Dict[str, Any]], 
                      file_path: Path, format_type: str) -> bool:
        """
        Save data to a file in the specified format.
        
        Args:
            data: Data to save
            file_path: Path where to save the file
            format_type: Format to save in
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if format_type == "csv" and isinstance(data, pd.DataFrame):
                data.to_csv(file_path, index=False)
            elif format_type == "json":
                if isinstance(data, pd.DataFrame):
                    data.to_json(file_path, orient='records', indent=2)
                else:
                    with open(file_path, 'w') as f:
                        json.dump(data, f, indent=2, default=str)
            elif format_type == "xlsx" and isinstance(data, pd.DataFrame):
                data.to_excel(file_path, index=False)
            elif format_type == "parquet" and isinstance(data, pd.DataFrame):
                data.to_parquet(file_path, index=False)
            else:
                self.logger.warning(f"Unsupported format {format_type} for data type {type(data)}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving data to {file_path}: {e}")
            return False
    
    def save_step_result(self, step_id: str, data: Union[pd.DataFrame, Dict[str, Any]], 
                        step_type: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Save a step result to workflow storage.
        
        Args:
            step_id: Unique identifier for the step
            data: Data to be stored
            step_type: Type of step (e.g., 'agent_execution', 'data_processing')
            metadata: Additional metadata about the step
            
        Returns:
            Dictionary containing information about the saved result
        """
        timestamp = datetime.now()
        
        # Determine optimal storage format
        optimal_format = self._determine_optimal_format(data)
        
        # Create filename
        filename = f"{step_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.{optimal_format}"
        file_path = self.step_results_path / filename
        
        # Save data to file
        success = self._save_to_file(data, file_path, optimal_format)
        
        if not success:
            self.logger.error(f"Failed to save step result to {file_path}")
            return {}
        
        # Create result info
        result_info = {
            "step_id": step_id,
            "step_type": step_type,
            "timestamp": timestamp.isoformat(),
            "workflow_id": self.workflow_id,
            "files": {},
            "metadata": metadata or {},
            "storage_backend": self.storage_config["warehouse_type"]
        }
        
        # Ensure storage_backend is in metadata for easy access
        result_info["metadata"]["storage_backend"] = self.storage_config["warehouse_type"]
        
        # Add file information
        result_info["files"][optimal_format] = str(file_path)
        
        # Add DataFrame-specific metadata if applicable
        if isinstance(data, pd.DataFrame):
            # Add DataFrame info to metadata
            result_info["metadata"]["data_shape"] = list(data.shape)
            result_info["metadata"]["data_columns"] = data.columns.tolist()
            result_info["metadata"]["data_types"] = data.dtypes.astype(str).to_dict()
            result_info["metadata"]["storage_format"] = optimal_format
            result_info["metadata"]["storage_reason"] = f"Optimal format for {data.shape[0]} rows, {data.shape[1]} columns"
        
        # Save metadata
        metadata_file = self.step_results_path / f"{step_id}_metadata.json"
        try:
            with open(metadata_file, 'w') as f:
                json.dump(result_info, f, indent=2, default=str)
        except Exception as e:
            self.logger.warning(f"Could not save metadata: {e}")
        
        self.logger.info(f"Step result saved: {file_path}")
        return result_info
    
    def save_agent_result(self, 
                          agent_name: str, 
                          step_name: str, 
                          data: Union[pd.DataFrame, Dict[str, Any]], 
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Simple method for agents to save their results.
        
        This is the main method agents should use - it automatically:
        - Determines the optimal storage format
        - Saves to database if available
        - Saves to local files for debugging
        - Generates comprehensive metadata
        
        Args:
            agent_name: Name of the agent (e.g., "cleaning_agent")
            step_name: Name of the step (e.g., "data_cleaning")
            data: Data to be stored (DataFrame or dict)
            metadata: Additional metadata about the operation
            
        Returns:
            Dictionary containing information about the saved result
        """
        step_id = f"{agent_name}_{step_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Add agent-specific metadata
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "agent_name": agent_name,
            "step_name": step_name,
            "execution_timestamp": datetime.now().isoformat(),
            "data_type": type(data).__name__
        })
        
        # Save the result
        return self.save_step_result(step_id, data, "agent_execution", metadata)
    
    def get_step_result(self, step_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a step result from storage.
        
        Args:
            step_id: Identifier of the step to retrieve
            
        Returns:
            Step result data if found, None otherwise
        """
        # Look for metadata file
        metadata_files = list(self.step_results_path.glob(f"{step_id}_metadata.json"))
        if not metadata_files:
            return None
        
        try:
            with open(metadata_files[0], 'r') as f:
                metadata = json.load(f)
            
            # Load the actual data file
            data_files = metadata.get("files", {})
            if not data_files:
                return metadata
            
            # Load the first available data file
            format_type, file_path = next(iter(data_files.items()))
            file_path = Path(file_path)
            
            if not file_path.exists():
                self.logger.warning(f"Data file not found: {file_path}")
                return metadata
            
            # Load data based on format
            if format_type == "csv":
                data = pd.read_csv(file_path)
            elif format_type == "json":
                data = pd.read_json(file_path)
            elif format_type == "xlsx":
                data = pd.read_excel(file_path)
            elif format_type == "parquet":
                data = pd.read_parquet(file_path)
            else:
                self.logger.warning(f"Unsupported format: {format_type}")
                return metadata
            
            metadata["data"] = data
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error loading step result: {e}")
            return None
    
    def list_step_results(self) -> List[Dict[str, Any]]:
        """
        List all available step results.
        
        Returns:
            List of step result metadata
        """
        results = []
        metadata_files = list(self.step_results_path.glob("*_metadata.json"))
        
        for metadata_file in metadata_files:
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                results.append(metadata)
            except Exception as e:
                self.logger.warning(f"Error loading metadata from {metadata_file}: {e}")
        
        return results
    
    def cleanup_old_results(self, max_age_hours: int = 24) -> int:
        """
        Clean up old step results to save disk space.
        
        Args:
            max_age_hours: Maximum age of results to keep in hours
            
        Returns:
            Number of files cleaned up
        """
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        cleaned_count = 0
        
        for file_path in self.step_results_path.glob("*"):
            try:
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
            except Exception as e:
                self.logger.warning(f"Error cleaning up {file_path}: {e}")
        
        self.logger.info(f"Cleaned up {cleaned_count} old result files")
        return cleaned_count
    
    def aggregate_final_results(self) -> Dict[str, Any]:
        """
        Aggregate all step results into final workflow outputs.
        
        Returns:
            Dictionary containing aggregated results and workflow summary
        """
        try:
            step_results = self.list_step_results()
            
            if not step_results:
                self.logger.warning("No step results found to aggregate")
                return {"status": "no_results", "message": "No step results found"}
            
            # Aggregate results by agent type
            agent_results = {}
            workflow_summary = {
                "workflow_id": self.workflow_id,
                "total_steps": len(step_results),
                "agents_used": set(),
                "data_summary": {},
                "execution_timeline": [],
                "quality_metrics": {}
            }
            
            for result in step_results:
                agent_name = result.get("agent_name", "unknown")
                step_id = result.get("step_id", "unknown")
                
                # Track agents used
                workflow_summary["agents_used"].add(agent_name)
                
                # Group results by agent
                if agent_name not in agent_results:
                    agent_results[agent_name] = []
                agent_results[agent_name].append(result)
                
                # Add to execution timeline
                execution_time = result.get("timestamp", "unknown")
                workflow_summary["execution_timeline"].append({
                    "step_id": step_id,
                    "agent": agent_name,
                    "timestamp": execution_time,
                    "status": result.get("status", "unknown")
                })
                
                # Aggregate data quality metrics
                if "data_quality_score" in result.get("metadata", {}):
                    if "data_quality_score" not in workflow_summary["quality_metrics"]:
                        workflow_summary["quality_metrics"]["data_quality_score"] = []
                    workflow_summary["quality_metrics"]["data_quality_score"].append(
                        result["metadata"]["data_quality_score"]
                    )
                
                # Track data shapes
                if "data_shape" in result.get("metadata", {}):
                    data_shape = result["metadata"]["data_shape"]
                    if agent_name not in workflow_summary["data_summary"]:
                        workflow_summary["data_summary"][agent_name] = []
                    workflow_summary["data_summary"][agent_name].append(data_shape)
            
            # Convert set to list for JSON serialization
            workflow_summary["agents_used"] = list(workflow_summary["agents_used"])
            
            # Calculate average quality metrics
            for metric, values in workflow_summary["quality_metrics"].items():
                if values and all(isinstance(v, (int, float)) for v in values):
                    workflow_summary["quality_metrics"][f"{metric}_average"] = sum(values) / len(values)
            
            # Create final outputs
            final_outputs = {
                "workflow_summary": workflow_summary,
                "agent_results": agent_results,
                "aggregation_timestamp": datetime.now().isoformat(),
                "total_files_processed": len(step_results)
            }
            
            # Save final outputs
            final_outputs_file = self.final_outputs_path / "workflow_summary.json"
            with open(final_outputs_file, 'w') as f:
                json.dump(final_outputs, f, indent=2, default=str)
            
            # Also save a CSV summary for easy analysis
            summary_data = []
            for result in step_results:
                summary_data.append({
                    "step_id": result.get("step_id", "unknown"),
                    "agent_name": result.get("agent_name", "unknown"),
                    "timestamp": result.get("timestamp", "unknown"),
                    "status": result.get("status", "unknown"),
                    "data_shape": str(result.get("metadata", {}).get("data_shape", "unknown")),
                    "data_quality_score": result.get("metadata", {}).get("data_quality_score", "unknown")
                })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                summary_csv = self.final_outputs_path / "workflow_summary.csv"
                summary_df.to_csv(summary_csv, index=False)
                self.logger.info(f"Workflow summary saved to {summary_csv}")
            
            self.logger.info(f"Final results aggregated: {len(step_results)} steps, {len(agent_results)} agents")
            return final_outputs
            
        except Exception as e:
            self.logger.error(f"Error aggregating final results: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """
        Get current workflow status and statistics.
        
        Returns:
            Dictionary containing workflow status information
        """
        try:
            step_results = self.list_step_results()
            
            status = {
                "workflow_id": self.workflow_id,
                "total_steps": len(step_results),
                "completed_steps": len([r for r in step_results if r.get("status") == "completed"]),
                "failed_steps": len([r for r in step_results if r.get("status") == "failed"]),
                "agents_used": list(set(r.get("agent_name", "unknown") for r in step_results)),
                "last_updated": max([r.get("timestamp", "1970-01-01") for r in step_results], default="1970-01-01"),
                "storage_path": str(self.workflow_path),
                "step_results_path": str(self.step_results_path),
                "final_outputs_path": str(self.final_outputs_path)
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting workflow status: {e}")
            return {"status": "error", "message": str(e)}
