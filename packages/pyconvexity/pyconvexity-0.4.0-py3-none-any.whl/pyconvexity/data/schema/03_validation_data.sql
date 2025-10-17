-- ============================================================================
-- PYPSA ATTRIBUTE VALIDATION RULES
-- Complete set of validation rules for all component types
-- Based on PyPSA component attribute definitions
-- Updated to use simplified 5-group system: basic, power, economics, control, other
-- Version 2.2.0
-- ============================================================================

-- Clear any existing validation rules
DELETE FROM attribute_validation_rules;

-- ============================================================================
-- BUS ATTRIBUTES
-- ============================================================================

-- BUS attributes from buses.csv (PyPSA reference) - Updated to simplified groups
INSERT INTO attribute_validation_rules (component_type, attribute_name, display_name, data_type, unit, default_value, allowed_storage_types, is_required, is_input, description, min_value, max_value, group_name, to_save) VALUES
-- Input attributes for BUS
('BUS', 'v_nom', 'Nominal Voltage', 'float', 'kV', '1', 'static', FALSE, TRUE, 'Nominal voltage', 0, NULL, 'power', FALSE),
('BUS', 'type', 'Bus Type', 'string', 'n/a', 'n/a', 'static', FALSE, TRUE, 'Placeholder for bus type. Not yet implemented.', NULL, NULL, 'basic', FALSE),
('BUS', 'x', 'X Coordinate', 'float', 'n/a', '0', 'static', FALSE, TRUE, 'Position (e.g. longitude); the Spatial Reference System Identifier (SRID) is set in network.srid.', NULL, NULL, 'other', FALSE),
('BUS', 'y', 'Y Coordinate', 'float', 'n/a', '0', 'static', FALSE, TRUE, 'Position (e.g. latitude); the Spatial Reference System Identifier (SRID) is set in network.srid.', NULL, NULL, 'other', FALSE),
('BUS', 'carrier', 'Energy Carrier', 'string', 'n/a', 'AC', 'static', FALSE, TRUE, 'Energy carrier: can be "AC" or "DC" for electrical buses, or "heat" or "gas".', NULL, NULL, 'basic', FALSE),
('BUS', 'unit', 'Unit', 'string', 'n/a', 'None', 'static', FALSE, TRUE, 'Unit of the bus'' carrier if the implicitly assumed unit ("MW") is inappropriate (e.g. "t/h", "MWh_th/h"). Only descriptive. Does not influence any PyPSA functions.', NULL, NULL, 'basic', FALSE),
('BUS', 'v_mag_pu_set', 'Voltage Magnitude Setpoint', 'float', 'per unit', '1', 'static_or_timeseries', FALSE, TRUE, 'Voltage magnitude set point, per unit of v_nom.', 0, NULL, 'power', FALSE),
('BUS', 'v_mag_pu_min', 'Min Voltage Magnitude', 'float', 'per unit', '0', 'static', FALSE, TRUE, 'Minimum desired voltage, per unit of v_nom. This is a placeholder attribute and is not currently used by any PyPSA functions.', 0, NULL, 'power', FALSE),
('BUS', 'v_mag_pu_max', 'Max Voltage Magnitude', 'float', 'per unit', 'inf', 'static', FALSE, TRUE, 'Maximum desired voltage, per unit of v_nom. This is a placeholder attribute and is not currently used by any PyPSA functions.', 0, NULL, 'power', FALSE),
-- Output attributes for BUS
('BUS', 'control', 'Control Strategy', 'string', 'n/a', 'PQ', 'static', FALSE, FALSE, 'P,Q,V control strategy for PF, must be "PQ", "PV" or "Slack". Note that this attribute is an output inherited from the controls of the generators attached to the bus; setting it directly on the bus will not have any effect.', NULL, NULL, 'control', FALSE),
('BUS', 'generator', 'Slack Generator', 'string', 'n/a', 'n/a', 'static', FALSE, FALSE, 'Name of slack generator attached to slack bus.', NULL, NULL, 'control', FALSE),
('BUS', 'sub_network', 'Sub-Network', 'string', 'n/a', 'n/a', 'static', FALSE, FALSE, 'Name of connected sub-network to which bus belongs. This attribute is set by PyPSA in the function network.determine_network_topology(); do not set it directly by hand.', NULL, NULL, 'other', FALSE),
('BUS', 'p', 'Active Power', 'float', 'MW', '0', 'timeseries', FALSE, FALSE, 'active power at bus (positive if net generation at bus)', NULL, NULL, 'power', TRUE),
('BUS', 'q', 'Reactive Power', 'float', 'MVar', '0', 'timeseries', FALSE, FALSE, 'reactive power (positive if net generation at bus)', NULL, NULL, 'power', TRUE),
('BUS', 'v_mag_pu', 'Voltage Magnitude', 'float', 'per unit', '1', 'timeseries', FALSE, FALSE, 'Voltage magnitude, per unit of v_nom', NULL, NULL, 'power', TRUE),
('BUS', 'v_ang', 'Voltage Angle', 'float', 'radians', '0', 'timeseries', FALSE, FALSE, 'Voltage angle', NULL, NULL, 'power', TRUE),
('BUS', 'marginal_price', 'Marginal Price', 'float', 'currency/MWh', '0', 'timeseries', FALSE, FALSE, 'Locational marginal price from LOPF from power balance constraint', NULL, NULL, 'economics', TRUE);

-- ============================================================================
-- GENERATOR ATTRIBUTES  
-- ============================================================================

