import uuid
from dataclasses import dataclass, asdict


@dataclass
class ReportBlock:
    id: str
    type: str
    data: dict[str, any]

    @staticmethod
    def content(content_type, content_name, content):
        return ReportBlock(
            id=ReportBlock.generate_random_id(),
            type=content_type,
            data={
                content_name: content
            }
        )

    @staticmethod
    def header(level, content):

        if level == 1:
            header_type = 'headerOne'
        elif level == 2:
            header_type = 'headerTwo'
        elif level == 3:
            header_type = 'headerThree'
        else:
            raise Exception(f'Unsupported header level: {level}')

        return ReportBlock(
            id=ReportBlock.generate_random_id(),
            type=header_type,
            data={'level': level, 'text': content or ''}
        )

    @staticmethod
    def generate_random_id():
        return str(uuid.uuid4())
