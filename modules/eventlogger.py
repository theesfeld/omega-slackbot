import json
from datetime import datetime

from modules.database import Database
from modules.logger import get_logger


class EventLogger:
    def __init__(self, body, app):
        self.logger = get_logger("EventLogger")
        self.body = body
        self.app = app
        self.db = Database()
        self.files_info = []

        self.parse_event_data()
        self.fetch_user_profile()
        if "files" in self.body.get("event", {}):
            self.handle_files()

    def parse_event_data(self):
        event = self.body.get("event", {})
        self.user_id = event.get("user") or event.get("user_id")
        self.channel_id = event.get("channel") or event.get("channel_id")
        self.event_type = event.get("type")
        self.event_ts = datetime.fromtimestamp(
            float(event.get("event_ts", 0))
        ).strftime("%Y-%m-%d %H:%M:%S")
        self.event_text = event.get("text", "")

    def fetch_user_profile(self):
        if self.user_id:
            response = self.app.client.users_profile_get(user=self.user_id)
            profile = response.get("profile", {})
            self.user_fname = profile.get("first_name", "")
            self.user_lname = profile.get("last_name", "")
            self.user_fullname = profile.get("real_name", "")
            self.user_email = profile.get("email", "")
        else:
            self.logger.warning("No user ID found in event.")

    def handle_files(self):
        files = self.body.get("event", {}).get("files", [])
        for file in files:
            file_id = file.get("id")
            file_info_response = self.app.client.files_info(file=file_id)
            file_info = file_info_response.get("file", {})
            self.files_info.append(
                {
                    "id": file_id,
                    "name": file_info.get("name"),
                    "url_private_download": file_info.get("url_private_download"),
                    "filetype": file_info.get("filetype"),
                    "size": file_info.get("size"),
                }
            )

    def log_event(self):
        body_json = json.dumps(self.body)
        files_json = json.dumps(self.files_info)
        params = (
            body_json,
            self.event_type,
            self.event_ts,
            self.event_text,
            self.user_id,
            self.channel_id,
            files_json,
            self.user_fname,
            self.user_lname,
            self.user_fullname,
            self.user_email,
        )
        query = """INSERT INTO slack_event_log 
                   (event_body, event_type, event_ts, event_text, user_id, 
                    channel_id, files_info, user_fname, user_lname, 
                    user_fullname, user_email) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""

        self.db.execute_query(query, params)
        self.logger.info(
            f"Logged event: {self.event_type} from {self.user_fullname} in channel {self.channel_id} at {self.event_ts}"
        )

        return query, params