-- GENERATOR attributes from generators.csv (PyPSA reference) - Updated to simplified groups
INSERT INTO attribute_validation_rules (component_type, attribute_name, display_name, data_type, unit, default_value, allowed_storage_types, is_required, is_input, description, min_value, max_value, group_name) VALUES
-- Input attributes for GENERATOR
('GENERATOR', 'control', 'Control Strategy', 'string', 'n/a', 'PQ', 'static', FALSE, TRUE, 'P,Q,V control strategy for PF, must be "PQ", "PV" or "Slack".', NULL, NULL, 'control'),
('GENERATOR', 'type', 'Generator Type', 'string', 'n/a', 'n/a', 'static', FALSE, TRUE, 'Placeholder for generator type. Not yet implemented.', NULL, NULL, 'basic'),
('GENERATOR', 'p_nom', 'Nominal Power', 'float', 'MW', '0', 'static', FALSE, TRUE, 'Nominal power for limits in optimization.', 0, NULL, 'power'),
('GENERATOR', 'p_nom_mod', 'Nominal Power Module', 'float', 'MW', '0', 'static', FALSE, TRUE, 'Nominal power of the generator module.', 0, NULL, 'power'),
('GENERATOR', 'p_nom_extendable', 'Extendable Capacity', 'boolean', 'n/a', 'False', 'static', FALSE, TRUE, 'Switch to allow capacity p_nom to be extended in optimization.', NULL, NULL, 'power'),
('GENERATOR', 'p_nom_min', 'Min Nominal Power', 'float', 'MW', '0', 'static', FALSE, TRUE, 'If p_nom is extendable in optimization, set its minimum value.', 0, NULL, 'power'),
('GENERATOR', 'p_nom_max', 'Max Nominal Power', 'float', 'MW', 'inf', 'static', FALSE, TRUE, 'If p_nom is extendable in optimization, set its maximum value (e.g. limited by technical potential).', 0, NULL, 'power'),
('GENERATOR', 'p_min_pu', 'Min Capacity Factor', 'float', 'per unit', '0', 'static_or_timeseries', FALSE, TRUE, 'The minimum output for each snapshot per unit of p_nom for the optimization (e.g. for variable renewable generators this can change due to weather conditions and compulsory feed-in; for conventional generators it represents a minimal dispatch). Note that if comittable is False and p_min_pu > 0, this represents a must-run condition.', 0, NULL, 'power'),
('GENERATOR', 'p_max_pu', 'Max Capacity Factor', 'float', 'per unit', '1', 'static_or_timeseries', FALSE, TRUE, 'The maximum output for each snapshot per unit of p_nom for the optimization (e.g. for variable renewable generators this can change due to weather conditions; for conventional generators it represents a maximum dispatch).', 0, 1, 'power'),
('GENERATOR', 'p_set', 'Active Power Setpoint', 'float', 'MW', '0', 'static_or_timeseries', FALSE, TRUE, 'active power set point (for PF)', NULL, NULL, 'power'),
('GENERATOR', 'e_sum_min', 'Min Energy Sum', 'float', 'MWh', '-inf', 'static', FALSE, TRUE, 'The minimum total energy produced during a single optimization horizon.', NULL, NULL, 'power'),
('GENERATOR', 'e_sum_max', 'Max Energy Sum', 'float', 'MWh', 'inf', 'static', FALSE, TRUE, 'The maximum total energy produced during a single optimization horizon.', NULL, NULL, 'power'),
('GENERATOR', 'q_set', 'Reactive Power Setpoint', 'float', 'MVar', '0', 'static_or_timeseries', FALSE, TRUE, 'reactive power set point (for PF)', NULL, NULL, 'power'),
('GENERATOR', 'sign', 'Power Sign', 'float', 'n/a', '1', 'static', FALSE, TRUE, 'power sign', NULL, NULL, 'power'),
('GENERATOR', 'carrier', 'Energy Carrier', 'string', 'n/a', 'n/a', 'static', FALSE, TRUE, 'Prime mover energy carrier (e.g. coal, gas, wind, solar); required for global constraints on primary energy in optimization', NULL, NULL, 'basic'),
('GENERATOR', 'marginal_cost', 'Marginal Cost', 'float', 'currency/MWh', '0', 'static_or_timeseries', FALSE, TRUE, 'Marginal cost of production of 1 MWh.', 0, NULL, 'economics'),
('GENERATOR', 'marginal_cost_quadratic', 'Quadratic Marginal Cost', 'float', 'currency/MWh', '0', 'static_or_timeseries', FALSE, TRUE, 'Quadratic marginal cost of production of 1 MWh.', 0, NULL, 'economics'),
('GENERATOR', 'capital_cost', 'Capital Cost', 'float', 'currency/MW', '0', 'static', FALSE, TRUE, 'Fixed period costs of extending p_nom by 1 MW, including periodized investment costs and periodic fixed O&M costs (e.g. annuitized investment costs).', 0, NULL, 'economics'),
('GENERATOR', 'active', 'Active', 'boolean', 'n/a', 'True', 'static', FALSE, TRUE, 'Whether to consider the component in basic functionality or not', NULL, NULL, 'basic'),
('GENERATOR', 'build_year', 'Build Year', 'int', 'year', '0', 'static', FALSE, TRUE, 'build year', 0, 3000, 'economics'),
('GENERATOR', 'lifetime', 'Lifetime', 'float', 'years', 'inf', 'static', FALSE, TRUE, 'lifetime', 0, NULL, 'economics'),
('GENERATOR', 'efficiency', 'Efficiency', 'float', 'per unit', '1', 'static_or_timeseries', FALSE, TRUE, 'Ratio between primary energy and electrical energy, e.g. takes value 0.4 MWh_elec/MWh_thermal for gas. This is required for global constraints on primary energy in optimization.', 0, 1, 'power'),
('GENERATOR', 'committable', 'Committable', 'boolean', 'n/a', 'False', 'static', FALSE, TRUE, 'Use unit commitment (only possible if p_nom is not extendable).', NULL, NULL, 'control'),
('GENERATOR', 'start_up_cost', 'Start-up Cost', 'float', 'currency', '0', 'static', FALSE, TRUE, 'Cost to start up the generator. Only read if committable is True.', 0, NULL, 'control'),
('GENERATOR', 'shut_down_cost', 'Shutdown Cost', 'float', 'currency', '0', 'static', FALSE, TRUE, 'Cost to shut down the generator. Only read if committable is True.', 0, NULL, 'control'),
('GENERATOR', 'stand_by_cost', 'Stand-by Cost', 'float', 'currency/h', '0', 'static_or_timeseries', FALSE, TRUE, 'Stand-by cost for operating the generator at null power output.', 0, NULL, 'control'),
('GENERATOR', 'min_up_time', 'Min Up Time', 'int', 'snapshots', '0', 'static', FALSE, TRUE, 'Minimum number of snapshots for status to be 1. Only read if committable is True.', 0, NULL, 'control'),
('GENERATOR', 'min_down_time', 'Min Down Time', 'int', 'snapshots', '0', 'static', FALSE, TRUE, 'Minimum number of snapshots for status to be 0. Only read if committable is True.', 0, NULL, 'control'),
('GENERATOR', 'up_time_before', 'Up Time Before', 'int', 'snapshots', '1', 'static', FALSE, TRUE, 'Number of snapshots that the generator was online before network.snapshots start. Only read if committable is True and min_up_time is non-zero.', 0, NULL, 'control'),
('GENERATOR', 'down_time_before', 'Down Time Before', 'int', 'snapshots', '0', 'static', FALSE, TRUE, 'Number of snapshots that the generator was offline before network.snapshots start. Only read if committable is True and min_down_time is non-zero.', 0, NULL, 'control'),
('GENERATOR', 'ramp_limit_up', 'Ramp Up Limit', 'float', 'per unit', '1', 'static_or_timeseries', FALSE, TRUE, 'Maximum active power increase from one snapshot to the next, per unit of the nominal power. Ignored if 1.', NULL, NULL, 'control'),
('GENERATOR', 'ramp_limit_down', 'Ramp Down Limit', 'float', 'per unit', '1', 'static_or_timeseries', FALSE, TRUE, 'Maximum active power decrease from one snapshot to the next, per unit of the nominal power. Ignored if 1.', NULL, NULL, 'control'),
('GENERATOR', 'ramp_limit_start_up', 'Ramp Up at Start', 'float', 'per unit', '1', 'static', FALSE, TRUE, 'Maximum active power increase at start up, per unit of the nominal power. Only read if committable is True.', NULL, NULL, 'control'),
('GENERATOR', 'ramp_limit_shut_down', 'Ramp Down at Shutdown', 'float', 'per unit', '1', 'static', FALSE, TRUE, 'Maximum active power decrease at shut down, per unit of the nominal power. Only read if committable is True.', NULL, NULL, 'control'),
('GENERATOR', 'weight', 'Weight', 'float', 'n/a', '1', 'static', FALSE, TRUE, 'Weighting of a generator. Only used for network clustering.', NULL, NULL, 'other'),
-- Output attributes for GENERATOR (from PyPSA generators.csv lines 38-46)
('GENERATOR', 'p', 'Active Power', 'float', 'MW', '0', 'timeseries', FALSE, FALSE, 'active power at bus (positive if net generation)', NULL, NULL, 'power'),
('GENERATOR', 'q', 'Reactive Power', 'float', 'MVar', '0', 'timeseries', FALSE, FALSE, 'reactive power (positive if net generation)', NULL, NULL, 'power'),
('GENERATOR', 'p_nom_opt', 'Optimised Nominal Power', 'float', 'MW', '0', 'static', FALSE, FALSE, 'Optimised nominal power.', 0, NULL, 'power'),
('GENERATOR', 'status', 'Status', 'float', 'n/a', '1', 'timeseries', FALSE, FALSE, 'Status (1 is on, 0 is off). Only outputted if committable is True.', NULL, NULL, 'control'),
('GENERATOR', 'mu_upper', 'Shadow Price Upper', 'float', 'currency/MWh', '0', 'timeseries', FALSE, FALSE, 'Shadow price of upper p_nom limit', NULL, NULL, 'economics'),
('GENERATOR', 'mu_lower', 'Shadow Price Lower', 'float', 'currency/MWh', '0', 'timeseries', FALSE, FALSE, 'Shadow price of lower p_nom limit', NULL, NULL, 'economics'),
('GENERATOR', 'mu_p_set', 'Shadow Price P Set', 'float', 'currency/MWh', '0', 'timeseries', FALSE, FALSE, 'Shadow price of fixed power generation p_set', NULL, NULL, 'economics'),
('GENERATOR', 'mu_ramp_limit_up', 'Shadow Price Ramp Up', 'float', 'currency/MWh', '0', 'timeseries', FALSE, FALSE, 'Shadow price of upper ramp up limit', NULL, NULL, 'economics'),
('GENERATOR', 'mu_ramp_limit_down', 'Shadow Price Ramp Down', 'float', 'currency/MWh', '0', 'timeseries', FALSE, FALSE, 'Shadow price of lower ramp down limit', NULL, NULL, 'economics');

-- ============================================================================
-- LOAD ATTRIBUTES
-- ============================================================================

