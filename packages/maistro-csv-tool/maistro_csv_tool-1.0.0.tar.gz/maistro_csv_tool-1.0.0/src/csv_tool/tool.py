from maistro.core.base_tool import CustomBaseTool
import csv
import json
from typing import Union, List, Dict


class CSVTool(CustomBaseTool):
    def __init__(self):
        super().__init__(
            name="csv_tool",
            description=(
                "CSV dosyalarını okuma veya yazma işlemleri yapar. "
                "Eyleme bağlı olarak dosya içeriğini JSON formatında döndürür veya verilen veriyi CSV'ye yazar."
            ),
        )

    def _run(
        self,
        file_path: str,
        action: str = "read",
        data: Union[List[Dict], Dict, None] = None,
        append: bool = False
    ) -> str:
        """
        CSV dosyası üzerinde okuma veya yazma işlemi gerçekleştirir.

        Args:
            file_path (str): CSV dosyasının tam yolu.
            action (str): "read" veya "write"
            data (list[dict] | dict, optional): Yazılacak veri.
            append (bool): True ise mevcut dosyanın sonuna ekleme yapılır.

        Returns:
            str: Okuma işlemi için JSON string; yazma işlemi için onay mesajı.
        """

        if action not in ("read", "write"):
            return "Geçersiz işlem türü. 'read' veya 'write' kullanılmalıdır."

        # --- READ ---
        if action == "read":
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                return json.dumps(rows, ensure_ascii=False)
            except Exception as e:
                return f"CSV okuma hatası: {e}"

        # --- WRITE ---
        if action == "write":
            if not data:
                return "Yazılacak veri belirtilmedi."

            mode = "a" if append else "w"
            try:
                with open(file_path, mode, newline="", encoding="utf-8") as f:
                    if isinstance(data, dict):
                        data = [data]
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    if not append or f.tell() == 0:
                        writer.writeheader()
                    writer.writerows(data)
                return f"Veri başarıyla {'eklenmiştir' if append else 'kaydedilmiştir'}: {file_path}"
            except Exception as e:
                return f"CSV yazma hatası: {e}"

    async def _arun(
        self,
        file_path: str,
        action: str = "read",
        data: Union[List[Dict], Dict, None] = None,
        append: bool = False
    ) -> str:
        """Asenkron kullanım için _run metodunu çağırır."""
        return self._run(file_path, action, data, append)
