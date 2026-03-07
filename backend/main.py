from typing import Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="ThingSpeak Backend")


class ThingSpeakWritePayload(BaseModel):
    write_api_key: str
    field1: str
    field2: str


@app.get("/")
def health() -> dict:
    return {"message": "Backend is running"}


@app.get("/thingspeak")
def get_thingspeak_data(
    channel_id: int = Query(..., gt=0),
    read_api_key: Optional[str] = Query(default=None),
    results: int = Query(default=10, ge=1, le=8000),
) -> dict:
    params = {"results": results}
    if read_api_key:
        params["api_key"] = read_api_key

    base_url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.json"
    url = f"{base_url}?{urlencode(params)}"

    try:
        with urlopen(url, timeout=10) as response:
            payload = response.read().decode("utf-8")
        return json.loads(payload)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch data from ThingSpeak: {exc}",
        ) from exc


@app.post("/thingspeak/send")
def send_thingspeak_data(payload: ThingSpeakWritePayload) -> dict:
    params = {
        "api_key": payload.write_api_key,
        "field1": payload.field1,
        "field2": payload.field2,
    }

    body = urlencode(params).encode("utf-8")
    request = Request(
        "https://api.thingspeak.com/update.json",
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urlopen(request, timeout=10) as response:
            raw_payload = response.read().decode("utf-8")
        return json.loads(raw_payload)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to send data to ThingSpeak: {exc}",
        ) from exc


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
