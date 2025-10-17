import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import mapmatcher4gmns as m4g
import os
import pandas as pd

def main():
    net = m4g.loadNetFromCSV(folder='mapmatcher4gmns/examples/net', node_file='node.csv', link_file='link.csv')

    gps_df = pd.read_csv('mapmatcher4gmns/examples/net/cleaned_waypoint.csv')
    # gps_df = pd.read_csv('mapmatcher4gmns/examples/net/test_data_2.csv')
    # gps_df = pd.read_csv('mapmatcher4gmns/examples/net/journey_182427f85180665a_data.csv')

    matcher = m4g.mapmatching(
        network=net,
        time_field='local_time',
        time_format='%Y-%m-%dT%H:%M:%S.%fZ',
        extra_fields=['capture_time'],
        out_dir='mapmatcher4gmns/examples/net',
        result_file='matched_result_1.csv',
        route_file='matched_route.csv',
    )

    matcher.match(gps_df)

if __name__ == '__main__':
    main()
