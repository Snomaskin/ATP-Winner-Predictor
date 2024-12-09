from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from prediction_model import ApiRequestHandler


class PredictionRequest(BaseModel):
    player1: str
    player2: str
    court_surface: str

class StatsLookupRequest(BaseModel):
    player: str


@asynccontextmanager
async def lifespan(app: FastAPI):
        handler = ApiRequestHandler()
        app.state.handler = handler
        yield

app = FastAPI(lifespan=lifespan)

origins = [    
    "https://storage.googleapis.com",
    "https://storage.cloud.google.com",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/predict_winner")
async def winner_prediction(request_data: PredictionRequest):
    try:
        predicted_winner_name = app.state.handler.prediction_request(request_data.player1, request_data.player2, request_data.court_surface)
        return PlainTextResponse(predicted_winner_name)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/lookup_player_stats")
async def player_stats_lookup(request_data: StatsLookupRequest):
    try:
        player_stats = app.state.handler.player_stats_lookup_request(request_data.player)
        return PlainTextResponse(player_stats)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    #port = int(os.environ.get("PORT", 8000))
    uvicorn.run("API:app", host="0.0.0.0", port=8080)