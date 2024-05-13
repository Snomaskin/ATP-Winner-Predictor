from fastapi import FastAPI
from fastapi import HTTPException
from Wrapper import InputHandler
from pydantic import BaseModel
from uvicorn import run


app = FastAPI()
handler = InputHandler()


class PredictionRequest(BaseModel):
    player1: str
    player2: str
    court_surface: str


@app.post("/winner_predict")
async def prediction_request(request_data: PredictionRequest):
    try:
        winner_name = handler.user_input(request_data.player1, request_data.player2, request_data.court_surface)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return winner_name


if __name__ == "__main__":
    run("API:app", port=8000)