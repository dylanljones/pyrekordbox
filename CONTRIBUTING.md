# Contributing

If you encounter an issue or want to contribute to pyrekordbox, please feel free to get in touch,
[open an issue][issue] or create a new [pull request][pulls]!

pyrekordbox is tested on Windows and MacOS, however some features can't be tested in
the CI setup since it requires a working Rekordbox installation.

## Pre-commit Hooks

We are using the [pre-commit framework] to automatically run a linter and code formatter
at commit time. This ensures that every commit fulfills the basic requirements to be
mergeable and follows the coding style of the project.

The pre-commit hooks can be installed via
````sh
$ pre-commit install
````

## Commit Message Format

A format influenced by [Angular commit message].

```text
<type>(<scope>): <subject>
<BLANK LINE>
<body>
<BLANK LINE>
<footer>
```

### Type

Must be one of the following:

- **feat:** A new feature
- **fix:** Bug fixes or improvements
- **perf:** A code change that improves performance
- **refactor:** Code refactoring
- **ci:** Changes to CI configuration files and scripts
- **docs:** Documention changes
- **build:** Updating Makefile etc, no production code changes
- **test:** Adding missing tests or correcting existing tests
- **update** Other configurations updates

### Scope (optional)

The scope should specify the affected part of the project.
The following is a list of possible scopes:

- **config**: Configuration handling
- **xml**: Rekordbox XML database handling
- **db**: Rekordbox v6 database handling
- **anlz**: ANLZ file handling
- **mysetting**: MySettings file handling


### Subject

Use the summary field to provide a succinct description of the change:
- use the imperative, present tense: "change" not "changed" nor "changes"
- don't capitalize the first letter
- no dot (.) at the end

### Body (optional)

Just as in the summary, use the imperative, present tense: "fix" not "fixed" nor "fixes".

Explain the motivation for the change in the commit message body.
This commit message should explain why you are making the change. You can include a comparison of the previous behavior with the new behavior in order to illustrate the impact of the change.

### Footer (optional)

The footer can contain information about breaking changes and deprecations and is also the place to reference GitHub issues, Jira tickets, and other PRs that this commit closes or is related to. For example:
```
BREAKING CHANGE: <breaking change summary>
<BLANK LINE>
<breaking change description + migration instructions>
<BLANK LINE>
<BLANK LINE>
Fixes #<issue number>
```

or

```
DEPRECATED: <what is deprecated>
<BLANK LINE>
<deprecation description + recommended update path>
<BLANK LINE>
<BLANK LINE>
Closes #<pr number>
```

Breaking Change section should start with the phrase "BREAKING CHANGE: " followed by a summary of the breaking change, a blank line, and a detailed description of the breaking change that also includes migration instructions.

Similarly, a Deprecation section should start with "DEPRECATED: " followed by a short description of what is deprecated, a blank line, and a detailed description of the deprecation that also mentions the recommended update path.

[issue]: https://github.com/dylanljones/pyrekordbox/issues
[pulls]: https://github.com/dylanljones/pyrekordbox/pulls
[pre-commit framework]: https://pre-commit.com/
[Angular commit message]: https://github.com/angular/angular/blob/master/CONTRIBUTING.md#commit-message-format