-- LOAD attributes from loads.csv (PyPSA reference) - Updated to simplified groups
INSERT INTO attribute_validation_rules (component_type, attribute_name, display_name, data_type, unit, default_value, allowed_storage_types, is_required, is_input, description, min_value, max_value, group_name) VALUES
-- Input attributes for LOAD
('LOAD', 'carrier', 'Energy Carrier', 'string', 'n/a', 'n/a', 'static', FALSE, TRUE, 'Energy carrier: can be "AC" or "DC" for electrical buses, or "heat" or "gas".', NULL, NULL, 'basic'),
('LOAD', 'type', 'Load Type', 'string', 'n/a', 'n/a', 'static', FALSE, TRUE, 'Placeholder for load type. Not yet implemented.', NULL, NULL, 'basic'),
('LOAD', 'p_set', 'Active Power Demand', 'float', 'MW', '0', 'static_or_timeseries', FALSE, TRUE, 'Active power consumption (positive if the load is consuming power).', NULL, NULL, 'power'),
('LOAD', 'q_set', 'Reactive Power Demand', 'float', 'MVar', '0', 'static_or_timeseries', FALSE, TRUE, 'Reactive power consumption (positive if the load is inductive).', NULL, NULL, 'power'),
('LOAD', 'sign', 'Power Sign', 'float', 'n/a', '-1', 'static', FALSE, TRUE, 'power sign (opposite sign to generator)', NULL, NULL, 'power'),
('LOAD', 'active', 'Active', 'boolean', 'n/a', 'True', 'static', FALSE, TRUE, 'Whether to consider the component in common functionalities or not', NULL, NULL, 'basic'),
-- Output attributes for LOAD (PyPSA load outputs)
('LOAD', 'p', 'Active Power', 'float', 'MW', '0', 'timeseries', FALSE, FALSE, 'active power consumption (positive if consuming)', NULL, NULL, 'power'),
('LOAD', 'q', 'Reactive Power', 'float', 'MVar', '0', 'timeseries', FALSE, FALSE, 'reactive power consumption (positive if consuming)', NULL, NULL, 'power');

-- ============================================================================
-- LINE ATTRIBUTES
-- ============================================================================

-- LINE attributes from lines.csv (PyPSA reference) - Updated to simplified groups
INSERT INTO attribute_validation_rules (component_type, attribute_name, display_name, data_type, unit, default_value, allowed_storage_types, is_required, is_input, description, min_value, max_value, group_name) VALUES
-- Input attributes for LINE
('LINE', 'type', 'Line Type', 'string', 'n/a', '', 'static', FALSE, TRUE, 'Name of line standard type. If this is not an empty string "", then the line standard type impedance parameters are multiplied with the line length and divided/multiplied by num_parallel to compute x, r, etc. This will override any values set in r, x, and b. If the string is empty, PyPSA will simply read r, x, etc.', NULL, NULL, 'basic'),
('LINE', 'x', 'Series Reactance', 'float', 'Ohm', '0', 'static', FALSE, TRUE, 'Series reactance, must be non-zero for AC branch in linear power flow. If the line has series inductance L in Henries then x = 2πfL where f is the frequency in Hertz. Series impedance z = r + jx must be non-zero for the non-linear power flow. Ignored if type defined.', 0, NULL, 'power'),
('LINE', 'r', 'Series Resistance', 'float', 'Ohm', '0', 'static', FALSE, TRUE, 'Series resistance, must be non-zero for DC branch in linear power flow. Series impedance z = r + jx must be non-zero for the non-linear power flow. Ignored if type defined.', 0, NULL, 'power'),
('LINE', 'g', 'Shunt Conductance', 'float', 'Siemens', '0', 'static', FALSE, TRUE, 'Shunt conductivity. Shunt admittance is y = g + jb.', 0, NULL, 'power'),
('LINE', 'b', 'Shunt Susceptance', 'float', 'Siemens', '0', 'static', FALSE, TRUE, 'Shunt susceptance. If the line has shunt capacitance C in Farads then b = 2πfC where f is the frequency in Hertz. Shunt admittance is y = g + jb. Ignored if type defined.', NULL, NULL, 'power'),
('LINE', 's_nom', 'Nominal Apparent Power', 'float', 'MVA', '0', 'static', FALSE, TRUE, 'Limit of apparent power which can pass through branch.', 0, NULL, 'power'),
('LINE', 's_nom_mod', 'Nominal Power Module', 'float', 'MVA', '0', 'static', FALSE, TRUE, 'Unit size of line expansion of s_nom.', 0, NULL, 'power'),
('LINE', 's_nom_extendable', 'Extendable Capacity', 'boolean', 'n/a', 'False', 'static', FALSE, TRUE, 'Switch to allow capacity s_nom to be extended in OPF.', NULL, NULL, 'power'),
('LINE', 's_nom_min', 'Min Nominal Power', 'float', 'MVA', '0', 'static', FALSE, TRUE, 'If s_nom is extendable in OPF, set its minimum value.', 0, NULL, 'power'),
('LINE', 's_nom_max', 'Max Nominal Power', 'float', 'MVA', 'inf', 'static', FALSE, TRUE, 'If s_nom is extendable in OPF, set its maximum value (e.g. limited by potential).', 0, NULL, 'power'),
('LINE', 's_max_pu', 'Max Power Factor', 'float', 'per unit', '1', 'static_or_timeseries', FALSE, TRUE, 'The maximum allowed absolute flow per unit of s_nom for the OPF (e.g. can be set <1 to approximate n-1 factor, or can be time-varying to represent weather-dependent dynamic line rating for overhead lines).', 0, 1, 'power'),
('LINE', 'capital_cost', 'Capital Cost', 'float', 'currency/MVA', '0', 'static', FALSE, TRUE, 'Fixed period costs of extending s_nom by 1 MVA, including periodized investment costs and periodic fixed O&M costs (e.g. annuitized investment costs).', 0, NULL, 'economics'),
('LINE', 'active', 'Active', 'boolean', 'n/a', 'True', 'static', FALSE, TRUE, 'Whether to consider the component in basic functionality or not', NULL, NULL, 'basic'),
('LINE', 'build_year', 'Build Year', 'int', 'year', '0', 'static', FALSE, TRUE, 'build year', 0, 3000, 'economics'),
('LINE', 'lifetime', 'Lifetime', 'float', 'years', 'inf', 'static', FALSE, TRUE, 'lifetime', 0, NULL, 'economics'),
('LINE', 'length', 'Line Length', 'float', 'km', '0', 'static', FALSE, TRUE, 'Length of line used when "type" is set, also useful for calculating the capital cost.', 0, NULL, 'power'),
('LINE', 'carrier', 'Energy Carrier', 'string', 'n/a', '', 'static', FALSE, TRUE, 'Type of current, "AC" is the only valid value', NULL, NULL, 'basic'),
('LINE', 'terrain_factor', 'Terrain Factor', 'float', 'per unit', '1', 'static', FALSE, TRUE, 'Terrain factor for increasing capital cost.', 0, NULL, 'power'),
('LINE', 'num_parallel', 'Number of Parallel Lines', 'float', 'n/a', '1', 'static', FALSE, TRUE, 'When "type" is set, this is the number of parallel lines (can also be fractional). If "type" is empty "" this value is ignored.', 1, NULL, 'power'),
('LINE', 'v_ang_min', 'Min Voltage Angle Diff', 'float', 'Degrees', '-inf', 'static', FALSE, TRUE, 'Minimum voltage angle difference across the line. This is a placeholder attribute and is not currently used by any PyPSA functions.', NULL, NULL, 'power'),
('LINE', 'v_ang_max', 'Max Voltage Angle Diff', 'float', 'Degrees', 'inf', 'static', FALSE, TRUE, 'Maximum voltage angle difference across the line. This is a placeholder attribute and is not currently used by any PyPSA functions.', NULL, NULL, 'power'),
-- Output attributes for LINE (PyPSA line outputs)
('LINE', 'p0', 'Active Power Bus0', 'float', 'MW', '0', 'timeseries', FALSE, FALSE, 'active power at bus0 (positive if power flows from bus0 to bus1)', NULL, NULL, 'power'),
('LINE', 'p1', 'Active Power Bus1', 'float', 'MW', '0', 'timeseries', FALSE, FALSE, 'active power at bus1 (positive if power flows from bus1 to bus0)', NULL, NULL, 'power'),
('LINE', 'q0', 'Reactive Power Bus0', 'float', 'MVar', '0', 'timeseries', FALSE, FALSE, 'reactive power at bus0', NULL, NULL, 'power'),
('LINE', 'q1', 'Reactive Power Bus1', 'float', 'MVar', '0', 'timeseries', FALSE, FALSE, 'reactive power at bus1', NULL, NULL, 'power'),
('LINE', 's_nom_opt', 'Optimised Apparent Power', 'float', 'MVA', '0', 'static', FALSE, FALSE, 'Optimised apparent power limit.', 0, NULL, 'power'),
('LINE', 'mu_upper', 'Shadow Price Upper', 'float', 'currency/MVA', '0', 'timeseries', FALSE, FALSE, 'Shadow price of upper s_nom limit', NULL, NULL, 'economics'),
('LINE', 'mu_lower', 'Shadow Price Lower', 'float', 'currency/MVA', '0', 'timeseries', FALSE, FALSE, 'Shadow price of lower s_nom limit', NULL, NULL, 'economics'),
('LINE', 'sub_network', 'Sub-Network', 'string', 'n/a', 'n/a', 'static', FALSE, FALSE, 'Name of connected sub-network to which line belongs. This attribute is set by PyPSA.', NULL, NULL, 'other'),
('LINE', 'x_pu', 'Per Unit Reactance', 'float', 'per unit', '0', 'static', FALSE, FALSE, 'Per unit series reactance calculated by PyPSA from x and bus.v_nom', NULL, NULL, 'power'),
('LINE', 'r_pu', 'Per Unit Resistance', 'float', 'per unit', '0', 'static', FALSE, FALSE, 'Per unit series resistance calculated by PyPSA from r and bus.v_nom', NULL, NULL, 'power'),
('LINE', 'g_pu', 'Per Unit Conductance', 'float', 'per unit', '0', 'static', FALSE, FALSE, 'Per unit shunt conductivity calculated by PyPSA from g and bus.v_nom', NULL, NULL, 'power'),
('LINE', 'b_pu', 'Per Unit Susceptance', 'float', 'per unit', '0', 'static', FALSE, FALSE, 'Per unit shunt susceptance calculated by PyPSA from b and bus.v_nom', NULL, NULL, 'power'),
('LINE', 'x_pu_eff', 'Effective Per Unit Reactance', 'float', 'per unit', '0', 'static', FALSE, FALSE, 'Effective per unit series reactance for linear power flow', NULL, NULL, 'power'),
('LINE', 'r_pu_eff', 'Effective Per Unit Resistance', 'float', 'per unit', '0', 'static', FALSE, FALSE, 'Effective per unit series resistance for linear power flow', NULL, NULL, 'power');

