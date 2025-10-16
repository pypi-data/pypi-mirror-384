# Markten

Assess your students' work with all of the delight and none of the tedium.

Markten is an automation framework aimed at reducing the pain of marking
student assignments in bulk. By writing a simple recipe, you can define the
steps you take to mark an assignment, which can be anything from fetching
submissions, compiling their code, viewing their codebase in an IDE, or running
a test suite. It's all done with simple readable Python, with enough power
under the hood to make even the most annoying workflows trivial.

## Installing

```bash
$ pip install markten
...
Successfully installed markten-1.0.0
```

Or to install in an independent environment, you can use `pipx` or `uv`:

```bash
$ pipx install markten
  installed package markten 1.0.0, installed using Python 3.12.6
  These apps are now globally available
    - markten
done! ✨ 🌟 ✨
$ uv tool install markten
Resolved 10 packages in 2ms
Installed 10 packages in 11ms
 + aiosqlite==0.21.0
 + click==8.2.1
 + humanize==4.12.3
 + markdown-it-py==3.0.0
 + markten==1.0.0
 + mdurl==0.1.2
 + platformdirs==4.3.8
 + pygments==2.19.1
 + rich==13.9.4
 + typing-extensions==4.14.0
Installed 1 executable: markten
```

## Running recipes

You can execute the recipe directly, like you would any Python script:

```sh
$ python my_recipe.py
...
```

You can also use the `markten` executable if you want to keep `markten`'s
dependencies in an isolated environment. The Python script you provide as
an argument is executed within that environment.

```sh
$ markten my_recipe.py
...
```

## How it works

Define your recipe parameters. For example, this recipe takes in git repo names
from stdin.

```py
from markten import Recipe, ActionSession, parameters, actions

marker = Recipe("Clone COMP1010 repos")

marker.parameter("repo", parameters.stdin("Repo name"))
```

Write simple marking recipes by defining simple functions for each step.

```py
# Functions can take arbitrary parameters, as long as those parameters were
# defined earlier in the script.
# Using the `Recipe.step` decorator allows us to register an action as a step
# to the recipe.
@marker.step
async def setup(action: ActionSession, repo: str):
    """Set up marking environment"""
    # Clone the given git repo to a temporary directory
    directory = await actions.git.clone(action, f"git@github.com:COMP1010UNSW/{repo}.git")
    return {
        "directory": directory,
    }
```

The values returned by your previous steps can be used in later steps, just
by giving the function parameters the same name.

```py
@marker.step
def open_code(action: ActionSession, directory: Path):
    """Open the cloned git repo in VS Code"""
    return actions.editor.vs_code(action, directory)
```

Then run the recipe. It'll run for every permutation of your parameters, making
it easy to mark in bulk.

```py
marker.run()
```

For more examples, see the examples directory.
