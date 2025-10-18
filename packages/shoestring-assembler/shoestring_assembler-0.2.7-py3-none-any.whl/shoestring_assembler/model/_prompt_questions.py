from shoestring_assembler.implementation.dsl.prompt_criteria import parse_criteria


class Question:

    @classmethod
    def create(cls, id, key, details):
        match details["type"]:
            case "select":
                return Question.Select(id, key, details)
            case "text":
                return Question.Text(id, key, details)
            case "bool":
                return Question.Bool(id,key,details)

    class Base:
        def __init__(self, id, key, details):
            self.__id = id  # internal id
            self.prefix = ""  # to be set when prompts are started

            self.key = key
            self.criteria = parse_criteria(details.get("criteria"))
            self.prompt = details.get("prompt")

        @property
        def id(self):
            return f"{self.prefix}-{self.__id}"

        def __str__(self):
            return (
                f"{type(self)}(id={self.id}, key={self.key}, criteria={self.criteria})"
            )

        def __repr__(self):
            return self.__str__()

        def apply_prefix(self, prefix):
            self.prefix = prefix

        def is_shown(self, context):
            return self.criteria.matches(context)

    class Text(Base):
        def __init__(self, id, key, details):
            super().__init__(id, key, details)

    class Select(Base):

        def __init__(self, id, key, details):
            super().__init__(id, key, details)
            self.__options = {}
            for key, prompt in details["opt"].items():
                self.__options[key] = prompt

        @property
        def choices(self):
            return self.__options

    class Bool(Base):
        def __init__(self, id, key, details):
            super().__init__(id, key, details)