-- ============================================================================
-- LINK ATTRIBUTES
-- ============================================================================

-- LINK attributes from links.csv (PyPSA reference) - Updated to simplified groups
INSERT INTO attribute_validation_rules (component_type, attribute_name, display_name, data_type, unit, default_value, allowed_storage_types, is_required, is_input, description, min_value, max_value, group_name) VALUES
-- Input attributes for LINK
('LINK', 'type', 'Link Type', 'string', 'n/a', 'n/a', 'static', FALSE, TRUE, 'Placeholder for link type. Not yet implemented.', NULL, NULL, 'basic'),
('LINK', 'carrier', 'Energy Carrier', 'string', 'n/a', '', 'static', FALSE, TRUE, 'Energy carrier transported by the link: can be "DC" for electrical HVDC links, or "heat" or "gas" etc.', NULL, NULL, 'basic'),
('LINK', 'efficiency', 'Transfer Efficiency', 'float', 'per unit', '1', 'static_or_timeseries', FALSE, TRUE, 'Efficiency of power transfer from bus0 to bus1. (Can be time-dependent to represent temperature-dependent Coefficient of Performance of a heat pump from an electric to a heat bus.)', 0, 1, 'power'),
('LINK', 'active', 'Active', 'boolean', 'n/a', 'True', 'static', FALSE, TRUE, 'Whether to consider the component in basic functionality or not', NULL, NULL, 'basic'),
('LINK', 'build_year', 'Build Year', 'int', 'year', '0', 'static', FALSE, TRUE, 'build year', 0, 3000, 'economics'),
('LINK', 'lifetime', 'Lifetime', 'float', 'years', 'inf', 'static', FALSE, TRUE, 'lifetime', 0, NULL, 'economics'),
('LINK', 'p_nom', 'Nominal Power', 'float', 'MW', '0', 'static', FALSE, TRUE, 'Limit of active power which can pass through link.', 0, NULL, 'power'),
('LINK', 'p_nom_mod', 'Nominal Power Module', 'float', 'MW', '0', 'static', FALSE, TRUE, 'Limit of active power of the link module.', 0, NULL, 'power'),
('LINK', 'p_nom_extendable', 'Extendable Capacity', 'boolean', 'n/a', 'False', 'static', FALSE, TRUE, 'Switch to allow capacity p_nom to be extended.', NULL, NULL, 'power'),
('LINK', 'p_nom_min', 'Min Nominal Power', 'float', 'MW', '0', 'static', FALSE, TRUE, 'If p_nom is extendable, set its minimum value.', 0, NULL, 'power'),
('LINK', 'p_nom_max', 'Max Nominal Power', 'float', 'MW', 'inf', 'static', FALSE, TRUE, 'If p_nom is extendable, set its maximum value (e.g. limited by potential).', 0, NULL, 'power'),
('LINK', 'p_set', 'Power Setpoint', 'float', 'MW', '0', 'static_or_timeseries', FALSE, TRUE, 'The dispatch set point for p0 of the link in PF.', NULL, NULL, 'power'),
('LINK', 'p_min_pu', 'Min Capacity Factor', 'float', 'per unit of p_nom', '0', 'static_or_timeseries', FALSE, TRUE, 'Minimal dispatch (can also be negative) per unit of p_nom for the link.', NULL, NULL, 'power'),
('LINK', 'p_max_pu', 'Max Capacity Factor', 'float', 'per unit of p_nom', '1', 'static_or_timeseries', FALSE, TRUE, 'Maximal dispatch (can also be negative) per unit of p_nom for the link.', NULL, NULL, 'power'),
('LINK', 'capital_cost', 'Capital Cost', 'float', 'currency/MW', '0', 'static', FALSE, TRUE, 'Fixed period costs of extending p_nom by 1 MW, including periodized investment costs and periodic fixed O&M costs (e.g. annuitized investment costs).', 0, NULL, 'economics'),
('LINK', 'marginal_cost', 'Marginal Cost', 'float', 'currency/MWh', '0', 'static_or_timeseries', FALSE, TRUE, 'Marginal cost of transfering 1 MWh (before efficiency losses) from bus0 to bus1. NB: marginal cost only makes sense if p_max_pu >= 0.', 0, NULL, 'economics'),
('LINK', 'marginal_cost_quadratic', 'Quadratic Marginal Cost', 'float', 'currency/MWh', '0', 'static_or_timeseries', FALSE, TRUE, 'Quadratic marginal cost for transferring 1 MWh (before efficiency losses) from bus0 to bus1.', 0, NULL, 'economics'),
('LINK', 'stand_by_cost', 'Stand-by Cost', 'float', 'currency/h', '0', 'static_or_timeseries', FALSE, TRUE, 'Stand-by cost for operating the link at null power flow.', 0, NULL, 'control'),
('LINK', 'length', 'Link Length', 'float', 'km', '0', 'static', FALSE, TRUE, 'Length of line, useful for calculating the capital cost.', 0, NULL, 'power'),
('LINK', 'terrain_factor', 'Terrain Factor', 'float', 'per unit', '1', 'static', FALSE, TRUE, 'Terrain factor for increasing capital cost.', 0, NULL, 'power'),
('LINK', 'committable', 'Committable', 'boolean', 'n/a', 'False', 'static', FALSE, TRUE, 'Use unit commitment (only possible if p_nom is not extendable).', NULL, NULL, 'control'),
('LINK', 'start_up_cost', 'Start-up Cost', 'float', 'currency', '0', 'static', FALSE, TRUE, 'Cost to start up the link. Only read if committable is True.', 0, NULL, 'control'),
('LINK', 'shut_down_cost', 'Shutdown Cost', 'float', 'currency', '0', 'static', FALSE, TRUE, 'Cost to shut down the link. Only read if committable is True.', 0, NULL, 'control'),
('LINK', 'min_up_time', 'Min Up Time', 'int', 'snapshots', '0', 'static', FALSE, TRUE, 'Minimum number of snapshots for status to be 1. Only read if committable is True.', 0, NULL, 'control'),
('LINK', 'min_down_time', 'Min Down Time', 'int', 'snapshots', '0', 'static', FALSE, TRUE, 'Minimum number of snapshots for status to be 0. Only read if committable is True.', 0, NULL, 'control'),
('LINK', 'up_time_before', 'Up Time Before', 'int', 'snapshots', '1', 'static', FALSE, TRUE, 'Number of snapshots that the link was online before network.snapshots start. Only read if committable is True and min_up_time is non-zero.', 0, NULL, 'control'),
('LINK', 'down_time_before', 'Down Time Before', 'int', 'snapshots', '0', 'static', FALSE, TRUE, 'Number of snapshots that the link was offline before network.snapshots start. Only read if committable is True and min_down_time is non-zero.', 0, NULL, 'control'),
('LINK', 'ramp_limit_up', 'Ramp Up Limit', 'float', 'per unit', '1', 'static_or_timeseries', FALSE, TRUE, 'Maximum increase from one snapshot to the next, per unit of the bus0 unit. Ignored if 1.', NULL, NULL, 'control'),
('LINK', 'ramp_limit_down', 'Ramp Down Limit', 'float', 'per unit', '1', 'static_or_timeseries', FALSE, TRUE, 'Maximum decrease from one snapshot to the next, per unit of the bus0 unit. Ignored if 1.', NULL, NULL, 'control'),
('LINK', 'ramp_limit_start_up', 'Ramp Up at Start', 'float', 'per unit', '1', 'static', FALSE, TRUE, 'Maximumincrease at start up, per unit of bus0 unit. Only read if committable is True.', NULL, NULL, 'control'),
-- Output attributes for LINK (PyPSA link outputs)
('LINK', 'p0', 'Active Power Bus0', 'float', 'MW', '0', 'timeseries', FALSE, FALSE, 'active power at bus0 (positive if power flows from bus0 to bus1)', NULL, NULL, 'power'),
('LINK', 'p1', 'Active Power Bus1', 'float', 'MW', '0', 'timeseries', FALSE, FALSE, 'active power at bus1 (positive if power flows from bus1 to bus0)', NULL, NULL, 'power'),
('LINK', 'p_nom_opt', 'Optimised Nominal Power', 'float', 'MW', '0', 'static', FALSE, FALSE, 'Optimised nominal power.', 0, NULL, 'power'),
('LINK', 'status', 'Status', 'float', 'n/a', '1', 'timeseries', FALSE, FALSE, 'Status (1 is on, 0 is off). Only outputted if committable is True.', NULL, NULL, 'control'),
('LINK', 'mu_upper', 'Shadow Price Upper', 'float', 'currency/MW', '0', 'timeseries', FALSE, FALSE, 'Shadow price of upper p_nom limit', NULL, NULL, 'economics'),
('LINK', 'mu_lower', 'Shadow Price Lower', 'float', 'currency/MW', '0', 'timeseries', FALSE, FALSE, 'Shadow price of lower p_nom limit', NULL, NULL, 'economics'),
('LINK', 'mu_p_set', 'Shadow Price P Set', 'float', 'currency/MWh', '0', 'timeseries', FALSE, FALSE, 'Shadow price of fixed power transmission p_set', NULL, NULL, 'economics'),
('LINK', 'mu_ramp_limit_up', 'Shadow Price Ramp Up', 'float', 'currency/MWh', '0', 'timeseries', FALSE, FALSE, 'Shadow price of upper ramp up limit', NULL, NULL, 'economics'),
('LINK', 'mu_ramp_limit_down', 'Shadow Price Ramp Down', 'float', 'currency/MWh', '0', 'timeseries', FALSE, FALSE, 'Shadow price of lower ramp down limit', NULL, NULL, 'economics');

