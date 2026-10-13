"""Mask a batch of patient comments before storing them or sending them to an LLM.

Run: python examples/patient_comments.py
"""

from cloakix import Masker

comments = [
    "شكرا للدكتورة نورة على الاهتمام، ورقم ملفي 4471029",
    "زرت المستشفى مع أخي فهد السبيعي في الرياض والخدمة كانت سيئة",
    "موبايلي 01012345678 والرقم القومي 29001010112345، محدش رد عليا",
    "Great care from Dr. Sara Al-Qahtani. Call me on +971 50 123 4567",
    "الانتظار كان طويل جدا في الطوارئ",
]

masker = Masker()

for result in masker.mask_batch(comments):
    print(result.text)

# When a comment is linked to a patient record, pass what you already know.
# Those values are masked wherever they appear, in any format.
comment = "سلمان يقول التعامل ممتاز، اتصلوا عليه 055 999 8877"
known = {"PERSON": ["سلمان الدوسري"], "PHONE": ["0559998877"], "MRN": ["X-99812"]}
print(masker.mask(comment, known=known).text)
