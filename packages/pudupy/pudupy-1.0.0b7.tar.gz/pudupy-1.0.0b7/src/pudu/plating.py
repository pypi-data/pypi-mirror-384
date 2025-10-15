from typing import Optional, Dict
from pudu import colors, SmartPipette
from opentrons import protocol_api

class Plating():
    """
    Creates a protocol for automated plating of transformed bacteria

    Attributes:

    """
    def __init__(self,
                 volume_total_reaction: float = 20,
                 volume_bacteria_transfer: float = 2,
                 volume_colony: float = 4,
                 volume_lb_transfer: float = 18,
                 volume_lb: float = 10000,
                 replicates: int = 1,
                 number_dilutions: int = 2,
                 max_colonies = 192,

                 thermocycler_starting_well: int = 0,
                 # thermocycler_labware: str = 'nest_96_wellplate_100ul_pcr_full_skirt',
                 thermocycler_labware: str = 'biorad_96_wellplate_200ul_pcr',

                 small_tiprack: str = 'opentrons_96_filtertiprack_20ul',
                 small_tiprack_position: str = '9',
                 initial_small_tip: str = None,
                 large_tiprack: str = 'opentrons_96_filtertiprack_200ul',
                 large_tiprack_position: str = '1',
                 initial_large_tip:str = None,
                 small_pipette: str = 'p20_single_gen2',
                 small_pipette_position: str = 'left',
                 large_pipette: str = 'p300_single_gen2',
                 large_pipette_position: str = 'right',


                 # dilution_plate: str = 'nest_96_wellplate_200ul_flat',
                 dilution_plate: str = 'nest_96_wellplate_100ul_pcr_full_skirt',
                 dilution_plate_position1: str = '2',
                 dilution_plate_position2: str = '3',
                 # agar_plate: str = 'nunc_omnitray_96grid',
                 agar_plate: str = 'nest_96_wellplate_100ul_pcr_full_skirt',
                 agar_plate_position1: str = '5',
                 agar_plate_position2: str = '6',
                 tube_rack: str = 'opentrons_15_tuberack_falcon_15ml_conical',
                 tube_rack_position: str = '4',
                 lb_tube_position: int = 0,

                 aspiration_rate: float = 0.5,
                 dispense_rate: float = 1,
                 bacterium_locations: Dict = None):

        self.volume_total_reaction = volume_total_reaction
        self.volume_bacteria_transfer = volume_bacteria_transfer
        self.volume_colony = volume_colony
        self.volume_lb_transfer = volume_lb_transfer
        self.volume_lb = volume_lb
        self.replicates = replicates
        self.number_dilutions = number_dilutions
        self.thermocycler_starting_well = thermocycler_starting_well
        self.thermocycler_labware = thermocycler_labware
        self.small_tiprack = small_tiprack
        self.small_tiprack_position = small_tiprack_position
        self.initial_small_tip = initial_small_tip
        self.large_tiprack = large_tiprack
        self.large_tiprack_position = large_tiprack_position
        self.initial_large_tip = initial_large_tip
        self.small_pipette = small_pipette
        self.small_pipette_position = small_pipette_position
        self.large_pipette = large_pipette
        self.large_pipette_position = large_pipette_position
        self.dilution_plate = dilution_plate
        self.dilution_plate_position1 = dilution_plate_position1
        self.dilution_plate_position2 = dilution_plate_position2
        self.agar_plate = agar_plate
        self.agar_plate_position1 = agar_plate_position1
        self.agar_plate_position2 = agar_plate_position2
        self.tube_rack = tube_rack
        self.tube_rack_position = tube_rack_position
        self.lb_tube_position = lb_tube_position
        self.aspiration_rate = aspiration_rate
        self.dispense_rate = dispense_rate
        self.bacterium_locations = bacterium_locations
        self.number_constructs = len(bacterium_locations)
        self.total_colonies = self.number_constructs * self.number_dilutions * self.replicates
        self.max_colonies = max_colonies
        if self.total_colonies > self.max_colonies:
            raise ValueError(f"Protocol only supports a max of {self.max_colonies} colonies")
        if self.replicates > 8:
            raise ValueError("Protocol only supports a max of 8 replicates")
        if self.number_dilutions > 2:
            raise ValueError("Protocol currently supports a max of 2 dilutions")

    def calculate_plate_layout(self,protocol, plate1, plate2=None):
        """
        Calculate the layout for colonies on plates with dynamic buffer between dilutions
        Returns: dict with plate assignments and well positions
        """
        colonies_per_dilution = self.number_constructs * self.replicates

        layout =  {
            'dilution_1': {'plate': 1, 'wells':[]},
            'dilution_2': {'plate': 1, 'wells':[]} if self.number_dilutions ==2 else None
        }

        #Check if we need two plates
        if self.number_dilutions ==2 and colonies_per_dilution > 48:
            if plate2 is None:
                raise ValueError("Two plates required but plate2 not provided")
            #Each Dilution gets its own plate
            layout['dilution_1']['wells'] = plate1.wells()[:colonies_per_dilution]
            layout['dilution_2']['plate'] = 2
            layout['dilution_2']['wells'] = plate2.wells()[:colonies_per_dilution]
            protocol.comment(f"Using 2 plates: {colonies_per_dilution} colonies per dilution exceeds single plate capacity")
        elif self.number_dilutions ==2 and colonies_per_dilution <= 48:
            #Both Dilutions Fit On One Plate
            first_half = plate1.wells()[:colonies_per_dilution]
            second_half = plate1.wells()[48:48+colonies_per_dilution]
            layout['dilution_1']['wells'] = first_half
            layout['dilution_2']['wells'] = second_half
            protocol.comment(f"Using only one {plate1}: {colonies_per_dilution} colonies on each half")
        else:
            #Single dilution
            layout['dilution_1']['wells'] = plate1.wells()[:colonies_per_dilution]
        return layout

    def run(self, protocol: protocol_api.ProtocolContext):
        #Labware
        #Load the thermocycler module, its default location is on slots 7, 8, 10 and 11
        thermocycler = protocol.load_module('thermocyclerModuleV1')
        thermocycler_plate = thermocycler.load_labware(self.thermocycler_labware)
        #Load the tipracks
        small_tiprack = protocol.load_labware(self.small_tiprack, self.small_tiprack_position)
        large_tiprack = protocol.load_labware(self.large_tiprack, self.large_tiprack_position)
        #Load the pipettes
        small_pipette = protocol.load_instrument(self.small_pipette, self.small_pipette_position, tip_racks=[small_tiprack])
        if self.initial_small_tip:
            small_pipette.starting_tip = small_tiprack[self.initial_small_tip]
        large_pipette = protocol.load_instrument(self.large_pipette, self.large_pipette_position, tip_racks=[large_tiprack])
        if self.initial_large_tip:
            large_pipette.starting_tip = large_tiprack[self.initial_large_tip]
        #SmartPipette Wrapper to avoid dunking into the LB
        smart_pipette = SmartPipette(large_pipette,protocol)
        #Load the tube rack
        tube_rack = protocol.load_labware(self.tube_rack, self.tube_rack_position)
        lb_tube = tube_rack.wells()[self.lb_tube_position]
        #load liquids
        liquid_broth = protocol.define_liquid(
            name="liquid_broth",
            description="Liquid broth for dilutions",
            display_color="#D2B48C"
        )
        lb_tube.load_liquid(liquid = liquid_broth, volume = self.volume_lb)
        # Load bacteria into thermocycler wells
        for i, (well_position, construct_names) in enumerate(self.bacterium_locations.items()):
            liquid_bacteria = protocol.define_liquid(
                name="transformed_bacteria",
                description=f"{construct_names}",
                display_color=colors[i%len(colors)]
            )
            well = thermocycler_plate[well_position]
            well.load_liquid(liquid=liquid_bacteria, volume=self.volume_total_reaction)

        # Load the dilution plates and Calculate the layout of the plates
        dilution_plate1 = protocol.load_labware(self.dilution_plate, self.dilution_plate_position1)
        if self.total_colonies <= len(dilution_plate1.wells()):
            dilution_layout = self.calculate_plate_layout(protocol, dilution_plate1)
        else:
            dilution_plate2 = protocol.load_labware(self.dilution_plate, self.dilution_plate_position2)
            dilution_layout = self.calculate_plate_layout(protocol, dilution_plate1, dilution_plate2)

        #Load the Agar plates and Calculate the layout of the plates
        agar_plate1 = protocol.load_labware(self.agar_plate, self.agar_plate_position1)
        if self.total_colonies <= len(agar_plate1.wells()):
            agar_layout = self.calculate_plate_layout(protocol, agar_plate1)
        else:
            agar_plate2 = protocol.load_labware(self.agar_plate, self.agar_plate_position2)
            agar_layout = self.calculate_plate_layout(protocol, agar_plate1, agar_plate2)


        thermocycler.set_block_temperature(4)
        thermocycler.open_lid()

        #Load the Liquid Broth into the dilution wells
        protocol.comment("\n=== Step 1: Distributing LB to dilution wells ===")
        # Get all wells that will receive LB (both dilutions if applicable)
        all_dilution_wells = dilution_layout['dilution_1']['wells'][:]
        if self.number_dilutions == 2 and dilution_layout['dilution_2']:
            all_dilution_wells.extend(dilution_layout['dilution_2']['wells'])
        # Distribute LB efficiently using built-in distribute method
        # Process in chunks of 8 wells to update aspiration height
        chunk_size = 8
        for i in range(0, len(all_dilution_wells), chunk_size):
            chunk_wells = all_dilution_wells[i:i + chunk_size]

            # Get current aspiration location before each chunk
            aspiration_location = smart_pipette.get_aspiration_location(lb_tube)
            protocol.comment(f"Distributing to wells {i + 1}-{min(i + chunk_size, len(all_dilution_wells))}")

            # Use built-in distribute method with updated aspiration location
            large_pipette.distribute(
                volume=self.volume_lb_transfer,
                source=aspiration_location,
                dest=chunk_wells,
                disposal_volume=4,  # For accuracy
                new_tip='once'  # Use one tip for the chunk
            )

            # Load liquid tracking for dilution wells
            for well in chunk_wells:
                well.load_liquid(liquid=liquid_broth, volume=self.volume_lb_transfer)

        #Transfer bacteria to first dilution and process
        protocol.comment("\n=== Step 2: Transferring bacteria and plating ===")

        well_index = 0
        for construct_position, construct_names in self.bacterium_locations.items():
            for replicate in range(self.replicates):
                # Get source and destination wells
                source_well = thermocycler_plate[construct_position]
                dilution1_well = dilution_layout['dilution_1']['wells'][well_index]
                agar1_well = agar_layout['dilution_1']['wells'][well_index]

                protocol.comment(f"\nProcessing {construct_names[0]} replicate {replicate + 1}")

                # Pick up tip once for entire workflow per well
                small_pipette.pick_up_tip()

                # Transfer bacteria to dilution plate 1
                small_pipette.aspirate(self.volume_bacteria_transfer, source_well, rate=self.aspiration_rate)
                small_pipette.dispense(self.volume_bacteria_transfer, dilution1_well, rate=self.dispense_rate)

                # Mix in dilution plate 1 (15µL mixing volume)
                small_pipette.mix(repetitions=5, volume=19, location=dilution1_well)

                # Plate on agar 1
                small_pipette.aspirate(self.volume_colony, dilution1_well, rate=self.aspiration_rate)
                small_pipette.dispense(self.volume_colony, agar1_well.top(-8), rate=self.dispense_rate)
                small_pipette.blow_out()

                # If we have a second dilution, continue with same tip
                if self.number_dilutions == 2:
                    dilution2_well = dilution_layout['dilution_2']['wells'][well_index]
                    agar2_well = agar_layout['dilution_2']['wells'][well_index]

                    # Transfer from dilution 1 to dilution 2
                    small_pipette.aspirate(self.volume_bacteria_transfer, dilution1_well, rate=self.aspiration_rate)
                    small_pipette.dispense(self.volume_bacteria_transfer, dilution2_well, rate=self.dispense_rate)

                    # Mix in dilution plate 2
                    small_pipette.mix(repetitions=5, volume=19, location=dilution2_well)

                    # Plate on agar 2
                    small_pipette.aspirate(self.volume_colony, dilution2_well, rate=self.aspiration_rate)
                    small_pipette.dispense(self.volume_colony, agar2_well.top(-8), rate=self.dispense_rate)
                    small_pipette.blow_out()

                # Drop tip after completing all transfers for this well
                small_pipette.drop_tip()

                well_index += 1

        # Close thermocycler lid
        # thermocycler.close_lid()
        # thermocycler.deactivate_block()

        protocol.comment("\n=== Plating protocol complete ===")
        protocol.comment(f"Plated {self.number_constructs} constructs with {self.replicates} replicates")
        protocol.comment(f"Created a total of {self.total_colonies} colonies")