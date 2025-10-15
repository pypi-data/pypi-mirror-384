from imecilabt.gpulab.schemas.active_jobs_counts import ActiveJobsCounts


class TestActiveJobsCounts:
    def test_initialization(self) -> None:
        obj = ActiveJobsCounts(onhold=1, queued=2, assigned=3, starting=4, running=5, musthalt=6, halting=7)
        assert obj.onhold == 1
        assert obj.queued == 2
        assert obj.assigned == 3
        assert obj.starting == 4
        assert obj.running == 5
        assert obj.musthalt == 6
        assert obj.halting == 7

    def test_zero_method(self) -> None:
        obj = ActiveJobsCounts.zero()
        assert obj.onhold == 0
        assert obj.queued == 0
        assert obj.assigned == 0
        assert obj.starting == 0
        assert obj.running == 0
        assert obj.musthalt == 0
        assert obj.halting == 0
