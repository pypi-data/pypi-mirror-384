class KvPair:
    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
        self.subject = None
        self.old_predicate = None

    def setKey(self, key):
        self.key = key

    def setValue(self, value):
        self.value = value

    def setSubject(self, subject):
        self.subject = subject

    def setOldPredicate(self, old_predicate):
        self.old_predicate = old_predicate

    def getSubject(self):
        return self.subject

    def getDataProperty(self):
        return self.old_predicate

    def getTriple(self):
        return f"{self.subject} <{self.key}> \"{self.value}\" .\n"

    def toCSVEntry(self, key):
        return f"{self.subject},{self.key},{self.value}"

    def toCsvEntryExtraProperties(self, key, extra_props):
        base = self.toCSVEntry(key)
        extras = ",".join(f"{k},{v}" for k, v in extra_props)
        return f"{base},{extras}"
