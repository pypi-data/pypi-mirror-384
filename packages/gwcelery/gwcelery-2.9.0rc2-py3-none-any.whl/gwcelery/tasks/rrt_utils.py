import json

from ligo.skymap.io import read_sky_map
from ligo.skymap.postprocess.crossmatch import crossmatch

from .. import app
from ..util.tempfile import NamedTemporaryFile
from . import gracedb


@app.task(ignore_result=True, shared=False)
def check_high_profile(skymap, em_bright,
                       p_astro, superevent):
    superevent_id = superevent['superevent_id']
    # conditions are defined in L2100046
    # RAVEN_ALERT HIGH_PROFILE is implemented in raven.py
    # Checking if the label is applied beforehand
    if 'HIGH_PROFILE' in superevent['labels']:
        return  # HIGH_PROFILE already applied

    # low-far unmodelled burst condition
    far_list = []
    gw_events = superevent["gw_events"]
    for event in gw_events:
        events_dict = gracedb.get_event(event)
        far_list.append({"group": events_dict["group"],
                         "search": events_dict["search"],
                         "far": events_dict["far"]})
    far_list_sorted = sorted(far_list, key=lambda k: k["far"])

    if far_list_sorted[0]["group"] == "Burst" and \
       far_list_sorted[0]["search"] != "BBH":
        gracedb.create_label_with_log(
            log_message='Superevent labeled '
            '<span color="red">HIGH_PROFILE</span> '
            'since event with lowest FAR is a Burst event.',
            label='HIGH_PROFILE',
            tags=['em_follow'],
            superevent_id=superevent_id)
        return

    # annotation number condition
    preferred_event = superevent['preferred_event_data']
    if preferred_event["search"] == "SSM":
        gracedb.create_label_with_log(
            log_message='Superevent labeled '
            '<span color="red">HIGH_PROFILE</span> '
            'since preferred event is from SSM search.',
            label='HIGH_PROFILE',
            tags=['em_follow'],
            superevent_id=superevent_id)
        return
    if preferred_event["group"] == "CBC":
        em_bright_dict = json.loads(em_bright)
        has_remnant = em_bright_dict['HasRemnant']
        pastro_dict = json.loads(p_astro)
        p_bns = pastro_dict['BNS']
        p_terr = pastro_dict['Terrestrial']
        p_nsbh = pastro_dict['NSBH']

        with NamedTemporaryFile(content=skymap) as skymap_file:
            gw_skymap = read_sky_map(skymap_file.name, moc=True)
            cl = 90
            result = crossmatch(gw_skymap, contours=[cl / 100])
            sky_area = result.contour_areas[0]
            # This is commented out while we figure out the distance cutoff
            # is_far_away = not (gw_skymap.meta.get('distmean', np.nan) < 2000)
        if p_terr < 0.5:
            if p_bns > 0.1:
                gracedb.create_label_with_log(
                    log_message='Superevent labeled '
                    '<span color="red">HIGH_PROFILE</span> since p_BNS > 10%.',  # noqa: E501
                    label='HIGH_PROFILE',
                    tags=['em_follow'],
                    superevent_id=superevent_id)
                return
            elif p_nsbh > 0.1:
                gracedb.create_label_with_log(
                    log_message='Superevent labeled '
                    '<span color="red">HIGH_PROFILE</span> since p_NSBH > 10%.',  # noqa: E501
                    label='HIGH_PROFILE',
                    tags=['em_follow'],
                    superevent_id=superevent_id)
                return
            elif has_remnant > 0.1:
                gracedb.create_label_with_log(
                    log_message='Superevent labeled '
                    '<span color="red">HIGH_PROFILE</span> since '
                    'p_HasRemnant > 10%.',
                    label='HIGH_PROFILE',
                    tags=['em_follow'],
                    superevent_id=superevent_id)
                return
            elif sky_area < 100:
                gracedb.create_label_with_log(
                    log_message='Superevent labeled '
                    '<span color="red">HIGH_PROFILE</span> since area of '
                    '90% confidence level in the skymap is < 100 sq.deg.',
                    label='HIGH_PROFILE',
                    tags=['em_follow'],
                    superevent_id=superevent_id)
                return
    return "No conditions satisfied. Skipping"
