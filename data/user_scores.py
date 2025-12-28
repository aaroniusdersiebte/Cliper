import json
from pathlib import Path
from typing import Dict, Optional
from data.models import UserScore
from config import USER_SCORES_FILE


class UserScoreManager:
    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path or USER_SCORES_FILE
        self._scores: Dict[str, UserScore] = {}
        self.load()

    def load(self):
        """Lädt User-Scores aus JSON-Datei"""
        if not self.file_path.exists():
            self._scores = {}
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._scores = {}
            for username, score_data in data.items():
                self._scores[username] = UserScore(
                    username=username,
                    total_clips=score_data.get("total_clips", 0),
                    ratings={
                        int(k): v for k, v in score_data.get("ratings", {}).items()
                    }
                )
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Fehler beim Laden der User-Scores: {e}")
            self._scores = {}

    def save(self):
        """Speichert User-Scores in JSON-Datei"""
        data = {}
        for username, score in self._scores.items():
            data[username] = {
                "total_clips": score.total_clips,
                "ratings": score.ratings,
            }

        # Ordner erstellen falls nicht vorhanden
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_score(self, username: str) -> UserScore:
        """Gibt UserScore für einen User zurück (erstellt neuen falls nicht vorhanden)"""
        if username not in self._scores:
            self._scores[username] = UserScore(username=username)
        return self._scores[username]

    def add_rating(self, username: str, rating: int):
        """Fügt eine Bewertung für einen User hinzu"""
        score = self.get_score(username)
        score.add_rating(rating)
        self.save()

    def get_average(self, username: str) -> float:
        """Gibt den Durchschnittsscore eines Users zurück"""
        if username not in self._scores:
            return 0.0
        return self._scores[username].average_score

    def get_tier(self, username: str) -> str:
        """Gibt die Qualitätsstufe eines Users zurück"""
        if username not in self._scores:
            return "unknown"
        return self._scores[username].quality_tier

    def get_all_users(self) -> Dict[str, UserScore]:
        """Gibt alle User-Scores zurück"""
        return self._scores.copy()

    def get_users_by_tier(self, tier: str) -> list:
        """Gibt alle User einer bestimmten Qualitätsstufe zurück"""
        return [
            score for score in self._scores.values()
            if score.quality_tier == tier
        ]

    def filter_by_min_score(self, min_score: float) -> list:
        """Gibt alle User mit mindestens diesem Durchschnittsscore zurück"""
        return [
            score for score in self._scores.values()
            if score.average_score >= min_score
        ]
