class SimplePluralizer:
    def pluralize(self, name: str) -> str:
        return name + "s" if not name.endswith("s") else name + "es"