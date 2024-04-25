from fastapi import FastAPI
from Wrapper import InputHandler
from pydantic import BaseModel

app = FastAPI()
handler = InputHandler()


class PredictionRequest(BaseModel):
    player1: str
    player2: str
    court_surface: str


@app.post("/winner_predict")
async def prediction_request(request_data: PredictionRequest):
    winner_name = handler.user_input(request_data.player1, request_data.player2, request_data.court_surface)
    
    return winner_name
