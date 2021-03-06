#!/usr/bin/env python
# encoding: utf-8

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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Copyright (C) Albert Kottke, 2013-2016

import numpy as np

from numpy.testing import assert_allclose
from scipy.stats import pearsonr

from pysra import site, variation


def test_randnorm():
    assert_allclose(1, np.std(variation.randnorm(size=100000)),
                    rtol=0.005)


class TestSoilTypeVariation:
    @classmethod
    def setup_class(cls):
        cls.stv = variation.SoilTypeVariation(
            0.7, [0.1, 1], [0.001, 0.20]
        )

    def test_correlation(self):
        assert_allclose(self.stv.correlation, 0.7)

    def test_limits_mod_reduc(self):
        assert_allclose(self.stv.limits_mod_reduc,
                        [0.1, 1])

    def test_limits_damping(self):
        assert_allclose(self.stv.limits_damping,
                        [0.001, 0.20])


class TestDarendeliVariation:
    @classmethod
    def setup_class(cls):
        cls.st = site.SoilType(
            'Test', unit_wt=16,
            mod_reduc=site.DarendeliNonlinearProperty(
                0, 1, 1, freq=1, num_cycles=10,
                strains=[1E-5, 2.2E-3, 1E0],
                param='mod_reduc'
            ),
            damping=site.DarendeliNonlinearProperty(
                0, 1, 1, freq=1, num_cycles=10,
                strains=[1E-5, 2.2E-3, 1E0],
                param='damping'
            )
        )
        cls.dvar = variation.DarendeliVariation(
            -0.7,
            limits_mod_reduc=[-np.inf, np.inf],
            limits_damping=[-np.inf, np.inf]
        )
        n = 1000
        realizations = [cls.dvar(cls.st) for _ in range(n)]

        cls.mod_reducs = np.array([r.mod_reduc.values for r in realizations])
        cls.dampings = np.array([r.damping.values for r in realizations])

    def test_calc_std_mod_reduc(self):
        assert_allclose(
            self.dvar.calc_std_mod_reduc(self.st.mod_reduc.values),
            # Values from Table 11.1 of Darendeli (2001).
            [0.01836, 0.05699, 0.04818],
            rtol=0.01
        )

    def test_calc_std_damping(self):
        assert_allclose(
            self.dvar.calc_std_damping(self.st.damping.values),
            # Values from Table 11.1 of Darendeli (2001).
            [0.0070766, 0.0099402, 0.0355137],
            rtol=0.01
        )

    def test_sample_std_mod_reduc(self):
        assert_allclose(
            np.std(self.mod_reducs, axis=0),
            # Values from Table 11.1 of Darendeli (2001).
            [0.01836, 0.05699, 0.04818],
            rtol=0.2
        )

    def test_sample_std_damping(self):
        assert_allclose(
            np.std(self.dampings, axis=0),
            # Values from Table 11.1 of Darendeli (2001).
            [0.0070766, 0.0099402, 0.0355137],
            rtol=0.2
        )

    def test_correlation(self):
        assert_allclose(
            pearsonr(self.mod_reducs[:, 1], self.dampings[:, 1])[0],
            self.dvar.correlation, rtol=0.1, atol=0.1)


class TestSpidVariation:
    @classmethod
    def setup_class(cls):
        soil_type = site.SoilType(
            'Test', unit_wt=16,
            mod_reduc=0.5,
            damping=5.,
        )
        cls.svar = variation.SpidVariation(
            0.9, limits_mod_reduc=[0, np.inf], limits_damping=[0, np.inf],
            std_mod_reduc=0.2, std_damping=0.2)
        n = 1000
        realizations = [cls.svar(soil_type) for _ in range(n)]
        cls.mod_reducs = np.array([r.mod_reduc for r in realizations])
        cls.dampings = np.array([r.damping for r in realizations])

    def test_sample_std_mod_reduc(self):
        assert_allclose(
            np.std(np.log(self.mod_reducs)), self.svar.std_mod_reduc, rtol=0.2)

    def test_sample_std_damping(self):
        assert_allclose(
            np.std(np.log(self.dampings)), self.svar.std_damping, rtol=0.2)

    def test_correlation(self):
        assert_allclose(
            pearsonr(self.mod_reducs, self.dampings)[0],
            self.svar.correlation, rtol=0.1, atol=0.1)
