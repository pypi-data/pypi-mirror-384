import re
import uuid


class ImportResult:
    def __init__(self):
        self.added = {}
        self.updated = {}
        self.unchanged = {}
        self.surplus = {}
        self.failed = {}
        self.errors = []

    def get_id(self, record):
        id = record.get("id", None)
        if id is None:
            id = uuid.uuid4().hex
        return id

    def set_surplus(self, record):
        id = self.get_id(record)
        self.surplus[id] = record

    def set_added(self, record):
        id = self.get_id(record)
        self.added[id] = record
        self.surplus.pop(id, None)

    def set_updated(self, record):
        id = self.get_id(record)
        self.updated[id] = record
        self.surplus.pop(id, None)

    def set_unchanged(self, record):
        id = self.get_id(record)
        self.unchanged[id] = record
        self.surplus.pop(id, None)

    def set_deleted(self, record):
        id = self.get_id(record)
        self.surplus.pop(id, None)

    def fail(self, record, error):
        id = self.get_id(record)
        self.failed[id] = record
        self.errors.append(dict(record=record, error=repr(error)))

    def dict(self):
        return dict(
            added=self.added,
            updated=self.updated,
            unchanged=self.unchanged,
            surplus=self.surplus,
            failed=self.failed,
            errors=self.errors,
        )


class Importer:
    def __init__(self, api):
        self.api = api
        self.api.raw = False
        self.api.json = True
        self.api.by_id = True
        self.api.include_id = True
        self.api.include_key = True
        self.records_by_id = {}
        self.records_by_key = {}
        self.results = {}

    def import_records(self, records):
        if not isinstance(records, list):
            if self.get_field(records, "type", require=False, allow_none=True) in self.api.IMPORT_TYPES:
                # assume input is a single record
                records = [records]
            else:
                # assume input is a dict keyed bye ID or Key
                records = records.values()

        for record in records:
            zone = self.get_field(record, "zone")
            self.get_zone_records(zone)
            if self.api.debug:
                self.import_record(zone, record)
            else:
                try:
                    self.import_record(zone, record)
                except Exception as e:
                    self.results[zone].fail(record, e)

        return {zone: result.dict() for zone, result in self.results.items()}

    def get_zone_records(self, zone):
        if zone not in self.records_by_id:
            self.records_by_id[zone] = {}
            self.records_by_key[zone] = {}
            records = self.api.get_zone_records(zone)
            formatted = self.api.format_records(zone, records)
            self.results[zone] = ImportResult()
            for id, record in formatted.items():
                key = self.get_field(record, "key")
                self.records_by_id[zone][id] = record
                self.records_by_key[zone][key] = record
                self.results[zone].set_surplus(record)

        return self.records_by_id[zone].values()

    def get_record_by_id(self, zone, id):
        return self.records_by_id[zone].get(id, None)

    def get_record_by_key(self, zone, key):
        return self.records_by_key[zone].get(key, None)

    def get_field(self, record, field, *, require=True, allow_none=False, default=None):
        if field in record:
            value = record.get(field, default)
            if value is None:
                if not allow_none:
                    raise RuntimeError(f"Null '{field}' value in input record")
        else:
            if require:
                raise RuntimeError(f"Missing field '{field}' in input record")
            value = default
        return value

    def import_record(self, zone, record):

        current = None

        if "id" in record:
            id = self.get_field(record, "id")
            current = self.get_record_by_id(zone, id)

        if current is None:
            if "key" in record:
                key = self.get_field(record, "key")
            else:
                key = self.api.format_key(zone, record)
            current = self.get_record_by_key(zone, key)

        if current is None:
            current = self.find_matching_current_record(zone, record)
            if current is not None:
                self.results[zone].set_unchanged(current)
                return

        updating = False
        if current is not None:
            id = self.get_field(current, "id")
            if self.diff(record, current):
                updating = True
                self.delete_record(zone, id)
                self.results[zone].set_deleted(current)
            else:
                self.results[zone].set_unchanged(current)
                return

        added = self.add_record(zone, record)
        if updating:
            self.results[zone].set_updated(added)
        else:
            self.results[zone].set_added(added)
        return

    def delete_record(self, zone, id):
        record = dict(id=id)
        return self.api.delete_record(zone, record)

    def find_matching_current_record(self, zone, record):
        """find matching current record in zone records"""
        current_records = self.get_zone_records(zone)
        for current in current_records:
            if self.get_field(current, "type") in self.api.IMPORT_TYPES:
                if not self.diff(record, current):
                    return current
        return None

    def diff(self, record, current):
        """check record content for difference"""
        type = self.get_field(record, "type")
        if type not in self.api.IMPORT_TYPES:
            raise RuntimeError(f"cannot import type '{type}'")
        if type != self.get_field(current, "type"):
            return True
        if self.get_field(record, "zone") != self.get_field(current, "zone"):
            raise RuntimeError("zone mismatch")
        if self.get_field(record, "host") != self.get_field(current, "host"):
            return True

        record_content = self.get_field(record, "content")
        if type == "SRV":
            weight = self.get_field(record, "weight", require=False, default=self.api.DEFAULT_WEIGHT)
            if str(weight) != str(self.get_field(current, "weight")):
                return True
            port = self.get_field(record, "port")
            if str(port) != str(self.get_field(current, "port")):
                return True
            record_content = f"{weight} {port} {record_content}"

        if record_content != self.get_field(current, "content"):
            return True
        if self.get_field(record, "ttl", require=False, default=self.api.DEFAULT_TTL) != self.get_field(current, "ttl"):
            return True
        if type in self.api.PRIORITY_TYPES:
            if self.get_field(record, "priority", require=False, default=self.api.DEFAULT_PRIORITY) != self.get_field(
                current, "priority"
            ):
                return True
        return False

    def add_record(self, zone, record):
        type = self.get_field(record, "type")
        if type not in self.api.IMPORT_TYPES:
            raise ValueError(f"Unsupported record type '{type}'")
        host = self.get_field(record, "host")
        content = self.get_field(record, "content")
        ttl = self.get_field(record, "ttl", require=False, default=self.api.DEFAULT_TTL)
        priority = None
        weight = None
        port = None
        if type in self.api.PRIORITY_TYPES:
            priority = self.get_field(record, "priority", require=False, default=self.api.DEFAULT_PRIORITY)
        if type == "SRV":
            matched = re.match(r"^(\d+) (\d+) (.*)$", content)
            if matched:
                weight, port, content = matched.groups()
                if "weight" in record and int(weight) != int(self.get_field(record, "weight")):
                    raise ValueError("content weight != record field")
                if "port" in record and int(port) != int(self.get_field(record, "port")):
                    raise ValueError("content port != record field")
            else:
                weight = self.get_field(record, "weight")
                port = self.get_field(record, "port")
            if port is None:
                raise ValueError("port is required for SRV record")
        added = self.api.add_record(zone, type, host, content, ttl, priority, weight, port)
        return self.api.format_record(zone, added)
