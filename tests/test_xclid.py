from twscrape.xclid import get_scripts_list


def test_get_scripts_list_with_name_map():
    # New format: g.u=e=>(({name_map}[e]||e)+"."+{hash_map}[e]+"a.js")
    # Numeric keys in hash map, separate name map resolves IDs to chunk names
    text = (
        'stuff... g.u=e=>(({1:"ondemand.s",2:"bundle.Main"}[e]||e)'
        '+"."+{1:"abc1234",2:"def5678"}[e]+"a.js")... stuff'
    )

    scripts = list(get_scripts_list(text))

    assert len(scripts) == 2
    assert "https://abs.twimg.com/responsive-web/client-web/ondemand.s.abc1234a.js" in scripts
    assert "https://abs.twimg.com/responsive-web/client-web/bundle.Main.def5678a.js" in scripts


def test_get_scripts_list_name_map_fallback():
    # When a key exists in hash map but not in name map, the numeric ID is used as-is
    text = (
        'stuff... g.u=e=>(({1:"ondemand.s"}[e]||e)'
        '+"."+{1:"abc1234",2:"def5678"}[e]+"a.js")... stuff'
    )

    scripts = list(get_scripts_list(text))

    assert len(scripts) == 2
    assert "https://abs.twimg.com/responsive-web/client-web/ondemand.s.abc1234a.js" in scripts
    assert "https://abs.twimg.com/responsive-web/client-web/2.def5678a.js" in scripts