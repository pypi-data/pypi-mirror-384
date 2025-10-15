#!/usr/bin/env python
"""
Project: Parallel.GAMIT
Date: 6/15/24 10:29 AM
Author: Demian D. Gomez

Description goes here

"""

import argparse
import datetime
import os
import json
import numpy as np
import simplekml

from pgamit.pyOkada import cosd, sind
from tqdm import tqdm

from pgamit import dbConnection, pyETM
from pgamit.pyDate import Date
from pgamit.pyLeastSquares import adjust_lsq
from pgamit.pyOkada import ScoreTable
from pgamit.Utils import (cart2euler, get_stack_stations, process_stnlist, add_version_argument,
                          stationID, file_write, xyz2sphere_lla, required_length, print_columns)


def build_design(hdata, vdata):

    An, Ae = build_design_href(hdata)

    if 'v' in hdata[0].keys():
        # test to see if velocity was passed
        Lh = np.array([[d['v'][0]] for d in hdata]
                      + [[d['v'][1]] for d in hdata])
    else:
        Lh = []

    if len(vdata) > 0:
        # stack the horizontal components for the Euler pole
        Ah = np.row_stack((An, Ae))
        # design matrix for the effect of vref on href
        Anv, Aev, _ = build_design_vref(hdata)
        A = np.column_stack((Ah, np.row_stack((Anv, Aev))))
        # actual vref
        _, _, Auv = build_design_vref(vdata)
        Av = np.column_stack((np.zeros((Auv.shape[0], 3)), Auv))
        A = np.row_stack((A, Av))

        if 'v' in vdata[0].keys():
            # test to see if velocity was passed
            L = np.row_stack((Lh, np.array([[d['v'][2]] for d in vdata])))
        else:
            L = Lh
    else:
        A = np.row_stack((An, Ae))
        L = Lh

    return A, L


def build_design_href(data):
    slat = sind(np.array([d['lat'] for d in data]))
    slon = sind(np.array([d['lon'] for d in data]))
    clat = cosd(np.array([d['lat'] for d in data]))
    clon = cosd(np.array([d['lon'] for d in data]))

    slatslon = slat * slon
    slatclon = slat * clon

    Re = 6378137

    An = Re * 1e-9 * np.column_stack((slon, -clon, np.zeros_like(slon)))
    Ae = Re * 1e-9 * np.column_stack((-slatclon, -slatslon, clat))

    return An, Ae


def build_design_vref(data):

    lat = np.array([d['lat'] for d in data])
    lon = np.array([d['lon'] for d in data])

    An = np.column_stack((-(sind(lat) * cosd(lon)), -sind(lon),
                          cosd(lat) * cosd(lon)))
    Ae = np.column_stack((-(sind(lat) * sind(lon)),
                          cosd(lon), cosd(lat) * sind(lon)))
    Au = np.column_stack((cosd(lat), np.zeros_like(lat), sind(lat)))

    return An, Ae, Au


