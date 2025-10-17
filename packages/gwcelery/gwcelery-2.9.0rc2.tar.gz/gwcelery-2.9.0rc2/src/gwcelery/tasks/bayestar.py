"""Rapid sky localization with :mod:`BAYESTAR <ligo.skymap.bayestar>`."""
import io
import logging

from celery.exceptions import Ignore
from igwn_ligolw.utils import load_fileobj
from ligo.skymap import bayestar as _bayestar
from ligo.skymap.io import events, fits

from .. import app

log = logging.getLogger('BAYESTAR')


@app.task(queue='openmp', shared=False)
def localize(coinc_psd, graceid, disabled_detectors=None):
    """Generate a rapid sky localization using
    :mod:`BAYESTAR <ligo.skymap.bayestar>`.

    Parameters
    ----------
    coinc_psd : byte
        contents of the input event's ``coinc.xml`` file that includes PSD.
    graceid : str
        The GraceDB ID, used for FITS metadata and recording log messages
        to GraceDB.
    disabled_detectors : list, optional
        List of detectors to disable.

    Returns
    -------
    bytes
        The byte contents of the finished FITS file.

    Notes
    -----
    This task is adapted from the command-line tool
    :doc:`bayestar-localize-lvalert
    <ligo.skymap:tool/bayestar_localize_lvalert>`.

    It should execute in a special queue for computationally intensive,
    multithreaded, OpenMP tasks.

    """
    try:
        # A little bit of Cylon humor
        log.info('by your command...')

        # Read the coinc.xml into a document
        doc = load_fileobj(io.BytesIO(coinc_psd),
                           contenthandler=events.ligolw.ContentHandler)

        # Parse event
        event_source = events.ligolw.open(doc, psd_file=doc, coinc_def=None)
        if disabled_detectors:
            event_source = events.detector_disabled.open(
                event_source, disabled_detectors)
        event, = event_source.values()

        # Run BAYESTAR
        log.info('starting sky localization')
        # FIXME: the low frequency cutoff should not be hardcoded.
        # It should be provided in the coinc.xml file.
        skymap = _bayestar.localize(event, f_low=15.0)
        skymap.meta['objid'] = str(graceid)
        skymap.meta['url'] = (
            f'https://{app.conf.gracedb_host}/events/{graceid}')
        log.info('sky localization complete')

        with io.BytesIO() as f:
            fits.write_sky_map(f, skymap, moc=True)
            return f.getvalue()
    except events.DetectorDisabledError:
        raise Ignore()
