# DNS Archiver

A Simple DNS lookup tool that dumps all records for archiving.

Useful to run on a schedule to monitor DNS changes which can help if a customer modifies their DNS and breaks their site you can quickly debug and tell what the old (correct) records were.

## Install

The recommended way to run is with `uvx` (part of [uv](https://docs.astral.sh/uv/)):

```bash
# Run directly without installing (recommended)
uvx dns-archiver example.com

# Or install persistently
uv tool install dns-archiver

# Alternative: use pipx
pipx install dns-archiver
```

## Usage

```
% dns-archiver --help

Usage: dns-archiver [OPTIONS] NAME

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    name      TEXT  DNS name to lookup [required]                                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --record                              [all|a|aaaa|cname|txt|ns|mx|soa]  The DNS record to archive [default: ALL]     │
│ --ttl                     --no-ttl                                      Include TTL values or not [default: ttl]     │
│ --nameserver          -n              TEXT                              DNS nameserver(s) to query (can be specified │
│                                                                         multiple times)                              │
│ --version             -v                                                                                             │
│ --install-completion                                                    Install completion for the current shell.    │
│ --show-completion                                                       Show completion for the current shell, to    │
│                                                                         copy it or customize the installation.       │
│ --help                                                                  Show this message and exit.                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Examples

### Basic Usage

```bash
# Archive all DNS records for a domain
dns-archiver example.com

# Archive only A records
dns-archiver example.com --record A

# Archive without TTL values
dns-archiver example.com --no-ttl
```

### Using Custom Nameservers

```bash
# Query using Google's DNS
dns-archiver example.com -n 8.8.8.8

# Query using Cloudflare's DNS
dns-archiver example.com -n 1.1.1.1

# Query with multiple nameservers (uses first available)
dns-archiver example.com -n 8.8.8.8 -n 1.1.1.1

# Check DNS propagation across different providers
dns-archiver example.com -n 8.8.8.8 > google-dns.json
dns-archiver example.com -n 1.1.1.1 > cloudflare-dns.json
diff google-dns.json cloudflare-dns.json
```

### Monitoring and Archiving

```bash
# Save DNS snapshot to a file with timestamp
dns-archiver example.com > "dns-$(date +%Y%m%d-%H%M%S).json"

# Query specific record types for monitoring
dns-archiver example.com --record MX -n 8.8.8.8
```
