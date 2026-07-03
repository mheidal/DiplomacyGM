

from enum import Enum
from typing import Optional
import uuid

from DiploGM.models.player import Player

class Vote(Enum):
    IN_FAVOR = "In favor"
    AGAINST = "Against"
    MISSING = "Missing"

class GameEndPoll:
    public: bool
    votes: dict[Vote, set[Player]]
    id: str
    deadline: Optional[int]
    description: Optional[str]

    def __init__(self) -> None:
        self.votes = {
            Vote.IN_FAVOR: set(),
            Vote.AGAINST: set(),
        }
        self.id = uuid.uuid4().hex[:6]
        self.deadline = None
        self.description = None

    def vote(self, player: Player, value: Vote) -> None:
        self.remove_vote(player)
        self.votes[value].add(player)

    def remove_vote(self, player: Player) -> None:
        for s in self.votes.values():
            s.discard(player)

    def set_public(self, value: bool):
        self.public = value

    def set_description(self, desc: Optional[str]):
        self.description = desc

    def get_players_to_vote(self, player_restriction: Optional[Player], full_player_set: Optional[set[Player]] = None) -> dict[Player, Vote]:
        if player_restriction is not None:
            return {
                player_restriction: self.get_vote(player_restriction)
            }
        vote_map = {}
        for vote, players in self.votes.items():
            for player in players:
                vote_map[player] = vote
        if full_player_set is not None:
            for player in full_player_set:
                if player not in vote_map:
                    vote_map[player] = Vote.MISSING
        return vote_map
    
    def get_vote_to_players(self, player_restriction: Optional[Player], full_player_set: Optional[set[Player]] = None) -> dict[Vote, set[Player]]:
        if player_restriction is not None:
            return {
                self.get_vote(player_restriction): {player_restriction}
            }
        output = self.votes.copy()
        output[Vote.MISSING] = set()
        if full_player_set is not None:
            for player in full_player_set:
                if not self.has_voted(player):
                    output[Vote.MISSING].add(player)
        return output


    def has_voted(self, player: Player):
        return any(player in s for s in self.votes.values())

    def get_vote(self, player: Player) -> Vote:
        for vote, players in self.votes.items():
            if player in players:
                return vote
        return Vote.MISSING

    def set_deadline(self, new_deadline: Optional[int]):
        self.deadline = new_deadline

    def parse_vote(self, vote: str):
        IN_FAVOR = [
            "yes",
            "yay",
            "yea",
            "y",
            "in favor",
            "for",
        ]
        AGAINST = [
            "nay",
            "n",
            "against",
        ]
        clean = vote.lower()
        if clean in IN_FAVOR:
            return Vote.IN_FAVOR
        elif clean in AGAINST:
            return Vote.AGAINST
        raise ValueError(
f"""Could not parse vote! Valid responses:
Yea: {', '.join(IN_FAVOR)}
Nay: {', '.join(AGAINST)}
"""

)
    