import re
from .base import MarkerBase, MarkerNoTranslator, MarkerWithEnd


class MarkerCommentBase(MarkerNoTranslator):
    pass


class CommentMarker(MarkerCommentBase):
    tag_head = "#"


class CommentMultiLineMarker(MarkerCommentBase, MarkerWithEnd):
    tag_head = "comments"

    def execute(self, context, command, marker_node, marker_set):
        return []


class CommentShebangMarker(MarkerCommentBase):
    tag_head = "#!"


class CommentConfigMarker(MarkerCommentBase):
    tag_head = "# config #"

    @classmethod
    def get_config_string(cls, content):
        match = re.search(f'(\n|^){cls.tag_head}', content)
        if match:
            begin = match.span()[-1]
            end = content.find('\n', begin)
            if end == -1:
                end = None
            return content[begin:end].strip()


class TextContentMarker(MarkerCommentBase):
    tag_head = "/"

    def text_content(self, command):
        return command[len(self.tag_head):]


class IgnoreMarker(MarkerBase):
    tag_head = ':'
