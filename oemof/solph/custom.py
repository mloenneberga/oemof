# -*- coding: utf-8 -*-
"""
This module is designed to hold custom components with their classes and
associated individual constraints (blocks) as well as their groupings.
Therefore this module holds the class definition and the block directly
located by each other.

To add a component you need to add:

* A class that will be used by the user
* A class that inherits from pyomo SimpleBlock that holds the constraints,
  variables etc.
* A few lines to the grouping function in the module that makes sure that
  the block is actually added to the model.
"""

__copyright__ = "oemof developer group"
__license__ = "GPLv3"

import numpy as np
from pyomo.core.base.block import SimpleBlock
from pyomo.environ import (Binary, Set, NonNegativeReals, Var, Constraint,
                           Expression, BuildAction)
from oemof.solph import Transformer

# ------------------------------------------------------------------------------
# Start of Engine-Generator Component
# ------------------------------------------------------------------------------


class DieselGenerator( Transformer ):
    """
    Component `DieselGenerator` to model stationary engine-generators.

    Parameters
    ----------
    fuel_input : dict
        Dictionary with key-value-pair of `oemof.Bus` and `oemof.Flow` object
        for the fuel input.
    fuel_curve : dict
        Dictionary with key-value-pair of operating points as fraction of
        nominal_capacity of output.keys and the specific fuel consumption.
        The fuel curve is linearized and fuel coefficients
        GenericEngineGenerator.fuel_coeff_a and
        GenericEngineGenerator.fuel_coeff_b are being calculated.
    electrical_output : dict
        Dictionary with key-value-pair of `oemof.Bus` and `oemof.Flow` object
        for the electrical output.

    Notes
    -----
    The following sets, variables, constraints and objective parts are created
     * :py:class:`~oemof.solph.blocks.DieselGenerator`
    """

    def __init__(self, fuel_curve, *args, **kwargs):
        super().__init__( *args, **kwargs )

        self.fuel_input = kwargs.get( 'fuel_input' )
        self.electrical_output = kwargs.get( 'electrical_output' )
        self.fuel_curve = {k: v for k, v in fuel_curve.items()}


        # map specific flows to standard API
        fuel_bus = list( self.fuel_input.keys() )[0]
        fuel_flow = list( self.fuel_input.values() )[0]
        fuel_bus.outputs.update( {self: fuel_flow} )

        self.outputs.update( kwargs.get( 'electrical_output' ) )

        x = sorted( map( float, self.fuel_curve.keys() ) )
        y = sorted( map( int, self.fuel_curve.values() ) )

        z = np.polyfit( x, y, 1 )

        self.fuel_coeff_a = z[0]
        self.fuel_coeff_b = z[1]

# ------------------------------------------------------------------------------
# End of Engine-Generator Component
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Start of Engine-Generator Block
# ------------------------------------------------------------------------------


class DieselGeneratorBlock( SimpleBlock ):
    """Block for nodes of class:`.DieselGenerator`."""

    CONSTRAINT_GROUP = True

    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs )

    def _create(self, group=None):
        """
        Create constraints for DieselGeneratorBlock.

        Parameters
        ----------
        group : list
            List containing `.DieselGenerators` objects.
            e.g. groups=[genericeg1, genericeg2,..]
        """
        m = self.parent_block()

        if group is None:
            return None

        in_flows = {n: [i for i in n.fuel_input.keys()] for n in group}
        out_flows = {n: [o for o in n.electrical_output.keys()] for n in group}

        self.relation = Constraint( group, noruleinit=True )

        def _input_output_relation_rule(block):
            for n in group:
                for t in m.TIMESTEPS:
                    for i in in_flows[n]:
                        for o in out_flows[n]:
                            try:
                                lhs = (m.flow[i, n, t] - n.fuel_coeff_b * m.NonConvexFlow.status[n, o, t]) *\
                                      m.flows[n,o].nominal_value \
                                      / n.fuel_coeff_a
                                rhs = m.flow[n, o, t]
                            except:
                                raise ValueError( "Error in constraint creation",
                                                  "source: {0}, target: {1}".format(
                                                      n.label, o.label ) )
                            block.relation.add((n, i, o, t), (lhs == rhs))

        self.relation_build = BuildAction( rule=_input_output_relation_rule )

        # ------------------------------------------------------------------------------
        # End of Engine-Generator Block
        # ------------------------------------------------------------------------------


def custom_component_grouping(node):
    if isinstance( node, DieselGenerator ):
        return DieselGeneratorBlock
