
from shiny import App, ui, reactive, render, req
from pycompound.spec_lib_matching import run_spec_lib_matching_on_HRMS_data 
from pycompound.spec_lib_matching import run_spec_lib_matching_on_NRMS_data 
from pycompound.spec_lib_matching import tune_params_on_HRMS_data
from pycompound.spec_lib_matching import tune_params_on_NRMS_data
from pycompound.plot_spectra import generate_plots_on_HRMS_data
from pycompound.plot_spectra import generate_plots_on_NRMS_data
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
import subprocess
import traceback
import asyncio
import io
import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import netCDF4 as nc
from pyteomics import mgf, mzml
import ast


_LOG_QUEUE: asyncio.Queue[str] = asyncio.Queue()


def strip_text(s):
    return [x.strip() for x in s.strip('[]').split(',') if x.strip()]


def strip_numeric(s):
    return [float(x.strip()) for x in s.strip('[]').split(',') if x.strip()]


def strip_weights(s):
    tuples = ast.literal_eval(s)
    keys = ['Cosine', 'Shannon', 'Renyi', 'Tsallis']
    return [dict(zip(keys,t)) for t in tuples]


def build_library(input_path=None, output_path=None):
    last_three_chars = input_path[(len(input_path)-3):len(input_path)]
    last_four_chars = input_path[(len(input_path)-4):len(input_path)]
    if last_three_chars == 'csv' or last_three_chars == 'CSV':
        return pd.read_csv(input_path)
    else:
        if last_three_chars == 'mgf' or last_three_chars == 'MGF':
            input_file_type = 'mgf'
        elif last_four_chars == 'mzML' or last_four_chars == 'mzml' or last_four_chars == 'MZML':
            input_file_type = 'mzML'
        elif last_three_chars == 'cdf' or last_three_chars == 'CDF':
            input_file_type = 'cdf'
        elif last_three_chars == 'msp' or last_three_chars == 'MSP':
            input_file_type = 'msp'
        else:
            print('ERROR: either an \'mgf\', \'mzML\', \'cdf\', or \'msp\' file must be passed to --input_path')
            sys.exit()

        spectra = []
        if input_file_type == 'mgf':
            with mgf.read(input_path, index_by_scans = True) as reader:
                for spec in reader:
                    spectra.append(spec)
        if input_file_type == 'mzML':
            with mzml.read(input_path) as reader:
                for spec in reader:
                    spectra.append(spec)

        if input_file_type == 'mgf' or input_file_type == 'mzML':
            ids = []
            mzs = []
            ints = []
            for i in range(0,len(spectra)):
                for j in range(0,len(spectra[i]['m/z array'])):
                    if input_file_type == 'mzML':
                        ids.append(f'ID_{i+1}')
                    else:
                        ids.append(spectra[i]['params']['name'])
                    mzs.append(spectra[i]['m/z array'][j])
                    ints.append(spectra[i]['intensity array'][j])

        if input_file_type == 'cdf':
            dataset = nc.Dataset(input_path, 'r')
            all_mzs = dataset.variables['mass_values'][:]
            all_ints = dataset.variables['intensity_values'][:]
            scan_idxs = dataset.variables['scan_index'][:]
            dataset.close()

            ids = []
            mzs = []
            ints = []
            for i in range(0,(len(scan_idxs)-1)):
                if i % 1000 == 0:
                    print(f'analyzed {i} out of {len(scan_idxs)} scans')
                s_idx = scan_idxs[i]
                e_idx = scan_idxs[i+1]

                mzs_tmp = all_mzs[s_idx:e_idx]
                ints_tmp = all_ints[s_idx:e_idx]

                for j in range(0,len(mzs_tmp)):
                    ids.append(f'ID_{i+1}')
                    mzs.append(mzs_tmp[j])
                    ints.append(ints_tmp[j])

        if input_file_type == 'msp':
            ids = []
            mzs = []
            ints = []
            with open(input_path, 'r') as f:
                i = 0
                for line in f:
                    line = line.strip()
                    if line.startswith('Name:'):
                        i += 1
                        spectrum_id = line.replace('Name: ','')
                    elif line and line[0].isdigit():
                        try:
                            mz, intensity = map(float, line.split()[:2])
                            ids.append(spectrum_id)
                            mzs.append(mz)
                            ints.append(intensity)
                        except ValueError:
                            continue

        df = pd.DataFrame({'id':ids, 'mz_ratio':mzs, 'intensity':ints})
        return df



def extract_first_column_ids(file_path: str, max_ids: int = 20000):
    suffix = Path(file_path).suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(file_path, usecols=[0])
        ids = df.iloc[:, 0].astype(str).dropna()
        ids = [x for x in ids if x.strip() != ""]
        seen = set()
        uniq = []
        for x in ids:
            if x not in seen:
                uniq.append(x)
                seen.add(x)
        return uniq[:max_ids]

    ids = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                ls = line.strip()
                if ls.startswith("TITLE="):
                    ids.append(ls.split("=", 1)[1].strip())
                elif ls.lower().startswith("name:"):
                    ids.append(ls.split(":", 1)[1].strip())
                if len(ids) >= max_ids:
                    break
    except Exception:
        pass

    if ids:
        seen = set()
        uniq = []
        for x in ids:
            if x not in seen:
                uniq.append(x)
                seen.add(x)
        return uniq
    return []


def _open_plot_window(session, png_bytes: bytes, title: str = "plot.png"):
    """Send PNG bytes to browser and open in a new window as a data URL."""
    b64 = base64.b64encode(png_bytes).decode("ascii")
    data_url = f"data:image/png;base64,{b64}"
    session.send_custom_message("open-plot-window", {"png": data_url, "title": title})


