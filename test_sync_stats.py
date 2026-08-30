import sys
from unittest.mock import MagicMock

# Mock dependencies
sys.modules['requests'] = MagicMock()
sys.modules['requests.adapters'] = MagicMock()
sys.modules['urllib3'] = MagicMock()
sys.modules['urllib3.util'] = MagicMock()
sys.modules['urllib3.util.retry'] = MagicMock()

import sync_stats

def test_generate_contribution_svg():
    calendar_data = {
        'weeks': [
            {
                'contributionDays': [
                    {
                        'color': '#ebedf0',
                        'contributionCount': 0,
                        'date': '2023-01-01'
                    }
                ]
            }
        ]
    }

    svg_str = sync_stats.generate_contribution_svg(calendar_data)

    # Basic assertions to ensure the new optimized function still produces the correct SVG shapes
    assert '<svg' in svg_str
    assert '</svg>' in svg_str
    assert '<rect' in svg_str
    assert 'width="10"' in svg_str
    assert 'rx="2"' in svg_str
    assert 'x="0"' in svg_str
    assert 'y="20"' in svg_str # y should be TOP_PAD
    assert '<title>0 contributions on 2023-01-01</title>' in svg_str

def test_generate_contribution_svg_advanced():
    calendar_data = {
        'weeks': [
            {
                'contributionDays': [
                    {
                        'color': '#ebedf0',
                        'contributionCount': 0,
                        'date': '2023-01-01'
                    },
                    {
                        'color': '#ebedf0',
                        'contributionCount': 5,
                        'date': '2023-01-02'
                    }
                ]
            },
            {
                'contributionDays': [
                    {
                        'color': '#ebedf0',
                        'contributionCount': 0,
                        'date': '2023-01-08'
                    }
                ]
            }
        ]
    }

    svg_str = sync_stats.generate_contribution_svg(calendar_data)

    # 2nd week, 1st day (x = 12, y = 20)
    assert 'x="12"' in svg_str

    # 1st week, 2nd day (x = 0, y = 32)
    assert 'y="32"' in svg_str

    assert '<title>5 contributions on 2023-01-02</title>' in svg_str


if __name__ == "__main__":
    test_generate_contribution_svg()
    test_generate_contribution_svg_advanced()
    print("Tests passed!")
