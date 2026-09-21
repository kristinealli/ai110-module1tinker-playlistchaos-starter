import unittest

from playlist_logic import (
    DEFAULT_PROFILE,
    build_playlists,
    classify_song,
    compute_playlist_stats,
    history_summary,
    lucky_pick,
    merge_playlists,
    most_common_artist,
    normalize_song,
    random_choice_or_none,
    search_songs,
)


class PlaylistLogicTests(unittest.TestCase):
    """Regression and behavior checks for the playlist logic helpers."""

    def test_normalize_song_converts_and_defaults_values(self):
        """Normalization trims text, lowercases comparisons, and parses energy."""
        song = normalize_song(
            {
                "title": "  Back in Black  ",
                "artist": " AC/DC ",
                "genre": " ROCK ",
                "energy": "8",
                "tags": "classic",
            }
        )

        self.assertEqual(song["title"], "Back in Black")
        self.assertEqual(song["artist"], "ac/dc")
        self.assertEqual(song["genre"], "rock")
        self.assertEqual(song["energy"], 8)
        self.assertEqual(song["tags"], ["classic"])

    def test_normalize_song_uses_zero_for_invalid_energy(self):
        """Invalid energy input falls back to zero instead of raising an error."""
        self.assertEqual(normalize_song({"energy": "unknown"})["energy"], 0)

    def test_classify_song_returns_chill_for_low_energy(self):
        """Songs at or below the Chill energy threshold are classified as Chill."""
        song = {"energy": 2, "genre": "ambient", "title": "Calm"}
        self.assertEqual(classify_song(song, DEFAULT_PROFILE), "Chill")

    def test_chill_takes_priority_over_favorite_genre(self):
        """A low-energy favorite-genre song remains Chill when rules overlap."""
        profile = {**DEFAULT_PROFILE, "favorite_genre": "ambient"}
        song = {"energy": 2, "genre": "ambient", "title": "Calm"}
        self.assertEqual(classify_song(song, profile), "Chill")

    def test_classify_song_matches_chill_title_case_insensitively(self):
        """Chill keywords in titles match regardless of capitalization."""
        song = {"energy": 5, "genre": "pop", "title": "Lofi Rain"}
        self.assertEqual(classify_song(song, DEFAULT_PROFILE), "Chill")

    def test_classify_song_returns_hype_for_hype_conditions(self):
        """High energy and favorite genre are independent Hype conditions."""
        self.assertEqual(
            classify_song(
                {"energy": 8, "genre": "pop", "title": "Loud"},
                DEFAULT_PROFILE,
            ),
            "Hype",
        )
        self.assertEqual(
            classify_song(
                {"energy": 5, "genre": "rock", "title": "Guitar"},
                DEFAULT_PROFILE,
            ),
            "Hype",
        )

    def test_classify_song_returns_mixed_when_no_rule_matches(self):
        """Songs matching neither mood rule fall into Mixed."""
        song = {"energy": 5, "genre": "jazz", "title": "Blue"}
        self.assertEqual(classify_song(song, DEFAULT_PROFILE), "Mixed")

    def test_build_playlists_assigns_moods_and_normalizes_songs(self):
        """Playlist building assigns each song once and preserves its mood label."""
        playlists = build_playlists(
            [
                {"title": "Loud", "artist": "Band", "genre": "rock", "energy": 8},
                {"title": "Calm", "artist": "Artist",
                    "genre": "ambient", "energy": 2},
                {"title": "Blue", "artist": "Jazzman",
                    "genre": "jazz", "energy": 5},
            ],
            DEFAULT_PROFILE,
        )

        self.assertEqual(len(playlists["Hype"]), 1)
        self.assertEqual(len(playlists["Chill"]), 1)
        self.assertEqual(len(playlists["Mixed"]), 1)
        self.assertEqual(playlists["Hype"][0]["mood"], "Hype")

    def test_compute_playlist_stats_uses_all_songs(self):
        """Stats use every playlist for totals, averages, and the Hype ratio."""
        playlists = {
            "Hype": [{"artist": "AC/DC", "energy": 8}],
            "Chill": [{"artist": "Queen", "energy": 2}],
            "Mixed": [{"artist": "Queen", "energy": 5}],
        }

        stats = compute_playlist_stats(playlists)

        self.assertEqual(stats["total_songs"], 3)
        self.assertEqual(stats["avg_energy"], 5.0)
        self.assertAlmostEqual(stats["hype_ratio"], 1 / 3)

    def test_compute_playlist_stats_handles_empty_playlists(self):
        """Empty playlists return safe zero values without division errors."""
        stats = compute_playlist_stats({"Hype": [], "Chill": [], "Mixed": []})

        self.assertEqual(stats["total_songs"], 0)
        self.assertEqual(stats["avg_energy"], 0.0)
        self.assertEqual(stats["hype_ratio"], 0.0)

    def test_most_common_artist_ignores_missing_artists(self):
        self.assertEqual(
            most_common_artist(
                [
                    {"artist": "Queen"},
                    {"artist": "Queen"},
                    {"title": "Unknown"},
                ]
            ),
            ("Queen", 2),
        )

    def test_search_songs_matches_partial_text_case_insensitively(self):
        """Search matches partial text in the selected field without case sensitivity."""
        songs = [
            {"artist": "AC/DC", "title": "Back in Black"},
            {"artist": "Queen", "title": "Radio Ga Ga"},
        ]

        self.assertEqual(search_songs(songs, "ac", "artist"), [songs[0]])
        self.assertEqual(search_songs(songs, "RADIO", "title"), [songs[1]])

    def test_search_songs_returns_all_songs_for_empty_query(self):
        """An empty query leaves the input song collection unchanged."""
        songs = [{"artist": "AC/DC"}, {"artist": "Queen"}]
        self.assertEqual(search_songs(songs, "", "artist"), songs)

    def test_random_choice_or_none_handles_empty_list(self):
        """Random selection returns None when there is no candidate song."""
        self.assertIsNone(random_choice_or_none([]))

    def test_lucky_pick_respects_mode(self):
        """Lucky picks use the requested mood, or either supported mood for any mode."""
        hype_song = {"title": "Hype"}
        chill_song = {"title": "Chill"}
        playlists = {"Hype": [hype_song], "Chill": [chill_song]}

        self.assertIs(lucky_pick(playlists, "hype"), hype_song)
        self.assertIs(lucky_pick(playlists, "chill"), chill_song)
        self.assertIn(lucky_pick(playlists), [hype_song, chill_song])

    def test_merge_playlists_combines_playlist_entries(self):
        merged = merge_playlists(
            {"Hype": [{"title": "One"}]},
            {"Chill": [{"title": "Two"}]},
        )

        self.assertEqual(merged["Hype"], [{"title": "One"}])
        self.assertEqual(merged["Chill"], [{"title": "Two"}])

    def test_history_summary_counts_known_and_unknown_moods(self):
        """Unknown history moods are grouped into the Mixed count."""
        history = [
            {"mood": "Hype"},
            {"mood": "Chill"},
            {"mood": "Unrecognized"},
        ]

        self.assertEqual(
            history_summary(history),
            {"Hype": 1, "Chill": 1, "Mixed": 1},
        )


if __name__ == "__main__":
    unittest.main()