def plot_spectra_ui(platform: str):
    # Base inputs common to all platforms
    base_inputs = [
        ui.input_file("query_data", "Upload query dataset (mgf, mzML, cdf, msp, or csv):"),
        ui.input_file("reference_data", "Upload reference dataset (mgf, mzML, cdf, msp, or csv):"),
        ui.input_selectize(
            "spectrum_ID1",
            "Select spectrum ID 1 (default is the first spectrum in the library):",
            choices=[],
            multiple=False,
            options={"placeholder": "Upload a library..."},
        ),
        ui.input_selectize(
            "spectrum_ID2",
            "Select spectrum ID 2 (default is the first spectrum in the library):",
            choices=[],
            multiple=False,
            options={"placeholder": "Upload a library..."},
        ),
        ui.input_select("similarity_measure", "Select similarity measure:", ["cosine","shannon","renyi","tsallis","mixture","jaccard","dice","3w_jaccard","sokal_sneath","binary_cosine","mountford","mcconnaughey","driver_kroeber","simpson","braun_banquet","fager_mcgowan","kulczynski","intersection","hamming","hellinger"]),
        ui.input_text('weights', 'Weights for similarity measure (cosine, shannon, renyi, tsallis):', '0.25, 0.25, 0.25, 0.25'),
        ui.input_select(
            "high_quality_reference_library",
            "Indicate whether the reference library is considered high quality. If True, filtering and noise removal are only applied to the query spectra.",
            [False, True],
        ),
    ]

    # Extra inputs depending on platform
    if platform == "HRMS":
        extra_inputs = [
            ui.input_text(
                "spectrum_preprocessing_order",
                "Sequence of characters for preprocessing order (C (centroiding), F (filtering), M (matching), N (noise removal), L (low-entropy transformation), W (weight factor transformation)). M must be included, C before M if used.",
                "FCNMWL",
            ),
            ui.input_numeric("window_size_centroiding", "Centroiding window-size:", 0.5),
            ui.input_numeric("window_size_matching", "Matching window-size:", 0.5),
        ]
    else:
        extra_inputs = [
            ui.input_text(
                "spectrum_preprocessing_order",
                "Sequence of characters for preprocessing order (F (filtering), N (noise removal), L (low-entropy transformation), W (weight factor transformation)).",
                "FNLW",
            )
        ]

    # Numeric inputs
    numeric_inputs = [
        ui.input_numeric("mz_min", "Minimum m/z for filtering:", 0),
        ui.input_numeric("mz_max", "Maximum m/z for filtering:", 99999999),
        ui.input_numeric("int_min", "Minimum intensity for filtering:", 0),
        ui.input_numeric("int_max", "Maximum intensity for filtering:", 999999999),
        ui.input_numeric("noise_threshold", "Noise removal threshold:", 0.0),
        ui.input_numeric("wf_mz", "Mass/charge weight factor:", 0.0),
        ui.input_numeric("wf_int", "Intensity weight factor:", 1.0),
        ui.input_numeric("LET_threshold", "Low-entropy threshold:", 0.0),
        ui.input_numeric("entropy_dimension", "Entropy dimension (Renyi/Tsallis only):", 1.1),
    ]

    # Y-axis transformation select input
    select_input = ui.input_select(
        "y_axis_transformation",
        "Transformation to apply to intensity axis:",
        ["normalized", "none", "log10", "sqrt"],
    )

    # Run and Back buttons
    run_button_plot_spectra = ui.download_button("run_btn_plot_spectra", "Run", style="font-size:16px; padding:15px 30px; width:200px; height:80px")
    back_button = ui.input_action_button("back", "Back to main menu", style="font-size:16px; padding:15px 30px; width:200px; height:80px")

    # Layout base_inputs and extra_inputs in columns
    if platform == "HRMS":
        inputs_columns = ui.layout_columns(
            ui.div(base_inputs[0:6], style="display:flex; flex-direction:column; gap:10px;"),
            ui.div([base_inputs[6:7], *extra_inputs], style="display:flex; flex-direction:column; gap:10px;"),
            ui.div(numeric_inputs[0:5], style="display:flex; flex-direction:column; gap:10px;"),
            ui.div([numeric_inputs[5:10], select_input], style="display:flex; flex-direction:column; gap:10px;"),
            col_widths=(3,3,3,3),
        )
    elif platform == "NRMS":
        inputs_columns = ui.layout_columns(
            ui.div(base_inputs[0:6], style="display:flex; flex-direction:column; gap:10px;"),
            ui.div([base_inputs[6:7], *extra_inputs], style="display:flex; flex-direction:column; gap:10px;"),
            ui.div(numeric_inputs[0:5], style="display:flex; flex-direction:column; gap:10px;"),
            ui.div([numeric_inputs[5:10], select_input], style="display:flex; flex-direction:column; gap:10px;"),
            col_widths=(3,3,3,3),
        )

    # Combine everything
    return ui.div(
        ui.TagList(
            ui.h2("Plot Spectra"),
            inputs_columns,
            run_button_plot_spectra,
            back_button,
            ui.div(ui.output_text("plot_query_status"), style="margin-top:8px; font-size:14px"),
            ui.div(ui.output_text("plot_reference_status"), style="margin-top:8px; font-size:14px")
        ),
    )



