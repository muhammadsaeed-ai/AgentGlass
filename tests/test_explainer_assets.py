"""Regression checks for the self-contained explainer assets."""

from html.parser import HTMLParser
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.external_assets = []
        self.scene_sections = 0
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "section" and "scene" in attrs.get("class", "").split():
            self.scene_sections += 1
        if tag == "script" and attrs.get("src"):
            self.external_assets.append(attrs["src"])
        if tag == "link" and attrs.get("href", "").startswith(("http://", "https://")):
            self.external_assets.append(attrs["href"])
        if tag in {"img", "video", "audio", "source"}:
            src = attrs.get("src", "")
            if src.startswith(("http://", "https://")):
                self.external_assets.append(src)


class ExplainerAssetTests(unittest.TestCase):
    def test_animation_svg_is_well_formed_and_animated(self):
        path = ROOT / "assets" / "readme" / "agentglass-explainer.svg"
        root = ET.parse(path).getroot()
        self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
        title = root.find("{http://www.w3.org/2000/svg}title")
        self.assertIsNotNone(title)
        animations = root.findall(".//{http://www.w3.org/2000/svg}animate")
        self.assertGreaterEqual(len(animations), 10)
        svg_text = path.read_text(encoding="utf-8")
        self.assertIn("SCENE 7 OF 7", svg_text)
        self.assertIn("PLANNED — NOT YET SHIPPED", svg_text)

    def test_player_has_seven_chapters_and_working_controls(self):
        path = ROOT / "docs" / "agentglass-explainer.html"
        html = path.read_text(encoding="utf-8")
        parser = _PageParser()
        parser.feed(html)
        parser.close()
        self.assertEqual(parser.scene_sections, 7)
        self.assertEqual(parser.external_assets, [])
        for element_id in (
            "playBtn", "restartBtn", "prevBtn", "nextBtn",
            "clock", "progress", "chapters", "stage",
        ):
            self.assertIn(element_id, parser.ids)
        self.assertIn("aria-label=\"Explainer chapters\"", html)
        self.assertIn("Read the full narration", html)
        self.assertIn("const duration=8000,total=duration*scenes.length", html)

    def test_readme_embeds_animation_and_links_player(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("assets/readme/agentglass-explainer.svg", readme)
        self.assertIn("docs/agentglass-explainer.html", readme)
        self.assertIn("not imply that the dashboard or roadmap features are already shipped", readme)
        self.assertIn("python -m http.server 8000", readme)


if __name__ == "__main__":
    unittest.main()
