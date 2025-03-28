from fastapi import APIRouter

router = APIRouter()

@router.post("/api/logs")
async def receive_log(data: dict):
    print(data)
    return {"status": "success", "message": "Log received"}