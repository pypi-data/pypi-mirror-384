"""Application configuration for ``gracedb-test01.ligo.org``.

Inherits all settings from :mod:`gwcelery.conf.playground`, with the exceptions
below.
"""

from . import *  # noqa: F401, F403

igwn_alert_group = 'gracedb-test01'
"""IGWN alert group."""

gracedb_host = 'gracedb-test01.igwn.org'
"""GraceDB host."""

kafka_alert_config = {
    'scimma': {'url': 'kafka://kafka.scimma.org/igwn.gwalert-test01',
               'suffix': 'avro', 'skymap_encoder': lambda _: _}
}
"""Kafka broker configuration details"""

sentry_environment = 'dev'
"""Record this `environment tag
<https://docs.sentry.io/enriching-error-data/environments/>`_ in Sentry log
messages."""

mock_events_simulate_multiple_uploads = True
"""If True, then upload each mock event several times in rapid succession with
random jitter in order to simulate multiple pipeline uploads."""

idq_ok_channels = ['H1:IDQ-OK_OVL_16_4096',
                   'L1:IDQ-OK_OVL_16_4096']
"""Low-latency iDQ OK channel names for O3 replay."""

idq_channels = ['H1:IDQ-FAP_OVL_16_4096',
                'L1:IDQ-FAP_OVL_16_4096']
"""Low-latency iDQ false alarm probability channel names for O3 replay."""

llhoft_glob = '/dev/shm/kafka/{detector}_O3ReplayMDC/*.gwf'
"""File glob for playground low-latency h(t) frames. Currently points
to O3 MDC Mock Data Challange data.
See https://git.ligo.org/emfollow/mock-data-challenge"""

llhoft_channels = {
    'H1:DMT-DQ_VECTOR': 'dmt_dq_vector_bits',
    'L1:DMT-DQ_VECTOR': 'dmt_dq_vector_bits',
    'H1:GDS-CALIB_STATE_VECTOR': 'ligo_state_vector_bits',
    'L1:GDS-CALIB_STATE_VECTOR': 'ligo_state_vector_bits',
    'V1:DQ_ANALYSIS_STATE_VECTOR': 'virgo_state_vector_bits'}
"""Low-latency h(t) state vector configuration. This is a dictionary consisting
of a channel and its bitmask, as defined in :mod:`gwcelery.tasks.detchar`."""

low_latency_frame_types = {'H1': 'H1_O3ReplayMDC_llhoft',
                           'L1': 'L1_O3ReplayMDC_llhoft',
                           'V1': 'V1_O3ReplayMDC_llhoft'}
"""Types of low latency frames used in Parameter Estimation (see
:mod:`gwcelery.tasks.inference`) and in cache creation for detchar
checks (see :mod:`gwcelery.tasks.detchar`).
"""

strain_channel_names = {'H1': 'H1:GDS-CALIB_STRAIN_INJ1_O3Replay',
                        'L1': 'L1:GDS-CALIB_STRAIN_INJ1_O3Replay',
                        'V1': 'V1:Hrec_hoft_16384Hz_INJ1_O3Replay'}
"""Names of h(t) channels used in Parameter Estimation (see
:mod:`gwcelery.tasks.inference`) and in detchar omegascan creation
(see :mod:`gwcelery.tasks.detchar`)."""

rapidpe_settings = {
    'run_mode': 'o3replay',
    'accounting_group': 'ligo.dev.o4.cbc.pe.lalinferencerapid',
    'use_cprofile': False,
}
"""Config settings used for rapidpe"""