-- ============================================================================
-- UNMET_LOAD ATTRIBUTES  
-- ============================================================================

-- UNMET_LOAD attributes - same as GENERATOR but with specific defaults and restrictions - Updated to simplified groups
INSERT INTO attribute_validation_rules (component_type, attribute_name, display_name, data_type, unit, default_value, allowed_storage_types, is_required, is_input, description, min_value, max_value, group_name) VALUES
-- Input attributes for UNMET_LOAD (same as GENERATOR)
('UNMET_LOAD', 'control', 'Control Strategy', 'string', 'n/a', 'PQ', 'static', FALSE, TRUE, 'P,Q,V control strategy for PF, must be "PQ", "PV" or "Slack".', NULL, NULL, 'control'),
('UNMET_LOAD', 'type', 'Unmet Load Type', 'string', 'n/a', 'n/a', 'static', FALSE, TRUE, 'Placeholder for generator type. Not yet implemented.', NULL, NULL, 'basic'),
('UNMET_LOAD', 'p_nom', 'Nominal Power', 'float', 'MW', '10000000', 'static', FALSE, TRUE, 'Nominal power for limits in OPF. Set very high for unmet load.', 0, NULL, 'power'),
('UNMET_LOAD', 'p_nom_extendable', 'Extendable Capacity', 'boolean', 'n/a', 'False', 'static', FALSE, TRUE, 'Switch to allow capacity p_nom to be extended in OPF.', NULL, NULL, 'power'),
('UNMET_LOAD', 'p_nom_min', 'Min Nominal Power', 'float', 'MW', '0', 'static', FALSE, TRUE, 'If p_nom is extendable in OPF, set its minimum value.', 0, NULL, 'power'),
('UNMET_LOAD', 'p_nom_max', 'Max Nominal Power', 'float', 'MW', 'inf', 'static', FALSE, TRUE, 'If p_nom is extendable in OPF, set its maximum value (e.g. limited by potential).', 0, NULL, 'power'),
('UNMET_LOAD', 'p_min_pu', 'Min Capacity Factor', 'float', 'per unit', '0', 'static_or_timeseries', FALSE, TRUE, 'The minimum output for each snapshot per unit of p_nom for the OPF.', 0, 1, 'power'),
('UNMET_LOAD', 'p_max_pu', 'Max Capacity Factor', 'float', 'per unit', '1', 'static_or_timeseries', FALSE, TRUE, 'The maximum output for each snapshot per unit of p_nom for the OPF.', 0, 1, 'power'),
('UNMET_LOAD', 'p_set', 'Active Power Setpoint', 'float', 'MW', '0', 'static_or_timeseries', FALSE, TRUE, 'active power set point (for PF)', NULL, NULL, 'power'),
('UNMET_LOAD', 'q_set', 'Reactive Power Setpoint', 'float', 'MVar', '0', 'static_or_timeseries', FALSE, TRUE, 'reactive power set point (for PF)', NULL, NULL, 'power'),
('UNMET_LOAD', 'sign', 'Power Sign', 'float', 'n/a', '1', 'static', FALSE, TRUE, 'power sign', NULL, NULL, 'power'),
('UNMET_LOAD', 'carrier', 'Energy Carrier', 'string', 'n/a', 'n/a', 'static', FALSE, TRUE, 'Prime mover energy carrier (e.g. coal, gas, wind, solar); required for global constraints on primary energy in OPF', NULL, NULL, 'basic'),
('UNMET_LOAD', 'marginal_cost', 'Marginal Cost (Penalty)', 'float', 'currency/MWh', '100000000', 'static_or_timeseries', FALSE, TRUE, 'Marginal cost of production of 1 MWh. Set very high for unmet load penalty.', 0, NULL, 'economics'),
('UNMET_LOAD', 'build_year', 'Build Year', 'int', 'year', '0', 'static', FALSE, TRUE, 'Year when generator can be built in the optimize branch.', NULL, NULL, 'economics'),
('UNMET_LOAD', 'lifetime', 'Lifetime', 'float', 'years', 'inf', 'static', FALSE, TRUE, 'Expected lifetime in years.', 0, NULL, 'economics'),
('UNMET_LOAD', 'capital_cost', 'Capital Cost', 'float', 'currency/MW', '0', 'static_or_timeseries', FALSE, TRUE, 'Capital cost of extending p_nom by 1 MW.', 0, NULL, 'economics'),
('UNMET_LOAD', 'efficiency', 'Efficiency', 'float', 'per unit', '1', 'static_or_timeseries', FALSE, TRUE, 'Ratio between primary energy and electrical energy. Use as energy consumption if negative.', NULL, NULL, 'power'),
('UNMET_LOAD', 'committable', 'Committable', 'boolean', 'n/a', 'False', 'static', FALSE, TRUE, 'Switch to allow the unit to be turned on or off with start up costs.', NULL, NULL, 'control'),
('UNMET_LOAD', 'start_up_cost', 'Start-up Cost', 'float', 'currency', '0', 'static', FALSE, TRUE, 'Start up cost when unit goes from offline to online status.', 0, NULL, 'control'),
('UNMET_LOAD', 'shut_down_cost', 'Shutdown Cost', 'float', 'currency', '0', 'static', FALSE, TRUE, 'Shut down cost when unit goes from online to offline status.', 0, NULL, 'control'),
('UNMET_LOAD', 'min_up_time', 'Min Up Time', 'int', 'snapshots', '0', 'static', FALSE, TRUE, 'Minimum number of snapshots for status to be 1. Only read if committable is True.', 0, NULL, 'control'),
('UNMET_LOAD', 'min_down_time', 'Min Down Time', 'int', 'snapshots', '0', 'static', FALSE, TRUE, 'Minimum number of snapshots for status to be 0. Only read if committable is True.', 0, NULL, 'control'),
('UNMET_LOAD', 'up_time_before', 'Up Time Before', 'int', 'snapshots', '1', 'static', FALSE, TRUE, 'Number of snapshots that the generator was online before network.snapshots start. Only read if committable is True and min_up_time is non-zero.', 0, NULL, 'control'),
('UNMET_LOAD', 'down_time_before', 'Down Time Before', 'int', 'snapshots', '0', 'static', FALSE, TRUE, 'Number of snapshots that the generator was offline before network.snapshots start. Only read if committable is True and min_down_time is non-zero.', 0, NULL, 'control'),
('UNMET_LOAD', 'ramp_limit_up', 'Ramp Up Limit', 'float', 'per unit', '1', 'static_or_timeseries', FALSE, TRUE, 'Maximum increase from one snapshot to the next, per unit of p_nom. Ignored if 1.', NULL, NULL, 'control'),
('UNMET_LOAD', 'ramp_limit_down', 'Ramp Down Limit', 'float', 'per unit', '1', 'static_or_timeseries', FALSE, TRUE, 'Maximum decrease from one snapshot to the next, per unit of p_nom. Ignored if 1.', NULL, NULL, 'control'),
('UNMET_LOAD', 'ramp_limit_start_up', 'Ramp Up at Start', 'float', 'per unit', '1', 'static', FALSE, TRUE, 'Maximum increase at start up, per unit of p_nom. Only read if committable is True.', NULL, NULL, 'control'),
('UNMET_LOAD', 'ramp_limit_shut_down', 'Ramp Down at Shutdown', 'float', 'per unit', '1', 'static', FALSE, TRUE, 'Maximum decrease at shut down, per unit of p_nom. Only read if committable is True.', NULL, NULL, 'control'),
('UNMET_LOAD', 'active', 'Active', 'boolean', 'n/a', 'True', 'static', FALSE, TRUE, 'Switch to enable/disable this unmet load component.', NULL, NULL, 'basic'),
-- Output attributes for UNMET_LOAD (same as GENERATOR since PyPSA treats them as generators)
('UNMET_LOAD', 'p', 'Active Power', 'float', 'MW', '0', 'timeseries', FALSE, FALSE, 'active power at bus (positive if net generation)', NULL, NULL, 'power'),
('UNMET_LOAD', 'q', 'Reactive Power', 'float', 'MVar', '0', 'timeseries', FALSE, FALSE, 'reactive power (positive if net generation)', NULL, NULL, 'power'),
('UNMET_LOAD', 'p_nom_opt', 'Optimised Nominal Power', 'float', 'MW', '0', 'static', FALSE, FALSE, 'Optimised nominal power.', 0, NULL, 'power'),
('UNMET_LOAD', 'status', 'Status', 'float', 'n/a', '1', 'timeseries', FALSE, FALSE, 'Status (1 is on, 0 is off). Only outputted if committable is True.', NULL, NULL, 'control'),
('UNMET_LOAD', 'mu_upper', 'Shadow Price Upper', 'float', 'currency/MWh', '0', 'timeseries', FALSE, FALSE, 'Shadow price of upper p_nom limit', NULL, NULL, 'economics'),
('UNMET_LOAD', 'mu_lower', 'Shadow Price Lower', 'float', 'currency/MWh', '0', 'timeseries', FALSE, FALSE, 'Shadow price of lower p_nom limit', NULL, NULL, 'economics'),
('UNMET_LOAD', 'mu_p_set', 'Shadow Price P Set', 'float', 'currency/MWh', '0', 'timeseries', FALSE, FALSE, 'Shadow price of fixed power generation p_set', NULL, NULL, 'economics'),
('UNMET_LOAD', 'mu_ramp_limit_up', 'Shadow Price Ramp Up', 'float', 'currency/MWh', '0', 'timeseries', FALSE, FALSE, 'Shadow price of upper ramp up limit', NULL, NULL, 'economics'),
('UNMET_LOAD', 'mu_ramp_limit_down', 'Shadow Price Ramp Down', 'float', 'currency/MWh', '0', 'timeseries', FALSE, FALSE, 'Shadow price of lower ramp down limit', NULL, NULL, 'economics');

