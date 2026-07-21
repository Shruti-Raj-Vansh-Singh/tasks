# Audit Log Format

This page documents the on-disk format guarantees for security audit logs
produced by this library. It applies to any renderer that emits audit records,
and to any code that formats an event for such a log.

## One record per line

Every audit event is exactly one physical line. A record is terminated by a
single newline that the logging output layer appends; the rendered record must
not contain an embedded line terminator of its own.

This is a hard requirement, not a formatting preference. Audit logs are parsed
one line per record by downstream tooling (SIEM ingestion, `grep`, log shippers,
incident review). If a single logged event can span more than one physical line,
that guarantee is broken.

## Field values are untrusted

Audit events routinely include attacker-influenced values: usernames, resource
identifiers, request parameters, user-agent strings, search terms. A renderer
must treat every value as untrusted text.

In particular, a value must never be able to terminate the current record or
begin a new one. Control characters that would forge or split records must be
neutralized before the value is written. At minimum this covers:

- line feed (`\n`, U+000A)
- carriage return (`\r`, U+000D)
- and other C0 control characters (U+0000..U+001F) and U+007F

The required behavior is to render such characters in an escaped, single-line
form (for example, a newline rendered as the two characters backslash-`n`) so
that the value stays on the same line as the rest of the record. Silently
dropping the characters is also acceptable as long as the one-record-per-line
guarantee holds; passing them through verbatim is not.

## Why this matters (log forging, CWE-117)

If a value is written verbatim, an attacker who controls it can embed a newline
followed by text that looks like a second, legitimate audit record. For example,
a username submitted as

```
alice
outcome=success event=admin_grant target=attacker
```

would, if written without neutralizing the newline, produce two physical lines:
the real record for `alice`, and a forged `event=admin_grant` record that no code
ever logged. Downstream tooling cannot tell the forged line from a real one. This
is log injection / log forging (CWE-117), and it is treated as a security defect,
not a cosmetic one.

## Example

A well-formed audit line:

```
event=login user=alice outcome=success
```

The same event where the username contains a newline must still be a single
line, with the newline escaped rather than literal:

```
event=login user=alice\noutcome=success event=admin_grant outcome=success
```

(The `\n` above is the two-character escape, not a real line break.)
