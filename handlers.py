"""
Handlers for data querying, filtering, redaction and differential privacy
"""

import json
import re
import random
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Tuple, Union
import redis

# Initialize Redis client
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def query_archives(data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Query data from archives based on provided parameters
    
    Parameters:
    - data: Dict containing query parameters
        - query_type: str - Type of query (e.g., 'full', 'summary', 'count')
        - time_range: Dict - Start and end timestamps
        - filters: Dict - Key-value pairs for filtering
        - limit: int - Maximum number of results
        - offset: int - Pagination offset
        
    Returns:
    - Tuple of (response_data, status_code)
    """
    try:
        # Extract parameters
        query_type = data.get('query_type', 'full')
        time_range = data.get('time_range', {})
        filters = data.get('filters', {})
        limit = int(data.get('limit', 100))
        offset = int(data.get('offset', 0))
        
        # Validate time range
        start_time = time_range.get('start', 0)
        end_time = time_range.get('end', int(datetime.now().timestamp()))
        
        # Build Redis query
        # This is a simplified example - in a real application, 
        # you might use more sophisticated data storage and retrieval
        
        # Get keys for the date range
        keys = []
        current_time = start_time
        while current_time <= end_time:
            date_str = datetime.fromtimestamp(current_time).strftime('%Y-%m-%d')
            keys.append(f"archive:{date_str}")
            # Move to next day
            current_time += 86400  # seconds in a day
        
        # Fetch and filter data
        results = []
        for key in keys:
            if redis_client.exists(key):
                archive_data = redis_client.lrange(key, 0, -1)
                for item_json in archive_data:
                    try:
                        item = json.loads(item_json)
                        # Apply filters
                        if all(item.get(k) == v for k, v in filters.items()):
                            results.append(item)
                    except json.JSONDecodeError:
                        continue
        
        # Apply pagination
        paginated_results = results[offset:offset+limit]
        
        # Format based on query type
        if query_type == 'count':
            response = {'count': len(results)}
        elif query_type == 'summary':
            response = {
                'count': len(results),
                'summary': [{'id': item.get('id'), 'timestamp': item.get('timestamp')} 
                           for item in paginated_results]
            }
        else:  # full
            response = {
                'count': len(results),
                'data': paginated_results
            }
        
        return response, 200
        
    except Exception as e:
        return {"error": str(e)}, 500

def apply_filters(data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Apply advanced filtering to query results
    
    Parameters:
    - data: Dict containing:
        - results: List of result objects
        - filters: Dict containing filter rules:
            - include_fields: List of fields to include
            - exclude_fields: List of fields to exclude
            - field_rules: Dict of field-specific filters (e.g., range, regex)
    
    Returns:
    - Tuple of (filtered_data, status_code)
    """
    try:
        results = data.get('results', [])
        filters = data.get('filters', {})
        
        include_fields = filters.get('include_fields', [])
        exclude_fields = filters.get('exclude_fields', [])
        field_rules = filters.get('field_rules', {})
        
        filtered_results = []
        
        for item in results:
            # Apply field rules first
            item_passes = True
            
            for field, rules in field_rules.items():
                if field not in item:
                    item_passes = False
                    break
                    
                field_value = item[field]
                
                # Range filter
                if 'range' in rules:
                    range_rule = rules['range']
                    if 'min' in range_rule and field_value < range_rule['min']:
                        item_passes = False
                        break
                    if 'max' in range_rule and field_value > range_rule['max']:
                        item_passes = False
                        break
                
                # Regex filter
                if 'regex' in rules and not re.match(rules['regex'], str(field_value)):
                    item_passes = False
                    break
                    
                # List membership
                if 'in' in rules and field_value not in rules['in']:
                    item_passes = False
                    break
            
            if not item_passes:
                continue
                
            # Create filtered item with selected fields
            filtered_item = {}
            
            if include_fields:
                # Only include specified fields
                for field in include_fields:
                    if field in item:
                        filtered_item[field] = item[field]
            else:
                # Include all fields except excluded ones
                filtered_item = {k: v for k, v in item.items() if k not in exclude_fields}
            
            filtered_results.append(filtered_item)
        
        return {'filtered_data': filtered_results, 'count': len(filtered_results)}, 200
        
    except Exception as e:
        return {"error": str(e)}, 500

def redact_names(data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Redact personal names from the data
    
    Parameters:
    - data: Dict containing:
        - results: List of result objects
        - fields_to_redact: List of fields that may contain names
        - redaction_character: Character to use for redaction (default: '*')
        - preserve_length: Whether to preserve the length of redacted names
    
    Returns:
    - Tuple of (redacted_data, status_code)
    """
    try:
        results = data.get('results', [])
        fields_to_redact = data.get('fields_to_redact', ['name', 'full_name', 'username'])
        redaction_char = data.get('redaction_character', '*')
        preserve_length = data.get('preserve_length', True)
        
        # Name pattern - simplistic example, real implementation would be more sophisticated
        name_pattern = re.compile(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b')  # First Last format
        
        redacted_results = []
        
        for item in results:
            redacted_item = {}
            
            for key, value in item.items():
                if key in fields_to_redact and isinstance(value, str):
                    # Direct field redaction
                    if preserve_length:
                        redacted_value = redaction_char * len(value)
                    else:
                        redacted_value = '[REDACTED]'
                    redacted_item[key] = redacted_value
                    
                elif isinstance(value, str) and not key in fields_to_redact:
                    # Scan other text fields for names
                    redacted_value = name_pattern.sub('[REDACTED]', value)
                    redacted_item[key] = redacted_value
                    
                else:
                    # Keep non-text or non-redacted fields as is
                    redacted_item[key] = value
                    
            redacted_results.append(redacted_item)
        
        return {'redacted_data': redacted_results, 'count': len(redacted_results)}, 200
        
    except Exception as e:
        return {"error": str(e)}, 500

def add_differential_privacy(data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Add differential privacy noise to numeric data
    
    Parameters:
    - data: Dict containing:
        - results: List of result objects or aggregated values
        - numeric_fields: List of numeric fields to protect
        - epsilon: Privacy parameter (smaller = more privacy)
        - sensitivity: Sensitivity of the query
    
    Returns:
    - Tuple of (privacy_protected_data, status_code)
    """
    try:
        results = data.get('results', [])
        numeric_fields = data.get('numeric_fields', [])
        epsilon = float(data.get('epsilon', 1.0))
        sensitivity = float(data.get('sensitivity', 1.0))
        
        # Validate epsilon (privacy budget)
        if epsilon <= 0:
            return {"error": "Epsilon must be positive"}, 400
            
        # Determine if results is a list of objects or a single aggregate object
        if isinstance(results, list):
            # List of objects - add noise to each numeric field in each object
            noisy_results = []
            
            for item in results:
                noisy_item = {}
                
                for key, value in item.items():
                    if key in numeric_fields and isinstance(value, (int, float)):
                        # Add Laplace noise
                        scale = sensitivity / epsilon
                        noise = np.random.laplace(0, scale)
                        noisy_value = value + noise
                        
                        # Round to appropriate precision if integer
                        if isinstance(value, int):
                            noisy_value = int(round(noisy_value))
                            
                        noisy_item[key] = noisy_value
                    else:
                        noisy_item[key] = value
                        
                noisy_results.append(noisy_item)
                
            result = {'privacy_protected_data': noisy_results, 'count': len(noisy_results)}
            
        else:
            # Aggregate object (e.g., counts, sums) - add noise to specified fields
            noisy_results = {}
            
            for key, value in results.items():
                if key in numeric_fields and isinstance(value, (int, float)):
                    # Add Laplace noise
                    scale = sensitivity / epsilon
                    noise = np.random.laplace(0, scale)
                    noisy_value = value + noise
                    
                    # Round to appropriate precision if integer
                    if isinstance(value, int):
                        noisy_value = int(round(noisy_value))
                        
                    noisy_results[key] = noisy_value
                else:
                    noisy_results[key] = value
                    
            result = {'privacy_protected_data': noisy_results}
        
        # Add metadata about privacy protection
        result['privacy_metadata'] = {
            'epsilon': epsilon,
            'sensitivity': sensitivity,
            'mechanism': 'Laplace'
        }
        
        return result, 200
        
    except Exception as e:
        return {"error": str(e)}, 500

def combined_query_with_privacy(data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Combined function that queries, filters, redacts, and adds differential privacy
    
    Parameters:
    - data: Dict containing all parameters for the component functions
    
    Returns:
    - Tuple of (processed_data, status_code)
    """
    try:
        # Step 1: Query archives
        query_data = {
            'query_type': data.get('query_type', 'full'),
            'time_range': data.get('time_range', {}),
            'filters': data.get('query_filters', {}),
            'limit': data.get('limit', 100),
            'offset': data.get('offset', 0)
        }
        
        query_result, status = query_archives(query_data)
        
        if status != 200:
            return query_result, status
            
        # Step 2: Apply filters
        filter_data = {
            'results': query_result.get('data', []),
            'filters': data.get('filters', {})
        }
        
        filtered_result, status = apply_filters(filter_data)
        
        if status != 200:
            return filtered_result, status
            
        # Step 3: Redact names
        redact_data = {
            'results': filtered_result.get('filtered_data', []),
            'fields_to_redact': data.get('fields_to_redact', []),
            'redaction_character': data.get('redaction_character', '*'),
            'preserve_length': data.get('preserve_length', True)
        }
        
        redacted_result, status = redact_names(redact_data)
        
        if status != 200:
            return redacted_result, status
            
        # Step 4: Add differential privacy
        privacy_data = {
            'results': redacted_result.get('redacted_data', []),
            'numeric_fields': data.get('numeric_fields', []),
            'epsilon': data.get('epsilon', 1.0),
            'sensitivity': data.get('sensitivity', 1.0)
        }
        
        privacy_result, status = add_differential_privacy(privacy_data)
        
        return privacy_result, status
        
    except Exception as e:
        return {"error": str(e)}, 500