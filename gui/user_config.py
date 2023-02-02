import os
import json


class UserConfig:
    def __init__(self):
        if os.path.isfile("up_config.json"):
            with open("up_config.json", "r", encoding="utf8") as f:
                self.data = json.load(f)
        else:
            self.data = {}

        self.orig_jp_path = self.data.get("orig_jp_path", "")
        self.orig_local_path = self.data.get("orig_local_path", "")
        self.new_jp_path = self.data.get("new_jp_path", "")
        self.orig_jp_textdata_path = self.data.get("orig_jp_textdata_path", "")
        self.new_jp_textdata_path = self.data.get("new_jp_textdata_path", "")
        self.compare_text_data = self.data.get("compare_text_data", True)
        self.compare_stories = self.data.get("compare_stories", True)
        self.save_new = self.data.get("save_new", True)

    def save_data(self):
        self.data.update({
            "orig_jp_path": self.orig_jp_path,
            "orig_local_path": self.orig_local_path,
            "new_jp_path": self.new_jp_path,
            "orig_jp_textdata_path": self.orig_jp_textdata_path,
            "new_jp_textdata_path": self.new_jp_textdata_path,
            "compare_text_data": self.compare_text_data,
            "compare_stories": self.compare_stories,
            "save_new": self.save_new
        })
        with open("up_config.json", "w", encoding="utf8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)


user_config = UserConfig()