import json


class Episode(dict):
    def __init__(self, id, title, summary, transcript, sample_questions):
        dict.__init__(
            self,
            id=id,
            title=title,
            summary=summary,
            transcript=transcript,
            sample_questions=sample_questions,
        )
        self.id = id
        self.title = title
        self.summary = summary
        self.transcript = transcript
        self.sample_questions = sample_questions

    def to_json(self):
        return json.dumps(self.__dict__)

    def __str__(self):
        return self.to_json()