def analize_candidates(cnn, args):
    llat = float(args.candidate_sites[0])
    ulat = float(args.candidate_sites[1])
    llon = float(args.candidate_sites[2])
    ulon = float(args.candidate_sites[3])
    myrs = float(args.candidate_sites[4])

    if llat > ulat:
        print(' >> Latitude range invalid')
        exit(1)

    if llon > ulon:
        print(' >> Latitude range invalid')
        exit(1)

    ' >> Obtaining the station stack list of stations...'
    # get all stations in the requested stack
    stations = get_stack_stations(cnn, args.stack_name[0])

    sites = '\'' + '\',\''.join(['%s' % (stationID(stn)) for stn in stations]) + '\''

    rs = cnn.query_float('SELECT "NetworkCode", "StationCode", lat, lon FROM stations '
                         'WHERE "NetworkCode" || \'.\' || "StationCode" IN (%s) '
                         'AND lat BETWEEN %f AND %f '
                         'AND lon BETWEEN %f AND %f '
                         'AND "DateEnd" - "DateStart" >= %f' % (sites, llat, ulat, llon, ulon, myrs), as_dict=True)

    print(' -- Preliminary station list:')
    print_columns(['%s' % (stationID(stn)) for stn in rs])

    final_list = []
    rejected   = []
    # now get a table of jumps and see if any of the stations are affected by earthquakes
    for stn in tqdm(rs, 'Stations S-Scores', ncols=160):
        tqdm.write(' -- Processing %s' % stationID(stn))
        st = ScoreTable(cnn, stn['lat'], stn['lon'], Date(year=1970, doy=1), Date(datetime=datetime.datetime.now()))

        if len(st.table) > 0:
            tqdm.write('    Station %s is unsuitable for Euler pole determination' % stationID(stn))
            rejected.append(stn)
        else:
            tqdm.write('    Station %s added to Euler pole determination' % stationID(stn))
            final_list.append(stn)

    if len(args.candidate_sites) == 6:
        kmz_file = args.candidate_sites[5]

        kml = simplekml.Kml()
        folder = kml.newfolder(name='Euler pole stations')
        folder_rejected = kml.newfolder(name='Rejected stations')
        ICON_SQUARE = 'http://maps.google.com/mapfiles/kml/shapes/placemark_square.png'

        styles_ok = simplekml.StyleMap()
        styles_ok.normalstyle.iconstyle.icon.href = ICON_SQUARE
        styles_ok.normalstyle.iconstyle.color = 'ff00ff00'
        styles_ok.normalstyle.iconstyle.scale = 1.5
        styles_ok.normalstyle.labelstyle.scale = 0

        styles_ok.highlightstyle.iconstyle.icon.href = ICON_SQUARE
        styles_ok.highlightstyle.iconstyle.color = 'ff00ff00'
        styles_ok.highlightstyle.iconstyle.scale = 2
        styles_ok.highlightstyle.labelstyle.scale = 2

        styles_nok = simplekml.StyleMap()
        styles_nok.normalstyle.iconstyle.icon.href = ICON_SQUARE
        styles_nok.normalstyle.iconstyle.color = 'ff0000ff'
        styles_nok.normalstyle.iconstyle.scale = 1.5
        styles_nok.normalstyle.labelstyle.scale = 0

        styles_nok.highlightstyle.iconstyle.icon.href = ICON_SQUARE
        styles_nok.highlightstyle.iconstyle.color = 'ff0000ff'
        styles_nok.highlightstyle.iconstyle.scale = 2
        styles_nok.highlightstyle.labelstyle.scale = 2

        for stn in final_list:
            pt = folder.newpoint(name=stationID(stn), coords=[(stn['lon'], stn['lat'])])
            pt.stylemap = styles_ok

        for stn in rejected:
            pt = folder_rejected.newpoint(name=stationID(stn), coords=[(stn['lon'], stn['lat'])])
            pt.stylemap = styles_nok

        # DDG Jun 17 2025: the wrong version of simplekml was being used, now using latest
        # import cgi
        # import html
        # cgi.escape = html.escape

        kml.savekmz(kmz_file + '.kmz')


