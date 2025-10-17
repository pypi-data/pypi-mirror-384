"""sopel-bsky

Fetch info about Bluesky links in your IRC conversations using Sopel.
"""
from __future__ import annotations

from datetime import datetime, timezone

import atproto

from sopel import plugin
from sopel.config.types import (
    NO_DEFAULT,
    SecretAttribute,
    StaticSection,
    ValidatedAttribute,
)
from sopel.tools import time


def _parse_iso_datetime(timestamp: str) -> datetime:
    parsed = datetime.fromisoformat(timestamp)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


class BskySection(StaticSection):
    handle = ValidatedAttribute('handle', default=NO_DEFAULT)
    password = SecretAttribute('password', default=NO_DEFAULT)


def configure(config):
    config.define_section('bsky', BskySection, validate=False)
    config.bsky.configure_setting(
        'handle',
        'Bluesky account handle:',
    )
    config.bsky.configure_setting(
        'password',
        'Bluesky account password:',
    )


def setup(bot):
    bot.config.define_section('bsky', BskySection)

    settings = bot.config.bsky

    client = atproto.Client()
    client.login(settings.handle, settings.password)

    bot.memory['bsky_client'] = client


@plugin.output_prefix('[skeet] ')
@plugin.url(
    r'https?://bsky\.app/profile/(?P<handle>[^/]+)/post/(?P<post_id>[^/]+)')
def skeet_info(bot, trigger):
    client = bot.memory['bsky_client']
    did = client.resolve_handle(trigger.group('handle')).did
    post = client.get_post(trigger.group('post_id'), did)
    profile = client.get_profile(did)

    now = trigger.time
    then = _parse_iso_datetime(post.value.created_at)
    timediff = (now - then).total_seconds()

    template = '{name} (@{handle}) | {reltime} | {text}'
    bot.say(
        template.format(
            name=profile.display_name,
            handle=profile.handle,
            reltime=time.seconds_to_human(timediff),
            text=post.value.text,
        ),
        truncation=' […]',
    )


@plugin.output_prefix('[skeeter] ')
@plugin.url(
    r'https?://bsky.app/profile/(?P<handle>[^/]+)$')
def skeeter_info(bot, trigger):
    client = bot.memory['bsky_client']
    profile = client.get_profile(trigger.group('handle'))

    template = (
        '{name} (@{handle}) | Following {following} | Followed by {followers}'
        ' | {skeets} skeets | {bio}'
    )
    bot.say(
        template.format(
            name=profile.display_name,
            handle=profile.handle,
            following=profile.follows_count,
            followers=profile.followers_count,
            skeets=profile.posts_count,
            bio=profile.description,
        ),
        truncation=' […]',
    )
