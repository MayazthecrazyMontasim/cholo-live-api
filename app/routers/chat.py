from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(
    prefix="/chat",
    tags=["Travis AI Interface"]
)

class ChatRequest(BaseModel):
    message: str
    context: dict

class ChatResponse(BaseModel):
    reply: str

@router.post("/travis", response_model=ChatResponse)
def chat_with_travis(request: ChatRequest):
    message = request.message.lower()
    
    if "budget" in message:
        return {"reply": "Hi! Travis here. Based on your inputs, sticking to local transport like CNG auto-rickshaws can slice 10% off your projected transport costs. Want me to apply this?"}
    elif "hotel" in message or "stay" in message:
        return {"reply": "For your selected destination, I noticed several eco-friendly budget stays in your price range. Keep an eye out for places with 'Budget' tags."}
    else:
        return {"reply": f"Travis here! I see you are planning a trip. Let me know if you need specific advice about budgeting or finding the right places."}