def euler_pole(args, cnn):

    # stations to use
    if args.include_stations:
        include_stn = process_stnlist(
            cnn, args.include_stations,
            summary_title='User selected list of stations to include:')
    else:
        include_stn = []

    # create folder for plots
    if args.directory:
        if not os.path.exists(args.directory):
            os.mkdir(args.directory)
    else:
        if not os.path.exists('production'):
            os.mkdir('production')
        args.directory = 'production'

    # vertical reference frame transformation
    if len(args.vertical_ref):
        vref = process_stnlist(cnn, args.include_stations,
                               summary_title='Stations for VREF:')
    else:
        vref = []

    if args.save_stack:
        save_stack = args.save_stack.lower()
    else:
        save_stack = None

    stack = args.stack_name[0]
    hdata = []

    for stn in tqdm(include_stn, ncols=80, disable=None):
        tqdm.write(' >> Processing HREF station ' + stationID(stn))
        station = stn['StationCode']
        network = stn['NetworkCode']

        if not args.ppp_solutions:
            # use a GAMIT stack
            rs = cnn.query_float(f'''SELECT etms.*, 
                                     stations.auto_x, stations.auto_y, stations.auto_z
                                     FROM etms INNER JOIN stations
                                     USING ("NetworkCode", "StationCode")
                                     WHERE ("NetworkCode", "StationCode", "stack",
                                     "object") =
                                     (\'{network}\', \'{station}\', \'{stack}\',
                                     \'polynomial\')''', as_dict=True)
        else:
            # use PPP solutions
            rs = cnn.query_float(f'''SELECT etms.*, 
                                                 stations.auto_x, stations.auto_y, stations.auto_z
                                                 FROM etms INNER JOIN stations
                                                 USING ("NetworkCode", "StationCode")
                                                 WHERE ("NetworkCode", "StationCode", "soln",
                                                 "object") =
                                                 (\'{network}\', \'{station}\', \'ppp\',
                                                 \'polynomial\')''', as_dict=True)

        if len(rs):
            lla = xyz2sphere_lla([rs[0]['auto_x'], rs[0]['auto_y'], rs[0]['auto_z']])
            params = np.array(rs[0]['params'])
            hdata.append({'NetworkCode': stn['NetworkCode'],
                          'StationCode': stn['StationCode'],
                          'lat': lla[0][0],
                          'lon': lla[0][1],
                          'v': params.reshape((
                              3, params.shape[0] // 3))[:, 1]})

    # now gather the data for the VREF, if any
    vdata = []
    if len(vref):
        for stn in tqdm(vref, ncols=80, disable=None):
            tqdm.write(' >> Processing VREF station ' + stationID(stn))
            station = stn['StationCode']
            network = stn['NetworkCode']

            if not args.ppp_solutions:
                # use a GAMIT stack
                rs = cnn.query_float(f'''SELECT etms.*,
                                         stations.auto_x, stations.auto_y, stations.auto_z
                                         FROM etms INNER JOIN stations
                                         USING ("NetworkCode", "StationCode")
                                         WHERE ("NetworkCode", "StationCode",
                                         "stack", "object") =
                                         (\'{network}\', \'{station}\', \'{stack}\',
                                         \'polynomial\')''', as_dict=True)
            else:
                # use PPP solutions
                rs = cnn.query_float(f'''SELECT etms.*,
                                                     stations.auto_x, stations.auto_y, stations.auto_z
                                                     FROM etms INNER JOIN stations
                                                     USING ("NetworkCode", "StationCode")
                                                     WHERE ("NetworkCode", "StationCode",
                                                     "soln", "object") =
                                                     (\'{network}\', \'{station}\', \'ppp\',
                                                     \'polynomial\')''', as_dict=True)

            if len(rs):
                lla = xyz2sphere_lla([rs[0]['auto_x'], rs[0]['auto_y'], rs[0]['auto_z']])
                params = np.array(rs[0]['params'])
                vdata.append({'NetworkCode': stn['NetworkCode'],
                              'StationCode': stn['StationCode'],
                              'lat': lla[0][0],
                              'lon': lla[0][1],
                              'v': params.reshape((
                                  3, params.shape[0] // 3))[:, 1]})
                vdata[-1]['v'][2] -= float(stn['parameters'][0]) / 1000.

    A, L = build_design(hdata, vdata)

    C, sigma, index, v, factor, _, cov = adjust_lsq(A, L)

    # summery of the Euler pole calculation
    iNE = index[0:len(hdata) * 2].reshape((2, len(hdata)))
    rNE = v[0:len(hdata) * 2].reshape((2, len(hdata)))
    fNE = (A @ C)[0:len(hdata) * 2].reshape((2, len(hdata)))
    tqdm.write('HREF residuals')
    tqdm.write('Station  NE-Used EP Vn[mm/yr] Ve[mm/yr] Rn[mm/yr] Re[mm/yr]')
    for i, stn in enumerate(hdata):
        tqdm.write('%s %-3s %-3s   %9.3f %9.3f %9.3f %9.3f'
                   % (stationID(stn), 'OK' if iNE[0, i] else 'NOK',
                      'OK' if iNE[1, i] else 'NOK',
                      fNE[0, i] * 1000., fNE[1, i] * 1000.,
                      rNE[0, i] * 1000., rNE[1, i] * 1000.))
    tqdm.write('----------------------------------------------------------')
    tqdm.write('RMS of residuals (NE)                  %9.3f %9.3f' %
               (np.sqrt(np.sum(np.square(rNE[0, :] * 1000.)) / len(hdata)),
                np.sqrt(np.sum(np.square(rNE[1, :] * 1000.)) / len(hdata))))

    # summery of VREF calculation
    if len(vref):
        iNE = index[len(hdata) * 2:]
        rNE = v[len(hdata) * 2:]
        fNE = (A @ C)[len(hdata) * 2:]
        tqdm.write('\nVREF residuals')
        tqdm.write('Station  Vu-Used Vu[mm/yr] Ru[mm/yr]')
        for i, stn in enumerate(vdata):
            tqdm.write('%s %-4s %9.3f %9.3f'
                       % (stationID(stn), 'OK' if iNE[i, 0] else 'NOK',
                          fNE[i, 0] * 1000., rNE[i, 0] * 1000.))
        tqdm.write('---------------------------------')
        tqdm.write('RMS of residuals       %9.3f'
                   % (np.sqrt(np.sum(np.square(
            rNE[:, 0] * 1000.)) / len(vdata))))

    lat, lon, rot = cart2euler(C[0, 0], C[1, 0], C[2, 0])
    # to convert to mas/yr
    k = 1e-9 * 180 / np.pi * 3600 * 1000

    # Euler vector covariance to lla
    mT_ = np.sqrt(np.sum(C ** 2))
    mXY = np.sqrt(C[0, 0] ** 2 + C[1, 0] ** 2)
    pXZ = C[0, 0] * C[2, 0]
    pYZ = C[1, 0] * C[2, 0]

    G = np.array([[C[0, 0] / mT_, C[1, 0] / mT_, C[1, 0] / mT_],
                  [-1 / mT_ ** 2 * pXZ / mXY, -1 / mT_ ** 2 * pYZ / mXY, 1 / mT_ ** 2 * mXY],
                  [-C[1, 0] / (mXY ** 2), C[0, 0] / (mXY ** 2), 0]])

    cov_lla = G @ cov[0:3, 0:3] @ G.transpose()

    tqdm.write('')
    tqdm.write(' -- Total obs.: %i' % index.shape[0])
    tqdm.write(' -- Obs. ok   : %i' % index[index].shape[0])
    tqdm.write(' -- Obs. nok  : %i' % index[~index].shape[0])
    tqdm.write(' -- wrms      : %.3f mm/yr' % (factor[0, 0] * 1000.))
    tqdm.write(' ==== EULER POLE SUMMARY ====')
    tqdm.write(''' -- XYZ (mas/yr mas/yr mas/yr) : %8.4f \xB1 %.3f %9.4f \xB1 %.3f %7.4f \xB1 %.3f'''
               % (C[0, 0] * k, sigma[0, 0] * k,
                  C[1, 0] * k, sigma[0, 1] * k,
                  C[2, 0] * k, sigma[0, 2] * k))
    tqdm.write(''' -- llr (deg deg deg/Myr)      : %8.4f \xB1 %.3f %9.4f \xB1 %.3f %7.4f \xB1 %.3f'''
               % (lat, np.rad2deg(np.sqrt(cov_lla[1, 1])),
                  lon, np.rad2deg(np.sqrt(cov_lla[2, 2])),
                  rot, np.rad2deg(np.sqrt(cov_lla[0, 0])) * 1e-9 * 1e6))

    if args.plot_etms:
        for stn in tqdm(hdata, ncols=80, disable=None):
            A, _ = build_design([stn], [stn] if len(vref) > 0 else [])
            v = np.zeros((3, 1))
            v[0:3 if len(vref) > 0 else 2] = A @ C
            model = pyETM.Model(pyETM.Model.VEL, velocity=v, fit=True)

            if not args.ppp_solutions:
                etm = pyETM.GamitETM(cnn, stn['NetworkCode'], stn['StationCode'],
                                     stack_name=stack, models=[model],
                                     plot_remove_jumps=True)
            else:
                etm = pyETM.PPPETM(cnn, stn['NetworkCode'], stn['StationCode'],
                                   models=[model], plot_remove_jumps=True)

            xfile = os.path.join(args.directory, '%s.%s_%s'
                                 % (etm.NetworkCode,
                                    etm.StationCode, 'plate-fixed'))
            etm.plot(xfile + '.png', plot_missing=False)

            if args.save_json:
                obj = etm.todictionary(time_series=True, model=True)
                file_write(xfile + '.json', json.dumps(obj, indent=4, sort_keys=False))

    if save_stack:
        stations = get_stack_stations(cnn, args.stack_name[0])

        # delete the entire stack to produce the new one
        if not args.preserve_stack:
            existing_stns = []
            cnn.query(f'DELETE FROM stacks WHERE name = \'{save_stack}\'')
        else:
            existing_stns = get_stack_stations(cnn, save_stack)
            existing_stns = [stationID(stn) for stn in existing_stns]

        pbar = tqdm(total=0, ncols=80, disable=None)

        for i, stn in enumerate(stations):

            # if preserve_stack, check if station was saved. If it was then skip
            if args.preserve_stack:
                if stationID(stn) in existing_stns:
                    tqdm.write(' -- Station %s (%i/%i) already in stack %s, skipping'
                               % (stationID(stn), i + 1, len(stations), save_stack))
                    continue

            try:
                tqdm.write(' -- Estimating EP velocity for station %s (%i/%i)'
                           % (stationID(stn), i + 1, len(stations)))

                StationCode = stn['StationCode']
                NetworkCode = stn['NetworkCode']

                A, _ = build_design([stn], [stn] if len(vref) > 0 else [])
                v = np.zeros((3, 1))
                v[0:3 if len(vref) > 0 else 2] = A @ C
                model = pyETM.Model(pyETM.Model.VEL, velocity=v, fit=True)

                if not args.ppp_solutions:
                    etm = pyETM.GamitETM(cnn,
                                         stn['NetworkCode'],
                                         stn['StationCode'],
                                         stack_name=stack,
                                         models=[model],
                                         plot_remove_jumps=True)
                else:
                    etm = pyETM.PPPETM(cnn,
                                       stn['NetworkCode'],
                                       stn['StationCode'],
                                       models=[model],
                                       plot_remove_jumps=True)

                tqdm.write(' -- Saving station %s to stack %s (%i/%i)'
                           % (stationID(stn), save_stack,
                              i + 1, len(stations)))
                pbar.total = len(etm.soln.date)
                pbar.reset()

                for x, y, z, d in zip(etm.L[0], etm.L[1], etm.L[2],
                                      etm.soln.date):
                    cnn.insert('stacks', Project=etm.soln.project,
                               NetworkCode=NetworkCode,
                               StationCode=StationCode,
                               X=float(x),
                               Y=float(y),
                               Z=float(z),
                               sigmax=0.00,
                               sigmay=0.00,
                               sigmaz=0.00,
                               FYear=float(d.fyear),
                               Year=int(d.year),
                               DOY=int(d.doy),
                               name=save_stack)
                    pbar.update()
                pbar.refresh()

                # replace stack name so that figures show the new stack name
                etm.soln.stack_name = save_stack

                if args.plot_etms:
                    xfile = os.path.join(args.directory, '%s.%s_%s'
                                         % (etm.NetworkCode,
                                            etm.StationCode, 'plate-fixed'))
                    etm.plot(xfile + '.png', plot_missing=False)

            except pyETM.pyETMException as e:
                tqdm.write(str(e))
            except Exception as e:
                tqdm.write(' -- Unexpected exception while processing %s: %s' % (stationID(stn), str(e)))

        pbar.close()


def main():
    parser = argparse.ArgumentParser(
        description='''Script to compute Euler pole given a set of stations.
                    Program can be invoked in two different ways: 1) to produce 
                    a list of candidate sites (obtained from the provided stack_name) 
                    to compute the Euler pole 2) obtain Euler vector parameters and
                    (optionally) produce time series in the resulting fixed-plate frame.''')

    parser.add_argument('stack_name', type=str, nargs=1,
                        metavar='{stack name}',
                        help='''Stack name to work with. The Euler pole
                             will be calculated so as to fix the velocities
                             of the selected sites in this stack. To use PPP 
                             solutions, provide any name for this argument and 
                             pass the -ppp switch.''')

    parser.add_argument('-include', '--include_stations', nargs='+', type=str,
                        metavar='{net.stnm}',
                        help='''Specify which stations
                             to use for Euler pole computation.''')

    parser.add_argument('-vref', '--vertical_ref', nargs='+',
                        metavar=('station', '[mm/yr]]'), default=[],
                        help='''Transform/align to a given vertical reference
                             frame using the provided station list
                             and velocities, given as [net.stnm] [vu],
                             where vu is the vertical velocity in mm/yr.''')

    parser.add_argument('-plot', '--plot_etms', action='store_true',
                        default=False,
                        help='''Plot the fixed-plate ETMs
                             after computation is done.''')

    parser.add_argument('-dir', '--directory', type=str, metavar='{dir name}',
                        help='''Directory to save the resulting PNG files.
                             If not specified, assumed to be the
                             production directory.''')

    parser.add_argument('-ppp', '--ppp_solutions', action='store_true',
                        default=False,
                        help='''Use PPP solutions instead of GAMIT. The 
                        input stack name will be ignored.''')

    parser.add_argument('-preserve', '--preserve_stack', action='store_true',
                        default=False,
                        help='''Do not erase stack when saving stations. This is useful for 
                        adding new stations to the stack, but EP parameters should match to 
                        keep the stack consistent.''')

    parser.add_argument('-json', '--save_json', action='store_true',
                        default=False,
                        help='''Save json files for the plotted ETMs. 
                        Needs -plot to work.''')

    parser.add_argument('-save', '--save_stack', type=str,
                        metavar='{new stack name}',
                        help='''Save the time series in the plate-fixed
                             frame as new stack.
                             Switch requires a stack name to use. WARNING!
                             If stack exists it will be overwritten.''')

    parser.add_argument('-candidates', '--candidate_sites', nargs='+',
                        action=required_length(5, 6),
                        help='''Provide a lat and lon range and a minimum year 
                        span to select sites to participate in an Euler pole 
                        determination. Final site selection will be output as 
                        a list of station names and coordinates or, alternatively 
                        as a kmz file (if filename given as 6th argument, do not 
                        include extension).''')

    add_version_argument(parser)

    args = parser.parse_args()

    cnn = dbConnection.Cnn("gnss_data.cfg")

    if args.candidate_sites:
        analize_candidates(cnn, args)
    else:
        euler_pole(args, cnn)


if __name__ == '__main__':
    main()
