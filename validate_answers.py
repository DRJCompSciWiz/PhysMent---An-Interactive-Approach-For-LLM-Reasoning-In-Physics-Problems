"""
Quick script to check that _check_answer() works across all scene answer formats.
Loads each scene JSON, generates some common LLM formatting variants, and reports
any scenes where matching fails.
"""

import json
import os
import re
import sys


# -- Answer normalization/checking (same logic as Experiment.py, copied here
#    so we don't need MuJoCo installed to run this) --

def _normalize_answer(answer):
    if answer is None:
        return ""
    s = str(answer).strip()
    s = re.sub(r'^[\[\(]+', '', s)
    s = re.sub(r'[\]\)]+$', '', s)
    s = re.sub(
        r'\s*(m/s²|m/s2|m/s|rad/s|kg·m/s|kg\*m/s|N·m|N\*m|rad|kg|m|N|J|W|s)\s*$',
        '', s, flags=re.IGNORECASE,
    )
    s = re.sub(r'\bobject_', '', s, flags=re.IGNORECASE)
    return s.strip()


def _check_answer(final, correct):
    if final is None or correct is None:
        return False

    nf = _normalize_answer(final)
    nc = _normalize_answer(correct)

    # Exact match
    if nf.lower() == nc.lower():
        return True

    # Numeric (tolerance 0.1)
    try:
        if abs(float(nf) - float(nc)) < 0.1:
            return True
    except (ValueError, TypeError):
        pass

    # Multi value CSV
    if ',' in str(correct):
        try:
            cp = [p.strip() for p in nc.split(',')]
            fp = [p.strip() for p in nf.split(',')]
            if len(cp) == len(fp):
                ok = True
                for c, f in zip(cp, fp):
                    try:
                        if abs(float(f) - float(c)) >= 0.1:
                            ok = False; break
                    except (ValueError, TypeError):
                        if f.lower() != c.lower():
                            ok = False; break
                if ok:
                    return True
        except Exception:
            pass

    # Word-boundary containment (prevents "elastic" matching "inelastic")
    fl, cl = nf.lower(), nc.lower()
    if fl and cl:
        if fl == cl:
            return True
        if re.search(r'\b' + re.escape(fl) + r'\b', cl):
            return True
        if re.search(r'\b' + re.escape(cl) + r'\b', fl):
            return True

    # Number extraction fallback
    fn = re.findall(r'-?\d+\.?\d*', nf)
    cn = re.findall(r'-?\d+\.?\d*', nc)
    if fn and cn and len(fn) == len(cn):
        try:
            if all(abs(float(a) - float(b)) < 0.1 for a, b in zip(fn, cn)):
                return True
        except (ValueError, TypeError):
            pass

    return False


# Answer Classification Part

def classify(answer):
    a = str(answer).strip()
    if ',' in a:
        parts = [p.strip() for p in a.split(',')]
        try:
            [float(p) for p in parts]
            return "multi_value_numeric"
        except ValueError:
            return "multi_value_mixed"
    try:
        float(a)
        return "numeric"
    except ValueError:
        pass
    if any(op in a for op in ['=', '^', '*', '/', 'sqrt', 'pi', 'sin', 'cos', 'tan', 'ln']):
        return "formula"
    if len(a.split()) <= 3:
        return "keyword"
    return "text"


def make_variants(answer, cat):
    """Generate common LLM formatting variants of a correct answer."""
    variants = [answer]
    if cat == "numeric":
        n = float(answer)
        variants += [f"{n}", f"{n} m/s", f"{n} N", str(round(n, 2))]
    elif cat == "multi_value_numeric":
        variants += [f"[{answer}]", f"({answer})"]
    elif cat == "keyword":
        variants += [answer.lower(), answer.upper()]
        try:
            variants.append(f"object_{int(answer)}")
        except ValueError:
            pass
    return variants


def main():
    scenes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Scenes")
    if not os.path.isdir(scenes_dir):
        print(f"Scenes directory not found: {scenes_dir}")
        sys.exit(1)

    scene_dirs = sorted(
        [d for d in os.listdir(scenes_dir) if d.startswith("Scene")],
        key=lambda x: int(re.findall(r'\d+', x)[0]),
    )

    categories = {}
    passed = 0
    failed = 0
    needs_review = []

    for dirname in scene_dirs:
        num = re.findall(r'\d+', dirname)[0]
        path = os.path.join(scenes_dir, dirname, f"scene{num}.json")
        if not os.path.isfile(path):
            continue

        with open(path, 'r') as f:
            data = json.load(f)

        answer = data.get("answer", "")
        ptype = data.get("metadata", {}).get("problem_type", "unknown")
        cat = classify(answer)
        categories[cat] = categories.get(cat, 0) + 1

        variants = make_variants(answer, cat)
        all_ok = all(_check_answer(v, answer) for v in variants)

        if all_ok:
            passed += 1
            print(f"  Scene {num:>3} OK  [{cat:<22}] {answer[:60]}")
        else:
            failed += 1
            print(f"  Scene {num:>3} FAIL [{cat:<22}] {answer[:60]}")
            for v in variants:
                ok = _check_answer(v, answer)
                print(f"         {'OK' if ok else 'FAIL'} variant: {v[:55]}")
            needs_review.append((num, answer, cat, ptype))

    print()
    print(f"Categories: {categories}")
    print(f"Results: {passed} passed, {failed} failed / {passed + failed} total")
    if needs_review:
        print(f"\nNeeds review:")
        for num, ans, cat, pt in needs_review:
            print(f"  Scene {num}: [{cat}] ({pt}) -> {ans[:50]}")


if __name__ == "__main__":
    main()