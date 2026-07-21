# FairPriorityQueue ordering

`FairPriorityQueue` adds per-key fairness on top of ordinary priority
queueing. Items carry an integer `priority` (lower number = higher priority)
and a `key` (a source identifier such as a domain). The goal is that, when
many keys have work queued at the same priority, no single noisy key can
monopolize the consumer -- turns are shared across the keys that have items
ready at that priority.

Fairness is a tie-breaker *inside* a priority level. It must not change the
ordering guarantees callers already rely on from a priority queue. Two
invariants are absolute and take precedence over fairness:

## 1. Priority is strict

`pop()` must always return an item from the highest-priority (lowest
-numbered) non-empty level that currently exists. A lower-priority item must
never be returned while any higher-priority item is queued. This holds even
as items arrive over time: if, after some pops at priority 5, a new priority
1 item is pushed, the very next `pop()` must return that priority 1 item --
fairness rotation at priority 5 does not carry over or delay a
higher-priority item. Fairness only ever chooses *among keys at the single
highest-priority non-empty level*.

## 2. FIFO within a (priority, key)

Within one priority level and one key, items must come out in the order they
were pushed (first-in, first-out). Fairness rotates *between* keys; it must
never reorder items that share the same priority and key.

## Fairness rule

Among the keys that have items ready at the current highest priority, `pop()`
should not keep returning items from the same key while other keys at that
priority still have items waiting. Rotating round-robin across those keys is
the intended behavior. A key with no items at the current priority is simply
skipped. When only one key has items at the current priority, every pop comes
from that key until another key appears or the level drains.

## Summary

Given the highest-priority non-empty level, spread `pop()` turns across the
keys that have items there, in FIFO order within each key. Never let fairness
promote a lower-priority item ahead of a higher-priority one, and never let
it reorder items within the same priority and key.
