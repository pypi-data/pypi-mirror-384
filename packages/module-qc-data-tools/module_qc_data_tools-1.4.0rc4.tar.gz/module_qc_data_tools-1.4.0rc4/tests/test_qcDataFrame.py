import json

from module_qc_data_tools import outputDataFrame, qcDataFrame


def test_valid_keys(datadir):
    data_chip1, *_ = json.loads(datadir.joinpath("20UPGXM1234567.json").read_text())[0]

    # create inputDF
    inputDF = outputDataFrame(_dict=data_chip1)
    qcframe = inputDF.get_results()
    metadata = qcframe.get_meta_data()

    # create outputDF
    outputDF = outputDataFrame()
    outputDF.set_test_type("ADC_CALIBRATION")
    data = qcDataFrame()
    data._meta_data.update(metadata)
    data.add_meta_data("SOME_METADATA", "metadata_value")
    data.add_property("SOME_PROPERTY", "property_value")
    data.add_parameter("SOME_PARAMETER", "parameter_value")

    outputDF.set_results(data)
    outputDF.set_pass_flag(False)
    output_dict = outputDF.to_dict(True)

    assert list(output_dict.keys()) == [
        "serialNumber",
        "testType",
        "runNumber",
        "results",
        "passed",
    ]
    assert "results" in output_dict
    assert "property" in output_dict["results"]
    assert "Metadata" in output_dict["results"]
    assert "DCSdata" in output_dict["results"]