-- ============================================================================
-- STORAGE_UNIT ATTRIBUTES
-- ============================================================================

-- STORAGE_UNIT attributes from storage_units.csv (PyPSA reference) - Updated to simplified groups
INSERT INTO attribute_validation_rules (component_type, attribute_name, display_name, data_type, unit, default_value, allowed_storage_types, is_required, is_input, description, min_value, max_value, group_name) VALUES
-- Input attributes for STORAGE_UNIT
('STORAGE_UNIT', 'control', 'Control Strategy', 'string', 'n/a', 'PQ', 'static', FALSE, TRUE, 'P,Q,V control strategy for PF, must be "PQ", "PV" or "Slack".', NULL, NULL, 'control'),
('STORAGE_UNIT', 'type', 'Storage Unit Type', 'string', 'n/a', 'n/a', 'static', FALSE, TRUE, 'Placeholder for storage unit type. Not yet implemented.', NULL, NULL, 'basic'),
('STORAGE_UNIT', 'p_nom', 'Nominal Power', 'float', 'MW', '0', 'static', FALSE, TRUE, 'Nominal power for limits in OPF.', 0, NULL, 'power'),
('STORAGE_UNIT', 'p_nom_mod', 'Nominal Power Module', 'float', 'MW', '0', 'static', FALSE, TRUE, 'Nominal power of the storage unit module.', 0, NULL, 'power'),
('STORAGE_UNIT', 'p_nom_extendable', 'Extendable Capacity', 'boolean', 'n/a', 'False', 'static', FALSE, TRUE, 'Switch to allow capacity p_nom to be extended in OPF.', NULL, NULL, 'power'),
('STORAGE_UNIT', 'p_nom_min', 'Min Nominal Power', 'float', 'MW', '0', 'static', FALSE, TRUE, 'If p_nom is extendable in OPF, set its minimum value.', 0, NULL, 'power'),
('STORAGE_UNIT', 'p_nom_max', 'Max Nominal Power', 'float', 'MW', 'inf', 'static', FALSE, TRUE, 'If p_nom is extendable in OPF, set its maximum value (e.g. limited by potential).', 0, NULL, 'power'),
('STORAGE_UNIT', 'p_min_pu', 'Min Capacity Factor', 'float', 'per unit', '-1', 'static_or_timeseries', FALSE, TRUE, 'The minimum output for each snapshot per unit of p_nom for the OPF (negative sign implies storing mode withdrawing power from bus).', -1, 1, 'power'),
('STORAGE_UNIT', 'p_max_pu', 'Max Capacity Factor', 'float', 'per unit', '1', 'static_or_timeseries', FALSE, TRUE, 'The maximum output for each snapshot per unit of p_nom for the OPF.', -1, 1, 'power'),
('STORAGE_UNIT', 'p_set', 'Active Power Setpoint', 'float', 'MW', '0', 'static_or_timeseries', FALSE, TRUE, 'active power set point (for PF)', NULL, NULL, 'power'),
('STORAGE_UNIT', 'q_set', 'Reactive Power Setpoint', 'float', 'MVar', '0', 'static_or_timeseries', FALSE, TRUE, 'reactive power set point (for PF)', NULL, NULL, 'power'),
('STORAGE_UNIT', 'sign', 'Power Sign', 'float', 'n/a', '1', 'static', FALSE, TRUE, 'power sign', NULL, NULL, 'power'),
('STORAGE_UNIT', 'carrier', 'Energy Carrier', 'string', 'n/a', 'n/a', 'static', FALSE, TRUE, 'Prime mover energy carrier (e.g. coal, gas, wind, solar); required for global constraints on primary energy in OPF', NULL, NULL, 'basic'),
('STORAGE_UNIT', 'spill_cost', 'Spill Cost', 'float', 'currency/MWh', '0', 'static_or_timeseries', FALSE, TRUE, 'Cost of spilling 1 MWh.', 0, NULL, 'economics'),
('STORAGE_UNIT', 'marginal_cost', 'Marginal Cost', 'float', 'currency/MWh', '0', 'static_or_timeseries', FALSE, TRUE, 'Marginal cost of production of 1 MWh.', 0, NULL, 'economics'),
('STORAGE_UNIT', 'marginal_cost_quadratic', 'Quadratic Marginal Cost', 'float', 'currency/MWh', '0', 'static_or_timeseries', FALSE, TRUE, 'Quadratic marginal cost of production (discharge) of 1 MWh.', 0, NULL, 'economics'),
('STORAGE_UNIT', 'marginal_cost_storage', 'Storage Marginal Cost', 'float', 'currency/MWh/h', '0', 'static_or_timeseries', FALSE, TRUE, 'Marginal cost of energy storage of 1 MWh for one hour.', 0, NULL, 'economics'),
('STORAGE_UNIT', 'capital_cost', 'Capital Cost', 'float', 'currency/MW', '0', 'static', FALSE, TRUE, 'Fixed period costs of extending p_nom by 1 MW, including periodized investment costs and periodic fixed O&M costs (e.g. annuitized investment costs).', 0, NULL, 'economics'),
('STORAGE_UNIT', 'active', 'Active', 'boolean', 'n/a', 'True', 'static', FALSE, TRUE, 'Whether to consider the component in basic functionality or not', NULL, NULL, 'basic'),
('STORAGE_UNIT', 'build_year', 'Build Year', 'int', 'year', '0', 'static', FALSE, TRUE, 'build year', 0, 3000, 'economics'),
('STORAGE_UNIT', 'lifetime', 'Lifetime', 'float', 'years', 'inf', 'static', FALSE, TRUE, 'lifetime', 0, NULL, 'economics'),
('STORAGE_UNIT', 'state_of_charge_initial', 'Initial State of Charge', 'float', 'MWh', '0', 'static', FALSE, TRUE, 'State of charge before the snapshots in the OPF.', 0, NULL, 'power'),
('STORAGE_UNIT', 'state_of_charge_initial_per_period', 'Initial SOC per Period', 'boolean', 'n/a', 'False', 'static', FALSE, TRUE, 'Switch: if True, then state of charge at the beginning of an investment period is set to state_of_charge_initial', NULL, NULL, 'power'),
('STORAGE_UNIT', 'state_of_charge_set', 'State of Charge Setpoint', 'float', 'MWh', '1', 'static_or_timeseries', FALSE, TRUE, 'State of charge set points for snapshots in the OPF.', NULL, NULL, 'power'),
('STORAGE_UNIT', 'cyclic_state_of_charge', 'Cyclic State of Charge', 'boolean', 'n/a', 'False', 'static', FALSE, TRUE, 'Switch: if True, then state_of_charge_initial is ignored and the initial state of charge is set to the final state of charge for the group of snapshots in the OPF (soc[-1] = soc[len(snapshots)-1]).', NULL, NULL, 'power'),
('STORAGE_UNIT', 'cyclic_state_of_charge_per_period', 'Cyclic SOC per Period', 'boolean', 'n/a', 'True', 'static', FALSE, TRUE, 'Switch: if True, then the cyclic constraints are applied to each period (first snapshot level if multiindexed) separately.', NULL, NULL, 'power'),
('STORAGE_UNIT', 'max_hours', 'Max Storage Hours', 'float', 'hours', '1', 'static', FALSE, TRUE, 'Maximum state of charge capacity in terms of hours at full output capacity p_nom', 0, NULL, 'power'),
('STORAGE_UNIT', 'efficiency_store', 'Storage Efficiency', 'float', 'per unit', '1', 'static_or_timeseries', FALSE, TRUE, 'Efficiency of storage on the way into the storage.', 0, 1, 'power'),
('STORAGE_UNIT', 'efficiency_dispatch', 'Dispatch Efficiency', 'float', 'per unit', '1', 'static_or_timeseries', FALSE, TRUE, 'Efficiency of storage on the way out of the storage.', 0, 1, 'power'),
('STORAGE_UNIT', 'standing_loss', 'Standing Loss', 'float', 'per unit', '0', 'static_or_timeseries', FALSE, TRUE, 'Losses per hour to state of charge.', 0, 1, 'power'),
('STORAGE_UNIT', '1low', 'Inflow', 'float', 'MW', '0', 'static_or_timeseries', FALSE, TRUE, '1low to the state of charge, e.g. due to river 1low in hydro reservoir.', NULL, NULL, 'power'),
-- Output attributes for STORAGE_UNIT (PyPSA storage unit outputs)
('STORAGE_UNIT', 'p', 'Active Power', 'float', 'MW', '0', 'timeseries', FALSE, FALSE, 'active power at bus (positive if discharging)', NULL, NULL, 'power'),
('STORAGE_UNIT', 'q', 'Reactive Power', 'float', 'MVar', '0', 'timeseries', FALSE, FALSE, 'reactive power at bus', NULL, NULL, 'power'),
('STORAGE_UNIT', 'state_of_charge', 'State of Charge', 'float', 'MWh', '0', 'timeseries', FALSE, FALSE, 'State of charge of storage unit', 0, NULL, 'power'),
('STORAGE_UNIT', 'p_nom_opt', 'Optimised Nominal Power', 'float', 'MW', '0', 'static', FALSE, FALSE, 'Optimised nominal power.', 0, NULL, 'power'),
('STORAGE_UNIT', 'spill', 'Spill', 'float', 'MWh', '0', 'timeseries', FALSE, FALSE, 'Spillage of storage unit', 0, NULL, 'power'),
('STORAGE_UNIT', 'status', 'Status', 'float', 'n/a', '1', 'timeseries', FALSE, FALSE, 'Status (1 is on, 0 is off). Only outputted if committable is True.', NULL, NULL, 'control'),
('STORAGE_UNIT', 'mu_upper', 'Shadow Price Upper', 'float', 'currency/MWh', '0', 'timeseries', FALSE, FALSE, 'Shadow price of upper p_nom limit', NULL, NULL, 'economics'),
('STORAGE_UNIT', 'mu_lower', 'Shadow Price Lower', 'float', 'currency/MWh', '0', 'timeseries', FALSE, FALSE, 'Shadow price of lower p_nom limit', NULL, NULL, 'economics'),
('STORAGE_UNIT', 'p_dispatch', 'Active Power Dispatch', 'float', 'MW', '0', 'timeseries', FALSE, FALSE, 'active power dispatch at bus', NULL, NULL, 'power'),
('STORAGE_UNIT', 'p_store', 'Active Power Charging', 'float', 'MW', '0', 'timeseries', FALSE, FALSE, 'active power charging at bus', NULL, NULL, 'power'),
('STORAGE_UNIT', 'mu_state_of_charge_set', 'Shadow Price SOC Set', 'float', 'currency/MWh', '0', 'timeseries', FALSE, FALSE, 'Shadow price of fixed state of charge state_of_charge_set', NULL, NULL, 'economics'),
('STORAGE_UNIT', 'mu_energy_balance', 'Shadow Price Energy Balance', 'float', 'currency/MWh', '0', 'timeseries', FALSE, FALSE, 'Shadow price of storage consistency equations', NULL, NULL, 'economics');

