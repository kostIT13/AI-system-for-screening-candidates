# 🤖 Fine-tuning LLM для скрининга кандидатов

Дообучение модели **Llama 3.2 3B** для оценки соответствия резюме вакансиям.

## 📁 Файлы

| Файл | Описание | Датасет | Время |
|------|----------|---------|-------|
| `FineTuning.ipynb` | Демо-версия для быстрого теста | 9 примеров | ~5 мин |
| `FineTuning_full_dataset.ipynb` | Полноценное обучение | 500 примеров | ~40 мин |
| `dataset_example.json` | Пример формата данных | — | — |

## 🚀 Быстрый старт

### 1. Демо (9 примеров)
Откройте [`FineTuning.ipynb`](./FineTuning.ipynb) в Google Colab и запустите все ячейки.

**Результат:**
- Модель выучит формат ответа (JSON)
- Loss: ~2.3 → 2.3 (не изменится значительно)
- **Не для продакшена** — только для проверки пайплайна

### 2. Полное обучение (500 примеров)
Откройте [`FineTuning_full_dataset.ipynb`](./FineTuning_full_dataset.ipynb) в Google Colab.

**Результат:**
- Модель научится оценивать соответствие
- Loss: ~2.6 → 0.4-0.7
- **Готово для интеграции** в приложение

## ⚙️ Параметры обучения

| Параметр | Значение |
|----------|----------|
| Базовая модель | `unsloth/Llama-3.2-3B-Instruct` |
| Метод | QLoRA 4-bit (Unsloth) |
| GPU | Google Colab T4 (бесплатно) |
| Batch size | 8 (2×4 gradient accumulation) |
| Learning rate | 1e-4 – 2e-4 |
| Max steps | Авто-расчёт под размер датасета |

## Ссылки на модели

* 🤗 [Репозиторий модели на Hugging Face](https://huggingface.co/jiikoool/screening-test/tree/main) (9 examples)
* 🤗 [Репозиторий модели на Hugging Face](https://huggingface.co/jiikoool/screening-test3b/tree/main) (500 examples)


## 🔧 Использование в Ollama

```bash
# скачайте модель.gguf и Modelfile в папку
cd papka

# Импортируйте в Ollama
ollama create screening-test:3b -f Modelfile

# Запустите
ollama run screening-test:3b
