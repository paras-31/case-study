# ADD CODE HERE
# change script to whatever language you are comfortable with

#!/usr/bin/env python3
import json
import sys
# from textwrap import indent


def check_plan(filepath):
    with open(filepath) as f:
        plan = json.load(f)

    # print(plan)

    changes = plan.get("resource_changes", [])
    problems = []

    # ignore no-op entries, we only care about real changes
    real_changes = [c for c in changes if c["change"]["actions"] != ["no-op"]]

    if not real_changes:
        problems.append("No create or modify actions in plan")
        return False, problems

    for change in real_changes:
        address = change["address"]
        actions = change["change"]["actions"]
        before = change["change"].get("before") or {}
        after = change["change"].get("after") or {}

        # create is always fine
        if actions == ["create"]:
            continue

        # update = modify, but only tags.GitCommitHash can change
        if actions == ["update"]:
            all_keys = set(before.keys()) | set(after.keys())
            changed = [k for k in all_keys if before.get(k) != after.get(k)]

            for attr in changed:
                if attr != "tags":
                    problems.append(
                        f"{address}: modifies '{attr}' — only 'tags' is allowed"
                    )

            if "tags" in changed:
                before_tags = before.get("tags") or {}
                after_tags = after.get("tags") or {}
                all_tags = set(before_tags.keys()) | set(after_tags.keys())

                for tag in all_tags:
                    if before_tags.get(tag) != after_tags.get(tag):
                        if tag != "GitCommitHash":
                            problems.append(
                                f"{address}: modifies tag '{tag}' — only 'GitCommitHash' is allowed"
                            )
            continue

        # anything with delete/replace/etc is blocked
        if "delete" in actions:
            problems.append(f"{address}: will be destroyed ({', '.join(actions)})")
        else:
            problems.append(f"{address}: disallowed action [{', '.join(actions)}]")

    return len(problems) == 0, problems


def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else "tfplan.json"
    ok, problems = check_plan(filepath)

    if ok:
        print("APPLY PROCEED")
        sys.exit(0)
    else:
        print("APPLY BLOCKED")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)


if __name__ == "__main__":
    main()