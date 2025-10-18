from logger_local.src.writer import Writer


def test_writer():
    writer1 = Writer()
    writer2 = Writer()

    assert writer1 is writer2

    # assert queue.Queue() called once
    assert writer1._queue is writer2._queue
