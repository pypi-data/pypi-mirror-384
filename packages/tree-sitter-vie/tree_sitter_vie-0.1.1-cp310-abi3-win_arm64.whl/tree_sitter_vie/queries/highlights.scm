[
  "{{"
  "}}"
  "{%"
  "%}"
  "("
  ")"
] @punctuation.bracket

"," @punctuation.delimiter

(comment) @comment

[
  "if"
  "else"
  "switch"
  "case"
  "end"
  "is"
  "not"
  "is not"
  "or"
  "and"
] @keyword

[
  "||"
  "&&"
  "<="
  ">="
  ">"
  "<"
  "!="
  "=="
  "!"
  ".."
  "|"
] @operator

(identifier) @variable

(pipe_expression
  function: (identifier) @function.call)

(call_expression
  function: (identifier) @function.call)

(boolean_literal) @boolean

(string_literal) @string

(escape_sequence) @string.escape
