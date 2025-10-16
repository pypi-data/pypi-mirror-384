
from string import Template
from os import rename


def process_template(path, **kwargs):
    with open(path, "rb") as f:
        raw = f.read().decode("utf8")

    content = Template(raw).substitute(**kwargs)

    new_path = path[:-len('.tmpl')] if path.endswith(".tmpl") else path

    if path.endswith(".tmpl"):
        rename(path, new_path)

    with open(new_path, "wb") as f:
        f.write(content.encode("utf8"))
