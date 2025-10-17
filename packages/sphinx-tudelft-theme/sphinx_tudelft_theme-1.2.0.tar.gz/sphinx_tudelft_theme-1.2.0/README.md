# Sphinx extension: TU Delft theme 

## Introduction

The default theme in JupyterBooks is usually not desired and need to be changed by adding custom stylesheets. The **Sphinx-TUDelft-theme** extension provides a simple solution to have a uniform theme across all the books created at Delft University of Technology that matches the TU Delft identity.

## What does it do?

This extension applies styling changes, being

- particular colours (different colors for light and dark themes) for:
    - admonitions (e.g. hint, note, tip, error, etc.),
    - proofs (e.g. theorem, axiom, lemma, corollary, etc.),
    - exercises,
    - buttons,
    - badges,
    - custom components,
    - $\LaTeX$,
    - the primary and secondary color of the book (mainly used for typesetting links).
- particular icons for:
    - proofs (e.g. theorem, axiom, lemma, corollary, etc.),
    - exercises,
    - custom components.

Unless specified otherwise, see [Usage](#usage), this extension also automatically sets:

- a Delft University of Technology logo;
- a Delft University of Technology favicon;
- the Delft University of Technology preferred fonts;
- rendering text inside MathJax as the surrounding text;
- an always visible logo (i.e. a sticky logo);
- a bigger title.

You can see how the TU Delft theme looks like applied in this [example book](http://teachbooks.io/TU-Delft-Theme-Example/).

## Installation
To implement the TU Delft theme, follow these steps:

**Step 1: Install the Package**

Install the `sphinx-tudelft-theme` package using `pip`:
```
pip install sphinx-tudelft-theme
```

**Step 2: Add to `requirements.txt`**

Make sure that the package is included in your project's `requirements.txt` to track the dependency:
```
sphinx-tudelft-theme
```

**Step 3: Enable in `_config.yml`**

In your `_config.yml` file, add the extension to the list of Sphinx extra extensions (**important**: underscore, not dash this time):
```yaml
sphinx: 
    extra_extensions:
        .
        .
        .
        - sphinx_tudelft_theme
        .
        .
        .
```

The following Sphinx extra extensions (if used) must be added _before_ this extension:

- `sphinx_proof`
- `sphinx_exercise`
- `teachbooks_sphinx_grasple`

If this is forgotten, the CSS of this extension cannot be applied correctly.

## Usage

By following the steps above, the theme will be applied automatically. To see the examples of usage visit the [TeachBooks manual](https://teachbooks.io/manual/intro.html).

To use the defined colors inside $\LaTeX$ rendered with MathJax, one should use the command
```
\class{<color>}{<math>}
```
where `<color>` is one of the following colors:

- tud-red
- tud-blue
- tud-green
- tud-raspberry
- tud-yellow
- tud-darkGreen
- tud-orange
- tud-cyan
- tud-gray
- tud-purple
- tud-pink
- tud-darkBlue

and `<math>` is the $\LaTeX$ that should be rendered in the color `<color>`.

If a Delft University of Technology logo should not be set (i.e. use logos defined by the user), include the following in your `_config.yml` file:
```yaml
sphinx:
  config:
    ...
    tud_change_logo: false
```

If a Delft University of Technology favicon should not be set (i.e. use a favicon defined by the user), include the following in your `_config.yml` file:
```yaml
sphinx:
  config:
    ...
    tud_change_favicon: false
```

If the Delft University of Technology fonts should not be set (i.e. use fonts defined by the user), include the following in your `_config.yml` file:
```yaml
sphinx:
  config:
    ...
    tud_change_fonts: false
```

If rendering text inside MathJax should not be the same as the surrounding html, include the following in your `_config.yml` file:
```yaml
sphinx:
  config:
    ...
    tud_change_mtext: false
```

If a sticky logo is not preferred, include the following in your `_config.yml` file:
```yaml
sphinx:
  config:
    ...
    tud_sticky_logo: false
```

If the title styling should not be altered (i.e. use title styling defined by the user), include the following in your `_config.yml` file:

```yaml
sphinx:
  config:
    ...
    tud_change_titlesize: false
```

## Contribute
This tool's repository is stored on [GitHub](https://github.com/TeachBooks/Sphinx-TUDelft-theme). The `README.md` of the branch `Manual` is also part of the [TeachBooks manual](https://teachbooks.io/manual/intro.html) as a submodule. If you'd like to contribute, you can create a fork and open a pull request on the [GitHub repository](https://github.com/TeachBooks/Sphinx-TUDelft-theme). To update the `README.md` shown in the TeachBooks manual, create a fork and open a merge request for the [GitHub repository of the manual](https://github.com/TeachBooks/manual). If you intent to clone the manual including its submodules, clone using: `git clone --recurse-submodulesgit@github.com:TeachBooks/manual.git`.
