import asyncio
import json
import logging
from typing import Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn


class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]


class ToolCallResponse(BaseModel):
    success: bool
    result: Any
    error: str = None


app = FastAPI(title="Data Validation MCP Server", version="1.0.0")
logger = logging.getLogger(__name__)


@app.post("/call_tool", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    if request.tool_name != "validate_data":
        raise HTTPException(status_code=400, detail=f"Unknown tool: {request.tool_name}")
    
    try:
        result = await validate_data(request.arguments)
        return ToolCallResponse(success=True, result=result)
    except Exception as e:
        logger.error(f"Error in validate_data: {str(e)}")
        return ToolCallResponse(success=False, error=str(e))


async def validate_data(arguments: Dict[str, Any]) -> Dict[str, Any]:
    # Simulate validation logic
    data = arguments.get("data", {})
    
    # Basic validation checks
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "validated_data": data.copy(),
        "validation_timestamp": datetime.now().isoformat()
    }
    
    # Check for required fields
    required_fields = arguments.get("required_fields", [])
    for field in required_fields:
        if field not in data or data[field] is None:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Required field '{field}' is missing")
    
    # Check data types
    expected_types = arguments.get("expected_types", {})
    for field, expected_type in expected_types.items():
        if field in data:
            actual_type = type(data[field]).__name__
            if actual_type != expected_type:
                validation_results["valid"] = False
                validation_results["errors"].append(f"Field '{field}' expected {expected_type}, got {actual_type}")
    
    # Check value ranges
    value_ranges = arguments.get("value_ranges", {})
    for field, range_config in value_ranges.items():
        if field in data:
            value = data[field]
            if isinstance(value, (int, float)):
                if "min" in range_config and value < range_config["min"]:
                    validation_results["valid"] = False
                    validation_results["errors"].append(f"Field '{field}' value {value} below minimum {range_config['min']}")
                if "max" in range_config and value > range_config["max"]:
                    validation_results["valid"] = False
                    validation_results["errors"].append(f"Field '{field}' value {value} above maximum {range_config['max']}")
    
    # Check string formats
    string_formats = arguments.get("string_formats", {})
    for field, format_pattern in string_formats.items():
        if field in data:
            value = str(data[field])
            # Simple email validation
            if format_pattern == "email" and "@" not in value:
                validation_results["valid"] = False
                validation_results["errors"].append(f"Field '{field}' does not contain a valid email format")
            # Simple phone validation
            elif format_pattern == "phone" and not value.replace("-", "").replace("(", "").replace(")", "").replace(" ", "").isdigit():
                validation_results["warnings"].append(f"Field '{field}' may not be a valid phone number")
    
    # Simulate processing delay
    await asyncio.sleep(0.1)
    
    # Add data enrichment
    if validation_results["valid"]:
        validation_results["validated_data"]["validation_id"] = f"val_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        validation_results["validated_data"]["validation_status"] = "passed"
    
    return validation_results


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "validation_server"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)