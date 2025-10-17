from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LaunchRequest(BaseModel):
    speed: str


app = FastAPI(title="Launch rocket api")


@app.post("/launch")
async def launch(request: LaunchRequest):
    """
    Launch endpoint that accepts a POST request with name and optional description
    """
    try:
        logger.info(f"Received launch request with speed: {request.speed}")
        return {
            "status": "success",
            "data": {
                "speed": request.speed,
            },
        }
    except Exception as e:
        logger.error(f"Error during launch: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
