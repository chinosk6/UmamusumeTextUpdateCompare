from typing import List, Optional, Callable
from pydantic import BaseModel
import json
import os

class TextBlockListItem(BaseModel):
    Name: str
    Text: str
    ChoiceDataList: List[str]
    ColorTextInfoList: List[str]


class StorytimelineModel(BaseModel):
    Title: str
    TextBlockList: List[Optional[TextBlockListItem]]

    filename_full: Optional[str]
    save_name: Optional[str] = None
    autosave: Optional[bool] = False
    is_list: Optional[bool] = False
    save_callback: Optional[Callable] = None

    def __init__(self, filename_full: str, save_name: Optional[str] = None):
        with open(filename_full, "r", encoding="utf8") as f:
            data = json.load(f)
        if isinstance(data, list):
            new_data = {
                "Title": "",
                "TextBlockList": [{
                    "Name": "",
                    "Text": i,
                    "ChoiceDataList": [],
                    "ColorTextInfoList": []
                } for i in data]
            }
            super().__init__(**new_data)
            self.is_list = True
        else:
            super().__init__(**data)
        self.filename_full = filename_full
        self.save_name = save_name

    def set_save_callback(self, func: Callable):
        self.save_callback = func

    def save_data(self, replace_orig=False, is_autosave=False, save_name: Optional[str] = None):
        if is_autosave:
            if not self.autosave:
                return

        if save_name is None:
            save_name = self.filename_full if (replace_orig or self.save_name is None) else self.save_name
        save_path = os.path.split(save_name)[0]
        if not os.path.isdir(save_path):
            os.makedirs(save_path)
        if self.is_list:
            save_data = [i.Text for i in self.TextBlockList]
        else:
            save_data = self.dict(exclude={"filename_full", "save_name", "autosave", "is_list", "save_callback"})
        with open(save_name, "w", encoding="utf8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=4)
        print(f"变更文件已保存: {save_name}")
        if self.save_callback is not None and is_autosave:
            self.save_callback(0, save_name)

    def set_autosave(self, value: bool):
        self.autosave = value

    def __lshift__(self, other):
        if not self.autosave:
            return

        has_change = False

        def get_trans(content):
            nonlocal has_change
            ret = other.get(content, None)
            if ret is not None:
                has_change = True
                return ret
            else:
                return content

        self.Title = get_trans(self.Title)
        for n, i in enumerate(self.TextBlockList):
            if i is None:
                continue
            self.TextBlockList[n].Name = get_trans(i.Name)
            self.TextBlockList[n].Text = get_trans(i.Text)
            for m, j in enumerate(i.ChoiceDataList):
                self.TextBlockList[n].ChoiceDataList[m] = get_trans(j)
            for m, j in enumerate(i.ColorTextInfoList):
                self.TextBlockList[n].ColorTextInfoList[m] = get_trans(j)

        # if has_change:
        self.save_data(is_autosave=True)
