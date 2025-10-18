try:
    import tomllib as toml
except ImportError:
    import tomli as toml

from ._prompt_questions import Question
from ._prompt_outputs import Output


class Prompts:
    def __init__(self):

        self.__queue = []
        self.__questions: dict[str, Question.Base] = {}
        self.__outputs: dict[str, Output.Base] = {}
        self.__has_prompts = False
        self.id_prefix = ""
        self.asked = set()

    def __str__(self):
        return f"Prompts({self.__queue})"

    def start(self, prefix, context={}):
        # reset question queue
        self.__queue = [
            question for question in self.__questions.values() if question.is_shown(context)
        ]
        self.id_prefix = prefix

    def next(self, context=None) -> Question.Base | None:
        if context is not None:
            to_ask = {
                prompt for prompt in self.__questions.values() if prompt.is_shown(context)
            }
            in_queue = set(self.__queue)
            new_prompts = to_ask - in_queue - self.asked
            self.__queue = [*new_prompts, *self.__queue]

        # returns next prompt or None
        try:
            next = self.__queue.pop(0)
            next.apply_prefix(self.id_prefix)
            self.asked.add(next)
            return next
        except IndexError:
            return None

    def exists(self):
        return self.__has_prompts

    def get(self, prefixed_id) -> Question.Base | None:
        id = prefixed_id.removeprefix(f"{self.id_prefix}-")
        return self.__questions.get(id)

    @classmethod
    def load(cls, file_path):
        """Load prompts from the prompts file (TOML)."""
        try:
            with file_path.open("rb") as f:
                spec = toml.load(f)
                inst = cls()
                inst.create(spec)
                return inst
        except FileNotFoundError:
            return cls()

    def create(self, prompt_spec):
        if prompt_spec is None:
            return  # no prompts
        counter = 1

        # parse questions
        questions = prompt_spec["Q"]
        for question_key, question_details in questions.items():
            id = f"{counter}"
            self.__questions[id] = Question.create(id, question_key, question_details)
            counter += 1

        self.__has_prompts = len(self.__questions) > 0

        # parse output specs
        output_map = prompt_spec["OUT"]
        self.__outputs = {}
        for output_key, output_details in output_map.items():
            self.__outputs[output_key] = Output.create(output_key, output_details)

    def generate_outputs(self, context):
        results = {}
        for key, output in self.__outputs.items():
            value = output.apply(context)
            if value:
                results[key] = value
        return results
