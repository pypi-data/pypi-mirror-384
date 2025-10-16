from techlens_agent.dependencies.walkers.classes import Walker, Entry
from typing import Union
import re


class DockerWalker(Walker):
    def clean_str(self, s: Union[str, bytes]) -> str:
        bad_chars = ["\n", "\r", "\t"]
        s = str(s)
        # remove inline comments
        s = s.split("#", 1)[0]
        # remove leading/trailing whitespace
        s = s.strip()
        # collapse multiple spaces
        s = re.sub(r"\s+", " ", s)
        # remove bad chars
        for char in bad_chars:
            s = s.replace(char, "")
        return s

    def parse_address(
        self, address: str, file: str, source: str = "Dockerfile"
    ) -> Entry:
        address = re.sub(r"\$\{[^:}]+:-([^}]+)\}", r"\1", address)

        name = address
        specifier = "*"

        if "@" in address:
            name, specifier = address.split("@", 1)
        else:
            last_slash = address.rfind("/")
            if last_slash != -1:
                last_part = address[last_slash + 1 :]
                if ":" in last_part:
                    name = address.rsplit(":", 1)[0]
                    specifier = address.rsplit(":", 1)[1]
            elif ":" in address:
                name, specifier = address.rsplit(":", 1)
        if not specifier:
            specifier = "*"

        e = Entry(
            name=name or "UNKNOWN",
            specifier=specifier,
            source=source,
            required_by=file,
        )
        return e

    def parse(self, file: str, expand=False):
        with open(file, "r") as f:
            lines = f.readlines()
            for line in lines:
                line = self.clean_str(line)
                if line.lower().startswith("from "):
                    name = line.split(" ")[1].strip().strip('"').strip("'")
                    e = self.parse_address(name, file)
                    self.entries.append(e)
                elif line.lower().startswith("image:"):
                    name = line[6:].split("#", 1)[0].strip().strip('"').strip("'")
                    e = self.parse_address(name, file, source="docker-compose")
                    self.entries.append(e)

    def expand(self, file):
        raise Exception("No expansion for this Walker")
