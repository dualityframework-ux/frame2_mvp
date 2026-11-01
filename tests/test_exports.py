"""Generate the advertised artifacts, rather than only testing their helpers."""
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('script,extension', [
    ('generate_web_timeline.py', '.html'),
    ('generate_mobile_timeline.py', '.html'),
    ('export_era_comparison_pdf.py', '.pdf'),
    ('build_timeline_slideshow.py', '.pptx'),
])
def test_export_produces_valid_artifact(tmp_path, script, extension):
    output = tmp_path / ('export' + extension)
    env = dict(os.environ, MPLBACKEND='Agg', MPLCONFIGDIR=str(tmp_path / 'mpl'))
    result = subprocess.run([sys.executable, str(ROOT / script), str(output)],
                            cwd=ROOT, env=env, text=True, capture_output=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    assert output.stat().st_size > 1000
    if extension == '.pdf':
        assert output.read_bytes().startswith(b'%PDF-')
    elif extension == '.pptx':
        with zipfile.ZipFile(output) as archive:
            assert 'ppt/presentation.xml' in archive.namelist()
    else:
        assert '<html' in output.read_text().lower()


def test_pdf_era_tag_counts_match_the_season_classifier():
    from adapters.redsox_history_loader import load_redsox_history
    from export_era_comparison_pdf import build_era_stats
    from intelligence.redsox_history_engine import classify_process_vs_result
    seasons = load_redsox_history()
    stats, classified = build_era_stats(seasons)
    expected = seasons.apply(lambda row: classify_process_vs_result(row)[0], axis=1).value_counts()
    for field, tag in [('signal','signal'), ('balanced','balanced'),
                       ('overperformed','overperformed process'), ('underperformed','underperformed process')]:
        assert stats[field].sum() == expected.get(tag, 0)
    assert stats[['signal','balanced','overperformed','underperformed']].sum().sum() == len(seasons)
    assert classified.tag.map(type).eq(str).all()


def test_era_titles_are_distinct_from_series_appearances():
    from adapters.redsox_history_loader import load_redsox_history
    from export_era_comparison_pdf import build_era_stats
    stats, _ = build_era_stats(load_redsox_history())
    assert stats.ws_titles.sum() == 4
    assert stats.ws_appearances.sum() == 7
    yaz = stats[stats.era.str.contains('Yaz')].iloc[0]
    assert yaz.ws_titles == 0
    assert yaz.ws_appearances == 2


def test_championship_slide_only_contains_winning_seasons():
    from pptx import Presentation
    from adapters.redsox_history_loader import load_redsox_history
    from build_timeline_slideshow import slide_ws_championships
    presentation = Presentation()
    slide_ws_championships(presentation, load_redsox_history())
    texts = {shape.text for shape in presentation.slides[0].shapes if shape.has_text_frame}
    assert {'2004', '2007', '2013', '2018'} <= texts
    assert not {'1967', '1975', '1986'} & texts
    assert 'Four Championships in This Dataset' in texts
