import uuid
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from typing import Optional

import rapidfuzz

from GameSentenceMiner.util.gsm_utils import remove_html_and_cloze_tags
from GameSentenceMiner.util.configuration import logger, get_config, gsm_state
from GameSentenceMiner.util.model import AnkiCard
import re

initial_time = datetime.now()


@dataclass
class GameLine:
    id: str
    text: str
    time: datetime
    prev: 'GameLine | None'
    next: 'GameLine | None'
    index: int = 0
    scene: str = ""
    TL: str = ""

    def get_previous_time(self):
        if self.prev:
            return self.prev.time
        return initial_time

    def get_next_time(self):
        if self.next:
            return self.next.time
        return 0

    def set_TL(self, tl: str):
        self.TL = tl

    def get_stripped_text(self):
        return self.text.replace('\n', '').strip()

    def __str__(self):
        return str({"text": self.text, "time": self.time})


@dataclass
class GameText:
    values: list[GameLine]
    values_dict: dict[str, GameLine]
    game_line_index = 0

    def __init__(self):
        self.values = []
        self.values_dict = {}

    def __getitem__(self, index):
        return self.values[index]

    def get_by_id(self, line_id: str) -> Optional[GameLine]:
        if not self.values_dict:
            return None
        return self.values_dict.get(line_id)

    def get_time(self, line_text: str, occurrence: int = -1) -> datetime:
        matches = [line for line in self.values if line.text == line_text]
        if matches:
            return matches[occurrence].time  # Default to latest
        return initial_time

    def get_event(self, line_text: str, occurrence: int = -1) -> GameLine | None:
        matches = [line for line in self.values if line.text == line_text]
        if matches:
            return matches[occurrence]
        return None

    def add_line(self, line_text, line_time=None):
        if not line_text:
            return
        line_id = str(uuid.uuid1())
        new_line = GameLine(
            id=line_id,  # Time-based UUID as an integer
            text=line_text,
            time=line_time or datetime.now(),
            prev=self.values[-1] if self.values else None,
            next=None,
            index=self.game_line_index,
            scene=gsm_state.current_game or ""
        )
        self.values_dict[line_id] = new_line
        self.game_line_index += 1
        if self.values:
            self.values[-1].next = new_line
        self.values.append(new_line)
        return new_line
        # self.remove_old_events(datetime.now() - timedelta(minutes=10))

    def has_line(self, line_text) -> bool:
        for game_line in self.values:
            if game_line.text == line_text:
                return True
        return False

    def get_last_line(self):
        if self.values:
            return self.values[-1]
        return None


game_log = GameText()

def strip_whitespace_and_punctuation(text: str) -> str:
    """
    Strips whitespace and punctuation from the given text.
    """
    # Remove all whitespace and specified punctuation using regex
    # Includes Japanese and common punctuation
    return re.sub(r'[\s　、。「」【】《》., ]', '', text).strip()


# TODO See if partial_ratio is better than ratio
def lines_match(texthooker_sentence, anki_sentence, similarity_threshold=80) -> bool:
    # Replace newlines, spaces, other whitespace characters, AND japanese punctuation
    texthooker_sentence = strip_whitespace_and_punctuation(texthooker_sentence)
    anki_sentence = strip_whitespace_and_punctuation(anki_sentence)
    similarity = rapidfuzz.fuzz.ratio(texthooker_sentence, anki_sentence)
    # logger.debug(f"Comparing sentences: '{texthooker_sentence}' and '{anki_sentence}' - Similarity: {similarity}")
    # if texthooker_sentence in anki_sentence:
    #     logger.debug(f"One contains the other: {texthooker_sentence} in {anki_sentence} - Similarity: {similarity}")
    # elif anki_sentence in texthooker_sentence:
    #     logger.debug(f"One contains the other: {anki_sentence} in {texthooker_sentence} - Similarity: {similarity}")
    return (anki_sentence in texthooker_sentence) or (texthooker_sentence in anki_sentence) or (similarity >= similarity_threshold)


def get_text_event(last_note) -> GameLine:
    lines = game_log.values

    if not lines:
        raise Exception("No voicelines in GSM. GSM can only do work on text that has been sent to it since it started. If you are not getting any text into GSM, please check your setup/config.")

    if not last_note:
        return lines[-1]

    sentence = last_note.get_field(get_config().anki.sentence_field)
    if not sentence:
        return lines[-1]

    # Check the last 50 lines for a match
    for line in reversed(lines[-50:]):
        if lines_match(line.text, remove_html_and_cloze_tags(sentence)):
            return line

    logger.info("Could not find matching sentence from GSM's history. Using the latest line.")
    return lines[-1]


def get_line_and_future_lines(last_note):
    if not last_note:
        return []

    sentence = last_note.get_field(get_config().anki.sentence_field)
    found_lines = []
    if sentence:
        found = False
        for line in game_log.values:
            if found:
                found_lines.append(line)
            if lines_match(line.text, remove_html_and_cloze_tags(sentence)):  # 80% similarity threshold
                found = True
                found_lines.append(line)
    return found_lines


def get_mined_line(last_note: AnkiCard, lines=None):
    if lines is None:
        lines = []
    if not last_note:
        return lines[-1]
    if not lines:
        lines = get_all_lines()
    if not lines:
        raise Exception("No voicelines in GSM. GSM can only do work on text that has been sent to it since it started. If you are not getting any text into GSM, please check your setup/config.")

    sentence = last_note.get_field(get_config().anki.sentence_field)
    for line in reversed(lines[-50:]):
        if lines_match(line.get_stripped_text(), remove_html_and_cloze_tags(sentence)):
            return line
    return lines[-1]


def get_time_of_line(line):
    return game_log.get_time(line)


def get_all_lines():
    return game_log.values


def get_text_log() -> GameText:
    return game_log

def add_line(current_line_after_regex, line_time):
    return game_log.add_line(current_line_after_regex, line_time)

def get_line_by_id(line_id: str) -> Optional[GameLine]:
    """
    Retrieve a GameLine by its unique ID.

    Args:
        line_id (str): The unique identifier of the GameLine.

    Returns:
        Optional[GameLine]: The GameLine object if found, otherwise None.
    """
    return game_log.get_by_id(line_id)
