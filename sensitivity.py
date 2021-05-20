#
# Copyright © 2021 United States Government as represented by the Administrator
# of the National Aeronautics and Space Administration. No copyright is claimed
# in the United States under Title 17, U.S. Code. All Other Rights Reserved.
#
# SPDX-License-Identifier: NASA-1.3
#

import altair as alt
from astropy.coordinates import GeocentricTrueEcliptic, get_sun, SkyCoord
from astropy.coordinates.name_resolve import NameResolveError
from astropy.time import Time
from astropy import units as u
import dorado.sensitivity
from matplotlib.colors import to_hex
import numpy as np
import pandas as pd
import seaborn
import synphot
import streamlit as st

"""
# Dorado Sensitivity Calculator

This interactive exposure time calculator computes the 5-sigma limiting
magnitude of Dorado as a function of exposure time for a variety of source
spectral models and background conditions. Advanced users may prefer the
[open-source Python backend](https://github.com/nasa/dorado-sensitivity).
"""

bandpass = dorado.sensitivity.bandpasses.NUV_D

st.sidebar.markdown('## Background')

night = st.sidebar.checkbox('Orbit night (low airglow background)', True)

zodi = st.sidebar.radio('Zodiacal light background', ('Low', 'Medium', 'High', 'Specific time and place'))

if zodi == 'Specific time and place':
    time = st.sidebar.text_input("""Time (e.g. '2025-03-01 12:00:00')""", '2025-03-01 12:00:00')

    try:
        time = Time(time)
    except ValueError:
        st.sidebar.error('Did not understand time format')
        st.stop()
    st.sidebar.success(f'Resolved to ' + time.isot)

    coord = st.sidebar.text_input("""Coordinates (e.g. 'NGC 4993', '13h09m47.706s -23d23'01.79"')""", 'NGC 4993')
    try:
        coord = SkyCoord.from_name(coord)
    except NameResolveError:
        try:
            coord = SkyCoord(coord)
        except ValueError:
            st.sidebar.error('Did not understand coordinate format')
            st.stop()
    st.sidebar.success(f'Resolved to ' + coord.to_string('hmsdms', format='latex') + ' (' + coord.to_string('decimal') + ')')
else:
    lat = {'Low': 90, 'Medium': 30, 'High': 0}[zodi]

    time = Time('2025-03-01')
    sun = get_sun(time).transform_to(GeocentricTrueEcliptic(equinox=time))
    coord = SkyCoord(sun.lon + 180*u.deg, lat*u.deg, frame=GeocentricTrueEcliptic(equinox=time))

st.markdown('## Source')

spectrum = st.radio('Spectrum', ('Thermal', 'Flat in frequency (AB mag = const)', 'Flat in wavelength (ST mag = const)'))

if spectrum == 'Thermal':
    temperature = st.number_input('Temperature (K)', 0, 20000, 10000, 1000)
    source = synphot.SourceSpectrum(synphot.BlackBodyNorm1D, temperature=temperature*u.K)
elif spectrum == 'Flat in frequency (AB mag = const)':
    source = synphot.SourceSpectrum(synphot.ConstFlux1D, amplitude=0 * u.ABmag)
elif spectrum == 'Flat in wavelength (ST mag = const)':
    source = synphot.SourceSpectrum(synphot.ConstFlux1D, amplitude=0 * u.STmag)

spectra = pd.DataFrame({
    'wavelength': bandpass.waveset.to_value(u.nm),
    'aeff': (bandpass(bandpass.waveset) * dorado.sensitivity.constants.AREA).to_value(u.cm**2),
    'source': source(bandpass.waveset, u.erg * u.s**-1 * u.cm**-2 * u.nm**-1)
})

palette = [to_hex(color) for color in seaborn.color_palette('colorblind', 2)]
chart = alt.Chart(spectra).encode(alt.X('wavelength', scale=alt.Scale(type='log'), title='Wavelength (nm)'))
chart = alt.layer(
    chart.mark_line(stroke=palette[0]).encode(alt.Y('source', axis=alt.Axis(labels=False, title='Spectral flux density (erg s⁻¹ cm⁻² nm⁻¹)', titleColor=palette[0]), scale=alt.Scale(type='log'))),
    chart.mark_line(stroke=palette[1]).encode(alt.Y('aeff', axis=alt.Axis(title='Effective Area (cm²)', titleColor=palette[1]), scale=alt.Scale(type='log')))
).resolve_scale(y='independent')

st.altair_chart(chart)

st.markdown('## Results')

exptime = np.arange(1, 20) * u.min
df = pd.DataFrame({
    'exptime': exptime.to_value(u.min),
    'limmag': dorado.sensitivity.get_limmag(source, exptime=exptime, snr=5, coord=coord, time=time, night=night).to_value(u.ABmag)
})

col1, col2 = st.beta_columns([2, 1])

col1.altair_chart(alt.Chart(df).mark_line().encode(
    alt.X('exptime', title='Exposure time (min)'),
    alt.Y('limmag', scale=alt.Scale(zero=False, reverse=True), title='Limiting magnitude (AB)'),
    tooltip=['exptime', 'limmag']
))

col2.dataframe(df)
