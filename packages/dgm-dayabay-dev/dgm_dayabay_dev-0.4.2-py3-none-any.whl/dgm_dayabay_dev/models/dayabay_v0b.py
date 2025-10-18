from collections.abc import Collection, Mapping, Sequence
from contextlib import suppress
from itertools import product
from os.path import relpath
from pathlib import Path
from typing import Any, Literal

from numpy import ndarray
from numpy.random import Generator

from dag_modelling.bundles.file_reader import FileReader
from dag_modelling.bundles.load_array import load_array
from dag_modelling.bundles.load_graph import load_graph, load_graph_data
from dag_modelling.bundles.load_parameters import load_parameters
from dag_modelling.core import Graph, NodeStorage
from dag_modelling.lib.arithmetic import Division, Product, Sum
from dag_modelling.lib.interpolation import Interpolator
from dag_modelling.tools.logger import logger
from dag_modelling.tools.schema import LoadYaml
from nested_mapping import NestedMapping


Features = {
    "all",
    "pdg",
    "xsec",
    "conversion",
    "hm-spectra",
    "hm-preinterpolate",
    "fix-neq-shape",
    "lsnl-curves",
    "lsnl-matrix",
    "short-baselines",
}

_SYSTEMATIC_UNCERTAINTIES_GROUPS = {
    "oscprob": "oscprob",
    "eres": "detector.eres",
    "lsnl": "detector.lsnl_scale_a",
    "iav": "detector.iav_offdiag_scale_factor",
    "detector_relative": "detector.detector_relative",
    "energy_per_fission": "reactor.energy_per_fission",
    "nominal_thermal_power": "reactor.nominal_thermal_power",
    "snf": "reactor.snf_scale",
    "neq": "reactor.nonequilibrium_scale",
    "fission_fraction": "reactor.fission_fraction_scale",
    "bkg_rate": "bkg.rate",
    "hm_corr": "reactor_anue.spectrum_uncertainty.corr",
    "hm_uncorr": "reactor_anue.spectrum_uncertainty.uncorr",
}


