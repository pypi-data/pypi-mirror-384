import json

import pytest

from module_qc_data_tools import (
    get_layer_from_sn,
    get_n_chips,
    get_nominal_current,
)


def test_get_nominal_current():
    data = json.dumps(
        {
            "tasks": {
                "GENERAL": {
                    "v_max": 3.0,
                    "i_config": {
                        "RD53B": {"L0": 5.55, "L1": 6.60, "L2": 5.88},
                        "ITKPIXV2_V1bom": {"L0": 5.67, "L1": 6.50, "L2": 6.06},
                    },
                },
            }
        }
    )

    meas_config = json.loads(data)
    serial_number = "20UPGM23210492"
    layer = get_layer_from_sn(serial_number)

    if serial_number[7] in ["1", "2"]:
        chip_type = "RD53B"
        assert_nom_curr = 5.88
    if serial_number[7] == "3":
        chip_type = "ITKPIXV2"
        assert_nom_curr = 6.06

    for n in range(5):
        expected_current = (
            float(n * assert_nom_curr / get_n_chips(layer))
            if n > 0
            else assert_nom_curr
        )
        assert (
            get_nominal_current(
                meas_config, layer, chip_type, "_V1bom", n_chips_input=n
            )
            == expected_current
        )


if __name__ == "__main__":
    pytest.main()
