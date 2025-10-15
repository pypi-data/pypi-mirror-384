import os
import subprocess
from collections.abc import Sequence


def _run_script(script: str) -> tuple[str, str, int]:
    print("Starting the test of the following script: ", script)
    result = subprocess.run(
        [script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout = result.stdout.decode()
    stderr = result.stderr.decode()

    if result.returncode != 0:
        print()
        print("stdout:")
        print(stdout)
        print()
        print("stderr:")
        print(stderr)
        print()
        print("Failed command:")
        print(script)
        print()

    assert result.returncode == 0

    return (stdout, stderr, result.returncode)


def _check_script_result(
    returncode: int,
    stderr: str,
    stdout: str | None,
    output_paths: Sequence | str | None,
):
    assert returncode == 0
    assert stderr == ""

    if isinstance(output_paths, str):
        output_paths = (output_paths,)

    if isinstance(output_paths, Sequence):
        for output_path in output_paths:
            if output_path is not None:
                if stdout is not None:
                    assert f"Write: {output_path}" in stdout

                assert os.path.exists(output_path)


def test_run_dayabay_plot_all_nodes():
    output_path = "output/background_plots"
    stdout, stderr, code = _run_script(
        "./tests/shell/test_dayabay-plot-all-outputs-2.sh",
    )
    _check_script_result(code, stderr, stdout, output_path)


def test_run_dayabay_plot_subgraph():
    output_path = "output/dayabay_graphs"
    stdout, stderr, code = _run_script(
        "./tests/shell/test_dayabay-plot-all-subgraphs-2.sh",
    )
    _check_script_result(code, stderr, stdout, output_path)


def test_run_dayabay_plot_detector_data():
    output = "output/detector_{type}.pdf"

    stdout, stderr, code = _run_script(
        "./tests/shell/test_dayabay-plot-detector-data.sh",
    )

    _check_script_result(code, stderr, stdout, None)
    for type in ["eff", "eff_livetime", "rate_accidentals"]:
        assert f"Save plot: {output.format(type=type)}" in stdout
        assert os.path.exists(output.format(type=type))


def test_run_dayabay_plot_reactor_data():
    output = "output/reactor_{type}.pdf"

    stdout, stderr, code = _run_script(
        "./tests/shell/test_dayabay-plot-reactor-data.sh",
    )

    _check_script_result(code, stderr, stdout, None)
    for type in ["power", "fission_fraction"]:
        assert f"Save plot: {output.format(type=type)}" in stdout
        assert os.path.exists(output.format(type=type))


def test_run_dayabay_print_internal_data():
    stdout, stderr, code = _run_script(
        "./tests/shell/test_dayabay-print-internal-data-3.sh",
    )

    _check_script_result(code, stderr, stdout, None)
    assert "parameters.free" in stdout
    assert "parameters.constrained" in stdout


def test_run_dayabay_print_parameters_latex():
    output_path = "output/parameters"
    _, stderr, code = _run_script(
        "./tests/shell/test_dayabay-print-parameters-latex.sh",
    )

    _check_script_result(code, stderr, None, output_path)


def test_run_dayabay_print_parameters_text():
    output_path = "output/parameters.txt"
    _, stderr, code = _run_script(
        "./tests/shell/test_dayabay-print-parameters-text.sh",
    )

    _check_script_result(code, stderr, None, output_path)


def test_run_dayabay_print_summary():
    output_paths = [
        "output/dayabay_summary.tsv",
        "output/dayabay_summary.tsv.bz2",
        "output/dayabay_summary.npz",
        "output/dayabay_summary.hdf5",
    ]
    _, stderr, code = _run_script(
        "./tests/shell/test_dayabay-print-summary.sh",
    )

    _check_script_result(code, stderr, None, output_paths)


def test_run_dayabay_save_detector_response_matrices():
    output_data_path = "output/matrix.{ext}"
    output_plot_path = "output/matrix_{type}.pdf"
    _, stderr, code = _run_script(
        "./tests/shell/test_dayabay-save-detector-response-matrices.sh",
    )

    _check_script_result(code, stderr, None, None)
    for ext in ["tsv", "npz", "hdf5"]:
        assert os.path.exists(output_data_path.format(ext=ext))

    for type in ["iav", "lsnl", "eres", "total"]:
        assert os.path.exists(output_plot_path.format(type=type))


def test_run_dayabay_save_parameters_to_latex_datax():
    output_path = "output/dayabay_parameters_datax.tex"
    _, stderr, code = _run_script(
        "./tests/shell/test_dayabay-save-parameters-to-latex-datax.sh",
    )

    _check_script_result(code, stderr, None, output_path)
