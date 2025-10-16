import struct
import math
import pandas as pd

def binary_to_dataframe(content, aux_names=None):
    data = content

    # Header format
    header_format = '<8siiq16sIIIIIIq'
    header_size = struct.calcsize(header_format)
    header_values = struct.unpack_from(header_format, data, 0)

    # Extract header fields
    data_stride_length = header_values[5]
    auxiliary_channel_count = header_values[8]
    timestep_count = header_values[9]

    # Precompute formats and sizes
    timestep_format = '<IdIIIdddddd'
    fixed_timestep_size = struct.calcsize(timestep_format)
    bitfield_bytes_needed = math.ceil(auxiliary_channel_count / 8)

    offset = header_size
    records = []

    for i in range(timestep_count):
        block = data[offset:offset + data_stride_length]

        # Unpack fixed McbinTimestep
        ts_values = struct.unpack_from(timestep_format, block, 0)
        row = {
            'LineNumber': ts_values[0],
            'TestTimeSeconds': ts_values[1],
            'Cycle': ts_values[2],
            'StepKind': ts_values[3],
            'StepIndex': ts_values[4],
            'Voltage': ts_values[5],
            'Current': ts_values[6],
            'ChargeCapacity': ts_values[7],
            'DischargeCapacity': ts_values[8],
            'ChargeEnergy': ts_values[9],
            'DischargeEnergy': ts_values[10],
        }

        # Unpack bitfield
        bitfield_start = fixed_timestep_size
        bitfield = struct.unpack_from(f'{bitfield_bytes_needed}s', block, bitfield_start)[0]

        # Parse auxiliary values
        aux_offset = bitfield_start + bitfield_bytes_needed
        for aux_index in range(auxiliary_channel_count):
            byte_index = aux_index // 8
            bit_index = aux_index % 8
            is_present = (bitfield[byte_index] >> bit_index) & 1

            if is_present:
                aux_value = struct.unpack_from('<d', block, aux_offset)[0]
                aux_offset += 8
            else:
                aux_value = None

            # Use aux_names if available, otherwise default to Aux_{index}
            col_name = aux_names[aux_index] if aux_names and aux_index < len(aux_names) else f'Aux_{aux_index}'
            row[col_name] = aux_value

        records.append(row)
        offset += data_stride_length
    df = pd.DataFrame(records)
    step_kind_map = {
        0: 'Unknown',
        1: 'Rest',
        2: 'CcCharge',
        3: 'CvCharge',
        4: 'Charge',
        5: 'Discharge' }
    df['StepKind'] = df['StepKind'].map(step_kind_map)

        
    return df