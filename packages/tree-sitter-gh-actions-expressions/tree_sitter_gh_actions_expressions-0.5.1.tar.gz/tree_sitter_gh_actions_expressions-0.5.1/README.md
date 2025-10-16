# tree-sitter-gh-actions-expressions

[![CI][ci]](https://github.com/Hdoc1509/tree-sitter-gh-actions-expressions/actions/workflows/ci.yml)
[![discord][discord]](https://discord.gg/w7nTvsVJhm)
[![matrix][matrix]](https://matrix.to/#/#tree-sitter-chat:matrix.org)
[![crates][crates]](https://crates.io/crates/tree-sitter-gh-actions-expressions)
[![npm][npm]](https://www.npmjs.com/package/tree-sitter-gh-actions-expressions)
[![pypi][pypi]](https://pypi.org/project/tree-sitter-gh-actions-expressions)

[Tree-sitter](https://github.com/tree-sitter/tree-sitter) grammar for
[Github Actions expressions][gh-actions-expressions-docs]

> [!IMPORTANT]
> ABI version: `15`

## Parser requirements

- [`gitignore`](https://github.com/shunsambongi/tree-sitter-gitignore)
  (optional): for `hashFiles()` function
- [`json`](https://github.com/tree-sitter/tree-sitter-json) (optional): for
  `fromJSON()` function
- [`yaml`](https://github.com/tree-sitter/tree-sitter-yaml): injection to its
  `block_mapping_pair` node. Check the [`yaml`
  injection](#injection-for-yaml-parser) section for more information

## Usage in Editors

### Neovim

- [`gh-actions.nvim`](https://github.com/Hdoc1509/gh-actions.nvim): plugin that
  integrates this grammar to your `Neovim` configuration

### Helix

WIP

### Emacs

WIP

### In General

You can get the built files from the [`release` branch][release-branch]. If you
have specific instructions for your editor, PR's are welcome.

## Injection for `yaml` parser

Use the following query:

```query
((block_mapping_pair
  key: (flow_node) @_key
  value: [
    (block_node
      (block_scalar) @_value)
    (flow_node
      [
        (plain_scalar
          (string_scalar) @_value)
        (double_quote_scalar) @_value
      ])
  ]
  (#match? @_value "${{")) @injection.content
  (#is-gh-actions-file? "") ; NOTE: NEW PREDICATE
  (#set! injection.language "gh_actions_expressions")
  (#set! injection.include-children))

((block_mapping_pair
  key: (flow_node) @_key
  (#eq? @_key "if")
  value: (flow_node
    (plain_scalar
      (string_scalar) @_value)
    (#not-match? @_value "${{"))) @injection.content
  (#is-gh-actions-file? "") ; NOTE: NEW PREDICATE
  (#set! injection.language "gh_actions_expressions")
  (#set! injection.include-children))
```

### `is-gh-actions-file` predicate

To avoid injecting this grammar to files other than github actions, is
recommended to create a predicate named `is-gh-actions-file`.

> [!NOTE]
> The creation of this directive varies for each editor

This predicate will be the responsible to allow injection to files that matches
the name pattern `.github/workflows/*.ya?ml`.

## Implementations

### gh-actions.nvim

- [Parser register and new predicate][gh-actions-nvim-tree-sitter]
- [Yaml injection][gh-actions-nvim-yaml-injection]

## Troubleshooting

### AST errors within `bash` injections when using `run` key

![AST error within bash injection](https://i.imgur.com/zNcY7ox.png)

To avoid these errors, is recommended to surround the `expression` within a
`raw_string` node, string with single quotes `'`, i.e.:

```yaml
jobs:
  dry-run:
    name: dry-run
    runs-on: ubuntu-latest
    steps:
      - name: dry-run
        run: ./script.sh '${{ inputs.mode }}' --dry-run
```

![Correct bash AST by using raw_string](https://i.imgur.com/30cUWIJ.png)

#### What if I need it within a variable expansion?

![AST error within variable expansion](https://i.imgur.com/6AFtGAE.png)

Because variable expansion is done by using `$` prefix, the `${{` and `}}` nodes
will cause an AST error. To avoid, this declare an auxiliary bash variable or an
environment variable:

```yaml
jobs:
  dry-run:
    name: dry-run
    runs-on: ubuntu-latest
    steps:
      - name: dry-run
        run: |
          auxiliary_var='${{ inputs.mode }}'
          ./script.sh "$MY_VAR and $MODE" --dry-run
          ./script.sh "$MY_VAR and $auxiliary_var" --dry-run
        env:
          MODE: ${{ inputs.mode }}
```

![Correct bash AST by using auxiliary variables](https://i.imgur.com/AIiaqoe.png)

## References

- [Github Actions expressions documentation][gh-actions-expressions-docs]
- `if` conditional:
  - [run.steps\[\*\].if][gh-run-steps-if]
  - [jobs.\<job_id>.if][gh-jobs-jobid-if]
- [Gihub Actions Context documentation][gh-actions-context-docs]

## Thanks

Thanks to [@disrupted](https://github.com/disrupted) for creating
[tree-sitter-github-actions grammar][ts-github-actions], which is the base I
used to create this grammar.

[ci]: https://github.com/Hdoc1509/tree-sitter-gh-actions-expressions/actions/workflows/ci.yml/badge.svg
[discord]: https://img.shields.io/discord/1063097320771698699?logo=discord&label=discord
[matrix]: https://img.shields.io/matrix/tree-sitter-chat%3Amatrix.org?logo=matrix&label=matrix
[crates]: https://img.shields.io/crates/v/tree-sitter-gh-actions-expressions?logo=rust
[npm]: https://img.shields.io/npm/v/tree-sitter-gh-actions-expressions?logo=npm
[pypi]: https://img.shields.io/pypi/v/tree-sitter-gh-actions-expressions?logo=pypi&logoColor=ffd242
[gh-actions-expressions-docs]: https://docs.github.com/en/actions/reference/evaluate-expressions-in-workflows-and-actions
[gh-run-steps-if]: https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax#runsstepsif
[gh-jobs-jobid-if]: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idif
[gh-actions-context-docs]: https://docs.github.com/en/actions/reference/workflows-and-actions/contexts
[ts-github-actions]: https://github.com/disrupted/tree-sitter-github-actions
[gh-actions-nvim-tree-sitter]: https://github.com/Hdoc1509/gh-actions.nvim/blob/master/lua/gh-actions/tree-sitter.lua
[gh-actions-nvim-yaml-injection]: https://github.com/Hdoc1509/gh-actions.nvim/blob/master/queries/yaml/injections.scm
[release-branch]: https://github.com/Hdoc1509/tree-sitter-gh-actions-expressions/tree/release
