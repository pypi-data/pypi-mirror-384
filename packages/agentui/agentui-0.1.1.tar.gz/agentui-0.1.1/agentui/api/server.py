from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any
import base64
import json
import os

from ..core.workflow import Workflow
from ..core.registry import registry


app = FastAPI(title="AgentUI Workflow API", version="1.0.0")

# Enable CORS for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WorkflowRequest(BaseModel):
    workflow: Dict[str, Any]


class ExecuteResponse(BaseModel):
    success: bool
    results: Dict[str, Any] = None
    error: str = None


@app.get("/api/")
async def root():
    return {"message": "AgentUI Workflow API"}


@app.get("/api/tools")
async def get_available_tools():
    """Get all available tool types and their information"""
    return registry.get_all_tool_info()


@app.post("/api/workflow/execute", response_model=ExecuteResponse)
async def execute_workflow(request: WorkflowRequest):
    """Execute a workflow from JSON definition"""
    try:
        # Create workflow from JSON
        workflow_json = json.dumps(request.workflow)
        workflow = Workflow.from_json(workflow_json, registry.get_all_types())

        # Execute workflow
        results = workflow.execute()

        # Convert PIL Images to base64 for JSON serialization
        serializable_results = {}
        for tool_id, result in results.items():
            serializable_results[tool_id] = {
                'type': result['type'],
                'outputs': {}
            }
            for output_name, output_value in result['outputs'].items():
                if hasattr(output_value, 'save'):  # PIL Image
                    # Convert to base64
                    import io
                    buffer = io.BytesIO()
                    output_value.save(buffer, format='JPEG')
                    img_str = base64.b64encode(buffer.getvalue()).decode()
                    serializable_results[tool_id]['outputs'][output_name] = f"data:image/jpeg;base64,{img_str}"
                elif hasattr(output_value, 'to_dict'):  # PixelFlow Detections or similar
                    serializable_results[tool_id]['outputs'][output_name] = output_value.to_dict()
                else:
                    serializable_results[tool_id]['outputs'][output_name] = output_value

        return ExecuteResponse(success=True, results=serializable_results)

    except Exception as e:
        return ExecuteResponse(success=False, error=str(e))


@app.post("/api/workflow/validate")
async def validate_workflow(request: WorkflowRequest):
    """Validate a workflow without executing it"""
    try:
        workflow_json = json.dumps(request.workflow)
        workflow = Workflow.from_json(workflow_json, registry.get_all_types())

        # Try to get execution order (this validates the DAG)
        execution_order = workflow.get_execution_order()

        return {"valid": True, "execution_order": execution_order}

    except Exception as e:
        return {"valid": False, "error": str(e)}


@app.post("/api/upload/image")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image and return base64 encoded data"""
    try:
        contents = await file.read()
        base64_data = base64.b64encode(contents).decode('utf-8')

        return {
            "filename": file.filename,
            "data": base64_data,
            "content_type": file.content_type
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Serve static files (for the web UI) - MUST be mounted last
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()