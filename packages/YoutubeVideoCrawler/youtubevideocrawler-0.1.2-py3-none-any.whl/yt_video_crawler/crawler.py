import time
from tqdm import tqdm
from .storage import Storage
from .utils import get_logger
from .utils import safe_sleep
from .utils import keyword_loader
from typing import List, Optional
from googleapiclient.discovery import build


class YouTubeCrawler:
    def __init__(
        self,
        api_key: str,
        output_json="videos.json",
        output_csv="video_index.csv",
        sleep_seconds: float = 2,
        api_service_name: str = "youtube",
        api_version: str = "v3",
    ):
        if not api_key:
            raise ValueError(
                "YouTube API key must be provided. See: https://console.cloud.google.com/apis/credentials"
            )

        self.logger = get_logger()
        self.logger.info("YouTubeCrawler initialization started...")
        self.api_key = api_key
        self.youtube = build(api_service_name, api_version, developerKey=api_key)
        self.storage = Storage(output_json, output_csv)
        self.sleep_seconds = sleep_seconds
        self.logger.info("YouTubeCrawler initialization completed!")

    def run(
        self,
        keywords: List[str] = [],
        search_mode: str = "single",
        fetch_comments: bool = False,
        keyword_start_index: int = 1,
        keyword_file: Optional[str] = None,
        max_per_keyword: Optional[int] = None,
    ):
        if keyword_file:
                keywords.extend(keyword_loader(keyword_file))
        if len(keywords) == 0:
            raise ValueError("No keywords provided for crawling.")
        existing = self.storage.load_existing_ids()
        self.logger.info(f"Loaded {len(existing)} existing video IDs")
        self.logger.info("=== Session Started ===")

        try:
            if search_mode == "multi":
                query = "|".join(keywords)
                self._crawl_for_keyword(query, existing, max_per_keyword, fetch_comments)
            else:
                if keyword_start_index < 1 or keyword_start_index > len(keywords):
                    raise ValueError("keyword_start_index is out of range.")
                for kw in keywords[keyword_start_index-1:]:
                    self._crawl_for_keyword(kw, existing, max_per_keyword, fetch_comments)
        except KeyboardInterrupt:
            self.logger.info("Stopped by user (Ctrl+C).")
        except Exception as e:
            self.logger.error(f"Unexpected error occurred: {e}", exc_info=True)
        finally:
            self.logger.info("=== Session Ended ===")
            self.logger.info(
                f"Total unique videos stored: {len(self.storage.load_existing_ids())}"
            )

    def _crawl_for_keyword(
        self, keyword: str, existing_ids: set, max_per_keyword: Optional[int], fetch_comments: bool
    ):
        total_fetched = self.storage.load_token_count(keyword)
        if total_fetched > 0:
            self.logger.info(f"Starting crawl for keyword: '{keyword}' (already fetched {total_fetched})")
        else:
            self.logger.info(f"Starting crawl for keyword: '{keyword}'")
        next_page_token = None

        while True:
            search_req = self.youtube.search().list(
                q=keyword,
                part="id",
                type="video",
                maxResults=50,
                pageToken=next_page_token,
            )
            search_res = search_req.execute()
            items = search_res.get("items", [])
            next_page_token = search_res.get("nextPageToken")

            if not items:
                self.logger.info(f"No results found for '{keyword}'.")
                break

            video_ids = [
                i["id"]["videoId"] for i in items if i["id"]["kind"] == "youtube#video"
            ]
            new_ids = [vid for vid in video_ids if vid not in existing_ids]

            if not new_ids:
                self.logger.info("All results are duplicates.")
                if not next_page_token:
                    break
                continue
            else:
                self.logger.info(f"{len(new_ids)} new videos found out of {len(video_ids)}.")

            safe_sleep(self.sleep_seconds, self.logger)
            video_data = self._fetch_video_details(new_ids, keyword, fetch_comments)
            self.storage.append_records(video_data)
            existing_ids.update(new_ids)
            total_fetched += len(new_ids)
            self.storage.update_token_count(keyword, len(new_ids))

            self.logger.info(
                f"Stored {len(video_data)} new videos, total={total_fetched} for '{keyword}'"
            )

            if not next_page_token:
                self.logger.info(f"No more videos for this {keyword}.")
                break

            if max_per_keyword:
                self.logger.info(f"{total_fetched}/{max_per_keyword} video(s) fetched.")
                if total_fetched >= max_per_keyword:
                    break
            safe_sleep(self.sleep_seconds, self.logger)

        self.logger.info(f"Keyword '{keyword}' done. Total fetched={total_fetched}")

    def _fetch_video_details(self, video_ids: List[str], kw: str = "", fetch_comments: bool = False):
        self.logger.info("Fetching video details and comments...")
        req = self.youtube.videos().list(
            part="contentDetails,id,liveStreamingDetails,localizations,paidProductPlacementDetails,recordingDetails,snippet,statistics,status,topicDetails",
            id=",".join(video_ids),
            maxResults=50,
        )
        res = req.execute()
        self.logger.info(f"Fetched video details for {len(res.get('items', []))} videos.")

        video_records = []

        for item in tqdm(res.get("items", []), desc="Fetching comments" if fetch_comments else "Processing videos", unit="video", dynamic_ncols=True):
            comments = self._fetch_comments(item["id"]) if fetch_comments else []
            video_records.append({**item, "comments": comments, "keyword": kw})

        return video_records

    def _fetch_comments(self, video_id: str):
        comments = []
        next_page_token = None
        page_count = 0
        total_comments = 0
        pbar = tqdm(
            desc=f"Comments for {video_id}",
            unit="page",
            leave=False,
            dynamic_ncols=True,
            bar_format="{l_bar} {n_fmt} pages | {postfix}"
        )

        while True:
            safe_sleep(self.sleep_seconds)
            req = self.youtube.commentThreads().list(
                part="id,snippet,replies",
                videoId=video_id,
                maxResults=50,
                pageToken=next_page_token,
                textFormat="plainText",
            )
            try:
                res = req.execute()
                new_items = res.get("items", [])
                comments.extend(new_items)
                page_count += 1
                total_comments += len(new_items)
                pbar.update(1)
                pbar.set_postfix_str(f"{total_comments} comments fetched")
            except Exception as e:
                self.logger.warning(f"Error fetching comments for {video_id}: {e}")
                break

            next_page_token = res.get("nextPageToken")
            if not next_page_token:
                break

        pbar.close()
        return comments

