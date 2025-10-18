"""Chirp mass estimates."""
import io
import json

from ligo.skymap.io import read_sky_map
from ligo_cgmi.chirp_probabilities import cgmi, load_posterior_samples
from matplotlib import pyplot as plt

from .. import app
from ..util import closing_figures
from ..util.tempfile import NamedTemporaryFile
from . import gracedb, igwn_alert


@igwn_alert.handler('superevent',
                    'mdc_superevent',
                    shared=False)
def handle(alert):
    """IGWN alert handler to plot and upload a visualization
    of every ``mchirp_source.json`` and ``mchirp_source_PE.json``.
    """
    filenames = ['mchirp_source.json', 'mchirp_source_PE.json']
    graceid = alert['uid']
    if alert['alert_type'] == 'log':
        for f in filenames:
            if alert['data']['filename'] == f:
                plot_tags = ['em_follow']
                if 'public' in alert['data']['tag_names']:
                    plot_tags.append('public')
                (
                    gracedb.download.si(f, graceid)
                    |
                    plot_mchirp.s()
                    |
                    gracedb.upload.s(
                        f.replace('.json', '.png'),
                        graceid,
                        message=(
                            'Chirp mass visualization from '
                            f'<a href="/api/superevents/{graceid}/files/{f}">'
                            f'{f}</a>'),
                        tags=plot_tags
                    )
                ).delay()
                break


@app.task(shared=False)
def binned_mchirp(sky_map, group, mchirp_det, mdc=False):
    """Find coarse-grained mass estimates.

    Parameters
    ----------
    sky_map:
        byte string sky map contents
    group: str
        search group, CBC or Burst
    mchirp_det: float
        detector frame chirp mass
    mdc: bool
        True is event is from MDC, False otherwise

    Returns
    -------
    data: json
        json chirp mass bins and probabilities

    """
    if group.lower() == 'burst':
        bins, probs, _ = cgmi(group, mchirp_det, None,
                              sky_map, cgmi_type='LL', MDC=mdc)
    elif group.lower() == 'cbc':
        with NamedTemporaryFile(content=sky_map) as skymap_file:
            gw_skymap = read_sky_map(skymap_file.name, moc=True)
            bins, probs, _ = cgmi(group, mchirp_det, None,
                                  gw_skymap, cgmi_type='LL', MDC=mdc)
    elif group.lower() == 'test':
        # For CBC Test events
        try:
            with NamedTemporaryFile(content=sky_map) as skymap_file:
                gw_skymap = read_sky_map(skymap_file.name, moc=True)
                bins, probs, _ = cgmi(group, mchirp_det, None,
                                      gw_skymap, cgmi_type='LL', MDC=mdc)
        # For Burst Test events
        except OSError:
            bins, probs, _ = cgmi(group, mchirp_det, None,
                                  sky_map, cgmi_type='LL', MDC=mdc)
    else:
        raise NotImplementedError

    return json.dumps({
        'bin_edges': bins.tolist(),
        'probabilities': probs.tolist()
    })


@app.task(shared=False)
def binned_mchirp_pe(pe_data, mdc=False):
    """Find PE-based coarse-grained mass estimates.

    Parameters
    ----------
    pe_data: pandas DataFrame
        parameter estimation table
    mdc: bool
        True is event is from MDC, False otherwise

    Returns
    -------
    data: json
        json chirp mass bins and probabilities
    """

    with NamedTemporaryFile(content=pe_data) as samplefile:
        filename = samplefile.name
        samples = load_posterior_samples(filename)
        bins, _, probs = cgmi(None, None, samples,
                              None, cgmi_type='PE', MDC=mdc)

    return json.dumps({
        'bin_edges': bins.tolist(),
        'probabilities': probs.tolist()
    })


@app.task(shared=False)
@closing_figures()
def plot_mchirp(json_contents):
    """Create chirp mass histogram.

    Parameters
    ----------
    json_contents: str
        chirp mass probs and bin edges

    Returns
    -------
    outfile: BytesIO object
        chirp mass histogram
    """
    plt.switch_backend('agg')

    outfile = io.BytesIO()
    r = json.loads(json_contents)
    probs = r['probabilities']
    bin_edges = r['bin_edges']
    with plt.style.context('seaborn-v0_8-white'):
        fig, ax = plt.subplots(figsize=(8, 2))
        ax.bar(range(len(bin_edges) - 1), probs, alpha=1, align='edge',
               width=1, edgecolor='w')
        # remove hanging .0 on integer bins for labels
        bin_labels = [int(e) if e % 1 == 0 else e for e in bin_edges]
        ax.set_xticks(range(len(bin_edges)), labels=bin_labels)
        ax.tick_params(axis='x', direction='out', length=3, width=1)
        ax.set_xlabel(r'Source Frame Chirp Mass Bin ($M_{\odot}$)')
        ax.set_ylabel('Probability')
        fig.tight_layout()
        fig.savefig(outfile, format='png')
    return outfile.getvalue()
