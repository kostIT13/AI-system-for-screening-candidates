import json
import random
from pathlib import Path


RANDOM_SEED = 42
TARGET_SAMPLES = 600
TRAIN_RATIO = 0.9


PROFILES = {
    "Python Backend Developer": {
        "candidate_skills": ["Python", "FastAPI", "Django", "PostgreSQL", "Redis", "Docker", "AsyncIO"],
        "vacancy_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Kafka", "Redis"],
        "candidate_exp": (2, 9),
        "vacancy_exp_min": (2, 6),
        "vacancy_exp_max_delta": (1, 3),
        "candidate_salary": (90000, 320000),
        "vacancy_salary": (120000, 340000),
        "locations": ["Москва", "Санкт-Петербург", "Казань", "Новосибирск", "Екатеринбург"],
    },
    "ML Engineer": {
        "candidate_skills": ["Python", "PyTorch", "TensorFlow", "Pandas", "NumPy", "MLflow", "Docker", "Airflow"],
        "vacancy_skills": ["Python", "PyTorch", "Albumentations", "OpenCV", "MLOps", "Docker"],
        "candidate_exp": (1, 8),
        "vacancy_exp_min": (1, 5),
        "vacancy_exp_max_delta": (1, 3),
        "candidate_salary": (110000, 340000),
        "vacancy_salary": (140000, 360000),
        "locations": ["Москва", "Санкт-Петербург", "Казань", "Регионы"],
    },
    "Frontend Developer": {
        "candidate_skills": ["JavaScript", "TypeScript", "React", "Redux", "CSS", "HTML", "Next.js", "Vue"],
        "vacancy_skills": ["React", "TypeScript", "Redux", "Next.js", "CSS", "REST API"],
        "candidate_exp": (1, 8),
        "vacancy_exp_min": (1, 6),
        "vacancy_exp_max_delta": (1, 2),
        "candidate_salary": (70000, 260000),
        "vacancy_salary": (100000, 290000),
        "locations": ["Москва", "Санкт-Петербург", "Казань", "Регионы"],
    },
    "DevOps Engineer": {
        "candidate_skills": ["Docker", "Kubernetes", "Terraform", "AWS", "GitLab CI", "Linux", "Prometheus"],
        "vacancy_skills": ["Docker", "Kubernetes", "Terraform", "AWS", "GitLab CI", "ArgoCD"],
        "candidate_exp": (2, 10),
        "vacancy_exp_min": (2, 7),
        "vacancy_exp_max_delta": (1, 3),
        "candidate_salary": (120000, 360000),
        "vacancy_salary": (150000, 390000),
        "locations": ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Регионы"],
    },
    "Data Analyst": {
        "candidate_skills": ["SQL", "Python", "Pandas", "Power BI", "Tableau", "A/B testing", "Statistics"],
        "vacancy_skills": ["SQL", "Python", "A/B testing", "Product metrics", "Tableau"],
        "candidate_exp": (1, 9),
        "vacancy_exp_min": (1, 6),
        "vacancy_exp_max_delta": (1, 3),
        "candidate_salary": (80000, 280000),
        "vacancy_salary": (110000, 300000),
        "locations": ["Москва", "Санкт-Петербург", "Казань", "Регионы"],
    },
}

REMOTE_OPTIONS = ["Да", "Нет", "Гибрид"]
EMPLOYMENT_OPTIONS = ["Полная", "Частичная"]


def choose_skills(base_skills, min_n=4, max_n=7):
    k = random.randint(min_n, min(max_n, len(base_skills)))
    return sorted(random.sample(base_skills, k=k))


def overlap(a, b):
    return sorted(set(a) & set(b))


