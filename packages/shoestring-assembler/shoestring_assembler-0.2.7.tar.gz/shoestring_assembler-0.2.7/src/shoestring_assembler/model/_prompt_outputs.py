from shoestring_assembler.implementation.dsl.prompt_criteria import parse_criteria

class Output:
    @classmethod
    def create(cls, key, details):
        if "var" in details:
            return Output.Variable(key, details)
        if "map" in details:
            return Output.Mapping(key, details)

    class Base:
        def __init__(self, key, _details):
            self.key = key
            
        def apply(self, answers):
            raise NotImplementedError()

    class Variable(Base):
        def __init__(self, key, details):
            super().__init__(key, details)
            self.var_name = details["var"]
            
        def apply(self, answers):
            return answers.get(self.var_name)

    class Mapping(Base):
        def __init__(self, key, details):
            super().__init__(key, details)
            self.map = [Output.Mapping.Entry(entry) for entry in details["map"]]
            
        def apply(self, answers):
            for entry in self.map:
                if entry.criteria.matches(answers):
                    return entry.value
            return None

        class Entry:
            def __init__(self, details):
                self.criteria = parse_criteria(details.get("criteria"))
                self.value = details.get("value")
