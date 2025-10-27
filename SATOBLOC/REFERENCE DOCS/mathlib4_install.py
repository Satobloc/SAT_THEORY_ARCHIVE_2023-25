import lean_dojo as ld

repo = ld.LeanGitRepo("https://github.com/leanprover-community/mathlib4.git")
traced_repo = ld.TracedRepo(repo)
dojo = ld.Dojo(entry=traced_repo)
