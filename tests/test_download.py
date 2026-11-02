import csv
import tempfile
import unittest
from pathlib import Path

from agent_reranking.download import convert_ml1m


class DownloadTests(unittest.TestCase):
    def test_convert_ml1m(self):
        with tempfile.TemporaryDirectory() as temporary:
            tmp_path = Path(temporary)
            raw = tmp_path / "raw"
            raw.mkdir()
            (raw / "ratings.dat").write_text("1::2::5::10\n", encoding="latin-1")
            (raw / "movies.dat").write_text(
                "2::Movie, The (1999)::Drama|Comedy\n", encoding="latin-1")
            (raw / "users.dat").write_text("1::F::25::4::00000\n", encoding="latin-1")
            out = Path(convert_ml1m(raw, tmp_path / "data"))
            self.assertTrue((out / "ml-1m.inter").is_file())
            with (out / "ml-1m.item").open(newline="", encoding="utf-8") as source:
                row = next(csv.DictReader(source, delimiter="\t"))
            self.assertEqual(row["movie_title:token_seq"], "Movie, The")
            self.assertEqual(row["release_year:token"], "1999")
            self.assertEqual(row["genre:token_seq"], "Drama Comedy")
