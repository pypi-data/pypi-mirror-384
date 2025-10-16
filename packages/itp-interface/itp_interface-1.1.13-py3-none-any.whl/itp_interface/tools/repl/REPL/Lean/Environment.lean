/-
Copyright (c) 2023 Kim Morrison. All Rights Reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Kim Morrison
-/
import REPL.Util.Pickle
import Lean.Replay

open System (FilePath)

namespace Lean.Environment

/--
Pickle an `Environment` to disk.

We only store:
* the list of imports
* the new constants from `Environment.constants`
and when unpickling, we build a fresh `Environment` from the imports,
and then add the new constants.
-/
def pickle (env : Environment) (path : FilePath) : IO Unit :=
  _root_.pickle path (env.header.imports, env.constants.map₂)

/--
Unpickle an `Environment` from disk.

We construct a fresh `Environment` with the relevant imports,
and then replace the new constants.
-/
def unpickle (path : FilePath) : IO (Environment × CompactedRegion) := unsafe do
  let ((imports, map₂), region) ← _root_.unpickle (Array Import × PHashMap Name ConstantInfo) path
  let env ← importModules imports {} 0 (loadExts := true)
  return (← env.replay (Std.HashMap.ofList map₂.toList), region)

end Lean.Environment
