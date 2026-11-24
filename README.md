# MSC Resolver Maubot Plugin

A bot plugin for [maubot](https://github.com/maubot/maubot) that posts links to
[Matrix Spec Changes](https://spec.matrix.org/unstable/proposals/) (MSCs) in a room
whenever a message contains the MSC's ID in the form `msc1234`.

## Install

Refer to [maubot's documentation](https://docs.mau.fi/maubot/usage/basic.html#uploading-plugins)
for information on how to upload this plugin into your maubot installion.

You can find a pre-built copy of this plugin (a `.mbp` file) via
the [releases page](https://github.com/matrix-org/maubot-msc-resolver/releases/latest).

## Usage

Invite an instance of the bot to a room and it should join automatically. It will then post
a notice containing information regarding an MSC whenever one is mentioned in a message!
`m.notice` messages are ignored.

## Development

This project uses [uv](https://docs.astral.sh/uv/).

```sh
uv sync                    # create .venv with maubot + dev tools
uv run ruff check .        # lint
uv run ruff format .       # format
uv run mbc build           # build the .mbp plugin file
```