def run_spec_lib_matching_ui(platform: str):
    # Base inputs common to all platforms
    base_inputs = [
        ui.input_file("query_data", "Upload query dataset (mgf, mzML, cdf, msp, or csv):"),
        ui.input_file("reference_data", "Upload reference dataset (mgf, mzML, cdf, msp, or csv):"),
        ui.input_select("similarity_measure", "Select similarity measure:", ["cosine","shannon","renyi","tsallis","mixture","jaccard","dice","3w_jaccard","sokal_sneath","binary_cosine","mountford","mcconnaughey","driver_kroeber","simpson","braun_banquet","fager_mcgowan","kulczynski","intersection","hamming","hellinger"]),
        ui.input_text('weights', 'Weights for similarity measure (cosine, shannon, renyi, tsallis):', '0.25, 0.25, 0.25, 0.25'),
        ui.input_selectize(
            "spectrum_ID1",
            "Select spectrum ID 1 (only applicable for plotting; default is the first spectrum in the query library):",
            choices=[],
            multiple=False,
            options={"placeholder": "Upload a library..."},
        ),
        ui.input_selectize(
            "spectrum_ID2",
            "Select spectrum ID 2 (only applicable for plotting; default is the first spectrum in the reference library):",
            choices=[],
            multiple=False,
            options={"placeholder": "Upload a library..."},
        ),
        ui.input_select(
            "high_quality_reference_library",
            "Indicate whether the reference library is considered high quality. If True, filtering and noise removal are only applied to the query spectra.",
            [False, True],
        )
    ]

    # Extra inputs depending on platform
    if platform == "HRMS":
        extra_inputs = [
            ui.input_text(
                "spectrum_preprocessing_order",
                "Sequence of characters for preprocessing order (C (centroiding), F (filtering), M (matching), N (noise removal), L (low-entropy transformation), W (weight factor transformation)). M must be included, C before M if used.",
                "FCNMWL",
            ),
            ui.input_numeric("window_size_centroiding", "Centroiding window-size:", 0.5),
            ui.input_numeric("window_size_matching", "Matching window-size:", 0.5),
        ]
    else:
        extra_inputs = [
            ui.input_text(
                "spectrum_preprocessing_order",
                "Sequence of characters for preprocessing order (F (filtering), N (noise removal), L (low-entropy transformation), W (weight factor transformation)).",
                "FNLW",
            )
        ]

    # Numeric inputs
    numeric_inputs = [
        ui.input_numeric("mz_min", "Minimum m/z for filtering:", 0),
        ui.input_numeric("mz_max", "Maximum m/z for filtering:", 99999999),
        ui.input_numeric("int_min", "Minimum intensity for filtering:", 0),
        ui.input_numeric("int_max", "Maximum intensity for filtering:", 999999999),
        ui.input_numeric("noise_threshold", "Noise removal threshold:", 0.0),
        ui.input_numeric("wf_mz", "Mass/charge weight factor:", 0.0),
        ui.input_numeric("wf_int", "Intensity weight factor:", 1.0),
        ui.input_numeric("LET_threshold", "Low-entropy threshold:", 0.0),
        ui.input_numeric("entropy_dimension", "Entropy dimension (Renyi/Tsallis only):", 1.1),
        ui.input_numeric("n_top_matches_to_save", "Number of top matches to save:", 3),
    ]


    # Run and Back buttons
    run_button_spec_lib_matching = ui.download_button("run_btn_spec_lib_matching", "Run Spectral Library Matching", style="font-size:16px; padding:15px 30px; width:200px; height:80px")
    run_button_plot_spectra_within_spec_lib_matching = ui.download_button("run_btn_plot_spectra_within_spec_lib_matching", "Plot Spectra", style="font-size:16px; padding:15px 30px; width:200px; height:80px")
    back_button = ui.input_action_button("back", "Back to main menu", style="font-size:16px; padding:15px 30px; width:200px; height:80px")

    # Layout base_inputs and extra_inputs in columns
    if platform == "HRMS":
        inputs_columns = ui.layout_columns(
            ui.div(base_inputs[0:6], style="display:flex; flex-direction:column; gap:10px;"),
            ui.div([base_inputs[6:7], *extra_inputs], style="display:flex; flex-direction:column; gap:10px;"),
            ui.div(numeric_inputs[0:5], style="display:flex; flex-direction:column; gap:10px;"),
            ui.div(numeric_inputs[5:10], style="display:flex; flex-direction:column; gap:10px;"),
            col_widths=(3,3,3,3)
        )
    elif platform == "NRMS":
        inputs_columns = ui.layout_columns(
            ui.div(base_inputs[0:6], style="display:flex; flex-direction:column; gap:10px;"),
            ui.div([base_inputs[6:7], *extra_inputs], style="display:flex; flex-direction:column; gap:10px;"),
            ui.div(numeric_inputs[0:5], style="display:flex; flex-direction:column; gap:10px;"),
            ui.div(numeric_inputs[5:10], style="display:flex; flex-direction:column; gap:10px;"),
            col_widths=(3,3,3,3)
        )

    log_panel = ui.card(
        ui.card_header("Identification log"),
        ui.output_text_verbatim("match_log"),
        style="max-height:300px; overflow:auto"
    )

    # Combine everything
    return ui.div(
        ui.TagList(
            ui.h2("Run Spectral Library Matching"),
            inputs_columns,
            run_button_spec_lib_matching,
            run_button_plot_spectra_within_spec_lib_matching,
            back_button,
            log_panel
        ),
    )



def run_parameter_tuning_ui(platform: str):
    # Base inputs common to all platforms
    base_inputs = [
        ui.input_file("query_data", "Upload query dataset (mgf, mzML, cdf, msp, or csv):"),
        ui.input_file("reference_data", "Upload reference dataset (mgf, mzML, cdf, msp, or csv):"),
        ui.input_selectize("similarity_measure", "Select similarity measure(s):", ["cosine","shannon","renyi","tsallis","mixture","jaccard","dice","3w_jaccard","sokal_sneath","binary_cosine","mountford","mcconnaughey","driver_kroeber","simpson","braun_banquet","fager_mcgowan","kulczynski","intersection","hamming","hellinger"], multiple=True, selected='cosine'),
        ui.input_text('weights', 'Weights for similarity measure (cosine, shannon, renyi, tsallis):', '((0.25, 0.25, 0.25, 0.25), (0.2, 0.3, 0.4, 0.1))'),
        ui.input_text("high_quality_reference_library", "Indicate whether the reference library is considered high quality. If True, filtering and noise removal are only applied to the query spectra.", '[True]')
    ]

    # Extra inputs depending on platform
    if platform == "HRMS":
        extra_inputs = [
            ui.input_text(
                "spectrum_preprocessing_order",
                "Sequence of characters for preprocessing order (C (centroiding), F (filtering), M (matching), N (noise removal), L (low-entropy transformation), W (weight factor transformation)). M must be included, C before M if used.",
                "[FCNMWL,CWM]",
            ),
            ui.input_text("window_size_centroiding", "Centroiding window-size:", "[0.5]"),
            ui.input_text("window_size_matching", "Matching window-size:", "[0.1,0.5]"),
        ]
    else:
        extra_inputs = [
            ui.input_text(
                "spectrum_preprocessing_order",
                "Sequence of characters for preprocessing order (F (filtering), N (noise removal), L (low-entropy transformation), W (weight factor transformation)).",
                "[FNLW,WNL]",
            )
        ]

    # Numeric inputs
    numeric_inputs = [
        ui.input_text("mz_min", "Minimum m/z for filtering:", '[0]'),
        ui.input_text("mz_max", "Maximum m/z for filtering:", '[99999999]'),
        ui.input_text("int_min", "Minimum intensity for filtering:", '[0]'),
        ui.input_text("int_max", "Maximum intensity for filtering:", '[999999999]'),
        ui.input_text("noise_threshold", "Noise removal threshold:", '[0.0]'),
        ui.input_text("wf_mz", "Mass/charge weight factor:", '[0.0]'),
        ui.input_text("wf_int", "Intensity weight factor:", '[1.0]'),
        ui.input_text("LET_threshold", "Low-entropy threshold:", '[0.0]'),
        ui.input_text("entropy_dimension", "Entropy dimension (Renyi/Tsallis only):", '[1.1]')
    ]


    # Run and Back buttons
    run_button_parameter_tuning = ui.download_button("run_btn_parameter_tuning", "Tune parameters", style="font-size:16px; padding:15px 30px; width:200px; height:80px")
    back_button = ui.input_action_button("back", "Back to main menu", style="font-size:16px; padding:15px 30px; width:200px; height:80px")

    # Layout base_inputs and extra_inputs in columns
    if platform == "HRMS":
        inputs_columns = ui.layout_columns(
            ui.div(base_inputs[0:6], style="display:flex; flex-direction:column; gap:10px;"),
            ui.div([base_inputs[6:7], *extra_inputs], style="display:flex; flex-direction:column; gap:10px;"),
            ui.div(numeric_inputs[0:5], style="display:flex; flex-direction:column; gap:10px;"),
            ui.div(numeric_inputs[5:9], style="display:flex; flex-direction:column; gap:10px;"),
            col_widths=(3, 3, 3, 3),
        )
    elif platform == "NRMS":
        inputs_columns = ui.layout_columns(
            ui.div(base_inputs[0:6], style="display:flex; flex-direction:column; gap:10px;"),
            ui.div([base_inputs[6:7], *extra_inputs], style="display:flex; flex-direction:column; gap:10px;"),
            ui.div(numeric_inputs[0:5], style="display:flex; flex-direction:column; gap:10px;"),
            ui.div(numeric_inputs[5:9], style="display:flex; flex-direction:column; gap:10px;"),
            col_widths=(3, 3, 3, 3),
        )

    log_panel = ui.card(
        ui.card_header("Identification log"),
        ui.output_text_verbatim("match_log"),
        style="max-height:300px; overflow:auto"
    )

    # Combine everything
    return ui.div(
        ui.TagList(
            ui.h2("Tune parameters"),
            inputs_columns,
            run_button_parameter_tuning,
            back_button,
            log_panel
        ),
    )