class model_dayabay_v0b:
    __slots__ = (
        "storage",
        "graph",
        "inactive_detectors",
        "index",
        "combinations",
        "_override_indices",
        "_path_data",
        "_source_type",
        "_strict",
        "_close",
        "_spectrum_correction_mode",
        "_anue_spectrum_model",
        "_future",
        "_covmatrix_kwargs",
        "_covariance_matrix",
        "_frozen_nodes",
        "_concatenation_mode",
        "_monte_carlo_mode",
        "_random_generator",
    )

    storage: NodeStorage
    graph: Graph | None
    inactive_detectors: tuple[set[str], ...]
    index: dict[str, tuple[str, ...]]
    combinations: dict[str, tuple[tuple[str, ...], ...]]
    _path_data: Path
    _override_indices: Mapping[str, Sequence[str]]
    _source_type: Literal["tsv", "hdf5", "root", "npz"]
    _strict: bool
    _close: bool
    _spectrum_correction_mode: Literal["linear", "exponential"]
    _anue_spectrum_model: str | None
    _future: set[
        Literal[
            "all", "pdg", "xsec", "conversion", "hm-spectra",
            "hm-preinterpolate", "fix-neq-shape", "lsnl-curves",
            "lsnl-matrix", "short-baselines"
        ]
    ]
    _concatenation_mode: Literal["detector", "detector_period"]
    _monte_carlo_mode: Literal[
        "asimov", "normal", "normal-stats", "poisson", "covariance"
    ]
    _random_generator: Generator
    _covmatrix_kwargs: dict
    _covariance_matrix: Any
    _frozen_nodes: dict[str, tuple]

    def __init__(
        self,
        *,
        source_type: Literal["tsv", "hdf5", "root", "npz"] = "npz",
        strict: bool = True,
        close: bool = True,
        override_indices: Mapping[str, Sequence[str]] = {},
        spectrum_correction_mode: Literal["linear", "exponential"] = "exponential",
        anue_spectrum_model: str | None = None,
        covmatrix_kwargs: Mapping = {},
        seed: int = 0,
        monte_carlo_mode: Literal[
            "asimov", "normal", "normal-stats", "poisson", "covariance"
        ] = "asimov",
        concatenation_mode: Literal["detector", "detector_period"] = "detector_period",
        merge_integration: bool = False,
        parameter_values: dict[str, float | str] = {},
        path_data: str | Path = "data/dayabay-v0b",
        future: Collection[
            Literal[
                "all", "pdg", "xsec", "conversion", "hm-spectra",
                "hm-preinterpolate", "fix-neq-shape", "lsnl-curves",
                "lsnl-matrix", "short-baselines"
            ]
        ] | Literal[
            "all", "pdg", "xsec", "conversion", "hm-spectra",
            "hm-preinterpolate", "fix-neq-shape", "lsnl-curves",
            "lsnl-matrix", "short-baselines"
        ] = (),
    ):
        self._strict = strict
        self._close = close

        self.graph = None
        self.storage = NodeStorage()
        self._path_data = Path(path_data)
        self._source_type = source_type
        self._override_indices = override_indices
        self._spectrum_correction_mode = spectrum_correction_mode
        self._anue_spectrum_model = anue_spectrum_model
        self._covmatrix_kwargs = dict(covmatrix_kwargs)
        self._concatenation_mode = concatenation_mode
        self._monte_carlo_mode = monte_carlo_mode
        self._random_generator = self._create_random_generator(seed)

        self._future = set((future,)) if isinstance(future, str) else set(future)
        assert all(f in Features for f in self._future)
        if "all" in self._future:
            self._future = set(Features)
            self._future.remove("all")
        if self._future:
            logger.info(f"Future options: {', '.join(self._future)}")

        if "hm-spectra" in self._future and self._anue_spectrum_model is None:
            logger.warning("Future: HM properly interpolated to 50 keV")
            self._anue_spectrum_model = "50keV_scaled_approx"

        self._covariance_matrix = None
        self._frozen_nodes = {}

        self.inactive_detectors = ({"6AD", "AD22"}, {"6AD", "AD34"}, {"7AD", "AD11"})
        self.index = {}
        self.combinations = {}

        self.build()

        if parameter_values:
            self.set_parameters(parameter_values)

    def build(self):
        storage = self.storage
        path_data = self._path_data

        path_parameters = path_data / "parameters"
        path_arrays = path_data / self._source_type
        path_root = path_data / "root"

        from dag_modelling.tools.schema import LoadPy

        antineutrino_model_edges = LoadPy(
            path_parameters / "reactor_antineutrino_spectrum_edges.py",
            variable="edges",
            type=ndarray,
        )

        index_names = {
            "U235": "²³⁵U",
            "U238": "²³⁸U",
            "Pu239": "²³⁹Pu",
            "Pu241": "²⁴¹Pu",
        }

        # Provide a list of indices and their values. Values should be globally unique
        index = self.index
        index["isotope"] = ("U235", "U238", "Pu239", "Pu241")
        index["isotope_lower"] = tuple(i.lower() for i in index["isotope"])
        index["isotope_neq"] = ("U235", "Pu239", "Pu241")
        index["detector"] = (
            "AD11",
            "AD12",
            "AD21",
            "AD22",
            "AD31",
            "AD32",
            "AD33",
            "AD34",
        )
        index["site"] = ("EH1", "EH2", "EH3")
        index["reactor"] = ("DB1", "DB2", "LA1", "LA2", "LA3", "LA4")
        index["anue_source"] = ("nu_main", "nu_neq", "nu_snf")
        index["anue_unc"] = ("uncorr", "corr")
        index["period"] = ("6AD", "8AD", "7AD")
        index["lsnl"] = ("nominal", "pull0", "pull1", "pull2", "pull3")
        index["lsnl_nuisance"] = ("pull0", "pull1", "pull2", "pull3")
        # index["bkg"] = ('acc', 'lihe', 'fastn', 'amc', 'alphan', 'muon')
        index["bkg"] = ("acc", "lihe", "fastn", "amc", "alphan")
        index["spec"] = tuple(
            f"spec_scale_{i:02d}" for i in range(len(antineutrino_model_edges))
        )

        index.update(self._override_indices)

        index_all = (
            index["isotope"] + index["detector"] + index["reactor"] + index["period"]
        )
        set_all = set(index_all)
        if len(index_all) != len(set_all):
            raise RuntimeError("Repeated indices")

        required_combinations = tuple(index.keys()) + (
            "reactor.detector",
            "reactor.isotope",
            "reactor.isotope_neq",
            "reactor.period",
            "reactor.isotope.period",
            "reactor.isotope.detector",
            "reactor.isotope_neq.detector",
            "reactor.isotope.detector.period",
            "reactor.isotope_neq.detector.period",
            "reactor.detector.period",
            "detector.period",
            "anue_unc.isotope",
            "bkg.detector",
            "bkg.detector.period",
        )
        # Provide the combinations of indices
        combinations = self.combinations
        for combname in required_combinations:
            combitems = combname.split(".")
            items = []
            for it in product(*(index[item] for item in combitems)):
                if any(inact.issubset(it) for inact in self.inactive_detectors):
                    continue
                items.append(it)
            combinations[combname] = tuple(items)

        combinations["anue_source.reactor.isotope.detector"] = (
            tuple(
                ("nu_main",) + cmb for cmb in combinations["reactor.isotope.detector"]
            )
            + tuple(
                ("nu_neq",) + cmb
                for cmb in combinations["reactor.isotope_neq.detector"]
            )
            + tuple(("nu_snf",) + cmb for cmb in combinations["reactor.detector"])
        )

        with (
            Graph(close_on_exit=self._close, strict=self._strict) as graph,
            storage,
            FileReader,
        ):
            # fmt: off
            self.graph = graph
            #
            # Load parameters
            #
            load_parameters(path="oscprob",    load=path_parameters/"oscprob.yaml")
            load_parameters(path="oscprob",    load=path_parameters/"oscprob_solar.yaml", joint_nuisance=True)
            load_parameters(path="oscprob",    load=path_parameters/"oscprob_constants.yaml"
            )

            if "pdg" in self._future:
                logger.warning("Future: latest PDG particle constants")
                load_parameters(path="ibd",        load=path_parameters/"pdg2024.yaml")
            else:
                load_parameters(path="ibd",        load=path_parameters/"pdg2012.yaml")

            if "xsec" in self._future:
                logger.warning("Future: latest IBD constants")
                load_parameters(path="ibd.csc",    load=path_parameters/"ibd_constants_future.yaml")
            else:
                load_parameters(path="ibd.csc",    load=path_parameters/"ibd_constants.yaml")

            if "conversion" in self._future:
                logger.warning("Future: latest conversion constants")
                load_parameters(path="conversion", load=path_parameters/"conversion_thermal_power_future.py")
                load_parameters(path="conversion", load=path_parameters/"conversion_oscprob_argument_future.py")
            else:
                load_parameters(path="conversion", load=path_parameters/"conversion_thermal_power.yaml")
                load_parameters(path="conversion", load=path_parameters/"conversion_oscprob_argument.yaml")

            if "short-baselines" in self._future:
                logger.warning("Future: truncated baselines")
                load_parameters(                   load=path_parameters/"baselines_short.yaml")
            else:
                load_parameters(                   load=path_parameters/"baselines_precise.yaml")

            load_parameters(path="detector",   load=path_parameters/"detector_efficiency.yaml")
            load_parameters(path="detector",   load=path_parameters/"detector_normalization.yaml")
            load_parameters(path="detector",   load=path_parameters/"detector_nprotons_correction.yaml")
            load_parameters(path="detector",   load=path_parameters/"detector_eres.yaml")
            load_parameters(path="detector",   load=path_parameters/"detector_lsnl.yaml",
                            replicate=index["lsnl_nuisance"])
            load_parameters(path="detector",   load=path_parameters/"detector_iav_offdiag_scale.yaml",
                            replicate=index["detector"])
            load_parameters(path="detector",   load=path_parameters/"detector_relative.yaml",
                            replicate=index["detector"],
                            keys_order = (("pargroup", "par", "detector"), ("pargroup", "detector", "par"))
                            )

            load_parameters(path="reactor",    load=path_parameters/"reactor_energy_per_fission.yaml")
            load_parameters(path="reactor",    load=path_parameters/"reactor_thermal_power_nominal.yaml",
                            replicate=index["reactor"])
            load_parameters(path="reactor",    load=path_parameters/"reactor_snf.yaml",
                            replicate=index["reactor"])
            load_parameters(path="reactor",    load=path_parameters/"reactor_nonequilibrium_correction.yaml",
                            replicate=combinations["reactor.isotope_neq"])
            load_parameters(path="reactor",    load=path_parameters/"reactor_snf_fission_fractions.yaml")
            load_parameters(path="reactor",    load=path_parameters/"reactor_fission_fraction_scale.yaml",
                            replicate=index["reactor"],
                            keys_order = (("par", "isotope", "reactor"), ("par", "reactor", "isotope"))
                            )

            load_parameters(path="bkg.rate",   load=path_parameters/"bkg_rate_acc.yaml")
            load_parameters(path="bkg.rate",   load=path_parameters/"bkg_rates.yaml")
            # fmt: on

            # Normalization constants
            load_parameters(
                format="value",
                state="fixed",
                parameters={
                    "conversion": {
                        "seconds_in_day_inverse": 1 / (60 * 60 * 24),
                    }
                },
                labels={
                    "conversion": {
                        "seconds_in_day_inverse": "Fraction of a day in a second",
                    }
                },
            )

            # Statistic constants for write-handed CNP
            load_parameters(
                format="value",
                state="fixed",
                parameters={
                    "stats": {
                        "pearson": 2 / 3,
                        "neyman": 1 / 3,
                    }
                },
                labels={
                    "stats": {
                        "pearson": "Pearson CNP coefficient",
                        "neyman": "Neyman CNP coefficient",
                    }
                },
            )

            nodes = storage.create_child("nodes")
            inputs = storage.create_child("inputs")
            outputs = storage.create_child("outputs")
            data = storage.create_child("data")
            parameters = storage("parameters")
            parameters_nuisance_normalized = storage("parameters.normalized")

            #
            # Create nodes
            #
            from numpy import arange, concatenate, linspace

            #
            # Define binning
            #
            in_edges_fine = linspace(0, 12, 241)
            in_edges_final = concatenate(([0.7], arange(1.2, 8.01, 0.20), [12.0]))
            in_edges_costheta = [-1, 1]

            from dag_modelling.lib.common import Array, View

            edges_costheta, _ = Array.replicate(
                name="edges.costheta", array=in_edges_costheta
            )
            edges_energy_common, _ = Array.replicate(
                name="edges.energy_common", array=in_edges_fine
            )
            edges_energy_final, _ = Array.replicate(
                name="edges.energy_final", array=in_edges_final
            )
            View.replicate(name="edges.energy_enu", output=edges_energy_common)
            edges_energy_edep, _ = View.replicate(
                name="edges.energy_edep", output=edges_energy_common
            )
            edges_energy_escint, _ = View.replicate(
                name="edges.energy_escint", output=edges_energy_common
            )
            edges_energy_evis, _ = View.replicate(
                name="edges.energy_evis", output=edges_energy_common
            )
            edges_energy_erec, _ = View.replicate(
                name="edges.energy_erec", output=edges_energy_common
            )

            Array.replicate(
                name="reactor_anue.spectrum_free_correction.spec_model_edges",
                array=antineutrino_model_edges,
            )

            #
            # Integration, kinematics
            #
            Array.from_value(
                "kinematics.integration.orders_x",
                5,
                edges=edges_energy_edep,
                store=True,
            )
            Array.from_value(
                "kinematics.integration.orders_y", 3, edges=edges_costheta, store=True
            )

            from dag_modelling.lib.integration import Integrator

            integrator, _ = Integrator.replicate(
                "gl2d",
                path="kinematics",
                names={
                    "sampler": "sampler",
                    "integrator": "integral",
                    "mesh_x": "sampler.mesh_edep",
                    "mesh_y": "sampler.mesh_costheta",
                },
                replicate_outputs=combinations["anue_source.reactor.isotope.detector"],
            )
            outputs.get_value("kinematics.integration.orders_x") >> integrator(
                "orders_x"
            )
            outputs.get_value("kinematics.integration.orders_y") >> integrator(
                "orders_y"
            )

            from dgm_reactor_neutrino import IBDXsecVBO1Group

            ibd, _ = IBDXsecVBO1Group.replicate(
                path="kinematics.ibd", input_energy="edep"
            )
            ibd << storage("parameters.constant.ibd")
            ibd << storage("parameters.constant.ibd.csc")
            outputs.get_value("kinematics.sampler.mesh_edep") >> ibd.inputs["edep"]
            (
                outputs.get_value("kinematics.sampler.mesh_costheta")
                >> ibd.inputs["costheta"]
            )
            kinematic_integrator_enu = ibd.outputs["enu"]

            # fmt: off
            #
            # Oscillations
            #
            from dgm_reactor_neutrino import NueSurvivalProbability
            NueSurvivalProbability.replicate(
                name="oscprob",
                distance_unit="m",
                leading_mass_splitting_3l_name="DeltaMSq32",
                replicate_outputs=combinations["reactor.detector"],
                surprobArgConversion = True
            )
            kinematic_integrator_enu >> inputs("oscprob.enu")
            parameters("constant.baseline") >> inputs("oscprob.L")
            parameters.get_value("all.conversion.oscprobArgConversion") >> inputs("oscprob.surprobArgConversion")
            nodes("oscprob") << parameters("free.oscprob")
            nodes("oscprob") << parameters("constrained.oscprob")
            nodes("oscprob") << parameters("constant.oscprob")

            #
            # Antineutrino spectrum configuration
            #
            anue_cfg = LoadYaml(path_data / "reactor_anue_spectrum_models.yaml")
            anue_modelname = self._anue_spectrum_model or anue_cfg["default"]
            try:
                filename_anue_spectrum, filename_anue_spectrum_unc = anue_cfg["models"][anue_modelname]
            except KeyError:
                raise RuntimeError(f"Unable to load anue model {anue_modelname}. Available models: {', '.join(anue_cfg['models'].keys())}")

            #
            # Nominal antineutrino spectrum
            #
            load_graph(
                name = "reactor_anue.neutrino_per_fission_per_MeV_input",
                filenames = path_arrays / f"{filename_anue_spectrum}.{self._source_type}",
                x = "enu",
                y = "spec",
                merge_x = True,
                replicate_outputs = index["isotope"],
            )

            #
            # Interpolate for the integration mesh
            #
            Interpolator.replicate(
                method = "exp",
                names = {
                    "indexer": "reactor_anue.spec_indexer",
                    "interpolator": "reactor_anue.neutrino_per_fission_per_MeV_nominal",
                    },
                replicate_outputs = index["isotope"],
            )

            if "hm-preinterpolate" in self._future:
                logger.warning("Future: do not pre-interpolate HM model to coarser grid")
                outputs.get_value("reactor_anue.neutrino_per_fission_per_MeV_input.enu") >> inputs.get_value("reactor_anue.neutrino_per_fission_per_MeV_nominal.xcoarse")
                outputs("reactor_anue.neutrino_per_fission_per_MeV_input.spec") >> inputs("reactor_anue.neutrino_per_fission_per_MeV_nominal.ycoarse")
            else:
                # Pre-interpolate input spectrum on coarser grid
                # NOTE:
                #     - not needed with the current scheme:
                #         - spectrum correction applied by multiplication
                #     - introduced for the consistency with GNA
                #     - to be removed in v1 TODO
                #
                Interpolator.replicate(
                    method = "exp",
                    names = {
                        "indexer": "reactor_anue.spec_indexer_pre",
                        "interpolator": "reactor_anue.neutrino_per_fission_per_MeV_nominal_pre",
                        },
                    replicate_outputs = index["isotope"],
                )
                outputs.get_value("reactor_anue.neutrino_per_fission_per_MeV_input.enu") >> inputs.get_value("reactor_anue.neutrino_per_fission_per_MeV_nominal_pre.xcoarse")
                outputs("reactor_anue.neutrino_per_fission_per_MeV_input.spec") >> inputs("reactor_anue.neutrino_per_fission_per_MeV_nominal_pre.ycoarse")
                outputs.get_value("reactor_anue.spectrum_free_correction.spec_model_edges") >> inputs.get_value("reactor_anue.neutrino_per_fission_per_MeV_nominal_pre.xfine")

                outputs.get_value("reactor_anue.spectrum_free_correction.spec_model_edges") >> inputs.get_value("reactor_anue.neutrino_per_fission_per_MeV_nominal.xcoarse")
                outputs("reactor_anue.neutrino_per_fission_per_MeV_nominal_pre") >> inputs("reactor_anue.neutrino_per_fission_per_MeV_nominal.ycoarse")

            kinematic_integrator_enu >> inputs.get_value("reactor_anue.neutrino_per_fission_per_MeV_nominal.xfine")

            #
            # SNF and NEQ normalization factors
            #
            load_parameters(
                format="value",
                state="fixed",
                parameters={
                    "reactor": {
                        "snf_factor": 1.0,
                        "neq_factor": 1.0,
                    }
                },
                labels={
                    "reactor": {
                        "snf_factor": "Common Spent Nuclear Fuel (SNF) factor",
                        "neq_factor": "Common Non-EQuilibrium (NEQ) factor",
                    }
                },
            )

            #
            # Non-EQuilibrium correction
            #
            load_graph(
                name = "reactor_nonequilibrium_anue.correction_input",
                x = "enu",
                y = "nonequilibrium_correction",
                merge_x = True,
                filenames = path_arrays / f"nonequilibrium_correction.{self._source_type}",
                replicate_outputs = index["isotope_neq"],
                dtype = "d"
            )

            Interpolator.replicate(
                method = "linear",
                names = {
                    "indexer": "reactor_nonequilibrium_anue.correction_indexer",
                    "interpolator": "reactor_nonequilibrium_anue.correction_interpolated",
                    },
                replicate_outputs = index["isotope_neq"],
                underflow = "constant",
                overflow = "constant",
            )
            outputs.get_value("reactor_nonequilibrium_anue.correction_input.enu") >> inputs.get_value("reactor_nonequilibrium_anue.correction_interpolated.xcoarse")
            outputs("reactor_nonequilibrium_anue.correction_input.nonequilibrium_correction") >> inputs("reactor_nonequilibrium_anue.correction_interpolated.ycoarse")
            kinematic_integrator_enu >> inputs.get_value("reactor_nonequilibrium_anue.correction_interpolated.xfine")

            #
            # SNF correction
            #
            load_graph(
                name = "snf_anue.correction_input",
                x = "enu",
                y = "snf_correction",
                merge_x = True,
                filenames = path_arrays / f"snf_correction.{self._source_type}",
                replicate_outputs = index["reactor"],
                dtype = "d"
            )
            Interpolator.replicate(
                method = "linear",
                names = {
                    "indexer": "snf_anue.correction_indexer",
                    "interpolator": "snf_anue.correction_interpolated",
                    },
                replicate_outputs = index["reactor"],
                underflow = "constant",
                overflow = "constant",
            )
            outputs.get_value("snf_anue.correction_input.enu") >> inputs.get_value("snf_anue.correction_interpolated.xcoarse")
            outputs("snf_anue.correction_input.snf_correction") >> inputs("snf_anue.correction_interpolated.ycoarse")
            kinematic_integrator_enu >> inputs.get_value("snf_anue.correction_interpolated.xfine")

            #
            # Reactor antineutrino spectral correction:
            #   - not constrained
            #   - correlated between isotopes
            #   - uncorrelated between energy intervals
            #
            from dag_modelling.bundles.make_y_parameters_for_x import \
                make_y_parameters_for_x
            make_y_parameters_for_x(
                    outputs.get_value("reactor_anue.spectrum_free_correction.spec_model_edges"),
                    namefmt = "spec_scale_{:02d}",
                    format = "value",
                    state = "variable",
                    key = "neutrino_per_fission_factor",
                    values = 0.0,
                    labels = "Edge {i:02d} ({value:.2f} MeV) reactor antineutrino spectrum correction" \
                           + (" (exp)" if self._spectrum_correction_mode == "exponential" else " (linear)"),
                    hide_nodes = True
                    )

            from dag_modelling.lib.common import Concatenation

            Concatenation.replicate(
                    parameters("all.neutrino_per_fission_factor"),
                    name = "reactor_anue.spectrum_free_correction.input"
                    )
            outputs.get_value("reactor_anue.spectrum_free_correction.input").dd.axes_meshes = (outputs.get_value("reactor_anue.spectrum_free_correction.spec_model_edges"),)
            if self._spectrum_correction_mode == "exponential":
                from dag_modelling.lib.exponential import Exp
                Exp.replicate(
                        outputs.get_value("reactor_anue.spectrum_free_correction.input"),
                        name = "reactor_anue.spectrum_free_correction.correction"
                        )
            else:
                Array.from_value("reactor_anue.spectrum_free_correction.unity", 1.0, dtype="d", mark="1", label="Array of 1 element =1", shape=1, store=True)
                Sum.replicate(
                        outputs.get_value("reactor_anue.spectrum_free_correction.unity"),
                        outputs.get_value("reactor_anue.spectrum_free_correction.input"),
                        name = "reactor_anue.spectrum_free_correction.correction"
                        )
                outputs.get_value("reactor_anue.spectrum_free_correction.correction").dd.axes_meshes = (outputs.get_value("reactor_anue.spectrum_free_correction.spec_model_edges"),)

            Interpolator.replicate(
                method = "exp",
                names = {
                    "indexer": "reactor_anue.spectrum_free_correction.indexer",
                    "interpolator": "reactor_anue.spectrum_free_correction.interpolated"
                    },
            )
            outputs.get_value("reactor_anue.spectrum_free_correction.spec_model_edges") >> inputs.get_value("reactor_anue.spectrum_free_correction.interpolated.xcoarse")
            outputs.get_value("reactor_anue.spectrum_free_correction.correction") >> inputs.get_value("reactor_anue.spectrum_free_correction.interpolated.ycoarse")
            kinematic_integrator_enu >> inputs.get_value("reactor_anue.spectrum_free_correction.interpolated.xfine")

            #
            # Huber+Mueller spectrum shape uncertainties
            #   - constrained
            #   - two parts:
            #       - uncorrelated between isotopes and energy intervals
            #       - correlated between isotopes and energy intervals
            #
            load_graph(
                name = "reactor_anue.spectrum_uncertainty",
                filenames = path_arrays / f"{filename_anue_spectrum_unc}.{self._source_type}",
                x = "enu_centers",
                y = "uncertainty",
                merge_x = True,
                replicate_outputs = combinations["anue_unc.isotope"],
            )

            # In the case of constant (left) interpolation bin edges should be used
            # from dag_modelling.lib.MeshToEdges import MeshToEdges
            # MeshToEdges.replicate(name="reactor_anue.spectrum_uncertainty.enu")
            # outputs.get_value("reactor_anue.spectrum_uncertainty.enu_centers") >> inputs.get_value("reactor_anue.spectrum_uncertainty.enu")
            # nodes.get_value("reactor_anue.spectrum_uncertainty.enu").close()

            for isotope in index["isotope"]:
                make_y_parameters_for_x(
                        outputs.get_value("reactor_anue.spectrum_uncertainty.enu_centers"),
                        namefmt = "unc_scale_{:03d}",
                        format = ("value", "sigma_absolute"),
                        state = "variable",
                        key = f"reactor_anue.spectrum_uncertainty.uncorr.{isotope}",
                        values = (0.0, 1.0),
                        labels = f"Edge {{i:02d}} ({{value:.2f}} MeV) uncorrelated {index_names[isotope]} spectrum correction",
                        disable_last_one = False, # True for the constant interpolation, last edge is unused
                        hide_nodes = True
                        )

            load_parameters(
                    path = "reactor_anue.spectrum_uncertainty",
                    format=("value", "sigma_absolute"),
                    state="variable",
                    parameters={
                        "corr": (0.0, 1.0)
                        },
                    labels={
                        "corr": "Correlated ν̅ spectrum shape uncertainty"
                        },
                    joint_nuisance = False
                    )

            Concatenation.replicate(
                    parameters("constrained.reactor_anue.spectrum_uncertainty.uncorr"),
                    name = "reactor_anue.spectrum_uncertainty.scale.uncorr",
                    replicate_outputs = index["isotope"]
                    )

            Product.replicate(
                    outputs("reactor_anue.spectrum_uncertainty.scale.uncorr"),
                    outputs("reactor_anue.spectrum_uncertainty.uncertainty.uncorr"),
                    name = "reactor_anue.spectrum_uncertainty.correction.uncorr",
                    replicate_outputs = index["isotope"]
                    )

            Product.replicate(
                    parameters.get_value("constrained.reactor_anue.spectrum_uncertainty.corr"),
                    outputs("reactor_anue.spectrum_uncertainty.uncertainty.corr"),
                    name = "reactor_anue.spectrum_uncertainty.correction.corr",
                    replicate_outputs = index["isotope"]
                    )

            single_unity = Array("single_unity", [1.0], dtype="d", mark="1", label="Array of 1 element =1")
            Sum.replicate(
                    outputs("reactor_anue.spectrum_uncertainty.correction.uncorr"),
                    single_unity,
                    name = "reactor_anue.spectrum_uncertainty.correction.uncorr_factor",
                    replicate_outputs = index["isotope"]
                    )
            Sum.replicate(
                    outputs("reactor_anue.spectrum_uncertainty.correction.corr"),
                    single_unity,
                    name = "reactor_anue.spectrum_uncertainty.correction.corr_factor",
                    replicate_outputs = index["isotope"]
                    )

            Product.replicate(
                    outputs("reactor_anue.spectrum_uncertainty.correction.uncorr_factor"),
                    outputs("reactor_anue.spectrum_uncertainty.correction.corr_factor"),
                    name = "reactor_anue.spectrum_uncertainty.correction.full",
                    replicate_outputs = index["isotope"]
                    )

            Interpolator.replicate(
                method = "linear",
                names = {
                    "indexer": "reactor_anue.spectrum_uncertainty.correction_index",
                    "interpolator": "reactor_anue.spectrum_uncertainty.correction_interpolated"
                    },
                replicate_outputs=index["isotope"]
            )
            outputs.get_value("reactor_anue.spectrum_uncertainty.enu_centers") >> inputs.get_value("reactor_anue.spectrum_uncertainty.correction_interpolated.xcoarse")
            outputs("reactor_anue.spectrum_uncertainty.correction.full") >> inputs("reactor_anue.spectrum_uncertainty.correction_interpolated.ycoarse")
            kinematic_integrator_enu >> inputs.get_value("reactor_anue.spectrum_uncertainty.correction_interpolated.xfine")

            #
            # Antineutrino spectrum with corrections
            #
            Product.replicate(
                    outputs("reactor_anue.neutrino_per_fission_per_MeV_nominal"),
                    outputs.get_value("reactor_anue.spectrum_free_correction.interpolated"),
                    outputs("reactor_anue.spectrum_uncertainty.correction_interpolated"),
                    name = "reactor_anue.part.neutrino_per_fission_per_MeV_main",
                    replicate_outputs=index["isotope"],
                    )

            if "fix-neq-shape" in self._future:
                logger.warning("Future: HM uncertainties do not affect NEQ")
                Product.replicate(
                        outputs("reactor_anue.neutrino_per_fission_per_MeV_nominal"),
                        outputs("reactor_nonequilibrium_anue.correction_interpolated"),
                        name = "reactor_anue.part.neutrino_per_fission_per_MeV_neq_nominal",
                        allow_skip_inputs = True,
                        skippable_inputs_should_contain = ("U238",),
                        replicate_outputs=index["isotope_neq"],
                        )
            else:
                Product.replicate(
                        outputs("reactor_anue.neutrino_per_fission_per_MeV_nominal"),
                        outputs("reactor_nonequilibrium_anue.correction_interpolated"),
                        outputs("reactor_anue.spectrum_uncertainty.correction_interpolated"),
                        name = "reactor_anue.part.neutrino_per_fission_per_MeV_neq_nominal",
                        allow_skip_inputs = True,
                        skippable_inputs_should_contain = ("U238",),
                        replicate_outputs=index["isotope_neq"],
                        )

            #
            # Livetime
            #
            from dag_modelling.bundles.load_record import load_record_data
            load_record_data(
                name = "daily_data.detector_all",
                filenames = path_arrays/f"livetimes_Dubna_AdSimpleNL_all.{self._source_type}",
                replicate_outputs = index["detector"],
                name_function = lambda idx, _: f"EH{idx[-2]}AD{idx[-1]}",
                columns = ("day", "ndet", "livetime", "eff", "efflivetime"),
                skip = self.inactive_detectors
            )
            from ..bundles.refine_detector_data_v0ae import \
                refine_detector_data
            refine_detector_data(
                data("daily_data.detector_all"),
                data.create_child("daily_data.detector"),
                detectors = index["detector"]
            )

            load_record_data(
                name = "daily_data.reactor_all",
                filenames = path_arrays/f"weekly_power_fulldata_release_v2.{self._source_type}",
                replicate_outputs = ("core_data",),
                columns = ("week", "day", "ndet", "ndays", "core", "power") + index["isotope_lower"],
                output_key_order = (("week", "core_data"), ("week",))
            )
            from ..bundles.refine_reactor_data_v0ae import split_refine_reactor_data
            split_refine_reactor_data(
                data("daily_data.reactor_all"),
                data.create_child("daily_data.reactor"),
                reactors = index["reactor"],
                isotopes = index["isotope"],
            )

            from ..bundles.sync_reactor_detector_data import \
                sync_reactor_detector_data
            sync_reactor_detector_data(
                    data("daily_data.reactor"),
                    data("daily_data.detector"),
                    )

            Array.from_storage(
                "daily_data.detector.livetime",
                storage("data"),
                remove_processed_arrays = True,
                dtype = "d"
            )

            Array.from_storage(
                "daily_data.detector.eff",
                storage("data"),
                remove_processed_arrays = True,
                dtype = "d"
            )

            Array.from_storage(
                "daily_data.detector.efflivetime",
                storage("data"),
                remove_processed_arrays = True,
                dtype = "d"
            )

            Array.from_storage(
                "daily_data.reactor.power",
                storage("data"),
                remove_processed_arrays = True,
                dtype = "d"
            )

            Array.from_storage(
                "daily_data.reactor.fission_fraction",
                storage("data"),
                remove_processed_arrays = True,
                dtype = "d"
            )
            del storage["data.daily_data"]

            #
            # Neutrino rate
            #
            Product.replicate(
                    parameters("all.reactor.nominal_thermal_power"),
                    parameters.get_value("all.conversion.reactorPowerConversion"),
                    name = "reactor.thermal_power_nominal_MeVs",
                    replicate_outputs = index["reactor"]
                    )

            Product.replicate(
                    parameters("central.reactor.nominal_thermal_power"),
                    parameters.get_value("all.conversion.reactorPowerConversion"),
                    name = "reactor.thermal_power_nominal_MeVs_central",
                    replicate_outputs = index["reactor"]
                    )

            # Time dependent, fit dependent (non-nominal) for reactor core
            Product.replicate(
                    parameters("all.reactor.fission_fraction_scale"),
                    outputs("daily_data.reactor.fission_fraction"),
                    name = "daily_data.reactor.fission_fraction_scaled",
                    replicate_outputs=combinations["reactor.isotope.period"],
                    )

            Product.replicate(
                    parameters("all.reactor.energy_per_fission"),
                    outputs("daily_data.reactor.fission_fraction_scaled"),
                    name = "reactor.energy_per_fission_weighted_MeV",
                    replicate_outputs=combinations["reactor.isotope.period"],
                    )

            Sum.replicate(
                    outputs("reactor.energy_per_fission_weighted_MeV"),
                    name = "reactor.energy_per_fission_average_MeV",
                    replicate_outputs=combinations["reactor.period"],
                    )

            Product.replicate(
                    outputs("daily_data.reactor.power"),
                    outputs("daily_data.reactor.fission_fraction_scaled"),
                    outputs("reactor.thermal_power_nominal_MeVs"),
                    name = "reactor.thermal_power_isotope_MeV_per_second",
                    replicate_outputs=combinations["reactor.isotope.period"],
                    )

            Division.replicate(
                    outputs("reactor.thermal_power_isotope_MeV_per_second"),
                    outputs("reactor.energy_per_fission_average_MeV"),
                    name = "reactor.fissions_per_second",
                    replicate_outputs=combinations["reactor.isotope.period"],
                    )

            # Nominal, time and reactor independent power and fission fractions for SNF
            # NOTE: central values are used for energy_per_fission
            Product.replicate(
                    parameters("central.reactor.energy_per_fission"),
                    parameters("all.reactor.fission_fraction_snf"),
                    name = "reactor.energy_per_fission_snf_weighted_MeV",
                    replicate_outputs=index["isotope"],
                    )

            Sum.replicate(
                    outputs("reactor.energy_per_fission_snf_weighted_MeV"),
                    name = "reactor.energy_per_fission_snf_average_MeV",
                    )

            # NOTE: central values are used for the thermal power
            Product.replicate(
                    parameters("all.reactor.fission_fraction_snf"),
                    outputs("reactor.thermal_power_nominal_MeVs_central"),
                    name = "reactor.thermal_power_snf_isotope_MeV_per_second",
                    replicate_outputs=combinations["reactor.isotope"],
                    )

            Division.replicate(
                    outputs("reactor.thermal_power_snf_isotope_MeV_per_second"),
                    outputs.get_value("reactor.energy_per_fission_snf_average_MeV"),
                    name = "reactor.fissions_per_second_snf",
                    replicate_outputs=combinations["reactor.isotope"],
                    )

            # Effective number of fissions seen in Detector from Reactor from Isotope during Period
            Product.replicate(
                    outputs("reactor.fissions_per_second"),
                    outputs("daily_data.detector.efflivetime"),
                    name = "reactor_detector.nfissions_daily",
                    replicate_outputs=combinations["reactor.isotope.detector.period"],
                    allow_skip_inputs = True,
                    skippable_inputs_should_contain = self.inactive_detectors
                    )

            # Total effective number of fissions from a Reactor seen in the Detector during Period
            from dag_modelling.lib.summation import ArraySum
            ArraySum.replicate(
                    outputs("reactor_detector.nfissions_daily"),
                    name = "reactor_detector.nfissions",
                    )

            # Baseline factor from Reactor to Detector: 1/(4πL²)
            from dgm_reactor_neutrino import InverseSquareLaw
            InverseSquareLaw.replicate(
                name="reactor_detector.baseline_factor_per_cm2",
                scale="m_to_cm",
                replicate_outputs=combinations["reactor.detector"]
            )
            parameters("constant.baseline") >> inputs("reactor_detector.baseline_factor_per_cm2")

            # Number of protons per detector
            Product.replicate(
                    parameters.get_value("all.detector.nprotons_nominal_ad"),
                    parameters("all.detector.nprotons_correction"),
                    name = "detector.nprotons",
                    replicate_outputs = index["detector"]
            )

            # Number of fissions × N protons × ε / (4πL²)  (main)
            Product.replicate(
                    outputs("reactor_detector.nfissions"),
                    outputs("detector.nprotons"),
                    outputs("reactor_detector.baseline_factor_per_cm2"),
                    parameters.get_value("all.detector.efficiency"),
                    name = "reactor_detector.nfissions_nprotons_per_cm2",
                    replicate_outputs=combinations["reactor.isotope.detector.period"],
                    )

            Product.replicate(
                    outputs("reactor_detector.nfissions_nprotons_per_cm2"),
                    parameters("all.reactor.nonequilibrium_scale"),
                    parameters.get_value("all.reactor.neq_factor"),
                    name = "reactor_detector.nfissions_nprotons_per_cm2_neq",
                    replicate_outputs=combinations["reactor.isotope.detector.period"],
                    )

            # Detector live time
            ArraySum.replicate(
                    outputs("daily_data.detector.livetime"),
                    name = "detector.livetime",
                    )

            ArraySum.replicate(
                    outputs("daily_data.detector.efflivetime"),
                    name = "detector.efflivetime",
                    )

            Product.replicate(
                    outputs("detector.efflivetime"),
                    parameters.get_value("all.conversion.seconds_in_day_inverse"),
                    name="detector.efflivetime_days",
                    replicate_outputs=combinations["detector.period"],
                    allow_skip_inputs=True,
                    skippable_inputs_should_contain=self.inactive_detectors,
                    )

            # Effective live time × N protons × ε / (4πL²)  (SNF)
            Product.replicate(
                    outputs("detector.efflivetime"),
                    outputs("detector.nprotons"),
                    outputs("reactor_detector.baseline_factor_per_cm2"),
                    parameters("all.reactor.snf_scale"),
                    parameters.get_value("all.reactor.snf_factor"),
                    parameters.get_value("all.detector.efficiency"),
                    name = "reactor_detector.livetime_nprotons_per_cm2_snf",
                    replicate_outputs=combinations["reactor.detector.period"],
                    allow_skip_inputs = True,
                    skippable_inputs_should_contain = self.inactive_detectors
                    )

            #
            # Average SNF Spectrum
            #
            Product.replicate(
                    outputs("reactor_anue.neutrino_per_fission_per_MeV_nominal"),
                    outputs("reactor.fissions_per_second_snf"),
                    name = "snf_anue.neutrino_per_second_isotope",
                    replicate_outputs=combinations["reactor.isotope"],
                    )

            Sum.replicate(
                    outputs("snf_anue.neutrino_per_second_isotope"),
                    name = "snf_anue.neutrino_per_second",
                    replicate_outputs=index["reactor"],
                    )

            Product.replicate(
                    outputs("snf_anue.neutrino_per_second"),
                    outputs("snf_anue.correction_interpolated"),
                    name = "snf_anue.neutrino_per_second_snf",
                    replicate_outputs = index["reactor"]
                    )

            #
            # Integrand: flux × oscillation probability × cross section
            # [Nν·cm²/fission/proton]
            #
            Product.replicate(
                    outputs.get_value("kinematics.ibd.crosssection"),
                    outputs.get_value("kinematics.ibd.jacobian"),
                    name="kinematics.ibd.crosssection_jacobian",
            )

            Product.replicate(
                    outputs.get_value("kinematics.ibd.crosssection_jacobian"),
                    outputs("oscprob"),
                    name="kinematics.ibd.crosssection_jacobian_oscillations",
                    replicate_outputs=combinations["reactor.detector"]
            )

            Product.replicate(
                    outputs("kinematics.ibd.crosssection_jacobian_oscillations"),
                    outputs("reactor_anue.part.neutrino_per_fission_per_MeV_main"),
                    name="kinematics.neutrino_cm2_per_MeV_per_fission_per_proton.part.nu_main",
                    replicate_outputs=combinations["reactor.isotope.detector"]
            )

            Product.replicate(
                    outputs("kinematics.ibd.crosssection_jacobian_oscillations"),
                    outputs("reactor_anue.part.neutrino_per_fission_per_MeV_neq_nominal"),
                    name="kinematics.neutrino_cm2_per_MeV_per_fission_per_proton.part.nu_neq",
                    replicate_outputs=combinations["reactor.isotope_neq.detector"]
            )

            Product.replicate(
                    outputs("kinematics.ibd.crosssection_jacobian_oscillations"),
                    outputs("snf_anue.neutrino_per_second_snf"),
                    name="kinematics.neutrino_cm2_per_MeV_per_fission_per_proton.part.nu_snf",
                    replicate_outputs=combinations["reactor.detector"]
            )
            outputs("kinematics.neutrino_cm2_per_MeV_per_fission_per_proton.part.nu_main") >> inputs("kinematics.integral.nu_main")
            outputs("kinematics.neutrino_cm2_per_MeV_per_fission_per_proton.part.nu_neq") >> inputs("kinematics.integral.nu_neq")
            outputs("kinematics.neutrino_cm2_per_MeV_per_fission_per_proton.part.nu_snf") >> inputs("kinematics.integral.nu_snf")

            #
            # Multiply by the scaling factors:
            #  - nu_main: fissions_per_second[p,r,i] × effective live time[p,d] × N protons[d] × efficiency[d]
            #  - nu_neq:  fissions_per_second[p,r,i] × effective live time[p,d] × N protons[d] × efficiency[d] × nonequilibrium scale[r,i] × neq_factor(=1)
            #  - nu_snf:                               effective live time[p,d] × N protons[d] × efficiency[d] × SNF scale[r]              × snf_factor(=1)
            #
            Product.replicate(
                    outputs("kinematics.integral.nu_main"),
                    outputs("reactor_detector.nfissions_nprotons_per_cm2"),
                    name = "eventscount.parts.nu_main",
                    replicate_outputs = combinations["reactor.isotope.detector.period"]
                    )

            Product.replicate(
                    outputs("kinematics.integral.nu_neq"),
                    outputs("reactor_detector.nfissions_nprotons_per_cm2_neq"),
                    name = "eventscount.parts.nu_neq",
                    replicate_outputs = combinations["reactor.isotope_neq.detector.period"],
                    allow_skip_inputs = True,
                    skippable_inputs_should_contain = ("U238",)
                    )

            Product.replicate(
                    outputs("kinematics.integral.nu_snf"),
                    outputs("reactor_detector.livetime_nprotons_per_cm2_snf"),
                    name = "eventscount.parts.nu_snf",
                    replicate_outputs = combinations["reactor.detector.period"]
                    )

            Sum.replicate(
                outputs("eventscount.parts"),
                name="eventscount.raw",
                replicate_outputs=combinations["detector.period"]
            )

            #
            # Detector effects
            #
            load_array(
                name = "detector.iav",
                filenames = path_arrays/f"detector_IAV_matrix_P14A_LS.{self._source_type}",
                replicate_outputs = ("matrix_raw",),
                name_function = {"matrix_raw": "iav_matrix"},
                array_kwargs = {
                    'edges': (edges_energy_escint, edges_energy_edep)
                    }
            )

            from dag_modelling.lib.normalization import RenormalizeDiag
            RenormalizeDiag.replicate(mode="offdiag", name="detector.iav.matrix_rescaled", replicate_outputs=index["detector"])
            parameters("all.detector.iav_offdiag_scale_factor") >> inputs("detector.iav.matrix_rescaled.scale")
            outputs.get_value("detector.iav.matrix_raw") >> inputs("detector.iav.matrix_rescaled.matrix")

            from dag_modelling.lib.linalg import VectorMatrixProduct
            VectorMatrixProduct.replicate(name="eventscount.iav", replicate_outputs=combinations["detector.period"], mode="column")
            outputs("detector.iav.matrix_rescaled") >> inputs("eventscount.iav.matrix")
            outputs("eventscount.raw") >> inputs("eventscount.iav.vector")

            load_graph_data(
                name = "detector.lsnl.curves",
                x = "edep",
                y = "evis_parts",
                merge_x = True,
                filenames = path_arrays/f"detector_LSNL_curves_Jan2022_newE_v1.{self._source_type}",
                replicate_outputs = index["lsnl"],
            )

            if "lsnl-curves" in self._future:
                # Refine LSNL curves: interpolate with smaller step
                logger.warning("Future: Pre-interpolate LSNL curves")
                from ..bundles.refine_lsnl_data import \
                    refine_lsnl_data
                refine_lsnl_data(
                    storage("data.detector.lsnl.curves"),
                    xname = 'edep',
                    nominalname = 'evis_parts.nominal',
                    refine_times = 4,
                    newmin = 0.5,
                    newmax = 12.1
                )
            else:
                # Coarse LSNL model, consistent with GNA implementation
                from ..bundles.cross_check_refine_lsnl_data import \
                    cross_check_refine_lsnl_data
                cross_check_refine_lsnl_data(
                    storage("data.detector.lsnl.curves"),
                    xname = 'edep',
                    nominalname = 'evis_parts.nominal',
                    newmin = 0.5,
                    newmax = 12.1
                )

            Array.from_storage(
                "detector.lsnl.curves",
                storage("data"),
                meshname = "edep",
                remove_processed_arrays = True
            )

            Product.replicate(
                outputs("detector.lsnl.curves.evis_parts"),
                parameters("constrained.detector.lsnl_scale_a"),
                name = "detector.lsnl.curves.evis_parts_scaled",
                allow_skip_inputs = True,
                skippable_inputs_should_contain = ("nominal",),
                replicate_outputs=index["lsnl_nuisance"]
            )

            Sum.replicate(
                outputs.get_value("detector.lsnl.curves.evis_parts.nominal"),
                outputs("detector.lsnl.curves.evis_parts_scaled"),
                name="detector.lsnl.curves.evis_coarse"
            )

            #
            # Force Evis(Edep) to grow monotonously
            # - Required by matrix calculation algorithm
            # - Introduced to achieve stable minimization
            # - Non-monotonous behavior happens for extreme systematic values and is not expected to affect the analysis
            from dgm_dayabay_dev.nodes.Monotonize import Monotonize
            Monotonize.replicate(
                    name="detector.lsnl.curves.evis_coarse_monotonous",
                    index_fraction = 0.5,
                    gradient = 1.0,
                    with_x = True
                    )
            outputs.get_value("detector.lsnl.curves.edep") >> inputs.get_value("detector.lsnl.curves.evis_coarse_monotonous.x")
            outputs.get_value("detector.lsnl.curves.evis_coarse") >> inputs.get_value("detector.lsnl.curves.evis_coarse_monotonous.y")

            from nested_mapping.tools import remap_items
            remap_items(
                parameters("all.detector.detector_relative"),
                outputs.create_child("detector.parameters_relative"),
                reorder_indices=[
                    ["detector", "parameters"],
                    ["parameters", "detector"],
                ],
            )

            if "lsnl-matrix" in self._future:
                logger.warning("Future: precise LSNL matrix computation")
                # Interpolate Evis(Edep)
                Interpolator.replicate(
                    method = "linear",
                    names = {
                        "indexer": "detector.lsnl.indexer_fwd",
                        "interpolator": "detector.lsnl.interpolated_fwd",
                        },
                )
                outputs.get_value("detector.lsnl.curves.edep") >> inputs.get_value("detector.lsnl.interpolated_fwd.xcoarse")
                outputs.get_value("detector.lsnl.curves.evis_coarse_monotonous") >> inputs.get_value("detector.lsnl.interpolated_fwd.ycoarse")
                edges_energy_edep >> inputs.get_value("detector.lsnl.interpolated_fwd.xfine")

                # Introduce uncorrelated between detectors energy scale for interpolated Evis[detector]=s[detector]*Evis(Edep)
                Product.replicate(
                    outputs.get_value("detector.lsnl.interpolated_fwd"),
                    outputs("detector.parameters_relative.energy_scale_factor"),
                    name="detector.lsnl.curves.evis",
                    replicate_outputs = index["detector"]
                )

                # Introduce uncorrelated between detectors energy scale for coarse Evis[detector]=s[detector]*Evis(Edep)
                Product.replicate(
                    outputs.get_value("detector.lsnl.curves.evis_coarse_monotonous"),
                    outputs("detector.parameters_relative.energy_scale_factor"),
                    name="detector.lsnl.curves.evis_coarse_monotonous_scaled",
                    replicate_outputs = index["detector"]
                )

                # Interpolate Edep(Evis[detector])
                Interpolator.replicate(
                    method = "linear",
                    names = {
                        "indexer": "detector.lsnl.indexer_bwd",
                        "interpolator": "detector.lsnl.interpolated_bwd",
                        },
                    replicate_xcoarse = True,
                    replicate_outputs = index["detector"]
                )
                outputs.get_dict("detector.lsnl.curves.evis_coarse_monotonous_scaled") >> inputs.get_dict("detector.lsnl.interpolated_bwd.xcoarse")
                outputs.get_value("detector.lsnl.curves.edep")  >> inputs.get_dict("detector.lsnl.interpolated_bwd.ycoarse")
                edges_energy_evis.outputs[0] >> inputs.get_dict("detector.lsnl.interpolated_bwd.xfine")

                # Build LSNL matrix
                from dag_modelling.lib.hist import AxisDistortionMatrix
                AxisDistortionMatrix.replicate(name="detector.lsnl.matrix", replicate_outputs=index["detector"])
                edges_energy_escint.outputs[0] >> inputs("detector.lsnl.matrix.EdgesOriginal")
                edges_energy_evis.outputs[0] >> inputs("detector.lsnl.matrix.EdgesTarget")
                outputs.get_value("detector.lsnl.interpolated_fwd") >> inputs.get_dict("detector.lsnl.matrix.EdgesModified")
                outputs.get_dict("detector.lsnl.interpolated_bwd") >> inputs.get_dict("detector.lsnl.matrix.EdgesModifiedBackwards")
            else:
                Interpolator.replicate(
                    method = "linear",
                    names = {
                        "indexer": "detector.lsnl.indexer_fwd",
                        "interpolator": "detector.lsnl.interpolated_fwd",
                        },
                )
                outputs.get_value("detector.lsnl.curves.edep") >> inputs.get_value("detector.lsnl.interpolated_fwd.xcoarse")
                outputs.get_value("detector.lsnl.curves.evis_coarse_monotonous") >> inputs.get_value("detector.lsnl.interpolated_fwd.ycoarse")
                edges_energy_edep >> inputs.get_value("detector.lsnl.interpolated_fwd.xfine")

                Product.replicate(
                    outputs.get_value("detector.lsnl.interpolated_fwd"),
                    outputs("detector.parameters_relative.energy_scale_factor"),
                    name="detector.lsnl.curves.evis",
                    replicate_outputs = index["detector"]
                )

                from dgm_dayabay_dev.nodes.AxisDistortionMatrixLinearLegacy import \
                    AxisDistortionMatrixLinearLegacy
                AxisDistortionMatrixLinearLegacy.replicate(
                    name="detector.lsnl.matrix",
                    replicate_outputs=index["detector"],
                    min_value_modified=0.7001
                )
                edges_energy_escint.outputs[0] >> inputs("detector.lsnl.matrix.EdgesOriginal")
                edges_energy_evis.outputs[0] >> inputs("detector.lsnl.matrix.EdgesTarget")
                outputs("detector.lsnl.curves.evis") >> inputs("detector.lsnl.matrix.EdgesModified")

            VectorMatrixProduct.replicate(name="eventscount.evis", replicate_outputs=combinations["detector.period"], mode="column")
            outputs("detector.lsnl.matrix") >> inputs("eventscount.evis.matrix")
            outputs("eventscount.iav") >> inputs("eventscount.evis.vector")

            from dag_modelling.lib.physics import EnergyResolution
            EnergyResolution.replicate(path="detector.eres")
            nodes.get_value("detector.eres.sigma_rel") << parameters("constrained.detector.eres")
            outputs.get_value("edges.energy_evis") >> inputs.get_value("detector.eres.matrix.e_edges")
            outputs.get_value("edges.energy_erec") >> inputs.get_value("detector.eres.matrix.e_edges_out")
            outputs.get_value("edges.energy_evis") >> inputs.get_value("detector.eres.e_edges")

            VectorMatrixProduct.replicate(name="eventscount.erec", replicate_outputs=combinations["detector.period"], mode="column")
            outputs.get_value("detector.eres.matrix") >> inputs("eventscount.erec.matrix")
            outputs("eventscount.evis") >> inputs("eventscount.erec.vector")

            Product.replicate(
                parameters.get_value("all.detector.global_normalization"),
                outputs("detector.parameters_relative.efficiency_factor"),
                name = "detector.normalization",
                replicate_outputs=index["detector"],
            )

            Product.replicate(
                outputs("detector.normalization"),
                outputs("eventscount.erec"),
                name = "eventscount.fine.ibd_normalized",
                replicate_outputs=combinations["detector.period"],
            )

            Sum.replicate(
                outputs("eventscount.fine.ibd_normalized"),
                name = "eventscount.fine.ibd_normalized_detector",
                replicate_outputs=combinations["detector"],
            )

            from dag_modelling.lib.hist import Rebin
            Rebin.replicate(
                names={"matrix": "detector.rebin.matrix_ibd", "product": "eventscount.final.ibd"},
                replicate_outputs=combinations["detector.period"],
            )
            edges_energy_erec >> inputs.get_value("detector.rebin.matrix_ibd.edges_old")
            edges_energy_final >> inputs.get_value("detector.rebin.matrix_ibd.edges_new")
            outputs("eventscount.fine.ibd_normalized") >> inputs("eventscount.final.ibd")

            #
            # Backgrounds
            #
            from dag_modelling.bundles.load_hist import load_hist
            bkg_names = {
                'acc': "accidental",
                'lihe': "lithium9",
                'fastn': "fastNeutron",
                'amc': "amCSource",
                'alphan': "carbonAlpha",
                'muon': "muonRelated"
            }
            load_hist(
                name = "bkg",
                x = "erec",
                y = "spectrum_shape",
                merge_x = True,
                normalize = True,
                filenames = path_root/"bkg_SYSU_input_by_period_{}.root",
                replicate_files = index["period"],
                replicate_outputs = combinations["bkg.detector"],
                skip = self.inactive_detectors,
                key_order = (1, 2, 0),
                name_function = lambda _, idx: f"DYB_{bkg_names[idx[0]]}_expected_spectrum_EH{idx[-2][-2]}_AD{idx[-2][-1]}"
            )

            # TODO: Daya Bay v1 (if needed)
            # from nested_mapping.tools import remap_items
            # ads_at_sites = {
            #         "EH1": ("AD11", "AD12"),
            #         "EH2": ("AD21", "AD22"),
            #         "EH3": ("AD31", "AD32", "AD33", "AD34"),
            #         }
            # remap_items(
            #     parameters("all.bkg.rate.fastn"),
            #     outputs.create_child("bkg.rate.fastn"),
            #     rename_indices = ads_at_sites,
            #     skip_indices_target = self.inactive_detectors,
            #     fcn = lambda par: par.output
            # )
            # remap_items(
            #     parameters("all.bkg.rate.lihe"),
            #     outputs.create_child("bkg.rate.lihe"),
            #     rename_indices = ads_at_sites,
            #     skip_indices_target = self.inactive_detectors,
            #     fcn = lambda par: par.output
            # )

            # NOTE:
            # GNA upload fast-n as array from 0 to 12 MeV (50 keV), and it normalized to 1.
            # So, every bin contain 0.00416667.
            # TODO: remove in dayabay-v1
            from numpy import ones
            fastn_data = ones(240) / 240
            for key, spectrum in storage("outputs.bkg.spectrum_shape.fastn").walkitems():
                spectrum._data[:] = fastn_data

            Product.replicate(
                    parameters("all.bkg.rate.acc"),
                    outputs("bkg.spectrum_shape.acc"),
                    name="bkg.spectrum_per_day.acc",
                    replicate_outputs=combinations["detector.period"],
                    )

            Product.replicate(
                    # outputs("bkg.rate.lihe"),
                    parameters("all.bkg.rate.lihe"),
                    outputs("bkg.spectrum_shape.lihe"),
                    name="bkg.spectrum_per_day.lihe",
                    replicate_outputs=combinations["detector.period"],
                    )

            Product.replicate(
                    # outputs("bkg.rate.fastn"),
                    parameters("all.bkg.rate.fastn"),
                    outputs("bkg.spectrum_shape.fastn"),
                    name="bkg.spectrum_per_day.fastn",
                    replicate_outputs=combinations["detector.period"],
                    )

            Product.replicate(
                    parameters("all.bkg.rate.alphan"),
                    outputs("bkg.spectrum_shape.alphan"),
                    name="bkg.spectrum_per_day.alphan",
                    replicate_outputs=combinations["detector.period"],
                    )

            Product.replicate(
                    parameters("all.bkg.rate.amc"),
                    outputs("bkg.spectrum_shape.amc"),
                    name="bkg.spectrum_per_day.amc",
                    replicate_outputs=combinations["detector.period"],
                    )

            # Total spectrum of Background in Detector during Period
            # spectrum_per_day [N / day] * efflivetime [sec] * seconds_in_day_inverse [day / sec] -> [N]
            Product.replicate(
                    outputs("detector.efflivetime_days"),
                    outputs("bkg.spectrum_per_day"),
                    name="bkg.spectrum",
                    replicate_outputs=combinations["bkg.detector.period"],
                    )

            Sum.replicate(
                    outputs("bkg.spectrum"),
                    name="eventscount.fine.bkg",
                    replicate_outputs=combinations["detector.period"],
                    )

            Sum.replicate(
                    outputs("eventscount.fine.ibd_normalized"),
                    outputs("eventscount.fine.bkg"),
                    name="eventscount.fine.total",
                    replicate_outputs=combinations["detector.period"],
                    check_edges_contents=True,
                    )

            Rebin.replicate(
                    names={"matrix": "detector.rebin.matrix_bkg", "product": "eventscount.final.bkg"},
                    replicate_outputs=combinations["detector.period"],
            )
            edges_energy_erec >> inputs.get_value("detector.rebin.matrix_bkg.edges_old")
            edges_energy_final >> inputs.get_value("detector.rebin.matrix_bkg.edges_new")
            outputs("eventscount.fine.bkg") >> inputs("eventscount.final.bkg")

            Sum.replicate(
                outputs("eventscount.final.ibd"),
                outputs("eventscount.final.bkg"),
                name="eventscount.final.detector_period",
                replicate_outputs=combinations["detector.period"],
            )

            Concatenation.replicate(
                outputs("eventscount.final.detector_period"),
                name="eventscount.final.concatenated.detector_period",
            )

            Sum.replicate(
                outputs("eventscount.final.detector_period"),
                name="eventscount.final.detector",
                replicate_outputs=index["detector"],
            )

            Concatenation.replicate(
                outputs("eventscount.final.detector"),
                name="eventscount.final.concatenated.detector"
            )

            outputs["eventscount.final.concatenated.selected"] = outputs[f"eventscount.final.concatenated.{self._concatenation_mode}"]

            #
            # Covariance matrices
            #
            from dag_modelling.lib.statistics import CovarianceMatrixGroup
            self._covariance_matrix = CovarianceMatrixGroup(store_to="covariance", **self._covmatrix_kwargs)

            for name, parameters_source in self.systematic_uncertainties_groups().items():
                self._covariance_matrix.add_covariance_for(name, parameters_nuisance_normalized[parameters_source])
            self._covariance_matrix.add_covariance_sum()

            outputs.get_value("eventscount.final.concatenated.selected") >> self._covariance_matrix

            npars_cov = self._covariance_matrix.get_parameters_count()
            list_parameters_nuisance_normalized = list(parameters_nuisance_normalized.walkvalues())
            npars_nuisance = len(list_parameters_nuisance_normalized)
            if npars_cov!=npars_nuisance:
                raise RuntimeError("Some parameters are missing from covariance matrix")

            from dag_modelling.lib.parameters import ParArrayInput
            parinp_mc = ParArrayInput(
                name="mc.parameters.inputs",
                parameters=list_parameters_nuisance_normalized,
            )

            #
            # Statistic
            #
            # Create Nuisance parameters
            Sum.replicate(outputs("statistic.nuisance.parts"), name="statistic.nuisance.all")

            from dag_modelling.lib.statistics import MonteCarlo
            MonteCarlo.replicate(
                name="data.pseudo.self",
                mode=self._monte_carlo_mode,
                generator=self._random_generator,
            )
            outputs.get_value("eventscount.final.concatenated.selected") >> inputs.get_value("data.pseudo.self.data")
            self._frozen_nodes["pseudodata"] = (nodes.get_value("data.pseudo.self"),)

            from dag_modelling.lib.common import Proxy
            Proxy.replicate(
                name="data.proxy",
            )
            outputs.get_value("data.pseudo.self") >> inputs.get_value("data.proxy.input")

            MonteCarlo.replicate(
                name="covariance.data.fixed",
                mode="asimov",
                generator=self._random_generator,
            )
            outputs.get_value("eventscount.final.concatenated.selected") >> inputs.get_value("covariance.data.fixed.data")
            self._frozen_nodes["covariance_data_fixed"] = (nodes.get_value("covariance.data.fixed"),)

            MonteCarlo.replicate(
                name="mc.parameters.toymc",
                mode="normal-unit",
                shape=(npars_nuisance,),
                generator=self._random_generator,
            )
            outputs.get_value("mc.parameters.toymc") >> parinp_mc
            nodes["mc.parameters.inputs"] = parinp_mc

            from dag_modelling.lib.linalg import Cholesky
            Cholesky.replicate(name="cholesky.stat.variable")
            outputs.get_value("eventscount.final.concatenated.selected") >> inputs.get_value("cholesky.stat.variable")

            Cholesky.replicate(name="cholesky.stat.fixed")
            outputs.get_value("covariance.data.fixed") >> inputs.get_value("cholesky.stat.fixed")

            Cholesky.replicate(name="cholesky.stat.data.fixed")
            outputs.get_value("data.proxy") >> inputs.get_value("cholesky.stat.data.fixed")

            from dag_modelling.lib.summation import SumMatOrDiag
            SumMatOrDiag.replicate(name="covariance.covmat_full_p.stat_fixed")
            outputs.get_value("covariance.data.fixed") >> nodes.get_value("covariance.covmat_full_p.stat_fixed")
            outputs.get_value("covariance.covmat_syst.sum") >> nodes.get_value("covariance.covmat_full_p.stat_fixed")

            Cholesky.replicate(name="cholesky.covmat_full_p.stat_fixed")
            outputs.get_value("covariance.covmat_full_p.stat_fixed") >> inputs.get_value("cholesky.covmat_full_p.stat_fixed")

            SumMatOrDiag.replicate(name="covariance.covmat_full_p.stat_variable")
            outputs.get_value("eventscount.final.concatenated.selected") >> nodes.get_value("covariance.covmat_full_p.stat_variable")
            outputs.get_value("covariance.covmat_syst.sum") >> nodes.get_value("covariance.covmat_full_p.stat_variable")

            Cholesky.replicate(name="cholesky.covmat_full_p.stat_variable")
            outputs.get_value("covariance.covmat_full_p.stat_variable") >> inputs.get_value("cholesky.covmat_full_p.stat_variable")

            SumMatOrDiag.replicate(name="covariance.covmat_full_n")
            outputs.get_value("data.proxy") >> nodes.get_value("covariance.covmat_full_n")
            outputs.get_value("covariance.covmat_syst.sum") >> nodes.get_value("covariance.covmat_full_n")

            Cholesky.replicate(name="cholesky.covmat_full_n")
            outputs.get_value("covariance.covmat_full_n") >> inputs.get_value("cholesky.covmat_full_n")

            from dag_modelling.lib.statistics import Chi2

            # (1) chi-squared Pearson stat (fixed Pearson errors)
            Chi2.replicate(name="statistic.stat.chi2p_iterative")
            outputs.get_value("eventscount.final.concatenated.selected") >> inputs.get_value("statistic.stat.chi2p_iterative.theory")
            outputs.get_value("cholesky.stat.fixed") >> inputs.get_value("statistic.stat.chi2p_iterative.errors")
            outputs.get_value("data.proxy") >> inputs.get_value("statistic.stat.chi2p_iterative.data")

            # (2-2) chi-squared Neyman stat
            Chi2.replicate(name="statistic.stat.chi2n")
            outputs.get_value("eventscount.final.concatenated.selected") >> inputs.get_value("statistic.stat.chi2n.theory")
            outputs.get_value("cholesky.stat.data.fixed") >> inputs.get_value("statistic.stat.chi2n.errors")
            outputs.get_value("data.proxy") >> inputs.get_value("statistic.stat.chi2n.data")

            # (2-1)
            Chi2.replicate(name="statistic.stat.chi2p")
            outputs.get_value("eventscount.final.concatenated.selected") >> inputs.get_value("statistic.stat.chi2p.theory")
            outputs.get_value("cholesky.stat.variable") >> inputs.get_value("statistic.stat.chi2p.errors")
            outputs.get_value("data.proxy") >> inputs.get_value("statistic.stat.chi2p.data")

            # (5) chi-squared Pearson syst (fixed Pearson errors)
            Chi2.replicate(name="statistic.full.chi2p_covmat_fixed")
            outputs.get_value("data.proxy") >> inputs.get_value("statistic.full.chi2p_covmat_fixed.data")
            outputs.get_value("eventscount.final.concatenated.selected") >> inputs.get_value("statistic.full.chi2p_covmat_fixed.theory")
            outputs.get_value("cholesky.covmat_full_p.stat_fixed") >> inputs.get_value("statistic.full.chi2p_covmat_fixed.errors")

            # (2-3) chi-squared Neyman syst
            Chi2.replicate(name="statistic.full.chi2n_covmat")
            outputs.get_value("data.proxy") >> inputs.get_value("statistic.full.chi2n_covmat.data")
            outputs.get_value("eventscount.final.concatenated.selected") >> inputs.get_value("statistic.full.chi2n_covmat.theory")
            outputs.get_value("cholesky.covmat_full_n") >> inputs.get_value("statistic.full.chi2n_covmat.errors")

            # (2-4) Pearson variable stat errors
            Chi2.replicate(name="statistic.full.chi2p_covmat_variable")
            outputs.get_value("data.proxy") >> inputs.get_value("statistic.full.chi2p_covmat_variable.data")
            outputs.get_value("eventscount.final.concatenated.selected") >> inputs.get_value("statistic.full.chi2p_covmat_variable.theory")
            outputs.get_value("cholesky.covmat_full_p.stat_variable") >> inputs.get_value("statistic.full.chi2p_covmat_variable.errors")

            from dag_modelling.lib.statistics import CNPStat
            CNPStat.replicate(name="statistic.staterr.cnp")
            outputs.get_value("data.proxy") >> inputs.get_value("statistic.staterr.cnp.data")
            outputs.get_value("eventscount.final.concatenated.selected") >> inputs.get_value("statistic.staterr.cnp.theory")

            # (3) chi-squared CNP stat
            Chi2.replicate(name="statistic.stat.chi2cnp")
            outputs.get_value("data.proxy") >> inputs.get_value("statistic.stat.chi2cnp.data")
            outputs.get_value("eventscount.final.concatenated.selected") >> inputs.get_value("statistic.stat.chi2cnp.theory")
            outputs.get_value("statistic.staterr.cnp") >> inputs.get_value("statistic.stat.chi2cnp.errors")

            # (2) chi-squared Pearson stat + pull (fixed Pearson errors)
            Sum.replicate(
                outputs.get_value("statistic.stat.chi2p_iterative"),
                outputs.get_value("statistic.nuisance.all"),
                name="statistic.full.chi2p_iterative",
            )
            # (4) chi-squared CNP stat + pull (fixed Pearson errors)
            Sum.replicate(
                outputs.get_value("statistic.stat.chi2cnp"),
                outputs.get_value("statistic.nuisance.all"),
                name="statistic.full.chi2cnp",
            )

            from dag_modelling.lib.statistics import LogProdDiag
            LogProdDiag.replicate(name="statistic.log_prod_diag")
            outputs.get_value("cholesky.covmat_full_p.stat_variable") >> inputs.get_value("statistic.log_prod_diag")

            # (7) chi-squared Pearson stat + log|V| (unfixed Pearson errors)
            Sum.replicate(
                outputs.get_value("statistic.stat.chi2p"),
                outputs.get_value("statistic.log_prod_diag"),
                name="statistic.stat.chi2p_unbiased",
            )

            # (8) chi-squared Pearson stat + log|V| + pull (unfixed Pearson errors)
            Sum.replicate(
                outputs.get_value("statistic.stat.chi2p_unbiased"),
                outputs.get_value("statistic.nuisance.all"),
                name="statistic.full.chi2p_unbiased",
            )

            Product.replicate(
                parameters.get_value("all.stats.pearson"),
                outputs.get_value("statistic.full.chi2p_covmat_variable"),
                name="statistic.helper.pearson",
            )
            Product.replicate(
                parameters.get_value("all.stats.neyman"),
                outputs.get_value("statistic.full.chi2n_covmat"),
                name="statistic.helper.neyman",
            )
            # (2-4) CNP covmat
            Sum.replicate(
                outputs.get_value("statistic.helper.pearson"),
                outputs.get_value("statistic.helper.neyman"),
                name="statistic.full.chi2cnp_covmat",
            )
            # fmt: on

        self._setup_labels()

        # Ensure stem nodes are calculated
        self._touch()

    @staticmethod
    def _create_random_generator(seed: int) -> Generator:
        from numpy.random import MT19937, SeedSequence

        (sequence,) = SeedSequence(seed).spawn(1)
        algo = MT19937(seed=sequence.spawn(1)[0])
        return Generator(algo)

    def _touch(self):
        for output in (
            self.storage["outputs"].get_dict("eventscount.final.detector").walkvalues()
        ):
            output.touch()

    def update_frozen_nodes(self):
        for nodes in self._frozen_nodes.values():
            for node in nodes:
                node.unfreeze()
                node.touch()

    def update_covariance_matrix(self):
        self._covariance_matrix.update_matrices()

    def set_parameters(
        self,
        parameter_values: (
            Mapping[str, float | str] | Sequence[tuple[str, float | int]]
        ) = (),
        *,
        mode: Literal["value", "normvalue"] = "value"
    ):
        parameters_storage = self.storage("parameters.all")
        if isinstance(parameter_values, Mapping):
            iterable = parameter_values.items()
        else:
            iterable = parameter_values

        match mode:
            case "value":
                def setter(par, value):
                    par.push(value)
                    print(f"Push {parname}={svalue}")
            case "normvalue":
                def setter(par, value):
                    par.normvalue = value
                    print(f"Set norm {parname}={svalue}")
            case _:
                raise ValueError(mode)

        for parname, svalue in iterable:
            value = float(svalue)
            par = parameters_storage[parname]
            setter(par, value)

    def next_sample(
        self, *, mc_parameters: bool = True, mc_statistics: bool = True
    ) -> None:
        if mc_parameters:
            self.storage.get_value("nodes.mc.parameters.toymc").next_sample()
            self.storage.get_value("nodes.mc.parameters.inputs").touch()

        if mc_statistics:
            self.storage.get_value("nodes.data.pseudo.self").next_sample()

        if mc_parameters:
            self.storage.get_value("nodes.mc.parameters.toymc").reset()
            self.storage.get_value("nodes.mc.parameters.inputs").touch()

    @staticmethod
    def systematic_uncertainties_groups() -> dict[str, str]:
        return dict(_SYSTEMATIC_UNCERTAINTIES_GROUPS)

    def _setup_labels(self):
        labels = LoadYaml(relpath(__file__.replace(".py", "_labels.yaml")))

        processed_keys_set = set()
        self.storage("nodes").read_labels(labels, processed_keys_set=processed_keys_set)
        self.storage("outputs").read_labels(
            labels, processed_keys_set=processed_keys_set
        )
        self.storage("inputs").remove_connected_inputs()
        self.storage.read_paths(index=self.index)
        self.graph.build_index_dict(self.index)

        labels_mk = NestedMapping(labels, sep=".")
        if not self._strict:
            return

        for key in processed_keys_set:
            labels_mk.delete_with_parents(key)

        if not labels_mk:
            return

        unused_keys = list(labels_mk.walkjoinedkeys())
        may_ignore = {
            "detector.lsnl.curves.evis_coarse_monotonous_scaled.group.text",
            "detector.lsnl.indexer_bwd.group.text",
            "detector.lsnl.interpolated_bwd.group.text",
        }
        for key in may_ignore:
            with suppress(ValueError):
                unused_keys.remove(key)

        if not unused_keys:
            return

        raise RuntimeError(
            f"The following label groups were not used: {', '.join(unused_keys)}"
        )
