# Filechat

A file-based AI chat tool designed to integrate with Visual Studio Code (VS Code), enabling you to engage with a Large Language Model (LLM) directly within a Markdown file.

## Requirements

### Python 3.12.2

https://www.python.org/downloads/release/python-3122/

### Python packages

See [`requirements.txt`](requirements.txt).

### Visual Studio Code

https://code.visualstudio.com/

## Usage

### Cloning the repository and installing dependencies

1.  Clone the repository:

    ```sh
    git clone https://github.com/noveky/filechat.git
    ```

2.  Ensure that Python and `pip` are installed on your system.
3.  Create a Python virtual environment in the repository. _(Optional)_
4.  Install project dependencies:

    ```sh
    pip install -r requirements.txt
    ```

### Building a workflow in VS Code

1.  Open the repository with VS Code.

2.  Install the [_Code Runner_](https://marketplace.visualstudio.com/items?itemName=formulahendry.code-runner) extension (`formulahendry.code-runner`) for VS Code.

3.  Specify the run code command for Markdown files in `.vscode/settings.json`.

    -   For Windows:

        ```json
        // .vscode/settings.json
        {
            "code-runner.executorMap": {
                "markdown": "cd $dir && ..\\run.ps1 $fullFileName"
            }
        }
        ```

    -   For macOS/Linux:

        ```json
        // .vscode/settings.json
        {
            "code-runner.executorMap": {
                "markdown": "cd $dir && bash ../run.sh $fullFileName"
            }
        }
        ```

4.  Install the [_Markdown All in One_](https://marketplace.visualstudio.com/items?itemName=yzhang.markdown-all-in-one) extension (`yzhang.markdown-all-in-one`).

    This extension enables you to open a preview panel for a Markdown file (default keyboard shortcut is `Ctrl + K` `V`), where you can read the rendered Markdown content more easily.

### Configuring the app

#### Specifying OpenAI API key and base URL

To access a chat model, you need to specify the OpenAI API key and base URL.

There are three ways to do that:

1.  Set system environment variables `OPENAI_API_KEY` and `OPENAI_API_URL` .
2.  Create a `.env` file in the root directory of the repository and set the two environment variables in the file.

    ```env
    OPENAI_API_KEY=<your_api_key>
    OPENAI_API_URL=<your_base_url>
    ```

3.  Specify the API key and the base URL in the app configuration file introduced below.

#### Customizing app configurations

You can customize the app configurations in `config.yaml`.

Here is a template, and you can choose what you want to specify:

```yaml
# ---- Chat Completion ----
model: # Name of your preferred completion model
temperature: # Your preferred `temperature` parameter for the model (optional)
max_tokens: # Your preferred `max_tokens` parameter for the model (optional)

# ---- App Behaviors ----
max_retries: # How many times to retry (default is 3)
print_response: # Whether to print the response in standard output (default is true)
stream_for_file: # Whether to append the response to the file token by token or as a whole (default is true)

# ---- OpenAI API ----
api_key: # OpenAI API key (overrides the environment variable `OPENAI_API_KEY` if specified)
base_url: # OpenAI base URL (overrides the environment variable `OPENAI_API_URL` if specified)
```

### Chatting with an LLM in a file

Here is a quick guide to get yourself started:

1.  Make a `chats` directory in the repository and create a Markdown file in it (e.g. `New Chat.md`).
2.  Type a message in the Markdown file.

    ```markdown
    Tell me a joke.
    ```

3.  Save the file, and run _Filechat_ on the current file by hitting "Run Code" (default keyboard shortcut is `Ctrl + Alt + N`).

    Non-structured file content is regarded as a user message, so the file gets formatted into a `# User` heading followed by the original content.

    After a few seconds, hopefully you will see the LLM response get appended to the end of the file. The new `# User` heading prompts you continue the conversation.

    ```markdown
    # User

    Tell me a joke.

    # Assistant

    Why don't skeletons fight each other?

    They don't have the guts!

    # User

    |
    ```

4.  Type your reply message and follow step 3 to continue chatting.

### Adding a system prompt

Besides user messages, you can optionally include a system prompt, labeled with a `# System` heading. This is a special section that sets the context or provides initial instructions for the model before processing user inputs.

```markdown
# System

This is a system prompt.

# User

This is a user message.
```

### Adding file-wise configurations

At the very beginning of your chat file, you can include a front matter section. This section is enclosed within triple dashes (`---`) and is written in YAML format. It allows you to specify file-wise configurations that override the app configurations.

```yaml
---
model: gpt-4o
temperature: 0.7
---
```
