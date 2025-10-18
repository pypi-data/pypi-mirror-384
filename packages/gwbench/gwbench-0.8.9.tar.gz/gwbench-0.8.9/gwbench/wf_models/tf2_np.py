# Copyright (C) 2020  Ssohrab Borhanian
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import numpy as np

from gwbench.wf_models.tf2 import hfpc_raw, wf_symbs_string

deriv_mod = 'numdifftools'



def hfpc(f, Mc, eta, chi1z, chi2z, DL, tc, phic, iota):
     '''
     Numpy implementation of TaylorF2 waveform model for BBH systems.
     For further details check gwbench.wf_models.tf2.hfpc
     '''
     return hfpc_raw(f, Mc, eta, chi1z, chi2z, DL, tc, phic, iota, np.cos, np.sin, np.exp, np.log)
