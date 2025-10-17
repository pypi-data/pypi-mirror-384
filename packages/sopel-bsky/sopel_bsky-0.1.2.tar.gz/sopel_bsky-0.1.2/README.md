# sopel-bsky

Fetch info about Bluesky links in your IRC conversations using Sopel.

## Installing

Releases are hosted on PyPI, so after installing Sopel, all you need is `pip`:

```shell
$ pip install sopel-bsky
```

Please note that the `atproto` package maintains a strict Python version policy,
so installation might not be possible on a given Python release even if Sopel
itself is compatible with it. Drop by [GitHub][gh-sopel-bsky] and open a PR or
issue if you notice that the dependencies are outdated.

[gh-sopel-bsky]: https://github.com/sopel-irc/sopel-bsky

## Configuring

The easiest way to configure `sopel-bsky` is via Sopel's configuration
wizard—simply run `sopel-plugins configure bsky` and enter the values for which
it prompts you.

At present, you need to give the plugin a Bluesky account for which you don't
mind the handle & password being stored in Sopel's config file in plain text.
It's recommended to create a new account specifically for your bot, instead of
using your real account's credentials (if you have one).

## Maintenance Note

This plugin as it exists now is mostly a proof of concept, just to have some
minimal level of parity with the Sopel ecosystem's support for Twitter (it is
_not_ called X!) and Mastodon.

Showing details for links to Bluesky users and posts was tested and confirmed
working as of the last release's publish date. The plugin is published in the
hope that it will be useful; in case of breakage or needed improvements, pull
requests are always welcome.
