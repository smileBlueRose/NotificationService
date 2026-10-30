from dataclasses import dataclass

from common.models import Channel

RETRY_DELAYS_SECONDS = {
    "retry-5s": 5,
    "retry-30s": 30,
    "retry-5m": 300,
}


@dataclass(frozen=True)
class RetryTopic:
    name: str
    delay_seconds: int


@dataclass(frozen=True)
class ChannelTopics:
    main: str
    retries: list[RetryTopic]
    dead_letter: str

    @classmethod
    def for_channel(cls, channel: Channel) -> "ChannelTopics":
        retries = [
            RetryTopic(name=f"{channel.value}-{suffix}", delay_seconds=delay_seconds)
            for suffix, delay_seconds in RETRY_DELAYS_SECONDS.items()
        ]
        return cls(main=channel.value, retries=retries, dead_letter=f"{channel.value}-dlq")

    def next_topic_after(self, attempts: int) -> str:
        if attempts <= len(self.retries):
            return self.retries[attempts - 1].name
        return self.dead_letter