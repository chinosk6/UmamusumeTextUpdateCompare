import os
import json

if not os.path.isdir("./save"):
    os.makedirs("./save")

class TextDataCompare:
    def __init__(self, orig_jp_path: str, orig_localized_path: str, new_jp_path: str):
        self.orig_jp_path = orig_jp_path
        self.orig_localized_path = orig_localized_path
        self.new_jp_path = new_jp_path

        self.target_file_names = [
            "character_system_text.json",
            "race_jikkyo_comment.json",
            "race_jikkyo_message.json",
            "text_data.json"
        ]

    @staticmethod
    def read_file_data(fname: str) -> dict:
        with open(fname, "r", encoding="utf8") as f:
            return json.load(f)

    def update_cmp_dict(self, new_dict_data: dict, orig_dict_data: dict, orig_local_dict: dict, fname: str):
        save_new_data = new_dict_data.copy()

        for k in new_dict_data:
            v = new_dict_data[k]
            if isinstance(v, str):
                orig_jp_v = orig_dict_data.get(k, None)
                orig_local_v = orig_local_dict.get(k, None)
                if v == orig_jp_v:
                    save_new_data[k] = v if not isinstance(orig_local_v, str) else orig_local_v
                else:
                    print(f"{fname} 有文本更新: {orig_jp_v} -> {v}")

            elif isinstance(v, dict):
                save_new_data[k].update(self.update_cmp_dict(
                    v, orig_dict_data.get(k, {}),
                    orig_local_dict.get(k, {}),
                    fname)
                )

            else:
                save_new_data[k] = v
                print(f"不支持的数据格式: {type(v)}")

        return save_new_data


    def start_compare(self, progress_callback=None, file_update_callback=None):
        total_count = len(self.target_file_names)
        for n, fname in enumerate(self.target_file_names):
            new_jp_data = self.read_file_data(f"{self.new_jp_path}/{fname}")
            orig_jp_data = self.read_file_data(f"{self.orig_jp_path}/{fname}")
            orig_local_data = self.read_file_data(f"{self.orig_localized_path}/{fname}")

            new_data = self.update_cmp_dict(new_jp_data, orig_jp_data, orig_local_data, fname)
            with open(f"./save/{fname}", "w", encoding="utf8") as f:
                f.write(json.dumps(new_data, ensure_ascii=False, indent=4))

            if progress_callback is not None:
                progress_callback(n + 1, total_count)
            if file_update_callback is not None:
                file_update_callback(0, f"./save/{fname}")
