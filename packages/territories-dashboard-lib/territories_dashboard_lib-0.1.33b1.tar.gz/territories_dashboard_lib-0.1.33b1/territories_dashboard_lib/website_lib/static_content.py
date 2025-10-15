import re

from martor.utils import markdownify


def put_daily_motion_iframe(html_text):
    pattern = re.compile(
        r"<a href=\"(https://geo\.dailymotion\.com/player/x14squ\.html\?video=[a-z0-9]+)\">https://geo\.dailymotion\.com/player/x14squ\.html\?video=[a-z0-9]+</a>",
        re.MULTILINE,
    )

    def replacer(match):
        full_url = match.group(1)
        return f'<iframe src="{full_url}" height="270" width="480"></iframe>'

    return pattern.sub(replacer, html_text)


def markdown_content_to_html(content):
    return put_daily_motion_iframe(markdownify(content))
