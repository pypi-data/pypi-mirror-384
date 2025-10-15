from dataclasses import dataclass


@dataclass
class Feature:
    is_binary: bool
    is_relevant: bool
