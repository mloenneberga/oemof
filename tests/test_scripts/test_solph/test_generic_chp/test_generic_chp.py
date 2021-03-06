# -*- coding: utf-8 -*-
"""
Example that illustrates how to use custom component `GenericCHP` can be used.

In this case it is used to model a combined cycle extraction turbine.
"""

import os
import pandas as pd
import oemof.solph as solph
from oemof.outputlib import processing, views


def test_gen_chp():
    # read sequence data

    full_filename = os.path.join(os.path.dirname(__file__), 'ccet.csv')
    data = pd.read_csv(full_filename)

    # select periods
    periods = len(data)-1

    # create an energy system
    idx = pd.date_range('1/1/2017', periods=periods, freq='H')
    es = solph.EnergySystem(timeindex=idx)

    # resources
    bgas = solph.Bus(label='bgas')

    rgas = solph.Source(label='rgas', outputs={bgas: solph.Flow()})

    # heat
    bth = solph.Bus(label='bth')

    source_th = solph.Source(label='source_th',
                             outputs={bth: solph.Flow(variable_costs=1000)})

    demand_th = solph.Sink(label='demand_th', inputs={bth: solph.Flow(fixed=True,
                           actual_value=data['demand_th'], nominal_value=200)})

    # power
    bel = solph.Bus(label='bel')

    demand_el = solph.Sink(label='demand_el', inputs={bel: solph.Flow(
                           variable_costs=data['price_el'])})

    # generic chp
    # (for back pressure characteristics Q_CW_min=0 and back_pressure=True)
    ccet = solph.components.GenericCHP(
        label='combined_cycle_extraction_turbine',
        fuel_input={bgas: solph.Flow(
            H_L_FG_share=data['H_L_FG_share'])},
        electrical_output={bel: solph.Flow(
            P_max_woDH=data['P_max_woDH'],
            P_min_woDH=data['P_min_woDH'],
            Eta_el_max_woDH=data['Eta_el_max_woDH'],
            Eta_el_min_woDH=data['Eta_el_min_woDH'])},
        heat_output={bth: solph.Flow(
            Q_CW_min=data['Q_CW_min'])},
        Beta=data['Beta'], back_pressure=False,
        fixed_costs=0)

    # create an optimization problem and solve it
    om = solph.OperationalModel(es)

    # solve model
    om.solve(solver='cbc')

    # create result object
    results = processing.results(om)

    data = views.node(results, 'bth')['sequences'].sum(axis=0).to_dict()

    test_dict = {
        (('bth', 'demand_th'), 'flow'): 20000.0,
        (('combined_cycle_extraction_turbine', 'bth'), 'flow'): 14070.15215799997,
        (('source_th', 'bth'), 'flow'): 5929.8478649200015}

    for key in test_dict.keys():
        a = int(round(data[key]))
        b = int(round(test_dict[key]))
        assert a == b, "\n{0}: \nGot: {1}\nExpected: {2}".format(key, a, b)
