"""Article and achievement card for the product basket.

Measured rows are formatted from outputs/results.json. The article row stays
unsubmitted: the checked special issue is past its printed deadline, and a
patent attorney has not reviewed a manuscript. This card does not describe
the cutoff rule.
"""

from __future__ import annotations

REPO = "https://github.com/parsasohrab1/articles-avguard-grounding"
BRANCH = "feat/avguard-grounding-realdata"
PULL = "https://github.com/parsasohrab1/articles-avguard-grounding/pull/2"
TITLE = (
    "What share of field values stated by a language model match the NTSB record? "
    "A sample of public occurrence narratives"
)
FIELDS = ("injury", "weather", "light", "midair")
LABELS = {
    "injury": "آسیب",
    "weather": "هوا",
    "light": "روشنایی",
    "midair": "برخورد میان‌هوایی",
}


def _pct(rate) -> str:
    if rate is None:
        return "n/a"
    return f"{100 * rate:.1f}%"


def _field_table(claims: dict) -> str:
    lines = [
        "| فیلد | خانه | پاسخ‌داده | منطبق | نامنطبق | امتناع | نرخ انطباق میان پاسخ‌داده‌ها |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name in FIELDS:
        row = claims["by_field"][name]
        lines.append(
            f"| {LABELS[name]} ({name}) | {row['n']} | {row['n_answered']} | {row['n_match']} | "
            f"{row['n_mismatch']} | {row['n_abstain']} | {_pct(row['match_rate_answered'])} |"
        )
    return "\n".join(lines)


def _support_lines(results: dict) -> str:
    minimum = results["provenance"]["min_false_cal"]
    lines = []
    for name in FIELDS:
        row = results["support"]["by_field"][name]
        label = f"{LABELS[name]} ({name})"
        if row["status"] != "estimated":
            lines.append(
                f"برای {label} سهم پذیرش نادرست ثبت نمی‌شود: "
                f"ادعاهای نامنطبق کالیبراسیون {row['n_false_cal']} است و حداقل لازم {minimum}."
            )
            continue
        lines.append(
            f"برای {label}، {_pct(row['false_accept'])} از {row['n_false_test']} "
            f"ادعای نامنطبقِ کنارگذاشته‌شده بالای آستانه بود و "
            f"{_pct(row['true_accept'])} از {row['n_true_test']} ادعای منطبق."
        )
    return " ".join(lines)


def registration_markdown(results: dict) -> str:
    """Filing card. `results` is the object written by scripts/run_experiment.py."""
    prov = results["provenance"]
    claims = results["claims"]
    if prov.get("api_key_in_repo") is not False:
        raise ValueError("the registration card refuses a run that stored an API key")
    years = prov["years"]
    return f"""# ثبت مقاله و دستاوردها

شناسه سبد: `avguard`. این برگه برای ثبت داخلی است. مقاله‌ای به ژورنال ارسال نشده است.

| قلم | ثبت |
|---|---|
| محصول | AvGuard-Ground |
| ریپو | {REPO} |
| شاخه | `{BRANCH}` |
| پیش‌نویس بررسی | {PULL} |
| بلوغ | TRL 3 |
| نوع داده | گزارش عمومی رخداد (NTSB، پیش از ۲۰۰۸) |
| داده | {prov["corpus_n"]} رکورد، سال‌های {years[0]}–{years[1]}؛ نمونه {prov["sample_n"]} روایت، بذر {prov["seed"]} |
| مدل | `{prov["model"]}` |
| عنوان یادداشت | {TITLE} |
| متن | `article/abstract.md` |
| دروازه ژورنال | `docs/JOURNAL_FIT.md` |
| وضعیت مقاله | ارسال نشده |
| فراخوان بررسی‌شده | Advanced Engineering Informatics، ویژه «AI Trustworthiness and Applications of Large Language Models in Aviation Safety, Accident Investigation and Aircraft Engineering»؛ مهلت چاپ‌شده ۳۱ مارس ۲۰۲۶ گذشته است |
| وکیل پتنت | متن ارسال را تأیید نکرده است. این برگه قاعده‌ی آستانه را شرح نمی‌دهد. |

## دستاورد اندازه‌گیری‌شده

منبع اعداد: `outputs/results.json`. خلاصه پاسخ‌ها `{prov["response_sha256"][:12]}`. از {claims["n_slots"]} خانه، مدل برای {claims["n_answered"]} کد داد و برای {claims["n_abstain"]} امتناع کرد. از کدهای داده‌شده، {claims["n_match"]} با فیلد ساخت‌یافته یکی بود ({_pct(claims["match_rate_answered"])}) و {claims["n_mismatch"]} نبود.

{_field_table(claims)}

تقسیم همان نمونه: آموزش {results["support"]["n_train"]}، کالیبراسیون {results["support"]["n_cal"]}، کنارگذاشته {results["support"]["n_test"]}. {_support_lines(results)}

دستاورد ثبت‌شده نرخ انطباق مقدارهایی است که همین مدل روی همین نمونه گفته است. این نرخ عملکرد کل پایگاه نیست و مبنای پذیرش یک خلاصه در تحقیق نیست.
"""
