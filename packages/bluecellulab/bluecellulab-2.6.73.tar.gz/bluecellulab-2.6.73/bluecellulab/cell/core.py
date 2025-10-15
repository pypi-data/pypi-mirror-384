# Copyright 2023-2024 Blue Brain Project / EPFL

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Cell class."""

from __future__ import annotations

import logging

from pathlib import Path
import queue
from typing import List, Optional, Tuple
from typing_extensions import deprecated

import neuron
import numpy as np
import pandas as pd
import re

import bluecellulab
from bluecellulab.cell.recording import section_to_voltage_recording_str
from bluecellulab.psection import PSection, init_psections
from bluecellulab.cell.injector import InjectableMixin
from bluecellulab.cell.plotting import PlottableMixin
from bluecellulab.cell.section_distance import EuclideanSectionDistance
from bluecellulab.cell.sonata_proxy import SonataProxy
from bluecellulab.cell.template import NeuronTemplate, TemplateParams, public_hoc_cell
from bluecellulab.circuit.config.sections import Conditions
from bluecellulab.circuit import EmodelProperties, SynapseProperty
from bluecellulab.circuit.node_id import CellId
from bluecellulab.circuit.simulation_access import get_synapse_replay_spikes
from bluecellulab.exceptions import BluecellulabError
from bluecellulab.importer import load_mod_files
from bluecellulab.neuron_interpreter import eval_neuron
from bluecellulab.rngsettings import RNGSettings
from bluecellulab.stimulus.circuit_stimulus_definitions import SynapseReplay
from bluecellulab.synapse import SynapseFactory, Synapse
from bluecellulab.synapse.synapse_types import SynapseID
from bluecellulab.type_aliases import HocObjectType, NeuronSection, SectionMapping
from bluecellulab.cell.section_tools import currents_vars, section_to_variable_recording_str

logger = logging.getLogger(__name__)


class Cell(InjectableMixin, PlottableMixin):
    """Represents a Cell object."""

    last_id = 0

    @classmethod
    def from_template_parameters(
        cls, template_params: TemplateParams, cell_id: Optional[CellId] = None,
        record_dt: Optional[float] = None
    ) -> Cell:
        """Create a cell from a TemplateParams object.

        Useful in isolating runs.
        """
        return cls(
            template_path=template_params.template_filepath,
            morphology_path=template_params.morph_filepath,
            cell_id=cell_id,
            record_dt=record_dt,
            template_format=template_params.template_format,
            emodel_properties=template_params.emodel_properties,
        )

    @load_mod_files
    def __init__(self,
                 template_path: str | Path,
                 morphology_path: str | Path,
                 cell_id: Optional[CellId] = None,
                 record_dt: Optional[float] = None,
                 template_format: str = "v5",
                 emodel_properties: Optional[EmodelProperties] = None) -> None:
        """Initializes a Cell object.

        Args:
            template_path: Path to hoc template file.
            morphology_path: Path to morphology file.
            cell_id: ID of the cell, used in RNG seeds.
            record_dt: Timestep for the recordings.
            template_format: Cell template format such as 'v5' or 'v6_air_scaler'.
            emodel_properties: Template specific emodel properties.
        """
        super().__init__()
        self.template_params = TemplateParams(
            template_filepath=template_path,
            morph_filepath=morphology_path,
            template_format=template_format,
            emodel_properties=emodel_properties,
        )
        if cell_id is None:
            cell_id = CellId("", Cell.last_id)
            Cell.last_id += 1
        self.cell_id = cell_id

        # Load the template
        neuron_template = NeuronTemplate(template_path, morphology_path, template_format, emodel_properties)
        self.template_id = neuron_template.template_name  # useful to map NEURON and python objects
        self.cell = neuron_template.get_cell(self.cell_id.id)
        if template_format == 'v6':
            if emodel_properties is None:
                raise BluecellulabError('EmodelProperties must be provided for v6 template')
            self.hypamp: float | None = emodel_properties.holding_current
            self.threshold: float = emodel_properties.threshold_current
        else:
            try:
                self.hypamp = self.cell.getHypAmp()
            except AttributeError:
                self.hypamp = None
            try:
                self.threshold = self.cell.getThreshold()
            except AttributeError:
                self.threshold = 0.0
        self.soma = public_hoc_cell(self.cell).soma[0]
        # WARNING: this finitialize 'must' be here, otherwhise the
        # diameters of the loaded morph are wrong
        neuron.h.finitialize()

        self.recordings: dict[str, HocObjectType] = {}
        self.synapses: dict[SynapseID, Synapse] = {}
        self.connections: dict[SynapseID, bluecellulab.Connection] = {}

        self.ips: dict[SynapseID, HocObjectType] = {}
        self.syn_mini_netcons: dict[SynapseID, HocObjectType] = {}

        # Be careful when removing this,
        # time recording needs this push
        self.soma.push()
        self.hocname = neuron.h.secname(sec=self.soma).split(".")[0]
        self.record_dt = record_dt
        self.add_recordings(['self.soma(0.5)._ref_v', 'neuron.h._ref_t'],
                            dt=self.record_dt)

        self.delayed_weights = queue.PriorityQueue()  # type: ignore
        self.psections: dict[int, PSection] = {}
        self.secname_to_psection: dict[str, PSection] = {}

        # Keep track of when a cell is made passive by make_passive()
        # Used to know when re_init_rng() can be executed
        self.is_made_passive = False

        neuron.h.pop_section()  # Undoing soma push
        self.sonata_proxy: Optional[SonataProxy] = None

        # Persistent objects, like clamps, that exist as long
        # as the object exists
        self.persistent: list[HocObjectType] = []

    def _init_psections(self) -> None:
        """Initialize the psections of the cell."""
        if not self.psections:
            self.psections, self.secname_to_psection = init_psections(public_hoc_cell(self.cell))

    def _extract_sections(self, sections) -> SectionMapping:
        res: SectionMapping = {}
        for section in sections:
            key_name = str(section).split(".")[-1]
            res[key_name] = section
        return res

    @property
    def somatic(self) -> list[NeuronSection]:
        return list(public_hoc_cell(self.cell).somatic)

    @property
    def basal(self) -> list[NeuronSection]:
        return list(public_hoc_cell(self.cell).basal)

    @property
    def apical(self) -> list[NeuronSection]:
        return list(public_hoc_cell(self.cell).apical)

    @property
    def axonal(self) -> list[NeuronSection]:
        return list(public_hoc_cell(self.cell).axonal)

    @property
    def sections(self) -> SectionMapping:
        return self._extract_sections(public_hoc_cell(self.cell).all)

    def __repr__(self) -> str:
        base_info = f"Cell Object: {super().__repr__()}"
        hoc_info = f"NEURON ID: {self.template_id}"
        return f"{base_info}.\n{hoc_info}."

    def connect_to_circuit(self, sonata_proxy: SonataProxy) -> None:
        """Connect this cell to a circuit via sonata proxy."""
        self.sonata_proxy = sonata_proxy

    def re_init_rng(self) -> None:
        """Reinitialize the random number generator for stochastic channels."""
        if not self.is_made_passive:
            self.cell.re_init_rng()

    def get_psection(self, section_id: int | str) -> PSection:
        """Return a python section with the specified section id."""
        self._init_psections()
        if isinstance(section_id, int):
            return self.psections[section_id]
        elif isinstance(section_id, str):
            return self.secname_to_psection[section_id]
        else:
            raise BluecellulabError(
                f"Section id must be an int or a str, not {type(section_id)}"
            )

    def make_passive(self) -> None:
        """Make the cell passive by deactivating all the active channels."""
        for section in self.sections.values():
            mech_names = set()
            for seg in section:
                for mech in seg:
                    mech_names.add(mech.name())
            for mech_name in mech_names:
                if mech_name not in ["k_ion", "na_ion", "ca_ion", "pas",
                                     "ttx_ion"]:
                    neuron.h('uninsert %s' % mech_name, sec=section)
        self.is_made_passive = True

    def enable_ttx(self) -> None:
        """Add TTX to the environment (i.e. block the Na channels).

        Enable TTX by inserting TTXDynamicsSwitch and setting ttxo to
        1.0
        """
        if hasattr(public_hoc_cell(self.cell), 'enable_ttx'):
            public_hoc_cell(self.cell).enable_ttx()
        else:
            self._default_enable_ttx()

    def disable_ttx(self) -> None:
        """Remove TTX from the environment (i.e. unblock the Na channels).

        Disable TTX by inserting TTXDynamicsSwitch and setting ttxo to
        1e-14
        """
        if hasattr(public_hoc_cell(self.cell), 'disable_ttx'):
            public_hoc_cell(self.cell).disable_ttx()
        else:
            self._default_disable_ttx()

    @property
    def ttx_enabled(self):
        return getattr(self, "_ttx_enabled", False)

    def _default_enable_ttx(self) -> None:
        """Default enable_ttx implementation."""
        for section in self.sections.values():
            if not neuron.h.ismembrane("TTXDynamicsSwitch"):
                section.insert('TTXDynamicsSwitch')
            section.ttxo_level_TTXDynamicsSwitch = 1.0

    def _default_disable_ttx(self) -> None:
        """Default disable_ttx implementation."""
        for section in self.sections.values():
            if not neuron.h.ismembrane("TTXDynamicsSwitch"):
                section.insert('TTXDynamicsSwitch')
            section.ttxo_level_TTXDynamicsSwitch = 1e-14

    def area(self) -> float:
        """The total surface area of the cell."""
        area = 0.0
        for section in self.sections.values():
            x_s = np.arange(1.0 / (2 * section.nseg), 1.0,
                            1.0 / (section.nseg))
            for x in x_s:
                area += neuron.h.area(x, sec=section)
            # for segment in section:
            #    area += neuron.h.area(segment.x, sec=section)
        return area

    def add_recording(self, var_name: str, dt: Optional[float] = None) -> None:
        """Add a recording to the cell.

        Args:
            var_name: Variable to be recorded.
            dt: Recording time step. If not provided, the recording step will
            default to the simulator's time step.
        """
        recording = neuron.h.Vector()
        if dt:
            # This float_epsilon stuff is some magic from M. Hines to make
            # the time points fall exactly on the dts
            recording.record(
                eval_neuron(var_name, self=self, neuron=neuron),
                self.get_precise_record_dt(dt),
            )
        else:
            recording.record(eval_neuron(var_name, self=self, neuron=neuron))
        self.recordings[var_name] = recording

    @staticmethod
    def get_precise_record_dt(dt: float) -> float:
        """Get a more precise record_dt to make time points faill on dts."""
        return (1.0 + neuron.h.float_epsilon) / (1.0 / dt)

    def add_recordings(self, var_names: list[str], dt: Optional[float] = None) -> None:
        """Add a list of recordings to the cell.

        Args:
            var_names: Variables to be recorded.
            dt: Recording time step. If not provided, the recording step will
            default to the simulator's time step.
        """
        for var_name in var_names:
            self.add_recording(var_name, dt)

    def add_ais_recording(self, dt: Optional[float] = None) -> None:
        """Adds recording to AIS."""
        self.add_recording("self.axonal[1](0.5)._ref_v", dt=dt)

    @deprecated("Use add_variable_recording('v', ...) instead.")
    def add_voltage_recording(
        self, section: Optional[NeuronSection] = None, segx: float = 0.5, dt: Optional[float] = None
    ) -> None:
        """Add a voltage recording to a certain section at a given segment
        (segx).

        Args:
            section: Section to record from (Neuron section pointer).
            segx: Segment x coordinate. Specify a value between 0 and 1.
                  0 is typically the end closest to the soma, 1 is the distal end.
            dt: Recording time step. If not provided, the recording step will
                default to the simulator's time step.
        """
        if section is None:
            section = self.soma
        var_name = section_to_voltage_recording_str(section, segx)
        self.add_recording(var_name, dt)

    @deprecated("Use get_variable_recording('v', ...) instead.")
    def get_voltage_recording(
        self, section: Optional[NeuronSection] = None, segx: float = 0.5
    ) -> np.ndarray:
        """Get a voltage recording for a certain section at a given segment
        (segx).

        Args:
            section: Section to record from (Neuron section pointer).
            segx: Segment x coordinate. Specify a value between 0 and 1.
                  0 is typically the end closest to the soma, 1 is the distal end.

        Returns:
            A NumPy array containing the voltage recording values.

        Raises:
            BluecellulabError: If voltage recording was not added previously using add_voltage_recording.
        """
        if section is None:
            section = self.soma
        recording_name = section_to_voltage_recording_str(section, segx)
        if recording_name in self.recordings:
            return self.get_recording(recording_name)
        else:
            raise BluecellulabError(
                f"get_voltage_recording: Voltage recording {recording_name}"
                " was not added previously using add_voltage_recording"
            )

    def add_allsections_voltagerecordings(self):
        """Add a voltage recording to every section of the cell."""
        for section in self.sections.values():
            self.add_voltage_recording(section, dt=self.record_dt)

    def get_allsections_voltagerecordings(self) -> dict[str, np.ndarray]:
        """Get all the voltage recordings from all the sections."""
        all_section_voltages = {}
        for section in self.sections.values():
            recording = self.get_voltage_recording(section)
            all_section_voltages[section.name()] = recording
        return all_section_voltages

    def get_recording(self, var_name: str) -> np.ndarray:
        """Get recorded values."""
        try:
            res = np.array(self.recordings[var_name].to_python())
        except KeyError as e:
            raise ValueError(f"No recording for '{var_name}' was found.") from e
        return res

    def add_replay_synapse(self,
                           synapse_id: SynapseID,
                           syn_description: pd.Series,
                           connection_modifiers: dict,
                           condition_parameters: Conditions,
                           popids: tuple[int, int],
                           extracellular_calcium: float | None) -> None:
        """Add synapse based on the syn_description to the cell."""
        synapse = SynapseFactory.create_synapse(
            cell=self,
            syn_id=synapse_id,
            syn_description=syn_description,
            condition_parameters=condition_parameters,
            popids=popids,
            extracellular_calcium=extracellular_calcium,
            connection_modifiers=connection_modifiers)

        self.synapses[synapse_id] = synapse

        logger.debug(f'Added synapse to cell {self.cell_id.id}')

    def add_replay_delayed_weight(
        self, sid: tuple[str, int], delay: float, weight: float
    ) -> None:
        """Add a synaptic weight for sid that will be set with a time delay."""
        self.delayed_weights.put((delay, (sid, weight)))

    def pre_gids(self) -> list[int]:
        """Get the list of unique gids of cells that connect to this cell.

        Returns:
            A list of gids of cells that connect to this cell.
        """
        pre_gids = {self.synapses[syn_id].pre_gid for syn_id in self.synapses}
        return list(pre_gids)

    def pre_gid_synapse_ids(self, pre_gid: int) -> list[SynapseID]:
        """List of synapse_ids of synapses a cell uses to connect to this cell.

        Args:
            pre_gid: gid of the presynaptic cell.

        Returns:
            synapse_id's that connect the presynaptic cell with this cell.
        """
        syn_id_list = []
        for syn_id in self.synapses:
            if self.synapses[syn_id].pre_gid == pre_gid:
                syn_id_list.append(syn_id)
        return syn_id_list

    def create_netcon_spikedetector(self, target: HocObjectType, location: str, threshold: float = -30.0) -> HocObjectType:
        """Add and return a spikedetector.

        This function creates a NetCon object that detects spikes at a specific
        location in the current cell and connects to the provided target point process.
        The location can be specified as a predefined site ('soma' or 'AIS') or as a
        custom location in the format `section[index](position)`. Custom locations
        allow fine-grained control of the spike detection site within the cell's sections.

        Args:
            target: A NEURON point process object (e.g., synapse) that the NetCon connects to.
            location: The spike detection location. Acceptable formats include:

                - `"soma"`: Detect spikes in the soma section at the distal end.

                - `"AIS"`: Detect spikes in the axon initial segment at the midpoint.

                - `"section[index](position)"`: Custom location specifying:

                  - `section`: The name of the section (e.g., 'soma', 'axon').
                  - `[index]` (optional): Segment index within a section array (e.g., 'soma[0]').
                  - `(position)` (optional): Normalized position along the section length (0 to 1).
                    Defaults to 0.5 if not provided.

            threshold: The voltage threshold for spike detection (default: -30.0 mV).

        Returns:
            A NEURON `NetCon` object configured for spike detection at the specified location.

        Raises:
            ValueError: If:

                - The `location` is not 'soma', 'AIS', or a valid custom format.

                - The specified section or segment index does not exist.

                - The position is out of bounds (e.g., negative or greater than 1.0).
        """

        if location == "soma":
            sec = public_hoc_cell(self.cell).soma[0]
            source = sec(1)._ref_v
        elif location == "AIS":
            sec = public_hoc_cell(self.cell).axon[1]
            source = sec(0.5)._ref_v
        else:
            # Parse custom location (e.g., 'soma[0](0.3)')
            pattern = r'^([a-zA-Z_]+)(?:\[(\d+)\])?(?:\((-?\d+\.\d+)\))?$'
            match = re.search(pattern, location)

            # Extract the value if a match is found
            if match:
                section_name = match.group(1)
                segment_index = match.group(2)
                pos = match.group(3)
                if pos is None:
                    pos = 0.5
                else:
                    pos = float(pos)

            else:
                raise ValueError(f"Invalid location format: {location}")

            try:
                # Handle section arrays (e.g., soma[0])
                if segment_index is not None:
                    sec = getattr(public_hoc_cell(self.cell), section_name)[int(segment_index)]
                else:
                    sec = getattr(public_hoc_cell(self.cell), section_name)

                source = sec(pos)._ref_v
            except (AttributeError, ValueError, IndexError) as e:
                raise ValueError(f"Invalid spike detection location: {location}") from e

        netcon = neuron.h.NetCon(source, target, sec=sec)
        netcon.threshold = threshold
        return netcon

    def start_recording_spikes(self, target: HocObjectType, location: str, threshold: float = -30) -> None:
        """Start recording spikes in the current cell.

        Args:
            target: target point process
            location: the spike detection location
            threshold: spike detection threshold
        """
        nc = self.create_netcon_spikedetector(target, location, threshold)
        spike_vec = neuron.h.Vector()
        nc.record(spike_vec)
        self.recordings[f"spike_detector_{location}_{threshold}"] = spike_vec

    def is_recording_spikes(self, location: str, threshold: float) -> bool:
        key = f"spike_detector_{location}_{threshold}"
        return key in self.recordings

    def get_recorded_spikes(self, location: str, threshold: float = -30) -> list[float]:
        """Get recorded spikes in the current cell.

        Args:
            location: the spike detection location
            threshold: spike detection threshold

        Returns: recorded spikes
        """
        result = self.recordings[f"spike_detector_{location}_{threshold}"]
        return result.to_python()

    def add_replay_minis(self,
                         synapse_id: SynapseID,
                         syn_description: pd.Series,
                         connection_modifiers: dict,
                         popids: tuple[int, int],
                         mini_frequencies: tuple[float | None, float | None]) -> None:
        """Add minis from the replay."""
        source_popid, target_popid = popids

        sid = synapse_id[1]

        weight = syn_description[SynapseProperty.G_SYNX]
        # numpy int to int
        post_sec_id = int(syn_description[SynapseProperty.POST_SECTION_ID])

        weight_scalar = connection_modifiers.get('Weight', 1.0)
        exc_mini_frequency, inh_mini_frequency = mini_frequencies \
            if mini_frequencies is not None else (None, None)

        synapse = self.synapses[synapse_id]

        # SpontMinis in sim config takes precedence of values in nodes file
        if 'SpontMinis' in connection_modifiers:
            spont_minis_rate = connection_modifiers['SpontMinis']
        elif synapse.mech_name in ["GluSynapse", "ProbAMPANMDA_EMS"]:
            spont_minis_rate = exc_mini_frequency
        else:
            spont_minis_rate = inh_mini_frequency

        if spont_minis_rate is not None and spont_minis_rate > 0:
            synapse_hoc_args = SynapseFactory.determine_synapse_location(
                syn_description, self
            )
            # add the *minis*: spontaneous synaptic events
            self.ips[synapse_id] = neuron.h.\
                InhPoissonStim(synapse_hoc_args.location, sec=synapse_hoc_args.section)

            self.syn_mini_netcons[synapse_id] = neuron.h.\
                NetCon(self.ips[synapse_id], synapse.hsynapse, sec=synapse_hoc_args.section)
            self.syn_mini_netcons[synapse_id].delay = 0.1
            self.syn_mini_netcons[synapse_id].weight[0] = weight * weight_scalar
            # set netcon type
            nc_param_name = f'nc_type_param_{synapse.hsynapse}'.split('[')[0]
            if hasattr(neuron.h, nc_param_name):
                nc_type_param = int(getattr(neuron.h, nc_param_name))
                # NC_SPONTMINI
                self.syn_mini_netcons[synapse_id].weight[nc_type_param] = 1

            rng_settings = RNGSettings.get_instance()
            if rng_settings.mode == 'Random123':
                seed2 = source_popid * 65536 + target_popid \
                    + rng_settings.minis_seed
                self.ips[synapse_id].setRNGs(
                    sid + 200,
                    self.cell_id.id + 250,
                    seed2 + 300,
                    sid + 200,
                    self.cell_id.id + 250,
                    seed2 + 350)
            else:
                exprng = neuron.h.Random()
                self.persistent.append(exprng)

                uniformrng = neuron.h.Random()
                self.persistent.append(uniformrng)

                base_seed = rng_settings.base_seed
                if rng_settings.mode == 'Compatibility':
                    exp_seed1 = sid * 100000 + 200
                    exp_seed2 = self.cell_id.id + 250 + base_seed + \
                        rng_settings.minis_seed
                    uniform_seed1 = sid * 100000 + 300
                    uniform_seed2 = self.cell_id.id + 250 + base_seed + \
                        rng_settings.minis_seed
                elif rng_settings.mode == "UpdatedMCell":
                    exp_seed1 = sid * 1000 + 200
                    exp_seed2 = source_popid * 16777216 + self.cell_id.id + 250 + \
                        base_seed + \
                        rng_settings.minis_seed
                    uniform_seed1 = sid * 1000 + 300
                    uniform_seed2 = source_popid * 16777216 + self.cell_id.id + 250 \
                        + base_seed + \
                        rng_settings.minis_seed
                else:
                    raise ValueError(
                        f"Cell: Unknown rng mode: {rng_settings.mode}")

                exprng.MCellRan4(exp_seed1, exp_seed2)
                exprng.negexp(1.0)

                uniformrng.MCellRan4(uniform_seed1, uniform_seed2)
                uniformrng.uniform(0.0, 1.0)

                self.ips[synapse_id].setRNGs(exprng, uniformrng)

            tbins_vec = neuron.h.Vector(1)
            tbins_vec.x[0] = 0.0
            rate_vec = neuron.h.Vector(1)
            rate_vec.x[0] = spont_minis_rate
            self.persistent.append(tbins_vec)
            self.persistent.append(rate_vec)
            self.ips[synapse_id].setTbins(tbins_vec)
            self.ips[synapse_id].setRate(rate_vec)

    def get_childrensections(self, parentsection: HocObjectType) -> list[HocObjectType]:
        """Get the children section of a neuron section."""
        number_children = neuron.h.SectionRef(sec=parentsection).nchild()
        children = []
        for index in range(int(number_children)):
            children.append(neuron.h.SectionRef(sec=self.soma).child[index])
        return children

    @staticmethod
    def get_parentsection(childsection: HocObjectType) -> HocObjectType:
        """Get the parent section of a neuron section."""
        return neuron.h.SectionRef(sec=childsection).parent

    def addAxialCurrentRecordings(self, section):
        """Record all the axial current flowing in and out of the section."""
        secname = neuron.h.secname(sec=section)
        self.add_recording(secname)
        for child in self.get_childrensections(section):
            self.add_recording(child)
        self.get_parentsection(section)

    def getAxialCurrentRecording(self, section):
        """Return the axial current recording."""
        secname = neuron.h.secname(sec=section)
        for child in self.get_childrensections(section):
            self.get_recording(secname)
            self.get_recording(child)

    def somatic_branches(self) -> None:
        """Show the index numbers."""
        nchild = neuron.h.SectionRef(sec=self.soma).nchild()
        for index in range(int(nchild)):
            secname = neuron.h.secname(sec=neuron.h.SectionRef(
                sec=self.soma).child[index])
            if "axon" not in secname:
                if "dend" in secname:
                    dendnumber = int(
                        secname.split("dend")[1].split("[")[1].split("]")[0])
                    secnumber = int(public_hoc_cell(self.cell).nSecAxonalOrig +
                                    public_hoc_cell(self.cell).nSecSoma + dendnumber)
                elif "apic" in secname:
                    apicnumber = int(secname.split(
                        "apic")[1].split("[")[1].split("]")[0])
                    secnumber = int(public_hoc_cell(self.cell).nSecAxonalOrig +
                                    public_hoc_cell(self.cell).nSecSoma +
                                    public_hoc_cell(self.cell).nSecBasal + apicnumber)
                    logger.info((apicnumber, secnumber))
                else:
                    raise BluecellulabError(
                        f"somaticbranches: No apic or dend found in section {secname}"
                    )

    @staticmethod
    @deprecated("Use bluecellulab.cell.section_distance.EuclideanSectionDistance instead.")
    def euclid_section_distance(
            hsection1=None,
            hsection2=None,
            location1=None,
            location2=None,
            projection=None):
        """Calculate euclidian distance between positions on two sections Uses
        bluecellulab.cell.section_distance.EuclideanSectionDistance.

        Parameters
        ----------

        hsection1 : hoc section
                    First section
        hsection2 : hoc section
                    Second section
        location1 : float
                    range x along hsection1
        location2 : float
                    range x along hsection2
        projection : string
                     planes to project on, e.g. 'xy'
        """
        dist = EuclideanSectionDistance()
        return dist(hsection1, hsection2, location1, location2, projection)

    def apical_trunk(self):
        """Return the apical trunk of the cell."""
        if len(self.apical) == 0:
            return []
        else:
            apicaltrunk = []
            max_diam_section = self.apical[0]
            while True:
                apicaltrunk.append(max_diam_section)

                children = [
                    neuron.h.SectionRef(sec=max_diam_section).child[index]
                    for index in range(int(neuron.h.SectionRef(
                        sec=max_diam_section).nchild()))]
                if len(children) == 0:
                    break
                maxdiam = 0
                for child in children:
                    if child.diam > maxdiam:
                        max_diam_section = child
                        maxdiam = child.diam
            return apicaltrunk

    def get_time(self) -> np.ndarray:
        """Get the time vector."""
        return self.get_recording('neuron.h._ref_t')

    def get_soma_voltage(self) -> np.ndarray:
        """Get a vector of the soma voltage."""
        return self.get_recording('self.soma(0.5)._ref_v')

    def get_ais_voltage(self) -> np.ndarray:
        """Get a vector of AIS voltage."""
        return self.get_recording('self.axonal[1](0.5)._ref_v')

    def add_variable_recording(
        self,
        variable: str,
        section: Optional[NeuronSection] = None,
        segx: float = 0.5,
        dt: Optional[float] = None
    ) -> None:
        """Add a recording of any NEURON RANGE variable (e.g., gna, gk, ina)
        from a given section and segment.

        Args:
            variable: The NEURON variable name to record (e.g., "gna").
            section: The section to record from (defaults to soma).
            segx: Segment position between 0 and 1.
            dt: Optional recording time step.
        """

        if section is None:
            section = self.soma

        # validate before constructing the string
        seg = section(segx)
        if "." in variable:
            mech, var = variable.split(".", 1)
            mobj = getattr(seg, mech, None)
            if mobj is None or not hasattr(mobj, f"_ref_{var}"):
                raise AttributeError(
                    f"'{variable}' not recordable at {section.name()}({segx}). "
                    f"Mechanisms here: {list(section.psection()['density_mechs'].keys())}"
                )
        else:
            if not hasattr(seg, f"_ref_{variable}"):
                raise AttributeError(
                    f"'{variable}' not recordable at {section.name()}({segx}). "
                    f"(Top-level vars are typically v/ina/ik/ica)"
                )

        var_name = section_to_variable_recording_str(section, segx, variable)
        self.add_recording(var_name, dt)

    def get_variable_recording(
        self, variable: str, section: Optional[NeuronSection], segx: float
    ) -> np.ndarray:
        """Get a recording of any variable recorded from a section and segment.

        Args:
            variable: The name of the recorded variable (e.g., 'v', 'gna').
            section: The NEURON section object.
            segx: Segment location from 0 to 1.

        Returns:
            NumPy array of recorded values.

        Raises:
            ValueError: If the recording is not found.
        """
        if section is None:
            section = self.soma
        recording_name = section_to_variable_recording_str(section, segx, variable)
        return self.get_recording(recording_name)

    @property
    def n_segments(self) -> int:
        """Get the number of segments in the cell."""
        return sum(section.nseg for section in self.sections.values())

    def add_synapse_replay(
        self, stimulus: SynapseReplay, spike_threshold: float, spike_location: str
    ) -> None:
        """Adds the synapse spike replay to the cell if the synapse is
        connected to that cell."""
        if self.sonata_proxy is None:
            raise BluecellulabError("Cell: add_synapse_replay requires a sonata proxy.")

        file_path = Path(stimulus.spike_file).expanduser()
        if not file_path.is_absolute():
            config_dir = stimulus.config_dir
            if config_dir is not None:
                file_path = Path(config_dir) / file_path

        file_path = file_path.resolve()

        if not file_path.exists():
            raise FileNotFoundError(f"Spike file not found: {str(file_path)}")
        synapse_spikes: dict = get_synapse_replay_spikes(str(file_path))
        for synapse_id, synapse in self.synapses.items():
            source_population = synapse.syn_description["source_population_name"]
            pre_gid = CellId(
                source_population, int(synapse.syn_description[SynapseProperty.PRE_GID])
            )
            if pre_gid.id in synapse_spikes:
                spikes_of_interest = synapse_spikes[pre_gid.id]
                # filter spikes of interest >=stimulus.delay, <=stimulus.duration
                spikes_of_interest = spikes_of_interest[
                    (spikes_of_interest >= stimulus.delay)
                    & (spikes_of_interest <= stimulus.duration)
                ]
                connection = bluecellulab.Connection(
                    synapse,
                    pre_spiketrain=spikes_of_interest,
                    pre_cell=None,
                    stim_dt=self.record_dt,
                    spike_threshold=spike_threshold,
                    spike_location=spike_location,
                )
                logger.debug(
                    f"Added synapse replay from {pre_gid} to {self.cell_id.id}, {synapse_id}"
                )

                self.connections[synapse_id] = connection

    @property
    def info_dict(self):
        """Return a dictionary with all the information of this cell."""
        return {
            'synapses': {
                sid: synapse.info_dict for sid, synapse in self.synapses.items()
            },
            'connections': {
                sid: connection.info_dict for sid, connection in self.connections.items()
            }
        }

    def delete(self):
        """Delete the cell."""
        self.delete_plottable()
        if hasattr(self, 'cell') and self.cell is not None:
            if public_hoc_cell(self.cell) is not None and hasattr(public_hoc_cell(self.cell), 'clear'):
                public_hoc_cell(self.cell).clear()

            self.connections = None
            self.synapses = None

        if hasattr(self, 'recordings'):
            for recording in self.recordings:
                del recording

        if hasattr(self, 'persistent'):
            for persistent_object in self.persistent:
                del persistent_object

    def __del__(self):
        self.delete()

    def get_section(self, section_name: str) -> NeuronSection:
        """Return a single, fully specified NEURON section (e.g., 'soma[0]',
        'dend[3]').

        Raises:
            ValueError or TypeError if the section is not found or invalid.
        """
        if section_name in self.sections:
            section = self.sections[section_name]
            if hasattr(section, "nseg"):
                return section
            raise TypeError(f"'{section_name}' exists but is not a NEURON section.")

        available = ", ".join(self.sections.keys())
        raise ValueError(f"Section '{section_name}' not found. Available: [{available}]")

    def get_sections(self, section_name: str) -> List[NeuronSection]:
        """Return a list of NEURON sections.

        If the section name is a fully specified one (e.g., 'dend[3]'), return it as a list of one.
        If the section name is a base name (e.g., 'dend'), return all matching sections like 'dend[0]', 'dend[1]', etc.

        Raises:
            ValueError if no valid sections are found.
        """
        # Try to interpret as fully qualified section name
        try:
            return [self.get_section(section_name)]
        except ValueError:
            pass  # Not a precise match; try prefix match

        # Fallback to prefix-based match (e.g., 'dend' → 'dend[0]', 'dend[1]', ...)
        matched = [
            section for name, section in self.sections.items()
            if name.startswith(f"{section_name}[")
        ]
        if matched:
            return matched

        available = ", ".join(self.sections.keys())
        raise ValueError(f"Section '{section_name}' not found. Available: [{available}]")

    def get_section_by_id(self, section_id: int) -> NeuronSection:
        """Return NEURON section by global section index (LibSONATA
        ordering)."""
        if not self.psections:
            self._init_psections()

        try:
            return self.psections[int(section_id)].hsection
        except KeyError:
            raise IndexError(f"Section ID {section_id} is out of range for cell {self.cell_id.id}")

    def resolve_segments_from_compartment_set(self, node_id, compartment_nodes) -> List[Tuple[NeuronSection, str, float]]:
        """Resolve segments for a cell using a predefined compartment node
        list.

        Supports both LibSONATA format ([node_id, section_id, seg]) and
        name-based format ([node_id, section_name, seg]).
        """
        result = []
        for n_id, sec_ref, seg in compartment_nodes:
            if n_id != node_id:
                continue

            if isinstance(sec_ref, str):
                # Name-based: e.g., "dend[5]"
                section = self.get_section(sec_ref)
                sec_name = section.name().split(".")[-1]
            elif isinstance(sec_ref, int):
                # ID-based: resolve by section index
                try:
                    section = self.get_section_by_id(sec_ref)
                    sec_name = section.name().split(".")[-1]
                except AttributeError:
                    raise ValueError(f"Cell object does not support section lookup by index: {sec_ref}")
            else:
                raise TypeError(f"Unsupported section reference type: {type(sec_ref)}")

            result.append((section, sec_name, seg))
        return result

    def resolve_segments_from_config(self, report_cfg) -> List[Tuple[NeuronSection, str, float]]:
        """Resolve segments from NEURON sections based on config."""
        compartment = report_cfg.get("compartments", "center")
        if compartment not in {"center", "all"}:
            raise ValueError(
                f"Unsupported 'compartments' value '{compartment}' — must be 'center' or 'all'."
            )

        section_name = report_cfg.get("sections", "soma")
        sections = self.get_sections(section_name)

        targets = []
        for sec in sections:
            sec_name = sec.name().split(".")[-1]
            if compartment == "center":
                targets.append((sec, sec_name, 0.5))
            elif compartment == "all":
                for seg in sec:
                    targets.append((sec, sec_name, seg.x))
        return targets

    def configure_recording(self, recording_sites, variable_name, report_name):
        """Configure recording of a variable on a single cell.

        This function sets up the recording of the specified variable (e.g., membrane voltage)
        in the target cell, for each resolved segment.

        Parameters
        ----------
        cell : Any
            The cell object on which to configure recordings.

        recording_sites : list of tuples
            List of tuples (section, section_name, segment) where:
            - section is the section object in the cell.
            - section_name is the name of the section.
            - segment is the Neuron segment index (0-1).

        variable_name : str
            The name of the variable to record (e.g., "v" for membrane voltage).

        report_name : str
            The name of the report (used in logging).
        """
        node_id = self.cell_id.id

        for sec, sec_name, seg in recording_sites:
            try:
                self.add_variable_recording(variable=variable_name, section=sec, segx=seg)
                logger.info(
                    f"Recording '{variable_name}' at {sec_name}({seg}) on GID {node_id} for report '{report_name}'"
                )
            except AttributeError:
                logger.warning(
                    f"Recording for variable '{variable_name}' is not implemented in Cell."
                )
                return
            except Exception as e:
                logger.warning(
                    f"Failed to record '{variable_name}' at {sec_name}({seg}) on GID {node_id} for report '{report_name}': {e}"
                )

    def add_currents_recordings(
        self,
        section,
        segx: float = 0.5,
        *,
        include_nonspecific: bool = True,
        include_point_processes: bool = False,
        dt: float | None = None,
    ) -> list[str]:
        """Record all available currents (ionic + optionally nonspecific) at
        (section, segx)."""

        # discover what’s available at this site
        available = currents_vars(section)
        chosen: list[str] = []

        for name, meta in available.items():
            kind = meta.get("kind")

            if kind == "ionic_current":
                self.add_variable_recording(name, section=section, segx=segx, dt=dt)
                chosen.append(name)

            elif kind == "nonspecific_current":
                if not include_nonspecific:
                    continue
                # density-mech nonspecific currents
                self.add_variable_recording(name, section=section, segx=segx, dt=dt)
                chosen.append(name)

            elif kind == "point_process_current":
                if not include_point_processes:
                    continue
                # point process nonspecific currents
                self.add_variable_recording(name, section=section, segx=segx, dt=dt)
                chosen.append(name)

        return chosen
