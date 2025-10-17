# LLM Tools Browser History

A tool for the [llm](https://llm.datasette.io/) command line that allows searching local browser history files.

The tool currently supports Chrome, Firefox, and Safari browser histories.

# Usage

Install for use with llm:

```sh
# install the plugin:
llm install llm-tools-browser-history

# see available plugins:
llm plugins

...
  {
    "name": "llm-tools-browser-history",
    "hooks": [
      "register_tools"
    ],
    "version": "0.1.0"
  },
...
```

Examples:

```sh
# Search for pages mentioning yosemite in title or URL
llm -T llm_time -T BrowserHistory "what pages about yosemite did I look up recently?"

# Limit to Firefox and Safari sources
llm -T llm_time -T 'BrowserHistory(["firefox","safari"])' "what pages about yosemite did I look up recently?"

llm -T BrowserHistory "show a table of how much I used each browser over the past year by month"
```


# Security and Privacy

**Warning**: This tool has read-access to your entire browser history. You risk sending
this highly sensitive personal data to third-party services (like OpenAI).

See [the lethal trifecta article](https://simonw.substack.com/p/the-lethal-trifecta-for-ai-agents) for more information about the risks of using tools like this with LLMs.

To mitigate the risks of data leakage:
- Only runs queries against a copy of the target browser's history database (so any malicious modification has no effect).
- Limits the number of results to no more than 100 records per tool use.
- Does not return the entire browser history record. This tool will return a subset of fields (URL, title, visit date). Query parameters are stripped from URLs and timestamps only include the date (not the time).

## Dev setup

```bash
make setup
make test

pip install -e .

llm -T llm_time -T BrowserHistory --td "what pages about yosemite did I look up recently?"
```

# ADRs

* [1. Python project](docs/adr/0001-python-project.md)
* [2. Expose browser history as an LLM toolbox tool](docs/adr/0002-browser-tool.md)
* [3. Normalized SQL interface](docs/adr/0003-normalized-sql-interface.md)
