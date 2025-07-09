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


app = FastAPI(title="Data Processing MCP Server", version="1.0.0")
logger = logging.getLogger(__name__)


@app.post("/call_tool", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    if request.tool_name != "process_data":
        raise HTTPException(status_code=400, detail=f"Unknown tool: {request.tool_name}")
    
    try:
        result = await process_data(request.arguments)
        return ToolCallResponse(success=True, result=result)
    except Exception as e:
        logger.error(f"Error in process_data: {str(e)}")
        return ToolCallResponse(success=False, error=str(e))


async def process_data(arguments: Dict[str, Any]) -> Dict[str, Any]:
    # Simulate data processing
    data = arguments.get("data", {})
    processing_type = arguments.get("processing_type", "standard")
    
    # Simulate processing delay based on data size
    data_size = len(json.dumps(data))
    processing_delay = min(0.5, data_size / 1000)  # Max 0.5 seconds
    await asyncio.sleep(processing_delay)
    
    processed_data = data.copy()
    
    # Apply different processing based on type
    if processing_type == "standard":
        # Standard processing - add metadata and timestamps
        processed_data["processed_at"] = datetime.now().isoformat()
        processed_data["processing_id"] = f"proc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        processed_data["processing_type"] = "standard"
        
        # Transform data if needed
        if "name" in processed_data:
            processed_data["name"] = processed_data["name"].title()
        
        if "email" in processed_data:
            processed_data["email"] = processed_data["email"].lower()
    
    elif processing_type == "financial":
        # Financial processing - add security and compliance metadata
        processed_data["processed_at"] = datetime.now().isoformat()
        processed_data["processing_id"] = f"fin_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        processed_data["processing_type"] = "financial"
        processed_data["compliance_check"] = "passed"
        processed_data["security_level"] = "high"
        
        # Mask sensitive data
        if "account_number" in processed_data:
            account = str(processed_data["account_number"])
            processed_data["account_number_masked"] = f"****{account[-4:]}"
        
        if "ssn" in processed_data:
            ssn = str(processed_data["ssn"])
            processed_data["ssn_masked"] = f"***-**-{ssn[-4:]}"
    
    elif processing_type == "analytics":
        # Analytics processing - add statistics and insights
        processed_data["processed_at"] = datetime.now().isoformat()
        processed_data["processing_id"] = f"analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        processed_data["processing_type"] = "analytics"
        
        # Add analytics metadata
        processed_data["analytics"] = {
            "field_count": len(processed_data),
            "data_quality_score": 85,  # Simulated score
            "completeness": 0.9,
            "accuracy": 0.95
        }
    
    # Add processing statistics
    processing_stats = {
        "start_time": datetime.now().isoformat(),
        "processing_duration_ms": int(processing_delay * 1000),
        "data_size_bytes": data_size,
        "fields_processed": len(processed_data),
        "success": True
    }
    
    # Check for processing errors (simulate occasional failures)
    if arguments.get("simulate_failure", False):
        raise Exception("Simulated processing failure")
    
    return {
        "success": True,
        "processed_data": processed_data,
        "processing_stats": processing_stats,
        "message": f"Data processed successfully using {processing_type} processing"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "processing_server"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)