app_ui = ui.page_fluid(
    ui.output_ui("main_ui"),
    ui.output_text("status_output")
)


def server(input, output, session):

    current_page = reactive.Value("main_menu")
    
    plot_clicks = reactive.Value(0)
    match_clicks = reactive.Value(0)
    back_clicks = reactive.Value(0)

    run_status_plot_spectra = reactive.Value("")
    run_status_spec_lib_matching = reactive.Value("")
    run_status_plot_spectra_within_spec_lib_matching = reactive.Value("")
    run_status_parameter_tuning = reactive.Value("")
    is_tuning_running = reactive.Value(False)
    match_log_rv = reactive.Value("")
    is_matching_rv = reactive.Value(False)
    is_any_job_running = reactive.Value(False)

    query_ids_rv = reactive.Value([])
    query_file_path_rv = reactive.Value(None)
    query_result_rv = reactive.Value(None)
    query_status_rv = reactive.Value("")
    reference_ids_rv = reactive.Value([])
    reference_file_path_rv = reactive.Value(None)
    reference_result_rv = reactive.Value(None)
    reference_status_rv = reactive.Value("")

    converted_query_path_rv = reactive.Value(None)
    converted_reference_path_rv = reactive.Value(None)


    #def _drain_queue_nowait(q: asyncio.Queue[str]) -> list[str]:
    def _drain_queue_nowait(q: asyncio.Queue) -> list[str]:
        out = []
        try:
            while True:
                out.append(q.get_nowait())
        except asyncio.QueueEmpty:
            pass
        return out


    @reactive.effect
    async def _pump_logs():
        if not is_any_job_running.get():
            return

        reactive.invalidate_later(0.1)
        msgs = _drain_queue_nowait(_LOG_QUEUE)
        if msgs:
            match_log_rv.set(match_log_rv.get() + "".join(msgs))
            await reactive.flush()


    def process_database(file_path: str):
        suffix = Path(file_path).suffix.lower()
        return {"path": file_path, "suffix": suffix}

    @render.text
    def plot_query_status():
        return query_status_rv.get() or ""

    @render.text
    def plot_reference_status():
        return reference_status_rv.get() or ""


    @reactive.effect
    @reactive.event(input.query_data)
    async def _on_query_upload():
        files = input.query_data()
        req(files and len(files) > 0)

        file_path = files[0]["datapath"]
        query_file_path_rv.set(file_path)

        query_status_rv.set(f"Processing query database: {Path(file_path).name} …")
        await reactive.flush()

        try:
            result = await asyncio.to_thread(process_database, file_path)
            query_result_rv.set(result)
            query_status_rv.set("✅ Query database processed.")
            await reactive.flush()
        except Exception as e:
            query_status_rv.set(f"❌ Failed to process query database: {e}")
            await reactive.flush()


    @reactive.effect
    @reactive.event(input.reference_data)
    async def _on_reference_upload():
        files = input.reference_data()
        req(files and len(files) > 0)

        file_path = files[0]["datapath"]
        reference_file_path_rv.set(file_path)

        reference_status_rv.set(f"Processing reference database: {Path(file_path).name} …")
        await reactive.flush()

        try:
            result = await asyncio.to_thread(process_database, file_path)
            reference_result_rv.set(result)
            reference_status_rv.set("✅ Reference database processed.")
            await reactive.flush()
        except Exception as e:
            reference_status_rv.set(f"❌ Failed to process reference database: {e}")
            await reactive.flush()


    @render.text
    def match_log():
        return match_log_rv.get()


    class ReactiveWriter(io.TextIOBase):
        def __init__(self, rv):
            self.rv = rv
        def write(self, s: str):
            if not s:
                return 0
            self.rv.set(self.rv.get() + s)
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(reactive.flush())
            except RuntimeError:
                pass
            return len(s)
        def flush(self):
            pass



    @reactive.Effect
    def _():
        if input.plot_spectra() > plot_clicks.get():
            current_page.set("plot_spectra")
            plot_clicks.set(input.plot_spectra())
        elif input.run_spec_lib_matching() > match_clicks.get():
            current_page.set("run_spec_lib_matching")
            match_clicks.set(input.run_spec_lib_matching())
        elif input.run_parameter_tuning() > match_clicks.get():
            current_page.set("run_parameter_tuning")
            match_clicks.set(input.run_parameter_tuning())
        elif hasattr(input, "back") and input.back() > back_clicks.get():
            current_page.set("main_menu")
            back_clicks.set(input.back())


    @render.image
    def image():
        from pathlib import Path

        dir = Path(__file__).resolve().parent
        img: ImgData = {"src": str(dir / "www/emblem.png"), "width": "320px", "height": "250px"}
        return img


    @output
    @render.ui
    def main_ui():
        if current_page() == "main_menu":
            return ui.page_fluid(
                ui.h2("Main Menu"),
                ui.div(
                    ui.output_image("image"),
                    style=(
                        "position:fixed; top:0; left:50%; transform:translateX(-50%); "
                        "z-index:1000; text-align:center; padding:10px; background-color:white;"
                    ),
                ),
                ui.div(
                    "Overview:",
                    style="text-align:left; font-size:24px; font-weight:bold; margin-top:350px"
                ),
                ui.div(
                    "PyCompound is a Python-based tool designed for performing spectral library matching on either high-resolution mass spectrometry data (HRMS) or low-resolution mass spectrometry data (NRMS). PyCompound offers a range of spectrum preprocessing transformations and similarity measures. These spectrum preprocessing transformations include filtering on mass/charge and/or intensity values, weight factor transformation, low-entropy transformation, centroiding, noise removal, and matching. The available similarity measures include the canonical Cosine similarity measure, three entropy-based similarity measures, and a variety of binary similarity measures: Jaccard, Dice, 3W-Jaccard, Sokal-Sneath, Binary Cosine, Mountford, McConnaughey, Driver-Kroeber, Simpson, Braun-Banquet, Fager-McGowan, Kulczynski, Intersection, Hamming, and Hellinger.",
                    style="margin-top:10px; text-align:left; font-size:16px; font-weight:500"
                ),
                ui.div(
                    "Select options:",
                    style="margin-top:30px; text-align:left; font-size:24px; font-weight:bold"
                ),
                ui.div(
                    ui.input_radio_buttons("chromatography_platform", "Specify chromatography platform:", ["HRMS","NRMS"]),
                    style="font-size:18px; margin-top:10px; max-width:none"
                ),
                ui.input_action_button("plot_spectra", "Plot two spectra before and after preprocessing transformations.", style="font-size:18px; padding:20px 40px; width:550px; height:100px; margin-top:10px; margin-right:50px"),
                ui.input_action_button("run_spec_lib_matching", "Run spectral library matching to perform compound identification on a query library of spectra.", style="font-size:18px; padding:20px 40px; width:550px; height:100px; margin-top:10px; margin-right:50px"),
                ui.input_action_button("run_parameter_tuning", "Tune parameters to maximize accuracy of compound identification given a query library with known spectrum IDs.", style="font-size:18px; padding:20px 40px; width:450px; height:120px; margin-top:10px; margin-right:50px"),
                ui.div(
                    "References:",
                    style="margin-top:35px; text-align:left; font-size:24px; font-weight:bold"
                ),
                ui.div(
                    "If Shannon Entropy similarity measure, low-entropy transformation, or centroiding are used:",
                    style="margin-top:10px; text-align:left; font-size:14px; font-weight:500"
                ),
                ui.div(
                    ui.HTML(
                        'Li, Y., Kind, T., Folz, J. et al. (2021) Spectral entropy outperforms MS/MS dot product similarity for small-molecule compound identification. Nat Methods, 18 1524–1531. <a href="https://doi.org/10.1038/s41592-021-01331-z" target="_blank">https://doi.org/10.1038/s41592-021-01331-z</a>.'
                    ),
                    style="text-align:left; font-size:14px; font-weight:500"
                ),
                ui.div(
                    "If Tsallis Entropy similarity measure or series of preprocessing transformations are used:",
                    style="margin-top:10px; text-align:left; font-size:14px; font-weight:500"
                ),
                ui.div(
                    ui.HTML(
                        'Dlugas, H., Zhang, X., Kim, S. (2025) Comparative analysis of continuous similarity measures for compound identification in mass spectrometry-based metabolomics. Chemometrics and Intelligent Laboratory Systems, 263, 105417. <a href="https://doi.org/10.1016/j.chemolab.2025.105417", target="_blank">https://doi.org/10.1016/j.chemolab.2025.105417</a>.'
                    ),
                    style="text-align:left; font-size:14px; font-weight:500"
                ),
                ui.div(
                    "If binary similarity measures are used:",
                    style="margin-top:10px; text-align:left; font-size:14px; font-weight:500"
                ),
                ui.div(
                    ui.HTML(
                        'Kim, S., Kato, I., & Zhang, X. (2022). Comparative Analysis of Binary Similarity Measures for Compound Identification in Mass Spectrometry-Based Metabolomics. Metabolites, 12(8), 694. <a href="https://doi.org/10.3390/metabo12080694" target="_blank">https://doi.org/10.3390/metabo12080694</a>.'
                    ),
                    style="text-align:left; font-size:14px; font-weight:500"
                ),

                ui.div(
                    "If weight factor transformation is used:",
                    style="margin-top:10px; text-align:left; font-size:14px; font-weight:500"
                ),
                ui.div(
                    ui.HTML(
                        'Kim, S., Koo, I., Wei, X., & Zhang, X. (2012). A method of finding optimal weight factors for compound identification in gas chromatography-mass spectrometry. Bioinformatics, 28(8), 1158-1163. <a href="https://doi.org/10.1093/bioinformatics/bts083" target="_blank">https://doi.org/10.1093/bioinformatics/bts083</a>.'
                    ),
                    style="margin-bottom:40px; text-align:left; font-size:14px; font-weight:500"
                ),
            )
        elif current_page() == "plot_spectra":
            return plot_spectra_ui(input.chromatography_platform())
        elif current_page() == "run_spec_lib_matching":
            return run_spec_lib_matching_ui(input.chromatography_platform())
        elif current_page() == "run_parameter_tuning":
            return run_parameter_tuning_ui(input.chromatography_platform())



    @reactive.effect
    @reactive.event(input.query_data)
    async def _populate_ids_from_query_upload():
        #if current_page() != "plot_spectra":
        #    return

        files = input.query_data()
        if not files:
            return

        in_path = Path(files[0]["datapath"])
        suffix = in_path.suffix.lower()

        # Decide what CSV to read IDs from
        try:
            if suffix == ".csv":
                csv_path = in_path
                converted_query_path_rv.set(str(csv_path))
            else:
                query_status_rv.set(f"Converting {in_path.name} → CSV …")
                await reactive.flush()

                # Choose an output temp path next to the upload
                tmp_csv_path = in_path.with_suffix(".converted.csv")

                out_obj = await asyncio.to_thread(build_library, str(in_path), str(tmp_csv_path))

                # out_obj may be a path (str/PathLike) OR a DataFrame. Normalize to a path.
                if isinstance(out_obj, (str, os.PathLike, Path)):
                    csv_path = Path(out_obj)
                elif isinstance(out_obj, pd.DataFrame):
                    # Write the DF to our chosen path
                    out_obj.to_csv(tmp_csv_path, index=False)
                    csv_path = tmp_csv_path
                else:
                    raise TypeError(f"build_library returned unsupported type: {type(out_obj)}")

                converted_query_path_rv.set(str(csv_path))

            query_status_rv.set(f"Reading IDs from: {csv_path.name} …")
            await reactive.flush()

            # Extract IDs from the CSV’s first column
            ids = await asyncio.to_thread(extract_first_column_ids, str(csv_path))
            query_ids_rv.set(ids)

            # Update dropdowns
            ui.update_selectize("spectrum_ID1", choices=ids, selected=(ids[0] if ids else None))

            query_status_rv.set(
                f"✅ Loaded {len(ids)} IDs from {csv_path.name}" if ids else f"⚠️ No IDs found in {csv_path.name}"
            )
            await reactive.flush()

        except Exception as e:
            query_status_rv.set(f"❌ Failed: {e}")
            await reactive.flush()
            raise


    @reactive.effect
    @reactive.event(input.reference_data)
    async def _populate_ids_from_reference_upload():
        #if current_page() != "plot_spectra":
        #    return

        files = input.reference_data()
        if not files:
            return

        in_path = Path(files[0]["datapath"])
        suffix = in_path.suffix.lower()

        # Decide what CSV to read IDs from
        try:
            if suffix == ".csv":
                csv_path = in_path
                converted_reference_path_rv.set(str(csv_path))
            else:
                reference_status_rv.set(f"Converting {in_path.name} → CSV …")
                await reactive.flush()

                # Choose an output temp path next to the upload
                tmp_csv_path = in_path.with_suffix(".converted.csv")

                out_obj = await asyncio.to_thread(build_library, str(in_path), str(tmp_csv_path))

                # out_obj may be a path (str/PathLike) OR a DataFrame. Normalize to a path.
                if isinstance(out_obj, (str, os.PathLike, Path)):
                    csv_path = Path(out_obj)
                elif isinstance(out_obj, pd.DataFrame):
                    # Write the DF to our chosen path
                    out_obj.to_csv(tmp_csv_path, index=False)
                    csv_path = tmp_csv_path
                else:
                    raise TypeError(f"build_library returned unsupported type: {type(out_obj)}")

                converted_reference_path_rv.set(str(csv_path))

            reference_status_rv.set(f"Reading IDs from: {csv_path.name} …")
            await reactive.flush()

            # Extract IDs from the CSV’s first column
            ids = await asyncio.to_thread(extract_first_column_ids, str(csv_path))
            reference_ids_rv.set(ids)

            # Update dropdowns
            ui.update_selectize("spectrum_ID2", choices=ids, selected=(ids[0] if ids else None))

            reference_status_rv.set(
                f"✅ Loaded {len(ids)} IDs from {csv_path.name}" if ids else f"⚠️ No IDs found in {csv_path.name}"
            )
            await reactive.flush()

        except Exception as e:
            reference_status_rv.set(f"❌ Failed: {e}")
            await reactive.flush()
            raise


    @render.download(filename=lambda: f"plot.png")
    def run_btn_plot_spectra():
        spectrum_ID1 = input.spectrum_ID1() or None
        spectrum_ID2 = input.spectrum_ID2() or None

        weights = [float(weight.strip()) for weight in input.weights().split(",") if weight.strip()]
        weights = {'Cosine':weights[0], 'Shannon':weights[1], 'Renyi':weights[2], 'Tsallis':weights[3]}

        if input.chromatography_platform() == "HRMS":
            fig = generate_plots_on_HRMS_data(query_data=input.query_data()[0]['datapath'], reference_data=input.reference_data()[0]['datapath'], spectrum_ID1=spectrum_ID1, spectrum_ID2=spectrum_ID2, similarity_measure=input.similarity_measure(), weights=weights, spectrum_preprocessing_order=input.spectrum_preprocessing_order(), high_quality_reference_library=input.high_quality_reference_library(), mz_min=input.mz_min(), mz_max=input.mz_max(), int_min=input.int_min(), int_max=input.int_max(), window_size_centroiding=input.window_size_centroiding(), window_size_matching=input.window_size_matching(), noise_threshold=input.noise_threshold(), wf_mz=input.wf_mz(), wf_intensity=input.wf_int(), LET_threshold=input.LET_threshold(), entropy_dimension=input.entropy_dimension(), y_axis_transformation=input.y_axis_transformation(), return_plot=True)
            plt.show()
        elif input.chromatography_platform() == "NRMS":
            fig = generate_plots_on_NRMS_data(query_data=input.query_data()[0]['datapath'], reference_data=input.reference_data()[0]['datapath'], spectrum_ID1=spectrum_ID1, spectrum_ID2=spectrum_ID2, similarity_measure=input.similarity_measure(), spectrum_preprocessing_order=input.spectrum_preprocessing_order(), high_quality_reference_library=input.high_quality_reference_library(), mz_min=input.mz_min(), mz_max=input.mz_max(), int_min=input.int_min(), int_max=input.int_max(), noise_threshold=input.noise_threshold(), wf_mz=input.wf_mz(), wf_intensity=input.wf_int(), LET_threshold=input.LET_threshold(), entropy_dimension=input.entropy_dimension(), y_axis_transformation=input.y_axis_transformation(), return_plot=True)
            plt.show()
        with io.BytesIO() as buf:
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            plt.close()
            yield buf.getvalue()


    @render.text
    def status_output():
        return run_status_plot_spectra.get()
        return run_status_spec_lib_matching.get()
        return run_status_parameter_tuning.get()


    class ReactiveWriter(io.TextIOBase):
        def __init__(self, rv: reactive.Value, loop: asyncio.AbstractEventLoop):
            self.rv = rv
            self.loop = loop

        def write(self, s: str):
            if not s:
                return 0
            def _apply():
                self.rv.set(self.rv.get() + s)
                self.loop.create_task(reactive.flush())
            self.loop.call_soon_threadsafe(_apply)
            return len(s)

        def flush(self):
            pass


    @render.download(filename="identification_output.csv")
    async def run_btn_spec_lib_matching():
        match_log_rv.set("Starting identification...\n")
        await reactive.flush()

        hq = input.high_quality_reference_library()
        if isinstance(hq, str):
            hq = hq.lower() == "true"
        elif isinstance(hq, (int, float)):
            hq = bool(hq)

        weights = [float(weight.strip()) for weight in input.weights().split(",") if weight.strip()]
        weights = {'Cosine':weights[0], 'Shannon':weights[1], 'Renyi':weights[2], 'Tsallis':weights[3]}

        common_kwargs = dict(
            query_data=input.query_data()[0]["datapath"],
            reference_data=input.reference_data()[0]["datapath"],
            likely_reference_ids=None,
            similarity_measure=input.similarity_measure(),
            weights=weights,
            spectrum_preprocessing_order=input.spectrum_preprocessing_order(),
            high_quality_reference_library=hq,
            mz_min=input.mz_min(), mz_max=input.mz_max(),
            int_min=input.int_min(), int_max=input.int_max(),
            noise_threshold=input.noise_threshold(),
            wf_mz=input.wf_mz(), wf_intensity=input.wf_int(),
            LET_threshold=input.LET_threshold(), entropy_dimension=input.entropy_dimension(),
            n_top_matches_to_save=input.n_top_matches_to_save(),
            print_id_results=True,  # ensure the library actually prints
            output_identification=str(Path.cwd() / "identification_output.csv"),
            output_similarity_scores=str(Path.cwd() / "similarity_scores.csv"),
            return_ID_output=True,
        )

        loop = asyncio.get_running_loop()
        rw = ReactiveWriter(match_log_rv, loop)

        try:
            with redirect_stdout(rw), redirect_stderr(rw):
                if input.chromatography_platform() == "HRMS":
                    df_out = await asyncio.to_thread(
                        run_spec_lib_matching_on_HRMS_data,
                        window_size_centroiding=input.window_size_centroiding(),
                        window_size_matching=input.window_size_matching(),
                        **common_kwargs
                    )
                else:
                    df_out = await asyncio.to_thread(run_spec_lib_matching_on_NRMS_data, **common_kwargs)
            match_log_rv.set(match_log_rv.get() + "\n✅ Identification finished.\n")
            await reactive.flush()
        except Exception as e:
            match_log_rv.set(match_log_rv.get() + f"\n❌ Error: {e}\n")
            await reactive.flush()
            raise

        yield df_out.to_csv(index=True)



    @render.download(filename="plot.png")
    def run_btn_plot_spectra_within_spec_lib_matching():
        req(input.query_data(), input.reference_data())

        spectrum_ID1 = input.spectrum_ID1() or None
        spectrum_ID2 = input.spectrum_ID2() or None

        hq = input.high_quality_reference_library()
        if isinstance(hq, str):
            hq = hq.lower() == "true"
        elif isinstance(hq, (int, float)):
            hq = bool(hq)

        weights = [float(weight.strip()) for weight in input.weights().split(",") if weight.strip()]
        weights = {'Cosine':weights[0], 'Shannon':weights[1], 'Renyi':weights[2], 'Tsallis':weights[3]}

        common = dict(
            query_data=input.query_data()[0]['datapath'],
            reference_data=input.reference_data()[0]['datapath'],
            spectrum_ID1=spectrum_ID1,
            spectrum_ID2=spectrum_ID2,
            similarity_measure=input.similarity_measure(),
            weights=weights,
            spectrum_preprocessing_order=input.spectrum_preprocessing_order(),
            high_quality_reference_library=hq,
            mz_min=input.mz_min(), mz_max=input.mz_max(),
            int_min=input.int_min(), int_max=input.int_max(),
            noise_threshold=input.noise_threshold(),
            wf_mz=input.wf_mz(), wf_intensity=input.wf_int(),
            LET_threshold=input.LET_threshold(), entropy_dimension=input.entropy_dimension(),
            y_axis_transformation="normalized",
            return_plot=True
        )

        if input.chromatography_platform() == "HRMS":
            fig = generate_plots_on_HRMS_data(
                window_size_centroiding=input.window_size_centroiding(),
                window_size_matching=input.window_size_matching(),
                **common
            )
            plt.show()
        else:
            fig = generate_plots_on_NRMS_data(**common)
            plt.show()

        with io.BytesIO() as buf:
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            plt.close()
            yield buf.getvalue()


    '''
    @render.download(filename="parameter_tuning_output.csv")
    async def run_btn_parameter_tuning():
        match_log_rv.set("Running grid search of all parameters specified...\n")

        similarity_measure_tmp = list(input.similarity_measure())
        high_quality_reference_library_tmp = [x.strip().lower() == "true" for x in input.high_quality_reference_library().strip().strip("[]").split(",") if x.strip()]
        spectrum_preprocessing_order_tmp = strip_text(input.spectrum_preprocessing_order())
        mz_min_tmp = strip_numeric(input.mz_min())
        mz_max_tmp = strip_numeric(input.mz_max())
        int_min_tmp = strip_numeric(input.int_min())
        int_max_tmp = strip_numeric(input.int_max())
        noise_threshold_tmp = strip_numeric(input.noise_threshold())
        wf_mz_tmp = strip_numeric(input.wf_mz())
        wf_int_tmp = strip_numeric(input.wf_int())
        LET_threshold_tmp = strip_numeric(input.LET_threshold())
        entropy_dimension_tmp = strip_numeric(input.entropy_dimension())
        weights_tmp = strip_weights(input.weights())

        common_kwargs = dict(
            query_data=input.query_data()[0]["datapath"],
            reference_data=input.reference_data()[0]["datapath"],
            output_path=str(Path.cwd() / "parameter_tuning_output.csv"),
            return_output=True
        )

        loop = asyncio.get_running_loop()
        rw = ReactiveWriter(match_log_rv, loop)

        try:
            with redirect_stdout(rw), redirect_stderr(rw):
                if input.chromatography_platform() == "HRMS":
                    window_size_centroiding_tmp = strip_numeric(input.window_size_centroiding())
                    window_size_matching_tmp = strip_numeric(input.window_size_matching())
                    grid={'similarity_measure':similarity_measure_tmp, 'weight':weights_tmp, 'spectrum_preprocessing_order':spectrum_preprocessing_order_tmp, 'mz_min':mz_min_tmp, 'mz_max':mz_max_tmp, 'int_min':int_min_tmp, 'int_max':int_max_tmp, 'noise_threshold':noise_threshold_tmp, 'wf_mz':wf_mz_tmp, 'wf_int':wf_int_tmp, 'LET_threshold':LET_threshold_tmp, 'entropy_dimension':entropy_dimension_tmp, 'high_quality_reference_library':high_quality_reference_library_tmp, 'window_size_centroiding':window_size_centroiding_tmp, 'window_size_matching':window_size_matching_tmp}
                    df_out = await asyncio.to_thread(tune_params_on_HRMS_data, **common_kwargs, grid=grid)
                else:
                    grid={'similarity_measure':similarity_measure_tmp, 'weight':weights_tmp, 'spectrum_preprocessing_order':spectrum_preprocessing_order_tmp, 'mz_min':mz_min_tmp, 'mz_max':mz_max_tmp, 'int_min':int_min_tmp, 'int_max':int_max_tmp, 'noise_threshold':noise_threshold_tmp, 'wf_mz':wf_mz_tmp, 'wf_int':wf_int_tmp, 'LET_threshold':LET_threshold_tmp, 'entropy_dimension':entropy_dimension_tmp, 'high_quality_reference_library':high_quality_reference_library_tmp}
                    df_out = await asyncio.to_thread(tune_params_on_NRMS_data, **common_kwargs, grid=grid)
            match_log_rv.set(match_log_rv.get() + "\n✅ Parameter tuning finished.\n")
            #await reactive.flush()
        except Exception as e:
            match_log_rv.set(match_log_rv.get() + f"\n❌ Error: {e}\n")
            #await reactive.flush()
            raise

        yield df_out.to_csv(index=False)
    '''


    @render.download(filename="parameter_tuning_output.csv")
    async def run_btn_parameter_tuning():
        is_any_job_running.set(True)
        is_tuning_running.set(True)
        match_log_rv.set("Running grid search of all parameters specified...\n")
        _drain_queue_nowait(_LOG_QUEUE) 

        similarity_measure_tmp = list(input.similarity_measure())
        high_quality_reference_library_tmp = [x.strip().lower() == "true" for x in input.high_quality_reference_library().strip().strip("[]").split(",") if x.strip()]
        spectrum_preprocessing_order_tmp = strip_text(input.spectrum_preprocessing_order())
        mz_min_tmp = strip_numeric(input.mz_min())
        mz_max_tmp = strip_numeric(input.mz_max())
        int_min_tmp = strip_numeric(input.int_min())
        int_max_tmp = strip_numeric(input.int_max())
        noise_threshold_tmp = strip_numeric(input.noise_threshold())
        wf_mz_tmp = strip_numeric(input.wf_mz())
        wf_int_tmp = strip_numeric(input.wf_int())
        LET_threshold_tmp = strip_numeric(input.LET_threshold())
        entropy_dimension_tmp = strip_numeric(input.entropy_dimension())
        weights_tmp = strip_weights(input.weights())

        common_kwargs = dict(
            query_data=input.query_data()[0]["datapath"],
            reference_data=input.reference_data()[0]["datapath"],
            output_path=str(Path.cwd() / "parameter_tuning_output.csv"),
            return_output=True
        )

        loop = asyncio.get_running_loop()
        rw = ReactiveWriter(match_log_rv,loop)

        try:
            with redirect_stdout(ReactiveWriter(match_log_rv, asyncio.get_running_loop())), redirect_stderr(ReactiveWriter(match_log_rv, asyncio.get_running_loop())):
                if input.chromatography_platform() == "HRMS":
                    window_size_centroiding_tmp = strip_numeric(input.window_size_centroiding())
                    window_size_matching_tmp = strip_numeric(input.window_size_matching())
                    grid={'similarity_measure':similarity_measure_tmp, 'weight':weights_tmp, 'spectrum_preprocessing_order':spectrum_preprocessing_order_tmp, 'mz_min':mz_min_tmp, 'mz_max':mz_max_tmp, 'int_min':int_min_tmp, 'int_max':int_max_tmp, 'noise_threshold':noise_threshold_tmp, 'wf_mz':wf_mz_tmp, 'wf_int':wf_int_tmp, 'LET_threshold':LET_threshold_tmp, 'entropy_dimension':entropy_dimension_tmp, 'high_quality_reference_library':high_quality_reference_library_tmp, 'window_size_centroiding':window_size_centroiding_tmp, 'window_size_matching':window_size_matching_tmp}
                    df_out = await asyncio.to_thread(tune_params_on_HRMS_data, **common_kwargs, grid=grid)
                else:
                    grid={'similarity_measure':similarity_measure_tmp, 'weight':weights_tmp, 'spectrum_preprocessing_order':spectrum_preprocessing_order_tmp, 'mz_min':mz_min_tmp, 'mz_max':mz_max_tmp, 'int_min':int_min_tmp, 'int_max':int_max_tmp, 'noise_threshold':noise_threshold_tmp, 'wf_mz':wf_mz_tmp, 'wf_int':wf_int_tmp, 'LET_threshold':LET_threshold_tmp, 'entropy_dimension':entropy_dimension_tmp, 'high_quality_reference_library':high_quality_reference_library_tmp}
                    df_out = await asyncio.to_thread(tune_params_on_NRMS_data, **common_kwargs, grid=grid)

            match_log_rv.set(match_log_rv.get() + "\n✅ Parameter tuning finished.\n")
        except Exception as e:
            match_log_rv.set(match_log_rv.get() + f"\n❌ Error: {e}\n")
            raise
        finally:
            is_tuning_running.set(False)
            is_any_job_running.set(False)
            trailing = _drain_queue_nowait(_LOG_QUEUE)
            if trailing:
                match_log_rv.set(match_log_rv.get() + "".join(trailing))
            await reactive.flush()

        #yield df_out.to_csv(index=False)
        csv_bytes = df_out.to_csv(index=False).encode('utf-8')
        yield csv_bytes



    @render.text
    def status_output():
        return run_status_plot_spectra.get()
        return run_status_spec_lib_matching.get()
        return run_status_parameter_tuning.get()


    class ReactiveWriter(io.TextIOBase):
        def __init__(self, rv: reactive.Value, loop: asyncio.AbstractEventLoop):
            self._rv = rv
            self._loop = loop

        def write(self, s: str):
            if not s:
                return 0
            self._loop.call_soon_threadsafe(_LOG_QUEUE.put_nowait, s)
            return len(s)

        def flush(self):
            pass


    @reactive.effect
    async def _pump_reactive_writer_logs():
        if not is_tuning_running.get():
            return

        reactive.invalidate_later(0.1)
        msgs = _drain_queue_nowait(_LOG_QUEUE)
        if msgs:
            match_log_rv.set(match_log_rv.get() + "".join(msgs))
            await reactive.flush()



    @render.text
    def status_output():
        return run_status_plot_spectra.get()
        return run_status_spec_lib_matching.get()
        return run_status_parameter_tuning.get()



app = App(app_ui, server)


