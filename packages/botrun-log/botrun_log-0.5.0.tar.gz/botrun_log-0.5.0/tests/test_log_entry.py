from botrun_log.log_entry import TextLogEntry, AudioLogEntry, ImageLogEntry, VectorDBLogEntry

def test_text_log_entry():
    log_entry = TextLogEntry(
        "2021-01-01T00:00:00Z", 'botrun.ai', "test_org", "user_1", "127.0.0.1", "session_1", "llm_input",
        "JcXGTcW", "gpt-4o", "波程.botrun", "~!@#$%^&*()_+台灣No.1", "user_agent", "resource_1"
    )
    assert log_entry.ch_characters == 2
    assert log_entry.en_characters == 17
    assert log_entry.total_characters == 19

    log_dict = log_entry.to_dict()
    assert log_dict["timestamp"] == "2021-01-01T00:00:00Z"
    assert log_dict["domain_name"] == "botrun.ai"
    assert log_dict["user_department"] == "test_org"
    assert log_dict["user_name"] == "user_1"
    assert log_dict["source_ip"] == "127.0.0.1"
    assert log_dict["session_id"] == "session_1"
    assert log_dict["action_type"] == "llm_input"
    assert log_dict["developer"] == "JcXGTcW"
    assert log_dict["action_details"] == "~!@#$%^&*()_+台灣No.1"
    assert log_dict["model"] == "gpt-4o"
    assert log_dict["botrun"] == "波程.botrun"
    assert log_dict["user_agent"] == "user_agent"
    assert log_dict["resource_id"] == "resource_1"
    assert log_dict["ch_characters"] == 2
    assert log_dict["en_characters"] == 17
    assert log_dict["total_characters"] == 19

def test_audio_log_entry():
    log_entry = AudioLogEntry(
        "2021-01-01T00:00:00Z", 'botrun.ai', "test_org", "user_1", "127.0.0.1", "session_1", "audio_upload",
        "JcXGTcW", "whisper-1", "波程.botrun", 20, "音檔上傳", "user_agent", "audio_1"
    )
    log_dict = log_entry.to_dict()
    assert log_dict["timestamp"] == "2021-01-01T00:00:00Z"
    assert log_dict["domain_name"] == "botrun.ai"
    assert log_dict["user_department"] == "test_org"
    assert log_dict["user_name"] == "user_1"
    assert log_dict["source_ip"] == "127.0.0.1"
    assert log_dict["session_id"] == "session_1"
    assert log_dict["action_type"] == "audio_upload"
    assert log_dict["developer"] == "JcXGTcW"
    assert log_dict["action_details"] == "音檔上傳"
    assert log_dict["model"] == "whisper-1"
    assert log_dict["botrun"] == "波程.botrun"
    assert log_dict["user_agent"] == "user_agent"
    assert log_dict["resource_id"] == "audio_1"
    assert log_dict["file_size_mb"] == 20

def test_image_log_entry():
    log_entry = ImageLogEntry(
        "2021-01-01T00:00:00Z", 'botrun.ai', "test_org", "user_1", "127.0.0.1", "session_1", "image_upload",
        "JcXGTcW", "dall-e-3", "波程.botrun", 1.5, "圖片上傳", "user_agent", "image_1"
    )
    log_dict = log_entry.to_dict()
    assert log_dict["timestamp"] == "2021-01-01T00:00:00Z"
    assert log_dict["domain_name"] == "botrun.ai"
    assert log_dict["user_department"] == "test_org"
    assert log_dict["user_name"] == "user_1"
    assert log_dict["source_ip"] == "127.0.0.1"
    assert log_dict["session_id"] == "session_1"
    assert log_dict["action_type"] == "image_upload"
    assert log_dict["developer"] == "JcXGTcW"
    assert log_dict["action_details"] == "圖片上傳"
    assert log_dict["model"] == "dall-e-3"
    assert log_dict["botrun"] == "波程.botrun"
    assert log_dict["user_agent"] == "user_agent"
    assert log_dict["resource_id"] == "image_1"
    assert log_dict["img_size_mb"] == 1.5

def test_vector_log_entry():
    log_entry = VectorDBLogEntry(
        "2021-01-01T00:00:00Z", 'botrun.ai', "test_org", "user_1", "127.0.0.1", "session_1", "vector_operation",
        "JcXGTcW", "text-embedding-ada-002", "波程.botrun", 10, "向量操作", "user_agent", "1AE5_wQsEretANgmgIFAkSVY5JUepZ767"
    )
    log_dict = log_entry.to_dict()
    assert log_dict["timestamp"] == "2021-01-01T00:00:00Z"
    assert log_dict["domain_name"] == "botrun.ai"
    assert log_dict["user_department"] == "test_org"
    assert log_dict["user_name"] == "user_1"
    assert log_dict["source_ip"] == "127.0.0.1"
    assert log_dict["session_id"] == "session_1"
    assert log_dict["action_type"] == "vector_operation"
    assert log_dict["developer"] == "JcXGTcW"
    assert log_dict["action_details"] == "向量操作"
    assert log_dict["model"] == "text-embedding-ada-002"
    assert log_dict["botrun"] == "波程.botrun"
    assert log_dict["user_agent"] == "user_agent"
    assert log_dict["resource_id"] == "1AE5_wQsEretANgmgIFAkSVY5JUepZ767"
    assert log_dict["page_num"] == 10