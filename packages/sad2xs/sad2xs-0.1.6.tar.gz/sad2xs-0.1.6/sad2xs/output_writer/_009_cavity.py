"""
(Unofficial) SAD to XSuite Converter: Output Writer - Cavities
=============================================
Author(s):  John P T Salvesen
Email:      john.salvesen@cern.ch
Date:       09-10-2025
"""

################################################################################
# Import Packages
################################################################################
import xtrack as xt
import xdeps as xd
import textwrap

from ._000_helpers import *
from ..types import ConfigLike

################################################################################
# Lattice File
################################################################################
def create_cavity_lattice_file_information(
        line:       xt.Line,
        line_table: xd.table.Table,
        config:     ConfigLike) -> str:

    ########################################
    # Get information
    ########################################
    unique_cavi_names       = []
    unique_cavi_variables   = []
    for cavi in line_table.rows[line_table.element_type == 'Cavity'].name:
        parentname      = get_parentname(cavi)
        variablename    = get_variablename(cavi)
        if parentname not in unique_cavi_names:
            unique_cavi_names.append(parentname)
            unique_cavi_variables.append(variablename)

    ########################################
    # Ensure there are cavities in the line
    ########################################
    if len(unique_cavi_names) == 0:
        return ""

    ########################################
    # Create Output string
    ########################################
    output_string   = f"""
############################################################
# Cavities
############################################################"""

    ########################################
    # Create elements
    ########################################
    for cavi_name, cavi_variable_name in zip(unique_cavi_names, unique_cavi_variables):

        # Get the information
        length      = line[cavi_name].length
        frequency   = line[cavi_name].frequency
        voltage     = line[cavi_name].voltage
        lag         = line[cavi_name].lag

        cavity_generation   = f"""
env.new(
    name        = '{cavi_name}',
    parent      = xt.Cavity"""
        if length != 0:
            cavity_generation += f""",
    length      = {length}"""
        cavity_generation += f""",
    frequency   = 'freq_{cavi_variable_name} * (1 + fshift)'"""
        cavity_generation += f""",
    voltage     = 'volt_{cavi_variable_name}'"""
        cavity_generation += f""",
    lag         = 'lag_{cavi_variable_name}'"""
            
        # Close the element definition
        cavity_generation += """)"""

        # Write to the file
        output_string += cavity_generation

    ########################################
    # Return
    ########################################
    output_string += "\n"
    return output_string

################################################################################
# Optics File
################################################################################
def create_cavity_optics_file_information(
        line:       xt.Line,
        line_table: xd.table.Table,
        config:     ConfigLike) -> str:

    ########################################
    # Get information
    ########################################
    unique_cavi_names       = []
    unique_cavi_variables   = []
    for cavi in line_table.rows[line_table.element_type == 'Cavity'].name:
        parentname      = get_parentname(cavi)
        variablename    = get_variablename(cavi)
        if parentname not in unique_cavi_names:
            unique_cavi_names.append(parentname)
            unique_cavi_variables.append(variablename)

    ########################################
    # Ensure there are cavities in the line
    ########################################
    if len(unique_cavi_names) == 0:
        return ""

    ########################################
    # Create Output string
    ########################################
    output_string = f"""
    ############################################################
    # Cavities
    ############################################################"""

    for cavi, variable_name in zip(unique_cavi_names, unique_cavi_variables):

        if cavi.startswith('-'):
            continue

        freq    = 0
        volt    = 0
        lag     = 180

        try:
            freq  = line[cavi].frequency
        except KeyError:
            try:
                freq  = line[f"-{cavi}"].frequency
            except KeyError:
                raise KeyError(f"Could not find cavity variable {cavi} or -{cavi} in line.")
            
        try:
            volt  = line[cavi].voltage
        except KeyError:
            try:
                volt  = line[f"-{cavi}"].voltage
            except KeyError:
                raise KeyError(f"Could not find cavity variable {cavi} or -{cavi} in line.")
            
        try:
            lag   = line[cavi].lag
        except KeyError:
            try:
                lag  = line[f"-{cavi}"].lag
            except KeyError:
                raise KeyError(f"Could not find cavity variable {cavi} or -{cavi} in line.")

        output_string += f"""
    {f'freq_{variable_name}'}{' ' * (config.OUTPUT_STRING_SEP - len(f'freq_{variable_name}') + 4)}{'= '}{freq:.24f},"""
        output_string += f"""
    {f'volt_{variable_name}'}{' ' * (config.OUTPUT_STRING_SEP - len(f'volt_{variable_name}') + 4)}{'= '}{volt:.24f},"""
        output_string += f"""
    {f'lag_{variable_name}'}{' ' * (config.OUTPUT_STRING_SEP - len(f'lag_{variable_name}') + 4)}{'= '}{lag:.24f},"""

    ########################################
    # Return
    ########################################
    output_string += "\n"
    return output_string
