import string
import json

# 英數字符和常見符號集合
en_and_common_symbols = string.ascii_letters + string.digits + string.punctuation + ' '

class BaseLogEntry:
    def __init__(self, timestamp, domain_name, user_department, user_name, source_ip, session_id, action_type, developer, model, botrun, action_details=None, user_agent=None, resource_id=None):
        self.timestamp = timestamp
        self.domain_name = domain_name
        self.user_department = user_department
        self.user_name = user_name
        self.source_ip = source_ip
        self.session_id = session_id
        self.action_type = action_type
        self.developer = developer
        self.model = model
        self.botrun = botrun
        try:
            json_obj = json.loads(action_details)
            action_details = json.dumps(json_obj, ensure_ascii=False)
        except json.JSONDecodeError:
            pass
        self.action_details = action_details
        self.user_agent = user_agent
        self.resource_id = resource_id

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "domain_name": self.domain_name,
            "user_department": self.user_department,
            "user_name": self.user_name,
            "source_ip": self.source_ip,
            "session_id": self.session_id,
            "action_type": self.action_type,
            "action_details": self.action_details,
            "user_agent": self.user_agent,
            "resource_id": self.resource_id,
            "developer": self.developer,
            "model": self.model,
            "botrun": self.botrun,
        }

class TextLogEntry(BaseLogEntry):
    def __init__(self, timestamp, domain_name, user_department, user_name, source_ip, session_id, action_type, developer, model, botrun, action_details=None, user_agent=None, resource_id=None):
        super().__init__(timestamp, domain_name, user_department, user_name, source_ip, session_id, action_type, developer, model, botrun, action_details, user_agent, resource_id)
        self._calculate_characters()

    def _calculate_characters(self):
        # TODO: 新增各種計算規則
        if self.action_details is not None:
            self.ch_characters = self._calculate_ch_characters(self.action_details)
            self.en_characters = self._calculate_en_characters(self.action_details)
        else:
            self.ch_characters = 0
            self.en_characters = 0

        self.total_characters = self.ch_characters + self.en_characters

    def _calculate_ch_characters(self, str_detail):
        return sum(1 for char in str_detail if char not in en_and_common_symbols)

    def _calculate_en_characters(self, str_detail):
        return sum(1 for char in str_detail if char in en_and_common_symbols)

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "ch_characters": self.ch_characters,
            "en_characters": self.en_characters,
            "total_characters": self.total_characters,
        })
        return base_dict

class AudioLogEntry(BaseLogEntry):
    def __init__(self, timestamp, domain_name, user_department, user_name, source_ip, session_id, action_type, developer, model, botrun, file_size_mb, action_details=None, user_agent=None, resource_id=None):
        super().__init__(timestamp, domain_name, user_department, user_name, source_ip, session_id, action_type, developer, model, botrun, action_details, user_agent, resource_id)
        self.file_size_mb = file_size_mb

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "file_size_mb": self.file_size_mb,
        })
        return base_dict

class ImageLogEntry(BaseLogEntry):
    def __init__(self, timestamp, domain_name, user_department, user_name, source_ip, session_id, action_type, developer, model, botrun, img_size_mb, action_details=None, user_agent=None, resource_id=None):
        super().__init__(timestamp, domain_name, user_department, user_name, source_ip, session_id, action_type, developer, model, botrun, action_details, user_agent, resource_id)
        self.img_size_mb = img_size_mb

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "img_size_mb": self.img_size_mb,
        })
        return base_dict

class VectorDBLogEntry(BaseLogEntry):
    def __init__(self, timestamp, domain_name, user_department, user_name, source_ip, session_id, action_type, developer, model, botrun, page_num, action_details=None, user_agent=None, resource_id=None):
        super().__init__(timestamp, domain_name, user_department, user_name, source_ip, session_id, action_type, developer, model, botrun, action_details, user_agent, resource_id)
        self.page_num = page_num

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "page_num": self.page_num,
        })
        return base_dict