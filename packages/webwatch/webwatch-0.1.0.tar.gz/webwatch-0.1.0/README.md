# WebWatch

[WebWatch](https://github.com/vincentpfister/webwatch) is a simple command-line tool to monitor a web page or a specific
part of it for changes. When a change is detected, it raises an alert on the console and can optionally send an email
notification.

## Features

- Watch any URL.
- Target specific content using CSS selectors or XPath expressions.
- Configurable check interval.
- Console and email notifications.
- Built with modern Python tools: click, httpx, loguru, and lxml.

## Installation

This project uses uv for package and virtual environment management.

1. **Install uv**:
   Follow the [official instructions](https://docs.astral.sh/uv/getting-started/installation/) to install uv:

   ```bash
   # Example for Linux/macOS
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Create a virtual environment and install webwatch**:
   Clone this repository, then run:

    ```bash
    git clone https://example.com/webwatch.git
    cd webwatch
    uv venv
    source .venv/bin/activate
    uv pip install -e .
    ```

## Usage

The basic command requires a single URL argument.

```bash
webwatch <URL> [OPTIONS]
```


### Examples

- Watch a page for any change in the <body> every 30 seconds:

  ```bash
  webwatch https://example.com --period 30
  ```
- Watch the element with ID main-content:

  ```bash
  webwatch https://example.com --css "#main-content"
  ```
- Watch the first <h1> tag on a page using XPath:

  ```bash
  webwatch https://example.com --xpath "/html/body/div/h1"
  ```
- Send an email notification on change:

  ```bash
  webwatch https://example.com --css ".price" --email "your.email@example.com"
  ```

- watch an online clock to see if it changes:
  ```bash
  webwatch https://dayspedia.com/time/online/ --xpath /html/body/div[1]/main/section[1]/div[1]/div[2]
  ```

> Tip: You can use the _developper tools_ in your browser to inspect elements and find their CSS selectors or XPath expressions.

### Command-line Options


| Argument / Option | Description                                             | Default |
|-------------------|---------------------------------------------------------|---------|
| URL (required)    | The URL of the web page to watch.                       | -       |
| --p, --period     | Time period in seconds to check for changes.            | 60      | 
| --css             | CSS selector to target a specific part of the page.     | -       |
| --xpath           | XPath expression to target a specific part of the page. | //body  |
| --email           | Email address to send notifications to on change.       |         |
| --v, --version    | Show the version and exit.                              | -       |
| -h, --help        | Show the help message and exit.                         | -       |


### Email Notification Setup

To receive email notifications, you must configure your SMTP server settings using environment variables:

```bash
export SMTP_SERVER="smtp.example.com"
export SMTP_PORT="587" # Or 465 for SMTP_SSL
export SMTP_USER="your-username"
export SMTP_PASSWORD="your-password"
export SMTP_FROM_EMAIL="sender@example.com"
```

## UsageProject Structure

```
.
├── .gitlab-ci.yml # GitLab CI/CD pipeline configuration
├── LICENSE # MIT License file
├── pyproject.toml # Project metadata and dependencies
├── README.md # This file
├── src
│ └── webwatch
│ ├── __init__.py
│ ├── cli.py # Command-line interface logic (click)
│ ├── watcher.py # Core logic for watching and comparing
│ └── notifications.py # Notification handling
└── tests
└── test_watcher.py # Unit tests for the watcher
```

## Development and Contribution

We welcome contributions! Please follow these steps to contribute.

### Setting up the Development Environment

1. Install development dependencies, including `pytest` and `ruff`:
    ```bash
    uv pip install -e ".[dev]"
    # Note: You need to define a [project.optional-dependencies] table in pyproject.toml for this. 
    # For now, install them manually: 
    uv pip install pytest pytest-httpx ruff
    ```

2. Run formatting and linting:
   This project uses `ruff` for code formatting and linting.
   ```bash
   # Check formatting
   ruff format --check .
   
    # Apply formatting    
    ruff format .

   # Check for linting errors
   ruff check .
   ```

3. Run tests:
   Tests are written with pytest.
   ```bash
   pytest
   ```

### Contribution Guidelines

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes, ensuring you add or update tests as appropriate.
4. Ensure all checks (linting and tests) pass.
5. Submit a pull request with a clear description of your changes.
