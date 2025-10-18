# tests/test_smoke.py

from csv_tool.src.csv_tool import CSVTool
import os
import json


def test_csv_tool_basic_run():
    tool = CSVTool()
    test_file = "test_output.csv"

    try:
        data = [
            {"name": "Mine", "age": 24},
            {"name": "Şeyma", "age": 25}
        ]
        write_result = tool._run(file_path=test_file, action="write", data=data)
        assert "başarıyla" in write_result or "kaydedilmiştir" in write_result

        read_result = tool._run(file_path=test_file, action="read")
        parsed = json.loads(read_result)
        assert isinstance(parsed, list)
        assert parsed[0]["name"] == "Mine"

        print(f"Smoke test passed. Read {len(parsed)} rows successfully.")

    except Exception as e:
        raise AssertionError(f"Smoke test failed: {e}")

    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


if __name__ == "__main__":
    test_csv_tool_basic_run()
