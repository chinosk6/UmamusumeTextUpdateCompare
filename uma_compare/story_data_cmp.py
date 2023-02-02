import os
from .models import StorytimelineModel

if not os.path.isdir("./save/stories"):
    os.makedirs("./save/stories")


class StoryDataCompare:
    def __init__(self, orig_jp_path: str, orig_localized_path: str, new_jp_path: str):
        self.orig_jp_path = self.normpath(orig_jp_path)
        self.orig_localized_path = self.normpath(orig_localized_path)
        self.new_jp_path = self.normpath(new_jp_path)

        if not self.orig_localized_path.endswith("stories"):
            self.orig_localized_path += "/stories"
        self.file_update_callback = None

    @staticmethod
    def normpath(data: str):
        return os.path.normpath(data).replace("\\", "/")

    def call_callback(self, *args, **kwargs):
        if self.file_update_callback is not None:
            return self.file_update_callback(*args, **kwargs)

    def check_match(self, m1: StorytimelineModel, m2: StorytimelineModel, need_print=True):
        if len(m1.TextBlockList) != len(m2.TextBlockList):
            if need_print:
                print(f"文件格式不匹配: {m1.filename_full} 和 {m2.filename_full}")
                self.call_callback(2, m1.filename_full, {
                    m1.filename_full: f"文件格式不匹配: {m1.filename_full} 和 {m2.filename_full}\nTextBlockList 长度不符"
                })
            return False

        for n, i in enumerate(m1.TextBlockList):
            local_text_block = m2.TextBlockList[n]
            if (i is None) or (local_text_block is None):
                if (i is None) and (local_text_block is None):
                    continue
                else:
                    if need_print:
                        print(f"文件格式不匹配: {m1.filename_full} 和 {m2.filename_full}")
                        self.call_callback(2, m1.filename_full, {
                            m1.filename_full: f"文件格式不匹配: {m1.filename_full} 和 {m2.filename_full}\n"
                                              f"TextBlockList[{n}] 内容不符"
                        })
                    return False

            if len(i.ChoiceDataList) != len(local_text_block.ChoiceDataList):
                if need_print:
                    print(f"文件格式不匹配: {m1.filename_full} 和 {m2.filename_full}")
                    self.call_callback(2, m1.filename_full, {
                        m1.filename_full: f"文件格式不匹配: {m1.filename_full} 和 {m2.filename_full}\n"
                                          f"[{n}].ChoiceDataList 长度不符"
                    })
                return False
            if len(i.ColorTextInfoList) != len(local_text_block.ColorTextInfoList):
                if need_print:
                    print(f"文件格式不匹配: {m1.filename_full} 和 {m2.filename_full}")
                    self.call_callback(2, m1.filename_full, {
                        m1.filename_full: f"文件格式不匹配: {m1.filename_full} 和 {m2.filename_full}\n"
                                          f"[{n}].ColorTextInfoList 长度不符"
                    })
                return False
        return True

    def build_trans(self, orig_jp: StorytimelineModel, orig_local: StorytimelineModel, new_jp: StorytimelineModel):
        if not self.check_match(orig_jp, orig_local):
            new_jp.set_autosave(True)
            return {}
        new_is_match = self.check_match(orig_jp, new_jp, False)
        if not new_is_match:
            new_jp.set_autosave(True)
        # if new_jp.Title != orig_jp.Title:
        #     new_jp.set_autosave(True)

        ret = {}
        for n, i in enumerate(orig_jp.TextBlockList):
            if i is None:
                continue
            local_text_block = orig_local.TextBlockList[n]

            ret[i.Name] = local_text_block.Name
            ret[i.Text] = local_text_block.Text

            if new_is_match:
                if (i.Name != new_jp.TextBlockList[n].Name) or (i.Text != new_jp.TextBlockList[n].Text):
                    new_jp.set_autosave(True)

            for lIndex, m in enumerate(i.ChoiceDataList):
                ret[m] = local_text_block.ChoiceDataList[lIndex]
                if new_is_match:
                    if m != new_jp.TextBlockList[n].ChoiceDataList[lIndex]:
                        new_jp.set_autosave(True)
            for lIndex, m in enumerate(i.ColorTextInfoList):
                ret[m] = local_text_block.ColorTextInfoList[lIndex]
                if new_is_match:
                    if m != new_jp.TextBlockList[n].ColorTextInfoList[lIndex]:
                        new_jp.set_autosave(True)
        return ret

    def start_compare(self, save_new_file=False, progress_callback=None, file_update_callback=None):
        self.file_update_callback = file_update_callback
        file_nums = sum([len(files) for root, dirs, files in os.walk(self.new_jp_path)])
        n = 0
        for root, dirs, files in os.walk(self.new_jp_path):
            for f in files:
                n += 1
                full_new_jp_name = self.normpath(os.path.join(root, f))
                relative_path = full_new_jp_name.replace(self.new_jp_path, "")  # "/abc/def/ghi.json"
                full_orig_jp_name = f"{self.orig_jp_path}{relative_path}"
                full_orig_localized_name = f"{self.orig_localized_path}{relative_path}"

                full_new_jp = StorytimelineModel(full_new_jp_name, f"./save/stories{relative_path}")
                full_new_jp.set_save_callback(file_update_callback)
                try:
                    full_orig_jp = StorytimelineModel(full_orig_jp_name)
                    full_orig_localized = StorytimelineModel(full_orig_localized_name)

                    if full_new_jp.Title == full_orig_jp.Title:
                        full_new_jp.Title = full_orig_localized.Title
                    full_new_jp << self.build_trans(full_orig_jp, full_orig_localized, full_new_jp)
                except FileNotFoundError:
                    if save_new_file:
                        if not os.path.isdir("./save_new/stories"):
                            os.makedirs("./save_new/stories")
                        full_new_jp.save_data(save_name=f"./save_new/stories{relative_path}")
                    # print(f"新增文件: {full_new_jp_name}")
                    if file_update_callback is not None:
                        file_update_callback(1, full_new_jp_name if not save_new_file else f"./save_new/"
                                                                                           f"stories{relative_path}")
                finally:
                    if progress_callback is not None:
                        progress_callback(n, file_nums)
