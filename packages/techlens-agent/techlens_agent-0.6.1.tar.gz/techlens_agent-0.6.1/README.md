[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](code_of_conduct.md)
# TechLens™ Agent

 TechLens Agent™ is one of many tools Crosslake uses to guide your critical technology decisions with data-driven confidence. To learn more, drop us a note at: techlens@crosslaketech.com.

## Requirements:
 - Python3 - Test with `python3 --version`
 - pip - Test with `pip -V`
 - SSH access to code repositories - Test with `git status`
 - Command line tool access to cloud hosting providers
 - Admin privileges on the computer used to run the agent (not required but recommended)
 - Outbound internet access (for posting results and fetching dependency metadata)
 - Your dependency management tools (e.g. `npm` or `yarn` or `maven`)

## To run the Agent:
 - Download the `techlens-agent` binary from crosslake
 - Run the agent `techlens-agent --config=/path/to/config`

## Config Options
 - If you want to check the output for yourself you can set `should_upload: false`, and use the flag `--output=/path/to/dir`. This will give you the chance to inspect what we collect before uploading. For large repositories, it is a lot of information, but we never upload your code or any credentials, just the summary data we collect.

## Troubleshooting:
### Python
 - Run `python3 -m pip install --upgrade pip setuptools wheel`
### git
 - Run `which git`, `git --version`
 - Run ` ssh -vT git@github.com` to test access to GitHub
###  AWS
 - Run `which aws`, `aws --version`
### Azure
 - Run `az git`, `az --version`
 - Run `az account subscription list` to check subscription Id
### Semgrep
 - Run `which semgrep`, `semgrep --version`
### pip
 - Run `which pip`
 - If no `pip`, run:
    `curl -o get-pip.py https://bootstrap.pypa.io/get-pip.py`
    `python get-pip.py`  OR `python3 get-pip.py`
 Run `sudo apt update`

 Copyright ©2023-2025 Crosslake Technologies.


## Run with Docker Compose
You can build and run the Techlens Agent container with Docker Compose. This mirrors the included run-docker.sh script but makes it easy to pass arguments and reuse mounts.

### Build the image
- docker compose -f docker-compose.yml build techlens-agent