-- ============================================================================
-- STORE ATTRIBUTES
-- ============================================================================

-- STORE attributes from stores.csv (PyPSA reference) - Updated to simplified groups
INSERT INTO attribute_validation_rules (component_type, attribute_name, display_name, data_type, unit, default_value, allowed_storage_types, is_required, is_input, description, min_value, max_value, group_name) VALUES
-- Input attributes for STORE
('STORE', 'type', 'Store Type', 'string', 'n/a', 'n/a', 'static', FALSE, TRUE, 'Placeholder for store type. Not yet implemented.', NULL, NULL, 'basic'),
('STORE', 'carrier', 'Energy Carrier', 'string', 'n/a', '', 'static', FALSE, TRUE, 'Energy carrier of the Store, e.g. "heat" or "gas".', NULL, NULL, 'basic'),
('STORE', 'e_nom', 'Nominal Energy Capacity', 'float', 'MWh', '0', 'static', FALSE, TRUE, 'Nominal energy capacity.', 0, NULL, 'power'),
('STORE', 'e_nom_mod', 'Nominal Energy Module', 'float', 'MWh', '0', 'static', FALSE, TRUE, 'Nominal energy capacity of the store module.', 0, NULL, 'power'),
('STORE', 'e_nom_extendable', 'Extendable Energy Capacity', 'boolean', 'n/a', 'False', 'static', FALSE, TRUE, 'Switch to allow capacity e_nom to be extended in OPF.', NULL, NULL, 'power'),
('STORE', 'e_nom_min', 'Min Energy Capacity', 'float', 'MWh', '0', 'static', FALSE, TRUE, 'If e_nom is extendable in OPF, set its minimum value.', 0, NULL, 'power'),
('STORE', 'e_nom_max', 'Max Energy Capacity', 'float', 'MWh', 'inf', 'static', FALSE, TRUE, 'If e_nom is extendable in OPF, set its maximum value (e.g. limited by technical potential).', 0, NULL, 'power'),
('STORE', 'e_min_pu', 'Min Energy Factor', 'float', 'per unit', '0', 'static_or_timeseries', FALSE, TRUE, 'Minimal value of e relative to e_nom for the OPF.', 0, 1, 'power'),
('STORE', 'e_max_pu', 'Max Energy Factor', 'float', 'per unit', '1', 'static_or_timeseries', FALSE, TRUE, 'Maximal value of e relative to e_nom for the OPF.', 0, 1, 'power'),
('STORE', 'e_initial', 'Initial Energy', 'float', 'MWh', '0', 'static', FALSE, TRUE, 'Energy before the snapshots in the OPF.', 0, NULL, 'power'),
('STORE', 'e_initial_per_period', 'Initial Energy per Period', 'boolean', 'n/a', 'False', 'static', FALSE, TRUE, 'Switch: if True, then at the beginning of each investment period e is set to e_initial', NULL, NULL, 'power'),
('STORE', 'e_cyclic', 'Cyclic Energy', 'boolean', 'n/a', 'False', 'static', FALSE, TRUE, 'Switch: if True, then e_initial is ignored and the initial energy is set to the final energy for the group of snapshots in the OPF.', NULL, NULL, 'power'),
('STORE', 'e_cyclic_per_period', 'Cyclic Energy per Period', 'boolean', 'n/a', 'True', 'static', FALSE, TRUE, 'Switch: if True, then the cyclic constraints are applied to each period (first snapshot level if multiindexed) separately.', NULL, NULL, 'power'),
('STORE', 'p_set', 'Active Power Setpoint', 'float', 'MW', '0', 'static_or_timeseries', FALSE, TRUE, 'active power set point (for PF)', NULL, NULL, 'power'),
('STORE', 'q_set', 'Reactive Power Setpoint', 'float', 'MVar', '0', 'static_or_timeseries', FALSE, TRUE, 'reactive power set point (for PF)', NULL, NULL, 'power'),
('STORE', 'sign', 'Power Sign', 'float', 'n/a', '1', 'static', FALSE, TRUE, 'power sign', NULL, NULL, 'power'),
('STORE', 'marginal_cost', 'Marginal Cost', 'float', 'currency/MWh', '0', 'static_or_timeseries', FALSE, TRUE, 'Marginal cost applied to both charging and discharging of 1 MWh.', 0, NULL, 'economics'),
('STORE', 'marginal_cost_quadratic', 'Quadratic Marginal Cost', 'float', 'currency/MWh', '0', 'static_or_timeseries', FALSE, TRUE, 'Quadratic marginal cost of applied to charging and discharging of 1 MWh.', 0, NULL, 'economics'),
('STORE', 'marginal_cost_storage', 'Storage Marginal Cost', 'float', 'currency/MWh/h', '0', 'static_or_timeseries', FALSE, TRUE, 'Marginal cost of energy storage of 1 MWh for one hour.', 0, NULL, 'economics'),
('STORE', 'capital_cost', 'Capital Cost', 'float', 'currency/MWh', '0', 'static', FALSE, TRUE, 'Fixed period costs of extending e_nom by 1 MWh, including periodized investment costs and periodic fixed O&M costs (e.g. annuitized investment costs).', 0, NULL, 'economics'),
('STORE', 'standing_loss', 'Standing Loss', 'float', 'per unit', '0', 'static_or_timeseries', FALSE, TRUE, 'Losses per hour to energy.', 0, 1, 'power'),
('STORE', 'active', 'Active', 'boolean', 'n/a', 'True', 'static', FALSE, TRUE, 'Whether to consider the component in basic functionality or not', NULL, NULL, 'basic'),
('STORE', 'build_year', 'Build Year', 'int', 'year', '0', 'static', FALSE, TRUE, 'build year', 0, 3000, 'economics'),
('STORE', 'lifetime', 'Lifetime', 'float', 'years', 'inf', 'static', FALSE, TRUE, 'lifetime', 0, NULL, 'economics'),
-- Output attributes for STORE (PyPSA store outputs)
('STORE', 'p', 'Active Power', 'float', 'MW', '0', 'timeseries', FALSE, FALSE, 'active power at bus (positive if withdrawing energy)', NULL, NULL, 'power'),
('STORE', 'q', 'Reactive Power', 'float', 'MVar', '0', 'timeseries', FALSE, FALSE, 'reactive power at bus', NULL, NULL, 'power'),
('STORE', 'e', 'Energy', 'float', 'MWh', '0', 'timeseries', FALSE, FALSE, 'Energy stored in store', 0, NULL, 'power'),
('STORE', 'e_nom_opt', 'Optimised Energy Capacity', 'float', 'MWh', '0', 'static', FALSE, FALSE, 'Optimised energy capacity.', 0, NULL, 'power'),
('STORE', 'mu_upper', 'Shadow Price Upper', 'float', 'currency/MWh', '0', 'timeseries', FALSE, FALSE, 'Shadow price of upper energy limit', NULL, NULL, 'economics'),
('STORE', 'mu_lower', 'Shadow Price Lower', 'float', 'currency/MWh', '0', 'timeseries', FALSE, FALSE, 'Shadow price of lower energy limit', NULL, NULL, 'economics');

