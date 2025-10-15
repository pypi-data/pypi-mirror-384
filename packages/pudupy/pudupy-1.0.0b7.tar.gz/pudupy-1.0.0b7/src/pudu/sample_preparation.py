from opentrons import protocol_api
from typing import List, Union, Optional, Tuple
from abc import ABC, abstractmethod
import math
from pudu.utils import colors


class SamplePreparation(ABC):
    """
    Abstract base class for all Sample Preparation protocols with shared functionality.
    """

    def __init__(self,
                 test_labware: str = 'corning_96_wellplate_360ul_flat',
                 test_position: str = '2',
                 aspiration_rate: float = 0.5,
                 dispense_rate: float = 1.0,
                 tiprack_labware: str = 'opentrons_96_filtertiprack_200ul',
                 tiprack_position: str = '9',
                 starting_tip: Optional[str] = None,
                 pipette: str = 'p300_single_gen2',
                 pipette_position: str = 'right',
                 use_temperature_module: bool = False,
                 temperature: int = 4,
                 **kwargs):
        self.test_labware = test_labware
        self.test_position = test_position
        self.aspiration_rate = aspiration_rate
        self.dispense_rate = dispense_rate
        self.tiprack_labware = tiprack_labware
        self.tiprack_position = tiprack_position
        self.starting_tip = starting_tip
        self.pipette = pipette
        self.pipette_position = pipette_position
        self.use_temperature_module = use_temperature_module
        self.temperature = temperature

        # Protocol tracking
        self.result_dict = {}
        self.liquid_tracker = {}

    @abstractmethod
    def run(self, protocol: protocol_api.ProtocolContext):
        """Abstract method that must be implemented by subclasses."""
        pass

    def _load_standard_labware(self, protocol: protocol_api.ProtocolContext):
        """Load standard labware common to all protocols."""
        tiprack = protocol.load_labware(self.tiprack_labware, self.tiprack_position)
        pipette = protocol.load_instrument(self.pipette, self.pipette_position, tip_racks=[tiprack])

        if self.starting_tip:
            pipette.starting_tip = tiprack[self.starting_tip]

        plate = protocol.load_labware(self.test_labware, self.test_position)

        return tiprack, pipette, plate

    def _load_source_labware(self, protocol: protocol_api.ProtocolContext,
                             temp_module_position: str = '1',
                             temp_module_labware: str = 'opentrons_24_aluminumblock_nest_1.5ml_snapcap',
                             tube_rack_position: str = '3',
                             tube_rack_labware: str = 'opentrons_24_tuberack_nest_1.5ml_snapcap'):
        """Load source tube labware with optional temperature control."""

        if self.use_temperature_module:
            temperature_module = protocol.load_module('Temperature Module', temp_module_position)
            source_rack = temperature_module.load_labware(temp_module_labware)
            temperature_module.set_temperature(self.temperature)
        else:
            source_rack = protocol.load_labware(tube_rack_labware, tube_rack_position)

        return source_rack

    def _create_slots(self, plate, replicates: int = 4):
        """
        Create well groupings for sample distribution.
        Flexible slot creation based on plate size and replicate requirements.
        """
        columns = plate.columns()

        middle_columns = columns[1:-1]
        edge_columns = [columns[0], columns[-1]]
        slots = []

        # All top halves of middle columns first
        slots.extend(col[:len(col) // 2] for col in middle_columns)
        # Bottom halves of middle columns
        slots.extend(col[len(col) // 2:] for col in middle_columns)
        # edge/buffer columns (both halves)
        for col in edge_columns:
            slots.extend([col[:len(col) // 2], col[len(col) // 2:]])

        return slots

    def _validate_plate_capacity(self, required_wells: int, plate):
        """Validate that plate has sufficient wells for the protocol."""
        available_wells = len(plate.wells())
        if required_wells > available_wells:
            raise ValueError(f'Protocol requires {required_wells} wells but plate only has {available_wells}')

    def _define_liquid(self, protocol: protocol_api.ProtocolContext,
                       name: str, description: str, color_index: int = 0):
        """Define and track a liquid for the protocol."""
        color = colors[color_index % len(colors)]
        liquid = protocol.define_liquid(name=name, description=description, display_color=color)
        self.liquid_tracker[name] = liquid
        return liquid


class PlateSamples(SamplePreparation):
    """
    Distributes multiple samples across a plate with replicates.
    Each sample gets distributed to a specified number of wells.
    """

    def __init__(self, samples: List[str],
                 sample_volume: float = 200,
                 sample_stock_volume: float = 1200,
                 replicates: int = 4,
                 starting_slot: int = 1,
                 temp_module_position: str = '1',
                 temp_module_labware: str = 'opentrons_24_aluminumblock_nest_1.5ml_snapcap',
                 tube_rack_position: str = '3',
                 tube_rack_labware: str = 'opentrons_24_tuberack_nest_1.5ml_snapcap',
                 **kwargs):
        super().__init__(**kwargs)
        self.samples = samples
        self.sample_volume = sample_volume
        self.sample_stock_volume = sample_stock_volume
        self.replicates = replicates
        self.starting_slot = starting_slot
        self.temp_module_position = temp_module_position
        self.temp_module_labware = temp_module_labware
        self.tube_rack_position = tube_rack_position
        self.tube_rack_labware = tube_rack_labware

        self.source_positions = {}
        self.plate_layout = {}

    def run(self, protocol: protocol_api.ProtocolContext):
        # Load labware
        tiprack, pipette, plate = self._load_standard_labware(protocol)
        source_rack = self._load_source_labware(
            protocol, self.temp_module_position, self.temp_module_labware,
            self.tube_rack_position, self.tube_rack_labware
        )

        # Create slots and validate
        slots = self._create_slots(plate, self.replicates)
        required_wells = len(self.samples) * self.replicates
        self._validate_plate_capacity(required_wells, plate)

        if len(self.samples) > len(source_rack.wells()):
            raise ValueError(
                f'Too many samples ({len(self.samples)}) for source rack ({len(source_rack.wells())} wells)')

        if len(self.samples) > len(slots[self.starting_slot - 1:]):
            raise ValueError(f'Too many samples ({len(self.samples)}) for available slots')

        # Load samples into source rack
        sample_wells = self._load_samples(protocol, source_rack)

        # Distribute samples to plate
        slot_counter = self.starting_slot - 1
        for source_well, sample in sample_wells:
            dest_wells = slots[slot_counter][:self.replicates]
            pipette.distribute(
                volume=self.sample_volume,
                source=source_well,
                dest=dest_wells,
                disposal_volume=0
            )
            self.plate_layout[sample] = [well.well_name for well in dest_wells]
            slot_counter += 1

        # Store results
        self.result_dict = {
            'source_positions': self.source_positions,
            'plate_layout': self.plate_layout
        }

        print('Sample Distribution Protocol Complete')
        print(f'Source positions: {self.source_positions}')
        print(f'Plate layout: {self.plate_layout}')

    def _load_samples(self, protocol: protocol_api.ProtocolContext, source_rack):
        """Load samples into source rack with liquid tracking."""
        sample_wells = []
        for i, sample in enumerate(self.samples):
            liquid = self._define_liquid(protocol, sample, f"Sample: {sample}", i)
            well = source_rack.wells()[i]
            well.load_liquid(liquid=liquid, volume=self.sample_stock_volume)
            self.source_positions[sample] = well.well_name
            sample_wells.append((well, sample))
        return sample_wells


class PlateWithGradient(SamplePreparation):
    """
    Creates serial dilution gradients of an inducer with a sample.
    Implements proper well-to-well serial dilution.
    """

    def __init__(self,
                 sample_name: str,
                 inducer_name: str,
                 initial_concentration: float = 1.0,
                 dilution_factor: float = 2.0,
                 dilution_steps: int = 8,
                 replicates: int = 3,
                 starting_row: str = 'A',
                 final_well_volume: float = 200,
                 initial_mix_ratio: float = 0.5,  # fraction of inducer in initial mix
                 transfer_volume: float = 100,  # volume transferred in each dilution step
                 sample_stock_volume: float = 1200,
                 inducer_stock_volume: float = 1200,
                 temp_module_position: str = '1',
                 temp_module_labware: str = 'opentrons_24_aluminumblock_nest_1.5ml_snapcap',
                 tube_rack_position: str = '3',
                 tube_rack_labware: str = 'opentrons_24_tuberack_nest_1.5ml_snapcap',
                 **kwargs):

        super().__init__(**kwargs)
        self.sample_name = sample_name
        self.inducer_name = inducer_name
        self.initial_concentration = initial_concentration
        self.dilution_factor = dilution_factor
        self.dilution_steps = dilution_steps
        self.replicates = replicates
        self.starting_row = starting_row
        self.final_well_volume = final_well_volume
        self.initial_mix_ratio = initial_mix_ratio
        self.transfer_volume = transfer_volume
        self.sample_stock_volume = sample_stock_volume
        self.inducer_stock_volume = inducer_stock_volume
        self.temp_module_position = temp_module_position
        self.temp_module_labware = temp_module_labware
        self.tube_rack_position = tube_rack_position
        self.tube_rack_labware = tube_rack_labware

        # Calculated properties
        self.concentration_series = self._calculate_concentrations()
        self.required_volumes = self._calculate_required_volumes()
        self.source_positions = {}
        self.plate_layout = {}
        self.concentration_map = {}

    def _calculate_concentrations(self) -> List[float]:
        """Calculate the concentration at each dilution step."""
        concentrations = []
        current_conc = self.initial_concentration
        for step in range(self.dilution_steps + 1):  # +1 for initial concentration
            concentrations.append(current_conc)
            current_conc = current_conc / self.dilution_factor
        return concentrations

    def _calculate_required_volumes(self) -> dict:
        """Calculate required stock volumes with safety margin."""
        # Initial mix volume per replicate
        initial_mix_volume = self.final_well_volume
        total_initial_mix = initial_mix_volume * self.replicates

        # Sample volume needed (including initial mix and pre-filling wells)
        sample_per_well = self.final_well_volume - self.transfer_volume
        sample_for_prefill = sample_per_well * self.dilution_steps * self.replicates
        sample_for_initial = total_initial_mix * (1 - self.initial_mix_ratio)
        total_sample = sample_for_prefill + sample_for_initial

        # Inducer volume needed
        inducer_for_initial = total_initial_mix * self.initial_mix_ratio
        total_inducer = inducer_for_initial

        # Add 20% safety margin and round up
        safety_factor = 1.2
        return {
            'sample': math.ceil(total_sample * safety_factor),
            'inducer': math.ceil(total_inducer * safety_factor)
        }

    def _row_letter_to_index(self, letter: str) -> int:
        """Convert row letter to 0-based index."""
        return ord(letter.upper()) - ord('A')

    def run(self, protocol: protocol_api.ProtocolContext):
        # Load labware
        tiprack, pipette, plate = self._load_standard_labware(protocol)
        source_rack = self._load_source_labware(
            protocol, self.temp_module_position, self.temp_module_labware,
            self.tube_rack_position, self.tube_rack_labware
        )

        # Validate plate capacity
        required_wells = self.replicates * (self.dilution_steps + 1)
        self._validate_plate_capacity(required_wells, plate)

        # Load stocks
        self._load_stocks(protocol, source_rack)

        # Get source wells
        sample_well = source_rack.wells()[0]
        inducer_well = source_rack.wells()[1]

        # Calculate layout
        start_row_idx = self._row_letter_to_index(self.starting_row)

        # Pre-fill wells with sample (diluent)
        self._prefill_wells(pipette, plate, sample_well, start_row_idx)

        # Create initial mixes and perform serial dilutions
        self._create_gradients(pipette, plate, sample_well, inducer_well, start_row_idx)

        # Store results
        self.result_dict = {
            'source_positions': self.source_positions,
            'plate_layout': self.plate_layout,
            'concentration_map': self.concentration_map,
            'concentration_series': self.concentration_series,
            'required_volumes': self.required_volumes
        }

        print('Serial Dilution Protocol Complete')
        print(f'Concentration series: {self.concentration_series}')
        print(f'Required volumes: {self.required_volumes}')
        print(f'Source positions: {self.source_positions}')
        print(f'Concentration map: {self.concentration_map}')

    def _load_stocks(self, protocol: protocol_api.ProtocolContext, source_rack):
        """Load sample and inducer stocks."""
        # Sample stock
        sample_liquid = self._define_liquid(protocol, self.sample_name,
                                            f"Sample: {self.sample_name}", 0)
        sample_well = source_rack.wells()[0]
        sample_well.load_liquid(liquid=sample_liquid, volume=self.sample_stock_volume)
        self.source_positions[self.sample_name] = sample_well.well_name

        # Inducer stock
        inducer_liquid = self._define_liquid(protocol, self.inducer_name,
                                             f"Inducer: {self.inducer_name}", 1)
        inducer_well = source_rack.wells()[1]
        inducer_well.load_liquid(liquid=inducer_liquid, volume=self.inducer_stock_volume)
        self.source_positions[self.inducer_name] = inducer_well.well_name

    def _prefill_wells(self, pipette, plate, sample_well, start_row_idx):
        """Pre-fill wells with sample to serve as diluent."""
        diluent_volume = self.final_well_volume - self.transfer_volume

        for rep in range(self.replicates):
            row_idx = start_row_idx + rep
            row = plate.rows()[row_idx]

            # Pre-fill wells 2 through dilution_steps+1 (skip first well for initial mix)
            dest_wells = row[1:self.dilution_steps + 1]

            pipette.distribute(
                volume=diluent_volume,
                source=sample_well,
                dest=dest_wells,
                disposal_volume=0
            )

    def _create_gradients(self, pipette, plate, sample_well, inducer_well, start_row_idx):
        """Create initial mixes and perform serial dilutions."""

        # Calculate initial mix volumes
        initial_sample_vol = self.final_well_volume * (1 - self.initial_mix_ratio)
        initial_inducer_vol = self.final_well_volume * self.initial_mix_ratio

        for rep in range(self.replicates):
            row_idx = start_row_idx + rep
            row = plate.rows()[row_idx]

            # Create initial mix in first well
            first_well = row[0]

            # Add sample to first well
            pipette.transfer(
                volume=initial_sample_vol,
                source=sample_well,
                dest=first_well,
                new_tip='always'
            )

            # Add inducer to first well and mix
            pipette.transfer(
                volume=initial_inducer_vol,
                source=inducer_well,
                dest=first_well,
                mix_after=(3, self.final_well_volume * 0.5),
                new_tip='always'
            )

            # Perform serial dilution across the row
            for step in range(self.dilution_steps):
                source_well = row[step]
                dest_well = row[step + 1]

                pipette.transfer(
                    volume=self.transfer_volume,
                    source=source_well,
                    dest=dest_well,
                    mix_after=(3, self.final_well_volume * 0.5),
                    new_tip='always'
                )

            # Record layout and concentrations for this replicate
            for step in range(self.dilution_steps + 1):
                well_name = row[step].well_name
                concentration = self.concentration_series[step]

                if f'replicate_{rep}' not in self.plate_layout:
                    self.plate_layout[f'replicate_{rep}'] = []

                self.plate_layout[f'replicate_{rep}'].append(well_name)
                self.concentration_map[well_name] = concentration
