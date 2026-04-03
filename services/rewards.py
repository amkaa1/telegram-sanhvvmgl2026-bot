from __future__ import annotations

from utils.constants import REWARD_THRESHOLDS


def check_reward_flags(user) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    count = user.invites_count
    if count >= 500 and not user.reward_500_sent:
        user.reward_500_sent = True
        hits.append((500, REWARD_THRESHOLDS[500]))
    if count >= 1000 and not user.reward_1000_sent:
        user.reward_1000_sent = True
        hits.append((1000, REWARD_THRESHOLDS[1000]))
    if count >= 2000 and not user.reward_2000_sent:
        user.reward_2000_sent = True
        hits.append((2000, REWARD_THRESHOLDS[2000]))
    if count >= 5000 and not user.reward_5000_sent:
        user.reward_5000_sent = True
        hits.append((5000, REWARD_THRESHOLDS[5000]))
    return hits
