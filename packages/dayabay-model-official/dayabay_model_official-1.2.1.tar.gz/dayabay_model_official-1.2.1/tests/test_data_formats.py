from os import environ

from dag_modelling.tools.logger import set_verbosity
from numpy import allclose, fabs
from pytest import mark

from dayabay_model_official import model_dayabay

source_type_reference = "hdf5"
source_types_other = ["tsv", "npz", "root"]

precision_requirement = {"tsv": 2.0e-10, "root": 0, "npz": 0}
set_verbosity(1)


@mark.parametrize("source_type", source_types_other)
def test_dayabay_v0(source_type: str):
    data_location = "dayabay-data-official"
    model_ref = model_dayabay(
        path_data=f"{data_location}/{source_type_reference}",
    )
    model = model_dayabay(
        path_data=f"{data_location}/{source_type}",
    )

    outname = "outputs.eventscount.final.concatenated.detector_period"
    output_ref = model_ref.storage[outname]
    output = model.storage[outname]

    data_ref = output_ref.data
    data = output.data

    diff = fabs(data - data_ref)
    diff_rel = diff / data_ref
    diff_rel[data_ref == 0.0] = 0.0
    print(f"{source_type}: maxdiff {diff.max()} rel. diff max {diff_rel.max()}")

    rtol = precision_requirement[source_type]
    assert allclose(data, data_ref, rtol=rtol, atol=0.0), f"{source_type} requires {rtol=}"
