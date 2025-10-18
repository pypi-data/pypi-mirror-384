import json
from unittest.mock import patch

import h5py
import numpy as np
import pytest

from ..tasks import mchirp_estimates
from ..util import read_binary
from ..util.tempfile import NamedTemporaryFile
from . import data

skymap = read_binary(data, 'bayestar.multiorder.fits')


@patch('gwcelery.tasks.gracedb.download.run', return_value='mock_mchirp')
@patch('gwcelery.tasks.gracedb.upload.run')
@patch('gwcelery.tasks.mchirp_estimates.plot_mchirp.run')
def test_handle_mchirp_json(mock_plot, mock_upload, mock_download):
    alert = {
        "data": {
            "tag_names": ["em_bright"],
            "filename": "mchirp_source.json"
        },
        "uid": "TS123456",
        "alert_type": "log"
    }
    mchirp_estimates.handle(alert)
    mock_download.assert_called_once_with(
        'mchirp_source.json',
        'TS123456'
    )
    mock_plot.assert_called_once_with('mock_mchirp')
    mock_upload.assert_called_once()


@patch('gwcelery.tasks.gracedb.download.run', return_value='mock_mchirp')
@patch('gwcelery.tasks.gracedb.upload.run')
@patch('gwcelery.tasks.mchirp_estimates.plot_mchirp.run')
def test_handle_binned_mchirp_pe_json(mock_plot, mock_upload, mock_download):
    alert = {
        "data": {
            "tag_names": ["em_bright"],
            "filename": "mchirp_source_PE.json"
        },
        "uid": "TS123456",
        "alert_type": "log"
    }
    mchirp_estimates.handle(alert)
    mock_download.assert_called_once_with(
        'mchirp_source_PE.json',
        'TS123456'
    )
    mock_plot.assert_called_once_with('mock_mchirp')
    mock_upload.assert_called_once()


@pytest.mark.parametrize(
        'mchirp_det,group,mchirp_bin,sky_map',
        [[1.6, 'CBC', 7, skymap],
         [32, 'CBC', 15, skymap],
         [1.5, 'Burst', 7, None],
         [1.5, 'Test', 7, skymap],
         [1.5, 'Test', 7, None]])
def test_binned_mchirp(mchirp_det, group, mchirp_bin, sky_map):
    #  load json and find most probable bin
    r = json.loads(mchirp_estimates.binned_mchirp(sky_map, group, mchirp_det))
    bin_idx = np.argmax(r['probabilities'])
    assert bin_idx == mchirp_bin


@pytest.mark.parametrize(
        'posterior_samples,group,mchirp_bin',
        [[[(1.2, 1.2),
           (1.3, 1.3)],
          'CBC', 2],
         [[(22.3, 12.2),
           (23.1, 13.3)],
          'CBC', 14],
         [[(1.5, 1.5),
           (1.6, 1.6)],
          'Burst', 5]])
def test_binned_mchirp_pe(posterior_samples, group, mchirp_bin):
    with NamedTemporaryFile() as f:
        filename = f.name
        with h5py.File(f, 'r+') as tmp_h5:
            data = np.array(
                    posterior_samples,
                    dtype=[('mass_1_source', '<f8'), ('mass_2_source', '<f8')])
            ps = 'posterior_samples'
            tmp_h5.create_dataset(
                ps,
                data=data)
        with open(filename, 'rb') as data:
            r = json.loads(mchirp_estimates.binned_mchirp_pe(data.read()))
    bin_idx = np.argmax(r['probabilities'])
    assert bin_idx == mchirp_bin


def test_amplfi_posterior_binned_mchirp_pe():
    posterior_samples_content = read_binary(
        data, 'amplfi.posterior_samples.hdf5'
    )
    res = json.loads(
        mchirp_estimates.binned_mchirp_pe(posterior_samples_content))
    assert set(res.keys()) - set(['bin_edges', 'probabilities']) \
        == set()


@pytest.mark.parametrize(
        'mchirp_det,group,sky_map',
        [[1.6, 'CBC', skymap],
         [1.5, 'Burst', None]])
def test_plot_mchirp(mchirp_det, group, sky_map):
    json_str = mchirp_estimates.binned_mchirp(sky_map, group, mchirp_det)
    outfile = mchirp_estimates.plot_mchirp(json_str)
    assert outfile
