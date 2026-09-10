-- This module serves as the root of the `Hello` library.
-- Import modules here that should be built as part of the library.
import Hello.Basic
theorem test : 2 + 2 = 4 := by
  decide
#eval IO.println s!"2 + 2 = {2 + 2}"
-- This module serves as the root of the `Hello` library.
import Hello.Basic

theorem test : 2 + 2 = 4 := by
  decide

#eval IO.println s!"2 + 2 = {2 + 2}"