-- ============================================================================
-- CONSTRAINT ATTRIBUTES
-- ============================================================================

-- CONSTRAINT attributes for Python code block constraints
INSERT INTO attribute_validation_rules (component_type, attribute_name, display_name, data_type, unit, default_value, allowed_storage_types, is_required, is_input, description, min_value, max_value, group_name) VALUES
-- Input attributes for CONSTRAINT
('CONSTRAINT', 'constraint_code', 'Constraint Code', 'string', 'n/a', '', 'static', TRUE, TRUE, 'Python code block defining constraint logic', NULL, NULL, 'basic'),
('CONSTRAINT', 'description', 'Description', 'string', 'n/a', '', 'static', FALSE, TRUE, 'Human-readable description of the constraint', NULL, NULL, 'basic'),
('CONSTRAINT', 'is_active', 'Is Active', 'boolean', 'n/a', 'True', 'static', FALSE, TRUE, 'Whether constraint is active and should be applied', NULL, NULL, 'basic'),
('CONSTRAINT', 'priority', 'Priority', 'int', 'n/a', '0', 'static', FALSE, TRUE, 'Execution priority (lower numbers execute first)', NULL, NULL, 'basic');

-- ============================================================================
-- COMPONENT CARRIER VALIDATION TRIGGERS
-- ============================================================================

-- Bus carrier validation - buses can only use AC, DC, heat, or gas carriers
CREATE TRIGGER validate_bus_carrier
    BEFORE INSERT ON components
    FOR EACH ROW
    WHEN NEW.component_type = 'BUS' AND NEW.carrier_id IS NOT NULL
BEGIN
    SELECT CASE 
        WHEN NOT EXISTS (
            SELECT 1 FROM carriers 
            WHERE id = NEW.carrier_id 
            AND name IN ('AC', 'DC', 'heat', 'gas')
            AND network_id = NEW.network_id
        ) THEN
            RAISE(ABORT, 'Buses can only use AC, DC, heat, or gas carriers')
    END;
END;

-- Bus carrier validation for updates
CREATE TRIGGER validate_bus_carrier_update
    BEFORE UPDATE OF carrier_id ON components
    FOR EACH ROW
    WHEN NEW.component_type = 'BUS' AND NEW.carrier_id IS NOT NULL AND NEW.carrier_id != OLD.carrier_id
BEGIN
    SELECT CASE 
        WHEN NOT EXISTS (
            SELECT 1 FROM carriers 
            WHERE id = NEW.carrier_id 
            AND name IN ('AC', 'DC', 'heat', 'gas')
            AND network_id = NEW.network_id
        ) THEN
            RAISE(ABORT, 'Buses can only use AC, DC, heat, or gas carriers')
    END;
END;

-- Line carrier validation - lines can only use AC carriers (PyPSA specification)
CREATE TRIGGER validate_line_carrier
    BEFORE INSERT ON components
    FOR EACH ROW
    WHEN NEW.component_type = 'LINE' AND NEW.carrier_id IS NOT NULL
BEGIN
    SELECT CASE 
        WHEN NOT EXISTS (
            SELECT 1 FROM carriers 
            WHERE id = NEW.carrier_id 
            AND name = 'AC'
            AND network_id = NEW.network_id
        ) THEN
            RAISE(ABORT, 'Lines can only use AC carriers')
    END;
END;

-- Line carrier validation for updates
CREATE TRIGGER validate_line_carrier_update
    BEFORE UPDATE OF carrier_id ON components
    FOR EACH ROW
    WHEN NEW.component_type = 'LINE' AND NEW.carrier_id IS NOT NULL AND NEW.carrier_id != OLD.carrier_id
BEGIN
    SELECT CASE 
        WHEN NOT EXISTS (
            SELECT 1 FROM carriers 
            WHERE id = NEW.carrier_id 
            AND name = 'AC'
            AND network_id = NEW.network_id
        ) THEN
            RAISE(ABORT, 'Lines can only use AC carriers')
    END;
END;

-- ============================================================================
-- NOTE: Bus connections are stored in connectivity JSON field, not as attributes
-- PyPSA export will resolve connectivity JSON to bus names during export process
-- ============================================================================

-- ============================================================================
-- VALIDATION COMPLETION
-- ============================================================================

-- Update schema version to indicate validation rules are populated
UPDATE system_metadata 
SET value = '2.2.0', updated_at = CURRENT_TIMESTAMP 
WHERE key = 'schema_version';

INSERT OR REPLACE INTO system_metadata (key, value, description) 
VALUES ('validation_rules_version', '2.2.0', 'PyPSA validation rules version');

INSERT OR REPLACE INTO system_metadata (key, value, description) 
VALUES ('validation_rules_count', (SELECT COUNT(*) FROM attribute_validation_rules), 'Total number of validation rules');

-- Set database user version for tracking
PRAGMA user_version = 3; 