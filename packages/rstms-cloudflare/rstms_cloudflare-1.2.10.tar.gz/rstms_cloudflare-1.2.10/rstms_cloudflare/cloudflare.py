"""Cloudflare API Client"""

import json
import os
import re

import CloudFlare


class API:

    RECORD_TYPES = ["A", "AAAA", "CNAME", "MX", "NS", "SOA", "TXT", "SRV", "LOC", "SSHFP", "CAA", "TLSA"]
    IMPORT_TYPES = ["A", "AAAA", "CNAME", "MX", "TXT", "SRV"]
    PRIORITY_TYPES = ["MX", "SRV"]

    DEFAULT_PRIORITY = 10
    DEFAULT_WEIGHT = 5
    DEFAULT_TTL = 60

    MAX_ZONES = 128

    def __init__(
        self,
        *,
        token=None,
        json=False,
        quiet=False,
        raw=False,
        include_id=False,
        include_ttl=False,
        include_key=False,
        output_function=None,
        by_key=False,
        by_id=False,
        debug=False,
    ):
        token = token or os.environ["CLOUDFLARE_AUTH_TOKEN"]
        self.client = CloudFlare.CloudFlare(token=token)
        self.json = json
        self.raw = raw
        self.quiet = quiet
        self.include_id = include_id
        self.include_ttl = include_ttl
        self.include_key = include_key
        self.by_key = by_key
        self.by_id = by_id
        self.output_function = output_function or print
        self.debug = debug

    def output(self, data):
        if self.quiet:
            return
        if self.json:
            data = json.dumps(data, indent=2)
        elif not data:
            return
        self.output_function(data)

    def get_zones(self):
        return self.client.zones.get(params={"per_page": self.MAX_ZONES})

    def get_zone_id(self, domain):
        zones = self.get_zones()
        for z in zones:
            if z["name"] == domain:
                return z["id"]
        raise ValueError(f"unknown domain {domain}")

    def get_zone_records(self, domain):
        records = {}
        zone_id = self.get_zone_id(domain)
        records = self.client.zones.dns_records.get(zone_id, params={"per_page": self.MAX_ZONES})
        return records

    def parse_host(self, name, domain):
        if name in ["@", domain]:
            name = domain
        else:
            name = ".".join([name, domain])
        name = name.strip(".")
        return name

    def delete_records(self, domain, records):
        deleted = [self.delete_record(domain, record) for record in records]
        if self.json:
            return deleted
        else:
            return "\n".join(deleted)

    def delete_record(self, domain, record):
        record_id = record["id"]
        zone_id = self.get_zone_id(domain)
        ret = self.client.zones.dns_records.delete(zone_id, record_id)
        if self.json:
            return ret
        else:
            return ret["id"]

    def add_record(self, domain, type, host, content, ttl=None, priority=None, weight=None, port=None):
        zone_id = self.get_zone_id(domain)
        host = self.parse_host(host, domain)
        if ttl is None:
            ttl = self.DEFAULT_TTL
        if type in self.PRIORITY_TYPES and priority is None:
            priority = self.DEFAULT_PRORITY
        record = dict(type=type, name=host, content=content, ttl=ttl)
        if type == "MX":
            record["priority"] = priority
        elif type == "SRV":
            if port is None:
                raise ValueError("port is required for SRV record")
            if weight is None:
                weight = self.DEFAULT_WEIGHT
            record["data"] = dict(port=port, priority=priority, target=record.pop("content"), weight=weight)
        ret = self.client.zones.dns_records.post(zone_id, data=record)
        if self.json:
            return ret
        else:
            return ret["id"]

    def update_records(self, domain, records):
        updated = [self.update_record(domain, record) for record in records]
        if self.json:
            return updated
        else:
            return "\n".join(updated)

    def update_record(self, domain, record):
        dns_record_id = record["id"]
        zone_id = self.get_zone_id(domain)
        update = dict(
            name=record["name"],
            type=record["type"],
            content=record["content"],
            ttl=record["ttl"],
            proxied=record["proxied"],
        )
        if record["type"] == "SRV":
            # SRV record update uses data dict for port, priority, weight, target
            update.pop("content")
            update["data"] = record["data"]
        elif record["type"] == "MX":
            update["priority"] = record["priority"]
        ret = self.client.zones.dns_records.patch(zone_id, dns_record_id, data=update)

        if self.json:
            return ret
        else:
            return ret["id"]

    def format_host(self, domain, record):
        if "host" in record:
            return record["host"]
        host = record["name"]
        if host.endswith(domain):
            host = host[: -1 - len(domain)]
        if not host:
            host = "@"
        return host

    def format_record(self, domain, record):
        if self.raw:
            return record

        out = dict(
            id=record["id"],
            key=self.format_key(domain, record),
            zone=domain,
            host=self.format_host(domain, record),
            fqdn=record["name"],
            type=record["type"],
            content=record["content"],
            priority=record.get("priority", record.get("data", {}).get("priority", None)),
            weight=record.get("data", {}).get("weight", None),
            port=record.get("data", {}).get("port", None),
            protocol=self.format_protocol(domain, record),
            ttl=record["ttl"],
        )

        if self.json:
            return out

        fields = []
        if self.include_id:
            fields.append(out["id"])
        if self.include_key:
            fields.append(out["key"])
        fields.append(out["type"])
        fields.append(out["protocol"])
        fields.append(out["priority"])
        fields.append(out["host"])
        if record["type"] == "TXT":
            fields.append('"' + out["content"] + '"')
        else:
            fields.append(out["content"])
        if self.include_ttl:
            fields.append(out["ttl"])
        return " ".join([str(f) for f in fields if f not in ["", None, "null", "None", False]])

    def format_records(self, domain, records):
        formatted = [self.format_record(domain, r) for r in records]
        if self.raw:
            return formatted
        if self.json:
            if self.by_key:
                return {f["key"]: f for f in formatted}
            elif self.by_id:
                return {f["id"]: f for f in formatted}
            return formatted
        else:
            return "\n".join(formatted)

    def is_selected(self, pattern, text):
        if pattern is None:
            return True
        elif pattern.startswith("/"):
            return bool(re.match(pattern.strip("/"), text))
        else:
            return pattern == text

    def select_records(self, domain, type=None, host=None, content=None, priority=None, weight=None):

        if host and type != "ID" and not host.startswith("/"):
            host = self.parse_host(host, domain)

        records = self.get_zone_records(domain)

        selected = []

        if type == "ID":
            for record in records:
                if host == record["id"]:
                    return [record]
            return []

        for record in records:
            if not self.is_selected(type, record["type"]):
                continue
            if not self.is_selected(host, record["name"]):
                continue
            if not self.is_selected(content, record["content"]):
                continue
            if record["type"] in ["MX", "SRV"]:
                if priority is not None:
                    if int(priority) != int(record["priority"]):
                        continue
            if record["type"] == "SRV":
                if weight is not None:
                    if int(weight) != int(record["weight"]):
                        continue

            selected.append(record)

        return selected

    def format_key(self, domain, record):
        fields = []
        if record["type"] == "TXT":
            protocol = self.format_protocol(domain, record)
            if protocol is not None:
                fields.append(record["type"] + "." + self.format_protocol(domain, record))
            else:
                fields.append(record["type"])
        elif record["type"] in ["MX", "SRV"]:
            fields.append(record["type"] + "." + str(record.get("priority", self.DEFAULT_PRIORITY)))
        else:
            fields.append(record["type"])
        fields.append(self.format_host(domain, record))
        fields.append(domain)
        return ";".join(fields)

    def format_protocol(self, domain, record):
        if record["type"] != "TXT":
            return None
        if "name" in record:
            if record["name"].endswith(f"._domainkey.{domain}"):
                return "DKIM"
        elif "host" in record:
            if record["host"].endswith("._domainkey"):
                return "DKIM"
        content = record["content"]
        patterns = {
            "^v=([a-zA-Z]+).*": None,
            "^(mailconf)=.*": None,
            "^k=rsa;.*": "DKIM",
        }
        for pattern, proto in patterns.items():
            m = re.match(pattern, content)
            if m:
                if proto:
                    return proto.upper()
                if len(m.groups()) > 0:
                    return m.groups()[0].upper()
        return None
