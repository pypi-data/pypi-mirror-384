import os
import json
import csv
import pandas as pd
from .utils import get_logger

class Storage:
    def __init__(self, json_path: str = "videos.json", csv_path: str = "video_index.csv", token_path="token.csv"):
        self.logger = get_logger()
        self.logger.info("Storage initialization started...")
        self.json_path = json_path
        self.csv_path = csv_path
        self.token_path = token_path

        # Initialize CSV index
        if os.path.exists(self.csv_path):
            self.index_df = pd.read_csv(self.csv_path)
        else:
            self.index_df = pd.DataFrame(columns=["videoId", "title"])
            self.index_df.to_csv(self.csv_path, index=False)

        # Ensure JSONL file exists
        if not os.path.exists(self.json_path):
            with open(self.json_path, "w", encoding="utf-8") as f:
                data = [{"name": "Youtube videos for Software Engineering education."}]
                f.write(json.dumps(data, ensure_ascii=False))

        self.logger.info("Storage initialization completed!")

    def load_existing_ids(self):
        if "videoId" in self.index_df.columns:
            return set(self.index_df["videoId"].astype(str))
        return set()
    
    def load_token_count(self, token: str) -> int:
        if os.path.exists(self.token_path):
            with open(self.token_path, newline='', encoding='utf-8') as f:
                for t, c in csv.reader(f):
                    if t == token:
                        return int(c)
        return 0

    def update_token_count(self, token: str, inc: int):
        data = {}
        if os.path.exists(self.token_path):
            with open(self.token_path, newline='', encoding='utf-8') as f:
                for t, c in csv.reader(f):
                    if t != "token":
                        data[t] = int(c)
        data[token] = data.get(token, 0) + inc
        with open(self.token_path, "w", newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(["token", "videoCount"])
            w.writerows(data.items())
        self.logger.info(f"Token count updated '{token}' : +{inc} -> {data[token]}")

    def append_record(self, data: dict):
        video_id = data.get("id") or data.get("videoId")
        snippet = data.get("snippet", {})
        title = snippet.get("title", "Untitled")

        if video_id in self.load_existing_ids():
            self.logger.info(f"Duplicate video skipped: {video_id}")
            return

        # Append to JSON (store full data)
        json_text = ",\n".join(json.dumps(obj) for obj in [data])
        with open(self.json_path, "rb+") as f:
            f.seek(0, os.SEEK_END)
            pos = f.tell()

            # Move backwards to find the last non-space character
            while pos > 0:
                pos -= 1
                f.seek(pos)
                if f.read(1) not in b" \n\r\t":
                    break

            f.seek(pos)
            last_char = f.read(1)

            if last_char == b']':
                # Move before the closing bracket
                f.seek(pos)
                # Check if there’s at least one object inside the array
                f.seek(pos - 1)
                prev_char = f.read(1)
                if prev_char != b'[':
                    f.write(b",\n")  # Add a comma only if array not empty
                f.write(json_text.encode())
                f.write(b"]")
            else:
                raise ValueError("File does not end with a JSON array ']'")

        # Append to CSV index
        new_row = pd.DataFrame([[video_id, title]], columns=["videoId", "title"])
        new_row.to_csv(self.csv_path, mode="a", header=False, index=False)

        # Reload index to keep state fresh
        self.index_df = pd.read_csv(self.csv_path)

        self.logger.info(f"Stored video: {video_id} | {title}", print_to="file")

    def append_records(self, records: list[dict]):
        for rec in records:
            self.append_record(rec)
        self.logger.info(f"Appended {len(records)} records to storage.")