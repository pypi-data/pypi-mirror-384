# ArtiNator: Your Agentic Systems and Network Coding Assistant

Welcome to ArtiNator, an automated coding assistant designed for systems and
networks programmers. ArtiNator leverages the power of Large Language Models
(LLMs) to help you navigate, understand, and manipulate your project's
environment efficiently.

## 🌟 Why Dynamic Prompts?

Traditional prompts become outdated as your code evolves. Our dynamic prompt
system ensures your AI interactions remain relevant, accurate, and valuable
throughout your development lifecycle.

**Stop maintaining prompts manually - let them maintain themselves!**

## Features

- **Dynamic Prompt Creation**: ArtiNator dynamically builds prompts based on
  your input, enhancing the relevance and accuracy of responses.
- **Contextual Awareness**: Automatically attaches file contents and command
  outputs to the prompt context, ensuring comprehensive answers.
- **Command Execution**: Runs shell commands to gather necessary information or
  execute tasks, making it an active participant in your workflow.

## Key Commands

### `shoot` Command

The `shoot` command is designed for one-shot LLM queries without looping. It
parses the prompt to:

- Automatically attach the content of any file path mentioned in the prompt.
- Run any command enclosed in `^` symbols and attach its output to the context.
- If the command output contains relative paths, ArtiNator will attach those
  file contents as well.

**Usage Examples:**

```bash
# To explain foo.py and attach the file content to the context
artinator shoot explain my/foo.py

# To run "your command", parse its output, and attach it to the context
# Useful for debugging tracebacks that include relative paths
artinator shoot what breaks ^my command^ is it a bug in foo.py
```

### `loop` Command

The `loop` command allows the LLM to run bash commands iteratively until it can
answer your query comprehensively. It's perfect for tasks that require ongoing
interaction or more complex problem-solving.

**Usage Example:**

```bash
# To fix a test, ArtiNator will suggest and run commands until the issue is resolved
artinator loop fix some test
```

**How it Works:**

- ArtiNator suggests one complete, executable shell command at a time within ```suggestedcommand``` blocks.
- It uses verbose flags where applicable to gather detailed context.
- The assistant avoids interactive commands and placeholders, ensuring all commands are ready to execute.
- It navigates the project directory structure using commands like `ls`, `cat`, or `grep` to inspect files and gather necessary context.
- ArtiNator stops suggesting commands once it has enough context to provide a complete, relevant answer.

## How to Use

1. **Install ArtiNator**: Use `pip install artinator`
2. **Run Commands**: Use `artinator shoot` for one-shot queries or `artinator loop` for iterative problem-solving.
3. **Interact**: Respond to ArtiNator's command suggestions with 'y' (yes), 'n' (no), or 'a' (accept all) to control command execution.

ArtiNator is designed to enhance your productivity by automating the gathering
of context and providing intelligent, context-aware responses to your queries.
Dive into your projects with confidence, knowing ArtiNator is there to assist
every step of the way!
