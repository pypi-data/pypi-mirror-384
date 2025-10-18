from fastapi import FastAPI, Request
from pathlib import Path
import uvicorn
import json_repair
import asyncio
from .file import File
from .db import Db
import os

class Callback:

    def __init__(self, db:Db, port: int, destination_dir: Path, func: callable = None, gateway: bool = False):
        self.port = port
        self.app = FastAPI()
        self.destination_dir = destination_dir
        self.func = func
        self.db = db
        self.gateway = gateway

        # register routes
        self.app.post("/batch_processing_done")(self.callback)

    def _process_file_gemini(self, file_path: Path, db: Db) -> None:
        try:

            if file_path.suffix != ".jsonl" or not file_path.is_relative_to(Path("output/")):
                raise ValueError("File must be a .jsonl file and starts with output/")

            downloaded_file_path = File.download(
                google_storage_file_path=file_path,
                destination_dir=self.destination_dir
            )
            if not downloaded_file_path:
                raise Exception("Failed to download file from Google Cloud Storage")

            with open(downloaded_file_path, "r") as file:
                for line in file:
                    data = json_repair.loads(line)

                    # Skip if status is present (indicating an error)
                    if data.get("status"):
                        db.update_payload(
                            custom_id=data.get('custom_id'),
                            status="FAILED"
                        )
                        continue

                    response_brut = data.get("response")["candidates"][0]["content"][
                        "parts"
                    ][0]["text"]
                    response = (
                        response_brut.replace("```json", "").replace("```", "").strip()
                    )

                    db.update_payload(
                        custom_id=data.get('custom_id',''),
                        llm_response=response,
                        tokens=data.get("response")["usageMetadata"].get("totalTokenCount", 0),
                        status="DONE"
                    )

            os.remove(downloaded_file_path)

        except Exception as e:
            print(e)

    async def callback(self, request: Request):
        try:
            data = await request.json()
            file_path = data.get("name")

            if not file_path:
                raise ValueError("File path is required")
            
            # in case of multiple files in multiple collections
            request_db = self.db

            if self.gateway:
                collection_name = str(Path(file_path).parts[2]).split("_")[0]
                request_db = self.db.clone_db(batch_collection_name=collection_name)

            await asyncio.to_thread(
                self._process_file_gemini, Path(file_path), request_db
            )
            
            # custom func accepts : results as list and file Path
            if self.func:
                await asyncio.to_thread(self.func, Path(file_path))
            
            request_db.update_file(
                file_path=Path(f"{Path(file_path).parts[2]}.jsonl"),
                status="DONE"
            )

            local_file_path = self.destination_dir / Path(file_path).name
            local_file_path.unlink(missing_ok=True)

            return {"status": "success"}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def start_server(self):
        try:
            uvicorn.run(app=self.app, host="0.0.0.0", port=self.port)
        except Exception as e:
            print(e)