def build_pair(profile_name, hard_negative=False):
    p = PROFILES[profile_name]
    candidate_title = profile_name
    vacancy_title = profile_name

    c_skills = choose_skills(p["candidate_skills"], 4, 7)
    v_skills = choose_skills(p["vacancy_skills"], 4, 6)

    if hard_negative:
        other_profile = random.choice([x for x in PROFILES if x != profile_name])
        v_skills = choose_skills(PROFILES[other_profile]["vacancy_skills"], 4, 6)
        vacancy_title = other_profile

    c_exp = random.randint(*p["candidate_exp"])
    v_min = random.randint(*p["vacancy_exp_min"])
    v_max = v_min + random.randint(*p["vacancy_exp_max_delta"])

    c_salary_min = random.randint(p["candidate_salary"][0], p["candidate_salary"][1] - 40000)
    c_salary_max = c_salary_min + random.randint(30000, 90000)
    v_salary_min = random.randint(p["vacancy_salary"][0], p["vacancy_salary"][1] - 50000)
    v_salary_max = v_salary_min + random.randint(40000, 120000)

    c_location = random.choice(p["locations"])
    if hard_negative and random.random() < 0.7:
        v_location = random.choice([x for x in p["locations"] if x != c_location]) if len(p["locations"]) > 1 else c_location
    else:
        v_location = c_location if random.random() < 0.7 else random.choice(p["locations"])

    c_remote = random.choice(REMOTE_OPTIONS)
    v_remote = random.choice(REMOTE_OPTIONS)
    c_employment = random.choice(EMPLOYMENT_OPTIONS)
    v_employment = random.choice(EMPLOYMENT_OPTIONS)

    common = overlap(c_skills, v_skills)
    missing = sorted(set(v_skills) - set(c_skills))
    required_count = len(v_skills) if v_skills else 1
    skill_ratio = len(common) / required_count

    if c_exp < v_min:
        exp_score = max(0.0, c_exp / max(1, v_min))
        exp_text = f"Опыт кандидата {c_exp} лет ниже диапазона вакансии ({v_min}-{v_max} лет)."
    elif c_exp > v_max:
        exp_score = 0.95
        exp_text = f"Опыт кандидата {c_exp} лет выше верхней границы ({v_max} лет), но это допустимо."
    else:
        exp_score = 1.0
        exp_text = f"Опыт кандидата {c_exp} лет находится в диапазоне вакансии ({v_min}-{v_max} лет)."

    intersect = not (c_salary_max < v_salary_min or c_salary_min > v_salary_max)
    salary_score = 1.0 if intersect else 0.45
    salary_text = (
        f"Ожидания кандидата ({c_salary_min}-{c_salary_max} руб.) "
        f"{'пересекаются' if intersect else 'не пересекаются'} "
        f"с вилкой вакансии ({v_salary_min}-{v_salary_max} руб.)."
    )

    same_location = c_location == v_location
    remote_ok = v_remote in {"Да", "Гибрид"} or c_remote in {"Да", "Гибрид"}
    location_score = 1.0 if same_location or remote_ok else 0.4
    if same_location:
        location_text = f"Локация совпадает: {c_location}."
    elif remote_ok:
        location_text = "Локация отличается, но удаленный/гибридный формат совместим."
    else:
        location_text = f"Локация не совпадает ({c_location} vs {v_location})."

    employment_score = 1.0 if c_employment == v_employment else 0.6
    score = int((skill_ratio * 0.45 + exp_score * 0.25 + salary_score * 0.15 + location_score * 0.1 + employment_score * 0.05) * 100)
    score = max(10, min(96, score))

    if score >= 80:
        rec = "hire"
    elif score >= 50:
        rec = "consider"
    else:
        rec = "reject"

    strengths = []
    weaknesses = []
    if common:
        strengths.append(f"Совпавшие навыки: {', '.join(common[:5])}")
    if c_exp >= v_min:
        strengths.append("Опыт соответствует минимальным требованиям")
    if intersect:
        strengths.append("Зарплатные ожидания в рабочем диапазоне")

    if missing:
        weaknesses.append(f"Недостающие навыки: {', '.join(missing[:5])}")
    if c_exp < v_min:
        weaknesses.append("Недостаточный опыт")
    if not (same_location or remote_ok):
        weaknesses.append("Несовпадение по локации/формату")

    user_prompt = (
        "Оцени соответствие кандидата вакансии и верни только JSON. "
        f"Кандидат: {candidate_title}, опыт {c_exp} лет, навыки {', '.join(c_skills)}, "
        f"зарплата {c_salary_min}-{c_salary_max}, локация {c_location}, формат {c_remote}, занятость {c_employment}. "
        f"Вакансия: {vacancy_title}, опыт {v_min}-{v_max} лет, навыки {', '.join(v_skills)}, "
        f"зарплата {v_salary_min}-{v_salary_max}, локация {v_location}, формат {v_remote}, занятость {v_employment}."
    )

    assistant_obj = {
        "analysis": {
            "skills_match": f"Совпавшие навыки ({len(common)}/{required_count}): {', '.join(common) if common else 'нет'}. Недостающие навыки: {', '.join(missing) if missing else 'нет'}.",
            "experience_match": exp_text,
            "salary_match": salary_text,
            "location_match": location_text,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendation": rec,
        },
        "confidence": round(0.55 + score / 250, 2),
        "match_score": score,
    }

    return {
        "messages": [
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": json.dumps(assistant_obj, ensure_ascii=False)},
        ]
    }


def main():
    random.seed(RANDOM_SEED)
    samples = []
    profile_names = list(PROFILES.keys())
    for i in range(TARGET_SAMPLES):
        profile = random.choice(profile_names)
        hard_negative = (i % 4 == 0)
        samples.append(build_pair(profile, hard_negative=hard_negative))

    random.shuffle(samples)
    train_size = int(len(samples) * TRAIN_RATIO)
    train_samples = samples[:train_size]
    val_samples = samples[train_size:]

    out_dir = Path(__file__).resolve().parent
    train_path = out_dir / "train_full.jsonl"
    val_path = out_dir / "val_full.jsonl"

    with train_path.open("w", encoding="utf-8") as f:
        for row in train_samples:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    with val_path.open("w", encoding="utf-8") as f:
        for row in val_samples:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Generated: {len(train_samples)} train / {len(val_samples)} val")
    print(f"Train: {train_path}")
    print(f"Val: {val_path}")


if __name__ == "__main__":
    main()
