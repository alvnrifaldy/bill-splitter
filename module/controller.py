import tempfile
from module.model.gemini import GeminiModel, normalized_receipt
from module.data.receipt_data import ReceiptData, ItemData
from module.utils.split_logic import count_the_bill

class ReceiptController:
    def __init__(self):
        self.receipt = None
        self.people = []
        self.temp_people = {}
        self.step = 1

    def process_receipt(self, api_key, uploaded_file):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(uploaded_file.read())
            img_path = tmp.name
    
        extractor = GeminiModel(api_key=api_key)
        raw = extractor.extract(img_path)
        normalized = normalized_receipt(raw)
    
        normalized["items"] = [
            ItemData(**item) for item in normalized["items"]
        ]
    
        self.receipt = ReceiptData(**normalized)
        self.step = 2
        return self.receipt

    def add_temp_menu(self, person_name, item_name, qty):
        """Tambah pilihan menu sementara sebelum user selesai."""
        if person_name not in self.temp_people:
            self.temp_people[person_name] = {}

        if item_name in self.temp_people[person_name]:
            self.temp_people[person_name][item_name] += qty
        else:
            self.temp_people[person_name][item_name] = qty

    def commit_person(self, person_name):
        """Pindahkan menu sementara ke daftar people"""
        menu = self.temp_people.get(person_name, {})

        self.people.append({
            "name": person_name,
            "menu": menu
        })

        # Hapus temp data orang ini
        del self.temp_people[person_name]

    def compute_bill(self):
        assignments = {}

        for idx, item in enumerate(self.receipt.items):
            payers = []
            for p in self.people:
                qty = p["menu"].get(item.name, 0)
                for _ in range(qty):
                    payers.append(p["name"])
            assignments[idx] = payers

        totals = count_the_bill(self.receipt, assignments)
        return totals

    def reset(self):
        self.receipt = None
        self.people = []
        self.temp_people = {}
        self.step = 1
