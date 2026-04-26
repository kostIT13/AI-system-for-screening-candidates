# Dataset Examples (5)

Папка содержит 5 эталонных примеров в формате `messages` для SFT.

Формат каждого файла:
- `messages[0]` — user prompt с кандидатом и вакансией.
- `messages[1]` — assistant ответ строго в JSON-формате:
  - `analysis.skills_match`
  - `analysis.experience_match`
  - `analysis.salary_match`
  - `analysis.location_match`
  - `analysis.strengths`
  - `analysis.weaknesses`
  - `analysis.recommendation`
  - `confidence`
  - `match_score`

Файлы:
- `example_01.json`
- `example_02.json`
- `example_03.json`
- `example_04.json`
- `example_05.json`

Также добавлен генератор полного датасета:
- `generate_full_dataset.py`

Сгенерированные файлы:
- `train_full.jsonl` (540 примеров)
- `val_full.jsonl` (60 примеров)

Запуск генерации:
- `python dataset_examples/generate_full_dataset.py`
