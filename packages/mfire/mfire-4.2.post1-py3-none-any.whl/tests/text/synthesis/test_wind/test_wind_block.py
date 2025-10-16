import pytest

from mfire.text.synthesis.wind_reducers.exceptions import WindSynthesisError
from mfire.text.synthesis.wind_reducers.wind.case3.wind_block import WindBlock
from mfire.text.synthesis.wind_reducers.wind.case3.wind_direction import (
    Pcd,
    WindDirection,
)
from mfire.text.synthesis.wind_reducers.wind.wind_intensity import Pci
from mfire.utils.date import Datetime, Timedelta
from tests.text.synthesis.test_wind.factories import WindIntensityFactory


class TestWindBlock:
    BEGIN_TIME: Datetime = Datetime(2023, 1, 1, 0, 0, 0)
    END_TIME: Datetime = Datetime(2023, 1, 1, 9, 0, 0)
    WIND_BLOCK: WindBlock = WindBlock(begin_time=BEGIN_TIME, end_time=END_TIME)

    def test_creation(self):
        assert self.WIND_BLOCK.begin_time == self.BEGIN_TIME
        assert self.WIND_BLOCK.end_time == self.END_TIME
        assert self.WIND_BLOCK.duration == Timedelta(self.END_TIME - self.BEGIN_TIME)

    def test_pcd(self):
        pcd = Pcd(
            begin_time=Datetime(2023, 1, 1, 2, 0, 0),
            end_time=Datetime(2023, 1, 1, 4, 0, 0),
            wd=WindDirection(10.0, 40.0),
        )
        pcd_list = [pcd]
        self.WIND_BLOCK.set_pcd(pcd_list)
        assert self.WIND_BLOCK.pcd == pcd_list

        self.WIND_BLOCK.set_pcd([])
        assert self.WIND_BLOCK.pcd == []

    @pytest.mark.parametrize(
        "pcd_list, exception",
        [
            (
                # 1 Pci: bad type
                [
                    Pci(
                        begin_time=Datetime(2023, 1, 1, 7, 0, 0),
                        end_time=Datetime(2023, 1, 1, 9, 0, 0),
                        wi=WindIntensityFactory(35.0),
                    )
                ],
                TypeError,
            ),
            (
                # 1 Pcd with a begin_time < block begin_time
                [
                    Pcd(
                        begin_time=Datetime(2022, 12, 31, 22, 0, 0),
                        end_time=Datetime(2023, 1, 1, 8, 0, 0),
                        wd=WindDirection(10.0, 40.0),
                    )
                ],
                WindSynthesisError,
            ),
            (
                # 1 Pcd with an end_time > block begin_time
                [
                    Pcd(
                        begin_time=Datetime(2023, 1, 1, 0, 0, 0),
                        end_time=Datetime(2023, 1, 1, 10, 59, 59),
                        wd=WindDirection(10.0, 40.0),
                    )
                ],
                WindSynthesisError,
            ),
            (
                # 1 Pcd with an end_time > block end_time
                [
                    Pcd(
                        begin_time=Datetime(2023, 1, 1, 7, 0, 0),
                        end_time=Datetime(2023, 1, 1, 23, 0, 0),
                        wd=WindDirection(10.0, 40.0),
                    )
                ],
                WindSynthesisError,
            ),
            (
                # 2 unordered Pcd
                [
                    Pcd(
                        begin_time=Datetime(2023, 1, 1, 7, 0, 0),
                        end_time=Datetime(2023, 1, 1, 9, 0, 0),
                        wd=WindDirection(10.0, 40.0),
                    ),
                    Pcd(
                        begin_time=Datetime(2023, 1, 1, 2, 0, 0),
                        end_time=Datetime(2023, 1, 1, 5, 0, 0),
                        wd=WindDirection(10.0, 40.0),
                    ),
                ],
                WindSynthesisError,
            ),
        ],
    )
    def test_pcd_exceptions(self, pcd_list, exception):
        with pytest.raises(exception):
            self.WIND_BLOCK.set_pcd(pcd_list)

    def test_pci(self):
        pci = Pci(
            begin_time=Datetime(2023, 1, 1, 2, 0, 0),
            end_time=Datetime(2023, 1, 1, 4, 0, 0),
            wi=WindIntensityFactory(35.0),
        )
        pci_list = [pci]
        self.WIND_BLOCK.set_pci(pci_list)
        assert self.WIND_BLOCK.pci == pci_list

        self.WIND_BLOCK.set_pci([])
        assert self.WIND_BLOCK.pci == []

    @pytest.mark.parametrize(
        "pci_list, exception",
        [
            (
                # 1 Pcd: bad type
                [
                    Pcd(
                        begin_time=Datetime(2023, 1, 1, 7, 0, 0),
                        end_time=Datetime(2023, 1, 1, 9, 0, 0),
                        wd=WindDirection(10.0, 40.0),
                    )
                ],
                TypeError,
            ),
            (
                # 1 Pci with a begin_time < block begin_time
                [
                    Pci(
                        begin_time=Datetime(2022, 12, 31, 22, 0, 0),
                        end_time=Datetime(2023, 1, 1, 8, 0, 0),
                        wi=WindIntensityFactory(35.0),
                    )
                ],
                WindSynthesisError,
            ),
            (
                # 1 Pci with an end_time > block end_time
                [
                    Pci(
                        begin_time=Datetime(2023, 1, 1, 7, 0, 0),
                        end_time=Datetime(2023, 1, 1, 23, 0, 0),
                        wi=WindIntensityFactory(35.0),
                    )
                ],
                WindSynthesisError,
            ),
            (
                # 1 Pci with an end_time > block begin_time
                [
                    Pci(
                        begin_time=Datetime(2023, 1, 1, 0, 0, 0),
                        end_time=Datetime(2023, 1, 1, 10, 59, 59),
                        wi=WindIntensityFactory(35.0),
                    )
                ],
                WindSynthesisError,
            ),
            (
                # 2 unordered Pci
                [
                    Pci(
                        begin_time=Datetime(2023, 1, 1, 7, 0, 0),
                        end_time=Datetime(2023, 1, 1, 9, 0, 0),
                        wi=WindIntensityFactory(35.0),
                    ),
                    Pci(
                        begin_time=Datetime(2023, 1, 1, 2, 0, 0),
                        end_time=Datetime(2023, 1, 1, 5, 0, 0),
                        wi=WindIntensityFactory(35.0),
                    ),
                ],
                WindSynthesisError,
            ),
        ],
    )
    def test_pci_exceptions(self, pci_list, exception):
        with pytest.raises(exception):
            self.WIND_BLOCK.set_pci(pci_list)

    @pytest.mark.parametrize(
        "blocks, expected",
        [
            (
                [
                    WindBlock(
                        begin_time=Datetime(2023, 1, 2, 0, 0, 0),
                        end_time=Datetime(2023, 1, 2, 10, 0, 0),
                        pci=[
                            Pci(
                                begin_time=Datetime(2023, 1, 2, 0, 0, 0),
                                end_time=Datetime(2023, 1, 2, 8, 0, 0),
                                wi=WindIntensityFactory(40.0),
                            )
                        ],
                        pcd=[
                            Pcd(
                                begin_time=Datetime(2023, 1, 2, 1, 0, 0),
                                end_time=Datetime(2023, 1, 2, 6, 0, 0),
                                wd=WindDirection(10.0, 40.0),
                            )
                        ],
                    ),
                    WindBlock(
                        begin_time=Datetime(2023, 1, 2, 12, 0, 0),
                        end_time=Datetime(2023, 1, 2, 23, 0, 0),
                        pci=[
                            Pci(
                                begin_time=Datetime(2023, 1, 2, 13, 0, 0),
                                end_time=Datetime(2023, 1, 2, 14, 0, 0),
                                wi=WindIntensityFactory(50.0),
                            )
                        ],
                        pcd=[
                            Pcd(
                                begin_time=Datetime(2023, 1, 2, 13, 0, 0),
                                end_time=Datetime(2023, 1, 2, 18, 0, 0),
                                wd=WindDirection(10.0, 40.0),
                            )
                        ],
                    ),
                ],
                WindBlock(
                    begin_time=Datetime(2023, 1, 2, 0, 0, 0),
                    end_time=Datetime(2023, 1, 2, 23, 0, 0),
                    pci=[
                        Pci(
                            begin_time=Datetime(2023, 1, 2, 0, 0, 0),
                            end_time=Datetime(2023, 1, 2, 8, 0, 0),
                            wi=WindIntensityFactory(40.0),
                        ),
                        Pci(
                            begin_time=Datetime(2023, 1, 2, 13, 0, 0),
                            end_time=Datetime(2023, 1, 2, 14, 0, 0),
                            wi=WindIntensityFactory(50.0),
                        ),
                    ],
                    pcd=[
                        Pcd(
                            begin_time=Datetime(2023, 1, 2, 1, 0, 0),
                            end_time=Datetime(2023, 1, 2, 6, 0, 0),
                            wd=WindDirection(10.0, 40.0),
                        ),
                        Pcd(
                            begin_time=Datetime(2023, 1, 2, 13, 0, 0),
                            end_time=Datetime(2023, 1, 2, 18, 0, 0),
                            wd=WindDirection(10.0, 40.0),
                        ),
                    ],
                ),
            )
        ],
    )
    def test_merge(self, blocks, expected):
        assert blocks[0].merge(blocks[1]) == expected

    @pytest.mark.parametrize(
        "blocks",
        [
            [
                WindBlock(
                    begin_time=Datetime(2023, 1, 2, 0, 0, 0),
                    end_time=Datetime(2023, 1, 2, 5, 0, 0),
                ),
                WindBlock(
                    begin_time=Datetime(2023, 1, 2, 2, 0, 0),
                    end_time=Datetime(2023, 1, 2, 10, 0, 0),
                ),
            ],
            [
                WindBlock(
                    begin_time=Datetime(2023, 1, 2, 0, 0, 0),
                    end_time=Datetime(2023, 1, 2, 5, 0, 0),
                ),
                WindBlock(
                    begin_time=Datetime(2023, 1, 2, 2, 0, 0),
                    end_time=Datetime(2023, 1, 2, 3, 0, 0),
                ),
            ],
        ],
    )
    def test_merge_exception(self, blocks):
        with pytest.raises(WindSynthesisError):
            blocks[0].merge(blocks[1])
