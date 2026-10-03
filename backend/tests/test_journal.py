from dashboard import journal


def test_fin_et_rotation(tmp_path):
    f = journal.tourner(tmp_path, "a")
    f.write_bytes(b"un\r\ndeux\nprogression 10%\rprogression 100%\ntrois\n")
    assert journal.fin(f, 2) == ["progression 100%", "trois"]
    assert journal.fin(f, 10) == ["un", "deux", "progression 100%", "trois"]
    assert journal.fin(f, 0) == []
    journal.tourner(tmp_path, "a")
    assert (tmp_path / "a.log.1").exists() and not (tmp_path / "a.log").exists()
    assert journal.fin(tmp_path / "absent.log") == []
