# Removing the 2nd resource (file1.txt) without affecting the others

## Problem

Resources are deployed with `count`. Indices are positional — removing the middle item and lowering `count` would reindex everything and force destroy/recreate on the remaining files (because `filename = "file${count.index}.txt"`).

**Goal:** Delete only `local_file.foo[1]` / `file1.txt`. Keep `file0.txt`, `file2.txt`, `file3.txt`, `file4.txt` unchanged. End with `terraform apply` reporting **No changes**.

**Approach:** Migrate from `count` to `for_each` with stable keys, then remove key `"1"` from the set.

---

## Step 1 — Refactor `main.tf` from `count` to `for_each`

Replace the current config with this (same 5 resources, stable keys):

```hcl
variable "files" {
  default = ["0", "1", "2", "3", "4"]
}

resource "local_file" "foo" {
  for_each = toset(var.files)
  content  = "# Some content for file ${each.key}"
  filename = "file${each.key}.txt"
}
```

Do **not** remove `"1"` yet — all 5 keys must stay for the state migration.

---

## Step 2 — Move existing state entries to the new `for_each` addresses

Run from the `infrastructure-as-code` folder:

```bash
terraform state mv 'local_file.foo[0]' 'local_file.foo["0"]'
terraform state mv 'local_file.foo[1]' 'local_file.foo["1"]'
terraform state mv 'local_file.foo[2]' 'local_file.foo["2"]'
terraform state mv 'local_file.foo[3]' 'local_file.foo["3"]'
terraform state mv 'local_file.foo[4]' 'local_file.foo["4"]'
```

`terraform state mv` updates state only — no resources are destroyed or recreated on disk.

Reference: https://developer.hashicorp.com/terraform/cli/commands/state/mv

---

## Step 3 — Verify the migration (expect no changes)

```bash
terraform plan
```

Expected: **No changes**. All 5 files still managed under new addresses.

```bash
terraform apply
```

Expected: **No changes**.

---

## Step 4 — Remove the 2nd resource from the config

Update the variable to exclude key `"1"` (the 2nd resource / `file1.txt`):

```hcl
variable "files" {
  default = ["0", "2", "3", "4"]
}
```

---

## Step 5 — Apply to destroy only file1.txt

```bash
terraform plan
```

Expected: **1 to destroy** — `local_file.foo["1"]` / `file1.txt` only.

```bash
terraform apply
```

Confirm the destroy when prompted.

---

## Step 6 — Final verification

```bash
terraform plan
terraform apply
```

Expected: **No changes**.

Remaining files on disk (unchanged):

| Key   | File       |
|-------|------------|
| `"0"` | file0.txt  |
| `"2"` | file2.txt  |
| `"3"` | file3.txt  |
| `"4"` | file4.txt  |

---

## Why not just lower `count`?

| Action | Result |
|--------|--------|
| `count = 5` → `count = 4` | Destroys index `[4]`, reindexes `[2]`→`[1]`, etc. |
| Manual file delete + rename | Works but fragile; state easily drifts from reality |
| `for_each` + stable keys | Remove one key → only that resource is destroyed |

Reference: https://developer.hashicorp.com/terraform/language/meta-arguments/for_each

---

## Optional — one-shot state migration script

```bash
for i in 0 1 2 3 4; do
  terraform state mv "local_file.foo[$i]" "local_file.foo[\"$i\"]"
done
```
