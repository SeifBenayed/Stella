import os
from langchain_core.language_models.llms import LLM


class FileUtils:

    def __init__(self, tmp_folder):
        self.tmp_folder = tmp_folder
        self.agent_scratchpad_path = os.path.join(tmp_folder, "scratchpad.txt")
        self.python_file_path = os.path.join(tmp_folder, "python_code.py")
        self.test_log_path = os.path.join(tmp_folder, "test.log")
        self.screenshot_path = os.path.join(tmp_folder, "tmp.png")
        self.html_path = os.path.join(tmp_folder, "tmp.html")
        self.feed_back_file_path = os.path.join(tmp_folder, "feedback.txt")
        self.links_to_parse_json_path = os.path.join(tmp_folder, "links.json")
        self.agent_scratchpad_seperator = ""

    def set_seperator(self, tool_name):
        self.agent_scratchpad_seperator = f'''{tool_name}: =================================='''

    @staticmethod
    def common_utils(file_path: str, mode: str, txt=None) -> str:
        with open(file_path, mode) as fp:
            if mode == "r":
                txt = fp.read()
            else:
                fp.write(txt)
            fp.close()
        return txt

    def read_file(self, file_path: str) -> str:
        return self.common_utils(file_path, "r")

    def write_file(self, file_path: str, txt: str) -> str:
        return self.common_utils(file_path, "w", txt)

    def append_file(self, file_path: str, txt: str) -> str:
        return self.common_utils(file_path, "a", txt)

    def query_file_with_llm(self, file_path: str, llm: LLM, query) -> str:
        txt = self.common_utils(file_path, "r")
        return llm.invoke(query + "\n" + txt).content

    def append_to_agent_scratchpad(self, txt, tool_name):
        self.set_seperator(tool_name)
        self.append_file(self.agent_scratchpad_path, self.agent_scratchpad_seperator + "\n" + txt + "\n")

    def read_from_agent_scratchpad(self):
        return self.read_file(self.agent_scratchpad_path)

    def read_logs_append_to_agent_scratchpad(self):
        txt = self.read_file(self.test_log_path)
        self.append_to_agent_scratchpad("test_logs: \n"+ txt, "logs added")