import jinja2
import yaml

ENV = jinja2.Environment(
    loader=jinja2.PackageLoader("datapipeline", "templates/stubs"),
    keep_trailing_newline=True,
)


def camel(s: str) -> str:
    return "".join(w.capitalize() for w in s.split("_"))


ENV.filters["camel"] = camel


def to_yaml(value, indent: int = 0) -> str:
    text = yaml.safe_dump(value, sort_keys=False).rstrip()
    if indent > 0:
        pad = " " * indent
        return "\n".join(pad + line for line in text.splitlines())
    return text

ENV.filters["to_yaml"] = to_yaml


def render(template: str, **ctx) -> str:
    return ENV.get_template(template).render(**ctx)
