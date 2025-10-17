"""
Ripgrep-based filtering engine for MCPlaywright responses.
"""

import asyncio
import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple, Union, AsyncIterator
from pathlib import Path
import tempfile
import logging

from .models import UniversalFilterParams, FilterMode, FilterResult, FilterableField

logger = logging.getLogger(__name__)


class RipgrepFilterEngine:
    """
    High-performance filtering engine using ripgrep for MCPlaywright responses.
    
    This engine converts structured data to searchable text formats,
    applies ripgrep filtering, and reconstructs the filtered response
    while preserving the original data structure.
    """
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "mcplaywright_filtering"
        self.temp_dir.mkdir(exist_ok=True)
        
    async def filter_response(
        self,
        data: Any,
        filter_params: UniversalFilterParams,
        filterable_fields: List[str],
        content_fields: Optional[List[str]] = None
    ) -> FilterResult:
        """
        Apply ripgrep filtering to response data.
        
        Args:
            data: The response data to filter
            filter_params: Filtering parameters
            filterable_fields: Fields that can be searched
            content_fields: Fields containing large text content
            
        Returns:
            FilterResult with filtered data and metadata
        """
        start_time = time.time()
        
        # Determine which fields to search
        fields_to_search = self._determine_search_fields(
            filter_params.filter_fields,
            filterable_fields,
            content_fields or []
        )
        
        # Prepare searchable content
        searchable_items = self._prepare_searchable_content(data, fields_to_search)
        
        # Execute ripgrep filtering
        filtered_results = await self._execute_ripgrep_filtering(
            searchable_items,
            filter_params
        )
        
        # Reconstruct filtered response
        filtered_data = self._reconstruct_response(
            data,
            filtered_results,
            filter_params.filter_mode
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        return FilterResult(
            filtered_data=filtered_data,
            match_count=filtered_results["total_matches"],
            total_items=len(searchable_items) if isinstance(searchable_items, list) else 1,
            filtered_items=len(filtered_results["matching_items"]),
            filter_summary={
                "pattern": filter_params.filter_pattern,
                "mode": filter_params.filter_mode,
                "fields_searched": fields_to_search,
                "case_sensitive": filter_params.case_sensitive,
                "whole_words": filter_params.whole_words,
                "invert_match": filter_params.invert_match,
                "context_lines": filter_params.context_lines
            },
            execution_time_ms=execution_time,
            pattern_used=filter_params.filter_pattern,
            fields_searched=fields_to_search
        )
    
    def _determine_search_fields(
        self,
        requested_fields: Optional[List[str]],
        available_fields: List[str],
        content_fields: List[str]
    ) -> List[str]:
        """Determine which fields to search based on parameters and availability."""
        if requested_fields:
            # Validate requested fields are available
            invalid_fields = set(requested_fields) - set(available_fields)
            if invalid_fields:
                logger.warning(f"Requested fields not available: {invalid_fields}")
            return [f for f in requested_fields if f in available_fields]
        
        # Default to content fields if available, otherwise all fields
        return content_fields if content_fields else available_fields
    
    def _prepare_searchable_content(
        self,
        data: Any,
        fields_to_search: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Convert response data to searchable format.
        
        Returns list of items with searchable text and metadata.
        """
        if isinstance(data, dict):
            # Handle dictionary response (single item)
            return [self._extract_searchable_fields(data, fields_to_search, 0)]
        elif isinstance(data, list):
            # Handle list response (multiple items)
            return [
                self._extract_searchable_fields(item, fields_to_search, idx)
                for idx, item in enumerate(data)
            ]
        else:
            # Handle primitive response
            return [{
                "index": 0,
                "searchable_text": str(data),
                "original_data": data,
                "fields_found": ["_value"]
            }]
    
    def _extract_searchable_fields(
        self,
        item: Dict[str, Any],
        fields_to_search: List[str],
        item_index: int
    ) -> Dict[str, Any]:
        """Extract searchable text from specified fields in an item."""
        searchable_parts = []
        fields_found = []
        
        for field in fields_to_search:
            value = self._get_nested_field_value(item, field)
            if value is not None:
                # Convert value to searchable text
                text_value = self._value_to_searchable_text(value)
                if text_value:
                    searchable_parts.append(f"{field}:{text_value}")
                    fields_found.append(field)
        
        return {
            "index": item_index,
            "searchable_text": " ".join(searchable_parts),  # Use space separator instead of newlines
            "original_data": item,
            "fields_found": fields_found
        }
    
    def _get_nested_field_value(self, item: Dict[str, Any], field_path: str) -> Any:
        """Get value from nested field using dot notation."""
        try:
            value = item
            for part in field_path.split("."):
                if isinstance(value, dict):
                    value = value.get(part)
                elif isinstance(value, list) and part.isdigit():
                    value = value[int(part)]
                else:
                    return None
            return value
        except (KeyError, IndexError, TypeError):
            return None
    
    def _value_to_searchable_text(self, value: Any) -> str:
        """Convert any value to searchable text format."""
        if isinstance(value, str):
            return value
        elif isinstance(value, (int, float, bool)):
            return str(value)
        elif isinstance(value, dict):
            # Convert dict to JSON for searching
            return json.dumps(value, separators=(',', ':'))
        elif isinstance(value, list):
            # Convert list elements to searchable text
            return " ".join(self._value_to_searchable_text(item) for item in value)
        else:
            return str(value)
    
    async def _execute_ripgrep_filtering(
        self,
        searchable_items: List[Dict[str, Any]],
        filter_params: UniversalFilterParams
    ) -> Dict[str, Any]:
        """Execute ripgrep filtering on searchable content."""
        
        # Create temporary file with searchable content
        temp_file = self.temp_dir / f"search_{int(time.time() * 1000)}.txt"
        
        try:
            # Write searchable content to temporary file
            with open(temp_file, 'w', encoding='utf-8') as f:
                for item in searchable_items:
                    f.write(f"ITEM_INDEX:{item['index']}\n")
                    f.write(item['searchable_text'])
                    f.write("\n---ITEM_END---\n")
            
            # Build ripgrep command
            rg_cmd = self._build_ripgrep_command(filter_params, temp_file)
            
            # Execute ripgrep
            rg_results = await self._run_ripgrep_command(rg_cmd)
            
            # Process ripgrep results
            return self._process_ripgrep_results(
                rg_results,
                searchable_items,
                filter_params.filter_mode
            )
            
        finally:
            # Clean up temporary file
            if temp_file.exists():
                temp_file.unlink()
    
    def _build_ripgrep_command(
        self,
        filter_params: UniversalFilterParams,
        temp_file: Path
    ) -> List[str]:
        """Build ripgrep command with appropriate flags."""
        cmd = ["rg"]
        
        # Add pattern
        cmd.append(filter_params.filter_pattern)
        
        # Add flags based on parameters
        if not filter_params.case_sensitive:
            cmd.append("-i")
        
        if filter_params.whole_words:
            cmd.append("-w")
        
        if filter_params.invert_match:
            cmd.append("-v")
        
        if filter_params.multiline:
            cmd.extend(["-U", "--multiline-dotall"])
        
        # Context lines
        if filter_params.context_lines is not None:
            cmd.extend(["-C", str(filter_params.context_lines)])
        elif filter_params.context_before is not None:
            cmd.extend(["-B", str(filter_params.context_before)])
        elif filter_params.context_after is not None:
            cmd.extend(["-A", str(filter_params.context_after)])
        
        # Output format
        if filter_params.filter_mode == FilterMode.COUNT:
            cmd.append("-c")
        elif filter_params.filter_mode == FilterMode.FILES_WITH_MATCHES:
            cmd.append("-l")
        else:  # CONTENT mode
            cmd.extend(["-n", "--no-heading"])
        
        # Max matches
        if filter_params.max_matches:
            cmd.extend(["-m", str(filter_params.max_matches)])
        
        # Add file path
        cmd.append(str(temp_file))
        
        return cmd
    
    async def _run_ripgrep_command(self, cmd: List[str]) -> str:
        """Execute ripgrep command asynchronously."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode not in (0, 1):  # 1 is normal "no matches" exit code
                error_msg = stderr.decode()
                logger.warning(f"Ripgrep command failed: {error_msg}")
                raise ValueError(f"Ripgrep filtering failed: {error_msg}")
            
            return stdout.decode('utf-8', errors='replace')
            
        except FileNotFoundError:
            logger.error("ripgrep not found. Please install ripgrep for filtering functionality.")
            return ""
        except ValueError:
            # Re-raise ValueError (regex errors, etc.) so decorator can handle gracefully
            raise
        except Exception as e:
            logger.error(f"Error running ripgrep: {e}")
            return ""
    
    def _process_ripgrep_results(
        self,
        rg_output: str,
        searchable_items: List[Dict[str, Any]],
        mode: FilterMode
    ) -> Dict[str, Any]:
        """Process ripgrep output and extract matching item indices."""
        
        if not rg_output.strip():
            return {
                "matching_items": [],
                "total_matches": 0,
                "match_details": {}
            }
        
        matching_indices = set()
        match_details = {}
        total_matches = 0
        
        if mode == FilterMode.COUNT:
            # Count mode - just count total matches
            total_matches = sum(int(line) for line in rg_output.strip().split('\n') if line.isdigit())
            
        else:
            # Extract item indices from ripgrep output with line numbers
            for line in rg_output.split('\n'):
                if not line.strip():
                    continue
                
                # Parse line number and content from ripgrep output (format: "line_num:content")
                line_match = re.match(r'^(\d+):(.+)$', line)
                if line_match:
                    line_number = int(line_match.group(1))
                    content = line_match.group(2).strip()
                    
                    # Calculate item index based on file structure:
                    # Line 1: ITEM_INDEX:0, Line 2: content, Line 3: ---ITEM_END---
                    # Line 4: ITEM_INDEX:1, Line 5: content, Line 6: ---ITEM_END---
                    # So content lines are: 2, 5, 8, ... = 3*n + 2 where n is item_index
                    # Therefore: item_index = (line_number - 2) // 3
                    if (line_number - 2) % 3 == 0 and line_number >= 2:
                        item_index = (line_number - 2) // 3
                        matching_indices.add(item_index)
                        
                        if item_index not in match_details:
                            match_details[item_index] = []
                        
                        match_details[item_index].append(content)
                        total_matches += 1
        
        # Get matching items
        matching_items = [
            searchable_items[i] for i in matching_indices
            if i < len(searchable_items)
        ]
        
        return {
            "matching_items": matching_items,
            "total_matches": total_matches,
            "match_details": match_details
        }
    
    def _reconstruct_response(
        self,
        original_data: Any,
        filtered_results: Dict[str, Any],
        mode: FilterMode
    ) -> Any:
        """Reconstruct the filtered response maintaining original structure."""
        
        if mode == FilterMode.COUNT:
            # Return count information
            return {
                "total_matches": filtered_results["total_matches"],
                "matching_items_count": len(filtered_results["matching_items"]),
                "original_item_count": (
                    len(original_data) if isinstance(original_data, list) else 1
                )
            }
        
        matching_items = filtered_results["matching_items"]
        
        if not matching_items:
            # Return empty result in same structure as original
            return [] if isinstance(original_data, list) else None
        
        if isinstance(original_data, list):
            # Return filtered list
            return [item["original_data"] for item in matching_items]
        
        elif isinstance(original_data, dict):
            # Return the single item if it matched
            return matching_items[0]["original_data"] if matching_items else None
        
        else:
            # Return the primitive value if it matched
            return matching_items[0]["original_data"] if matching_items else None
    
    async def filter_streaming_response(
        self,
        data_iterator: AsyncIterator[Any],
        filter_params: UniversalFilterParams,
        filterable_fields: List[str],
        chunk_size: int = 100
    ) -> AsyncIterator[FilterResult]:
        """
        Filter large responses in streaming chunks to avoid memory issues.
        
        This is useful for very large datasets that might not fit in memory.
        """
        chunk = []
        async for item in data_iterator:
            chunk.append(item)
            
            if len(chunk) >= chunk_size:
                # Process chunk
                result = await self.filter_response(
                    chunk,
                    filter_params,
                    filterable_fields
                )
                yield result
                chunk = []
        
        # Process remaining items
        if chunk:
            result = await self.filter_response(
                chunk,
                filter_params,
                filterable_fields
            )
            yield result