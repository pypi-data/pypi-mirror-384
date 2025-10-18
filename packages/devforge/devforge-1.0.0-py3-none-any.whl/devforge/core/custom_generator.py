# devforge/core/custom_generator.py
import re
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

def _sanitize_base_path(bp: str) -> Path:
    p = Path(bp).expanduser()
    if p.exists() and p.is_file():
        logger.warning("تم تحديد ملف بدل مجلد: '%s' — سأستخدم المجلد الأب.", p)
        p = p.parent
    if not p.exists():
        try:
            p.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            fallback = Path.cwd()
            logger.warning("لا أملك صلاحية إنشاء '%s' — سأستخدم مجلد العمل الحالي: %s", p, fallback)
            p = fallback
    return p

def _clean_name(raw: str) -> str:
    # ازالة أي تعليق بعد ← أو #
    raw = re.split(r'←|#', raw)[0]
    # إزالة رموز الرسم الزخرفية
    raw = re.sub(r'[│└├─]+', '', raw)
    return raw.strip()

def create_structure(base_path: str, structure_text: str) -> Optional[Path]:
    """
    ينشئ هيكل ملفات/مجلدات من ASCII tree.
    يعيد Path إلى جذر المشروع المُنشأ أو None لو فشل.
    """
    base = _sanitize_base_path(base_path)
    lines = [ln.rstrip('\n') for ln in structure_text.splitlines()]

    # ابحث أول سطر غير فارغ ليحسب الجذر (root)
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx >= len(lines):
        logger.error("لا يوجد نص صالح في الهيكل المُدخل.")
        return None

    first = lines[idx].strip()
    root_name = _clean_name(first).rstrip('/')
    if not root_name:
        logger.error("لم أتمكّن من استنتاج اسم الجذر من السطر الأول.")
        return None

    project_root = base.joinpath(root_name)
    try:
        project_root.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning("فشل إنشاء جذر المشروع '%s': %s — سيتم استخدام '%s' بدلاً منه.",
                       project_root, e, base)
        project_root = base

    stack = [(0, project_root)]

    for line in lines[idx + 1:]:
        if not line.strip() or line.strip() == '│':
            continue

        # العثور على أول connector (├ أو └) لتحديد العمق النسبي
        m = re.search(r'[├└]', line)
        if m:
            prefix = line[:m.start()]
            normalized = prefix.replace('│', ' ' * 4)
            depth = (len(normalized) // 4) + 1
        else:
            lead_match = re.match(r'^([ \t│]*)', line)
            lead = lead_match.group(1) if lead_match else ''
            normalized = lead.replace('│', ' ' * 4)
            depth = (len(normalized) // 4) + 1

        # استخراج الاسم وتنظيفه
        name_part = re.sub(r'^.*?[├└]──\s*', '', line)
        name_part = _clean_name(name_part)
        if not name_part:
            continue

        is_dir = line.strip().endswith('/') or name_part.endswith('/')

        # تصحيح الستاك للوصول إلى الأب المناسب
        while len(stack) > 1 and stack[-1][0] >= depth:
            stack.pop()

        parent_path = Path(stack[-1][1]) if stack else project_root
        current_path = parent_path.joinpath(name_part.rstrip('/'))

        try:
            if is_dir:
                current_path.mkdir(parents=True, exist_ok=True)
                stack.append((depth, current_path))
                logger.debug("Created dir: %s (depth=%s)", current_path, depth)
            else:
                current_path.parent.mkdir(parents=True, exist_ok=True)
                if not current_path.exists():
                    current_path.write_text("", encoding="utf-8")
                    logger.debug("Created file: %s", current_path)
        except PermissionError:
            logger.warning("لا أملك صلاحية إنشاء '%s'. تم تجاهله.", current_path)
        except Exception as e:
            logger.error("خطأ عند إنشاء '%s': %s", current_path, e)

    logger.info("✅ تم إنشاء المشروع بنجاح داخل: %s", project_root)
    return project_root
